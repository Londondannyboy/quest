"""LinkedIn Apify Scraper Workflow - orchestrates the full job scraping pipeline."""

from datetime import timedelta, datetime
from typing import Dict, Any
from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class LinkedInApifyScraperWorkflow:
    """
    Workflow for scraping UK fractional jobs from LinkedIn via Apify.

    Pipeline:
    1. Scrape LinkedIn via Apify API (filtered for UK + fractional keywords)
    2. Classify jobs with Gemini Flash (fractional vs full-time, seniority)
    3. Extract skills from descriptions (OpenAI)
    4. Save to Neon database (job_boards + jobs tables)

    Schedule: Daily at 2 AM UTC
    Duration: ~10-15 minutes (depends on Apify scraping time)
    """

    @workflow.run
    async def run(self, config: dict = None) -> dict:
        """
        Execute LinkedIn fractional jobs scraping pipeline.

        Args:
            config: Optional configuration:
                - location: Default "United Kingdom"
                - keywords: Default "fractional OR part-time OR contract OR interim"
                - max_results: Default 500

        Returns:
            Dictionary with pipeline execution summary:
                - source: "linkedin_apify"
                - jobs_scraped: Number of jobs scraped from Apify
                - jobs_classified: Number of jobs classified
                - jobs_fractional: Number marked as fractional
                - jobs_added: Number added to database
                - jobs_updated: Number updated in database
                - errors: List of error messages
                - duration_seconds: Total execution time
        """
        config = config or {}
        start_time = workflow.now()
        workflow.logger.info(f"Starting LinkedIn Apify Scraper workflow with config: {config}")

        # Step 1: Scrape LinkedIn via Apify
        workflow.logger.info("Step 1: Scraping LinkedIn via Apify...")
        try:
            raw_jobs = await workflow.execute_activity(
                "scrape_linkedin_via_apify",
                config,
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=RetryPolicy(
                    maximum_attempts=2,
                    initial_interval=timedelta(seconds=30),
                ),
            )
        except Exception as e:
            workflow.logger.error(f"Scraping failed: {e}")
            return {
                "source": "linkedin_apify",
                "jobs_scraped": 0,
                "jobs_classified": 0,
                "jobs_fractional": 0,
                "jobs_added": 0,
                "jobs_updated": 0,
                "errors": [f"Scraping failed: {str(e)}"],
                "duration_seconds": (workflow.now() - start_time).total_seconds(),
            }

        if not raw_jobs:
            workflow.logger.warning("No jobs scraped from LinkedIn")
            return {
                "source": "linkedin_apify",
                "jobs_scraped": 0,
                "jobs_classified": 0,
                "jobs_fractional": 0,
                "jobs_added": 0,
                "jobs_updated": 0,
                "errors": ["No jobs found from Apify scrape"],
                "duration_seconds": (workflow.now() - start_time).total_seconds(),
            }

        workflow.logger.info(f"Step 1 complete: Scraped {len(raw_jobs)} raw jobs")

        # Step 2: Classify jobs with Gemini
        workflow.logger.info("Step 2: Classifying jobs with Gemini...")
        try:
            classified_jobs = await workflow.execute_activity(
                "classify_jobs_with_gemini",
                raw_jobs,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )
        except Exception as e:
            workflow.logger.warning(f"Classification failed: {e}, continuing with raw jobs")
            classified_jobs = raw_jobs

        if not classified_jobs:
            classified_jobs = []

        # Filter to fractional/part-time/contract only
        fractional_jobs = [
            j for j in classified_jobs
            if j.get("employment_type") in ["fractional", "part_time", "contract", "temporary"]
            or j.get("is_fractional", False)
        ]

        workflow.logger.info(
            f"Step 2 complete: Classified {len(classified_jobs)} jobs, "
            f"{len(fractional_jobs)} are fractional"
        )

        if not fractional_jobs:
            workflow.logger.warning("No jobs classified as fractional")
            return {
                "source": "linkedin_apify",
                "jobs_scraped": len(raw_jobs),
                "jobs_classified": len(classified_jobs),
                "jobs_fractional": 0,
                "jobs_added": 0,
                "jobs_updated": 0,
                "errors": ["No jobs classified as fractional"],
                "duration_seconds": (workflow.now() - start_time).total_seconds(),
            }

        # Step 3: Extract skills from descriptions
        workflow.logger.info("Step 3: Extracting skills...")
        try:
            enriched_jobs = await workflow.execute_activity(
                "extract_job_skills",
                fractional_jobs,
                start_to_close_timeout=timedelta(minutes=3),
            )
        except Exception as e:
            workflow.logger.warning(f"Skill extraction failed: {e}, continuing without skills")
            enriched_jobs = fractional_jobs

        workflow.logger.info(f"Step 3 complete: Enriched {len(enriched_jobs)} jobs")

        # Step 4: Save to database
        workflow.logger.info("Step 4: Saving to database...")

        # Create virtual "company" for LinkedIn aggregator
        linkedin_board = {
            "name": "LinkedIn UK (Apify)",
            "board_url": "https://www.linkedin.com/jobs",
            "board_type": "apify",
        }

        try:
            db_result = await workflow.execute_activity(
                "save_jobs_to_database",
                {"company": linkedin_board, "jobs": enriched_jobs},
                start_to_close_timeout=timedelta(minutes=2),
            )
        except Exception as e:
            workflow.logger.error(f"Database save failed: {e}")
            return {
                "source": "linkedin_apify",
                "jobs_scraped": len(raw_jobs),
                "jobs_classified": len(classified_jobs),
                "jobs_fractional": len(fractional_jobs),
                "jobs_added": 0,
                "jobs_updated": 0,
                "errors": [f"Database save failed: {str(e)}"],
                "duration_seconds": (workflow.now() - start_time).total_seconds(),
            }

        duration = (workflow.now() - start_time).total_seconds()

        result = {
            "source": "linkedin_apify",
            "jobs_scraped": len(raw_jobs),
            "jobs_classified": len(classified_jobs),
            "jobs_fractional": len(fractional_jobs),
            "jobs_added": db_result.get("added", 0),
            "jobs_updated": db_result.get("updated", 0),
            "errors": db_result.get("errors", []),
            "duration_seconds": duration,
        }

        workflow.logger.info(f"Workflow complete: {result}")
        return result
