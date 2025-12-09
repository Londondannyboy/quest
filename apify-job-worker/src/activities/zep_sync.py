"""ZEP knowledge graph sync activities for jobs."""

import os
from typing import List, Dict
from temporalio import activity
import logging
from zep_cloud import Zep

logger = logging.getLogger(__name__)


@activity.defn
async def sync_jobs_to_zep(jobs: List[Dict]) -> Dict:
    """
    Sync classified jobs to ZEP knowledge graph.

    Each job is added as an episode with structured data that ZEP
    will automatically extract entities and relationships from.
    """
    zep_api_key = os.getenv("ZEP_API_KEY")
    graph_id = os.getenv("ZEP_GRAPH_ID", "jobs-tech")

    if not zep_api_key:
        activity.logger.error("ZEP_API_KEY not set, cannot sync to ZEP")
        return {"synced": 0, "failed": len(jobs), "error": "ZEP_API_KEY not set"}

    activity.logger.info(f"Syncing {len(jobs)} jobs to ZEP graph: {graph_id}")

    # Initialize ZEP client
    client = Zep(api_key=zep_api_key)

    synced = 0
    failed = 0
    errors = []

    activity.logger.info(f"Starting to sync {len(jobs)} jobs...")

    for i, job in enumerate(jobs, 1):
        try:
            # Build rich text episode with entity hints for ZEP to extract entities and relationships
            # This format helps ZEP identify: Companies, Jobs, Skills, Locations, and their relationships
            company_name = job.get('company_name', 'Unknown Company')
            job_title = job.get('title', 'Unknown Position')
            location = f"{job.get('city', '')}, {job.get('country', 'Unknown')}".strip(', ')
            is_fractional = job.get('is_fractional', False)
            is_remote = job.get('is_remote', False)

            job_text = f"""Job Posting: {job_title} at {company_name}

The company {company_name} has posted a position for {job_title}"""

            # Add location info
            if location != 'Unknown':
                job_text += f" in {location}"

            job_text += ".\n\n"

            # Add job details
            job_text += f"Location: {location}\n"
            job_text += f"Employment Type: {job.get('employment_type', 'unknown')}\n"
            job_text += f"Seniority Level: {job.get('seniority_level', 'unknown')}\n"
            job_text += f"Category: {job.get('category', 'unknown')}\n"
            job_text += f"Remote Work: {'Yes' if is_remote else 'No'}\n"

            # Highlight fractional opportunities
            if is_fractional:
                job_text += "\nThis is a fractional role, suitable for experienced professionals seeking part-time or contract opportunities.\n"

            # Add description
            description = job.get('description', '')
            if description:
                job_text += f"\nJob Description:\n{description[:500]}"
                if len(description) > 500:
                    job_text += "..."
                job_text += "\n"

            # Add required skills with structure
            required_skills = job.get('required_skills', [])
            if required_skills:
                job_text += "\nRequired Skills:\n"
                for skill in required_skills[:10]:  # Limit to top 10
                    job_text += f"- {skill} (essential)\n"

            # Add nice-to-have skills
            nice_skills = job.get('nice_to_have_skills', [])
            if nice_skills:
                job_text += "\nNice to Have Skills:\n"
                for skill in nice_skills[:5]:  # Limit to top 5
                    job_text += f"- {skill} (beneficial)\n"

            # Add job URL if available
            job_url = job.get('url', job.get('link', ''))
            if job_url:
                job_text += f"\nApply: {job_url}"

            activity.logger.info(f"Syncing job {i}/{len(jobs)}: {job_title} at {company_name}")

            # Add to ZEP graph - ZEP will automatically extract entities and relationships
            # Using "text" type (not "message") for better entity extraction
            result = client.graph.add(
                graph_id=graph_id,
                type="text",  # Changed from "message" to "text" for better entity extraction
                data=job_text.strip()
            )

            synced += 1
            activity.logger.info(f"✅ Synced job to ZEP: {job.get('title')} (uuid: {result.uuid_})")

        except Exception as e:
            failed += 1
            error_msg = f"Error syncing job {job.get('title', 'unknown')}: {str(e)}"
            activity.logger.error(f"❌ {error_msg}")
            errors.append(error_msg)

    activity.logger.info(f"ZEP sync complete: {synced} synced, {failed} failed")

    return {
        "synced": synced,
        "failed": failed,
        "errors": errors[:10],  # Limit to first 10 errors
        "total": len(jobs)
    }


@activity.defn
async def update_zep_job_timestamps(job_ids: List[str]) -> Dict:
    """
    Update activity for existing jobs in ZEP (no-op for now).

    Since we're using episodes, ZEP will handle entity deduplication
    and relationship updates automatically.
    """
    # For now, just return success - ZEP handles entity updates automatically
    return {"updated": len(job_ids), "failed": 0, "errors": []}
