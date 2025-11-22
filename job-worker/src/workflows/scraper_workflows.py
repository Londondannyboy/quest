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
    """Workflow for scraping Greenhouse job boards via API"""

    @workflow.run
    async def run(self, company: dict) -> dict:
        start_time = workflow.now()

        # Scrape via Greenhouse API
        jobs = await workflow.execute_activity(
            "scrape_greenhouse_jobs",
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
