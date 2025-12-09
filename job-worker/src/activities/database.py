import asyncpg
import json
from datetime import datetime
from temporalio import activity
from ..config.settings import get_settings


def compute_site_tags(job: dict) -> list:
    """
    Compute which sites this job should appear on based on classification.

    Sites:
    - 'fractional': fractional.quest - fractional/part-time executive roles
    - 'startup-jobs': future site - all startup tech jobs
    - 'all': master list of all jobs
    """
    tags = ['all']  # Every job goes to master list

    # Fractional jobs go to fractional.quest
    if job.get("is_fractional"):
        tags.append('fractional')

    # Part-time, contract, temporary also go to fractional if senior enough
    employment_type = job.get("employment_type", "").lower()
    seniority = job.get("seniority_level", "").lower()

    if employment_type in ('part_time', 'contract', 'temporary', 'fractional'):
        if seniority in ('c_suite', 'vp', 'director'):
            if 'fractional' not in tags:
                tags.append('fractional')

    # All tech/startup jobs go to startup-jobs site
    tags.append('startup-jobs')

    return tags


@activity.defn
async def save_jobs_to_database(data: dict) -> dict:
    """Save scraped jobs to Neon database with classification data and site routing"""
    company = data["company"]
    jobs = data["jobs"]

    settings = get_settings()
    conn = await asyncpg.connect(settings.database_url)

    added = 0
    updated = 0
    errors = []

    try:
        # Get board_id (actual column is company_name, not name)
        board_id = await conn.fetchval(
            "SELECT id FROM job_boards WHERE company_name = $1",
            company["name"]
        )

        if not board_id:
            # Create the job board (actual columns: company_name, url, board_type)
            board_id = await conn.fetchval("""
                INSERT INTO job_boards (company_name, url, board_type, is_active)
                VALUES ($1, $2, $3, true)
                RETURNING id
            """, company["name"], company.get("board_url", ""), company.get("board_type", "custom"))

        for job in jobs:
            try:
                # Compute site tags based on classification
                site_tags = compute_site_tags(job)

                # Check if job exists (by URL or title+company)
                existing = await conn.fetchval("""
                    SELECT id FROM jobs
                    WHERE board_id = $1 AND (url = $2 OR title = $3)
                """, board_id, job.get("url"), job.get("title"))

                if existing:
                    # Update existing job with classification data
                    await conn.execute("""
                        UPDATE jobs SET
                            full_description = $1,
                            department = $2,
                            location = $3,
                            employment_type = $4,
                            seniority_level = $5,
                            is_fractional = $6,
                            classification_confidence = $7,
                            classification_reasoning = $8,
                            is_remote = $9,
                            hours_per_week = $10,
                            site_tags = $11,
                            last_seen_at = $12
                        WHERE id = $13
                    """,
                        job.get("description"),
                        job.get("department"),
                        job.get("location"),
                        job.get("employment_type"),
                        job.get("seniority_level"),
                        job.get("is_fractional", False),
                        job.get("classification_confidence", 0.0),
                        job.get("classification_reasoning"),
                        job.get("is_remote"),
                        job.get("hours_per_week"),
                        site_tags,
                        datetime.utcnow(),
                        existing
                    )
                    updated += 1
                else:
                    # Insert new job with all classification fields
                    await conn.execute("""
                        INSERT INTO jobs (
                            board_id, company_name, title, full_description, department,
                            location, employment_type, seniority_level, is_fractional,
                            classification_confidence, classification_reasoning,
                            is_remote, hours_per_week, site_tags,
                            url, posted_date, first_seen_at, last_seen_at, external_id
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $17, $18)
                    """,
                        board_id,
                        company["name"],
                        job.get("title"),
                        job.get("description"),
                        job.get("department"),
                        job.get("location"),
                        job.get("employment_type"),
                        job.get("seniority_level"),
                        job.get("is_fractional", False),
                        job.get("classification_confidence", 0.0),
                        job.get("classification_reasoning"),
                        job.get("is_remote"),
                        job.get("hours_per_week"),
                        site_tags,
                        job.get("url"),
                        job.get("posted_date") or datetime.utcnow().date(),
                        datetime.utcnow(),
                        job.get("url", "")[:255]  # Use URL as external_id
                    )
                    added += 1

            except Exception as e:
                errors.append(f"Job '{job.get('title')}': {str(e)}")

        return {"added": added, "updated": updated, "errors": errors}

    finally:
        await conn.close()


@activity.defn
async def update_job_graphs(results: list) -> dict:
    """Update Zep knowledge graphs with job data"""
    from zep_cloud.client import AsyncZep

    settings = get_settings()
    zep = AsyncZep(api_key=settings.zep_api_key)

    # Get all newly added jobs from database
    conn = await asyncpg.connect(settings.database_url)

    try:
        # Get jobs added in last hour (recent scrape) - use actual column names
        rows = await conn.fetch("""
            SELECT j.*, jb.company_name
            FROM jobs j
            JOIN job_boards jb ON j.board_id = jb.id
            WHERE j.first_seen_at > NOW() - INTERVAL '1 hour'
        """)

        if not rows:
            return {"jobs_added_to_graph": 0}

        # Add to master graph (lightweight)
        for row in rows:
            job_data = {
                "type": "Job",
                "id": str(row["id"]),
                "title": row["title"],
                "company": row["company_name"],
                "location": row["location"],
                "department": row["department"],
            }

            await zep.graph.add(
                graph_id="jobs",
                type="json",
                data=json.dumps(job_data)
            )

            # Also add to vertical graph (jobs-tech for now)
            detailed_data = {
                "type": "Job",
                "id": str(row["id"]),
                "title": row["title"],
                "company": row["company_name"],
                "location": row["location"],
                "department": row["department"],
                "employment_type": row["employment_type"],
                "description": row.get("description", "")[:500],  # Truncate
            }

            await zep.graph.add(
                graph_id="jobs-tech",
                type="json",
                data=json.dumps(detailed_data)
            )

        return {"jobs_added_to_graph": len(rows)}

    finally:
        await conn.close()
