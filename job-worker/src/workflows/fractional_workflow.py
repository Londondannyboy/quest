from datetime import timedelta
from typing import List
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from ..models.job import ScrapingResult


@workflow.defn
class FractionalJobsScraperWorkflow:
    """
    Workflow for scraping fractional executive job boards.

    This workflow:
    1. Scrapes job listings from fractionaljobs.io
    2. Uses AI to classify if jobs are truly fractional/part-time/contract
    3. Saves verified fractional jobs to the database
    """

    @workflow.run
    async def run(self, config: dict = None) -> dict:
        """
        Run fractional jobs scraping.

        Args:
            config: Optional configuration with:
                - source_url: URL to scrape (default: fractionaljobs.io)
                - max_pages: Maximum pages to scrape (default: 5)
                - uk_only: Filter to UK jobs only (default: True)
        """
        config = config or {}
        start_time = workflow.now()

        # Step 1: Scrape job listings from fractionaljobs.io
        raw_jobs = await workflow.execute_activity(
            "scrape_fractional_jobs",
            config,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        if not raw_jobs:
            return {
                "source": config.get("source_url", "https://www.fractionaljobs.io/"),
                "jobs_scraped": 0,
                "jobs_classified_fractional": 0,
                "jobs_added": 0,
                "jobs_updated": 0,
                "errors": ["No jobs found on source page"],
                "duration_seconds": (workflow.now() - start_time).total_seconds(),
            }

        # Step 2: Use AI to classify jobs as fractional/part-time
        classified_jobs = await workflow.execute_activity(
            "classify_fractional_jobs",
            raw_jobs,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        # Filter to only fractional jobs
        fractional_jobs = [j for j in classified_jobs if j.get("is_fractional", False)]

        if not fractional_jobs:
            return {
                "source": config.get("source_url", "https://www.fractionaljobs.io/"),
                "jobs_scraped": len(raw_jobs),
                "jobs_classified_fractional": 0,
                "jobs_added": 0,
                "jobs_updated": 0,
                "errors": ["No jobs classified as fractional"],
                "duration_seconds": (workflow.now() - start_time).total_seconds(),
            }

        # Step 3: Extract skills from job descriptions
        enriched_jobs = await workflow.execute_activity(
            "extract_job_skills",
            fractional_jobs,
            start_to_close_timeout=timedelta(minutes=3),
        )

        # Step 4: Save to database
        db_result = await workflow.execute_activity(
            "save_fractional_jobs_to_database",
            {"jobs": enriched_jobs, "source": config.get("source_url", "fractionaljobs.io")},
            start_to_close_timeout=timedelta(minutes=2),
        )

        duration = (workflow.now() - start_time).total_seconds()

        return {
            "source": config.get("source_url", "https://www.fractionaljobs.io/"),
            "jobs_scraped": len(raw_jobs),
            "jobs_classified_fractional": len(fractional_jobs),
            "jobs_added": db_result.get("added", 0),
            "jobs_updated": db_result.get("updated", 0),
            "errors": db_result.get("errors", []),
            "duration_seconds": duration,
        }
