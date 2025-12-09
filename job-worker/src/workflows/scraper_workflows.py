from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from ..models.job import ScrapingResult


@workflow.defn
class AshbyScraperWorkflow:
    """Workflow for scraping Ashby job boards using Crawl4AI"""

    @workflow.run
    async def run(self, company: dict) -> dict:
        start_time = workflow.now()

        # Scrape jobs using Crawl4AI
        jobs = await workflow.execute_activity(
            "scrape_ashby_jobs",
            company,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        # Extract skills from descriptions
        enriched_jobs = await workflow.execute_activity(
            "extract_job_skills",
            jobs,
            start_to_close_timeout=timedelta(minutes=3),
        )

        # Save to database
        db_result = await workflow.execute_activity(
            "save_jobs_to_database",
            {"company": company, "jobs": enriched_jobs},
            start_to_close_timeout=timedelta(minutes=2),
        )

        duration = (workflow.now() - start_time).total_seconds()

        return {
            "company_name": company["name"],
            "jobs_found": len(jobs),
            "jobs_added": db_result.get("added", 0),
            "jobs_updated": db_result.get("updated", 0),
            "errors": db_result.get("errors", []),
            "duration_seconds": duration,
        }


@workflow.defn
class GreenhouseScraperWorkflow:
    """Workflow for scraping Greenhouse job boards via API with full pipeline"""

    @workflow.run
    async def run(self, company: dict) -> dict:
        start_time = workflow.now()

        # Step 1: Scrape via Greenhouse API (gets basic job list)
        jobs = await workflow.execute_activity(
            "scrape_greenhouse_jobs",
            company,
            start_to_close_timeout=timedelta(minutes=3),
        )

        if not jobs:
            return {
                "company_name": company["name"],
                "jobs_found": 0,
                "jobs_deep_scraped": 0,
                "jobs_classified": 0,
                "jobs_added": 0,
                "jobs_updated": 0,
                "errors": ["No jobs found"],
                "duration_seconds": (workflow.now() - start_time).total_seconds(),
            }

        # Step 2: Deep scrape each job URL via Crawl4AI for full descriptions
        deep_scraped_jobs = await workflow.execute_activity(
            "deep_scrape_job_urls",
            jobs,
            start_to_close_timeout=timedelta(minutes=10),  # Longer timeout for many URLs
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        # Step 3: Classify jobs with Gemini Flash (now has full descriptions)
        classified_jobs = await workflow.execute_activity(
            "classify_jobs_with_gemini",
            deep_scraped_jobs,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        # Step 4: Save to Zep knowledge graph (with dedup check)
        zep_result = await workflow.execute_activity(
            "save_jobs_to_zep",
            classified_jobs,
            start_to_close_timeout=timedelta(minutes=2),
        )

        # Step 5: Save to Neon database (has dedup built in)
        db_result = await workflow.execute_activity(
            "save_jobs_to_database",
            {"company": company, "jobs": classified_jobs},
            start_to_close_timeout=timedelta(minutes=2),
        )

        duration = (workflow.now() - start_time).total_seconds()

        # Count fractional jobs
        fractional_count = sum(1 for j in classified_jobs if j.get("is_fractional"))

        return {
            "company_name": company["name"],
            "jobs_found": len(jobs),
            "jobs_deep_scraped": len(deep_scraped_jobs),
            "jobs_classified": len(classified_jobs),
            "jobs_fractional": fractional_count,
            "jobs_added": db_result.get("added", 0),
            "jobs_updated": db_result.get("updated", 0),
            "jobs_saved_to_zep": zep_result.get("jobs_saved_to_graph", 0),
            "zep_skipped_duplicates": zep_result.get("skipped_duplicates", 0),
            "errors": db_result.get("errors", []),
            "duration_seconds": duration,
        }


@workflow.defn
class LeverScraperWorkflow:
    """Workflow for scraping Lever job boards via API"""

    @workflow.run
    async def run(self, company: dict) -> dict:
        start_time = workflow.now()

        # Scrape via Lever API
        jobs = await workflow.execute_activity(
            "scrape_lever_jobs",
            company,
            start_to_close_timeout=timedelta(minutes=3),
        )

        # Extract skills
        enriched_jobs = await workflow.execute_activity(
            "extract_job_skills",
            jobs,
            start_to_close_timeout=timedelta(minutes=3),
        )

        # Save to database
        db_result = await workflow.execute_activity(
            "save_jobs_to_database",
            {"company": company, "jobs": enriched_jobs},
            start_to_close_timeout=timedelta(minutes=2),
        )

        duration = (workflow.now() - start_time).total_seconds()

        return {
            "company_name": company["name"],
            "jobs_found": len(jobs),
            "jobs_added": db_result.get("added", 0),
            "jobs_updated": db_result.get("updated", 0),
            "errors": db_result.get("errors", []),
            "duration_seconds": duration,
        }


@workflow.defn
class UnknownScraperWorkflow:
    """Fallback workflow for unknown board types - uses AI extraction"""

    @workflow.run
    async def run(self, company: dict) -> dict:
        start_time = workflow.now()

        # Try generic scraping with AI extraction
        jobs = await workflow.execute_activity(
            "scrape_generic_jobs",
            company,
            start_to_close_timeout=timedelta(minutes=5),
        )

        # Extract skills
        enriched_jobs = await workflow.execute_activity(
            "extract_job_skills",
            jobs,
            start_to_close_timeout=timedelta(minutes=3),
        )

        # Save to database
        db_result = await workflow.execute_activity(
            "save_jobs_to_database",
            {"company": company, "jobs": enriched_jobs},
            start_to_close_timeout=timedelta(minutes=2),
        )

        duration = (workflow.now() - start_time).total_seconds()

        return {
            "company_name": company["name"],
            "jobs_found": len(jobs),
            "jobs_added": db_result.get("added", 0),
            "jobs_updated": db_result.get("updated", 0),
            "errors": db_result.get("errors", []),
            "duration_seconds": duration,
        }
