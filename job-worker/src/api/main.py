from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from temporalio.client import Client
from datetime import datetime
import asyncpg

from ..config.settings import get_settings
from ..workflows import JobScrapingWorkflow

app = FastAPI(
    title="Job Worker API",
    description="API for triggering and managing job scraping workflows",
    version="0.1.0",
)

settings = get_settings()


class TriggerRequest(BaseModel):
    companies: list[str] | None = None  # Specific companies, or all if None


class TriggerResponse(BaseModel):
    workflow_id: str
    status: str


class JobSearchRequest(BaseModel):
    query: str
    vertical: str | None = None
    location: str | None = None
    limit: int = 20


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/scrape/trigger", response_model=TriggerResponse)
async def trigger_scrape(request: TriggerRequest):
    """Trigger a job scraping workflow"""
    try:
        client = await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
            api_key=settings.temporal_api_key,
        )

        # Prepare companies list if specific ones requested
        companies = None
        if request.companies:
            conn = await asyncpg.connect(settings.database_url)
            try:
                rows = await conn.fetch("""
                    SELECT id, name, careers_url as board_url, 'ashby' as board_type
                    FROM job_boards
                    WHERE name = ANY($1) AND is_active = true
                """, request.companies)
                companies = [dict(row) for row in rows]
            finally:
                await conn.close()

        # Start workflow
        workflow_id = f"job-scrape-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        handle = await client.start_workflow(
            JobScrapingWorkflow.run,
            companies,
            id=workflow_id,
            task_queue=settings.temporal_task_queue,
        )

        return TriggerResponse(
            workflow_id=workflow_id,
            status="started"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scrape/status/{workflow_id}")
async def get_scrape_status(workflow_id: str):
    """Get status of a scraping workflow"""
    try:
        client = await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
            api_key=settings.temporal_api_key,
        )

        handle = client.get_workflow_handle(workflow_id)
        description = await handle.describe()

        return {
            "workflow_id": workflow_id,
            "status": description.status.name,
            "start_time": description.start_time.isoformat() if description.start_time else None,
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/jobs")
async def list_jobs(
    company: str | None = None,
    department: str | None = None,
    location: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """List jobs with optional filters"""
    conn = await asyncpg.connect(settings.database_url)

    try:
        query = """
            SELECT j.*, jb.name as company_name
            FROM jobs j
            JOIN job_boards jb ON j.job_board_id = jb.id
            WHERE 1=1
        """
        params = []
        param_count = 0

        if company:
            param_count += 1
            query += f" AND jb.name = ${param_count}"
            params.append(company)

        if department:
            param_count += 1
            query += f" AND j.department ILIKE ${param_count}"
            params.append(f"%{department}%")

        if location:
            param_count += 1
            query += f" AND j.location ILIKE ${param_count}"
            params.append(f"%{location}%")

        query += f" ORDER BY j.created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])

        rows = await conn.fetch(query, *params)

        return {
            "jobs": [dict(row) for row in rows],
            "count": len(rows),
            "limit": limit,
            "offset": offset,
        }

    finally:
        await conn.close()


@app.post("/jobs/search")
async def search_jobs(request: JobSearchRequest):
    """Semantic search for jobs using Zep graph"""
    from zep_cloud.client import AsyncZep

    zep = AsyncZep(api_key=settings.zep_api_key)

    # Determine which graph to search
    graph_id = f"jobs-{request.vertical}" if request.vertical else "jobs"

    try:
        results = await zep.graph.search(
            graph_id=graph_id,
            query=request.query,
            limit=request.limit,
        )

        return {
            "query": request.query,
            "graph": graph_id,
            "results": results,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/companies")
async def list_companies():
    """List all companies with job counts"""
    conn = await asyncpg.connect(settings.database_url)

    try:
        rows = await conn.fetch("""
            SELECT
                jb.id,
                jb.name,
                jb.careers_url,
                COUNT(j.id) as job_count
            FROM job_boards jb
            LEFT JOIN jobs j ON j.job_board_id = jb.id
            WHERE jb.is_active = true
            GROUP BY jb.id, jb.name, jb.careers_url
            ORDER BY job_count DESC
        """)

        return {"companies": [dict(row) for row in rows]}

    finally:
        await conn.close()


@app.get("/companies/{company_name}/trends")
async def get_company_trends(company_name: str):
    """Get hiring trends for a specific company"""
    conn = await asyncpg.connect(settings.database_url)

    try:
        rows = await conn.fetch("""
            SELECT j.department, j.location, j.title, j.created_at
            FROM jobs j
            JOIN job_boards jb ON j.job_board_id = jb.id
            WHERE jb.name = $1
        """, company_name)

        if not rows:
            raise HTTPException(status_code=404, detail=f"Company {company_name} not found")

        from collections import Counter

        jobs = [dict(row) for row in rows]
        dept_counts = Counter(j.get("department") for j in jobs if j.get("department"))
        loc_counts = Counter(j.get("location") for j in jobs if j.get("location"))

        return {
            "company": company_name,
            "total_jobs": len(jobs),
            "departments": dict(dept_counts.most_common(10)),
            "locations": dict(loc_counts.most_common(10)),
        }

    finally:
        await conn.close()
