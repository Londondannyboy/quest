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

        # ===== PHASE 2: KEYWORD DISCOVERY =====
        # First step: Discover what people actually search for using DataForSEO Labs
        # This reveals unique audiences (e.g., "portugal visa for indians")
        workflow.logger.info("Phase 2: Keyword Discovery - DataForSEO Labs related_keywords")

        keyword_discovery = {}
        discovered_keywords = []
        unique_audiences = []
        content_themes = {}

        try:
            # Run keyword discovery for both US and UK regions in parallel
            kw_us_task = workflow.execute_activity(
                "dataforseo_related_keywords",
                args=[f"{country_name} relocation", "US", 3, 50],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            kw_uk_task = workflow.execute_activity(
                "dataforseo_related_keywords",
                args=[f"{country_name} relocation", "UK", 3, 50],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )

            kw_us, kw_uk = await asyncio.gather(kw_us_task, kw_uk_task, return_exceptions=True)

            # Combine results
            if not isinstance(kw_us, Exception):
                keyword_discovery["us"] = kw_us
                discovered_keywords.extend(kw_us.get("top_for_serp", []))
                unique_audiences.extend(kw_us.get("unique_audiences", []))
                for theme, kws in kw_us.get("content_themes", {}).items():
                    if theme not in content_themes:
                        content_themes[theme] = []
                    content_themes[theme].extend(kws)
                workflow.logger.info(f"US keywords: {kw_us.get('total', 0)} found, {len(kw_us.get('unique_audiences', []))} unique audiences")

            if not isinstance(kw_uk, Exception):
                keyword_discovery["uk"] = kw_uk
                discovered_keywords.extend(kw_uk.get("top_for_serp", []))
                unique_audiences.extend(kw_uk.get("unique_audiences", []))
                for theme, kws in kw_uk.get("content_themes", {}).items():
                    if theme not in content_themes:
                        content_themes[theme] = []
                    content_themes[theme].extend(kws)
                workflow.logger.info(f"UK keywords: {kw_uk.get('total', 0)} found, {len(kw_uk.get('unique_audiences', []))} unique audiences")

            # Dedupe discovered keywords
            discovered_keywords = list(dict.fromkeys(discovered_keywords))[:15]
            workflow.logger.info(f"Keyword discovery complete: {len(discovered_keywords)} top keywords for SERP")

        except Exception as e:
            workflow.logger.warning(f"Keyword discovery failed (non-blocking): {e}")

        # ===== PHASE 2B: SEO RESEARCH =====
        workflow.logger.info("Phase 2B: SEO Research - DataForSEO detailed keyword research")

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
        # Use DISCOVERED keywords to drive SERP/News searches
        # Fall back to default topics if discovery failed
        workflow.logger.info("Phase 3: Authoritative Research - SERP + News driven by discovered keywords")

        # Build search topics from discovered keywords OR fall back to defaults
        if discovered_keywords:
            # Use top discovered keywords (what people actually search)
            search_topics = discovered_keywords[:10]
            workflow.logger.info(f"Using {len(search_topics)} DISCOVERED keywords for SERP searches")
        else:
            # Fallback: default topics
            search_topics = [
                f"{country_name} relocation",
                f"{country_name} visa requirements",
                f"{country_name} cost of living",
                f"{country_name} tax expat",
                f"{country_name} property",
            ]
            workflow.logger.info(f"Using {len(search_topics)} DEFAULT keywords for SERP searches")

        # Search both UK and US regions for international perspective
        regions = ["UK", "US"]

        try:
            # Build parallel SERP tasks: topics × regions
            # Depth: 20 results each (page 1-2 of Google)
            serp_tasks = []
            for topic in search_topics:
                for region in regions:
                    serp_tasks.append(
                        workflow.execute_activity(
                            "dataforseo_serp_search",
                            args=[topic, region, 20, True, 4],  # 20 depth, AI overview, PAA
                            start_to_close_timeout=timedelta(minutes=2),
                            retry_policy=RetryPolicy(maximum_attempts=2)
                        )
                    )

            workflow.logger.info(f"Launching {len(serp_tasks)} SERP searches ({len(search_topics)} topics × {len(regions)} regions)")

            # NEWS: Use Serper.dev (24-hour recency, better for fresh news)
            # DataForSEO is better for SERP, Serper is better for news timeliness
            news_keywords = search_topics[:6] if search_topics else [f"{country_name} relocation"]
            news_task = workflow.execute_activity(
                "serper_news_search",  # Serper.dev - 24hr recency
                args=[
                    news_keywords,  # Use discovered keywords
                    regions,        # UK + US
                    20,             # depth per query
                    "past_week"     # past_week for country guides (not as time-sensitive as news workflow)
                ],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )

            # EXA: Authoritative/editorial sources - USE DISCOVERED KEYWORDS
            # Build Exa query from discovered keywords for better results
            exa_query = discovered_keywords[0] if discovered_keywords else f"{country_name} relocation guide"
            exa_task = workflow.execute_activity(
                "exa_research_topic",
                args=[exa_query, "guide", app],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )

            # REDDIT: Real expat experiences and opinions (JSON API, no auth needed)
            reddit_task = workflow.execute_activity(
                "reddit_search_expat_content",
                args=[country_name, None, 30, "relevance", "year"],  # country, terms, max, sort, time
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )

            # Run all in parallel (SERP + News + Exa + Reddit)
            all_results = await asyncio.gather(
                *serp_tasks, news_task, exa_task, reddit_task, return_exceptions=True
            )

            # Separate results
            serp_results = all_results[:-3]   # First N are SERP
            news_result = all_results[-3]      # News result
            exa_result = all_results[-2]       # Exa result
            reddit_result = all_results[-1]    # Reddit result

            # Combine results with deduplication
            research_urls = []
            research_content = []
            news_articles = []
            paa_questions = []
            ai_overview_content = []  # NEW: Collect AI Overview answers
            seen_urls = set()

            # Process Exa results first (authoritative sources)
            if not isinstance(exa_result, Exception) and exa_result:
                research_content.append(exa_result.get("summary", ""))
                for url in exa_result.get("urls", [])[:15]:
                    if url and url not in seen_urls:
                        research_urls.append(url)
                        seen_urls.add(url)
                workflow.logger.info(f"Exa: {len(exa_result.get('urls', []))} URLs")

            # Process all SERP results - extract URLs, AI Overview, PAA
            serp_url_count = 0
            for df_result in serp_results:
                if not isinstance(df_result, Exception) and df_result:
                    all_urls = df_result.get("all_urls", [])
                    for item in all_urls[:15]:  # Top 15 per SERP
                        url = item.get("url") if isinstance(item, dict) else item
                        if url and url not in seen_urls:
                            research_urls.append(url)
                            seen_urls.add(url)
                            serp_url_count += 1

                    # Collect snippets for context
                    for item in df_result.get("results", [])[:8]:
                        if item.get("snippet"):
                            research_content.append(item["snippet"])

                    # Collect PAA questions (CRITICAL for FAQ generation)
                    paa = df_result.get("paa_questions", [])
                    paa_questions.extend(paa)

                    # Collect AI Overview content (Google's AI-curated answers - CRITICAL)
                    # This includes the full AI Overview text which reveals topics like
                    # "Family Reunification D6", "Healthcare SNS" that we might miss
                    ai_urls = df_result.get("ai_overview_urls", [])
                    for ai_item in ai_urls:
                        if isinstance(ai_item, dict):
                            item_type = ai_item.get("type", "")
                            if item_type in ["ai_overview_content", "ai_overview_section"]:
                                # This is the actual AI Overview text - most valuable!
                                ai_overview_content.append({
                                    "type": item_type,
                                    "text": ai_item.get("text", ""),
                                    "query": ai_item.get("query", df_result.get("query", ""))
                                })
                            elif item_type == "ai_overview_reference":
                                # Reference URLs
                                ai_overview_content.append({
                                    "url": ai_item.get("url", ""),
                                    "title": ai_item.get("title", ""),
                                    "type": "reference"
                                })

            workflow.logger.info(f"SERP: {serp_url_count} URLs, {len(paa_questions)} PAA, {len(ai_overview_content)} AI Overview refs")

            # Process news results
            if not isinstance(news_result, Exception) and news_result:
                articles = news_result.get("articles", [])
                for article in articles[:30]:  # Top 30 news
                    url = article.get("url")
                    if url and url not in seen_urls:
                        research_urls.append(url)
                        seen_urls.add(url)
                        news_articles.append({
                            "title": article.get("title", ""),
                            "url": url,
                            "snippet": article.get("snippet", ""),
                            "source": article.get("source", ""),
                            "timestamp": article.get("timestamp", "")
                        })
                workflow.logger.info(f"News: {len(news_articles)} unique articles")

            # Process Reddit results - real expat voices
            reddit_voices = []
            if not isinstance(reddit_result, Exception) and reddit_result:
                reddit_voices = reddit_result.get("voices", [])
                reddit_posts = reddit_result.get("posts", [])
                # Add Reddit URLs to research for potential crawling
                for post in reddit_posts[:10]:
                    if post.get("url") and post["url"] not in seen_urls:
                        research_urls.append(post["url"])
                        seen_urls.add(post["url"])
                workflow.logger.info(
                    f"Reddit: {len(reddit_posts)} posts, {len(reddit_voices)} voices, "
                    f"subreddits: {reddit_result.get('subreddits_searched', [])}"
                )

            # Dedupe PAA questions
            paa_questions = list(set(paa_questions))

            metrics["research_sources"] = len(research_urls)
            metrics["reddit_voices"] = len(reddit_voices)
            workflow.logger.info(
                f"✅ Research complete: {len(research_urls)} URLs, {len(research_content)} snippets, "
                f"{len(news_articles)} news, {len(paa_questions)} PAA questions, {len(reddit_voices)} Reddit voices"
            )

        except Exception as e:
            workflow.logger.error(f"Research phase failed: {e}")
            research_urls = []
            research_content = []
            news_articles = []
            paa_questions = []
            reddit_voices = []
            ai_overview_content = []

        # ===== PHASE 4: CRAWL SOURCES =====
        workflow.logger.info("Phase 4: Crawl Sources - Crawl4AI batch crawl")

        crawled_content = []
        if research_urls:
            try:
                # Pre-filter URLs by relevancy
                filtered_urls = await workflow.execute_activity(
                    "prefilter_urls_by_relevancy",
                    args=[research_urls[:50], f"{country_name} relocation visa tax finance"],
                    start_to_close_timeout=timedelta(minutes=2)
                )

                # Activity returns {"relevant_urls": [url1, url2, ...]} - list of strings
                relevant_urls = filtered_urls.get("relevant_urls", [])[:20]
                workflow.logger.info(f"Filtered to {len(relevant_urls)} relevant URLs from {len(research_urls)}")

                if relevant_urls:
                    crawl_result = await workflow.execute_activity(
                        "crawl4ai_batch",
                        args=[relevant_urls],
                        start_to_close_timeout=timedelta(minutes=5),  # More time for more URLs
                        retry_policy=RetryPolicy(maximum_attempts=2)
                    )

                    for result in crawl_result.get("results", []):
                        if result.get("content"):
                            crawled_content.append({
                                "url": result.get("url"),
                                "title": result.get("title", ""),
                                "content": result.get("content", "")[:10000]  # More content per source
                            })

                    metrics["crawled_urls"] = len(crawled_content)
                    workflow.logger.info(f"Crawled {len(crawled_content)} sources successfully")

            except Exception as e:
                workflow.logger.warning(f"Crawl phase failed (non-blocking): {e}")

        # ===== PHASE 5: CURATE RESEARCH =====
        workflow.logger.info("Phase 5: Curate Research - AI filter and summarize")

        # Build research context for generation
        # Include international perspective guidance + keyword discovery insights
        research_context = {
            "country": country_name,
            "code": country_code,
            "perspective": "International - primarily UK and US citizens, but also applicable to other English-speaking expats",
            "summaries": research_content[:15],
            "crawled_sources": crawled_content[:20],
            "news_articles": news_articles[:10] if 'news_articles' in dir() else [],
            # PAA Questions - CRITICAL for FAQ generation (what Google thinks people ask)
            "paa_questions": list(set(paa_questions))[:25] if 'paa_questions' in dir() else [],
            # AI Overview references - Google's AI-curated authoritative sources
            "ai_overview_sources": ai_overview_content[:15] if 'ai_overview_content' in dir() else [],
            "seo_keywords": seo_keywords.get("primary_keywords", [])[:15],
            "seo_questions": seo_keywords.get("questions", [])[:20],
            # Keyword discovery data - what people actually search for
            "discovered_keywords": discovered_keywords[:20],
            "unique_audiences": unique_audiences[:15],  # e.g., "portugal visa for indians"
            "content_themes": content_themes,  # Grouped by theme (cost, visa, tax, etc.)
            # Reddit voices - real expat experiences and opinions
            "reddit_voices": reddit_voices[:20] if 'reddit_voices' in dir() else [],
        }

        try:
            # curate_research_sources expects: (topic, crawled_pages, news_articles, exa_results, max_sources)
            curation_result = await workflow.execute_activity(
                "curate_research_sources",
                args=[
                    f"{country_name} relocation and finance guide for UK and US citizens",  # topic
                    crawled_content,  # crawled_pages (list of dicts)
                    news_articles if 'news_articles' in dir() else [],  # news_articles
                    [],  # exa_results (already included in crawled_content)
                    25   # max_sources - more for comprehensive guide
                ],
                start_to_close_timeout=timedelta(minutes=3)
            )

            research_context["curated_summary"] = curation_result.get("summary", "")
            research_context["key_facts"] = curation_result.get("key_facts", [])
            research_context["curated_sources"] = curation_result.get("curated_sources", [])

            # Combine curation voices with Reddit voices
            curation_voices = curation_result.get("voices", [])
            reddit_voices_list = research_context.get("reddit_voices", [])
            all_voices = curation_voices + reddit_voices_list
            research_context["voices"] = all_voices  # Combined human perspectives

            workflow.logger.info(
                f"Curation complete: {len(research_context.get('curated_sources', []))} sources, "
                f"{len(research_context.get('key_facts', []))} facts, "
                f"{len(curation_voices)} curation voices + {len(reddit_voices_list)} Reddit voices = {len(all_voices)} total"
            )

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

        # ===== PHASE 7: GENERATE 3 CONTENT MODES =====
        workflow.logger.info("Phase 7: Generate Country Guide - 3 MODES (Story/Guide/YOLO)")

        # Get voices from curation for enrichment
        voices = research_context.get("voices", [])
        workflow.logger.info(f"Using {len(voices)} voices for content enrichment")

        # Generate all 3 modes - SEQUENTIALLY (each uses ~$0.05 Gemini, ~1-2 min)
        # Story mode is primary (used for metadata, motivations, faq, four_act_content)
        content_modes = {}

        for mode in ["story", "guide", "yolo"]:
            workflow.logger.info(f"Generating {mode.upper()} mode content...")

            mode_result = await workflow.execute_activity(
                "generate_country_guide_content",
                args=[
                    country_name,
                    country_code,
                    research_context,
                    seo_keywords,
                    target_word_count,
                    mode,    # NEW: content mode
                    voices   # NEW: voices for enrichment
                ],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )

            content_modes[mode] = mode_result
            workflow.logger.info(f"  {mode.upper()}: {mode_result.get('word_count', 0)} words")

        # Use STORY mode as primary (has all metadata, motivations, etc.)
        article = content_modes["story"]

        # Add all 3 content versions to payload
        article["content_story"] = content_modes["story"].get("content", "")
        article["content_guide"] = content_modes["guide"].get("content", "")
        article["content_yolo"] = content_modes["yolo"].get("content", "")

        # Save curation data for future reference
        article["curation"] = {
            "voices": research_context.get("voices", []),
            "key_facts": research_context.get("key_facts", []),
            "curated_sources": research_context.get("curated_sources", []),
            "paa_questions": research_context.get("paa_questions", []),
            "discovered_keywords": research_context.get("discovered_keywords", []),
            "unique_audiences": research_context.get("unique_audiences", []),
        }

        # Track word counts
        metrics["word_count"] = article.get("word_count", 0)
        metrics["word_count_story"] = content_modes["story"].get("word_count", 0)
        metrics["word_count_guide"] = content_modes["guide"].get("word_count", 0)
        metrics["word_count_yolo"] = content_modes["yolo"].get("word_count", 0)

        workflow.logger.info(
            f"Guide generated: {metrics['word_count']} words (Story), "
            f"{metrics['word_count_guide']} (Guide), {metrics['word_count_yolo']} (YOLO), "
            f"{len(article.get('motivations', []))} motivations"
        )

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

        # ===== PHASE 12: GENERATE 5 SEGMENT VIDEOS (SEQUENTIAL) =====
        # Hero, Family, Finance, Daily, YOLO - each ~2-3 min generation + upload
        # Total: ~15-20 minutes, ~$1.50 cost (5 × $0.30 Seedance)

        segment_videos = []
        video_url = None  # Primary hero video URL (backwards compat)
        video_playback_id = None
        video_asset_id = None

        if video_quality:
            workflow.logger.info("Phase 12: Generate 5 segment videos (BLOCKING)")

            four_act_content = article.get("four_act_content", [])
            segments = ["hero", "family", "finance", "daily", "yolo"]

            for i, segment in enumerate(segments):
                workflow.logger.info(f"  [{i+1}/5] Generating {segment.upper()} video...")

                # Generate video prompt for this segment
                prompt_result = await workflow.execute_activity(
                    "generate_segment_video_prompt",
                    args=[
                        country_name,
                        segment,
                        four_act_content if segment == "hero" else None
                    ],
                    start_to_close_timeout=timedelta(seconds=30)
                )

                video_prompt = prompt_result.get("video_prompt", "")
                segment_title = prompt_result.get("title", f"{segment.title()} Video")
                cluster = prompt_result.get("cluster", "story")

                workflow.logger.info(f"    Prompt: {video_prompt[:80]}...")

                # Generate video - BLOCKING
                video_result = await workflow.execute_activity(
                    "generate_four_act_video",
                    args=[
                        segment_title,              # title
                        article.get("content", ""), # content
                        app,                        # app
                        video_quality,              # quality
                        12,                         # duration (4-act = 12s)
                        "16:9",                     # aspect_ratio
                        "seedance",                 # video_model
                        video_prompt                # video_prompt
                    ],
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=RetryPolicy(maximum_attempts=2)
                )

                raw_video_url = video_result.get("video_url")
                workflow.logger.info(f"    Generated: {raw_video_url[:60] if raw_video_url else 'NONE'}...")

                # HARD FAIL for HERO video - workflow should fail if primary video fails
                if not raw_video_url and segment == "hero":
                    raise ValueError(
                        f"HERO video generation failed for {country_name}. "
                        f"Cannot proceed without primary video. "
                        f"Video result: {video_result}"
                    )

                # WARN for non-hero video failures (continue with remaining videos)
                if not raw_video_url and segment != "hero":
                    workflow.logger.warning(f"    ⚠️ {segment.upper()} video failed - continuing without it")
                    continue

                if raw_video_url:
                    # Upload to Mux
                    mux_result = await workflow.execute_activity(
                        "upload_video_to_mux",
                        args=[raw_video_url],
                        start_to_close_timeout=timedelta(minutes=5)
                    )

                    playback_id = mux_result.get("playback_id")
                    asset_id = mux_result.get("asset_id")
                    stream_url = mux_result.get("playback_url")

                    workflow.logger.info(f"    Uploaded to Mux: {playback_id}")

                    # Build segment video object
                    segment_video = {
                        "id": segment,
                        "title": segment_title,
                        "video_url": stream_url,
                        "playback_id": playback_id,
                        "asset_id": asset_id,
                        "position": i + 1,
                        "cluster": cluster,
                        "thumbnail_hero": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=10.5&width=1200",
                        "animated_gif": f"https://image.mux.com/{playback_id}/animated.gif?start=8&end=12&width=640&fps=12",
                        "thumbnails": [
                            {
                                "act": act_num + 1,
                                "time": act_num * 3 + 1.5,
                                "url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time={act_num * 3 + 1.5}&width=800"
                            }
                            for act_num in range(4)
                        ]
                    }
                    segment_videos.append(segment_video)

                    # First video (hero) is the primary for backwards compat
                    if segment == "hero":
                        video_url = stream_url
                        video_playback_id = playback_id
                        video_asset_id = asset_id

            workflow.logger.info(f"✅ Generated {len(segment_videos)}/5 segment videos")
        else:
            workflow.logger.info("Phase 12: Skipping videos (video_quality not set)")

        # ===== PHASE 13: FINAL UPDATE WITH ALL VIDEOS =====
        workflow.logger.info("Phase 13: Final update with segment videos")

        # Add segment_videos to article payload
        article["segment_videos"] = segment_videos

        # Build video_narrative for backwards compat (uses hero video)
        video_narrative = None
        if video_playback_id:
            four_act = article.get("four_act_content", [])
            video_narrative = {
                "playback_id": video_playback_id,
                "duration": 12,
                "acts": 4,
                "segment_count": len(segment_videos),
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

        # GIF for featured asset (from hero video)
        featured_asset_url = None
        if video_playback_id:
            featured_asset_url = f"https://image.mux.com/{video_playback_id}/animated.gif?start=8&end=12&width=640&fps=12"

        # Final update with all videos
        await workflow.execute_activity(
            "save_article_to_neon",
            args=[
                article_id,
                article.get("slug"),
                article.get("title"),
                app,
                "country_guide",
                article,  # Now contains segment_videos + content_story/guide/yolo
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

        # Add segment videos to metrics
        metrics["segment_videos"] = len(segment_videos)
        metrics["content_modes"] = 3  # story, guide, yolo

        return {
            "article_id": article_id,
            "country_id": country_id,
            "country_code": country_code,
            "slug": article.get("slug"),
            "title": article.get("title"),
            "status": "published",
            "video_playback_id": video_playback_id,
            "segment_videos": len(segment_videos),
            "metrics": metrics
        }
