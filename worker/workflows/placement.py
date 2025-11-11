"""
Placement Workflow - Dedicated workflow for placement.quest

Focused on financial news, private equity deals, M&A transactions.
Hardcoded with placement-specific image generation prompts.
"""

from datetime import timedelta
from typing import Optional
from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class PlacementWorkflow:
    """
    Dedicated workflow for Placement financial news articles

    This workflow:
    - Searches for financial news
    - Scrapes and extracts entities
    - Generates Bloomberg-style professional articles
    - Generates corporate/financial imagery
    - Saves to database with app='placement'
    """

    def __init__(self) -> None:
        self.approved_story: Optional[dict] = None

    @workflow.run
    async def run(
        self,
        topic: str,
        target_word_count: int = 1500,
        auto_approve: bool = True,
        skip_zep_check: bool = True
    ) -> dict:
        """
        Run the placement workflow

        Args:
            topic: Financial topic to generate article about
            target_word_count: Target word count for article
            auto_approve: If True, skip manual approval
            skip_zep_check: If True, skip Zep coverage check

        Returns:
            Complete Article dict
        """
        app = "placement"  # Hardcoded for this workflow

        workflow.logger.info(f"🚀 Placement workflow started")
        workflow.logger.info(f"   Topic: {topic}")
        workflow.logger.info(f"   Target words: {target_word_count}")

        # Configure retry policy
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3,
            backoff_coefficient=2.0,
        )

        # =====================================================================
        # STAGE 0: ZEP COVERAGE CHECK
        # =====================================================================
        if not skip_zep_check:
            workflow.logger.info("=" * 60)
            workflow.logger.info("🔍 STAGE 0: ZEP COVERAGE CHECK")
            workflow.logger.info("=" * 60)

            coverage_result = await workflow.execute_activity(
                "check_zep_coverage",
                args=[topic, app, 0.85],
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry_policy,
            )

            workflow.logger.info(f"   Novelty score: {coverage_result.get('novelty_score', 0):.2f}")
            workflow.logger.info(f"   Recommendation: {coverage_result.get('recommendation', 'unknown')}")

        # =====================================================================
        # STAGE 1: SEARCH NEWS
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("📰 STAGE 1: NEWS SEARCH")
        workflow.logger.info("=" * 60)

        search_input = {
            "keyword": topic,
            "location": "UK",
            "language": "en",
            "num_results": 5
        }

        news_output = await workflow.execute_activity(
            "search_news_serper",
            search_input,
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )

        news_items = news_output.get('news_items', [])
        news_urls = [item.get('link') for item in news_items if item.get('link')]

        workflow.logger.info(f"✅ Found {len(news_urls)} news articles")

        # =====================================================================
        # STAGE 2: SCRAPE SOURCES
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("📚 STAGE 2: SCRAPE SOURCES")
        workflow.logger.info("=" * 60)

        sources = [
            {
                "url": url,
                "title": f"News: {topic}",
                "content": "",
                "credibility_score": 8.0,
                "published_date": None,
                "author": None
            }
            for url in news_urls[:5]
        ]

        scraped_sources = await workflow.execute_activity(
            "deep_scrape_sources",
            sources,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )

        workflow.logger.info(f"✅ Scraped {len(scraped_sources)} sources")

        # =====================================================================
        # STAGE 3: EXTRACT ENTITIES
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🔍 STAGE 3: ENTITY EXTRACTION")
        workflow.logger.info("=" * 60)

        entity_data = await workflow.execute_activity(
            "extract_entities_from_news",
            scraped_sources,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )

        entities = entity_data.get("entities", [])
        themes = entity_data.get("themes", [])

        workflow.logger.info(f"✅ Extracted {len(entities)} entities, {len(themes)} themes")

        # =====================================================================
        # STAGE 4: CREATE BRIEF
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("📋 STAGE 4: CREATE BRIEF")
        workflow.logger.info("=" * 60)

        brief = {
            "title": f"{topic} - Latest Developments",
            "angle": themes[0] if themes else "Industry analysis",
            "target_word_count": target_word_count,
            "source_urls": news_urls,
            "approved_by": "system" if auto_approve else "manual",
        }

        workflow.logger.info(f"✅ Brief created: {brief['title']}")

        # =====================================================================
        # STAGE 5: EXTRACT ENTITIES & CITATIONS
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🔍 STAGE 5: DETAILED EXTRACTION")
        workflow.logger.info("=" * 60)

        research_brief = await workflow.execute_activity(
            "extract_entities_citations",
            args=[brief, scraped_sources],
            start_to_close_timeout=timedelta(minutes=3),
            retry_policy=retry_policy,
        )

        workflow.logger.info(f"✅ Research complete: {len(research_brief.get('entities', []))} entities")

        # =====================================================================
        # STAGE 6: GENERATE ARTICLE
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("✍️  STAGE 6: ARTICLE GENERATION")
        workflow.logger.info("=" * 60)

        article_data = await workflow.execute_activity(
            "generate_article",
            args=[brief, research_brief, app],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        article_data['app'] = app

        workflow.logger.info(f"✅ Article generated: {article_data.get('word_count', 0)} words")

        # =====================================================================
        # STAGE 7: CALCULATE QUALITY
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("📊 STAGE 7: QUALITY SCORE")
        workflow.logger.info("=" * 60)

        quality_score = await workflow.execute_activity(
            "calculate_quality_score",
            article_data,
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )

        workflow.logger.info(f"✅ Quality score: {quality_score:.1f}/10")

        # =====================================================================
        # STAGE 7.5: GENERATE IMAGES
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🎨 STAGE 7.5: IMAGE GENERATION")
        workflow.logger.info("=" * 60)

        # Use dedicated placement image generation activity
        image_urls = await workflow.execute_activity(
            "generate_placement_images",
            args=[article_data.get("id"),
                  article_data.get("title", "Untitled"),
                  brief.get("angle", "")],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )

        article_data['images'] = image_urls
        if image_urls.get('hero'):
            workflow.logger.info(f"✅ Generated 6 placement images: hero, featured, content, content2, content3, content4")
        else:
            workflow.logger.info(f"⚠️  Image generation skipped (API keys not set)")

        # =====================================================================
        # STAGE 8: SAVE TO DATABASE
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("💾 STAGE 8: DATABASE SAVE")
        workflow.logger.info("=" * 60)

        saved = await workflow.execute_activity(
            "save_to_neon",
            args=[article_data, brief],
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )

        if saved:
            workflow.logger.info(f"✅ Article saved to database (app: {app})")
        else:
            workflow.logger.error("❌ Failed to save article")

        # =====================================================================
        # STAGE 9: SYNC TO KNOWLEDGE BASE
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🔗 STAGE 9: KNOWLEDGE BASE SYNC")
        workflow.logger.info("=" * 60)

        zep_episode_id = await workflow.execute_activity(
            "sync_article_to_zep",
            article_data,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )

        workflow.logger.info(f"✅ Article synced to Zep: {zep_episode_id}")

        facts_result = await workflow.execute_activity(
            "extract_facts_to_zep",
            args=[article_data,
                  entity_data.get("entities", []),
                  entity_data.get("themes", [])],
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )

        workflow.logger.info(f"✅ Extracted {facts_result.get('fact_count', 0)} facts to Zep")

        article_data['zep_graph_id'] = zep_episode_id
        article_data['zep_episode_id'] = zep_episode_id
        article_data['neon_saved'] = saved

        workflow.logger.info(f"✅ Knowledge base sync complete")

        # =====================================================================
        # WORKFLOW COMPLETE
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🎉 PLACEMENT WORKFLOW COMPLETE")
        workflow.logger.info("=" * 60)

        workflow.logger.info(f"   Title: {article_data.get('title', 'Unknown')}")
        workflow.logger.info(f"   Words: {article_data.get('word_count', 0)}")
        workflow.logger.info(f"   Quality: {quality_score:.1f}/10")
        workflow.logger.info(f"   App: {app}")
        workflow.logger.info(f"   Saved: {saved}")
        workflow.logger.info("=" * 60)

        return article_data

    @workflow.query
    def get_status(self) -> dict:
        """Query the current workflow status"""
        return {
            "approved_story": self.approved_story
        }
