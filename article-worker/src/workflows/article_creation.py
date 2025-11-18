"""
Article Creation Workflow

Main Temporal workflow for comprehensive article research, generation, and publication.

Timeline: 5-12 minutes total (depending on image generation)
"""

from temporalio import workflow
from datetime import timedelta
import asyncio
from typing import Dict, Any

# Import activity functions (will be registered in worker)
with workflow.unsafe.imports_passed_through():
    from src.models.article_input import ArticleInput


@workflow.defn
class ArticleCreationWorkflow:
    """
    Complete article creation workflow with parallel research.

    Phases:
    1. Normalize Topic & Check (5s)
    2. Parallel Research (60s) - News + Exa + Crawl News + Crawl Sites
    3. Zep Context Query (5s)
    4. URL Validation (30s)
    5. Generate Article Content (60-120s)
    6. Analyze Sections (10s)
    7. Clean Generated Links (30s)
    8. Generate Contextual Images (5-10min)
    9. Extract & Link Companies (10s)
    10. Save to Database (5s)
    11. Sync to Zep (5s)
    """

    @workflow.run
    async def run(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute article creation workflow.

        Args:
            input_dict: ArticleInput as dict

        Returns:
            Dict with status, article_id, slug, metrics
        """
        # Convert input
        input_data = ArticleInput(**input_dict)

        workflow.logger.info(f"Creating article: {input_data.topic}")

        # ===== PHASE 1: NORMALIZE & CHECK =====
        workflow.logger.info("Phase 1: Normalizing topic and checking for duplicates")

        normalized = await workflow.execute_activity(
            "normalize_article_topic",
            args=[input_data.topic, input_data.app],
            start_to_close_timeout=timedelta(seconds=30)
        )

        existing = await workflow.execute_activity(
            "check_article_exists",
            args=[normalized["slug"]],
            start_to_close_timeout=timedelta(seconds=10)
        )

        if existing["exists"] and not input_data.auto_publish:
            workflow.logger.warning(
                f"Article with similar slug exists (ID: {existing['article_id']}). "
                f"Continuing anyway..."
            )

        # ===== PHASE 2: PARALLEL RESEARCH =====
        workflow.logger.info("Phase 2: Parallel research (News + Exa + News Crawl + Site Crawl)")

        # Build jurisdiction-aware queries
        jurisdiction_suffix = f" {input_data.jurisdiction}" if input_data.jurisdiction else ""

        # Launch all research activities in parallel
        news_task = workflow.execute_activity(
            "fetch_topic_news",
            args=[
                input_data.topic,
                input_data.app,
                input_data.jurisdiction,
                input_data.num_research_sources
            ],
            start_to_close_timeout=timedelta(minutes=2)
        )

        exa_task = workflow.execute_activity(
            "exa_research_topic",
            args=[
                input_data.topic + jurisdiction_suffix,
                input_data.app,
                input_data.target_word_count
            ],
            start_to_close_timeout=timedelta(minutes=5)
        )

        # These will be launched conditionally
        news_crawl_task = None
        auth_crawl_task = None

        # Wait for news first to get URLs
        news_data = await news_task

        # Now crawl the news sources
        if news_data.get("articles"):
            news_urls = [article["url"] for article in news_data["articles"][:10]]
            news_crawl_task = workflow.execute_activity(
                "crawl_news_sources",
                args=[news_urls],
                start_to_close_timeout=timedelta(minutes=5)
            )

        # Crawl authoritative sites if enabled
        if input_data.deep_crawl_enabled:
            auth_crawl_task = workflow.execute_activity(
                "crawl_authoritative_sites",
                args=[input_data.topic, input_data.app],
                start_to_close_timeout=timedelta(minutes=5)
            )

        # Wait for all to complete
        gather_tasks = [exa_task]
        if news_crawl_task:
            gather_tasks.append(news_crawl_task)
        if auth_crawl_task:
            gather_tasks.append(auth_crawl_task)

        results = await asyncio.gather(*gather_tasks)

        exa_data = results[0]
        news_crawl_data = results[1] if len(results) > 1 and news_crawl_task else {"pages": [], "success": False}
        auth_crawl_data = results[2] if len(results) > 2 and auth_crawl_task else {"pages": [], "success": False}

        workflow.logger.info(
            f"Phase 2 complete: {len(news_data.get('articles', []))} news articles, "
            f"{len(news_crawl_data.get('pages', []))} news pages crawled, "
            f"{len(auth_crawl_data.get('pages', []))} authoritative pages crawled, "
            f"Exa research complete"
        )

        # ===== PHASE 3: ZEP CONTEXT QUERY =====
        workflow.logger.info("Phase 3: Querying Zep for article context")

        zep_context = await workflow.execute_activity(
            "query_zep_for_article_context",
            args=[input_data.topic, input_data.app],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(
            f"Zep context: {len(zep_context.get('related_companies', []))} related companies, "
            f"{len(zep_context.get('related_articles', []))} related articles"
        )

        # ===== PHASE 4: VALIDATE SOURCE URLS =====
        workflow.logger.info("Phase 4: Validating source URLs (removing 404s and paywalls)")

        # Collect all URLs from research sources
        all_source_urls = []
        for article in news_data.get("articles", []):
            if article.get("url"):
                all_source_urls.append(article["url"])
        for result in exa_data.get("results", []):
            if result.get("url"):
                all_source_urls.append(result["url"])

        # Validate URLs
        validation_result = await workflow.execute_activity(
            "playwright_url_cleanse",
            args=[all_source_urls],
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Filter out invalid URLs
        valid_urls_set = set(validation_result["valid_urls"])
        news_data["articles"] = [
            article for article in news_data.get("articles", [])
            if article.get("url") in valid_urls_set
        ]
        exa_data["results"] = [
            result for result in exa_data.get("results", [])
            if result.get("url") in valid_urls_set
        ]

        workflow.logger.info(
            f"URL validation: {len(validation_result['valid_urls'])} valid, "
            f"{len(validation_result['invalid_urls'])} invalid"
        )

        # ===== PHASE 5: GENERATE ARTICLE CONTENT =====
        workflow.logger.info("Phase 5: Generating article content")

        # Build research data for content generation
        research_data = {
            "topic": input_data.topic,
            "app": input_data.app,
            "target_word_count": input_data.target_word_count,
            "article_format": input_data.article_format,
            "jurisdiction": input_data.jurisdiction,
            "target_keywords": input_data.target_keywords or [],
            "news_articles": news_data.get("articles", []),
            "news_crawl_pages": news_crawl_data.get("pages", []),
            "auth_crawl_pages": auth_crawl_data.get("pages", []),
            "exa_research": exa_data,
            "zep_context": zep_context,
            "article_angle": input_data.article_angle,
            "total_cost": news_data.get("cost", 0.0) + exa_data.get("cost", 0.0)
        }

        content_result = await workflow.execute_activity(
            "generate_article_content",
            args=[research_data],
            start_to_close_timeout=timedelta(minutes=3)
        )

        payload = content_result["article"]

        # Override meta description if provided
        if input_data.meta_description:
            payload["meta_description"] = input_data.meta_description

        # Set author if provided
        if input_data.author:
            payload["author"] = input_data.author

        workflow.logger.info(
            f"Article content generated: {payload['word_count']} words, "
            f"{len(payload.get('sections', []))} sections"
        )

        # ===== PHASE 6: ANALYZE SECTIONS =====
        workflow.logger.info("Phase 6: Analyzing sections for contextual images")

        sections_analysis = await workflow.execute_activity(
            "analyze_article_sections",
            args=[payload["content"], payload["sections"]],
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Update payload with analyzed sections
        payload["sections"] = sections_analysis["sections"]
        payload["narrative_arc"] = sections_analysis.get("narrative_arc")
        payload["overall_sentiment"] = sections_analysis.get("overall_sentiment")
        payload["opening_sentiment"] = sections_analysis.get("opening_sentiment")
        payload["middle_sentiment"] = sections_analysis.get("middle_sentiment")
        payload["climax_sentiment"] = sections_analysis.get("climax_sentiment")
        payload["primary_business_context"] = sections_analysis.get("primary_business_context")

        workflow.logger.info(
            f"Section analysis complete: {sections_analysis.get('recommended_image_count', 0)} images recommended"
        )

        # ===== PHASE 7: CLEAN GENERATED LINKS =====
        workflow.logger.info("Phase 7: Cleaning generated links (removing broken URLs)")

        # Extract URLs from content
        content_with_clean_links = await workflow.execute_activity(
            "playwright_clean_article_links",
            args=[payload["content"]],
            start_to_close_timeout=timedelta(seconds=30)
        )

        payload["content"] = content_with_clean_links

        workflow.logger.info("Link cleaning complete")

        # ===== PHASE 8: GENERATE CONTEXTUAL IMAGES =====
        if input_data.generate_images:
            workflow.logger.info("Phase 8: Generating contextual images (Flux Kontext Max)")

            article_images = await workflow.execute_activity(
                "generate_article_contextual_images",
                args=[
                    normalized["slug"],
                    input_data.topic,
                    payload["sections"],
                    sections_analysis.get("recommended_image_count", 3),
                    input_data.app
                ],
                start_to_close_timeout=timedelta(minutes=10)
            )

            # Merge image URLs into payload
            payload.update(article_images.get("images", {}))

            workflow.logger.info(
                f"Image generation complete: {article_images.get('images_generated', 0)} images created"
            )
        else:
            workflow.logger.info("Phase 8: Skipping image generation (disabled)")

        # ===== PHASE 9: EXTRACT & LINK COMPANIES =====
        workflow.logger.info("Phase 9: Extracting company mentions and linking")

        companies_result = await workflow.execute_activity(
            "extract_company_mentions",
            args=[payload["content"], zep_context.get("related_companies", [])],
            start_to_close_timeout=timedelta(seconds=30)
        )

        payload["mentioned_companies"] = companies_result.get("companies", [])
        payload["company_mention_count"] = len(payload["mentioned_companies"])

        # Calculate completeness
        completeness = await workflow.execute_activity(
            "calculate_article_completeness",
            args=[payload],
            start_to_close_timeout=timedelta(seconds=10)
        )

        payload["completeness_score"] = completeness

        workflow.logger.info(
            f"Company extraction complete: {len(payload['mentioned_companies'])} companies found"
        )

        # ===== PHASE 10: SAVE TO DATABASE =====
        workflow.logger.info("Phase 10: Saving to Neon database")

        # Add data source tracking
        payload["data_sources"] = {
            "serper": {
                "articles": len(news_data.get("articles", [])),
                "cost": news_data.get("cost", 0.0)
            },
            "crawl4ai": {
                "pages": len(news_crawl_data.get("pages", [])) + len(auth_crawl_data.get("pages", [])),
                "success": news_crawl_data.get("success", False) or auth_crawl_data.get("success", False)
            },
            "firecrawl": {
                "pages": 0,
                "cost": 0.0,
                "success": False
            },
            "exa": {
                "results": len(exa_data.get("results", [])),
                "cost": exa_data.get("cost", 0.0)
            }
        }

        # Set publication status
        payload["status"] = "published" if input_data.auto_publish else "draft"
        if input_data.auto_publish:
            from datetime import datetime
            payload["published_at"] = datetime.now().isoformat()

        article_id = await workflow.execute_activity(
            "save_article_to_neon",
            args=[
                existing.get("article_id"),
                normalized["slug"],
                payload,
                input_data.app
            ],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(f"Saved to database: article_id={article_id}")

        # Link companies to article
        if payload["mentioned_companies"]:
            await workflow.execute_activity(
                "link_companies_to_article",
                args=[str(article_id), payload["mentioned_companies"]],
                start_to_close_timeout=timedelta(seconds=30)
            )
            workflow.logger.info(f"Linked {len(payload['mentioned_companies'])} companies to article")

        # ===== PHASE 11: ZEP SYNC =====
        if not input_data.skip_zep_sync:
            workflow.logger.info("Phase 11: Syncing to Zep knowledge graph")

            zep_summary = await workflow.execute_activity(
                "create_article_zep_summary",
                args=[payload, zep_context],
                start_to_close_timeout=timedelta(seconds=30)
            )

            zep_result = await workflow.execute_activity(
                "sync_article_to_zep",
                args=[
                    str(article_id),
                    input_data.topic,
                    normalized["slug"],
                    zep_summary,
                    payload,
                    input_data.app
                ],
                start_to_close_timeout=timedelta(minutes=2)
            )

            payload["zep_graph_id"] = zep_result.get("graph_id")
            payload["zep_facts_count"] = zep_result.get("facts_count", 0)

            workflow.logger.info("Zep sync complete")
        else:
            workflow.logger.info("Phase 11: Skipping Zep sync (disabled)")

        # ===== COMPLETE =====
        total_cost = (
            research_data["total_cost"] +
            content_result.get("cost", 0.0") +
            (article_images.get("total_cost", 0.0) if input_data.generate_images else 0.0)
        )

        workflow.logger.info(
            f"✅ Article creation complete: {normalized['slug']} "
            f"(cost: ${total_cost:.4f}, word count: {payload['word_count']})"
        )

        return {
            "status": "created" if not existing["exists"] else "updated",
            "article_id": article_id,
            "slug": normalized["slug"],
            "title": payload["title"],
            "word_count": payload["word_count"],
            "section_count": len(payload.get("sections", [])),
            "featured_image_url": payload.get("featured_image_url"),
            "hero_image_url": payload.get("hero_image_url"),
            "research_cost": total_cost,
            "completeness_score": completeness,
            "company_mentions": len(payload["mentioned_companies"]),
            "publication_status": payload["status"],
            "zep_graph_id": payload.get("zep_graph_id")
        }
