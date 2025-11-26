"""
Narrative Article Creation Workflow - Video-First 3-Act Storytelling

This workflow builds a 3-act narrative FIRST, then generates both:
1. Video (from narrative.video_prompt)
2. Article (from narrative.acts with key_points)

The video and article tell ONE unified story.

Flow:
1. Research + Curation (same as before)
2. BUILD 3-ACT NARRATIVE (NEW - from curated research)
3. Generate video (from narrative.video_prompt)
4. Upload to Mux (get thumbnails at act timestamps)
5. Generate article (from narrative.acts)
6. Save to database (with video_narrative)
7. Sync to Zep
"""

from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
from typing import Dict, Any

with workflow.unsafe.imports_passed_through():
    from src.activities.generation.narrative_builder import (
        generate_mux_narrative_urls,
        generate_chapter_data,
    )


@workflow.defn
class NarrativeArticleCreationWorkflow:
    """
    Video-first narrative article creation.

    Creates articles where video + text tell ONE unified story
    through a 3-act narrative structure.
    """

    @workflow.run
    async def run(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the narrative article creation workflow.

        Args:
            input_dict: {
                "topic": str,
                "article_type": str (news, guide, etc.),
                "app": str (relocation, placement, etc.),
                "video_quality": str (low, medium, high),
                "target_word_count": int (default 2000),
                "custom_slug": str (optional),
            }

        Returns:
            Dict with article, video, narrative structure
        """
        topic = input_dict["topic"]
        article_type = input_dict.get("article_type", "guide")
        app = input_dict.get("app", "relocation")
        video_quality = input_dict.get("video_quality", "medium")
        target_word_count = input_dict.get("target_word_count", 2000)
        custom_slug = input_dict.get("custom_slug")

        workflow.logger.info(f"Starting narrative article creation: {topic}")
        workflow.logger.info(f"Type: {article_type}, App: {app}")

        # ===== PHASE 1: PARALLEL RESEARCH =====
        workflow.logger.info("Phase 1: Parallel research (DataForSEO + Serper + Exa)")

        # Run research in parallel
        dataforseo_task = workflow.execute_activity(
            "dataforseo_news_search" if article_type == "news" else "dataforseo_serp_search",
            args=[topic, app],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )

        serper_task = workflow.execute_activity(
            "serper_news_search",
            args=[topic, 20],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )

        exa_task = workflow.execute_activity(
            "exa_research_topic",
            args=[topic, app, 15],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )

        # Wait for all research
        try:
            dataforseo_data, serper_data, exa_data = await workflow.wait_all([
                dataforseo_task, serper_task, exa_task
            ])
        except Exception as e:
            workflow.logger.warning(f"Some research failed: {e}")
            dataforseo_data = {}
            serper_data = {"articles": []}
            exa_data = {"results": []}

        # Combine news articles
        all_news_articles = []
        all_news_articles.extend(dataforseo_data.get("articles", []))
        all_news_articles.extend(serper_data.get("articles", []))

        workflow.logger.info(f"Research: {len(all_news_articles)} news, {len(exa_data.get('results', []))} exa results")

        # ===== PHASE 2: CRAWL URLS =====
        workflow.logger.info("Phase 2: Crawling relevant URLs")

        urls_to_crawl = []
        for article in all_news_articles[:20]:
            if article.get("url"):
                urls_to_crawl.append(article["url"])
        for result in exa_data.get("results", [])[:10]:
            if result.get("url"):
                urls_to_crawl.append(result["url"])

        crawled_pages = []
        if urls_to_crawl:
            try:
                crawl_result = await workflow.execute_activity(
                    "crawl4ai_batch_crawl",
                    args=[urls_to_crawl[:30], topic],
                    start_to_close_timeout=timedelta(seconds=180),
                    retry_policy=RetryPolicy(maximum_attempts=2)
                )
                crawled_pages = crawl_result.get("pages", [])
            except Exception as e:
                workflow.logger.warning(f"Crawling failed: {e}")

        workflow.logger.info(f"Crawled {len(crawled_pages)} pages")

        # ===== PHASE 3: CURATE RESEARCH =====
        workflow.logger.info("Phase 3: Curating research sources")

        curation_result = await workflow.execute_activity(
            "curate_research_sources",
            args=[topic, all_news_articles, crawled_pages, exa_data.get("results", [])],
            start_to_close_timeout=timedelta(seconds=60)
        )

        workflow.logger.info(f"Curated {len(curation_result.get('curated_sources', []))} sources")

        # Build curated research text for narrative
        curated_text = "\n\n".join([
            f"Source: {s.get('title', '')}\nURL: {s.get('url', '')}\n{s.get('summary', '')}"
            for s in curation_result.get("curated_sources", [])[:15]
        ])

        # ===== PHASE 4: BUILD 3-ACT NARRATIVE =====
        workflow.logger.info("Phase 4: Building 3-act narrative")

        narrative = await workflow.execute_activity(
            "build_3_act_narrative",
            args=[topic, article_type, app, curated_text],
            start_to_close_timeout=timedelta(seconds=90)
        )

        if not narrative.get("success"):
            workflow.logger.error(f"Narrative building failed: {narrative.get('error')}")
            return {"status": "failed", "error": "Narrative building failed"}

        workflow.logger.info(f"Narrative built: {narrative.get('template')} template")
        workflow.logger.info(f"Title: {narrative.get('title', '')[:60]}...")
        workflow.logger.info(f"Acts: {[a.get('title') for a in narrative.get('acts', [])]}")

        # ===== PHASE 5: GENERATE VIDEO =====
        workflow.logger.info("Phase 5: Generating 10-second video from narrative")

        video_prompt = narrative.get("video_prompt", "")
        if not video_prompt:
            workflow.logger.error("No video prompt in narrative")
            return {"status": "failed", "error": "No video prompt"}

        video_result = await workflow.execute_activity(
            "generate_article_video",
            args=[
                narrative.get("title", topic),
                "<p>Narrative-driven article</p>",
                app,
                video_quality,
                10,  # 10 seconds for 3-act structure
                "16:9",
                "wan-2.5",
                video_prompt
            ],
            start_to_close_timeout=timedelta(minutes=10),
            heartbeat_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(f"Video generated: {video_result.get('video_url', '')[:50]}...")

        # ===== PHASE 6: UPLOAD TO MUX =====
        workflow.logger.info("Phase 6: Uploading to Mux")

        mux_result = await workflow.execute_activity(
            "upload_video_to_mux",
            args=[video_result["video_url"], True],
            start_to_close_timeout=timedelta(minutes=5)
        )

        playback_id = mux_result.get("playback_id")
        asset_id = mux_result.get("asset_id")
        duration = mux_result.get("duration", 10)

        workflow.logger.info(f"Mux upload complete: {playback_id}")

        # Generate all Mux URLs for acts
        mux_urls = generate_mux_narrative_urls(playback_id, narrative.get("acts", []))
        mux_urls["playback_id"] = playback_id
        mux_urls["asset_id"] = asset_id

        # Generate chapter data
        chapters = generate_chapter_data(narrative.get("acts", []))

        # ===== PHASE 7: GENERATE ARTICLE =====
        workflow.logger.info("Phase 7: Generating narrative article")

        research_context = {
            "curated_sources": curation_result.get("curated_sources", []),
            "key_facts": curation_result.get("key_facts", []),
            "high_authority_sources": curation_result.get("high_authority_sources", []),
            "news_articles": all_news_articles[:15],
            "exa_results": exa_data.get("results", [])[:10],
        }

        article_result = await workflow.execute_activity(
            "generate_narrative_article",
            args=[narrative, research_context, app, mux_urls, target_word_count],
            start_to_close_timeout=timedelta(minutes=3)
        )

        if not article_result.get("success"):
            workflow.logger.error(f"Article generation failed: {article_result.get('error')}")
            return {"status": "failed", "error": "Article generation failed"}

        article = article_result["article"]
        workflow.logger.info(f"Article generated: {article['word_count']} words")

        # ===== PHASE 8: SAVE TO DATABASE =====
        workflow.logger.info("Phase 8: Saving to database")

        # Build video_narrative payload
        video_narrative = {
            "template": narrative.get("template"),
            "acts": narrative.get("acts", []),
            "chapters": chapters,
            "mux_urls": mux_urls,
            "video_prompt": video_prompt[:500],
        }

        article_id = await workflow.execute_activity(
            "save_article_to_neon",
            args=[
                None,  # article_id (new)
                article["slug"],
                article["title"],
                app,
                article_type,
                article,
                mux_urls.get("acts", {}).get("act_1", {}).get("thumbnail"),  # featured_asset
                None,  # hero_asset
                [],  # mentioned_companies
                "draft",
                mux_urls.get("stream_url"),
                playback_id,
                asset_id,
                curated_text[:5000],  # raw_research
                video_narrative,  # NEW: video_narrative column
            ],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(f"Article saved: {article_id}")

        # ===== PHASE 9: SYNC TO ZEP =====
        workflow.logger.info("Phase 9: Syncing to Zep")

        try:
            await workflow.execute_activity(
                "sync_article_to_zep",
                args=[
                    article_id,
                    article["slug"],
                    article["title"],
                    article.get("content", "")[:8000],
                    app,
                    article_type,
                    curation_result.get("curated_sources", [])[:10],
                ],
                start_to_close_timeout=timedelta(minutes=2)
            )
            workflow.logger.info("Zep sync complete")
        except Exception as e:
            workflow.logger.warning(f"Zep sync failed (non-critical): {e}")

        # ===== RETURN RESULT =====
        return {
            "status": "created",
            "article_id": article_id,
            "slug": article["slug"],
            "title": article["title"],
            "word_count": article["word_count"],
            "narrative_template": narrative.get("template"),
            "acts": [a.get("title") for a in narrative.get("acts", [])],
            "video_playback_id": playback_id,
            "video_duration": duration,
            "mux_urls": {
                "stream": mux_urls.get("stream_url"),
                "act_1_thumbnail": mux_urls.get("acts", {}).get("act_1", {}).get("thumbnail"),
                "act_2_thumbnail": mux_urls.get("acts", {}).get("act_2", {}).get("thumbnail"),
                "act_3_thumbnail": mux_urls.get("acts", {}).get("act_3", {}).get("thumbnail"),
            },
            "chapters": chapters,
            "costs": {
                "narrative": narrative.get("cost", 0),
                "video": video_result.get("cost", 0),
                "article": article_result.get("cost", 0),
            }
        }
