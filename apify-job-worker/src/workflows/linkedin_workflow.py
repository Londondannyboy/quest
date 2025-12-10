"""LinkedIn Apify Scraper Workflow - orchestrates the full job scraping pipeline."""

from datetime import timedelta, datetime
from typing import Dict, Any
from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class LinkedInApifyScraperWorkflow:
    """
    Workflow for scraping jobs from LinkedIn via Apify.

    Pipeline (simplified):
    1. Scrape LinkedIn via Apify API
    2. Save raw jobs to Neon database
    3. Sync raw jobs to ZEP knowledge graph

    Classification and fractional assessment handled downstream.
    Schedule: Daily at 2 AM UTC
    Duration: ~5-10 minutes (depends on Apify scraping time)
    """

    @workflow.run
    async def run(self, config: dict = None) -> dict:
        """
        Execute LinkedIn jobs scraping and ingestion pipeline.

        Args:
            config: Optional configuration:
                - location: Default "United Kingdom"
                - keywords: Default "fractional"
                - jobs_entries: Default 100

        Returns:
            Dictionary with pipeline execution summary:
                - source: "linkedin_apify"
                - jobs_scraped: Number of jobs scraped from Apify
                - jobs_added_to_neon: Number added to Neon database
                - jobs_synced_to_zep: Number synced to ZEP knowledge graph
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
                "jobs_added_to_neon": 0,
                "jobs_synced_to_zep": 0,
                "errors": [f"Scraping failed: {str(e)}"],
                "duration_seconds": (workflow.now() - start_time).total_seconds(),
            }

        if not raw_jobs:
            workflow.logger.warning("No jobs scraped from LinkedIn")
            return {
                "source": "linkedin_apify",
                "jobs_scraped": 0,
                "jobs_added_to_neon": 0,
                "jobs_synced_to_zep": 0,
                "errors": ["No jobs found from Apify scrape"],
                "duration_seconds": (workflow.now() - start_time).total_seconds(),
            }

        workflow.logger.info(f"Step 1 complete: Scraped {len(raw_jobs)} raw jobs")

        # Step 2: UPSERT jobs to Neon database (insert new, update existing)
        workflow.logger.info("Step 2: Upserting jobs to Neon (insert new, update existing)...")

        neon_save_result = {"added": 0, "updated": 0}
        try:
            neon_save_result = await workflow.execute_activity(
                "save_jobs_to_database",
                {"company": {}, "jobs": raw_jobs},  # UPSERT all raw jobs
                start_to_close_timeout=timedelta(minutes=3),
            )
        except Exception as e:
            workflow.logger.error(f"Neon upsert failed: {e}")
            return {
                "source": "linkedin_apify",
                "jobs_scraped": len(raw_jobs),
                "jobs_added_to_neon": 0,
                "jobs_synced_to_zep": 0,
                "errors": [f"Neon upsert failed: {str(e)}"],
                "duration_seconds": (workflow.now() - start_time).total_seconds(),
            }

        workflow.logger.info(
            f"Neon upsert complete: {neon_save_result.get('added', 0)} added, "
            f"{neon_save_result.get('updated', 0)} updated"
        )

        # Step 3: UPSERT jobs to ZEP knowledge graph (insert new, update existing)
        workflow.logger.info("Step 3: Upserting jobs to ZEP (insert new, update existing)...")
        zep_sync_result = {"synced": 0}
        try:
            zep_sync_result = await workflow.execute_activity(
                "sync_jobs_to_zep",
                raw_jobs,  # UPSERT all raw jobs
                start_to_close_timeout=timedelta(minutes=5),
            )
        except Exception as e:
            workflow.logger.warning(f"ZEP upsert failed: {e}, continuing without ZEP sync")
            zep_sync_result = {"synced": 0, "error": str(e)}

        workflow.logger.info(f"ZEP upsert complete: {zep_sync_result.get('synced', 0)} synced")

        duration = (workflow.now() - start_time).total_seconds()

        result = {
            "source": "linkedin_apify",
            "jobs_scraped": len(raw_jobs),
            "jobs_added_to_neon": neon_save_result.get("added", 0),
            "jobs_updated_in_neon": neon_save_result.get("updated", 0),
            "jobs_synced_to_zep": zep_sync_result.get("synced", 0),
            "errors": neon_save_result.get("errors", []) + zep_sync_result.get("errors", []),
            "duration_seconds": duration,
        }

        workflow.logger.info(f"LinkedIn Apify Job Scraper Workflow complete: {result}")
        return result
