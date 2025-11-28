"""
Country Guide Creation Workflow

Temporal workflow for comprehensive country relocation guides.

Generates guides covering all 8 motivations:
- corporate, trust, wealth, retirement, digital-nomad, lifestyle, new-start, family

Outputs:
- Article in articles table (with country_code and guide_type)
- Updated countries row with facts JSONB
- 4-act video via Mux

Timeline: 8-15 minutes
"""

from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
import asyncio
from typing import Dict, Any


@workflow.defn
class CountryGuideCreationWorkflow:
    """
    Comprehensive country guide creation workflow.

    Phases:
    1. Country Setup (5s) - Create/update country row
    2. SEO Research (60s) - DataForSEO keyword research for country
    3. Authoritative Research (120s) - Exa + DataForSEO for gov sites, tax info
    4. Crawl Sources (90s) - Crawl4AI for discovered URLs
    5. Curate Research (30s) - AI filter and summarize
    6. Zep Context (5s) - Query knowledge graph
    7. Generate Guide (180s) - AI generates 8-motivation content
    8. Save Article (5s) - Save to articles table
    9. Link to Country (5s) - Set country_code and guide_type
    10. Update Country Facts (5s) - Merge facts into countries.facts JSONB
    11. Sync to Zep (5s) - Update knowledge graph
    12. Generate Video (5min) - 4-act Seedance video
    13. Final Update (5s) - Add video to article
    """

    @workflow.run
    async def run(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute country guide creation workflow.

        Args:
            input_dict: {
                "country_name": "Cyprus",
                "country_code": "CY",  # ISO 3166-1 alpha-2
                "app": "relocation",
                "language": "Greek, Turkish, English",  # Optional
                "relocation_motivations": ["corporate", ...],  # Optional, defaults to all
                "relocation_tags": ["eu-member", ...],  # Optional
                "video_quality": "medium",  # Optional
                "target_word_count": 4000  # Optional
            }

        Returns:
            Dict with article_id, country_id, slug, status, metrics
        """
        country_name = input_dict["country_name"]
        country_code = input_dict["country_code"]
        app = input_dict.get("app", "relocation")
        language = input_dict.get("language")
        relocation_motivations = input_dict.get("relocation_motivations")
        relocation_tags = input_dict.get("relocation_tags")
        video_quality = input_dict.get("video_quality", "medium")
        target_word_count = input_dict.get("target_word_count", 4000)

        workflow.logger.info(f"Creating country guide for {country_name} ({country_code})")

        # Tracking metrics
        metrics = {
            "research_sources": 0,
            "crawled_urls": 0,
            "word_count": 0,
            "facts_extracted": 0
        }

        # ===== PHASE 1: COUNTRY SETUP =====
        workflow.logger.info("Phase 1: Country Setup - Creating/updating country row")

        country_result = await workflow.execute_activity(
            "save_or_create_country",
            args=[country_name, country_code, language, relocation_motivations, relocation_tags],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )

        country_id = country_result.get("country_id")
        country_slug = country_result.get("slug")
        workflow.logger.info(f"Country {'created' if country_result.get('created') else 'updated'}: {country_slug} (ID: {country_id})")

        # ===== PHASE 2: SEO RESEARCH =====
        workflow.logger.info("Phase 2: SEO Research - DataForSEO keyword research")

        seo_keywords = {}
        try:
            seo_result = await workflow.execute_activity(
                "research_country_seo_keywords",
                args=[country_name, "UK", 30],  # UK region, 30 keywords per seed
                start_to_close_timeout=timedelta(minutes=3),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            seo_keywords = seo_result
            workflow.logger.info(f"SEO research: {seo_result.get('total_keywords', 0)} keywords, volume {seo_result.get('total_volume', 0)}")

            # Save SEO keywords to country
            await workflow.execute_activity(
                "update_country_seo_keywords",
                args=[country_code, seo_keywords],
                start_to_close_timeout=timedelta(seconds=30)
            )
        except Exception as e:
            workflow.logger.warning(f"SEO research failed (non-blocking): {e}")

        # ===== PHASE 3: AUTHORITATIVE RESEARCH =====
        workflow.logger.info("Phase 3: Authoritative Research - Exa + DataForSEO")

        # Build research queries for country guide
        research_queries = [
            f"{country_name} visa requirements official",
            f"{country_name} digital nomad visa 2025",
            f"{country_name} tax residency expat",
            f"{country_name} cost of living expat",
            f"{country_name} golden visa investment",
            f"{country_name} retirement visa requirements",
            f"{country_name} corporate tax rate",
            f"relocate to {country_name} guide",
        ]

        # Parallel research: Exa + DataForSEO
        try:
            exa_task = workflow.execute_activity(
                "exa_research_topic",
                args=[f"{country_name} relocation guide", "guide", app],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )

            dataforseo_task = workflow.execute_activity(
                "dataforseo_serp_search",
                args=[
                    f"{country_name} visa tax cost of living expat relocation",
                    "UK",
                    50,  # depth
                    True,  # include AI overview
                    6  # people also ask depth
                ],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )

            exa_result, dataforseo_result = await asyncio.gather(
                exa_task, dataforseo_task, return_exceptions=True
            )

            # Combine results
            research_urls = []
            research_content = []

            if not isinstance(exa_result, Exception):
                research_content.append(exa_result.get("summary", ""))
                research_urls.extend(exa_result.get("urls", [])[:20])
                metrics["research_sources"] += len(exa_result.get("urls", []))

            if not isinstance(dataforseo_result, Exception):
                items = dataforseo_result.get("items", [])
                for item in items[:30]:
                    if item.get("url"):
                        research_urls.append(item["url"])
                    if item.get("description"):
                        research_content.append(item["description"])
                metrics["research_sources"] += len(items)

            workflow.logger.info(f"Research collected: {len(research_urls)} URLs, {len(research_content)} summaries")

        except Exception as e:
            workflow.logger.error(f"Research phase failed: {e}")
            research_urls = []
            research_content = []

        # ===== PHASE 4: CRAWL SOURCES =====
        workflow.logger.info("Phase 4: Crawl Sources - Crawl4AI batch crawl")

        crawled_content = []
        if research_urls:
            try:
                # Pre-filter URLs by relevancy
                filtered_urls = await workflow.execute_activity(
                    "prefilter_urls_by_relevancy",
                    args=[research_urls[:40], f"{country_name} relocation visa tax"],
                    start_to_close_timeout=timedelta(minutes=2)
                )

                relevant_urls = [u.get("url") for u in filtered_urls.get("relevant", [])][:15]

                if relevant_urls:
                    crawl_result = await workflow.execute_activity(
                        "crawl4ai_batch_crawl",
                        args=[relevant_urls],
                        start_to_close_timeout=timedelta(minutes=3),
                        retry_policy=RetryPolicy(maximum_attempts=2)
                    )

                    for result in crawl_result.get("results", []):
                        if result.get("content"):
                            crawled_content.append({
                                "url": result.get("url"),
                                "title": result.get("title", ""),
                                "content": result.get("content", "")[:8000]  # Limit per source
                            })

                    metrics["crawled_urls"] = len(crawled_content)
                    workflow.logger.info(f"Crawled {len(crawled_content)} sources")

            except Exception as e:
                workflow.logger.warning(f"Crawl phase failed (non-blocking): {e}")

        # ===== PHASE 5: CURATE RESEARCH =====
        workflow.logger.info("Phase 5: Curate Research - AI filter and summarize")

        # Build research context for generation (will be enhanced by curation)
        research_context = {
            "country": country_name,
            "code": country_code,
            "summaries": research_content[:10],
            "crawled_sources": crawled_content[:15],
            "seo_keywords": seo_keywords.get("primary_keywords", [])[:10],
            "questions": seo_keywords.get("questions", [])[:15]
        }

        try:
            # curate_research_sources expects: (topic, crawled_pages, news_articles, exa_results, max_sources)
            curation_result = await workflow.execute_activity(
                "curate_research_sources",
                args=[
                    f"{country_name} relocation guide",  # topic
                    crawled_content,  # crawled_pages (list of dicts)
                    [],  # news_articles (empty for country guides)
                    [],  # exa_results (empty - we already have exa in crawled_content)
                    20   # max_sources
                ],
                start_to_close_timeout=timedelta(minutes=2)
            )

            research_context["curated_summary"] = curation_result.get("summary", "")
            research_context["key_facts"] = curation_result.get("key_facts", [])
            research_context["curated_sources"] = curation_result.get("curated_sources", [])

            workflow.logger.info(f"Curation complete: {len(research_context.get('curated_sources', []))} curated sources")

        except Exception as e:
            workflow.logger.warning(f"Curation failed (non-blocking): {e}")

        # ===== PHASE 6: ZEP CONTEXT =====
        workflow.logger.info("Phase 6: Query Zep for existing knowledge")

        try:
            zep_context = await workflow.execute_activity(
                "query_zep_for_context",
                args=[f"{country_name} relocation visa tax", country_name.lower(), app],
                start_to_close_timeout=timedelta(seconds=30)
            )

            if zep_context.get("facts"):
                research_context["zep_facts"] = zep_context["facts"]
                workflow.logger.info(f"Zep returned {len(zep_context.get('facts', []))} facts")

        except Exception as e:
            workflow.logger.warning(f"Zep query failed (non-blocking): {e}")

        # ===== PHASE 7: GENERATE GUIDE =====
        workflow.logger.info("Phase 7: Generate Country Guide - AI with 8 motivations")

        article = await workflow.execute_activity(
            "generate_country_guide_content",
            args=[country_name, country_code, research_context, seo_keywords, target_word_count],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )

        metrics["word_count"] = article.get("word_count", 0)
        workflow.logger.info(f"Guide generated: {metrics['word_count']} words, {len(article.get('motivations', []))} motivations")

        # ===== PHASE 8: SAVE ARTICLE =====
        workflow.logger.info("Phase 8: Save Article to database")

        article_id = await workflow.execute_activity(
            "save_article_to_neon",
            args=[
                None,  # article_id (new)
                article.get("slug"),
                article.get("title"),
                app,
                "country_guide",  # article_type
                article,  # payload
                None,  # featured_asset_url (added later)
                None,  # hero_asset_url
                None,  # mentioned_companies
                "draft",  # status
            ],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )

        workflow.logger.info(f"Article saved: ID {article_id}")

        # ===== PHASE 9: LINK TO COUNTRY =====
        workflow.logger.info("Phase 9: Link article to country")

        await workflow.execute_activity(
            "link_article_to_country",
            args=[article_id, country_code, "country_comprehensive"],
            start_to_close_timeout=timedelta(seconds=30)
        )

        # ===== PHASE 10: UPDATE COUNTRY FACTS =====
        workflow.logger.info("Phase 10: Update country facts JSONB")

        extracted_facts = await workflow.execute_activity(
            "extract_country_facts",
            args=[article],
            start_to_close_timeout=timedelta(seconds=30)
        )

        await workflow.execute_activity(
            "update_country_facts",
            args=[country_code, extracted_facts, True],  # merge=True
            start_to_close_timeout=timedelta(seconds=30)
        )

        metrics["facts_extracted"] = len(extracted_facts)
        workflow.logger.info(f"Updated {len(extracted_facts)} facts for {country_code}")

        # ===== PHASE 11: SYNC TO ZEP =====
        workflow.logger.info("Phase 11: Sync to Zep knowledge graph")

        try:
            await workflow.execute_activity(
                "sync_article_to_zep",
                args=[
                    str(article_id),  # article_id
                    article.get("title", ""),  # title
                    article.get("slug", ""),  # slug
                    article.get("content", ""),  # content
                    article.get("excerpt", ""),  # excerpt
                    "country_guide",  # article_type
                    [],  # mentioned_companies
                    app  # app
                ],
                start_to_close_timeout=timedelta(minutes=1)
            )
            workflow.logger.info("Article synced to Zep")
        except Exception as e:
            workflow.logger.warning(f"Zep sync failed (non-blocking): {e}")

        # ===== PHASE 12: GENERATE VIDEO (BLOCKING) =====
        video_url = None
        video_playback_id = None
        video_asset_id = None

        if video_quality:
            workflow.logger.info("Phase 12: Generate 4-act video (BLOCKING - will fail workflow if video fails)")

            # Generate video prompt from four_act_content
            four_act_content = article.get("four_act_content", [])
            video_prompt = await workflow.execute_activity(
                "generate_country_video_prompt",
                args=[country_name, four_act_content],
                start_to_close_timeout=timedelta(seconds=30)
            )

            workflow.logger.info(f"Generated video prompt: {video_prompt[:100] if video_prompt else 'NONE'}...")

            # Generate video - BLOCKING (no try/except, will fail workflow if video fails)
            # Args: title, content, app, quality, duration, aspect_ratio, video_model, video_prompt
            video_result = await workflow.execute_activity(
                "generate_four_act_video",
                args=[
                    article.get("title", ""),      # title
                    article.get("content", ""),    # content
                    app,                           # app
                    video_quality,                 # quality
                    12,                            # duration (4-act = 12s)
                    "16:9",                        # aspect_ratio
                    "seedance",                    # video_model
                    video_prompt                   # video_prompt - THE ACTUAL PROMPT!
                ],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )

            # Video result contains video_url directly (from Replicate)
            video_url = video_result.get("video_url")
            workflow.logger.info(f"Video generated: {video_url[:60] if video_url else 'NONE'}...")

            if video_url:
                # Upload to Mux
                mux_result = await workflow.execute_activity(
                    "upload_video_to_mux",
                    args=[video_url],
                    start_to_close_timeout=timedelta(minutes=5)
                )

                video_url = mux_result.get("playback_url")
                video_playback_id = mux_result.get("playback_id")
                video_asset_id = mux_result.get("asset_id")

                workflow.logger.info(f"Video uploaded to Mux: {video_playback_id}")
        else:
            workflow.logger.info("Phase 12: Skipping video (video_quality not set)")

        # ===== PHASE 13: FINAL UPDATE =====
        workflow.logger.info("Phase 13: Final update with video")

        # Build video_narrative for thumbnails
        video_narrative = None
        if video_playback_id:
            four_act = article.get("four_act_content", [])
            video_narrative = {
                "playback_id": video_playback_id,
                "duration": 12,
                "acts": 4,
                "thumbnails": {
                    "hero": f"https://image.mux.com/{video_playback_id}/thumbnail.jpg?time=10.5&width=1200",
                    "sections": [
                        {
                            "time": i * 3 + 1.5,
                            "title": act.get("title", ""),
                            "thumbnail_url": f"https://image.mux.com/{video_playback_id}/thumbnail.jpg?time={i * 3 + 1.5}&width=800"
                        }
                        for i, act in enumerate(four_act[:4])
                    ]
                }
            }

        # GIF for featured asset
        featured_asset_url = None
        if video_playback_id:
            featured_asset_url = f"https://image.mux.com/{video_playback_id}/animated.gif?start=8&end=12&width=640&fps=12"

        # Final update
        await workflow.execute_activity(
            "save_article_to_neon",
            args=[
                article_id,
                article.get("slug"),
                article.get("title"),
                app,
                "country_guide",
                article,
                featured_asset_url,
                None,  # hero_asset_url
                None,  # mentioned_companies
                "published",  # Publish the guide
                video_url,
                video_playback_id,
                video_asset_id,
                None,  # raw_research
                video_narrative
            ],
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Publish the country
        await workflow.execute_activity(
            "publish_country",
            args=[country_code],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(f"Country guide complete: {country_name} ({country_code})")

        return {
            "article_id": article_id,
            "country_id": country_id,
            "country_code": country_code,
            "slug": article.get("slug"),
            "title": article.get("title"),
            "status": "published",
            "video_playback_id": video_playback_id,
            "metrics": metrics
        }
