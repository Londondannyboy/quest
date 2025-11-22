import httpx
import json
from temporalio import activity
from ..config.settings import get_settings


@activity.defn
async def get_companies_to_scrape() -> list[dict]:
    """Fetch all active companies from database"""
    import asyncpg

    settings = get_settings()
    conn = await asyncpg.connect(settings.database_url)

    try:
        rows = await conn.fetch("""
            SELECT
                id, name, careers_url as board_url,
                'ashby' as board_type,  -- Default, would be stored in DB
                'Technology' as industry
            FROM job_boards
            WHERE is_active = true
        """)

        return [dict(row) for row in rows]
    finally:
        await conn.close()


@activity.defn
async def scrape_ashby_jobs(company: dict) -> list[dict]:
    """Scrape jobs from Ashby board using Crawl4AI service"""
    settings = get_settings()

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.crawl4ai_url}/scrape",
            json={
                "url": company["board_url"],
                "extraction_type": "ashby_jobs",
            }
        )
        response.raise_for_status()
        data = response.json()

        jobs = data.get("jobs", [])

        # Normalize to our Job format
        normalized = []
        for job in jobs:
            normalized.append({
                "title": job.get("title"),
                "company_name": company["name"],
                "department": job.get("department"),
                "location": job.get("location"),
                "employment_type": job.get("employmentType"),
                "description": job.get("description"),
                "url": job.get("url"),
                "vertical": company.get("vertical", "tech"),
            })

        return normalized


@activity.defn
async def scrape_greenhouse_jobs(company: dict) -> list[dict]:
    """Scrape jobs from Greenhouse via their public API"""
    board_token = company.get("board_token")  # e.g., "anthropic"

    if not board_token:
        # Extract from URL like https://boards.greenhouse.io/anthropic
        url = company.get("board_url", "")
        board_token = url.rstrip("/").split("/")[-1]

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(
            f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs",
            params={"content": "true"}
        )
        response.raise_for_status()
        data = response.json()

        jobs = data.get("jobs", [])

        normalized = []
        for job in jobs:
            location = job.get("location", {})
            location_name = location.get("name") if isinstance(location, dict) else location

            normalized.append({
                "title": job.get("title"),
                "company_name": company["name"],
                "department": job.get("departments", [{}])[0].get("name") if job.get("departments") else None,
                "location": location_name,
                "employment_type": None,
                "description": job.get("content"),
                "url": job.get("absolute_url"),
                "vertical": company.get("vertical", "tech"),
            })

        return normalized


@activity.defn
async def scrape_lever_jobs(company: dict) -> list[dict]:
    """Scrape jobs from Lever via their public API"""
    board_token = company.get("board_token")

    if not board_token:
        url = company.get("board_url", "")
        board_token = url.rstrip("/").split("/")[-1]

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(
            f"https://api.lever.co/v0/postings/{board_token}"
        )
        response.raise_for_status()
        jobs = response.json()

        normalized = []
        for job in jobs:
            categories = job.get("categories", {})

            normalized.append({
                "title": job.get("text"),
                "company_name": company["name"],
                "department": categories.get("department"),
                "location": categories.get("location"),
                "employment_type": categories.get("commitment"),
                "description": job.get("descriptionPlain"),
                "url": job.get("hostedUrl"),
                "vertical": company.get("vertical", "tech"),
            })

        return normalized


@activity.defn
async def scrape_generic_jobs(company: dict) -> list[dict]:
    """Fallback scraper using AI extraction"""
    settings = get_settings()

    # Use Crawl4AI with generic extraction
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.crawl4ai_url}/scrape",
            json={
                "url": company["board_url"],
                "extraction_type": "generic_jobs",
                "use_ai": True,
            }
        )
        response.raise_for_status()
        data = response.json()

        jobs = data.get("jobs", [])

        normalized = []
        for job in jobs:
            normalized.append({
                "title": job.get("title"),
                "company_name": company["name"],
                "department": job.get("department"),
                "location": job.get("location"),
                "employment_type": job.get("employment_type"),
                "description": job.get("description"),
                "url": job.get("url"),
                "vertical": company.get("vertical", "tech"),
            })

        return normalized
