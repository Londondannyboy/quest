"""Main Temporal worker for LinkedIn Apify Scraper."""

import asyncio
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

from temporalio.client import Client
from temporalio.worker import Worker

from .config.settings import get_settings

# Load environment variables from .env
load_dotenv(Path(__file__).parent.parent / ".env")
from .workflows import LinkedInApifyScraperWorkflow
from .activities import (
    # Core scraping
    scrape_linkedin_via_apify,

    # Pydantic AI classification
    classify_jobs_with_pydantic_ai,

    # Duplicate checking
    check_duplicates_in_neon,
    check_duplicates_in_zep,
    merge_duplicate_results,

    # ZEP knowledge graph sync
    sync_jobs_to_zep,
    update_zep_job_timestamps,

    # Database operations
    save_jobs_to_database,

    # Skills (placeholder)
    extract_job_skills,
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

    # Configure Pydantic AI Gateway
    if settings.pydantic_gateway_api_key:
        os.environ["PYDANTIC_AI_GATEWAY_API_KEY"] = settings.pydantic_gateway_api_key
        logger.info("✅ Configured Pydantic AI Gateway")

    # Configure Pydantic Logfire
    if settings.pydantic_logifire_api_key:
        os.environ["PYDANTIC_LOGIFIRE_API_KEY"] = settings.pydantic_logifire_api_key
        logger.info("✅ Configured Pydantic Logfire")

    # Ensure GEMINI_API_KEY is set for Pydantic AI (fallback if not using gateway)
    if not os.getenv("GEMINI_API_KEY"):
        if settings.google_api_key:
            os.environ["GEMINI_API_KEY"] = settings.google_api_key
            logger.info("Set GEMINI_API_KEY from GOOGLE_API_KEY")
        elif settings.gemini_api_key:
            os.environ["GEMINI_API_KEY"] = settings.gemini_api_key

    # Ensure ZEP_API_KEY is set for ZEP knowledge graph sync
    if not os.getenv("ZEP_API_KEY"):
        if settings.zep_api_key:
            os.environ["ZEP_API_KEY"] = settings.zep_api_key
            logger.info("✅ Set ZEP_API_KEY for knowledge graph sync")

    # Ensure other API keys are available in environment
    if settings.apify_api_key and not os.getenv("APIFY_API_KEY"):
        os.environ["APIFY_API_KEY"] = settings.apify_api_key

    if settings.database_url and not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = settings.database_url

    logger.info("=" * 70)
    logger.info("LinkedIn Apify Scraper Worker")
    logger.info("=" * 70)
    logger.info(f"Connecting to Temporal at {settings.temporal_host}")
    logger.info(f"Namespace: {settings.temporal_namespace}")
    logger.info(f"Task queue: {settings.temporal_task_queue}")
    logger.info(f"Apify Task ID: {settings.apify_task_id}")

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
                # Core scraping
                scrape_linkedin_via_apify,

                # Pydantic AI classification
                classify_jobs_with_pydantic_ai,

                # Duplicate checking
                check_duplicates_in_neon,
                check_duplicates_in_zep,
                merge_duplicate_results,

                # ZEP knowledge graph sync
                sync_jobs_to_zep,
                update_zep_job_timestamps,

                # Database operations
                save_jobs_to_database,

                # Skills extraction
                extract_job_skills,
            ],
        )

        logger.info("=" * 70)
        logger.info("✅ LinkedIn Apify Job Worker Started Successfully")
        logger.info(f"Task Queue: {settings.temporal_task_queue}")
        logger.info(f"Namespace: {settings.temporal_namespace}")
        logger.info("")
        logger.info("Registered Workflows:")
        logger.info("  - LinkedInApifyScraperWorkflow")
        logger.info("")
        logger.info("Registered Activities:")
        logger.info("  Scraping:")
        logger.info("    - scrape_linkedin_via_apify")
        logger.info("  Classification:")
        logger.info("    - classify_jobs_with_pydantic_ai (Gemini 2.0 Flash)")
        logger.info("  Duplicate Checking:")
        logger.info("    - check_duplicates_in_neon")
        logger.info("    - check_duplicates_in_zep")
        logger.info("    - merge_duplicate_results")
        logger.info("  Storage & Sync:")
        logger.info("    - save_jobs_to_database (Neon)")
        logger.info("    - sync_jobs_to_zep (Knowledge Graph)")
        logger.info("    - update_zep_job_timestamps")
        logger.info("  Enhancement:")
        logger.info("    - extract_job_skills")
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
