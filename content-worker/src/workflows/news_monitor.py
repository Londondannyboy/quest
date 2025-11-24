"""
News Monitor Workflow

SCHEDULED workflow that runs daily to find and create news articles.

Pipeline:
1. Fetch news from DataForSEO (primary - ISO timestamps)
2. Fetch news from Serper (supplementary)
3. Deduplicate and merge results
4. Get recent articles (Neon) for duplicate check
5. AI assessment: relevance, priority
6. Spawn ArticleCreationWorkflow for relevant stories
"""

from temporalio import workflow
from datetime import timedelta
from typing import Dict, Any, List

with workflow.unsafe.imports_passed_through():
    from src.config.app_config import get_app_config, get_all_apps


@workflow.defn
class NewsMonitorWorkflow:
    """
    Scheduled workflow that monitors news and creates articles.

    Runs daily (or on schedule) to:
    1. Find relevant news for the app
    2. Use AI to assess if we should cover it
    3. Automatically create articles for high-priority stories
    """

    @workflow.run
    async def run(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute news monitoring workflow.

        Args:
            input_dict: {
                "app": "placement",
                "min_relevance_score": 0.7,
                "auto_create_articles": True,
                "max_articles_to_create": 3
            }

        Returns:
            Summary of monitoring results
        """
        app = input_dict.get("app", "placement")
        min_relevance = input_dict.get("min_relevance_score", 0.7)
        auto_create = input_dict.get("auto_create_articles", True)
        max_articles = input_dict.get("max_articles_to_create", 3)

        # Get full app configuration
        app_config = get_app_config(app)
        keywords = app_config.keywords
        exclusions = app_config.exclusions
        interests = app_config.interests
        geographic_focus = app_config.geographic_focus
        priority_sources = app_config.priority_sources
        target_audience = app_config.target_audience

        workflow.logger.info(f"News Monitor starting for app: {app}")
        workflow.logger.info(f"Keywords: {keywords[:3]}...")
        workflow.logger.info(f"Geographic focus: {geographic_focus}")

        # ===== PHASE 1A: FETCH NEWS FROM DATAFORSEO (PRIMARY) =====
        workflow.logger.info("Phase 1a: Fetching news from DataForSEO (primary)")

        # Map geographic focus to DataForSEO region codes
        dataforseo_regions = []
        for geo in geographic_focus:
            if geo.upper() in ["UK", "US", "SG", "EU", "ASIA"]:
                if geo.upper() == "ASIA":
                    dataforseo_regions.append("SG")
                elif geo.upper() == "EU":
                    dataforseo_regions.append("UK")  # Use UK as EU proxy
                else:
                    dataforseo_regions.append(geo.upper())

        if not dataforseo_regions:
            dataforseo_regions = ["UK", "US", "SG"]

        dataforseo_result = await workflow.execute_activity(
            "dataforseo_news_search",
            args=[keywords[:5], dataforseo_regions, 100, "past_24_hours"],
            start_to_close_timeout=timedelta(minutes=3)
        )

        dataforseo_articles = dataforseo_result.get("articles", [])
        workflow.logger.info(f"DataForSEO: {len(dataforseo_articles)} results")

        # ===== PHASE 1B: FETCH NEWS FROM SERPER (SUPPLEMENTARY) =====
        workflow.logger.info("Phase 1b: Fetching news from Serper (supplementary)")

        serper_result = await workflow.execute_activity(
            "serper_news_search",
            args=[keywords, geographic_focus, 30],
            start_to_close_timeout=timedelta(minutes=2)
        )

        serper_articles = serper_result.get("articles", [])
        workflow.logger.info(f"Serper: {len(serper_articles)} results")

        # ===== PHASE 1C: DEDUPLICATE AND MERGE =====
        workflow.logger.info("Phase 1c: Deduplicating and merging results")

        # Deduplicate by URL, prioritizing DataForSEO (has timestamps)
        seen_urls = set()
        stories = []

        # Add DataForSEO first (has ISO timestamps)
        for article in dataforseo_articles:
            url = article.get("url", "").lower().replace("www.", "").split("?")[0]
            if url and url not in seen_urls:
                seen_urls.add(url)
                stories.append(article)

        # Add Serper (supplementary)
        for article in serper_articles:
            url = article.get("url", "").lower().replace("www.", "").split("?")[0]
            if url and url not in seen_urls:
                seen_urls.add(url)
                stories.append(article)

        total_cost = dataforseo_result.get("cost", 0) + serper_result.get("cost", 0)
        workflow.logger.info(f"Total unique stories: {len(stories)} (cost: ${total_cost:.3f})")

        if not stories:
            return {
                "app": app,
                "stories_found": 0,
                "stories_relevant": 0,
                "articles_created": 0,
                "message": "No news stories found for today"
            }

        # ===== PHASE 2: GET RECENT ARTICLES =====
        workflow.logger.info("Phase 2: Getting recently published from Neon")

        recent_articles = await workflow.execute_activity(
            "neon_get_recent_articles",
            args=[app, 7, 50],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(f"Found {len(recent_articles)} recent articles")

        # ===== PHASE 3: AI ASSESSMENT =====
        workflow.logger.info("Phase 3: AI assessment of story relevance")

        # Build app context for AI assessment
        app_context = {
            "keywords": keywords,
            "exclusions": exclusions,
            "interests": interests,
            "target_audience": target_audience,
            "priority_sources": priority_sources
        }

        assessment_result = await workflow.execute_activity(
            "claude_assess_news",
            args=[
                stories,
                app,
                app_context,
                recent_articles,
                min_relevance
            ],
            start_to_close_timeout=timedelta(minutes=5)
        )

        relevant_stories = assessment_result.get("relevant_stories", [])

        workflow.logger.info(
            f"Assessment complete: {len(relevant_stories)} relevant stories "
            f"(high={assessment_result.get('total_high_priority', 0)}, "
            f"medium={assessment_result.get('total_medium_priority', 0)}, "
            f"low={assessment_result.get('total_low_priority', 0)})"
        )

        # ===== PHASE 4: CREATE ARTICLES =====
        articles_created = []

        if auto_create and relevant_stories:
            workflow.logger.info(f"Phase 4: Creating articles for top {max_articles} stories")

            # Sort by priority and relevance
            sorted_stories = sorted(
                relevant_stories,
                key=lambda x: (
                    0 if x.get("priority") == "high" else (1 if x.get("priority") == "medium" else 2),
                    -x.get("relevance_score", 0)
                )
            )

            # Create articles for top stories
            for story_assessment in sorted_stories[:max_articles]:
                story = story_assessment.get("story", {})

                workflow.logger.info(f"Creating article: {story.get('title', '')[:50]}...")

                # Build article input - just pass the topic
                article_input = {
                    "topic": story.get("title", ""),
                    "article_type": "news",
                    "app": app,
                    "target_word_count": 1500,
                    "jurisdiction": geographic_focus[0] if geographic_focus else "UK",
                    "generate_images": True,
                    "num_research_sources": 10
                }

                # Spawn child workflow
                try:
                    result = await workflow.execute_child_workflow(
                        "ArticleCreationWorkflow",
                        article_input,
                        id=f"article-{app}-{workflow.uuid4().hex[:8]}",
                        task_queue=workflow.info().task_queue
                    )

                    articles_created.append({
                        "title": story.get("title"),
                        "article_id": result.get("article_id"),
                        "slug": result.get("slug"),
                        "priority": story_assessment.get("priority")
                    })

                    workflow.logger.info(f"Article created: {result.get('slug')}")

                except Exception as e:
                    workflow.logger.error(f"Failed to create article: {str(e)}")

        # ===== COMPLETE =====
        workflow.logger.info(
            f"News Monitor complete for {app}: "
            f"{len(stories)} found, {len(relevant_stories)} relevant, "
            f"{len(articles_created)} created"
        )

        return {
            "app": app,
            "keywords": keywords[:3],
            "stories_found": len(stories),
            "stories_assessed": assessment_result.get("stories_assessed", 0),
            "stories_relevant": len(relevant_stories),
            "articles_created": len(articles_created),
            "articles": articles_created,
            "high_priority_count": assessment_result.get("total_high_priority", 0),
            "medium_priority_count": assessment_result.get("total_medium_priority", 0),
            "low_priority_count": assessment_result.get("total_low_priority", 0),
            "cost": total_cost,
            "dataforseo_count": len(dataforseo_articles),
            "serper_count": len(serper_articles)
        }
