"""Duplicate checking activities for jobs in Neon and ZEP."""

import asyncpg
import httpx
from typing import List, Dict, Set
from temporalio import activity
import logging
import os

logger = logging.getLogger(__name__)


@activity.defn
async def check_duplicates_in_neon(jobs: List[Dict]) -> Dict[str, any]:
    """
    Check which jobs already exist in Neon database.

    Returns dict with:
        - new_jobs: List of jobs not in database
        - existing_jobs: List of jobs already in database (with their DB IDs)
        - duplicate_count: Number of duplicates found
    """
    from ..config.settings import get_settings

    settings = get_settings()
    activity.logger.info(f"Checking {len(jobs)} jobs for duplicates in Neon")

    try:
        conn = await asyncpg.connect(settings.database_url)

        # Get board_id for LinkedIn UK (Apify)
        board_id = await conn.fetchval(
            "SELECT id FROM job_boards WHERE company_name = $1",
            "LinkedIn UK (Apify)"
        )

        if not board_id:
            activity.logger.warning("LinkedIn UK (Apify) board not found, all jobs will be new")
            await conn.close()
            return {
                "new_jobs": jobs,
                "existing_jobs": [],
                "duplicate_count": 0
            }

        # Check each job's external_id
        new_jobs = []
        existing_jobs = []

        for job in jobs:
            external_id = job.get("job_id") or job.get("external_id") or job.get("url", "").split("/")[-1]

            existing_id = await conn.fetchval(
                "SELECT id FROM jobs WHERE board_id = $1 AND external_id = $2",
                board_id,
                external_id
            )

            if existing_id:
                job_copy = job.copy()
                job_copy["neon_id"] = str(existing_id)
                existing_jobs.append(job_copy)
            else:
                new_jobs.append(job)

        await conn.close()

        activity.logger.info(
            f"Duplicate check complete: {len(new_jobs)} new, {len(existing_jobs)} existing"
        )

        return {
            "new_jobs": new_jobs,
            "existing_jobs": existing_jobs,
            "duplicate_count": len(existing_jobs)
        }

    except Exception as e:
        activity.logger.error(f"Error checking duplicates in Neon: {e}")
        # On error, assume all are new to not block the workflow
        return {
            "new_jobs": jobs,
            "existing_jobs": [],
            "duplicate_count": 0,
            "error": str(e)
        }


@activity.defn
async def check_duplicates_in_zep(jobs: List[Dict]) -> Dict[str, any]:
    """
    Check which jobs already exist in ZEP knowledge graph.

    Returns dict with:
        - new_jobs: List of jobs not in ZEP
        - existing_jobs: List of jobs already in ZEP (with their graph node IDs)
        - duplicate_count: Number of duplicates found
    """
    zep_api_key = os.getenv("ZEP_API_KEY")
    zep_base_url = os.getenv("ZEP_BASE_URL", "https://api.getzep.com")

    if not zep_api_key:
        activity.logger.warning("ZEP_API_KEY not set, skipping ZEP duplicate check")
        return {
            "new_jobs": jobs,
            "existing_jobs": [],
            "duplicate_count": 0
        }

    activity.logger.info(f"Checking {len(jobs)} jobs for duplicates in ZEP")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Query ZEP graph for existing job nodes
            # We'll check by external_id or URL
            new_jobs = []
            existing_jobs = []

            for job in jobs:
                job_url = job.get("url")
                job_id = job.get("job_id") or job.get("external_id")

                # Search ZEP graph for this job
                search_response = await client.post(
                    f"{zep_base_url}/v2/graphs/job_market/search",
                    headers={
                        "Authorization": f"Bearer {zep_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "query": f"Job with URL {job_url} or ID {job_id}",
                        "limit": 1
                    }
                )

                if search_response.status_code == 200:
                    results = search_response.json()
                    if results.get("nodes") and len(results["nodes"]) > 0:
                        # Found existing node
                        job_copy = job.copy()
                        job_copy["zep_node_id"] = results["nodes"][0].get("uuid")
                        existing_jobs.append(job_copy)
                    else:
                        new_jobs.append(job)
                else:
                    # On error, assume new
                    new_jobs.append(job)

            activity.logger.info(
                f"ZEP duplicate check complete: {len(new_jobs)} new, {len(existing_jobs)} existing"
            )

            return {
                "new_jobs": new_jobs,
                "existing_jobs": existing_jobs,
                "duplicate_count": len(existing_jobs)
            }

    except Exception as e:
        activity.logger.error(f"Error checking duplicates in ZEP: {e}")
        # On error, assume all are new
        return {
            "new_jobs": jobs,
            "existing_jobs": [],
            "duplicate_count": 0,
            "error": str(e)
        }


@activity.defn
async def merge_duplicate_results(neon_result: Dict, zep_result: Dict) -> Dict:
    """
    Merge duplicate check results from both Neon and ZEP.

    Returns jobs categorized as:
        - completely_new: Not in Neon or ZEP
        - in_neon_only: In Neon but not ZEP (needs ZEP sync)
        - in_zep_only: In ZEP but not Neon (unusual, log warning)
        - in_both: Already in both systems (just update timestamps)
    """
    activity.logger.info("Merging duplicate check results from Neon and ZEP")

    # Get sets of job IDs
    neon_new_ids = {
        j.get("job_id") or j.get("external_id") or j.get("url")
        for j in neon_result.get("new_jobs", [])
    }
    neon_existing_ids = {
        j.get("job_id") or j.get("external_id") or j.get("url")
        for j in neon_result.get("existing_jobs", [])
    }

    zep_new_ids = {
        j.get("job_id") or j.get("external_id") or j.get("url")
        for j in zep_result.get("new_jobs", [])
    }
    zep_existing_ids = {
        j.get("job_id") or j.get("external_id") or j.get("url")
        for j in zep_result.get("existing_jobs", [])
    }

    # Categorize
    completely_new = neon_new_ids & zep_new_ids
    in_neon_only = neon_existing_ids & zep_new_ids
    in_zep_only = neon_new_ids & zep_existing_ids
    in_both = neon_existing_ids & zep_existing_ids

    # Build categorized job lists
    all_jobs = {
        (j.get("job_id") or j.get("external_id") or j.get("url")): j
        for j in (neon_result.get("new_jobs", []) + neon_result.get("existing_jobs", []))
    }

    result = {
        "completely_new": [all_jobs[jid] for jid in completely_new if jid in all_jobs],
        "in_neon_only": [all_jobs[jid] for jid in in_neon_only if jid in all_jobs],
        "in_zep_only": [all_jobs[jid] for jid in in_zep_only if jid in all_jobs],
        "in_both": [all_jobs[jid] for jid in in_both if jid in all_jobs],
    }

    activity.logger.info(
        f"Categorization complete: {len(result['completely_new'])} new, "
        f"{len(result['in_neon_only'])} need ZEP sync, "
        f"{len(result['in_both'])} already synced"
    )

    if result["in_zep_only"]:
        activity.logger.warning(
            f"{len(result['in_zep_only'])} jobs found in ZEP but not Neon (unusual)"
        )

    return result
