"""Activities for LinkedIn Apify Scraper workflow.

This module imports both local activities (Apify scraping) and shared activities
from the job-worker (classification, skills extraction, database saving).
"""

from .apify_scraper import scrape_linkedin_via_apify

# Import shared activities from job-worker
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Try to import from job-worker using path manipulation
job_worker_path = Path(__file__).parent.parent.parent.parent / "job-worker" / "src"

if job_worker_path.exists():
    logger.info(f"Found job-worker at {job_worker_path}")
    sys.path.insert(0, str(job_worker_path))
    try:
        from activities.classification import classify_jobs_with_gemini
        from activities.enrichment import extract_job_skills
        from activities.database import save_jobs_to_database

        logger.info(" Successfully imported shared activities from job-worker")
    except ImportError as e:
        logger.error(f"L Failed to import from job-worker: {e}")
        logger.error("Please ensure job-worker/src/activities/*.py files exist")
        raise
else:
    logger.error(f"L job-worker path not found at {job_worker_path}")
    raise ImportError(
        f"Cannot find job-worker at {job_worker_path}. "
        "Ensure fractional-worker is in /Users/dankeegan/worker/"
    )

__all__ = [
    "scrape_linkedin_via_apify",
    "classify_jobs_with_gemini",
    "extract_job_skills",
    "save_jobs_to_database",
]
