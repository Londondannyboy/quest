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
    1. Research Topic (60s) - Serper + Exa in parallel
    2. Crawl Discovered URLs (90s) - Get full content
    3. Query Zep Context (5s)
    4. Generate Article (60s) - AI with rich context
    5. Analyze Sections (10s) - For image generation
    6. Generate Images (5-8min) - Sequential contextual
    7. Save to Database (5s)
    8. Sync to Zep (5s)
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
                "target_word_count": 1500,
                "jurisdiction": "UK",  # Optional for geo-targeting
                "generate_images": True,
                "video_quality": None,  # None, "low", "medium", "high" - if set, generates video for hero
                "content_images": "with_content",  # "with_content" or "without_content"
                "num_research_sources": 10,
                "slug": "custom-url-slug"  # Optional - if not provided, generated from title
            }

        Returns:
            Dict with article_id, slug, title, status, metrics
        """
        topic = input_dict["topic"]
        article_type = input_dict["article_type"]
        app = input_dict.get("app", "placement")
        target_word_count = input_dict.get("target_word_count", 1500)
        jurisdiction = input_dict.get("jurisdiction", "UK")
        generate_images = input_dict.get("generate_images", True)
        video_quality = input_dict.get("video_quality")  # None, "low", "medium", "high"
        video_model = input_dict.get("video_model", "seedance")  # "seedance" or "wan-2.5"
        video_prompt = input_dict.get("video_prompt")  # Optional custom prompt
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

        # Serper article search
        serper_task = workflow.execute_activity(
            "serper_article_search",
            args=[
                topic,
                jurisdiction,
                30  # depth
            ],
            start_to_close_timeout=timedelta(minutes=2)
        )

        # Exa deep research
        exa_task = workflow.execute_activity(
            "exa_research_company",  # Reuse! Works for any topic
            args=["", topic, article_type],
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
        workflow.logger.info("Phase 2: Crawling ALL discovered URLs with Crawl4AI (free, parallel)")

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

        # Exa URLs - ALL of them
        for result in exa_data.get("results", []):
            if result.get("url"):
                urls_to_crawl.append(result["url"])

        # Deduplicate URLs only - no limit since crawling is free and parallel
        urls_to_crawl = list(dict.fromkeys(urls_to_crawl))

        workflow.logger.info(f"Crawling {len(urls_to_crawl)} discovered URLs")

        # Launch Crawl4AI tasks (with httpx fallback)
        crawl4ai_tasks = []

        for url in urls_to_crawl:
            crawl4ai_task = workflow.execute_activity(
                "crawl4ai_crawl",
                args=[url],
                start_to_close_timeout=timedelta(minutes=2)
            )
            crawl4ai_tasks.append(crawl4ai_task)

        # Execute all in parallel
        if crawl4ai_tasks:
            crawl4ai_results = await asyncio.gather(*crawl4ai_tasks, return_exceptions=True)
        else:
            crawl4ai_results = []

        # Extract pages from successful crawls
        crawled_pages = []
        crawl4ai_success = 0

        for result in crawl4ai_results:
            if not isinstance(result, Exception) and result.get("success"):
                pages = result.get("pages", [])
                crawled_pages.extend(pages)
                crawl4ai_success += 1

        workflow.logger.info(
            f"Crawled {len(crawled_pages)} pages "
            f"(Crawl4AI: {crawl4ai_success}/{len(urls_to_crawl)})"
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

        # Build research context using CURATED sources
        research_context = {
            "curated_sources": curation_result.get("curated_sources", []),
            "key_facts": curation_result.get("key_facts", []),
            "perspectives": curation_result.get("perspectives", []),
            "news_articles": all_news_articles[:10],  # Keep some raw news for reference
            "crawled_pages": crawled_pages[:5],  # Keep some raw pages for reference
            "exa_results": exa_data.get("results", [])[:5],
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

        # Initialize video_result for use in Phase 7 save
        video_result = None

        # ===== PHASE 5: ANALYZE SECTIONS (for images) =====
        if generate_images:
            workflow.logger.info("Phase 5: Analyzing sections for image generation")

            section_analysis = await workflow.execute_activity(
                "analyze_article_sections",
                args=[article["content"], article["title"], app],
                start_to_close_timeout=timedelta(seconds=60)
            )

            workflow.logger.info(
                f"Section analysis: {section_analysis['recommended_image_count']} images recommended"
            )

            # ===== PHASE 6: GENERATE VIDEO OR IMAGES =====
            if video_quality:
                # Generate video for hero/featured
                workflow.logger.info(f"Phase 6a: Generating video ({video_quality} quality, model={video_model})")
                workflow.logger.info(f"Video prompt provided: {bool(video_prompt)}")
                if video_prompt:
                    workflow.logger.info(f"Custom prompt: {video_prompt[:100]}...")

                # Set duration based on video model
                video_duration = 5 if video_model == "wan-2.5" else 3  # WAN 2.5: 5s, Seedance/Lightstream: 3s

                # Debug: Log what we're about to pass
                workflow.logger.info(f"DEBUG: About to call generate_article_video with:")
                workflow.logger.info(f"  title: {article['title'][:40]}...")
                workflow.logger.info(f"  app: {app}")
                workflow.logger.info(f"  quality: {video_quality}")
                workflow.logger.info(f"  duration: {video_duration}")
                workflow.logger.info(f"  model: {video_model}")
                workflow.logger.info(f"  video_prompt type: {type(video_prompt)}")
                workflow.logger.info(f"  video_prompt value: {video_prompt[:50] if video_prompt else 'None/Empty'}...")

                video_gen_result = await workflow.execute_activity(
                    "generate_article_video",
                    args=[
                        article["title"],
                        article["content"],
                        app,
                        video_quality,
                        video_duration,  # duration in seconds (varies by model)
                        "16:9",  # aspect ratio
                        video_model,  # seedance or wan-2.5
                        video_prompt  # custom prompt (or None for auto-generated)
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

            # Generate content images if requested (even with video)
            should_generate_content_images = (
                content_images == "with_content" or
                (not video_quality and generate_images)
            )

            if should_generate_content_images:
                workflow.logger.info("Phase 6c: Generating content images")

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
                        1 if video_quality else 1,  # min_content_images
                        2 if video_quality else 1   # max_content_images
                    ],
                    start_to_close_timeout=timedelta(minutes=8)
                )
            else:
                images_result = {"images_generated": 0, "total_cost": 0}

            # Update article with asset URLs and metadata (only if no video)
            if not video_quality:
                article["featured_asset_url"] = images_result.get("featured_image_url")
                article["featured_asset_alt"] = images_result.get("featured_image_alt")
                article["featured_asset_title"] = images_result.get("featured_image_title")
                article["featured_asset_description"] = images_result.get("featured_image_description")
                # Reuse featured as hero (cost saving)
                article["hero_asset_url"] = images_result.get("featured_image_url")
                article["hero_asset_alt"] = images_result.get("featured_image_alt")
                article["hero_asset_title"] = images_result.get("featured_image_title")
                article["hero_asset_description"] = images_result.get("featured_image_description")

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

            # Embed images into content at strategic positions
            if content_images:
                content = article["content"]
                paragraphs = content.split('</p>')

                if len(paragraphs) > 3:
                    # Calculate insertion points (after intro, middle, near-end)
                    total = len(paragraphs)
                    insert_points = [2, total // 2, total - 2]

                    new_paragraphs = []
                    img_index = 0

                    for i, para in enumerate(paragraphs):
                        new_paragraphs.append(para)
                        if para.strip():
                            new_paragraphs.append('</p>')

                        # Insert image at strategic points
                        if i in insert_points and img_index < len(content_images):
                            img = content_images[img_index]
                            img_html = f'\n\n<div class="my-8"><img src="{img["url"]}" alt="{img["alt"]}" class="w-full rounded-lg shadow-md" loading="lazy" /></div>\n\n'
                            new_paragraphs.append(img_html)
                            img_index += 1

                    article["content"] = ''.join(new_paragraphs)
                    workflow.logger.info(f"Embedded {img_index} images into content")

            workflow.logger.info(
                f"Images generated: {article['image_count']}, "
                f"cost: ${images_result.get('total_cost', 0):.4f}"
            )

            workflow.logger.info(
                f"Images generated: {article['image_count']}, "
                f"cost: ${images_result.get('total_cost', 0):.4f}"
            )

        # ===== PHASE 7: SAVE TO DATABASE =====
        workflow.logger.info("Phase 7: Saving article to database")

        # Save article to Neon database
        article_id = await workflow.execute_activity(
            "save_article_to_neon",
            args=[
                None,  # article_id (new article)
                article["slug"],
                article["title"],
                app,
                article_type,
                article,  # Full payload
                article.get("featured_asset_url"),  # GIF when video exists, image otherwise
                article.get("hero_asset_url"),  # None when video exists (video supersedes)
                [],  # mentioned_companies (extracted by Zep)
                "draft",  # status
                video_result.get("video_url") if video_result else None,
                video_result.get("video_playback_id") if video_result else None,
                video_result.get("video_asset_id") if video_result else None
            ],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(f"Article saved to database with ID: {article_id}")

        # ===== PHASE 8: SYNC TO ZEP =====
        workflow.logger.info("Phase 8: Syncing article to Zep knowledge graph")

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
