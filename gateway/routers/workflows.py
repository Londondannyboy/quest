"""
Workflow Trigger Endpoints

HTTP endpoints for triggering Temporal workflows.
"""

import os
import re
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from auth import validate_api_key
from temporal_client import TemporalClientManager


def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to URL-friendly slug."""
    # Lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    # Truncate to max_length
    return slug[:max_length].rstrip('-')


router = APIRouter(prefix="/v1/workflows", tags=["workflows"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ArticleWorkflowRequest(BaseModel):
    """Request to trigger article generation workflow"""
    topic: str = Field(..., description="Topic to generate article about", min_length=3)
    app: str = Field(default="placement", description="App/site: placement, relocation, etc.")
    target_word_count: int = Field(default=1500, ge=300, le=5000)
    auto_approve: bool = Field(default=True, description="Skip manual approval")


class ArticleResearchRequest(BaseModel):
    """Request to trigger Exa-based article research workflow"""
    topic: str = Field(..., description="Topic to research and create article about", min_length=3)
    app: str = Field(default="placement", description="App/site: placement, relocation, chief-of-staff, etc.")
    target_word_count: int = Field(default=1500, ge=300, le=5000)
    num_research_sources: int = Field(default=5, ge=3, le=10, description="Number of Exa sources to retrieve")
    deep_crawl_enabled: bool = Field(default=False, description="Enable FireCrawl deep scraping")
    skip_zep_sync: bool = Field(default=False, description="Skip Zep knowledge base sync")
    article_format: str = Field(default="article", description="Format type: 'article' or 'listicle'")


class CompanyWorkflowRequest(BaseModel):
    """Request to trigger company profile creation workflow"""
    company_name: str = Field(..., description="Name of the company", min_length=2)
    company_website: str = Field(..., description="Company website URL")
    auto_approve: bool = Field(default=True, description="Skip manual approval")


class CompanyWorkerRequest(BaseModel):
    """Request to trigger CompanyCreationWorkflow (content-worker service)"""
    url: str = Field(..., description="Company website URL", min_length=5)
    category: str = Field(..., description="Company category: placement_agent, relocation_provider, recruiter")
    jurisdiction: str = Field(..., description="Primary jurisdiction: UK, US, SG, EU, etc.")
    app: str = Field(default="relocation", description="App context: placement, relocation")
    force_update: bool = Field(default=False, description="Force re-research of existing company")
    company_name: Optional[str] = Field(default=None, description="Override auto-detected company name")
    research_depth: str = Field(default="standard", description="Research depth: quick, standard, deep")


class VideoEnrichmentRequest(BaseModel):
    """Request to trigger VideoEnrichmentWorkflow"""
    slug: str = Field(..., description="Article slug to enrich with videos", min_length=3)
    app: str = Field(default="relocation", description="App context: relocation, placement, newsroom")
    video_model: str = Field(default="seedance-1-pro-fast", description="Video model: seedance-1-pro-fast")
    video_resolution: str = Field(default="480p", description="Video resolution: 480p or 720p")
    min_sections: int = Field(default=4, ge=1, le=10, description="Minimum sections with videos")
    force_regenerate: bool = Field(default=False, description="Force video regeneration even if exists")


class WorkflowResponse(BaseModel):
    """Response after triggering workflow"""
    workflow_id: str
    status: str
    started_at: datetime
    topic: Optional[str] = None
    app: Optional[str] = None
    company_name: Optional[str] = None
    message: str


class WorkflowStatusResponse(BaseModel):
    """Workflow status query response"""
    workflow_id: str
    status: str  # running, completed, failed, cancelled
    result: Optional[dict] = None
    error: Optional[str] = None


# ============================================================================
# WORKFLOW ENDPOINTS
# ============================================================================

@router.post("/article", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def trigger_article_workflow(
    request: ArticleWorkflowRequest,
    api_key: str = Depends(validate_api_key),
) -> WorkflowResponse:
    """
    Trigger NewsroomWorkflow to generate an article

    Requires X-API-Key header for authentication.

    Args:
        request: Article generation parameters
        api_key: Validated API key from header

    Returns:
        Workflow execution details with workflow_id for status tracking
    """
    # Get Temporal client
    try:
        client = await TemporalClientManager.get_client()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Temporal: {str(e)}",
        )

    # Generate workflow ID
    workflow_id = f"article-{request.app}-{uuid4()}"

    # Use content-worker queue for ArticleCreationWorkflow
    task_queue = "quest-content-queue"

    try:
        # Use ArticleCreationWorkflow for all article generation
        workflow_name = "ArticleCreationWorkflow"
        workflow_args = [{
            "topic": request.topic,
            "article_type": "news",
            "app": request.app,
            "target_word_count": request.target_word_count,
            "generate_images": True,
            "num_research_sources": 5
        }]

        # Start workflow execution
        handle = await client.start_workflow(
            workflow_name,
            args=workflow_args,
            id=workflow_id,
            task_queue=task_queue,
        )

        return WorkflowResponse(
            workflow_id=handle.id,
            status="started",
            started_at=datetime.utcnow(),
            topic=request.topic,
            app=request.app,
            message=f"Article generation workflow started. Use workflow_id to check status.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}",
        )


@router.post("/article-research", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def trigger_article_research_workflow(
    request: ArticleResearchRequest,
    api_key: str = Depends(validate_api_key),
) -> WorkflowResponse:
    """
    Trigger ArticleWorkflow for Exa-based research article generation

    Uses Exa for comprehensive research instead of news search.
    Perfect for evergreen content, guides, and topic-based articles.

    Requires X-API-Key header for authentication.

    Args:
        request: Article research parameters
        api_key: Validated API key from header

    Returns:
        Workflow execution details with workflow_id for status tracking
    """
    # Get Temporal client
    try:
        client = await TemporalClientManager.get_client()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Temporal: {str(e)}",
        )

    # Generate workflow ID
    workflow_id = f"article-research-{request.app}-{uuid4()}"

    # Use content-worker queue for ArticleCreationWorkflow
    task_queue = "quest-content-queue"

    try:
        # Use ArticleCreationWorkflow for all article generation
        workflow_name = "ArticleCreationWorkflow"
        workflow_args = [{
            "topic": request.topic,
            "article_type": request.article_format if request.article_format != "listicle" else "guide",
            "app": request.app,
            "target_word_count": request.target_word_count,
            "generate_images": not request.skip_zep_sync,  # Generate images unless skipping
            "num_research_sources": request.num_research_sources
        }]

        # Start workflow execution
        handle = await client.start_workflow(
            workflow_name,
            args=workflow_args,
            id=workflow_id,
            task_queue=task_queue,
        )

        return WorkflowResponse(
            workflow_id=handle.id,
            status="started",
            started_at=datetime.utcnow(),
            topic=request.topic,
            app=request.app,
            message=f"Article research workflow started with Exa. Use workflow_id to check status.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}",
        )


@router.get("/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    api_key: str = Depends(validate_api_key),
) -> WorkflowStatusResponse:
    """
    Get workflow execution status

    Args:
        workflow_id: Workflow ID returned from trigger endpoint
        api_key: Validated API key from header

    Returns:
        Workflow status and result (if completed)
    """
    # Get Temporal client
    try:
        client = await TemporalClientManager.get_client()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Temporal: {str(e)}",
        )

    try:
        # Get workflow handle
        handle = client.get_workflow_handle(workflow_id)

        # Try to get result (non-blocking with timeout)
        try:
            result = await handle.result()
            return WorkflowStatusResponse(
                workflow_id=workflow_id,
                status="completed",
                result=result if isinstance(result, dict) else {"data": str(result)},
            )
        except TimeoutError:
            # Workflow still running
            return WorkflowStatusResponse(
                workflow_id=workflow_id,
                status="running",
            )

    except Exception as e:
        # Check if workflow exists
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found",
            )

        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            status="failed",
            error=error_msg,
        )


@router.get("/{workflow_id}/result")
async def get_workflow_result(
    workflow_id: str,
    api_key: str = Depends(validate_api_key),
) -> dict:
    """
    Get workflow result (waits for completion)

    This endpoint will block until the workflow completes.
    Use /status endpoint for non-blocking status checks.

    Args:
        workflow_id: Workflow ID returned from trigger endpoint
        api_key: Validated API key from header

    Returns:
        Workflow execution result
    """
    # Get Temporal client
    try:
        client = await TemporalClientManager.get_client()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Temporal: {str(e)}",
        )

    try:
        # Get workflow handle
        handle = client.get_workflow_handle(workflow_id)

        # Wait for result (this will block)
        result = await handle.result()

        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "result": result if isinstance(result, dict) else {"data": str(result)},
        }

    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found",
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {error_msg}",
        )


@router.post("/company", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def trigger_company_workflow(
    request: CompanyWorkflowRequest,
    api_key: str = Depends(validate_api_key),
) -> WorkflowResponse:
    """
    Trigger smart company profile creation workflow with auto-detection

    Just provide company name and website URL - AI automatically detects if the company is:
    - Executive Assistant / Chief of Staff recruiter
    - Placement agent (PE/VC)
    - Relocation service provider

    The workflow will:
    1. Scrape company website
    2. Use AI to classify company type
    3. Extract information with type-specific prompts
    4. Process logo and save to database

    Requires X-API-Key header for authentication.

    Args:
        request: Company creation parameters (name, website)
        api_key: Validated API key from header

    Returns:
        Workflow execution details with workflow_id for status tracking
    """
    # Get Temporal client
    try:
        client = await TemporalClientManager.get_client()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Temporal: {str(e)}",
        )

    # Always use SmartCompanyWorkflow (auto-detects type)
    workflow_name = "SmartCompanyWorkflow"

    # Generate workflow ID
    workflow_id = f"company-smart-{uuid4()}"

    # Get task queue from environment
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "quest-content-queue")

    try:
        # Start workflow execution
        handle = await client.start_workflow(
            workflow_name,
            args=[
                request.company_name,
                request.company_website,
                request.auto_approve,
            ],
            id=workflow_id,
            task_queue=task_queue,
        )

        return WorkflowResponse(
            workflow_id=handle.id,
            status="started",
            started_at=datetime.utcnow(),
            company_name=request.company_name,
            message=f"Smart company profile workflow started. AI will auto-detect company type. Use workflow_id to check status.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}",
        )


@router.post("/content-worker", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def trigger_company_worker_workflow(
    request: CompanyWorkerRequest,
    api_key: str = Depends(validate_api_key),
) -> WorkflowResponse:
    """
    Trigger CompanyCreationWorkflow for comprehensive company research (60+ fields)

    This workflow performs deep research on a company and generates structured profiles
    with 60+ data fields in 90-150 seconds for $0.08-0.14.

    Features:
    - Geo-targeted research (Serper.dev)
    - Multi-source research (Crawl4AI, Firecrawl, Exa)
    - AI profile generation (Gemini 2.5)
    - Ambiguity detection & auto re-scraping
    - Featured image generation (Replicate)
    - Article relationship mapping (competitive USP!)
    - Knowledge graph sync (Zep)

    Requires X-API-Key header for authentication.

    Args:
        request: Company creation parameters (url, category, jurisdiction, app)
        api_key: Validated API key from header

    Returns:
        Workflow execution details with workflow_id for status tracking

    Example:
        POST /v1/workflows/content-worker
        {
            "url": "https://evercore.com",
            "category": "placement_agent",
            "jurisdiction": "US",
            "app": "placement"
        }
    """
    # Get Temporal client
    try:
        client = await TemporalClientManager.get_client()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Temporal: {str(e)}",
        )

    # Use CompanyCreationWorkflow on quest-content-queue
    workflow_name = "CompanyCreationWorkflow"

    # Generate workflow ID
    workflow_id = f"content-worker-{request.app}-{uuid4()}"

    # Get task queue for content-worker (different from content queue!)
    task_queue = os.getenv("CONTENT_WORKER_TASK_QUEUE", "quest-content-queue")

    try:
        # Prepare workflow input matching CompanyInput model
        workflow_input = {
            "url": request.url,
            "category": request.category,
            "jurisdiction": request.jurisdiction,
            "app": request.app,
            "force_update": request.force_update,
            "company_name": request.company_name,
            "research_depth": request.research_depth,
        }

        # Start workflow execution
        handle = await client.start_workflow(
            workflow_name,
            workflow_input,
            id=workflow_id,
            task_queue=task_queue,
        )

        return WorkflowResponse(
            workflow_id=handle.id,
            status="started",
            started_at=datetime.utcnow(),
            company_name=request.company_name or "Auto-detected",
            app=request.app,
            message=f"Company research workflow started on {task_queue}. Expected completion: 90-150s. Use workflow_id to check status.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}",
        )


# ============================================================================
# ARTICLE-WORKER ENDPOINTS (NEW)
# ============================================================================

class ArticleCreationRequest(BaseModel):
    """
    Request to trigger ArticleCreationWorkflow (4-act article + video)

    4-ACT WORKFLOW:
    - Article written FIRST with 4 sections (each has four_act_visual_hint)
    - 4-act video prompt generated FROM article sections
    - Single 12-second video (4 acts × 3 seconds)
    - Thumbnails extracted from Mux at each act timestamp
    - No separate images - thumbnails from video
    """
    topic: str = Field(..., description="Article topic or subject", min_length=5)
    article_type: str = Field(default="news", description="Type: news, guide, comparison, narrative, listicle")
    app: str = Field(default="placement", description="App context: placement, relocation, pe_news")
    target_word_count: int = Field(default=1500, description="Target word count (default 1500)")
    jurisdiction: Optional[str] = Field(default="UK", description="Geo-targeting: UK, US, SG, EU, etc.")
    video_quality: str = Field(default="medium", description="Video quality: 'low', 'medium', 'high'")
    video_model: str = Field(default="seedance", description="Video model: 'seedance' (fast) or 'wan-2.5' (better text)")
    slug: Optional[str] = Field(default=None, description="Custom URL slug for SEO. Auto-generated from title if not provided.")


@router.post("/article-creation", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def trigger_article_creation_workflow(
    request: ArticleCreationRequest,
    api_key: str = Depends(validate_api_key),
) -> WorkflowResponse:
    """
    Trigger ArticleCreationWorkflow (article-worker service)

    NEW: Uses the dedicated article-worker service with comprehensive research,
    contextual image generation (7 images), and company mention extraction.

    Timeline: 5-12 minutes
    - Research: News + Exa + Crawling (60s)
    - Content generation: Gemini 2.5 + Claude (60-120s)
    - Images: 7 contextual images via Flux Kontext Max (5-10min)
    - Company linking: Automatic NER extraction

    Requires X-API-Key header for authentication.

    Args:
        request: Article creation parameters
        api_key: Validated API key from header

    Returns:
        Workflow execution details with workflow_id for status tracking
    """
    # Get Temporal client
    try:
        client = await TemporalClientManager.get_client()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Temporal: {str(e)}",
        )

    # Generate workflow ID with topic slug for easy identification
    topic_slug = slugify(request.topic)
    workflow_id = f"4act-{request.app}-{topic_slug}-{uuid4().hex[:6]}"

    # Use content-worker task queue (same as CompanyCreationWorkflow)
    task_queue = os.getenv("CONTENT_WORKER_TASK_QUEUE", "quest-content-queue")
    workflow_name = "ArticleCreationWorkflow"

    try:
        # Prepare workflow input for 4-act article + video workflow
        workflow_input = {
            "topic": request.topic,
            "article_type": request.article_type,
            "app": request.app,
            "target_word_count": request.target_word_count,
            "jurisdiction": request.jurisdiction,
            "video_quality": request.video_quality,
            "video_model": request.video_model,
            "slug": request.slug,
        }

        # Start workflow execution
        handle = await client.start_workflow(
            workflow_name,
            workflow_input,
            id=workflow_id,
            task_queue=task_queue,
        )

        return WorkflowResponse(
            workflow_id=handle.id,
            status="started",
            started_at=datetime.utcnow(),
            topic=request.topic,
            app=request.app,
            message=f"Article creation workflow started on {task_queue}. Expected completion: 5-12 minutes. Use workflow_id to check status.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}",
        )


# ============================================================================
# NEWS MONITOR WORKFLOW ENDPOINT
# ============================================================================

class CountryGuideRequest(BaseModel):
    """Request to trigger CountryGuideCreationWorkflow"""
    country_name: str = Field(..., description="Country name (e.g., Portugal, Thailand)", min_length=2)
    country_code: str = Field(..., description="ISO 3166-1 alpha-2 code (e.g., PT, TH)", min_length=2, max_length=2)
    app: str = Field(default="relocation", description="App context (relocation)")
    language: Optional[str] = Field(default=None, description="Official languages (e.g., 'Portuguese, English')")
    relocation_motivations: Optional[List[str]] = Field(default=None, description="List: corporate, trust, wealth, retirement, digital-nomad, lifestyle, new-start, family")
    relocation_tags: Optional[List[str]] = Field(default=None, description="Tags like eu-member, schengen, english-speaking")
    video_quality: str = Field(default="medium", description="Video quality: low, medium, high")
    target_word_count: int = Field(default=4000, description="Target word count for guide")
    use_cluster_architecture: bool = Field(default=True, description="Create 4 separate cluster articles (story/guide/yolo/voices) + topic clusters + hub page. Set False for legacy single-article mode.")


class NewsMonitorRequest(BaseModel):
    """Request to trigger NewsMonitorWorkflow"""
    app: str = Field(default="placement", description="App: placement, relocation")
    min_relevance_score: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum relevance score")
    auto_create_articles: bool = Field(default=True, description="Auto-create articles for relevant stories")
    max_articles_to_create: int = Field(default=3, ge=1, le=10, description="Max articles to create")


@router.post("/news-monitor", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def trigger_news_monitor_workflow(
    request: NewsMonitorRequest,
    api_key: str = Depends(validate_api_key),
) -> WorkflowResponse:
    """
    Trigger NewsMonitorWorkflow for scheduled news monitoring

    Monitors news for an app and automatically creates articles:
    1. Fetch news from Serper (using app keywords + geographic focus)
    2. Get recently published from Neon (duplicate check)
    3. AI assessment (relevance, priority, exclusions)
    4. Spawn ArticleCreationWorkflow for top stories

    Timeline: 2-15 minutes (depends on articles created)
    Cost: ~$0.01 + article costs

    Requires X-API-Key header for authentication.

    Args:
        request: News monitoring parameters
        api_key: Validated API key from header

    Returns:
        Workflow execution details with workflow_id for status tracking
    """
    # Get Temporal client
    try:
        client = await TemporalClientManager.get_client()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Temporal: {str(e)}",
        )

    # Generate workflow ID
    workflow_id = f"news-monitor-{request.app}-{uuid4()}"

    # Use content-worker task queue
    task_queue = os.getenv("CONTENT_WORKER_TASK_QUEUE", "quest-content-queue")

    try:
        # Prepare workflow input
        workflow_input = {
            "app": request.app,
            "min_relevance_score": request.min_relevance_score,
            "auto_create_articles": request.auto_create_articles,
            "max_articles_to_create": request.max_articles_to_create
        }

        # Start workflow execution
        handle = await client.start_workflow(
            "NewsMonitorWorkflow",
            workflow_input,
            id=workflow_id,
            task_queue=task_queue,
        )

        return WorkflowResponse(
            workflow_id=handle.id,
            status="started",
            started_at=datetime.utcnow(),
            app=request.app,
            message=f"News monitoring started for {request.app}. Will create up to {request.max_articles_to_create} articles. Use workflow_id to check status.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}",
        )


# ============================================================================
# COUNTRY GUIDE WORKFLOW ENDPOINT
# ============================================================================

@router.post("/country-guide", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def trigger_country_guide_workflow(
    request: CountryGuideRequest,
    api_key: str = Depends(validate_api_key),
) -> WorkflowResponse:
    """
    Trigger CountryGuideCreationWorkflow for comprehensive country relocation guides

    Creates a full country guide covering all 8 relocation motivations:
    - corporate, trust, wealth, retirement, digital-nomad, lifestyle, new-start, family

    Workflow phases (8-15 minutes):
    1. Country Setup - Create/update country row
    2. SEO Research - DataForSEO keyword research
    3. Authoritative Research - Exa + DataForSEO for gov sites, tax info
    4. Crawl Sources - Crawl4AI batch crawl
    5. Curate Research - AI filter and summarize
    6. Zep Context - Query knowledge graph
    7. Generate Guide - AI generates 8-motivation content
    8. Save Article - Save to articles table
    9. Link to Country - Set country_code and guide_type
    10. Update Country Facts - Merge facts into countries.facts JSONB
    11. Sync to Zep - Update knowledge graph
    12. Generate Video - 4-act Seedance video
    13. Final Update - Add video, publish

    Requires X-API-Key header for authentication.

    Args:
        request: Country guide creation parameters
        api_key: Validated API key from header

    Returns:
        Workflow execution details with workflow_id for status tracking

    Example:
        POST /v1/workflows/country-guide
        {
            "country_name": "Portugal",
            "country_code": "PT",
            "app": "relocation",
            "video_quality": "medium"
        }
    """
    # Get Temporal client
    try:
        client = await TemporalClientManager.get_client()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Temporal: {str(e)}",
        )

    # Generate workflow ID
    country_slug = slugify(request.country_name)
    workflow_id = f"country-guide-{country_slug}-{uuid4().hex[:6]}"

    # Use content-worker task queue
    task_queue = os.getenv("CONTENT_WORKER_TASK_QUEUE", "quest-content-queue")

    try:
        # Prepare workflow input
        workflow_input = {
            "country_name": request.country_name,
            "country_code": request.country_code.upper(),
            "app": request.app,
            "language": request.language,
            "relocation_motivations": request.relocation_motivations,
            "relocation_tags": request.relocation_tags,
            "video_quality": request.video_quality,
            "target_word_count": request.target_word_count,
            "use_cluster_architecture": request.use_cluster_architecture,
        }

        # Start workflow execution
        handle = await client.start_workflow(
            "CountryGuideCreationWorkflow",
            workflow_input,
            id=workflow_id,
            task_queue=task_queue,
        )

        return WorkflowResponse(
            workflow_id=handle.id,
            status="started",
            started_at=datetime.utcnow(),
            topic=f"{request.country_name} Country Guide",
            app=request.app,
            message=f"Country guide workflow started for {request.country_name} ({request.country_code}). Expected completion: 8-15 minutes. Use workflow_id to check status.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}",
        )


@router.post("/video-enrichment", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def trigger_video_enrichment(
    request: VideoEnrichmentRequest,
    api_key: str = Depends(validate_api_key),
) -> WorkflowResponse:
    """
    Trigger VideoEnrichmentWorkflow to add videos to existing article

    Analyzes article content and enriches with videos:
    - Ensures hero video is present
    - Generates 12-second 4-act videos using seedance-1-pro-fast
    - Inserts videos into at least 4 content sections
    - Uses thumbnails for remaining sections
    - Uploads to MUX and creates time-based cuts

    Workflow phases (2-5 minutes):
    1. Fetch article from database
    2. Check if video already exists (skip unless force_regenerate)
    3. Generate 4-act video prompt from article content
    4. Generate 12-second video with seedance-1-pro-fast
    5. Upload to MUX and cut into 4 acts
    6. Update article with video embeds and thumbnails

    Requires X-API-Key header for authentication.

    Args:
        request: Video enrichment parameters
        api_key: Validated API key from header

    Returns:
        Workflow execution details with workflow_id for status tracking

    Example:
        POST /v1/workflows/video-enrichment
        {
            "slug": "france-relocation-guide",
            "app": "relocation",
            "video_model": "seedance-1-pro-fast",
            "video_resolution": "480p",
            "min_sections": 4,
            "force_regenerate": false
        }
    """
    # Get Temporal client
    try:
        client = await TemporalClientManager.get_client()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Temporal: {str(e)}",
        )

    # Generate workflow ID
    workflow_id = f"video-enrichment-{request.slug}-{uuid4().hex[:8]}"

    # Use quest-content-queue for VideoEnrichmentWorkflow
    task_queue = "quest-content-queue"

    try:
        # Start VideoEnrichmentWorkflow
        workflow_name = "VideoEnrichmentWorkflow"
        workflow_args = [
            request.slug,
            request.app,
            request.video_model,
            request.min_sections,
            request.force_regenerate
        ]

        # Start workflow execution
        handle = await client.start_workflow(
            workflow_name,
            args=workflow_args,
            id=workflow_id,
            task_queue=task_queue,
        )

        return WorkflowResponse(
            workflow_id=handle.id,
            status="started",
            started_at=datetime.utcnow(),
            topic=request.slug,
            app=request.app,
            message=f"Video enrichment workflow started for article '{request.slug}'. Expected completion: 2-5 minutes. Use workflow_id to check status.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}",
        )
