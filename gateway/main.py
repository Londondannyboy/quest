"""
Quest Gateway - FastAPI HTTP API

HTTP API for triggering Quest content generation workflows.
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers (relative imports for Railway deployment)
from routers import health, workflows, voice, user_profile
from temporal_client import TemporalClientManager


# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events

    Startup:
    - Initialize Temporal client connection
    - Validate environment variables

    Shutdown:
    - Close Temporal client connection
    """
    # Startup
    print("🚀 Quest Gateway starting...")
    print(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"   Temporal Address: {os.getenv('TEMPORAL_ADDRESS', 'not set')}")
    print(f"   Temporal Namespace: {os.getenv('TEMPORAL_NAMESPACE', 'not set')}")

    # Validate critical environment variables
    required_vars = ["TEMPORAL_ADDRESS", "TEMPORAL_NAMESPACE"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"⚠️  Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("   Some features may not work correctly")

    # Initialize Temporal client (lazy - will connect on first use)
    print("✅ Gateway ready to accept requests")

    yield

    # Shutdown
    print("\n👋 Quest Gateway shutting down...")
    await TemporalClientManager.close()
    print("✅ Cleanup complete")


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Quest Gateway API",
    description="HTTP API for triggering Quest content generation workflows",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS middleware (configure allowed origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors

    Returns:
        JSON error response
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "type": type(exc).__name__,
        },
    )


# ============================================================================
# ROUTERS
# ============================================================================

# Include routers
app.include_router(health.router)
app.include_router(workflows.router)
app.include_router(voice.router)
app.include_router(user_profile.router)


# ============================================================================
# DEVELOPMENT SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))

    print(f"\n{'='*60}")
    print("🚀 Starting Quest Gateway (Development Server)")
    print(f"{'='*60}")
    print(f"   URL: http://localhost:{port}")
    print(f"   Docs: http://localhost:{port}/docs")
    print(f"   Health: http://localhost:{port}/health")
    print(f"{'='*60}\n")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )
