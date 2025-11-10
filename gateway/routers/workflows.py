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

from gateway.auth import validate_api_key
from gateway.temporal_client import TemporalClientManager


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


class WorkflowResponse(BaseModel):
    """Response after triggering workflow"""
    workflow_id: str
    status: str
    started_at: datetime
    topic: str
    app: str
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
        # Start workflow execution
        handle = await client.start_workflow(
            "NewsroomWorkflow",
            args=[
                request.topic,
                request.target_word_count,
                request.auto_approve,
                request.app,
            ],
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
