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
        workflow.logger.info("Phase 1: Parallel research (Serper + Exa)")

        # Serper news search
        news_task = workflow.execute_activity(
            "serper_search",  # Reuse! Works for any topic
            args=[
                "",  # No domain for articles
                topic,  # Company name field = topic
                article_type,  # Category field = article type
                jurisdiction
            ],
            start_to_close_timeout=timedelta(minutes=2)
        )

        # Exa deep research
        exa_task = workflow.execute_activity(
            "exa_research_company",  # Reuse! Works for any topic
            args=["", topic, article_type],
            start_to_close_timeout=timedelta(minutes=5)
        )

        # Execute in parallel
        news_data, exa_data = await asyncio.gather(
            news_task, exa_task,
            return_exceptions=True
        )

        # Handle failures gracefully
        if isinstance(news_data, Exception):
            workflow.logger.error(f"News research failed: {news_data}")
            news_data = {"articles": [], "cost": 0.0}

        if isinstance(exa_data, Exception):
            workflow.logger.error(f"Exa research failed: {exa_data}")
            exa_data = {"results": [], "cost": 0.0}

        workflow.logger.info(
            f"Research: {len(news_data.get('articles', []))} news articles, "
            f"{len(exa_data.get('results', []))} Exa results"
        )

        # ===== PHASE 2: CRAWL DISCOVERED URLs =====
        workflow.logger.info("Phase 2: Crawling discovered URLs with Crawl4AI")

        # Collect URLs from news + Exa
        urls_to_crawl = []

        # News URLs (up to 10)
        for article in news_data.get("articles", [])[:10]:
            if article.get("url"):
                urls_to_crawl.append(article["url"])

        # Exa URLs (up to 5)
        for result in exa_data.get("results", [])[:5]:
            if result.get("url"):
                urls_to_crawl.append(result["url"])

        # Deduplicate URLs
        urls_to_crawl = list(dict.fromkeys(urls_to_crawl))[:num_sources]

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

        # ===== PHASE 3: ZEP CONTEXT =====
        workflow.logger.info("Phase 3: Querying Zep for context")

        zep_context = await workflow.execute_activity(
            "query_zep_for_context",
            args=[topic, "", app],  # Topic as company_name, empty domain
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(
            f"Zep context: {len(zep_context.get('articles', []))} articles, "
            f"{len(zep_context.get('deals', []))} deals"
        )

        # ===== PHASE 4: GENERATE ARTICLE CONTENT =====
        workflow.logger.info("Phase 4: Generating article content with AI")

        # Build research context
        research_context = {
            "news_articles": news_data.get("articles", []),
            "crawled_pages": crawled_pages,
            "exa_results": exa_data.get("results", []),
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

                video_gen_result = await workflow.execute_activity(
                    "generate_article_video",
                    args=[
                        article["title"],
                        article["content"],
                        app,
                        video_quality,
                        3,  # duration in seconds
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

                # Store video data
                video_result = {
                    "video_url": mux_result.get("stream_url"),
                    "video_playback_id": mux_result.get("playback_id"),
                    "video_asset_id": mux_result.get("asset_id"),
                    "video_gif_url": mux_result.get("gif_url"),
                    "video_thumbnail_url": mux_result.get("thumbnail_url"),
                }

                # Use video thumbnail as featured/hero image
                article["featured_image_url"] = mux_result.get("thumbnail_featured")
                article["hero_image_url"] = mux_result.get("thumbnail_hero")

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

            # Update article with image URLs and metadata (only if no video)
            if not video_quality:
                article["featured_image_url"] = images_result.get("featured_image_url")
                article["featured_image_alt"] = images_result.get("featured_image_alt")
                article["featured_image_title"] = images_result.get("featured_image_title")
                article["featured_image_description"] = images_result.get("featured_image_description")
                # Reuse featured as hero (cost saving)
                article["hero_image_url"] = images_result.get("featured_image_url")
                article["hero_image_alt"] = images_result.get("featured_image_alt")
                article["hero_image_title"] = images_result.get("featured_image_title")
                article["hero_image_description"] = images_result.get("featured_image_description")

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
                article.get("featured_image_url"),
                article.get("hero_image_url"),
                [],  # mentioned_companies (extracted by Zep)
                "draft",  # status
                video_result.get("video_url") if video_result else None,
                video_result.get("video_playback_id") if video_result else None,
                video_result.get("video_asset_id") if video_result else None,
                video_result.get("video_gif_url") if video_result else None,
                video_result.get("video_thumbnail_url") if video_result else None
            ],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(f"Article saved to database with ID: {article_id}")

        # ===== PHASE 8: SYNC TO ZEP =====
        workflow.logger.info("Phase 8: Syncing article to Zep knowledge graph")

        zep_result = await workflow.execute_activity(
            "sync_article_to_zep",
            args=[
                article_id,
                article["title"],
                article["slug"],
                article["content"],
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
            news_data.get("cost", 0.0) +
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
            "featured_image_url": article.get("featured_image_url"),
            "hero_image_url": article.get("hero_image_url"),
            "research_cost": total_cost,
            "article": article  # Full payload for debugging
        }
