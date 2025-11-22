import asyncpg
import json
from datetime import datetime
from temporalio import activity
from ..config.settings import get_settings


@activity.defn
async def save_jobs_to_database(data: dict) -> dict:
    """Save scraped jobs to Neon database"""
    company = data["company"]
    jobs = data["jobs"]

    settings = get_settings()
    conn = await asyncpg.connect(settings.database_url)

    added = 0
    updated = 0
    errors = []

    try:
        # Get job_board_id
        board_id = await conn.fetchval(
            "SELECT id FROM job_boards WHERE name = $1",
            company["name"]
        )

        if not board_id:
            # Create the job board
            board_id = await conn.fetchval("""
                INSERT INTO job_boards (name, careers_url, is_active)
                VALUES ($1, $2, true)
                RETURNING id
            """, company["name"], company.get("board_url", ""))

        for job in jobs:
            try:
                # Check if job exists (by URL or title+company)
                existing = await conn.fetchval("""
                    SELECT id FROM jobs
                    WHERE job_board_id = $1 AND (url = $2 OR title = $3)
                """, board_id, job.get("url"), job.get("title"))

                if existing:
                    # Update existing job
                    await conn.execute("""
                        UPDATE jobs SET
                            description = $1,
                            department = $2,
                            location = $3,
                            employment_type = $4,
                            updated_at = $5
                        WHERE id = $6
                    """,
                        job.get("description"),
                        job.get("department"),
                        job.get("location"),
                        job.get("employment_type"),
                        datetime.utcnow(),
                        existing
                    )
                    updated += 1
                else:
                    # Insert new job
                    await conn.execute("""
                        INSERT INTO jobs (
                            job_board_id, title, description, department,
                            location, employment_type, url, posted_date, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                        board_id,
                        job.get("title"),
                        job.get("description"),
                        job.get("department"),
                        job.get("location"),
                        job.get("employment_type"),
                        job.get("url"),
                        job.get("posted_date") or datetime.utcnow(),
                        datetime.utcnow()
                    )
                    added += 1

            except Exception as e:
                errors.append(f"Job '{job.get('title')}': {str(e)}")

        return {"added": added, "updated": updated, "errors": errors}

    finally:
        await conn.close()


@activity.defn
async def update_job_graphs(results: list[dict]) -> dict:
    """Update Zep knowledge graphs with job data"""
    from zep_cloud.client import AsyncZep

    settings = get_settings()
    zep = AsyncZep(api_key=settings.zep_api_key)

    # Get all newly added jobs from database
    conn = await asyncpg.connect(settings.database_url)

    try:
        # Get jobs added in last hour (recent scrape)
        rows = await conn.fetch("""
            SELECT j.*, jb.name as company_name
            FROM jobs j
            JOIN job_boards jb ON j.job_board_id = jb.id
            WHERE j.created_at > NOW() - INTERVAL '1 hour'
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
