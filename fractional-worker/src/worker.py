"""Main Temporal worker for LinkedIn Apify Scraper."""

import asyncio
import logging
import sys

from temporalio.client import Client
from temporalio.worker import Worker

from .config.settings import get_settings
from .workflows import LinkedInApifyScraperWorkflow
from .activities import (
    scrape_linkedin_via_apify,
    classify_jobs_with_gemini,
    extract_job_skills,
    save_jobs_to_database,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Main worker function - connects to Temporal and runs worker."""
    settings = get_settings()

    logger.info("=" * 70)
    logger.info("LinkedIn Apify Scraper Worker")
    logger.info("=" * 70)
    logger.info(f"Connecting to Temporal at {settings.temporal_host}")
    logger.info(f"Namespace: {settings.temporal_namespace}")
    logger.info(f"Task queue: {settings.temporal_task_queue}")
    logger.info(f"Apify Actor ID: {settings.apify_actor_id}")

    # Validate required settings
    if not settings.temporal_api_key:
        logger.error("❌ TEMPORAL_API_KEY not set in environment")
        sys.exit(1)

    if not settings.apify_api_key:
        logger.error("❌ APIFY_API_KEY not set in environment")
        sys.exit(1)

    if not settings.database_url:
        logger.error("❌ DATABASE_URL not set in environment")
        sys.exit(1)

    try:
        # Connect to Temporal
        logger.info("Connecting to Temporal Cloud...")
        client = await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
            api_key=settings.temporal_api_key,
            tls=settings.temporal_tls,
        )
        logger.info("✅ Connected to Temporal")

        # Create and run worker
        worker = Worker(
            client,
            task_queue=settings.temporal_task_queue,
            workflows=[LinkedInApifyScraperWorkflow],
            activities=[
                scrape_linkedin_via_apify,
                classify_jobs_with_gemini,
                extract_job_skills,
                save_jobs_to_database,
            ],
        )

        logger.info("=" * 70)
        logger.info("✅ Worker started successfully")
        logger.info(f"Listening on task queue: {settings.temporal_task_queue}")
        logger.info("Workflows registered:")
        logger.info("  - LinkedInApifyScraperWorkflow")
        logger.info("Activities registered:")
        logger.info("  - scrape_linkedin_via_apify")
        logger.info("  - classify_jobs_with_gemini")
        logger.info("  - extract_job_skills")
        logger.info("  - save_jobs_to_database")
        logger.info("=" * 70)
        logger.info("Waiting for workflows to execute...")
        logger.info("(Press Ctrl+C to stop)")
        logger.info("=" * 70)

        await worker.run()

    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"❌ Worker error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
