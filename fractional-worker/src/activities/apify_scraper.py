"""Apify API integration activity for LinkedIn job scraping."""

import asyncio
import httpx
from typing import List, Dict
from temporalio import activity
import logging

from ..config.settings import get_settings
from ..models.apify import ApifyRunInput, ApifyRunResponse, ApifyRunStatus, ApifyJob

logger = logging.getLogger(__name__)


@activity.defn
async def scrape_linkedin_via_apify(config: dict = None) -> List[dict]:
    """
    Scrape UK fractional jobs from LinkedIn using Apify.

    Pipeline:
    1. Start Apify actor run with configured filters
    2. Poll for completion (with timeout)
    3. Retrieve results from dataset
    4. Normalize to internal job format

    Args:
        config: Optional overrides for location, keywords, maxResults
            - location: Default "United Kingdom"
            - keywords: Default "fractional OR part-time OR contract OR interim"
            - max_results: Default 500

    Returns:
        List of normalized job dictionaries

    Raises:
        RuntimeError: If Apify run fails
        TimeoutError: If polling exceeds 10 minutes
    """
    settings = get_settings()
    config = config or {}

    # Build run input
    run_input = ApifyRunInput(
        location=config.get("location", "United Kingdom"),
        searchKeywords=config.get("keywords", "fractional OR part-time OR contract OR interim"),
        maxResults=config.get("max_results", 500),
        scrapeJobDetails=True,
    )

    activity.logger.info(f"Starting Apify scrape with config: {run_input.dict()}")

    async with httpx.AsyncClient(timeout=300.0) as client:
        # Step 1: Start actor run
        activity.logger.info("Posting run request to Apify API...")
        try:
            response = await client.post(
                f"{settings.apify_base_url}/acts/{settings.apify_actor_id}/runs",
                headers={
                    "Authorization": f"Bearer {settings.apify_api_key}",
                    "Content-Type": "application/json",
                },
                json=run_input.dict(),
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            activity.logger.error(f"Failed to start Apify run: {e}")
            raise RuntimeError(f"Apify API error: {e}")

        run_data = response.json()
        run_response = ApifyRunResponse(**run_data["data"])
        run_id = run_response.id
        dataset_id = run_response.defaultDatasetId

        activity.logger.info(
            f"Apify run started: {run_id}, dataset: {dataset_id}"
        )

        # Step 2: Poll for completion (max 10 minutes)
        max_polls = 60  # 60 polls * 10 seconds = 10 minutes
        poll_count = 0

        while poll_count < max_polls:
            await asyncio.sleep(10)  # Wait 10 seconds between polls
            poll_count += 1

            try:
                status_response = await client.get(
                    f"{settings.apify_base_url}/actor-runs/{run_id}",
                    headers={"Authorization": f"Bearer {settings.apify_api_key}"},
                )
                status_response.raise_for_status()
            except httpx.HTTPError as e:
                activity.logger.warning(f"Status check failed: {e}, retrying...")
                continue

            status_data = status_response.json()
            status = status_data["data"]["status"]

            activity.logger.info(
                f"Apify run status: {status} (poll {poll_count}/{max_polls})"
            )

            if status == ApifyRunStatus.SUCCEEDED:
                dataset_id = status_data["data"]["defaultDatasetId"]
                activity.logger.info(f"Apify run succeeded! Dataset ID: {dataset_id}")
                break
            elif status in [
                ApifyRunStatus.FAILED,
                ApifyRunStatus.TIMED_OUT,
                ApifyRunStatus.ABORTED,
            ]:
                status_message = status_data["data"].get("statusMessage", "Unknown error")
                activity.logger.error(
                    f"Apify run {status}: {status_message}"
                )
                raise RuntimeError(
                    f"Apify run {status}: {status_message}"
                )

        if poll_count >= max_polls:
            activity.logger.error("Apify run polling timeout after 10 minutes")
            raise TimeoutError(
                f"Apify run {run_id} did not complete within 10 minutes"
            )

        # Step 3: Retrieve results from dataset
        activity.logger.info(f"Fetching results from dataset: {dataset_id}")

        try:
            results_response = await client.get(
                f"{settings.apify_base_url}/datasets/{dataset_id}/items",
                headers={"Authorization": f"Bearer {settings.apify_api_key}"},
                params={"format": "json"},
            )
            results_response.raise_for_status()
        except httpx.HTTPError as e:
            activity.logger.error(f"Failed to fetch dataset: {e}")
            raise RuntimeError(f"Failed to fetch Apify dataset: {e}")

        raw_jobs = results_response.json()

        # Step 4: Normalize to internal format
        activity.logger.info(f"Normalizing {len(raw_jobs)} jobs from Apify response")

        normalized_jobs = []
        failed_parse = 0

        for i, raw_job in enumerate(raw_jobs):
            try:
                # Handle various response formats
                if isinstance(raw_job, dict):
                    # Try to parse as ApifyJob model
                    apify_job = ApifyJob(**raw_job)
                    normalized_jobs.append(apify_job.to_internal_job())
                else:
                    activity.logger.warning(
                        f"Job {i} is not a dict: {type(raw_job)}"
                    )
                    failed_parse += 1
            except Exception as e:
                activity.logger.warning(
                    f"Failed to parse job {i}: {e}, skipping"
                )
                failed_parse += 1
                continue

        activity.logger.info(
            f"Scraped {len(normalized_jobs)} jobs from LinkedIn via Apify "
            f"({failed_parse} failed to parse)"
        )

        return normalized_jobs
