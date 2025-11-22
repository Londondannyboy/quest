import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker

from .config.settings import get_settings
from .workflows import (
    JobScrapingWorkflow,
    AshbyScraperWorkflow,
    GreenhouseScraperWorkflow,
    LeverScraperWorkflow,
    UnknownScraperWorkflow,
)
from .activities import (
    get_companies_to_scrape,
    scrape_ashby_jobs,
    scrape_greenhouse_jobs,
    scrape_lever_jobs,
    scrape_generic_jobs,
    extract_job_skills,
    calculate_company_trends,
    save_jobs_to_database,
    update_job_graphs,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    settings = get_settings()

    logger.info(f"Connecting to Temporal at {settings.temporal_host}")
    logger.info(f"Namespace: {settings.temporal_namespace}")
    logger.info(f"Task queue: {settings.temporal_task_queue}")

    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
        api_key=settings.temporal_api_key if settings.temporal_api_key else None,
    )

    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[
            JobScrapingWorkflow,
            AshbyScraperWorkflow,
            GreenhouseScraperWorkflow,
            LeverScraperWorkflow,
            UnknownScraperWorkflow,
        ],
        activities=[
            get_companies_to_scrape,
            scrape_ashby_jobs,
            scrape_greenhouse_jobs,
            scrape_lever_jobs,
            scrape_generic_jobs,
            extract_job_skills,
            calculate_company_trends,
            save_jobs_to_database,
            update_job_graphs,
        ],
    )

    logger.info("Starting Temporal worker...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
