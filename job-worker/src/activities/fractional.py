import httpx
import json
import asyncpg
from datetime import datetime
from typing import List, Optional
from temporalio import activity
from ..config.settings import get_settings


@activity.defn
async def scrape_fractional_jobs(config: dict) -> List[dict]:
    """
    Scrape job listings from fractionaljobs.io using Crawl4AI.

    Returns a list of raw job data with basic info extracted.
    """
    settings = get_settings()
    source_url = config.get("source_url", "https://www.fractionaljobs.io/")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.crawl4ai_url}/scrape",
            json={
                "url": source_url,
                "extraction_type": "job_listings",
                "use_ai": True,
                "schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "company": {"type": "string"},
                            "location": {"type": "string"},
                            "hours": {"type": "string"},
                            "compensation": {"type": "string"},
                            "function": {"type": "string"},
                            "url": {"type": "string"},
                            "description": {"type": "string"},
                        }
                    }
                }
            }
        )
        response.raise_for_status()
        data = response.json()

        jobs = data.get("jobs", data.get("extracted", []))

        # Normalize job data
        normalized = []
        for job in jobs:
            normalized.append({
                "title": job.get("title", ""),
                "company_name": job.get("company", ""),
                "location": job.get("location", ""),
                "hours_per_week": job.get("hours", ""),
                "compensation": job.get("compensation", ""),
                "department": job.get("function", ""),
                "url": job.get("url", ""),
                "description": job.get("description", ""),
                "source": "fractionaljobs.io",
            })

        return normalized


@activity.defn
async def classify_fractional_jobs(jobs: List[dict]) -> List[dict]:
    """
    Use AI to classify if jobs are truly fractional/part-time/contract roles.

    Adds 'is_fractional' boolean and 'fractional_type' to each job.
    """
    settings = get_settings()

    # Use OpenAI to classify
    from openai import AsyncOpenAI

    openai = AsyncOpenAI(api_key=settings.openai_api_key)

    classified = []
    for job in jobs:
        # Build context for classification
        job_context = f"""
Title: {job.get('title', '')}
Company: {job.get('company_name', '')}
Hours: {job.get('hours_per_week', '')}
Compensation: {job.get('compensation', '')}
Description: {job.get('description', '')[:500]}
"""

        try:
            response = await openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a job classification expert. Analyze job listings and determine if they are:
1. Fractional executive roles (C-suite/leadership working part-time for multiple companies)
2. Part-time permanent roles
3. Contract/temporary roles
4. Full-time roles (not fractional)

Respond with JSON: {"is_fractional": true/false, "fractional_type": "fractional|part-time|contract|full-time", "confidence": 0.0-1.0}"""
                    },
                    {
                        "role": "user",
                        "content": f"Classify this job:\n{job_context}"
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            result = json.loads(response.choices[0].message.content)
            job["is_fractional"] = result.get("is_fractional", False)
            job["fractional_type"] = result.get("fractional_type", "unknown")
            job["classification_confidence"] = result.get("confidence", 0.0)

        except Exception as e:
            # Default to fractional if classification fails (from fractional job board)
            job["is_fractional"] = True
            job["fractional_type"] = "unknown"
            job["classification_confidence"] = 0.5
            job["classification_error"] = str(e)

        classified.append(job)

    return classified


@activity.defn
async def save_fractional_jobs_to_database(data: dict) -> dict:
    """Save fractional jobs to database with proper attribution."""
    jobs = data.get("jobs", [])
    source = data.get("source", "fractionaljobs.io")

    settings = get_settings()
    conn = await asyncpg.connect(settings.database_url)

    added = 0
    updated = 0
    errors = []

    try:
        # Get or create the job board for fractional jobs
        board_id = await conn.fetchval(
            "SELECT id FROM job_boards WHERE company_name = $1",
            "FractionalJobs.io"
        )

        if not board_id:
            board_id = await conn.fetchval("""
                INSERT INTO job_boards (company_name, url, board_type, is_active)
                VALUES ($1, $2, $3, true)
                RETURNING id
            """, "FractionalJobs.io", "https://www.fractionaljobs.io/", "aggregator")

        for job in jobs:
            try:
                # Check if job exists by URL or title+company
                existing = await conn.fetchval("""
                    SELECT id FROM jobs
                    WHERE board_id = $1 AND (url = $2 OR (title = $3 AND company_name = $4))
                """, board_id, job.get("url"), job.get("title"), job.get("company_name"))

                if existing:
                    # Update existing job
                    await conn.execute("""
                        UPDATE jobs SET
                            full_description = $1,
                            department = $2,
                            location = $3,
                            employment_type = $4,
                            last_seen_at = $5
                        WHERE id = $6
                    """,
                        job.get("description"),
                        job.get("department"),
                        job.get("location"),
                        job.get("fractional_type", "fractional"),
                        datetime.utcnow(),
                        existing
                    )
                    updated += 1
                else:
                    # Insert new job
                    await conn.execute("""
                        INSERT INTO jobs (
                            board_id, company_name, title, full_description, department,
                            location, employment_type, url, posted_date,
                            first_seen_at, last_seen_at, external_id
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $10, $11)
                    """,
                        board_id,
                        job.get("company_name"),
                        job.get("title"),
                        job.get("description"),
                        job.get("department"),
                        job.get("location"),
                        job.get("fractional_type", "fractional"),
                        job.get("url"),
                        datetime.utcnow().date(),
                        datetime.utcnow(),
                        job.get("url", "")[:255]
                    )
                    added += 1

            except Exception as e:
                errors.append(f"Job '{job.get('title')}': {str(e)}")

        return {"added": added, "updated": updated, "errors": errors}

    finally:
        await conn.close()
