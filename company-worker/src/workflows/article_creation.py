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
                "num_research_sources": 10
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
        num_sources = input_dict.get("num_research_sources", 10)

        workflow.logger.info(f"Creating {article_type} article: {topic}")

        # ===== PHASE 1: RESEARCH TOPIC =====
        workflow.logger.info("Phase 1: Parallel research (Serper + Exa)")

        # Serper news search
        news_task = workflow.execute_activity(
            "fetch_company_news",  # Reuse! Works for any topic
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
        workflow.logger.info("Phase 2: Crawling discovered URLs (full content)")

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

        workflow.logger.info(f"Crawling {len(urls_to_crawl)} discovered URLs")

        # Crawl ALL URLs to get full content (avoid paywalls!)
        crawl_tasks = []
        for url in urls_to_crawl[:num_sources]:  # Limit to num_sources
            task = workflow.execute_activity(
                "crawl4ai_crawl",  # Use Crawl4AI service with fallback
                args=[url],
                start_to_close_timeout=timedelta(minutes=2)
            )
            crawl_tasks.append(task)

        if crawl_tasks:
            crawl_results = await asyncio.gather(*crawl_tasks, return_exceptions=True)
        else:
            crawl_results = []

        # Extract pages from successful crawls
        crawled_pages = []
        for result in crawl_results:
            if not isinstance(result, Exception) and result.get("success"):
                pages = result.get("pages", [])
                crawled_pages.extend(pages)

        workflow.logger.info(f"Crawled {len(crawled_pages)} pages successfully")

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
            args=[topic, article_type, app, research_context, target_word_count],
            start_to_close_timeout=timedelta(minutes=3)
        )

        if not article_result.get("success"):
            workflow.logger.error("Article generation failed")
            return {
                "status": "failed",
                "error": article_result.get("error", "Unknown error"),
                "article_id": None
            }

        article = article_result["article"]

        workflow.logger.info(
            f"Article generated: {article['word_count']} words, "
            f"{article['section_count']} sections"
        )

        # ===== PHASE 5: ANALYZE SECTIONS (for images) =====
        if generate_images:
            workflow.logger.info("Phase 5: Analyzing sections for image generation")

            section_analysis = await workflow.execute_activity(
                "analyze_article_sections",
                args=[article["content"], article["title"], app],
                start_to_close_timeout=timedelta(seconds=30)
            )

            workflow.logger.info(
                f"Section analysis: {section_analysis['recommended_image_count']} images recommended"
            )

            # ===== PHASE 6: GENERATE SEQUENTIAL IMAGES =====
            workflow.logger.info("Phase 6: Generating sequential contextual images")

            # Generate article_id for image storage (temporary, will be replaced after DB save)
            import hashlib
            temp_article_id = hashlib.md5(topic.encode()).hexdigest()[:12]

            images_result = await workflow.execute_activity(
                "generate_sequential_article_images",
                args=[
                    temp_article_id,
                    article["title"],
                    article["content"],
                    app,
                    "kontext-pro",  # Always use Pro for articles
                    True,  # generate_featured
                    True,  # generate_hero
                    3,  # min_content_images
                    5   # max_content_images
                ],
                start_to_close_timeout=timedelta(minutes=10)
            )

            # Update article with image URLs
            article["featured_image_url"] = images_result.get("featured_image_url")
            article["featured_image_alt"] = images_result.get("featured_image_alt")
            article["hero_image_url"] = images_result.get("hero_image_url")
            article["hero_image_alt"] = images_result.get("hero_image_alt")

            # Content images (up to 5)
            for i in range(1, 6):
                url_key = f"content_image{i}_url"
                alt_key = f"content_image{i}_alt"
                if images_result.get(url_key):
                    article[url_key] = images_result[url_key]
                    article[alt_key] = images_result.get(alt_key)

            article["image_count"] = images_result.get("images_generated", 0)

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
                article.get("mentioned_companies", []),
                "draft"  # status
            ],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(f"Article saved to database with ID: {article_id}")

        # ===== PHASE 8: SYNC TO ZEP =====
        workflow.logger.info("Phase 8: Syncing to Zep knowledge graph")

        # TODO: Implement sync_article_to_zep activity
        # Will extract entities and create graph nodes

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
            "company_mentions": article.get("company_mention_count", 0),
            "featured_image_url": article.get("featured_image_url"),
            "hero_image_url": article.get("hero_image_url"),
            "research_cost": total_cost,
            "completeness_score": article.get("completeness_score", 0.0),
            "article": article  # Full payload for debugging
        }
