"""
Article Workflow - Direct article creation from any topic

This workflow bypasses news assessment and creates articles directly
from research topics using Exa for comprehensive research.

Perfect for:
- Evergreen content (e.g., "Digital Nomad Visa Portugal")
- Industry guides and analysis
- Company/product deep dives
- Topic-based research articles
"""

from datetime import timedelta
from typing import Optional
from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class ArticleWorkflow:
    """
    Direct article creation workflow using Exa research

    This workflow:
    - Researches topics using Exa (bypasses news search)
    - Optionally deep crawls additional sources
    - Extracts insights and citations
    - Generates app-aware articles
    - Creates images and saves to database
    """

    def __init__(self) -> None:
        self.approved_brief: Optional[dict] = None

    @workflow.run
    async def run(
        self,
        topic: str,
        app: str = "placement",
        target_word_count: int = 1500,
        num_research_sources: int = 5,
        deep_crawl_enabled: bool = False,
        skip_zep_sync: bool = False
    ) -> dict:
        """
        Run the article workflow

        Args:
            topic: Topic to research and create article about
            app: App context (placement, relocation, etc.)
            target_word_count: Target word count for article
            num_research_sources: Number of Exa sources to retrieve
            deep_crawl_enabled: If True, deep crawl additional URLs
            skip_zep_sync: If True, skip Zep knowledge base sync

        Returns:
            Complete Article dict
        """
        workflow.logger.info(f"🚀 Article Workflow started")
        workflow.logger.info(f"   Topic: {topic}")
        workflow.logger.info(f"   App: {app}")
        workflow.logger.info(f"   Target words: {target_word_count}")
        workflow.logger.info(f"   Research sources: {num_research_sources}")

        # Configure retry policy
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3,
            backoff_coefficient=2.0,
        )

        # =====================================================================
        # STAGE 1: EXA RESEARCH
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🔍 STAGE 1: EXA RESEARCH")
        workflow.logger.info("=" * 60)

        research_input = {
            "topic": topic,
            "num_results": num_research_sources,
            "use_autoprompt": True,
            "category": "research paper"  # Exa will optimize for quality content
        }

        exa_results = await workflow.execute_activity(
            "exa_research_topic",
            research_input,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )

        research_results = exa_results.get('research_results', [])
        autoprompt = exa_results.get('autoprompt_string', None)

        workflow.logger.info(f"✅ Found {len(research_results)} high-quality sources via Exa")
        if autoprompt:
            workflow.logger.info(f"   Exa autoprompt: {autoprompt[:100]}...")

        # =====================================================================
        # STAGE 2: OPTIONAL DEEP CRAWL
        # =====================================================================
        if deep_crawl_enabled and len(research_results) > 0:
            workflow.logger.info("=" * 60)
            workflow.logger.info("🕷️  STAGE 2: DEEP CRAWL (OPTIONAL)")
            workflow.logger.info("=" * 60)

            # Extract URLs for deep crawling
            additional_urls = [r.get('url') for r in research_results if r.get('url')][:3]

            deep_crawl_results = await workflow.execute_activity(
                "deep_research_with_firecrawl",
                additional_urls,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )

            # Merge deep crawl results with Exa results
            for deep_result in deep_crawl_results:
                # Find matching Exa result and enhance it
                for exa_result in research_results:
                    if exa_result.get('url') == deep_result.get('url'):
                        # Enhance with FireCrawl content if longer
                        if len(deep_result.get('content', '')) > len(exa_result.get('content', '')):
                            exa_result['content'] = deep_result['content']
                            workflow.logger.info(f"   Enhanced: {deep_result['url'][:50]}...")

            workflow.logger.info(f"✅ Deep crawl complete")
        else:
            workflow.logger.info("⏭️  Skipping deep crawl (disabled or no sources)")

        # =====================================================================
        # STAGE 3: EXTRACT RESEARCH INSIGHTS
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🔍 STAGE 3: EXTRACT INSIGHTS")
        workflow.logger.info("=" * 60)

        research_brief = await workflow.execute_activity(
            "extract_research_insights",
            args=[topic, research_results, app],
            start_to_close_timeout=timedelta(minutes=3),
            retry_policy=retry_policy,
        )

        entities = research_brief.get("entities", [])
        citations = research_brief.get("citations", [])
        key_findings = research_brief.get("key_findings", [])
        themes = research_brief.get("themes", [])

        workflow.logger.info(f"✅ Extracted:")
        workflow.logger.info(f"   - {len(entities)} entities")
        workflow.logger.info(f"   - {len(citations)} citations")
        workflow.logger.info(f"   - {len(key_findings)} key findings")
        workflow.logger.info(f"   - {len(themes)} themes")

        # =====================================================================
        # STAGE 4: CREATE BRIEF
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("📋 STAGE 4: CREATE BRIEF")
        workflow.logger.info("=" * 60)

        # Create a compelling title and angle from research
        article_title = f"{topic}: Comprehensive Guide"
        if themes and len(themes) > 0:
            article_angle = themes[0]
        elif key_findings and len(key_findings) > 0:
            article_angle = key_findings[0]
        else:
            article_angle = f"Analysis and insights on {topic}"

        brief = {
            "title": article_title,
            "angle": article_angle,
            "target_word_count": target_word_count,
            "source_urls": [r.get('url') for r in research_results],
            "approved_by": "system",
            "app": app
        }

        self.approved_brief = brief

        workflow.logger.info(f"✅ Brief created:")
        workflow.logger.info(f"   Title: {brief['title']}")
        workflow.logger.info(f"   Angle: {brief['angle']}")

        # =====================================================================
        # STAGE 5: GENERATE ARTICLE
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("✍️  STAGE 5: ARTICLE GENERATION")
        workflow.logger.info("=" * 60)

        article_data = await workflow.execute_activity(
            "generate_article",
            args=[brief, research_brief, app],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        article_data['app'] = app

        workflow.logger.info(f"✅ Article generated:")
        workflow.logger.info(f"   Words: {article_data.get('word_count', 0)}")
        workflow.logger.info(f"   Citations: {len(article_data.get('citations', []))}")

        # =====================================================================
        # STAGE 6: CALCULATE QUALITY SCORE
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("📊 STAGE 6: QUALITY SCORE")
        workflow.logger.info("=" * 60)

        quality_score = await workflow.execute_activity(
            "calculate_quality_score",
            article_data,
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )

        article_data['quality_score'] = quality_score

        workflow.logger.info(f"✅ Quality score: {quality_score:.1f}/10")

        # =====================================================================
        # STAGE 7: GENERATE IMAGES
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🎨 STAGE 7: IMAGE GENERATION")
        workflow.logger.info("=" * 60)

        # Use app-aware image generation
        image_urls = await workflow.execute_activity(
            "generate_article_images",
            args=[article_data.get("id"),
                  article_data.get("title", "Untitled"),
                  brief.get("angle", ""),
                  app],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )

        article_data['images'] = image_urls

        if image_urls.get('hero'):
            workflow.logger.info(f"✅ Generated {len(image_urls)} images")
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

        article_data['neon_saved'] = saved

        if saved:
            workflow.logger.info(f"✅ Article saved to database (app: {app})")
        else:
            workflow.logger.error("❌ Failed to save article")

        # =====================================================================
        # STAGE 9: SYNC TO KNOWLEDGE BASE (OPTIONAL)
        # =====================================================================
        if not skip_zep_sync:
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

            # Extract entity names from entity dicts for Zep
            entity_names = [e.get("name", e) if isinstance(e, dict) else e for e in entities]

            facts_result = await workflow.execute_activity(
                "extract_facts_to_zep",
                args=[article_data, entity_names, themes],
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry_policy,
            )

            workflow.logger.info(f"✅ Extracted {facts_result.get('fact_count', 0)} facts to Zep")

            article_data['zep_graph_id'] = zep_episode_id
            article_data['zep_episode_id'] = zep_episode_id
        else:
            workflow.logger.info("⏭️  Skipping Zep sync (disabled)")

        # =====================================================================
        # WORKFLOW COMPLETE
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🎉 ARTICLE WORKFLOW COMPLETE")
        workflow.logger.info("=" * 60)

        workflow.logger.info(f"   Topic: {topic}")
        workflow.logger.info(f"   Title: {article_data.get('title', 'Unknown')}")
        workflow.logger.info(f"   Words: {article_data.get('word_count', 0)}")
        workflow.logger.info(f"   Quality: {quality_score:.1f}/10")
        workflow.logger.info(f"   App: {app}")
        workflow.logger.info(f"   Sources: {len(research_results)}")
        workflow.logger.info(f"   Citations: {len(article_data.get('citations', []))}")
        workflow.logger.info(f"   Saved: {saved}")
        workflow.logger.info("=" * 60)

        return article_data

    @workflow.query
    def get_status(self) -> dict:
        """Query the current workflow status"""
        return {
            "approved_brief": self.approved_brief
        }
