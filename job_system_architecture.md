# Job Scraping System Architecture

## 1. Ontological Structure ✅

Yes, we should define a proper ontology! Here's the job market ontology:

```python
JOB_MARKET_ONTOLOGY = {
    "entities": {
        "Company": {
            "properties": ["name", "industry", "website", "size", "founded"],
            "relationships": ["HAS_DEPARTMENT", "LOCATED_IN", "POSTS_JOB"]
        },
        "Job": {
            "properties": ["title", "description", "posted_date", "salary_range", "status"],
            "relationships": ["POSTED_BY", "REQUIRES_SKILL", "IN_LOCATION", "PART_OF_DEPARTMENT"]
        },
        "Location": {
            "properties": ["city", "country", "region", "timezone"],
            "relationships": ["HAS_JOBS", "HAS_COMPANIES"]
        },
        "Department": {
            "properties": ["name", "function", "size"],
            "relationships": ["BELONGS_TO_COMPANY", "HAS_JOBS"]
        },
        "Skill": {
            "properties": ["name", "category", "level"],
            "relationships": ["REQUIRED_BY_JOB", "RELATED_TO_SKILL"]
        },
        "Person": {
            "properties": ["name", "title", "experience"],
            "relationships": ["WORKS_AT", "HAS_SKILL", "APPLIED_TO"]
        }
    },
    "relationships": {
        "POSTED_BY": {"source": "Job", "target": "Company", "properties": ["posted_date", "status"]},
        "REQUIRES_SKILL": {"source": "Job", "target": "Skill", "properties": ["level", "required"]},
        "IN_LOCATION": {"source": "Job", "target": "Location", "properties": ["remote_allowed"]},
        "HAS_DEPARTMENT": {"source": "Company", "target": "Department", "properties": ["established_date"]},
        "SIMILAR_TO": {"source": "Job", "target": "Job", "properties": ["similarity_score"]}
    }
}
```

## 2. Temporal Workflow Architecture 🔄

### Separate Temporal Namespace: `job-workflows`

Create a dedicated Temporal namespace to keep job workflows separate:

```python
# temporal_config.py
JOB_TEMPORAL_CONFIG = {
    "namespace": "job-workflows",  # Separate from main quest workflows
    "task_queue": "job-scraping-queue",
    "worker_count": 3,
    "schedules": {
        "daily_scrape": "0 9 * * *",  # 9 AM daily
        "weekly_analysis": "0 10 * * 1",  # Monday 10 AM
    }
}
```

### Core Workflows

```python
# workflows/job_workflows.py

@workflow.defn
class JobMasterWorkflow:
    """Master workflow that orchestrates all job scraping"""
    
    @workflow.run
    async def run(self, config: JobScrapingConfig) -> JobScrapingResult:
        # 1. Discovery Phase
        boards = await workflow.execute_activity(
            discover_job_boards,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # 2. Parallel Scraping per board type
        scraping_tasks = []
        for board in boards:
            if board.type == "ashby":
                task = workflow.execute_child_workflow(
                    AshbyScraperWorkflow,
                    board,
                    id=f"ashby-{board.company_name}-{datetime.now().isoformat()}"
                )
            elif board.type == "greenhouse":
                task = workflow.execute_child_workflow(
                    GreenhouseScraperWorkflow,
                    board,
                    id=f"greenhouse-{board.company_name}-{datetime.now().isoformat()}"
                )
            elif board.type == "lever":
                task = workflow.execute_child_workflow(
                    LeverScraperWorkflow,
                    board,
                    id=f"lever-{board.company_name}-{datetime.now().isoformat()}"
                )
            else:
                task = workflow.execute_child_workflow(
                    GenericScraperWorkflow,
                    board,
                    id=f"generic-{board.company_name}-{datetime.now().isoformat()}"
                )
            scraping_tasks.append(task)
        
        # 3. Wait for all scrapers
        results = await asyncio.gather(*scraping_tasks)
        
        # 4. Process and deduplicate
        all_jobs = await workflow.execute_activity(
            process_and_deduplicate_jobs,
            results,
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        # 5. Enrich with additional data
        enriched_jobs = await workflow.execute_activity(
            enrich_job_data,  # Add salary estimates, company info, etc.
            all_jobs,
            start_to_close_timeout=timedelta(minutes=15)
        )
        
        # 6. Update databases
        await workflow.execute_activity(
            update_neon_database,
            enriched_jobs,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        await workflow.execute_activity(
            update_zep_graph,
            enriched_jobs,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # 7. Send notifications
        await workflow.execute_activity(
            send_job_alerts,
            enriched_jobs,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        return JobScrapingResult(
            total_jobs=len(enriched_jobs),
            new_jobs=sum(1 for j in enriched_jobs if j.is_new),
            updated_jobs=sum(1 for j in enriched_jobs if j.is_updated)
        )
```

