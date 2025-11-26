"""
Article Creation Workflow

Temporal workflow for comprehensive article research, generation, and publication.

Timeline: 5-10 minutes
"""

from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
import asyncio
from typing import Dict, Any


@workflow.defn
class ArticleCreationWorkflow:
    """
    Complete article creation workflow with parallel research.

    4-ACT VIDEO STRUCTURE:
    - Article written FIRST with 4 sections (each has four_act_visual_hint)
    - Video prompt generated FROM article sections (article-first approach)
    - Seedance 12s video (4 acts × 3 seconds)
    - Mux thumbnails replace static images

    Phases:
    1. Research Topic (60s) - DataForSEO + Serper + Exa in parallel
    2. Crawl Discovered URLs (90s) - Get full content
    3. Curate Research Sources (30s) - AI filter, dedupe, summarize
    4. Query Zep Context (5s)
    5. Generate Article (180s) - AI with 4-act structured sections
    5b. Validate Links (30s)
    6. SAVE TO DATABASE (5s) - Article safe before media generation
    7. SYNC TO ZEP (5s) - Knowledge graph updated early
    8. Generate VIDEO Prompt FROM ARTICLE (0s) - Combine four_act_visual_hint into 4-act prompt
    9. Generate 4-Act Video (2-5min) - Seedance 12s, upload to Mux
    10. Generate video_narrative JSON - Thumbnail URLs from Mux
    11. Final Update (5s) - With video_narrative
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
        target_word_count = input_dict.get("target_word_count", 1500)  # 4-act articles are ~1500 words
        jurisdiction = input_dict.get("jurisdiction", "UK")
        num_sources = input_dict.get("num_research_sources", 10)
        custom_slug = input_dict.get("slug")  # Optional custom slug for SEO

        # 4-ACT VIDEO CONFIGURATION
        # - All articles generate ONE 12-second 4-act video
        # - Thumbnails extracted from Mux at different timestamps
        # - No separate image generation (removed legacy code)
        video_quality = input_dict.get("video_quality", "medium")  # "low", "medium", "high" or None to skip
        video_model = input_dict.get("video_model", "seedance")  # "seedance" only for now

        # Legacy params (ignored but accepted for backwards compatibility)
        _ = input_dict.get("generate_images")  # Ignored - thumbnails from Mux now
        _ = input_dict.get("content_images")  # Ignored - removed
        _ = input_dict.get("video_count")  # Ignored - always 1 (4-act, 12 seconds)
        _ = input_dict.get("video_prompt")  # Ignored - generated from article's four_act_content

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

        # ===== PHASE 2a: PRE-FILTER URLs BY RELEVANCY =====
        workflow.logger.info("Phase 2a: Pre-filtering URLs by topic relevancy")

        # Build URL candidates list with metadata
        url_candidates = []

        # DataForSEO URLs
        if article_type == "news":
            for article in dataforseo_data.get("articles", []):
                if article.get("url"):
                    url_candidates.append({
                        "url": article["url"],
                        "title": article.get("title", ""),
                        "snippet": article.get("description", article.get("snippet", "")),
                        "source": "dataforseo"
                    })
        else:
            for item in dataforseo_data.get("all_urls", []):
                if item.get("url"):
                    url_candidates.append({
                        "url": item["url"],
                        "title": item.get("title", ""),
                        "snippet": item.get("description", item.get("snippet", "")),
                        "source": "dataforseo"
                    })

        # Serper URLs
        for article in serper_data.get("articles", []):
            if article.get("url"):
                url_candidates.append({
                    "url": article["url"],
                    "title": article.get("title", ""),
                    "snippet": article.get("snippet", ""),
                    "source": "serper"
                })

        # Exa URLs (skip pseudo-URLs)
        for result in exa_data.get("results", []):
            url = result.get("url", "")
            if url and url.startswith("http"):
                url_candidates.append({
                    "url": url,
                    "title": result.get("title", ""),
                    "snippet": result.get("text", "")[:500],
                    "source": "exa"
                })

        # Call pre-filter activity (visible in Temporal UI)
        # Soft filter: just 1 keyword match - removes obvious junk but keeps contextual articles
        prefilter_result = await workflow.execute_activity(
            "prefilter_urls_by_relevancy",
            args=[url_candidates, topic, 1, 30],  # min_matches=1 (soft), max_urls=30
            start_to_close_timeout=timedelta(seconds=30)
        )

        urls_to_crawl = prefilter_result.get("relevant_urls", [])
        workflow.logger.info(
            f"Pre-filter: {len(urls_to_crawl)} relevant from {prefilter_result.get('total_candidates', 0)} candidates, "
            f"{prefilter_result.get('skipped_count', 0)} skipped"
        )

        # ===== PHASE 2b: CRAWL RELEVANT URLs =====

        workflow.logger.info(f"Batch crawling {len(urls_to_crawl)} URLs with topic filtering")

        # Use batch crawl with BM25 topic filtering
        # Extracts only content relevant to the article topic
        # Note: No heartbeat_timeout - Crawl4AI is a single long HTTP call to external service
        # 10 minute timeout (generous guardrail for slow external service)
        crawl_result = await workflow.execute_activity(
            "crawl4ai_batch",
            args=[urls_to_crawl, topic, []],  # urls, topic, keywords
            start_to_close_timeout=timedelta(minutes=10)
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

        # ===== PHASE 3c: IDENTIFY SPAWN CANDIDATES =====
        # Identify high-confidence spawn opportunities (max 2) for saving after article_id is known
        spawn_opportunities = curation_result.get("spawn_opportunities", [])
        viable_spawns = []

        if spawn_opportunities:
            # Filter to high-confidence opportunities (0.7+), max 2
            viable_spawns = [
                s for s in spawn_opportunities
                if s.get("confidence", 0) >= 0.7
            ][:2]

            if viable_spawns:
                workflow.logger.info(f"Phase 3c: Found {len(viable_spawns)} viable spawn candidates: {[s.get('topic') for s in viable_spawns]}")
            else:
                workflow.logger.info("Phase 3c: No high-confidence spawn opportunities (need 0.7+)")
        else:
            workflow.logger.info("Phase 3c: No spawn opportunities found")

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

        # ===== PHASE 4b: VALIDATE SOURCE URLs BEFORE ARTICLE GENERATION (NON-BLOCKING) =====
        # Validate URLs BEFORE giving to Sonnet so it only cites working sources
        # This is NON-BLOCKING - if validation fails, we continue with unvalidated URLs
        workflow.logger.info("Phase 4b: Validating source URLs (non-blocking)")

        urls_to_validate = [s["url"] for s in all_source_urls if s.get("url")]
        validated_source_urls = all_source_urls  # Default: use all if validation fails

        if urls_to_validate:
            try:
                validation_result = await workflow.execute_activity(
                    "playwright_url_cleanse",
                    args=[urls_to_validate[:50], False],  # use_browser=False for speed (HEAD requests)
                    start_to_close_timeout=timedelta(seconds=45),  # Shorter timeout
                    retry_policy=RetryPolicy(
                        maximum_attempts=1,  # Don't retry - non-blocking
                        initial_interval=timedelta(seconds=1)
                    )
                )

                valid_url_set = set(validation_result.get("valid_urls", []))
                invalid_count = len(validation_result.get("invalid_urls", []))

                # Filter all_source_urls to only include validated URLs
                if valid_url_set:
                    validated_source_urls = [s for s in all_source_urls if s.get("url") in valid_url_set]
                    workflow.logger.info(
                        f"URL validation: {len(validated_source_urls)} valid, {invalid_count} filtered"
                    )
                else:
                    # No valid URLs returned - use original list
                    workflow.logger.warning("URL validation returned no valid URLs - using original list")
                    validated_source_urls = all_source_urls

            except Exception as e:
                # Non-blocking: log warning and continue with unvalidated URLs
                workflow.logger.warning(f"URL validation failed (non-blocking): {e}")
                workflow.logger.info("Continuing with unvalidated URLs - Phase 5b will catch broken links")

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
            "generate_four_act_article",
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
            try:
                validation_result = await workflow.execute_activity(
                    "playwright_url_cleanse",
                    args=[article_urls],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=1)  # Don't retry - non-critical
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
            except Exception as e:
                # Graceful fail - link validation is not critical
                workflow.logger.warning(f"Phase 5b: Link validation failed (non-critical): {e}")
                workflow.logger.info("Continuing with unvalidated links")
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

        # ===== PHASE 6b: SAVE SPAWN CANDIDATES =====
        # Now that we have article_id, save any spawn candidates with parent link
        spawn_candidates_saved = 0

        if viable_spawns:
            workflow.logger.info(f"Phase 6b: Saving {len(viable_spawns)} spawn candidates")

            for spawn in viable_spawns:
                try:
                    spawn_id = await workflow.execute_activity(
                        "save_spawn_candidate",
                        args=[spawn, article_id, app],  # Link to parent article
                        start_to_close_timeout=timedelta(seconds=15)
                    )
                    if spawn_id:
                        spawn_candidates_saved += 1
                        workflow.logger.info(f"  Saved spawn candidate: {spawn.get('topic')} (ID: {spawn_id})")
                except Exception as e:
                    workflow.logger.warning(f"  Failed to save spawn candidate: {e}")

            workflow.logger.info(f"Phase 6b: {spawn_candidates_saved}/{len(viable_spawns)} spawn candidates saved")

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

        # ===== PHASE 8: GENERATE VIDEO PROMPT FROM ARTICLE (article-first) =====
        # 4-ACT: Generate video prompt FROM article's four_act_content sections
        # Each section has four_act_visual_hint → combined into 4-act video prompt
        video_prompt_result = None
        if video_quality:
            workflow.logger.info(f"Phase 8: Generating 4-act video prompt from article sections")

            # Extract 4-act prompt from structured sections
            four_act_content = article.get("four_act_content", [])

            if four_act_content:
                workflow.logger.info(f"Extracting 4-act prompt from {len(four_act_content)} structured sections")
                video_prompt_result = await workflow.execute_activity(
                    "generate_four_act_video_prompt",
                    args=[article, app, video_model],
                    start_to_close_timeout=timedelta(seconds=30)
                )
            else:
                # No structured sections = article generation failed or is broken
                workflow.logger.error("NO STRUCTURED SECTIONS - Article must have 4 sections with four_act_visual_hint for 4-act video")
                workflow.logger.error("Skipping video generation - article needs regeneration")
                video_prompt_result = {
                    "prompt": "",
                    "success": False,
                    "error": "No four_act_content in article"
                }

            if video_prompt_result.get("success"):
                workflow.logger.info(f"4-act video prompt generated ({video_prompt_result.get('acts', 4)} acts): {video_prompt_result['prompt'][:100]}...")
            else:
                workflow.logger.warning(f"Video prompt generation failed: {video_prompt_result.get('error')}")

        # ===== PHASE 9: GENERATE 4-ACT VIDEO =====
        if video_quality:
            workflow.logger.info(f"Phase 9: Generating 4-act video ({video_quality} quality, model={video_model})")

            # Get the 4-act video prompt
            hero_video_prompt = video_prompt_result.get("prompt") if video_prompt_result else None

            if hero_video_prompt:
                workflow.logger.info(f"4-act video prompt: {hero_video_prompt[:120]}...")
            else:
                workflow.logger.warning("No video prompt available - will use auto-generated")

            # NEW: 4-act video structure = 12 seconds (4 acts × 3 seconds)
            # WAN 2.5 still uses 5s (different architecture)
            video_duration = 5 if video_model == "wan-2.5" else 12  # 12s for 4-act Seedance

            video_gen_result = await workflow.execute_activity(
                "generate_four_act_video",
                args=[
                    article["title"],
                    article["content"],  # Only used as fallback if no prompt
                    app,
                    video_quality,
                    video_duration,  # 12 seconds for 4-act structure
                    "16:9",  # aspect ratio
                    video_model,  # seedance or wan-2.5
                    hero_video_prompt  # 4-act prompt from article sections
                ],
                start_to_close_timeout=timedelta(minutes=15)
            )

            workflow.logger.info(f"4-act video generated: {video_gen_result.get('video_url', '')[:50]}...")

            # Upload to Mux
            workflow.logger.info("Phase 9b: Uploading 4-act video to Mux")

            mux_result = await workflow.execute_activity(
                "upload_video_to_mux",
                args=[video_gen_result["video_url"], True],  # public=True
                start_to_close_timeout=timedelta(minutes=10)
            )

            playback_id = mux_result.get("playback_id")

            # Store video data (video-first: GIF for featured, video supersedes hero)
            video_result = {
                "video_url": mux_result.get("stream_url"),
                "video_playback_id": playback_id,
                "video_asset_id": mux_result.get("asset_id"),
            }

            # Video-first logic:
            # - featured_asset_url = GIF (for collection cards)
            # - hero_asset_url = None (video_url supersedes in frontend)
            article["featured_asset_url"] = mux_result.get("gif_url")
            article["hero_asset_url"] = None  # Video supersedes hero

            workflow.logger.info(
                f"4-act video uploaded to Mux: {playback_id}, "
                f"cost: ${video_gen_result.get('cost', 0):.3f}"
            )

            # ===== PHASE 10: GENERATE VIDEO_NARRATIVE JSON =====
            # Build video_narrative with thumbnail URLs from Mux playback_id
            workflow.logger.info("Phase 10: Generating video_narrative with thumbnail URLs")

            # Get structured sections for thumbnail metadata
            four_act_content = article.get("four_act_content", [])

            # Build section thumbnails (mid-point of each act)
            section_thumbnails = []
            act_timestamps = [1.5, 4.5, 7.5, 10.5]  # Mid-point of each 3-second act

            for i, timestamp in enumerate(act_timestamps):
                section_data = four_act_content[i] if i < len(four_act_content) else {}
                section_thumbnails.append({
                    "time": timestamp,
                    "title": section_data.get("title", f"Section {i+1}"),
                    "factoid": section_data.get("factoid", ""),
                    "thumbnail_url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time={timestamp}&width=800"
                })

            # Build video_narrative JSON
            video_narrative = {
                "playback_id": playback_id,
                "duration": video_duration,
                "acts": 4,
                "thumbnails": {
                    "hero": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=10.5&width=1200",
                    "sections": section_thumbnails,
                    "faq": [
                        {"time": 1.0, "thumbnail_url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=1.0&width=400"},
                        {"time": 4.0, "thumbnail_url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=4.0&width=400"},
                        {"time": 7.0, "thumbnail_url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=7.0&width=400"},
                        {"time": 10.0, "thumbnail_url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=10.0&width=400"}
                    ],
                    "backgrounds": [
                        {"time": 10.0, "thumbnail_url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=10.0&width=1920"},
                        {"time": 5.0, "thumbnail_url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=5.0&width=1920"}
                    ]
                }
            }

            # Store video_narrative in article for database save
            article["video_narrative"] = video_narrative
            workflow.logger.info(f"Video narrative generated: {len(section_thumbnails)} section thumbnails")

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
                    None,  # raw_research already saved
                    article.get("video_narrative")  # 4-act video narrative with thumbnails
                ],
                start_to_close_timeout=timedelta(seconds=30)
            )
            workflow.logger.info("Article updated with video URLs and video_narrative")

        # ===== PHASE 10: MUX THUMBNAILS (4-Act Approach) =====
        # With the 4-act approach:
        # - ONE 12-second video with 4 acts (3 seconds each)
        # - Thumbnails extracted from Mux at different timestamps
        # - No separate image generation needed
        #
        # Frontend uses Mux thumbnail API:
        #   https://image.mux.com/{playback_id}/thumbnail.jpg?time={seconds}
        #
        # Act timestamps: Act 1 = 1.5s, Act 2 = 4.5s, Act 3 = 7.0s, Act 4 = 10.5s

        if video_quality and article.get("mux_playback_id"):
            playback_id = article["mux_playback_id"]

            # Store thumbnail URLs for each act (frontend can also generate these dynamically)
            article["thumbnail_act_1"] = f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=1.5&width=800"
            article["thumbnail_act_2"] = f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=4.5&width=800"
            article["thumbnail_act_3"] = f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=7.0&width=800"
            article["thumbnail_act_4"] = f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=10.5&width=800"
            article["hero_thumbnail"] = f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=10.5&width=1200&height=630&fit_mode=smartcrop"

            workflow.logger.info(f"Phase 10: Mux thumbnails configured for playback_id: {playback_id}")

        # Note: If video_quality is None, article will have no video/thumbnails
        # All articles should have video in the 4-act approach

        # ===== 4-ACT APPROACH: Media handled by frontend =====
        # In the 4-act approach:
        # - Hero video: Mux player with playback_id
        # - Section headers: Looping video segments from same Mux asset (using HLS.js + time ranges)
        # - Thumbnails: Mux thumbnail API at different timestamps
        # - No embedded media in content HTML - frontend handles all rendering
        workflow.logger.info("Phase 10 complete: 4-act video ready, thumbnails from Mux")

        # Calculate total cost
        total_cost = (
            dataforseo_data.get("cost", 0.0) +
            serper_data.get("cost", 0.0) +
            exa_data.get("cost", 0.0) +
            article_result.get("cost", 0.0) +
            (video_result.get("cost", 0.0) if video_result else 0.0)
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
            "four_act_content": len(four_act_content) if four_act_content else 0,
            "mux_playback_id": article.get("mux_playback_id"),
            "featured_asset_url": article.get("featured_asset_url"),
            "video_url": video_result.get("video_url") if video_result else None,
            "video_playback_id": video_result.get("video_playback_id") if video_result else None,
            "research_cost": total_cost,
            "spawn_candidates_saved": spawn_candidates_saved,
            "article": article
        }
