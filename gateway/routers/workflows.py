"""
Workflow Trigger Endpoints

HTTP endpoints for triggering Temporal workflows.
"""

import os
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from auth import validate_api_key
from temporal_client import TemporalClientManager


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
    """Request to trigger CompanyCreationWorkflow (company-worker service)"""
    url: str = Field(..., description="Company website URL", min_length=5)
    category: str = Field(..., description="Company category: placement_agent, relocation_provider, recruiter")
    jurisdiction: str = Field(..., description="Primary jurisdiction: UK, US, SG, EU, etc.")
    app: str = Field(default="relocation", description="App context: placement, relocation")
    force_update: bool = Field(default=False, description="Force re-research of existing company")
    company_name: Optional[str] = Field(default=None, description="Override auto-detected company name")
    research_depth: str = Field(default="standard", description="Research depth: quick, standard, deep")


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

    # Get task queue from environment
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "quest-content-queue")

    try:
        # Route to dedicated workflow if available, otherwise use NewsroomWorkflow
        workflow_name = "NewsroomWorkflow"
        workflow_args = [
            request.topic,
            request.target_word_count,
            request.auto_approve,
            request.app,
        ]

        # Use dedicated workflows for specific apps
        if request.app == "placement":
            workflow_name = "PlacementWorkflow"
            workflow_args = [
                request.topic,
                request.target_word_count,
                request.auto_approve,
                True,  # skip_zep_check
            ]
        elif request.app == "relocation":
            workflow_name = "RelocationWorkflow"
            workflow_args = [
                request.topic,
                request.target_word_count,
                request.auto_approve,
                True,  # skip_zep_check
            ]
        elif request.app == "chief-of-staff":
            workflow_name = "ChiefOfStaffWorkflow"
            workflow_args = [
                request.topic,
                request.target_word_count,
                request.auto_approve,
                True,  # skip_zep_check
            ]
        elif request.app == "gtm":
            workflow_name = "GTMWorkflow"
            workflow_args = [
                request.topic,
                request.target_word_count,
                request.auto_approve,
                True,  # skip_zep_check
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

    # Get task queue from environment
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "quest-content-queue")

    try:
        # Always use ArticleWorkflow for research-based articles
        workflow_name = "ArticleWorkflow"
        workflow_args = [
            request.topic,
            request.app,
            request.target_word_count,
            request.num_research_sources,
            request.deep_crawl_enabled,
            request.skip_zep_sync,
            request.article_format,
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


@router.post("/company-worker", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
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
        POST /v1/workflows/company-worker
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

    # Use CompanyCreationWorkflow on quest-company-queue
    workflow_name = "CompanyCreationWorkflow"

    # Generate workflow ID
    workflow_id = f"company-worker-{request.app}-{uuid4()}"

    # Get task queue for company-worker (different from content queue!)
    task_queue = os.getenv("COMPANY_WORKER_TASK_QUEUE", "quest-company-queue")

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
    """Request to trigger ArticleCreationWorkflow (company-worker service)"""
    topic: str = Field(..., description="Article topic or subject", min_length=5)
    article_type: str = Field(default="news", description="Type: news, guide, comparison")
    app: str = Field(default="placement", description="App context: placement, relocation, chief-of-staff, gtm, newsroom")
    target_word_count: int = Field(default=1500, ge=500, le=3000, description="Target word count")
    jurisdiction: Optional[str] = Field(default="UK", description="Geo-targeting: UK, US, SG, EU, etc.")
    num_research_sources: int = Field(default=10, ge=3, le=15, description="Number of research sources")
    generate_images: bool = Field(default=False, description="Generate contextual images (adds 5-8 min)")
    skip_zep_sync: bool = Field(default=False, description="Skip Zep knowledge graph sync")


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

    # Generate workflow ID
    workflow_id = f"article-creation-{request.app}-{uuid4()}"

    # Use company-worker task queue (same as CompanyCreationWorkflow)
    task_queue = os.getenv("COMPANY_WORKER_TASK_QUEUE", "quest-company-queue")
    workflow_name = "ArticleCreationWorkflow"

    try:
        # Prepare workflow input matching ArticleCreationWorkflow expected format
        workflow_input = {
            "topic": request.topic,
            "article_type": request.article_type,
            "app": request.app,
            "target_word_count": request.target_word_count,
            "jurisdiction": request.jurisdiction,
            "num_research_sources": request.num_research_sources,
            "generate_images": request.generate_images,
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