### Board-Specific Child Workflows

```python
@workflow.defn
class AshbyScraperWorkflow:
    """Specialized workflow for Ashby boards"""
    
    @workflow.run
    async def run(self, board: JobBoard) -> List[Job]:
        # 1. Get job listing page
        listing_data = await workflow.execute_activity(
            crawl4ai_scrape,
            board.url,
            scraper_config={"type": "ashby"},
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # 2. Extract job URLs
        job_urls = await workflow.execute_activity(
            extract_ashby_job_urls,
            listing_data,
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        # 3. Scrape individual job pages in batches
        jobs = []
        for batch in chunk(job_urls, 10):
            batch_jobs = await workflow.execute_activity(
                crawl4ai_batch_scrape,
                batch,
                start_to_close_timeout=timedelta(minutes=5)
            )
            jobs.extend(batch_jobs)
            
            # Rate limiting between batches
            await asyncio.sleep(2)
        
        return jobs

@workflow.defn
class GreenhouseScraperWorkflow:
    """Specialized workflow for Greenhouse boards"""
    
    @workflow.run
    async def run(self, board: JobBoard) -> List[Job]:
        # Greenhouse has API access
        jobs = await workflow.execute_activity(
            greenhouse_api_fetch,
            board.api_key,
            start_to_close_timeout=timedelta(minutes=2)
        )
        return jobs
```

## 3. FastAPI Service Layer 🚀

```python
# api/job_service.py
from fastapi import FastAPI, BackgroundTasks
from temporal.client import Client

app = FastAPI(title="Job Market API")

@app.post("/scrape/trigger")
async def trigger_scraping(
    company: Optional[str] = None,
    background_tasks: BackgroundTasks = None
):
    """Manually trigger job scraping"""
    temporal_client = await Client.connect("localhost:7233")
    
    handle = await temporal_client.start_workflow(
        JobMasterWorkflow.run,
        JobScrapingConfig(company_filter=company),
        id=f"job-scrape-{datetime.now().isoformat()}",
        task_queue="job-scraping-queue"
    )
    
    return {"workflow_id": handle.id, "status": "started"}

@app.get("/jobs")
async def get_jobs(
    company: Optional[str] = None,
    location: Optional[str] = None,
    skills: Optional[List[str]] = None,
    limit: int = 50
):
    """Query jobs from Neon with filters"""
    # Query Neon database
    pass

@app.get("/jobs/{job_id}")
async def get_job_details(job_id: str):
    """Get detailed job information"""
    # Query both Neon and Zep for comprehensive data
    pass

@app.post("/jobs/search")
async def semantic_search(query: str):
    """Semantic search using Zep graph"""
    client = AsyncZep(api_key=ZEP_API_KEY)
    results = await client.graph.search(
        graph_id="jobs",
        query=query,
        limit=20
    )
    return results

@app.post("/alerts/subscribe")
async def subscribe_to_alerts(
    email: str,
    criteria: JobAlertCriteria
):
    """Subscribe to job alerts"""
    # Store in database for notification workflow
    pass
```

