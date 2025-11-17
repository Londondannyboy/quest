"""
Company Creation Workflow

Main Temporal workflow for comprehensive company research and profile generation.

Timeline: 90-150 seconds total
"""

from temporalio import workflow
from datetime import timedelta
import asyncio
from typing import Dict, Any

# Import activity functions (will be registered in worker)
with workflow.unsafe.imports_passed_through():
    from src.models.input import CompanyInput
    from src.models.research import ResearchData


@workflow.defn
class CompanyCreationWorkflow:
    """
    Complete company creation workflow with parallel research.

    Phases:
    1. Normalize & Check (5s)
    2. Parallel Research (60s)
    3. Ambiguity Check (10s)
    4. Optional Re-scrape (30s)
    5. Zep Context (5s)
    6. Generate Profile (15s)
    7. Generate Images (15s)
    8. Save to Database (5s)
    9. Fetch Articles (5s)
    10. Sync to Zep (5s)
    """

    @workflow.run
    async def run(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute company creation workflow.

        Args:
            input_dict: CompanyInput as dict

        Returns:
            Dict with status, company_id, slug, metrics
        """
        # Convert input
        input_data = CompanyInput(**input_dict)

        workflow.logger.info(f"Creating company: {input_data.url}")

        # ===== PHASE 1: NORMALIZE & CHECK =====
        workflow.logger.info("Phase 1: Normalizing URL")

        normalized = await workflow.execute_activity(
            "normalize_company_url",
            args=[str(input_data.url), input_data.category],
            start_to_close_timeout=timedelta(seconds=30)
        )

        existing = await workflow.execute_activity(
            "check_company_exists",
            args=[normalized["domain"]],
            start_to_close_timeout=timedelta(seconds=10)
        )

        # Check if already exists and no force update
        if existing["exists"] and not input_data.force_update:
            workflow.logger.info("Company already exists")
            return {
                "status": "exists",
                "company_id": existing["company_id"],
                "slug": existing["slug"],
                "message": "Company already exists in database"
            }

        # ===== PHASE 2: PARALLEL RESEARCH =====
        workflow.logger.info("Phase 2: Parallel research (Serper + Crawl4AI + Firecrawl + Exa + Logo)")

        # Launch all research activities in parallel (now with separate crawlers!)
        news_task = workflow.execute_activity(
            "fetch_company_news",
            args=[
                normalized["domain"],
                normalized["company_name_guess"],
                input_data.category,
                input_data.jurisdiction
            ],
            start_to_close_timeout=timedelta(minutes=2)
        )

        crawl4ai_task = workflow.execute_activity(
            "crawl4ai_crawl",
            args=[normalized["normalized_url"]],
            start_to_close_timeout=timedelta(minutes=3)
        )

        firecrawl_task = workflow.execute_activity(
            "firecrawl_crawl",
            args=[normalized["normalized_url"]],
            start_to_close_timeout=timedelta(minutes=3)
        )

        exa_task = workflow.execute_activity(
            "exa_research_company",
            args=[
                normalized["domain"],
                normalized["company_name_guess"],
                input_data.category
            ],
            start_to_close_timeout=timedelta(minutes=5)
        )

        logo_task = workflow.execute_activity(
            "extract_and_process_logo",
            args=[normalized["normalized_url"], normalized["company_name_guess"]],
            start_to_close_timeout=timedelta(minutes=2)
        )

        # Wait for all to complete
        news_data, crawl4ai_data, firecrawl_data, exa_data, logo_data = await asyncio.gather(
            news_task, crawl4ai_task, firecrawl_task, exa_task, logo_task
        )

        # Combine crawler results
        website_data = {
            "pages": crawl4ai_data.get("pages", []) + firecrawl_data.get("pages", []),
            "crawl4ai_pages": len(crawl4ai_data.get("pages", [])),
            "firecrawl_pages": len(firecrawl_data.get("pages", [])),
            "crawl4ai_success": crawl4ai_data.get("success", False),
            "firecrawl_success": firecrawl_data.get("success", False),
            "cost": firecrawl_data.get("cost", 0.0),
            "crawlers_used": []
        }
        if crawl4ai_data.get("success"):
            website_data["crawlers_used"].append("crawl4ai")
        if firecrawl_data.get("success"):
            website_data["crawlers_used"].append("firecrawl")

        workflow.logger.info("Phase 2 complete: All research gathered")

        # ===== PHASE 3: AMBIGUITY CHECK =====
        workflow.logger.info("Phase 3: Checking research ambiguity")

        ambiguity = await workflow.execute_activity(
            "check_research_ambiguity",
            args=[news_data, website_data, exa_data, input_data.category],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(
            f"Ambiguity check: confidence={ambiguity['confidence']:.2f}, "
            f"recommendation={ambiguity['recommendation']}"
        )

        # ===== PHASE 4: OPTIONAL RE-SCRAPE =====
        if ambiguity["is_ambiguous"] and ambiguity["confidence"] < 0.7:
            workflow.logger.info("Phase 4: Running targeted re-scrape (low confidence)")

            category_clean = input_data.category.replace('_', ' ')
            refined_query = f"{normalized['company_name_guess']} {category_clean}"

            # Re-scrape with refined queries (parallel)
            news_refined_task = workflow.execute_activity(
                "fetch_targeted_research",
                args=[normalized["domain"], refined_query, input_data.jurisdiction],
                start_to_close_timeout=timedelta(minutes=2)
            )

            exa_refined_task = workflow.execute_activity(
                "exa_research_company",
                args=[normalized["domain"], refined_query, input_data.category],
                start_to_close_timeout=timedelta(minutes=5)
            )

            news_refined, exa_refined = await asyncio.gather(
                news_refined_task, exa_refined_task
            )

            # Merge results
            news_data["articles"].extend(news_refined.get("articles", []))
            exa_data["results"].extend(exa_refined.get("results", []))

            workflow.logger.info("Re-scrape complete: Results merged")

        # ===== PHASE 5: ZEP CONTEXT =====
        workflow.logger.info("Phase 5: Querying Zep for context")

        company_name = (
            exa_data.get("summary", {}).get("company_name") or
            normalized["company_name_guess"]
        )

        zep_context = await workflow.execute_activity(
            "query_zep_for_context",
            args=[company_name, normalized["domain"], input_data.app],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(
            f"Zep context: {len(zep_context.get('articles', []))} articles, "
            f"{len(zep_context.get('deals', []))} deals"
        )

        # ===== PHASE 5.5: VALIDATE SOURCE URLS =====
        workflow.logger.info("Phase 5.5: Validating source URLs (removing 404s and paywalls)")

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
            "validate_news_sources",
            args=[all_source_urls],
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Filter out invalid URLs from research data
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
            f"{len(validation_result['invalid_urls'])} invalid "
            f"({validation_result['paywall_count']} paywalls)"
        )

        # ===== PHASE 6: GENERATE PROFILE (V2 - Narrative-First) =====
        workflow.logger.info("Phase 6: Generating company profile with V2 (Narrative-First)")

        # Build research data
        research_data = ResearchData(
            normalized_url=normalized["normalized_url"],
            domain=normalized["domain"],
            company_name=company_name,
            jurisdiction=input_data.jurisdiction,
            category=input_data.category,
            news_articles=news_data.get("articles", []),
            website_content=website_data,
            exa_research=exa_data,
            logo_data=logo_data,
            zep_context=zep_context,
            confidence_score=ambiguity["confidence"],
            ambiguity_signals=ambiguity["signals"],
            is_ambiguous=ambiguity["is_ambiguous"],
            recommendation=ambiguity["recommendation"],
            total_cost=news_data.get("cost", 0.0) + exa_data.get("cost", 0.0)
        )

        profile_result = await workflow.execute_activity(
            "generate_company_profile_v2",
            args=[research_data.model_dump()],
            start_to_close_timeout=timedelta(seconds=120)  # Increased for Claude Sonnet 4.5 narrative generation
        )

        payload = profile_result["profile"]

        workflow.logger.info("Profile generated successfully")

        # ===== PHASE 6.5: CLEAN GENERATED LINKS =====
        workflow.logger.info("Phase 6.5: Cleaning generated links (removing broken URLs)")

        if "profile_sections" in payload and payload["profile_sections"]:
            cleaned_sections = await workflow.execute_activity(
                "clean_generated_links",
                args=[payload["profile_sections"]],
                start_to_close_timeout=timedelta(seconds=30)
            )
            payload["profile_sections"] = cleaned_sections
            workflow.logger.info("Link cleaning complete")

        # ===== PHASE 7: GENERATE IMAGES =====
        workflow.logger.info("Phase 7: Generating featured image")

        featured_image = await workflow.execute_activity(
            "generate_company_featured_image",
            args=[
                company_name,
                logo_data.get("logo_url"),
                payload.get("headquarters_country") or "Global",
                payload.get("hero_stats", {}).get("founded_year")
            ],
            start_to_close_timeout=timedelta(minutes=2)
        )

        # Calculate completeness
        completeness = await workflow.execute_activity(
            "calculate_completeness_score",
            args=[payload],
            start_to_close_timeout=timedelta(seconds=10)
        )

        payload["data_completeness_score"] = completeness

        # Add data source tracking for transparency
        payload["data_sources"] = {
            "serper": {
                "articles": len(news_data.get("articles", [])),
                "cost": news_data.get("cost", 0.0),
                "queries": news_data.get("num_queries", 0)
            },
            "crawl4ai": {
                "pages": website_data.get("crawl4ai_pages", 0),
                "success": website_data.get("crawl4ai_success", False)
            },
            "firecrawl": {
                "pages": website_data.get("firecrawl_pages", 0),
                "cost": website_data.get("cost", 0.0),
                "success": website_data.get("firecrawl_success", False)
            },
            "exa": {
                "results": len(exa_data.get("results", [])),
                "cost": exa_data.get("cost", 0.0),
                "research_id": exa_data.get("research_id")
            }
        }

        workflow.logger.info(f"Completeness score: {completeness}%")
        workflow.logger.info(f"Data sources: Serper={payload['data_sources']['serper']['articles']} articles, "
                           f"Crawl4AI={payload['data_sources']['crawl4ai']['pages']} pages, "
                           f"Firecrawl={payload['data_sources']['firecrawl']['pages']} pages, "
                           f"Exa={payload['data_sources']['exa']['results']} results")

        # ===== PHASE 8: SAVE TO NEON =====
        workflow.logger.info("Phase 8: Saving to Neon database")

        company_id = await workflow.execute_activity(
            "save_company_to_neon",
            args=[
                existing.get("company_id"),
                normalized["domain"],
                company_name,
                input_data.app,
                input_data.category,
                payload,
                logo_data.get("logo_url"),
                featured_image.get("url")
            ],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(f"Saved to database: company_id={company_id}")

        # ===== PHASE 9: FETCH RELATED ARTICLES - DISABLED =====
        # Disabled due to type error: Expected value to be str, was <class 'int'>
        # workflow.logger.info("Phase 9: Fetching related articles")
        #
        # related_articles = await workflow.execute_activity(
        #     "fetch_related_articles",
        #     args=[company_id, 10],
        #     start_to_close_timeout=timedelta(seconds=30)
        # )
        #
        # workflow.logger.info(f"Found {len(related_articles)} related articles")

        related_articles = []  # Placeholder

        # ===== PHASE 10: ZEP SYNC =====
        workflow.logger.info("Phase 10: Syncing to Zep knowledge graph")

        zep_summary = await workflow.execute_activity(
            "create_zep_summary",
            args=[payload, zep_context],
            start_to_close_timeout=timedelta(seconds=30)
        )

        zep_result = await workflow.execute_activity(
            "sync_company_to_zep",
            args=[str(company_id), company_name, zep_summary, input_data.app],
            start_to_close_timeout=timedelta(minutes=2)
        )

        workflow.logger.info("Zep sync complete")

        # ===== COMPLETE =====
        from src.utils.helpers import generate_slug
        slug = generate_slug(company_name, normalized["domain"])

        total_cost = (
            research_data.total_cost +
            profile_result.get("cost", 0.0) +
            featured_image.get("cost", 0.0)
        )

        workflow.logger.info(
            f"✅ Company creation complete: {slug} "
            f"(cost: ${total_cost:.4f}, confidence: {ambiguity['confidence']:.2f})"
        )

        return {
            "status": "created" if not existing["exists"] else "updated",
            "company_id": company_id,
            "slug": slug,
            "name": company_name,
            "logo_url": logo_data.get("logo_url"),
            "featured_image_url": featured_image.get("url"),
            "research_cost": total_cost,
            "research_confidence": ambiguity["confidence"],
            "data_completeness": completeness,
            "related_articles_count": len(related_articles),
            "zep_graph_id": zep_result.get("graph_id"),
            "ambiguity_signals": ambiguity["signals"]
        }
