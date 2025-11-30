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
                "target_word_count": 4000,  # Optional
                "use_cluster_architecture": False  # Optional - creates 4 separate articles instead of 1
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
        use_cluster_architecture = input_dict.get("use_cluster_architecture", False)

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

                # ===== PHASE 4b: URL Pre-Cleanse (Playwright) =====
                # Score URLs via browser to filter out 404s, paywalls, bot blocks
                # NON-BLOCKING: if this fails, continue with all URLs
                if relevant_urls:
                    try:
                        workflow.logger.info(f"Phase 4b: Pre-cleansing {len(relevant_urls)} URLs via Playwright")
                        cleanse_result = await workflow.execute_activity(
                            "playwright_pre_cleanse",
                            args=[relevant_urls],
                            start_to_close_timeout=timedelta(minutes=2),
                            heartbeat_timeout=timedelta(seconds=30),
                            retry_policy=RetryPolicy(
                                maximum_attempts=1,
                                initial_interval=timedelta(seconds=1)
                            )
                        )

                        # Filter to only high-confidence URLs (score >= 0.4)
                        scored_urls = cleanse_result.get("scored_urls", [])
                        cleansed_urls = [
                            item["url"] for item in scored_urls
                            if item.get("score", 0) >= 0.4
                        ]

                        # Log cleansing results
                        trusted = sum(1 for s in scored_urls if s.get("score", 0) >= 0.9)
                        flagged = len(relevant_urls) - len(cleansed_urls)
                        workflow.logger.info(
                            f"URL pre-cleanse: {len(cleansed_urls)} valid, {trusted} trusted, {flagged} filtered out"
                        )

                        if cleansed_urls:
                            relevant_urls = cleansed_urls

                    except Exception as e:
                        workflow.logger.warning(f"URL pre-cleanse failed (non-blocking): {e}")
                        # Continue with original URLs

                if relevant_urls:
                    # Launch individual crawl workflows for each URL (more reliable than batch)
                    crawl_topic = f"{country_name} relocation visa living expat guide"
                    workflow.logger.info(f"Starting {len(relevant_urls)} individual crawl workflows")

                    # Spawn all child workflows in parallel
                    crawl_handles = []
                    for i, url in enumerate(relevant_urls[:15]):  # Cap at 15 URLs
                        child_input = {
                            "url": url,
                            "topic": crawl_topic,
                            "country_code": country_code,
                            "crawler": "crawl4ai"  # Use crawl4ai for all (Serper scrape not working)
                        }
                        handle = await workflow.start_child_workflow(
                            "CrawlUrlWorkflow",
                            child_input,
                            id=f"crawl-{country_code.lower()}-{workflow.uuid4().hex[:8]}-{i}",
                            task_queue="quest-content-queue",
                            execution_timeout=timedelta(minutes=3),
                            retry_policy=RetryPolicy(maximum_attempts=2)
                        )
                        crawl_handles.append(handle)

                    # Wait for all to complete
                    for handle in crawl_handles:
                        try:
                            result = await handle
                            if result.get("success") and result.get("content"):
                                crawled_content.append({
                                    "url": result.get("url"),
                                    "title": result.get("title", ""),
                                    "content": result.get("content", "")[:10000]
                                })
                        except Exception as e:
                            workflow.logger.warning(f"Crawl child workflow failed: {e}")

                    metrics["crawled_urls"] = len(crawled_content)
                    workflow.logger.info(f"Crawled {len(crawled_content)} sources successfully via child workflows")

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

        # Generate all 4 modes - SEQUENTIALLY (each uses ~$0.05 Gemini, ~1-2 min)
        # Story mode is primary (used for metadata, motivations, faq, four_act_content)
        content_modes = {}

        # Pre-compute slugs for internal linking (slugs are predictable)
        base_slug = f"{country_name.lower().replace(' ', '-')}-relocation-guide"
        primary_slug = base_slug  # Story mode is primary
        all_slugs = {
            "story": base_slug,
            "guide": f"{base_slug}-guide",
            "yolo": f"{base_slug}-yolo",
            "voices": f"{base_slug}-voices"
        }

        for mode in ["story", "guide", "yolo", "voices"]:
            workflow.logger.info(f"Generating {mode.upper()} mode content for {country_name}...")

            # Get sibling slugs (exclude current mode, never link to self)
            sibling_slugs = [slug for m, slug in all_slugs.items() if m != mode]

            mode_result = await workflow.execute_activity(
                "generate_country_guide_content",
                args=[
                    country_name,
                    country_code,
                    research_context,
                    seo_keywords,
                    target_word_count,
                    mode,           # Content mode
                    voices,         # Voices for enrichment
                    primary_slug,   # Primary article slug for linking
                    sibling_slugs   # Sibling article slugs for cross-linking
                ],
                start_to_close_timeout=timedelta(minutes=12),  # Increased for comprehensive content + LLM latency
                retry_policy=RetryPolicy(maximum_attempts=3)   # Extra retry for thin content rejection
            )

            content_modes[mode] = mode_result
            workflow.logger.info(f"  {mode.upper()}: {mode_result.get('word_count', 0)} words")

        # Use STORY mode as primary (has all metadata, motivations, etc.)
        article = content_modes["story"]

        # Add all 4 content versions to payload
        article["content_story"] = content_modes["story"].get("content", "")
        article["content_guide"] = content_modes["guide"].get("content", "")
        article["content_yolo"] = content_modes["yolo"].get("content", "")
        article["content_voices_html"] = content_modes["voices"].get("content", "")  # HTML version

        # Add voices at top level for dedicated column (content_voices)
        article["content_voices"] = research_context.get("voices", [])

        # Save curation data for future reference (also in payload for backup)
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
        metrics["word_count_voices"] = content_modes["voices"].get("word_count", 0)

        workflow.logger.info(
            f"Guide generated: {metrics['word_count']} words (Story), "
            f"{metrics['word_count_guide']} (Guide), {metrics['word_count_yolo']} (YOLO), "
            f"{metrics['word_count_voices']} (Voices), "
            f"{len(article.get('motivations', []))} motivations"
        )

        # ===== CLUSTER ARCHITECTURE BRANCH =====
        # If use_cluster_architecture is True, create 4 separate articles via child workflows
        # instead of one article with 4 content columns
        #
        # IMPORTANT: Primary article (STORY) must complete FIRST before cluster siblings.
        # This ensures we always get a "home run" primary article even if cluster creation fails.
        if use_cluster_architecture:
            workflow.logger.info("===== CLUSTER ARCHITECTURE MODE =====")
            workflow.logger.info("Phase A: Create PRIMARY (Story) article first")

            # Generate cluster UUID
            cluster_id = str(workflow.uuid4())
            workflow.logger.info(f"Cluster ID: {cluster_id}")

            # Base slug from story article
            base_slug = article.get("slug")

            cluster_articles = []
            parent_id = None
            character_reference_url = None

            # ===== PHASE A: CREATE PRIMARY (STORY) ARTICLE FIRST =====
            # This MUST succeed before we create any other cluster articles
            story_input = {
                "country_name": country_name,
                "country_code": country_code,
                "cluster_id": cluster_id,
                "article_mode": "story",
                "parent_id": None,  # Story is the parent
                "base_slug": base_slug,
                "title": article.get("title"),
                "content": content_modes["story"].get("content", ""),
                "meta_description": article.get("meta_description", ""),
                "excerpt": article.get("excerpt", ""),
                "payload": article,
                "app": app,
                "video_quality": video_quality,
                "character_reference_url": None,
                "research_context": research_context,
            }

            workflow.logger.info("Creating STORY (primary) article with video...")

            story_result = await workflow.execute_child_workflow(
                "ClusterArticleWorkflow",
                story_input,
                id=f"cluster-{country_code.lower()}-story-{workflow.uuid4().hex[:8]}",
                task_queue="quest-content-queue",
                execution_timeout=timedelta(minutes=20)
            )

            if not story_result.get("success"):
                workflow.logger.error(f"PRIMARY article failed: {story_result}")
                raise RuntimeError(f"Primary article creation failed for {country_name}")

            # Primary article succeeded - capture parent_id and character reference
            parent_id = story_result.get("article_id")
            character_reference_url = story_result.get("character_reference_url")
            cluster_articles.append(story_result)

            workflow.logger.info(
                f"✅ PRIMARY ARTICLE COMPLETE: article_id={parent_id}, "
                f"slug={story_result.get('slug')}, video={story_result.get('video_playback_id')}"
            )
            if character_reference_url:
                workflow.logger.info(f"Character reference: {character_reference_url[:60]}...")

            # ===== PHASE B: CREATE REMAINING CLUSTER ARTICLES (Gravy) =====
            # These are bonus - primary is already safe in Neon
            workflow.logger.info("Phase B: Creating remaining cluster articles (Guide/YOLO/Voices)")

            remaining_modes = [
                {
                    "mode": "guide",
                    "content": content_modes["guide"].get("content", ""),
                    "meta_description": f"Practical guide for relocating to {country_name}. Step-by-step visa requirements, cost of living, and essential tips.",
                    "excerpt": f"Your practical guide to relocating to {country_name}.",
                },
                {
                    "mode": "yolo",
                    "content": content_modes["yolo"].get("content", ""),
                    "meta_description": f"The adventurous guide to {country_name} relocation. Bold moves, unique experiences, and living life fully.",
                    "excerpt": f"YOLO guide: {country_name} for the adventurous.",
                },
                {
                    "mode": "voices",
                    "content": content_modes["voices"].get("content", ""),  # Generated HTML content featuring testimonials
                    "meta_description": f"Real expat voices and experiences from {country_name}. Authentic stories from people who made the move.",
                    "excerpt": f"Hear from real expats in {country_name}.",
                },
            ]

            for config in remaining_modes:
                mode = config["mode"]
                workflow.logger.info(f"Creating {mode.upper()} cluster article...")

                child_input = {
                    "country_name": country_name,
                    "country_code": country_code,
                    "cluster_id": cluster_id,
                    "article_mode": mode,
                    "parent_id": parent_id,  # Link to story as parent
                    "base_slug": base_slug,
                    "title": article.get("title"),
                    "content": config["content"],
                    "meta_description": config["meta_description"],
                    "excerpt": config["excerpt"],
                    "payload": article,
                    "app": app,
                    "video_quality": video_quality,
                    "character_reference_url": character_reference_url,
                    "research_context": research_context,
                }

                try:
                    child_result = await workflow.execute_child_workflow(
                        "ClusterArticleWorkflow",
                        child_input,
                        id=f"cluster-{country_code.lower()}-{mode}-{workflow.uuid4().hex[:8]}",
                        task_queue="quest-content-queue",
                        execution_timeout=timedelta(minutes=20)
                    )

                    if child_result.get("success"):
                        cluster_articles.append(child_result)
                        workflow.logger.info(
                            f"  ✅ {mode.upper()} complete: article_id={child_result.get('article_id')}, "
                            f"slug={child_result.get('slug')}"
                        )
                    else:
                        workflow.logger.warning(f"  ⚠️ {mode.upper()} failed (non-blocking): {child_result}")

                except Exception as e:
                    # Non-blocking - primary is already saved, these are gravy
                    workflow.logger.warning(f"  ⚠️ {mode.upper()} workflow failed (non-blocking): {e}")
                    continue

            # Update country and sync to Zep using story article
            story_article = next((a for a in cluster_articles if a.get("article_mode") == "story"), None)
            article_id = story_article.get("article_id") if story_article else None

            if article_id:
                # Link to country
                await workflow.execute_activity(
                    "link_article_to_country",
                    args=[str(article_id), country_code, "country_comprehensive"],
                    start_to_close_timeout=timedelta(seconds=30)
                )

                # Extract and update country facts
                extracted_facts = await workflow.execute_activity(
                    "extract_country_facts",
                    args=[article],
                    start_to_close_timeout=timedelta(seconds=30)
                )

                await workflow.execute_activity(
                    "update_country_facts",
                    args=[country_code, extracted_facts, True],
                    start_to_close_timeout=timedelta(seconds=30)
                )

                # Sync story to Zep
                try:
                    await workflow.execute_activity(
                        "sync_article_to_zep",
                        args=[
                            str(article_id),
                            article.get("title", ""),
                            article.get("slug", ""),
                            article.get("content", ""),
                            article.get("excerpt", ""),
                            "country_guide",
                            [],
                            app
                        ],
                        start_to_close_timeout=timedelta(minutes=1)
                    )
                except Exception as e:
                    workflow.logger.warning(f"Zep sync failed: {e}")

                # Publish the country
                await workflow.execute_activity(
                    "publish_country",
                    args=[country_code],
                    start_to_close_timeout=timedelta(seconds=30)
                )

            # ===== PHASE C: TOPIC CLUSTER ARTICLES (SEO-Targeted) =====
            # Create dedicated articles for high-value keywords discovered in Phase 2
            # These are DIFFERENT from mode articles - they target specific search queries
            #
            # Example for Slovakia:
            # - /slovakia-cost-of-living (70 vol)
            # - /slovakia-visa-requirements (40 vol)
            # - /slovakia-golden-visa (10 vol)

            topic_cluster_articles = []

            # Get top keywords from country's seo_keywords
            # Topic cluster filtering thresholds (hardcoded to avoid sandbox import issues)
            MIN_VOLUME = 10        # Minimum monthly search volume (lowered to capture long-tail)
            MAX_DIFFICULTY = 70    # Maximum keyword difficulty (0-100)
            MAX_COUNT = 15         # Maximum topic cluster articles to create

            top_keywords = []

            # Extract keywords from seo_keywords structure
            # Filter by volume >= MIN_VOLUME AND competition <= MAX_DIFFICULTY
            if seo_keywords:
                long_tail = seo_keywords.get("long_tail", [])
                for kw in long_tail:
                    volume = kw.get("volume", 0)
                    # Use 'competition' field as difficulty (0-100 scale)
                    difficulty = kw.get("competition", kw.get("difficulty", 50))

                    if volume >= MIN_VOLUME and difficulty <= MAX_DIFFICULTY:
                        # Calculate opportunity score: higher volume + lower difficulty = better
                        opportunity_score = volume * (100 - difficulty) / 100
                        top_keywords.append({
                            "keyword": kw.get("keyword"),
                            "volume": volume,
                            "difficulty": difficulty,
                            "opportunity_score": opportunity_score,
                            "cpc": kw.get("cpc", 0),
                            "planning_type": kw.get("planning_type", "general")
                        })

            # Dedupe by keyword (case-insensitive)
            seen_keywords = set()
            deduped_keywords = []
            for kw in top_keywords:
                kw_lower = kw["keyword"].lower() if kw.get("keyword") else ""
                if kw_lower and kw_lower not in seen_keywords:
                    seen_keywords.add(kw_lower)
                    deduped_keywords.append(kw)

            # Sort by opportunity score (best opportunities first) and cap at MAX_COUNT
            deduped_keywords.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)
            top_keywords = deduped_keywords[:MAX_COUNT]

            workflow.logger.info(
                f"Topic cluster filtering: {len(deduped_keywords)} passed filters "
                f"(vol>={MIN_VOLUME}, diff<={MAX_DIFFICULTY}), taking top {len(top_keywords)}"
            )

            if top_keywords:
                workflow.logger.info(f"Phase C: Creating {len(top_keywords)} topic cluster articles")
                for kw in top_keywords:
                    workflow.logger.info(
                        f"  - '{kw['keyword']}' (vol={kw['volume']}, diff={kw.get('difficulty', '?')}, "
                        f"score={kw.get('opportunity_score', 0):.1f}, type={kw['planning_type']})"
                    )

                # Get parent video data for topic clusters to reuse
                parent_playback_id = story_result.get("video_playback_id") if story_result else None
                parent_four_act_content = article.get("four_act_content", []) if article else []

                for kw in top_keywords:
                    try:
                        topic_result = await workflow.execute_child_workflow(
                            "TopicClusterWorkflow",
                            {
                                "country_name": country_name,
                                "country_code": country_code,
                                "cluster_id": cluster_id,
                                "parent_id": parent_id,
                                "parent_slug": base_slug,
                                "target_keyword": kw["keyword"],
                                "keyword_volume": kw.get("volume", 0),
                                "keyword_difficulty": kw.get("difficulty"),
                                "keyword_cpc": kw.get("cpc", 0),
                                "planning_type": kw.get("planning_type", "general"),
                                "research_context": research_context,
                                "app": app,
                                # Reuse parent video - no new video generation
                                "parent_playback_id": parent_playback_id,
                                "parent_four_act_content": parent_four_act_content,
                            },
                            id=f"topic-{country_code.lower()}-{workflow.uuid4().hex[:8]}",
                            task_queue="quest-content-queue",
                            execution_timeout=timedelta(minutes=10)  # Faster without video gen
                        )

                        if topic_result.get("success"):
                            topic_cluster_articles.append(topic_result)
                            workflow.logger.info(
                                f"  ✅ Topic '{kw['keyword']}' complete: "
                                f"article_id={topic_result.get('article_id')}, "
                                f"slug={topic_result.get('slug')}"
                            )
                        else:
                            workflow.logger.warning(f"  ⚠️ Topic '{kw['keyword']}' failed")

                    except Exception as e:
                        # Non-blocking - mode articles are already saved
                        workflow.logger.warning(f"  ⚠️ Topic '{kw['keyword']}' workflow failed: {e}")
                        continue

                workflow.logger.info(f"Created {len(topic_cluster_articles)} topic cluster articles")

                # C.2: Inherit parent video to all topic cluster children
                if parent_id and parent_playback_id:
                    workflow.logger.info("  C.2: Inheriting parent video to topic cluster articles...")
                    try:
                        inherit_result = await workflow.execute_activity(
                            "inherit_parent_video_to_children",
                            args=[parent_id],
                            start_to_close_timeout=timedelta(seconds=30)
                        )
                        workflow.logger.info(
                            f"    Inherited video to {inherit_result.get('updated_count', 0)} children"
                        )
                    except Exception as e:
                        workflow.logger.warning(f"    Video inheritance failed: {e}")
            else:
                workflow.logger.info("Phase C: No high-volume keywords found, skipping topic clusters")

            # ===== PHASE D: CREATE/UPDATE COUNTRY HUB (SEO Pillar Page) =====
            # Creates a comprehensive hub page that aggregates all cluster content
            # with an SEO-optimized slug (up to 10 keywords)
            #
            # This is a CRUD operation: if hub exists, it updates; if not, creates.
            # Updated timestamps track when content was last refreshed.

            workflow.logger.info("Phase D: Creating/Updating Country Hub (SEO Pillar Page)")

            hub_result = {}
            try:
                # D.1: Generate SEO-optimized slug from DataForSEO keywords
                workflow.logger.info("  D.1: Generating SEO slug from keywords...")
                seo_slug_result = await workflow.execute_activity(
                    "generate_hub_seo_slug",
                    args=[country_name, seo_keywords, "country"],
                    start_to_close_timeout=timedelta(seconds=30)
                )

                hub_slug = seo_slug_result.get("slug", f"relocating-to-{country_name.lower()}-guide")
                hub_title = seo_slug_result.get("title", f"Relocating to {country_name}: Complete Guide")
                hub_meta = seo_slug_result.get("meta_description", "")
                hub_seo_data = seo_slug_result.get("seo_metadata", {})

                workflow.logger.info(f"    SEO slug: {hub_slug}")
                workflow.logger.info(f"    Title: {hub_title}")

                # D.2: Aggregate all cluster articles into hub payload
                workflow.logger.info("  D.2: Aggregating cluster content...")

                # Get country facts for quick stats
                country_data = await workflow.execute_activity(
                    "get_country_by_code",
                    args=[country_code],
                    start_to_close_timeout=timedelta(seconds=30)
                )
                country_facts = country_data.get("facts", {}) if country_data else {}

                # Build cluster articles list for aggregation
                all_cluster_data = []
                for ca in cluster_articles:
                    all_cluster_data.append({
                        "article_id": ca.get("article_id"),
                        "slug": ca.get("slug"),
                        "article_mode": ca.get("article_mode"),
                        "title": ca.get("title", article.get("title")),
                        "excerpt": ca.get("excerpt", ""),
                        "video_playback_id": ca.get("video_playback_id"),
                        "content": content_modes.get(ca.get("article_mode", "story"), {}).get("content", ""),
                        "payload": article,
                    })

                hub_payload = await workflow.execute_activity(
                    "aggregate_cluster_to_hub_payload",
                    args=[country_name, country_code, all_cluster_data, country_facts],
                    start_to_close_timeout=timedelta(minutes=1)
                )

                workflow.logger.info(f"    Aggregated {len(hub_payload.get('cluster_articles', []))} articles into hub")

                # D.2.5: Get all cluster videos for section assignments
                workflow.logger.info("  D.2.5: Getting cluster videos for section assignments...")
                cluster_videos = await workflow.execute_activity(
                    "get_cluster_videos",
                    args=[cluster_id],
                    start_to_close_timeout=timedelta(seconds=30)
                )

                # Add video assignments to hub payload
                hub_payload["cluster_videos"] = cluster_videos.get("videos_by_mode", {})
                hub_payload["section_video_assignments"] = cluster_videos.get("section_videos", {})

                workflow.logger.info(
                    f"    Found {len(cluster_videos.get('videos_by_mode', {}))} cluster videos: "
                    f"{list(cluster_videos.get('videos_by_mode', {}).keys())}"
                )

                # D.3: Generate full hub content
                workflow.logger.info("  D.3: Generating hub content...")
                hub_content = await workflow.execute_activity(
                    "generate_hub_content",
                    args=[country_name, hub_payload, "conde_nast"],
                    start_to_close_timeout=timedelta(minutes=1)
                )

                # D.4: Save/Update hub (UPSERT)
                workflow.logger.info("  D.4: Saving hub to database (UPSERT)...")

                # Get primary keyword from seo data
                primary_kw = hub_seo_data.get("primary_keyword", "")
                total_vol = hub_seo_data.get("total_volume", 0)

                # Get video from cluster_videos (preferred) or story_result
                primary_video = (
                    cluster_videos.get("primary_video") or
                    story_result.get("video_playback_id") if story_result else None
                )
                workflow.logger.info(f"    Hub primary video: {primary_video[:25] if primary_video else 'None'}...")

                hub_save_result = await workflow.execute_activity(
                    "save_or_update_country_hub",
                    args=[
                        country_code,
                        country_name,
                        cluster_id,
                        hub_slug,
                        hub_title,
                        hub_meta,
                        hub_content,
                        hub_payload,
                        hub_seo_data,
                        primary_kw,
                        total_vol,
                        None,  # keyword_difficulty
                        primary_video,
                        "country"
                    ],
                    start_to_close_timeout=timedelta(seconds=60)
                )

                hub_result = hub_save_result
                workflow.logger.info(
                    f"    Hub {'created' if hub_save_result.get('created') else 'updated'}: "
                    f"ID {hub_save_result.get('hub_id')}, slug: {hub_slug}"
                )

                # D.5: Publish hub
                workflow.logger.info("  D.5: Publishing hub...")
                await workflow.execute_activity(
                    "publish_country_hub",
                    args=[country_code],
                    start_to_close_timeout=timedelta(seconds=30)
                )

                workflow.logger.info(f"✅ Hub published: /{hub_slug}")

            except Exception as e:
                workflow.logger.warning(f"⚠️ Hub creation failed (non-blocking): {e}")
                hub_result = {"error": str(e)}

            # ===== PHASE E: FINESSE CLUSTER MEDIA =====
            # Final pass to ensure all articles have videos/thumbnails
            # - Topic cluster articles inherit from parent
            # - Hub gets primary video if missing
            # - All articles get displayable media
            workflow.logger.info("Phase E: Finessing cluster media (video inheritance)")

            try:
                finesse_result = await workflow.execute_activity(
                    "finesse_cluster_media",
                    args=[cluster_id],
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=RetryPolicy(maximum_attempts=2)
                )

                workflow.logger.info(
                    f"  Finessed: {finesse_result.get('topic_articles_updated', 0)} topics updated, "
                    f"hub={'yes' if finesse_result.get('hub_updated') else 'no'}"
                )
                metrics["topics_finessed"] = finesse_result.get("topic_articles_updated", 0)

            except Exception as e:
                workflow.logger.warning(f"  ⚠️ Media finessing failed (non-blocking): {e}")

            metrics["cluster_id"] = cluster_id
            metrics["cluster_articles"] = len(cluster_articles)
            metrics["topic_cluster_articles"] = len(topic_cluster_articles)
            metrics["hub_created"] = hub_result.get("created", False)
            metrics["hub_slug"] = hub_result.get("slug", "")

            workflow.logger.info(f"===== CLUSTER CREATION COMPLETE =====")
            workflow.logger.info(f"Created {len(cluster_articles)} cluster articles for {country_name}")
            if hub_result.get("slug"):
                workflow.logger.info(f"Hub page: /{hub_result.get('slug')}")

            return {
                "article_id": article_id,
                "country_id": country_id,
                "country_code": country_code,
                "cluster_id": cluster_id,
                "slug": article.get("slug"),
                "title": article.get("title"),
                "status": "published",
                "cluster_articles": [
                    {
                        "article_id": a.get("article_id"),
                        "slug": a.get("slug"),
                        "mode": a.get("article_mode"),
                        "video_playback_id": a.get("video_playback_id"),
                    }
                    for a in cluster_articles
                ],
                "topic_cluster_articles": [
                    {
                        "article_id": a.get("article_id"),
                        "slug": a.get("slug"),
                        "target_keyword": a.get("target_keyword"),
                        "keyword_volume": a.get("keyword_volume"),
                        "video_playback_id": a.get("video_playback_id"),
                    }
                    for a in topic_cluster_articles
                ],
                "hub": {
                    "hub_id": hub_result.get("hub_id"),
                    "slug": hub_result.get("slug"),
                    "created": hub_result.get("created", False),
                    "updated_at": hub_result.get("updated_at"),
                } if hub_result.get("hub_id") else None,
                "metrics": metrics
            }

        # ===== LEGACY SINGLE-ARTICLE MODE =====
        # Original behavior: save all content modes to one article

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
            args=[str(article_id), country_code, "country_comprehensive"],
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

        # ===== PHASE 12: GENERATE 5 SEGMENT VIDEOS (CHILD WORKFLOWS) =====
        # Each segment is a separate child workflow for:
        # - Isolated failures (one video failing doesn't block others)
        # - Independent retries
        # - Clearer monitoring in Temporal UI
        # - Each video gets its own optimized prompt
        #
        # SEQUENTIAL execution to maintain character consistency:
        # 1. Generate HERO video first
        # 2. Extract character reference frame from hero (Mux thumbnail at 1.5s)
        # 3. Pass reference to subsequent videos for visual continuity

        segment_videos = []
        video_url = None  # Primary hero video URL (backwards compat)
        video_playback_id = None
        video_asset_id = None
        character_reference_url = None  # Face frame from hero video for consistency

        if video_quality:
            workflow.logger.info("Phase 12: Generate 5 segment videos via child workflows")

            four_act_content = article.get("four_act_content", [])
            segments = ["hero", "family", "finance", "daily", "yolo"]

            for i, segment in enumerate(segments):
                workflow.logger.info(f"  [{i+1}/5] Spawning {segment.upper()} video workflow...")

                # Build child workflow input
                child_input = {
                    "country_name": country_name,
                    "country_code": country_code,
                    "segment": segment,
                    "video_quality": video_quality,
                    "article_id": article_id,
                    "four_act_content": four_act_content if segment == "hero" else None,
                    "character_reference_url": character_reference_url  # None for hero, face URL for others
                }

                try:
                    # Execute child workflow
                    child_result = await workflow.execute_child_workflow(
                        "SegmentVideoWorkflow",
                        child_input,
                        id=f"segment-video-{country_code.lower()}-{segment}-{workflow.uuid4().hex[:8]}",
                        task_queue="quest-content-queue",
                        execution_timeout=timedelta(minutes=15)
                    )

                    if child_result.get("success"):
                        segment_video = child_result.get("segment_video", {})
                        segment_videos.append(segment_video)

                        playback_id = child_result.get("playback_id")
                        asset_id = child_result.get("asset_id")
                        stream_url = child_result.get("video_url")

                        workflow.logger.info(f"    ✅ {segment.upper()} complete: {playback_id}")

                        # For HERO video: extract character reference for subsequent videos
                        # Use frame at 1.5s (Act 1 close-up) as character reference
                        if segment == "hero" and playback_id:
                            video_url = stream_url
                            video_playback_id = playback_id
                            video_asset_id = asset_id
                            # Mux thumbnail at Act 1 close-up moment
                            character_reference_url = f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=1.5&width=1024"
                            workflow.logger.info(f"    📸 Character reference extracted: {character_reference_url[:60]}...")
                    else:
                        error = child_result.get("error", "Unknown error")
                        workflow.logger.warning(f"    ⚠️ {segment.upper()} failed: {error}")

                        # HARD FAIL for HERO video - can't proceed without primary video
                        if segment == "hero":
                            raise ValueError(
                                f"HERO video generation failed for {country_name}. "
                                f"Cannot proceed without primary video. "
                                f"Error: {error}"
                            )

                except Exception as e:
                    workflow.logger.error(f"    ❌ {segment.upper()} workflow failed: {e}")

                    # HARD FAIL for HERO video
                    if segment == "hero":
                        raise ValueError(f"HERO video workflow failed: {e}")
                    # Continue for non-hero failures
                    continue

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
        metrics["content_modes"] = 4  # story, guide, yolo, voices

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