## 4. Scraper Strategy Pattern 🔧

```python
# scrapers/base.py
from abc import ABC, abstractmethod

class JobScraperStrategy(ABC):
    """Base strategy for all job scrapers"""
    
    @abstractmethod
    async def discover_jobs(self, board_url: str) -> List[str]:
        """Discover all job URLs from board"""
        pass
    
    @abstractmethod
    async def scrape_job(self, job_url: str) -> Job:
        """Scrape individual job details"""
        pass
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if this scraper can handle the URL"""
        pass

# scrapers/implementations.py
class AshbyScraperStrategy(JobScraperStrategy):
    async def discover_jobs(self, board_url: str) -> List[str]:
        # Use Crawl4AI with Ashby-specific extraction
        pass
    
    def can_handle(self, url: str) -> bool:
        return "ashbyhq.com" in url

class GreenhouseScraperStrategy(JobScraperStrategy):
    async def discover_jobs(self, board_url: str) -> List[str]:
        # Use Greenhouse API
        pass
    
    def can_handle(self, url: str) -> bool:
        return "greenhouse.io" in url

class LeverScraperStrategy(JobScraperStrategy):
    async def discover_jobs(self, board_url: str) -> List[str]:
        # Use Lever API or scraping
        pass
    
    def can_handle(self, url: str) -> bool:
        return "lever.co" in url

class GenericScraperStrategy(JobScraperStrategy):
    """Fallback scraper using AI to understand page structure"""
    
    async def discover_jobs(self, board_url: str) -> List[str]:
        # Use Crawl4AI with AI extraction
        # or Firecrawl for complex sites
        pass

# Scraper factory
class ScraperFactory:
    strategies = [
        AshbyScraperStrategy(),
        GreenhouseScraperStrategy(),
        LeverScraperStrategy(),
        GenericScraperStrategy()  # Fallback
    ]
    
    @classmethod
    def get_scraper(cls, url: str) -> JobScraperStrategy:
        for strategy in cls.strategies:
            if strategy.can_handle(url):
                return strategy
        return cls.strategies[-1]  # Generic fallback
```

## 5. Deployment Architecture 🏗️

```yaml
# docker-compose.yml
version: '3.8'

services:
  job-api:
    build: ./job-api
    ports:
      - "8001:8000"
    environment:
      - TEMPORAL_NAMESPACE=job-workflows
      - DATABASE_URL=${DATABASE_URL}
      - ZEP_API_KEY=${ZEP_API_KEY}
  
  job-worker:
    build: ./job-worker
    environment:
      - TEMPORAL_NAMESPACE=job-workflows
      - CRAWL4AI_URL=https://crawl4ai-production.up.railway.app
    deploy:
      replicas: 3
  
  temporal-schedule-manager:
    build: ./schedule-manager
    environment:
      - TEMPORAL_NAMESPACE=job-workflows
```

## 6. Monitoring & Observability 📊

```python
# monitoring/job_metrics.py
class JobMetrics:
    """Track job scraping metrics"""
    
    @staticmethod
    async def track_scraping_run(result: JobScrapingResult):
        # Send to monitoring service
        # Track: success rate, new jobs, processing time, errors
        pass
    
    @staticmethod
    async def alert_on_failure(error: Exception, board: JobBoard):
        # Send alerts for scraping failures
        pass
```

## Key Architecture Decisions:

1. **Separate Temporal Namespace**: Keeps job workflows visually separate
2. **Strategy Pattern for Scrapers**: Easy to add new board types
3. **Child Workflows**: Each board type gets specialized handling
4. **FastAPI Service**: RESTful interface for queries and triggers
5. **Dual Storage**: Neon for queries, Zep for graph relationships
6. **Scheduled vs On-Demand**: Both supported via Temporal

This architecture scales well and handles different scraper types elegantly!