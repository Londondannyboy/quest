"""
News Creation Workflow

SCHEDULED workflow that runs daily to find and create news articles.

Pipeline:
1. Fetch news from DataForSEO (primary - ISO timestamps)
2. Fetch news from Serper (supplementary)
3. Deduplicate and merge results
4. Get recent articles (Neon) for duplicate check
5. AI assessment: relevance, priority
6. Build intelligent video prompt for each story
7. Spawn ArticleCreationWorkflow with video-first configuration
"""

import re
from temporalio import workflow
from datetime import timedelta
from typing import Dict, Any, List

with workflow.unsafe.imports_passed_through():
    import asyncio
    from src.config.app_config import get_app_config, get_all_apps


@workflow.defn
class NewsCreationWorkflow:
    """
    Scheduled workflow that creates news articles with intelligent video prompts.

    Runs daily (or on schedule) to:
    1. Find relevant news for the app
    2. Use AI to assess if we should cover it
    3. Build intelligent, contextual video prompts
    4. Automatically create articles with video-first configuration
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

        # App-specific primary keywords for DataForSEO research
        dataforseo_keywords_by_app = {
            "placement": "private equity",
            "relocation": "Digital Nomad Visa"
        }
        dataforseo_keyword = dataforseo_keywords_by_app.get(app, "private equity")

        workflow.logger.info(f"DataForSEO primary keyword: {dataforseo_keyword}")

        # ===== PHASE 1A: FETCH NEWS FROM DATAFORSEO =====
        workflow.logger.info("Phase 1a: Fetching news from DataForSEO (UK)")

        dataforseo_result = await workflow.execute_activity(
            "dataforseo_news_search",
            args=[[dataforseo_keyword], ["UK"], 70],
            start_to_close_timeout=timedelta(minutes=10)
        )

        dataforseo_articles = dataforseo_result.get("articles", [])
        workflow.logger.info(f"DataForSEO news: {len(dataforseo_articles)} results")

        # ===== PHASE 1B: FETCH NEWS FROM SERPER (SUPPLEMENTARY) =====
        workflow.logger.info("Phase 1b: Fetching news from Serper (supplementary) - past 24 hours")

        serper_result = await workflow.execute_activity(
            "serper_news_search",
            args=[keywords, geographic_focus, 30, "qdr:d"],  # qdr:d = past 24 hours
            start_to_close_timeout=timedelta(minutes=2)
        )

        serper_articles = serper_result.get("articles", [])
        workflow.logger.info(f"Serper: {len(serper_articles)} results")

        # ===== PHASE 1C: DEDUPLICATE AND MERGE =====
        workflow.logger.info("Phase 1c: Deduplicating and merging results (news + organic + AI overview)")

        # Deduplicate by URL, prioritizing DataForSEO news (has timestamps)
        seen_urls = set()
        stories = []

        # Add DataForSEO news first (has ISO timestamps)
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
        workflow.logger.info(f"Total unique stories: {len(stories)} (dataforseo: {len(dataforseo_articles)}, serper: {len(serper_articles)}) (cost: ${total_cost:.3f})")

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
                priority = story_assessment.get("priority", "medium")
                story_title = story.get("title", "")

                workflow.logger.info(f"Creating article: {story_title[:50]}...")

                # ===== PHASE 3.5: CHECK ZEP FOR EXISTING COVERAGE =====
                # Query Zep to see if this story already exists
                zep_check = await workflow.execute_activity(
                    "query_zep_for_context",
                    args=[story_title, "", app],  # Story title as company_name, empty domain
                    start_to_close_timeout=timedelta(seconds=30)
                )

                existing_articles = zep_check.get("articles", [])

                if existing_articles:
                    # Check if it's a recent duplicate or old developing story
                    most_recent = existing_articles[0] if existing_articles else None
                    if most_recent:
                        recent_timestamp = most_recent.get("created_at") or most_recent.get("timestamp", "")
                        story_timestamp = story.get("timestamp", story.get("time_published", ""))

                        # Simple time check: if both from today, skip as duplicate
                        # In real implementation, would parse timestamps properly
                        if recent_timestamp and story_timestamp:
                            # Skip if both are from same date (avoid republishing same day)
                            if recent_timestamp[:10] == story_timestamp[:10]:  # Compare YYYY-MM-DD
                                workflow.logger.info(f"⏭️  SKIP: Recent duplicate - {story_title[:50]}...")
                                continue
                            else:
                                # Old story but same topic - reference it as ongoing saga
                                workflow.logger.info(
                                    f"📰 REFERENCE: Developing story - {story_title[:50]}... "
                                    f"(Previous coverage: {most_recent.get('title', '')})"
                                )

                # ===== PHASE 3.6: KEYWORD RESEARCH (if not provided) =====
                # Auto-research keywords for SEO optimization
                target_keyword = story.get("target_keyword")  # From dashboard, if specified
                secondary_keywords = story.get("secondary_keywords", [])
                keyword_volume = None
                keyword_difficulty = None

                if not target_keyword:
                    workflow.logger.info(f"Phase 3.6: Auto-researching keywords for: {story_title[:50]}...")
                    try:
                        keyword_result = await workflow.execute_activity(
                            "dataforseo_keyword_research",
                            args=[story_title, geographic_focus[0] if geographic_focus else "UK", 10],
                            start_to_close_timeout=timedelta(minutes=2)
                        )

                        keywords_list = keyword_result.get("keywords", [])
                        if keywords_list:
                            # Pick best keyword (highest opportunity_score)
                            best = max(keywords_list, key=lambda k: k.get("opportunity_score", 0))
                            target_keyword = best.get("keyword")
                            keyword_volume = best.get("search_volume")
                            keyword_difficulty = best.get("difficulty_score")

                            # Get 3-5 secondary keywords (excluding best)
                            secondary_keywords = [
                                k.get("keyword") for k in keywords_list[:6]
                                if k.get("keyword") != target_keyword
                            ][:5]

                            workflow.logger.info(
                                f"Keyword selected: '{target_keyword}' "
                                f"(vol={keyword_volume}, diff={keyword_difficulty:.1f}, opp={best.get('opportunity_score', 0):.2f})"
                            )
                        else:
                            workflow.logger.info("No keywords returned from research")
                    except Exception as e:
                        workflow.logger.warning(f"Keyword research failed (non-blocking): {e}")
                        # Continue without keywords - article still generates

                # ===== BUILD ARTICLE INPUT WITH 4-ACT VIDEO CONFIGURATION =====
                # Video prompt is now generated FROM the article's 4-act sections (article-first approach)
                # ArticleCreationWorkflow generates article with four_act_visual_hint per section,
                # then builds 4-act video prompt from those hints
                article_input = {
                    "topic": story.get("title", ""),
                    "article_type": "news",
                    "app": app,
                    "target_word_count": 1500,
                    "jurisdiction": geographic_focus[0] if geographic_focus else "UK",
                    "generate_images": True,
                    "video_quality": "medium" if priority in ["high", "medium"] else None,  # High/medium priority get videos
                    "video_model": "seedance",
                    # video_prompt is now generated FROM article sections (4-act approach)
                    "content_images": "with_content",
                    "num_research_sources": 10,
                    # SEO keyword targeting (Phase 3.6)
                    "target_keyword": target_keyword,
                    "keyword_volume": keyword_volume,
                    "keyword_difficulty": keyword_difficulty,
                    "secondary_keywords": secondary_keywords
                }

                workflow.logger.info(f"Spawning 4-act article workflow for: {story.get('title', '')[:50]}...")

                # Spawn child workflow with descriptive ID including topic
                story_title = story.get("title", "untitled")
                # Slugify: lowercase, replace spaces/special chars with hyphens, limit length
                topic_slug = re.sub(r'[^a-z0-9]+', '-', story_title.lower())[:50].strip('-')
                workflow_id = f"4act-{app}-{topic_slug}-{workflow.uuid4().hex[:6]}"

                try:
                    result = await workflow.execute_child_workflow(
                        "ArticleCreationWorkflow",
                        article_input,
                        id=workflow_id,
                        task_queue=workflow.info().task_queue
                    )

                    articles_created.append({
                        "title": story.get("title"),
                        "article_id": result.get("article_id"),
                        "slug": result.get("slug"),
                        "priority": story_assessment.get("priority"),
                        "target_keyword": target_keyword,
                        "keyword_volume": keyword_volume
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
