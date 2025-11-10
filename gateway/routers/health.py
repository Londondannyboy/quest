"""
Health Check Endpoints

Liveness and readiness probes for Railway/Kubernetes.
"""

import os
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from gateway.temporal_client import TemporalClientManager


router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str = "1.0.0"
    environment: str


class ReadinessResponse(BaseModel):
    """Readiness check response"""
    status: str
    temporal_connected: bool
    timestamp: datetime


@router.get("/health")
async def health_check() -> HealthResponse:
    """
    Basic health check - always returns 200 if service is running

    Returns:
        Health status
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        environment=os.getenv("ENVIRONMENT", "development"),
    )


@router.get("/ready")
async def readiness_check() -> ReadinessResponse:
    """
    Readiness check - verifies all dependencies are available

    Returns:
        Readiness status

    Raises:
        HTTPException: If service is not ready
    """
    temporal_connected = False

    # Check Temporal connection
    try:
        client = await TemporalClientManager.get_client()
        temporal_connected = client is not None
    except Exception:
        pass

    if not temporal_connected:
        raise HTTPException(
            status_code=503,
            detail="Service not ready - Temporal connection failed",
        )

    return ReadinessResponse(
        status="ready",
        temporal_connected=temporal_connected,
        timestamp=datetime.utcnow(),
    )


@router.get("/")
async def root():
    """
    Root endpoint - API information

    Returns:
        API metadata
    """
    return {
        "name": "Quest Gateway API",
        "version": "1.0.0",
        "description": "HTTP API for triggering Quest content generation workflows",
        "docs": "/docs",
        "health": "/health",
        "readiness": "/ready",
    }
