"""
Article Creation Workflow

Temporal workflow for comprehensive article research, generation, and publication.

Timeline: 5-10 minutes
"""

from temporalio import workflow
from datetime import timedelta
import asyncio
from typing import Dict, Any


@workflow.defn
class ArticleCreationWorkflow:
    """
    Complete article creation workflow with parallel research.

    Phases:
    1. Research Topic (60s) - DataForSEO + Serper + Exa in parallel
    2. Crawl Discovered URLs (90s) - Get full content
    3. Curate Research Sources (30s) - AI filter, dedupe, summarize
    4. Query Zep Context (5s)
    5. Generate Article (180s) - AI with rich context
    5b. Validate Links (30s)
    6. SAVE TO DATABASE (5s) - Article safe before media generation
    7. SYNC TO ZEP (5s) - Knowledge graph updated early
    8. Generate VIDEO Prompt (10s) - Model-aware (Seedance/WAN)
    9. Generate Video (5-15min) - Upload to Mux
    10. Generate IMAGE Prompts (10s) - Style-matched to video
    10b. Generate Content Videos (if video_count > 1)
    10c. Generate Content Images (Kontext Pro)
    11. Final Update (5s) - Embedded media in content
    """

    @workflow.run
    async def run(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute article creation workflow.

        Args:
            input_dict: {
                "topic": "Article topic",
                "article_type": "news|guide|comparison",
                "app": "placement|relocation|etc",
                "target_word_count": 3000,  # Default 3000 for comprehensive articles
                "jurisdiction": "UK",  # Optional for geo-targeting
                "generate_images": True,
                "video_quality": None,  # None, "low", "medium", "high" - if set, generates video for hero
                "video_model": "seedance",  # "seedance" or "wan-2.5"
                "video_prompt": None,  # Optional custom prompt for hero video
                "video_count": 1,  # Number of videos to generate: 1-3 (default 1 = hero only)
                "content_media": "hybrid",  # "images", "videos", or "hybrid" (2 videos + 2 images)
                "num_research_sources": 10,
                "slug": "custom-url-slug"  # Optional - if not provided, generated from title
            }

        Returns:
            Dict with article_id, slug, title, status, metrics
        """
        topic = input_dict["topic"]
        article_type = input_dict["article_type"]
        app = input_dict.get("app", "placement")
        target_word_count = input_dict.get("target_word_count", 3000)  # Default to 3000 words
        jurisdiction = input_dict.get("jurisdiction", "UK")
        generate_images = input_dict.get("generate_images", True)
        video_quality = input_dict.get("video_quality")  # None, "low", "medium", "high"
        video_model = input_dict.get("video_model", "seedance")  # "seedance" or "wan-2.5"
        video_prompt = input_dict.get("video_prompt")  # Optional custom prompt
        video_count = input_dict.get("video_count", 1)  # Number of videos: 1-3 (default 1)
        content_images = input_dict.get("content_images", "with_content")  # "with_content" or "without_content"
        num_sources = input_dict.get("num_research_sources", 10)
        custom_slug = input_dict.get("slug")  # Optional custom slug for SEO

        workflow.logger.info(f"Creating {article_type} article: {topic}")

        # ===== PHASE 1: RESEARCH TOPIC =====
        workflow.logger.info("Phase 1: Parallel research (DataForSEO + Serper + Exa)")

        # DataForSEO - use News for news articles, Organic for guides/comparisons
        if article_type == "news":
            # DataForSEO News search - best for breaking news with timestamps
            dataforseo_task = workflow.execute_activity(
                "dataforseo_news_search",
                args=[
                    [topic],  # keywords list
                    [jurisdiction],  # regions list
                    50  # depth - 5 pages worth
                ],
                start_to_close_timeout=timedelta(minutes=2)
            )
        else:
            # DataForSEO Organic search - best for evergreen content
            dataforseo_task = workflow.execute_activity(
                "dataforseo_serp_search",
                args=[
                    topic,  # query
                    jurisdiction,  # region
                    50,  # depth - 5 pages
                    True,  # include_ai_overview
                    4  # people_also_ask_depth
                ],
                start_to_close_timeout=timedelta(minutes=2)
            )

        # Serper news search (for article research)
        serper_task = workflow.execute_activity(
            "serper_news_search",
            args=[
                [topic],  # keywords as list
                [jurisdiction],  # geographic_focus as list
                30,  # depth
                "past_month"  # time_range - broader for article research
            ],
            start_to_close_timeout=timedelta(minutes=2)
        )

        # Exa deep research - use topic-specific function for articles
        exa_task = workflow.execute_activity(
            "exa_research_topic",  # Topic research (not company research!)
            args=[topic, article_type, app],
            start_to_close_timeout=timedelta(minutes=5)
        )

        # Execute all in parallel
        dataforseo_data, serper_data, exa_data = await asyncio.gather(
            dataforseo_task, serper_task, exa_task,
            return_exceptions=True
        )

        # Handle failures gracefully
        if isinstance(dataforseo_data, Exception):
            workflow.logger.error(f"DataForSEO research failed: {dataforseo_data}")
            dataforseo_data = {"articles": [], "all_urls": [], "results": [], "cost": 0.0}

        if isinstance(serper_data, Exception):
            workflow.logger.error(f"Serper research failed: {serper_data}")
            serper_data = {"articles": [], "cost": 0.0}

        if isinstance(exa_data, Exception):
            workflow.logger.error(f"Exa research failed: {exa_data}")
            exa_data = {"results": [], "cost": 0.0}

        # Count results
        dataforseo_count = len(dataforseo_data.get("articles", [])) or len(dataforseo_data.get("all_urls", []))
        serper_count = len(serper_data.get("articles", []))
        exa_count = len(exa_data.get("results", []))

        workflow.logger.info(
            f"Research: {dataforseo_count} DataForSEO, {serper_count} Serper, {exa_count} Exa"
        )

        # ===== PHASE 2: CRAWL DISCOVERED URLs =====
        workflow.logger.info("Phase 2: Batch crawling ALL discovered URLs with Crawl4AI")

        # Collect ALL URLs from all sources - no limits, crawl everything
        urls_to_crawl = []

        # DataForSEO URLs - ALL of them (50+ from news or organic)
        if article_type == "news":
            # News search returns "articles"
            for article in dataforseo_data.get("articles", []):
                if article.get("url"):
                    urls_to_crawl.append(article["url"])
        else:
            # Organic search returns "all_urls" (comprehensive list)
            for item in dataforseo_data.get("all_urls", []):
                if item.get("url"):
                    urls_to_crawl.append(item["url"])

        # Serper URLs - ALL of them
        for article in serper_data.get("articles", []):
            if article.get("url"):
                urls_to_crawl.append(article["url"])

        # Exa URLs - ALL of them (skip exa-research:// pseudo-URLs)
        for result in exa_data.get("results", []):
            url = result.get("url", "")
            if url and url.startswith("http"):
                urls_to_crawl.append(url)

        # Deduplicate URLs
        urls_to_crawl = list(dict.fromkeys(urls_to_crawl))

        workflow.logger.info(f"Batch crawling {len(urls_to_crawl)} discovered URLs with topic filtering")

        # Use batch crawl with BM25 topic filtering
        # Extracts only content relevant to the article topic
        crawl_result = await workflow.execute_activity(
            "crawl4ai_batch",
            args=[urls_to_crawl, topic, []],  # urls, topic, keywords
            start_to_close_timeout=timedelta(minutes=5),
            heartbeat_timeout=timedelta(seconds=60)
        )

        crawled_pages = crawl_result.get("pages", [])
        crawl_stats = crawl_result.get("stats", {})

        workflow.logger.info(
            f"Crawled {len(crawled_pages)} pages "
            f"({crawl_stats.get('successful', 0)}/{crawl_stats.get('total', 0)} successful, "
            f"crawler: {crawl_stats.get('crawler', 'unknown')})"
        )

        # ===== PHASE 3: CURATE RESEARCH SOURCES =====
        workflow.logger.info("Phase 3: Curating research sources with AI (filter, dedupe, summarize)")

        # Combine news articles from all sources
        all_news_articles = []
        # DataForSEO articles
        all_news_articles.extend(dataforseo_data.get("articles", []))
        # Serper articles
        all_news_articles.extend(serper_data.get("articles", []))

        curation_result = await workflow.execute_activity(
            "curate_research_sources",
            args=[
                topic,
                crawled_pages,  # All crawled content
                all_news_articles,  # All news from DataForSEO + Serper
                exa_data.get("results", []),  # Exa research
                20  # max_sources to curate
            ],
            start_to_close_timeout=timedelta(minutes=3)
        )

        workflow.logger.info(
            f"Curation: {curation_result.get('total_input', 0)} sources -> "
            f"{curation_result.get('total_output', 0)} curated, "
            f"{len(curation_result.get('key_facts', []))} facts extracted"
        )

        # ===== PHASE 3b: BUILD RAW RESEARCH (early - preserve even if article gen fails) =====
        # Build raw_research JSON immediately after curation so we don't lose it
        # This includes full URLs for source attribution in article generation
        import json as json_module
        raw_research_data = {
            "topic": topic,
            "dataforseo": {
                "articles": dataforseo_data.get("articles", [])[:50],
                "all_urls": dataforseo_data.get("all_urls", [])[:100],
            },
            "serper": {
                "articles": serper_data.get("articles", [])[:50],
            },
            "exa": {
                "results": exa_data.get("results", [])[:20],
            },
            "crawled_pages": [
                {"url": p.get("url"), "title": p.get("title"), "content": p.get("content", "")[:5000]}
                for p in crawled_pages[:50]
            ],
            "curation": {
                "curated_sources": curation_result.get("curated_sources", []),
                "key_facts": curation_result.get("key_facts", []),
                "perspectives": curation_result.get("perspectives", []),
                "high_authority_sources": curation_result.get("high_authority_sources", []),
                "article_outline": curation_result.get("article_outline", []),
                "duplicate_groups": curation_result.get("duplicate_groups", []),
            },
            "stats": {
                "dataforseo_count": dataforseo_count,
                "serper_count": serper_count,
                "exa_count": exa_count,
                "crawled_pages_count": len(crawled_pages),
                "curated_sources_count": curation_result.get("total_output", 0),
            }
        }
        raw_research = json_module.dumps(raw_research_data)
        workflow.logger.info(f"Phase 3b: Raw research built ({len(raw_research)} chars, {len(curation_result.get('curated_sources', []))} curated sources with URLs)")

        # ===== PHASE 4: ZEP CONTEXT =====
        workflow.logger.info("Phase 4: Querying Zep for context")

        zep_context = await workflow.execute_activity(
            "query_zep_for_context",
            args=[topic, "", app],  # Topic as company_name, empty domain
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(
            f"Zep context: {len(zep_context.get('articles', []))} articles, "
            f"{len(zep_context.get('deals', []))} deals"
        )

        # ===== PHASE 5: GENERATE ARTICLE CONTENT =====
        workflow.logger.info("Phase 5: Generating article content with AI")

        # Build consolidated URL list from ALL sources (for citations)
        # This gives Sonnet explicit access to all available URLs
        all_source_urls = []

        # From curated sources (highest quality)
        for source in curation_result.get("curated_sources", []):
            if source.get("url"):
                all_source_urls.append({
                    "url": source["url"],
                    "title": source.get("title", ""),
                    "type": "curated",
                    "authority": source.get("authority", "standard")
                })

        # From high authority sources (prioritize these)
        for source in curation_result.get("high_authority_sources", []):
            if isinstance(source, dict) and source.get("url"):
                all_source_urls.append({
                    "url": source["url"],
                    "title": source.get("title", ""),
                    "type": "high_authority",
                    "authority": source.get("authority", "official")
                })

        # From raw news articles (backup)
        for article in all_news_articles[:30]:
            if article.get("url") and article["url"] not in [s["url"] for s in all_source_urls]:
                all_source_urls.append({
                    "url": article["url"],
                    "title": article.get("title", ""),
                    "type": "news",
                    "authority": "news"
                })

        # From crawled pages (backup)
        for page in crawled_pages[:20]:
            if page.get("url") and page["url"] not in [s["url"] for s in all_source_urls]:
                all_source_urls.append({
                    "url": page["url"],
                    "title": page.get("title", ""),
                    "type": "crawled",
                    "authority": "standard"
                })

        # From Exa results (backup)
        for result in exa_data.get("results", [])[:15]:
            if result.get("url") and result["url"] not in [s["url"] for s in all_source_urls]:
                all_source_urls.append({
                    "url": result["url"],
                    "title": result.get("title", ""),
                    "type": "exa",
                    "authority": "research"
                })

        workflow.logger.info(f"Consolidated {len(all_source_urls)} source URLs for article generation")

        # ===== PHASE 4b: VALIDATE SOURCE URLs BEFORE ARTICLE GENERATION =====
        # Validate URLs BEFORE giving to Sonnet so it only cites working sources
        workflow.logger.info("Phase 4b: Validating source URLs (before article generation)")

        urls_to_validate = [s["url"] for s in all_source_urls if s.get("url")]

        if urls_to_validate:
            validation_result = await workflow.execute_activity(
                "playwright_url_cleanse",
                args=[urls_to_validate[:50], False],  # use_browser=False for speed (HEAD requests)
                start_to_close_timeout=timedelta(seconds=60)
            )

            valid_url_set = set(validation_result.get("valid_urls", []))
            invalid_count = len(validation_result.get("invalid_urls", []))

            # Filter all_source_urls to only include validated URLs
            validated_source_urls = [s for s in all_source_urls if s.get("url") in valid_url_set]

            workflow.logger.info(
                f"URL validation: {len(validated_source_urls)} valid, {invalid_count} invalid/broken"
            )

            # Log what was filtered out
            if invalid_count > 0:
                for item in validation_result.get("invalid_urls", [])[:5]:
                    workflow.logger.info(f"  Filtered: {item.get('url', '')[:60]} - {item.get('reason', 'unknown')}")
        else:
            validated_source_urls = all_source_urls

        # Build research context using CURATED sources + VALIDATED URLs
        research_context = {
            "curated_sources": curation_result.get("curated_sources", []),
            "key_facts": curation_result.get("key_facts", []),
            "perspectives": curation_result.get("perspectives", []),
            "high_authority_sources": curation_result.get("high_authority_sources", []),
            "article_outline": curation_result.get("article_outline", []),
            "all_source_urls": validated_source_urls,  # VALIDATED URLs only - Sonnet can cite with confidence
            "news_articles": all_news_articles[:20],
            "crawled_pages": crawled_pages[:15],
            "exa_results": exa_data.get("results", [])[:10],
            "zep_context": zep_context
        }

        article_result = await workflow.execute_activity(
            "generate_article_content",
            args=[topic, article_type, app, research_context, target_word_count, custom_slug],
            start_to_close_timeout=timedelta(minutes=3)
        )

        # Continue with whatever article we got (even minimal fallback)
        # Don't return early - always save to Neon and sync to Zep
        if not article_result.get("success"):
            workflow.logger.warning(f"Article generation had issues: {article_result.get('error')}")
            workflow.logger.info("Continuing with fallback article content")

        article = article_result["article"]

        workflow.logger.info(
            f"Article generated: {article['word_count']} words, "
            f"{article['section_count']} sections"
        )

        # ===== PHASE 5b: VALIDATE ARTICLE LINKS =====
        workflow.logger.info("Phase 5b: Validating article links")

        import re
        # Extract all URLs from article content
        url_pattern = r'href="(https?://[^"]+)"'
        article_urls = list(set(re.findall(url_pattern, article.get("content", ""))))

        if article_urls:
            validation_result = await workflow.execute_activity(
                "playwright_url_cleanse",
                args=[article_urls],
                start_to_close_timeout=timedelta(seconds=30)
            )

            invalid_urls = {item['url'] for item in validation_result.get('invalid_urls', [])}

            if invalid_urls:
                workflow.logger.info(f"Removing {len(invalid_urls)} broken/paywalled links")
                content = article["content"]
                for bad_url in invalid_urls:
                    # Replace broken link with just the text
                    pattern = rf'<a[^>]*href="{re.escape(bad_url)}"[^>]*>([^<]+)</a>'
                    content = re.sub(pattern, r'\1', content)
                article["content"] = content
            else:
                workflow.logger.info(f"All {len(article_urls)} links validated OK")
        else:
            workflow.logger.info("No external links to validate")

        # Initialize video_result
        video_result = None

        # ===== PHASE 6: SAVE TO DATABASE (early - article is safe even if media fails) =====
        workflow.logger.info("Phase 6: Saving article to database (before media generation)")
        # raw_research was already built in Phase 3b (immediately after curation)
        workflow.logger.info(f"Using raw_research from Phase 3b ({len(raw_research)} chars)")

        # Initial save - no video/images yet (they'll be added later)
        article_id = await workflow.execute_activity(
            "save_article_to_neon",
            args=[
                None,  # article_id (new article)
                article["slug"],
                article["title"],
                app,
                article_type,
                article,  # Full payload (no media yet)
                None,  # featured_asset_url (added after video/images)
                None,  # hero_asset_url (added after video/images)
                [],  # mentioned_companies (extracted by Zep)
                "draft",  # status
                None,  # video_url (added after video generation)
                None,  # video_playback_id
                None,  # video_asset_id
                raw_research  # Full research data
            ],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(f"Article saved to database with ID: {article_id}")

        # ===== PHASE 7: SYNC TO ZEP (early - knowledge graph doesn't need media) =====
        workflow.logger.info("Phase 7: Syncing article to Zep knowledge graph")

        # Build curated summary for Zep (under 10,000 chars, no chunking needed)
        zep_summary_parts = []
        zep_summary_parts.append(f"ARTICLE: {article['title']}\n")
        zep_summary_parts.append(f"TYPE: {article_type}\n")
        zep_summary_parts.append(f"APP: {app}\n\n")

        # Add key facts from curation (most valuable for knowledge graph)
        key_facts = curation_result.get("key_facts", [])
        if key_facts:
            zep_summary_parts.append("KEY FACTS:\n")
            for fact in key_facts[:15]:
                zep_summary_parts.append(f"• {fact}\n")

        # Add perspectives
        perspectives = curation_result.get("perspectives", [])
        if perspectives:
            zep_summary_parts.append("\nPERSPECTIVES:\n")
            for p in perspectives[:5]:
                zep_summary_parts.append(f"• {p}\n")

        # Add top source summaries
        curated_sources = curation_result.get("curated_sources", [])
        if curated_sources:
            zep_summary_parts.append("\nSOURCES:\n")
            for source in curated_sources[:10]:
                if source.get("summary"):
                    zep_summary_parts.append(f"• {source['summary'][:200]}\n")

        # Add article excerpt
        if article.get("excerpt"):
            zep_summary_parts.append(f"\nEXCERPT: {article['excerpt']}\n")

        zep_content = ''.join(zep_summary_parts)[:9500]  # Keep under 10k

        zep_result = await workflow.execute_activity(
            "sync_article_to_zep",
            args=[
                article_id,
                article["title"],
                article["slug"],
                zep_content,  # Curated summary instead of full content
                article.get("excerpt", ""),
                article_type,
                [],  # mentioned_companies (Zep extracts from content)
                app
            ],
            start_to_close_timeout=timedelta(minutes=2)
        )

        if zep_result.get("success"):
            workflow.logger.info(
                f"Article synced to Zep: graph={zep_result.get('graph_id')}, "
                f"companies={zep_result.get('companies_linked', 0)}"
            )
        else:
            workflow.logger.warning(f"Zep sync failed: {zep_result.get('error')}")

        # ===== PHASE 8: GENERATE VIDEO PROMPT (dedicated, model-aware) =====
        # Generate video prompt BEFORE video generation - separate from images
        video_prompt_result = None
        if video_quality:
            workflow.logger.info(f"Phase 8: Generating video prompt (model={video_model})")

            # Check if user provided a full prompt or just a hint/seed
            # Full prompt = 60+ words, use verbatim
            # Short hint = expand it with cinematic details
            user_prompt_words = len(video_prompt.split()) if video_prompt else 0

            if video_prompt and user_prompt_words >= 60:
                # User provided a complete prompt - use verbatim
                workflow.logger.info(f"Using complete custom prompt ({user_prompt_words} words)")
                video_prompt_result = {"prompt": video_prompt, "success": True, "cost": 0}
            else:
                # Generate prompt, using user's input as seed if provided
                seed_hint = video_prompt if video_prompt else None
                if seed_hint:
                    workflow.logger.info(f"Expanding user hint into cinematic prompt: '{seed_hint[:50]}...'")
                else:
                    workflow.logger.info("Generating video prompt from article content")

                video_prompt_result = await workflow.execute_activity(
                    "generate_video_prompt",
                    args=[article["title"], topic, app, video_model, seed_hint],
                    start_to_close_timeout=timedelta(seconds=60)
                )

                if video_prompt_result.get("success"):
                    workflow.logger.info(f"Video prompt generated: {video_prompt_result['prompt'][:80]}...")
                else:
                    workflow.logger.warning(f"Video prompt generation failed: {video_prompt_result.get('error')}")

        # ===== PHASE 9: GENERATE VIDEO =====
        if video_quality:
            workflow.logger.info(f"Phase 9: Generating video ({video_quality} quality, model={video_model})")

            # Get the video prompt
            hero_video_prompt = video_prompt_result.get("prompt") if video_prompt_result else None

            if hero_video_prompt:
                workflow.logger.info(f"Hero video prompt: {hero_video_prompt[:120]}...")
            else:
                workflow.logger.warning("No video prompt available - will use auto-generated")

            # Set duration based on video model
            video_duration = 5 if video_model == "wan-2.5" else 3  # WAN 2.5: 5s, Seedance/Lightstream: 3s

            video_gen_result = await workflow.execute_activity(
                "generate_article_video",
                args=[
                    article["title"],
                    article["content"],  # Only used as fallback if no prompt
                    app,
                    video_quality,
                    video_duration,  # duration in seconds (varies by model)
                    "16:9",  # aspect ratio
                    video_model,  # seedance or wan-2.5
                    hero_video_prompt  # Clean prompt from dedicated generation step
                ],
                start_to_close_timeout=timedelta(minutes=15)
            )

            workflow.logger.info(f"Video generated: {video_gen_result.get('video_url', '')[:50]}...")

            # Upload to Mux
            workflow.logger.info("Phase 6b: Uploading video to Mux")

            mux_result = await workflow.execute_activity(
                "upload_video_to_mux",
                args=[video_gen_result["video_url"], True],  # public=True
                start_to_close_timeout=timedelta(minutes=10)
            )

            # Store video data (video-first: GIF for featured, video supersedes hero)
            video_result = {
                "video_url": mux_result.get("stream_url"),
                "video_playback_id": mux_result.get("playback_id"),
                "video_asset_id": mux_result.get("asset_id"),
            }

            # Video-first logic:
            # - featured_asset_url = GIF (for collection cards)
            # - hero_asset_url = None (video_url supersedes in frontend)
            article["featured_asset_url"] = mux_result.get("gif_url")
            article["hero_asset_url"] = None  # Video supersedes hero

            workflow.logger.info(
                f"Video uploaded to Mux: {mux_result.get('playback_id')}, "
                f"cost: ${video_gen_result.get('cost', 0):.3f}"
            )

            # Update article in database with video data
            workflow.logger.info("Updating article with video data")
            await workflow.execute_activity(
                "save_article_to_neon",
                args=[
                    article_id,  # Update existing article
                    article["slug"],
                    article["title"],
                    app,
                    article_type,
                    article,  # Full payload with featured_asset_url set
                    article.get("featured_asset_url"),  # GIF from video
                    article.get("hero_asset_url"),  # None (video supersedes)
                    [],
                    "draft",
                    video_result.get("video_url"),
                    video_result.get("video_playback_id"),
                    video_result.get("video_asset_id"),
                    None  # raw_research already saved
                ],
                start_to_close_timeout=timedelta(seconds=30)
            )
            workflow.logger.info("Article updated with video URLs")

        # ===== PHASE 10: GENERATE IMAGE PROMPTS (after video, can match style) =====
        # Generate image prompts AFTER video so they can reference the video's visual style
        image_prompts_result = None
        content_images_count = input_dict.get("content_images_count", 2)

        if generate_images or (video_quality and video_count > 1):
            workflow.logger.info("Phase 10: Generating image prompts (after video, style-aware)")

            # Use video prompt as style reference if available
            video_style_desc = None
            if video_prompt_result and video_prompt_result.get("prompt"):
                video_style_desc = video_prompt_result["prompt"][:200]  # First 200 chars as style hint

            video_context_url = None
            if video_quality and article.get("featured_asset_url"):
                video_context_url = article["featured_asset_url"]

            # Determine how many prompts we need
            num_prompts_needed = max(content_images_count, video_count - 1, 4)

            image_prompts_result = await workflow.execute_activity(
                "generate_image_prompts",
                args=[
                    article["title"],
                    topic,
                    app,
                    num_prompts_needed,
                    video_context_url,  # GIF URL for visual reference
                    video_style_desc    # Video prompt text for style matching
                ],
                start_to_close_timeout=timedelta(seconds=60)
            )

            if image_prompts_result.get("success"):
                workflow.logger.info(
                    f"Image prompts generated: {len(image_prompts_result.get('prompts', []))} prompts, "
                    f"style_matched={image_prompts_result.get('matched_video_style')}"
                )
            else:
                workflow.logger.warning(f"Image prompt generation failed: {image_prompts_result.get('error')}")

        # ===== PHASE 10b: GENERATE CONTENT MEDIA (videos/images) =====
        # Get content media strategy from input
        content_media_strategy = input_dict.get("content_media", "hybrid")  # "images", "videos", "hybrid"

        # Initialize results
        content_videos_result = {"videos": [], "videos_generated": 0, "total_cost": 0}
        images_result = {"images_generated": 0, "total_cost": 0}

        # Generate sequential content VIDEOS (if video hero exists and video_count > 1)
        # video_count: 1 = hero only, 2 = hero + 1 content, 3 = hero + 2 content
        content_video_count = max(0, video_count - 1)  # Subtract hero video

        if video_quality and video_context_url and content_video_count > 0:
            # Get section prompts from image prompts
            section_prompts = image_prompts_result.get("prompts", []) if image_prompts_result else []

            if section_prompts:
                # Use first N section prompts for content videos
                video_prompts = section_prompts[:content_video_count]

                workflow.logger.info(f"Phase 6d: Generating {len(video_prompts)} sequential content videos (video_count={video_count})")

                content_videos_result = await workflow.execute_activity(
                    "generate_sequential_content_videos",
                    args=[
                        article["slug"],
                        article["title"],
                        article["content"],
                        app,
                        video_context_url,  # Hero GIF as context!
                        video_prompts,
                        video_quality,
                        3,  # 3 second videos
                        "16:9"
                    ],
                    start_to_close_timeout=timedelta(minutes=15)
                )

                # Upload content videos to Mux
                for i, vid in enumerate(content_videos_result.get("videos", [])):
                    mux_content = await workflow.execute_activity(
                        "upload_video_to_mux",
                        args=[vid["video_url"], True],
                        start_to_close_timeout=timedelta(minutes=5)
                    )
                    # Store in article
                    article[f"content_video_{i+1}_url"] = mux_content.get("stream_url")
                    article[f"content_video_{i+1}_playback_id"] = mux_content.get("playback_id")
                    article[f"content_video_{i+1}_gif"] = mux_content.get("gif_url")

                workflow.logger.info(f"Generated {content_videos_result['videos_generated']} content videos")

        # ===== PHASE 6e: GENERATE CONTENT IMAGES (optional, uses video GIF as style context) =====
        # Generate content IMAGES (Kontext Pro)
        should_generate_images = (
            generate_images and (
                content_media_strategy in ["images", "hybrid"] or
                not video_quality
            )
        )

        if should_generate_images:
            # For hybrid with videos: only generate 2 images (prompts 3-4)
            # For images-only: generate 2-3 images
            if content_media_strategy == "hybrid" and video_quality:
                min_images = 2
                max_images = 2
                workflow.logger.info("Phase 6e: Generating 2 content images (hybrid with videos)")
            else:
                min_images = 2 if video_quality else 2
                max_images = 3 if video_quality else 2
                workflow.logger.info(f"Phase 6e: Generating {max_images} content images")

            # Get clean prompts from dedicated image prompt generation step
            if image_prompts_result and image_prompts_result.get("prompts"):
                image_prompts = image_prompts_result["prompts"]
                workflow.logger.info(f"Using {len(image_prompts)} dedicated image prompts")
            else:
                image_prompts = []
                workflow.logger.info("No dedicated image prompts - will use section analysis")

            images_result = await workflow.execute_activity(
                "generate_sequential_article_images",
                args=[
                    article["slug"],
                    article["title"],
                    article["content"],
                    app,
                    "kontext-pro",
                    not video_quality,  # generate_featured only if no video
                    not video_quality,  # generate_hero only if no video
                    min_images,
                    max_images,
                    video_context_url,  # Video GIF for style matching!
                    image_prompts       # Clean prompts for images
                ],
                start_to_close_timeout=timedelta(minutes=8)
            )

        # Update article with asset URLs and metadata (only if no video)
        if not video_quality:
            article["featured_asset_url"] = images_result.get("featured_asset_url")
            article["featured_asset_alt"] = images_result.get("featured_asset_alt")
            article["featured_asset_title"] = images_result.get("featured_asset_title")
            article["featured_asset_description"] = images_result.get("featured_asset_description")
            # Reuse featured as hero (cost saving)
            article["hero_asset_url"] = images_result.get("hero_asset_url")
            article["hero_asset_alt"] = images_result.get("hero_asset_alt")
            article["hero_asset_title"] = images_result.get("hero_asset_title")
            article["hero_asset_description"] = images_result.get("hero_asset_description")

        # Content images - collect URLs and all metadata
        content_images = []
        for i in range(1, 6):
            gen_url_key = f"content_image{i}_url"
            gen_alt_key = f"content_image{i}_alt"
            gen_title_key = f"content_image{i}_title"
            gen_desc_key = f"content_image{i}_description"

            if images_result.get(gen_url_key):
                # Save with underscore format to article payload
                article[f"content_image_{i}_url"] = images_result[gen_url_key]
                article[f"content_image_{i}_alt"] = images_result.get(gen_alt_key)
                article[f"content_image_{i}_title"] = images_result.get(gen_title_key)
                article[f"content_image_{i}_description"] = images_result.get(gen_desc_key)

                content_images.append({
                    "url": images_result[gen_url_key],
                    "alt": images_result.get(gen_alt_key, f"Article image {i}")
                })

        article["image_count"] = images_result.get("images_generated", 0)
        article["video_count"] = content_videos_result.get("videos_generated", 0)

        # Collect all content media (videos first, then images) for embedding
        content_media = []

        # Add content videos (embedded as Mux players)
        for i in range(1, 5):
            playback_id = article.get(f"content_video_{i}_playback_id")
            gif_url = article.get(f"content_video_{i}_gif")
            if playback_id:
                content_media.append({
                    "type": "video",
                    "playback_id": playback_id,
                    "gif_url": gif_url,
                    "alt": f"Content video {i}"
                })

        # Add content images
        for img in content_images:
            content_media.append({
                "type": "image",
                "url": img["url"],
                "alt": img.get("alt", "Article image")
            })

        # Embed media into content at strategic positions
        if content_media:
            content = article["content"]
            paragraphs = content.split('</p>')

            if len(paragraphs) > 3:
                # Calculate insertion points spread throughout article
                # First image should be after ~25% of content (not too close to hero video)
                # Last image should be before ~90% (not at very end)
                total = len(paragraphs)
                num_media = len(content_media)

                # Start first media at ~25% into article (after hero video has impact)
                first_insert = max(4, total // 4)  # At least paragraph 4, or 25%
                # End last media at ~85% (not at very bottom)
                last_insert = min(total - 3, int(total * 0.85))

                if num_media == 1:
                    insert_points = [first_insert]
                elif num_media == 2:
                    insert_points = [first_insert, last_insert]
                else:
                    # Spread evenly between first and last positions
                    spacing = (last_insert - first_insert) // (num_media - 1) if num_media > 1 else 0
                    insert_points = [first_insert + i * spacing for i in range(num_media)]

                workflow.logger.info(f"Media insertion points: {insert_points} (total paragraphs: {total})")

                new_paragraphs = []
                media_index = 0

                for idx, para in enumerate(paragraphs):
                    new_paragraphs.append(para)
                    if para.strip():
                        new_paragraphs.append('</p>')

                    # Insert media at strategic points
                    if idx in insert_points and media_index < len(content_media):
                        media = content_media[media_index]
                        if media["type"] == "video":
                            # Embed Mux video player with autoplay (muted required for browser policy)
                            media_html = f'''
<div class="my-8 aspect-video rounded-lg overflow-hidden shadow-md">
  <mux-player
    playback-id="{media['playback_id']}"
    metadata-video-title="{media['alt']}"
    accent-color="#3b82f6"
    autoplay="muted"
    loop
    muted
    preload="auto"
    class="w-full h-full">
  </mux-player>
</div>
'''
                        else:
                            # Embed image
                            media_html = f'\n\n<div class="my-8"><img src="{media["url"]}" alt="{media["alt"]}" class="w-full rounded-lg shadow-md" loading="lazy" /></div>\n\n'
                        new_paragraphs.append(media_html)
                        media_index += 1

                article["content"] = ''.join(new_paragraphs)
                workflow.logger.info(f"Embedded {media_index} media items (videos + images) into content")

        total_media_cost = images_result.get('total_cost', 0) + content_videos_result.get('total_cost', 0)
        workflow.logger.info(
            f"Content media: {article.get('video_count', 0)} videos + {article['image_count']} images, "
            f"cost: ${total_media_cost:.4f}"
        )

        # ===== PHASE 10: FINAL UPDATE (with all media embedded in content) =====
        # Update article with embedded media content (images/videos in HTML)
        if images_result.get("images_generated", 0) > 0 or content_videos_result.get("videos_generated", 0) > 0:
            workflow.logger.info("Phase 10: Final update with embedded media")

            await workflow.execute_activity(
                "save_article_to_neon",
                args=[
                    article_id,  # Update existing article
                    article["slug"],
                    article["title"],
                    app,
                    article_type,
                    article,  # Full payload with embedded content
                    article.get("featured_asset_url"),
                    article.get("hero_asset_url"),
                    [],
                    "draft",
                    video_result.get("video_url") if video_result else None,
                    video_result.get("video_playback_id") if video_result else None,
                    video_result.get("video_asset_id") if video_result else None,
                    None  # raw_research already saved in Phase 6
                ],
                start_to_close_timeout=timedelta(seconds=30)
            )
            workflow.logger.info("Article updated with embedded media content")

        # Calculate total cost
        total_cost = (
            dataforseo_data.get("cost", 0.0) +
            serper_data.get("cost", 0.0) +
            exa_data.get("cost", 0.0) +
            article_result.get("cost", 0.0) +
            (images_result.get("total_cost", 0.0) if generate_images else 0.0)
        )

        workflow.logger.info(
            f"✅ Article creation complete! "
            f"ID: {article_id}, "
            f"Words: {article['word_count']}, "
            f"Cost: ${total_cost:.4f}"
        )

        return {
            "status": "created",
            "article_id": article_id,
            "slug": article["slug"],
            "title": article["title"],
            "word_count": article["word_count"],
            "section_count": article["section_count"],
            "image_count": article.get("image_count", 0),
            "featured_asset_url": article.get("featured_asset_url"),
            "hero_asset_url": article.get("hero_asset_url"),
            "video_url": video_result.get("video_url") if video_result else None,
            "video_playback_id": video_result.get("video_playback_id") if video_result else None,
            "research_cost": total_cost,
            "article": article  # Full payload for debugging
        }
