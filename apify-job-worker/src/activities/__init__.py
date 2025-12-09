"""Activities for LinkedIn Apify Scraper workflow."""

from .apify_scraper import scrape_linkedin_via_apify
from .pydantic_classification import classify_jobs_with_pydantic_ai
from .duplicate_checker import (
    check_duplicates_in_neon,
    check_duplicates_in_zep,
    merge_duplicate_results,
)
from .zep_sync import sync_jobs_to_zep, update_zep_job_timestamps
from temporalio import activity
import asyncpg
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# Keep the simple fallback for now
@activity.defn
async def extract_job_skills(jobs: List[Dict]) -> List[Dict]:
    """Extract skills from job descriptions (placeholder for future enhancement)."""
    activity.logger.info(f"Skill extraction placeholder for {len(jobs)} jobs")

    # Skills are now extracted by Pydantic AI in classification step
    # This is a placeholder for future dedicated skill extraction
    return jobs

@activity.defn
async def save_jobs_to_database(data: Dict) -> Dict:
    """Save jobs to Neon database (MVP version - basic save)."""
    from ..config.settings import get_settings

    settings = get_settings()
    jobs = data.get("jobs", [])
    company = data.get("company", {})

    activity.logger.info(f"Saving {len(jobs)} jobs to Neon database")

    if not jobs:
        return {"added": 0, "updated": 0, "failed": 0}

    try:
        conn = await asyncpg.connect(settings.database_url)

        # Get the LinkedIn UK (Apify) board entry
        board_id = await conn.fetchval(
            "SELECT id FROM job_boards WHERE company_name = $1 LIMIT 1",
            "LinkedIn UK (Apify)"
        )

        if not board_id:
            activity.logger.info("Creating LinkedIn UK (Apify) job board entry")
            board_id = await conn.fetchval(
                "INSERT INTO job_boards (company_name, url, board_type, is_active) VALUES ($1, $2, $3, $4) RETURNING id",
                "LinkedIn UK (Apify)",
                "https://www.linkedin.com/jobs/search",
                "custom",
                True
            )
            activity.logger.info(f"Created job board with ID: {board_id}")

        # Save jobs
        added = 0
        failed = 0

        for job in jobs:
            try:
                # Generate external_id from job_id or URL
                external_id = job.get("job_id") or job.get("external_id") or job.get("url", "").split("/")[-1]

                await conn.execute(
                    """INSERT INTO jobs (
                        board_id, external_id, title, company_name, location, full_description, url,
                        employment_type, seniority_level, is_fractional, is_remote,
                        posted_date, classification_confidence, classification_reasoning, site_tags
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    ON CONFLICT(board_id, external_id) DO UPDATE SET
                        updated_date = NOW(),
                        last_seen_at = NOW(),
                        is_fractional = EXCLUDED.is_fractional,
                        classification_confidence = EXCLUDED.classification_confidence,
                        classification_reasoning = EXCLUDED.classification_reasoning""",
                    board_id,
                    external_id,
                    job.get("title"),
                    job.get("company_name"),
                    job.get("location"),
                    job.get("full_description") or job.get("description"),
                    job.get("url"),
                    job.get("employment_type"),
                    job.get("seniority_level"),
                    job.get("is_fractional", False),
                    job.get("is_remote", False),
                    job.get("posted_date"),
                    job.get("classification_confidence", 0.8),
                    job.get("classification_reasoning"),
                    job.get("site_tags", ["fractional-jobs"])
                )
                added += 1
            except Exception as e:
                activity.logger.warning(f"Failed to save job {job.get('url', 'unknown')}: {e}")
                failed += 1

        await conn.close()

        activity.logger.info(f"Saved {added} jobs, {failed} failed")
        return {"added": added, "updated": 0, "failed": failed}

    except Exception as e:
        activity.logger.error(f"Database error: {e}")
        raise

__all__ = [
    "scrape_linkedin_via_apify",
    "classify_jobs_with_gemini",
    "extract_job_skills",
    "save_jobs_to_database",
]
