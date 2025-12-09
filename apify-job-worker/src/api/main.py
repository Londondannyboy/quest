"""FastAPI service for Apify LinkedIn Job Scraper."""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import asyncpg
import os

from temporalio.client import Client
from ..config.settings import get_settings

# Create FastAPI app
app = FastAPI(
    title="Apify Job Scraper API",
    description="API for scraping and managing LinkedIn jobs via Apify",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class TriggerScrapeRequest(BaseModel):
    """Request to trigger a job scrape."""
    location: str = "United Kingdom"
    job_title: str = "Fractional"
    keywords: Optional[str] = "fractional"
    max_results: int = 100
    post_time_filter: str = "r86400"  # Last 24 hours


class TriggerScrapeResponse(BaseModel):
    """Response from triggering a scrape."""
    workflow_id: str
    status: str
    message: str


class JobsQueryRequest(BaseModel):
    """Query parameters for job search."""
    country: Optional[str] = None
    category: Optional[str] = None
    employment_type: Optional[str] = None
    is_fractional: Optional[bool] = None
    is_remote: Optional[bool] = None
    company: Optional[str] = None
    limit: int = 50
    offset: int = 0


# Health check
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "apify-job-scraper",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Trigger scrape workflow
@app.post("/scrape/trigger", response_model=TriggerScrapeResponse)
async def trigger_scrape(request: TriggerScrapeRequest):
    """
    Manually trigger a LinkedIn job scrape via Apify.

    This starts a Temporal workflow that will:
    1. Call Apify API to scrape LinkedIn
    2. Classify jobs with Pydantic AI
    3. Check for duplicates in Neon and ZEP
    4. Save to Neon database
    5. Sync to ZEP knowledge graph

    Returns the workflow ID for tracking.
    """
    settings = get_settings()

    try:
        # Connect to Temporal
        client = await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
            api_key=settings.temporal_api_key,
            tls=settings.temporal_tls,
        )

        # Start workflow
        workflow_id = f"linkedin-apify-scrape-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        config = {
            "location": request.location,
            "job_title": request.job_title,
            "keywords": request.keywords,
            "jobs_entries": request.max_results,
            "job_post_time": request.post_time_filter,
        }

        handle = await client.start_workflow(
            "LinkedInApifyScraperWorkflow",
            config,
            id=workflow_id,
            task_queue=settings.temporal_task_queue,
        )

        return TriggerScrapeResponse(
            workflow_id=workflow_id,
            status="started",
            message=f"Scrape workflow started. Scraping {request.max_results} jobs from LinkedIn."
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")


# Query jobs
@app.post("/jobs/query")
async def query_jobs(request: JobsQueryRequest):
    """
    Query jobs from Neon database with filters.

    Supports filtering by:
    - country
    - category
    - employment_type
    - is_fractional
    - is_remote
    - company

    Returns paginated results.
    """
    settings = get_settings()

    try:
        conn = await asyncpg.connect(settings.database_url)

        # Build dynamic query
        conditions = ["j.is_active = true", "jb.company_name = 'LinkedIn UK (Apify)'"]
        params = []
        param_count = 1

        if request.country:
            params.append(request.country)
            conditions.append(f"j.location ILIKE '%' || ${param_count} || '%'")
            param_count += 1

        if request.category:
            params.append(request.category)
            conditions.append(f"j.role_category = ${param_count}")
            param_count += 1

        if request.employment_type:
            params.append(request.employment_type)
            conditions.append(f"j.employment_type = ${param_count}")
            param_count += 1

        if request.is_fractional is not None:
            params.append(request.is_fractional)
            conditions.append(f"j.is_fractional = ${param_count}")
            param_count += 1

        if request.is_remote is not None:
            params.append(request.is_remote)
            conditions.append(f"j.is_remote = ${param_count}")
            param_count += 1

        if request.company:
            params.append(f"%{request.company}%")
            conditions.append(f"j.company_name ILIKE ${param_count}")
            param_count += 1

        where_clause = " AND ".join(conditions)

        # Execute query
        query = f"""
            SELECT
                j.id,
                j.external_id,
                j.company_name,
                j.title,
                j.location,
                j.employment_type,
                j.workplace_type,
                j.is_fractional,
                j.is_remote,
                j.seniority_level,
                j.role_category,
                j.url,
                j.posted_date,
                j.description_snippet,
                j.salary_min,
                j.salary_max,
                j.salary_currency,
                j.site_tags,
                j.classification_confidence,
                j.first_seen_at
            FROM jobs j
            JOIN job_boards jb ON j.board_id = jb.id
            WHERE {where_clause}
            ORDER BY j.posted_date DESC NULLS LAST, j.first_seen_at DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """

        params.extend([request.limit, request.offset])
        rows = await conn.fetch(query, *params)

        # Get total count
        count_query = f"""
            SELECT COUNT(*) FROM jobs j
            JOIN job_boards jb ON j.board_id = jb.id
            WHERE {where_clause}
        """
        total = await conn.fetchval(count_query, *params[:-2])

        await conn.close()

        jobs = [dict(row) for row in rows]

        return {
            "jobs": jobs,
            "total": total,
            "limit": request.limit,
            "offset": request.offset,
            "has_more": (request.offset + request.limit) < total
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


# Get workflow status
@app.get("/workflows/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """
    Get the status of a scraping workflow.

    Returns current workflow state and execution details.
    """
    settings = get_settings()

    try:
        client = await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
            api_key=settings.temporal_api_key,
            tls=settings.temporal_tls,
        )

        handle = client.get_workflow_handle(workflow_id)
        desc = await handle.describe()

        return {
            "workflow_id": workflow_id,
            "status": desc.status.name if hasattr(desc.status, 'name') else str(desc.status),
            "start_time": desc.start_time.isoformat() if desc.start_time else None,
            "close_time": desc.close_time.isoformat() if desc.close_time else None,
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {str(e)}")


# Stats endpoint
@app.get("/stats")
async def get_stats():
    """
    Get statistics about scraped jobs.

    Returns counts by:
    - Total jobs
    - Fractional vs full-time
    - By country
    - By category
    - Recent activity
    """
    settings = get_settings()

    try:
        conn = await asyncpg.connect(settings.database_url)

        # Get board_id
        board_id = await conn.fetchval(
            "SELECT id FROM job_boards WHERE company_name = 'LinkedIn UK (Apify)'"
        )

        if not board_id:
            return {"error": "No jobs found"}

        # Total jobs
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM jobs WHERE board_id = $1 AND is_active = true",
            board_id
        )

        # Fractional vs full-time
        employment_stats = await conn.fetch(
            """
            SELECT employment_type, COUNT(*) as count
            FROM jobs
            WHERE board_id = $1 AND is_active = true
            GROUP BY employment_type
            ORDER BY count DESC
            """,
            board_id
        )

        # By country (top 10)
        country_stats = await conn.fetch(
            """
            SELECT
                COALESCE(SPLIT_PART(location, ',', -1), 'Unknown') as country,
                COUNT(*) as count
            FROM jobs
            WHERE board_id = $1 AND is_active = true
            GROUP BY country
            ORDER BY count DESC
            LIMIT 10
            """,
            board_id
        )

        # Recent activity (last 7 days)
        recent = await conn.fetchval(
            """
            SELECT COUNT(*) FROM jobs
            WHERE board_id = $1
            AND is_active = true
            AND first_seen_at >= NOW() - INTERVAL '7 days'
            """,
            board_id
        )

        await conn.close()

        return {
            "total_jobs": total,
            "recent_7_days": recent,
            "by_employment_type": [dict(row) for row in employment_stats],
            "by_country": [dict(row) for row in country_stats],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats query failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
