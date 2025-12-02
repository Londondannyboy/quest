"""
User Profile Router

API endpoints for user profile facts and voice sessions.
All endpoints require Stack Auth authentication.
"""

import os
import sys
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Header, Depends
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/user", tags=["user-profile"])

# Import services
try:
    gateway_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if gateway_dir not in sys.path:
        sys.path.insert(0, gateway_dir)
    from services.user_profile_service import user_profile_service
    from models.user_profile import FactType, FactSource
    SERVICE_ENABLED = user_profile_service.enabled
except ImportError as e:
    user_profile_service = None
    SERVICE_ENABLED = False
    logger.warning("user_profile_service_import_failed", error=str(e))

# Import ZEP user graph service
try:
    from services.zep_user_graph import zep_user_graph_service
    ZEP_USER_GRAPH_ENABLED = zep_user_graph_service.enabled
    logger.info("zep_user_graph_service_imported", enabled=ZEP_USER_GRAPH_ENABLED)
except ImportError as e:
    zep_user_graph_service = None
    ZEP_USER_GRAPH_ENABLED = False
    logger.warning("zep_user_graph_service_import_failed", error=str(e))


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class FactCreateRequest(BaseModel):
    """Request to create a new fact."""
    fact_type: str
    fact_value: Dict[str, Any]
    source: str = "user_edit"
    confidence: float = 1.0


class FactUpdateRequest(BaseModel):
    """Request to update a fact."""
    fact_value: Optional[Dict[str, Any]] = None
    is_user_verified: Optional[bool] = None


class SimpleFactUpdateRequest(BaseModel):
    """Simple request to update a fact value (from dashboard edit)."""
    fact_id: str
    fact_type: str
    value: str


class ProfileResponse(BaseModel):
    """User profile response."""
    user_id: str
    profile: Optional[Dict[str, Any]] = None
    facts: List[Dict[str, Any]] = []
    snapshot: Dict[str, Any] = {}


class FactResponse(BaseModel):
    """Single fact response."""
    id: int
    fact_type: str
    fact_value: Dict[str, Any]
    source: str
    confidence: float
    is_user_verified: bool
    created_at: Optional[str] = None


class SessionsResponse(BaseModel):
    """Voice sessions list response."""
    user_id: str
    sessions: List[Dict[str, Any]] = []


# ============================================================================
# AUTH HELPERS
# ============================================================================

async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_stack_user_id: Optional[str] = Header(None)
) -> str:
    """
    Get current user from Stack Auth headers.

    In production, validate JWT. For now, trust x-stack-user-id header.
    """
    # Check for user ID header (set by frontend)
    if x_stack_user_id:
        return x_stack_user_id

    # Could validate JWT from authorization header here
    if authorization and authorization.startswith("Bearer "):
        # TODO: Validate Stack Auth JWT and extract user_id
        pass

    raise HTTPException(
        status_code=401,
        detail="Authentication required. Please log in."
    )


# ============================================================================
# PROFILE ENDPOINTS
# ============================================================================

@router.get("/profile")
async def get_profile(
    user_id: str = Depends(get_current_user)
) -> ProfileResponse:
    """
    Get user profile with active facts and snapshot.

    Returns profile data, all active facts, and aggregated snapshot.
    """
    if not SERVICE_ENABLED:
        raise HTTPException(status_code=503, detail="Profile service unavailable")

    try:
        # Get or create profile
        profile_id = await user_profile_service.get_or_create_profile(user_id)
        if not profile_id:
            raise HTTPException(status_code=500, detail="Failed to get/create profile")

        # Get profile data
        profile = await user_profile_service.get_profile_by_stack_id(user_id)

        # Get facts
        facts = await user_profile_service.get_facts_by_stack_id(user_id, active_only=True)

        # Build snapshot
        snapshot = await user_profile_service.build_profile_snapshot(user_id)

        return ProfileResponse(
            user_id=user_id,
            profile=profile,
            facts=facts,
            snapshot=snapshot
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_profile_error", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get profile")


@router.get("/profile/snapshot")
async def get_profile_snapshot(
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get quick profile snapshot (aggregated facts).

    Lightweight endpoint for voice prompt context.
    """
    if not SERVICE_ENABLED:
        return {"user_id": user_id, "total_facts": 0}

    try:
        snapshot = await user_profile_service.build_profile_snapshot(user_id)
        return {"user_id": user_id, **snapshot}
    except Exception as e:
        logger.error("get_snapshot_error", user_id=user_id, error=str(e))
        return {"user_id": user_id, "total_facts": 0}


@router.get("/profile/context")
async def get_profile_context(
    user_id: str = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Get profile context formatted for LLM prompts.

    Returns natural language summary of user profile.
    """
    if not SERVICE_ENABLED:
        return {"context": ""}

    try:
        context = await user_profile_service.get_profile_context_for_prompt(user_id)
        return {"context": context}
    except Exception as e:
        logger.error("get_context_error", user_id=user_id, error=str(e))
        return {"context": ""}


# ============================================================================
# FACTS ENDPOINTS
# ============================================================================

@router.get("/profile/facts")
async def list_facts(
    user_id: str = Depends(get_current_user),
    fact_type: Optional[str] = Query(None, description="Filter by fact type"),
    include_inactive: bool = Query(False, description="Include soft-deleted facts")
) -> Dict[str, Any]:
    """
    List all facts for current user.

    Optionally filter by type or include inactive facts.
    """
    if not SERVICE_ENABLED:
        raise HTTPException(status_code=503, detail="Profile service unavailable")

    try:
        facts = await user_profile_service.get_facts_by_stack_id(
            user_id,
            fact_type=fact_type,
            active_only=not include_inactive
        )

        # Group by type
        by_type = {}
        for fact in facts:
            ft = fact["fact_type"]
            if ft not in by_type:
                by_type[ft] = []
            by_type[ft].append(fact)

        return {
            "user_id": user_id,
            "facts": facts,
            "by_type": by_type,
            "total": len(facts),
            "verified": sum(1 for f in facts if f.get("is_user_verified"))
        }

    except Exception as e:
        logger.error("list_facts_error", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list facts")


@router.post("/profile/facts")
async def create_fact(
    request: FactCreateRequest,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new fact (user-initiated).

    Users can manually add facts about themselves.
    """
    if not SERVICE_ENABLED:
        raise HTTPException(status_code=503, detail="Profile service unavailable")

    try:
        # Get or create profile
        profile_id = await user_profile_service.get_or_create_profile(user_id)
        if not profile_id:
            raise HTTPException(status_code=500, detail="Failed to get profile")

        # Store fact
        fact_id = await user_profile_service.store_fact(
            user_profile_id=profile_id,
            fact_type=request.fact_type,
            fact_value=request.fact_value,
            source=request.source,
            confidence=request.confidence
        )

        if not fact_id:
            raise HTTPException(status_code=500, detail="Failed to create fact")

        return {
            "id": fact_id,
            "fact_type": request.fact_type,
            "fact_value": request.fact_value,
            "created": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_fact_error", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create fact")


@router.put("/profile/facts/{fact_id}")
async def update_fact(
    fact_id: int,
    request: FactUpdateRequest,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update a fact (user edit).

    Users can correct or verify facts extracted from conversations.
    """
    if not SERVICE_ENABLED:
        raise HTTPException(status_code=503, detail="Profile service unavailable")

    try:
        # TODO: Verify fact belongs to user

        success = await user_profile_service.update_fact(
            fact_id=fact_id,
            fact_value=request.fact_value,
            is_user_verified=request.is_user_verified
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update fact")

        return {"id": fact_id, "updated": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_fact_error", fact_id=fact_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update fact")


@router.delete("/profile/facts/{fact_id}")
async def delete_fact(
    fact_id: int,
    user_id: str = Depends(get_current_user),
    hard: bool = Query(False, description="Permanently delete instead of soft delete")
) -> Dict[str, Any]:
    """
    Delete a fact.

    Soft deletes by default (can be restored). Use hard=true for permanent deletion.
    """
    if not SERVICE_ENABLED:
        raise HTTPException(status_code=503, detail="Profile service unavailable")

    try:
        # TODO: Verify fact belongs to user

        success = await user_profile_service.delete_fact(
            fact_id=fact_id,
            soft=not hard
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete fact")

        return {"id": fact_id, "deleted": True, "hard": hard}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_fact_error", fact_id=fact_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete fact")


@router.post("/profile/update")
async def update_fact_simple(
    request: SimpleFactUpdateRequest,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Simple endpoint to update a fact value from the dashboard.

    Used by the RepoSection edit feature.
    """
    if not SERVICE_ENABLED:
        raise HTTPException(status_code=503, detail="Profile service unavailable")

    try:
        logger.info("update_fact_simple_called",
                   user_id=user_id,
                   fact_id=request.fact_id,
                   fact_type=request.fact_type,
                   value=request.value[:50] if request.value else None)

        # Parse fact_id (could be string or int)
        fact_id = None
        try:
            fact_id = int(request.fact_id)
        except (ValueError, TypeError):
            logger.debug("fact_id_not_integer", fact_id=request.fact_id)

        if fact_id:
            # Update existing fact by ID
            success = await user_profile_service.update_fact(
                fact_id=fact_id,
                fact_value={"value": request.value},
                is_user_verified=True  # User explicitly edited, so verified
            )

            if not success:
                logger.warning("update_fact_failed", fact_id=fact_id)
                raise HTTPException(status_code=500, detail="Failed to update fact")

            # Emit SSE event for real-time update
            try:
                from services.event_publisher import emit_fact_updated
                await emit_fact_updated(
                    user_id,
                    fact_id,
                    old_value=None,  # We don't have old value here
                    new_value=request.value,
                    fact_type=request.fact_type
                )
            except Exception as evt_err:
                logger.debug("emit_fact_updated_error", error=str(evt_err))

            # Sync to ZEP User Graph after fact update
            try:
                if ZEP_USER_GRAPH_ENABLED and zep_user_graph_service:
                    profile = await user_profile_service.get_profile_by_stack_id(user_id)
                    all_facts = await user_profile_service.get_facts_by_stack_id(user_id, active_only=True)
                    sync_result = await zep_user_graph_service.sync_user_profile(
                        user_id=user_id,
                        profile=profile or {},
                        facts=all_facts,
                        app_id="relocation"
                    )
                    logger.info("zep_graph_synced_from_repo",
                               user_id=user_id,
                               fact_type=request.fact_type,
                               facts_synced=sync_result.get("facts_synced", 0))
            except Exception as zep_err:
                logger.warning("zep_sync_error_from_repo", error=str(zep_err))

            logger.info("fact_updated_success", fact_id=fact_id)
            return {"success": True, "id": fact_id, "updated": True, "zep_synced": ZEP_USER_GRAPH_ENABLED}
        else:
            # No valid fact_id - try to find existing fact by type and update it
            existing_facts = await user_profile_service.get_facts_by_stack_id(
                user_id, fact_type=request.fact_type, active_only=True
            )

            if existing_facts:
                # Update the most recent fact of this type
                existing_fact_id = existing_facts[0].get("id")
                if existing_fact_id:
                    success = await user_profile_service.update_fact(
                        fact_id=existing_fact_id,
                        fact_value={"value": request.value},
                        is_user_verified=True
                    )
                    if success:
                        # Sync to ZEP after update by type
                        try:
                            if ZEP_USER_GRAPH_ENABLED and zep_user_graph_service:
                                profile = await user_profile_service.get_profile_by_stack_id(user_id)
                                all_facts = await user_profile_service.get_facts_by_stack_id(user_id, active_only=True)
                                await zep_user_graph_service.sync_user_profile(
                                    user_id=user_id,
                                    profile=profile or {},
                                    facts=all_facts,
                                    app_id="relocation"
                                )
                        except Exception as zep_err:
                            logger.warning("zep_sync_error_from_repo", error=str(zep_err))

                        logger.info("fact_updated_by_type", fact_type=request.fact_type)
                        return {"success": True, "id": existing_fact_id, "updated": True, "zep_synced": ZEP_USER_GRAPH_ENABLED}

            # Create new fact if no existing fact found
            profile_id = await user_profile_service.get_or_create_profile(user_id)
            if not profile_id:
                raise HTTPException(status_code=500, detail="Failed to get profile")

            new_fact_id = await user_profile_service.store_fact(
                user_profile_id=profile_id,
                fact_type=request.fact_type,
                fact_value={"value": request.value},
                source="user_edit",
                confidence=1.0,
                is_verified=True
            )

            # Sync to ZEP after new fact creation
            try:
                if ZEP_USER_GRAPH_ENABLED and zep_user_graph_service:
                    profile = await user_profile_service.get_profile_by_stack_id(user_id)
                    all_facts = await user_profile_service.get_facts_by_stack_id(user_id, active_only=True)
                    await zep_user_graph_service.sync_user_profile(
                        user_id=user_id,
                        profile=profile or {},
                        facts=all_facts,
                        app_id="relocation"
                    )
            except Exception as zep_err:
                logger.warning("zep_sync_error_from_repo", error=str(zep_err))

            logger.info("fact_created", fact_id=new_fact_id, fact_type=request.fact_type)
            return {"success": True, "id": new_fact_id, "created": True, "zep_synced": ZEP_USER_GRAPH_ENABLED}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_fact_simple_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update fact")


# ============================================================================
# SESSIONS ENDPOINTS
# ============================================================================

@router.get("/sessions")
async def list_sessions(
    user_id: str = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100)
) -> SessionsResponse:
    """
    List recent voice sessions for current user.
    """
    if not SERVICE_ENABLED:
        return SessionsResponse(user_id=user_id, sessions=[])

    try:
        sessions = await user_profile_service.get_user_sessions(user_id, limit=limit)
        return SessionsResponse(user_id=user_id, sessions=sessions)

    except Exception as e:
        logger.error("list_sessions_error", user_id=user_id, error=str(e))
        return SessionsResponse(user_id=user_id, sessions=[])


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a specific voice session with messages and extracted facts.
    """
    if not SERVICE_ENABLED:
        raise HTTPException(status_code=503, detail="Profile service unavailable")

    try:
        session = await user_profile_service.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Verify session belongs to user
        if session.get("stack_user_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return session

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_session_error", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get session")


# ============================================================================
# ZEP USER GRAPH ENDPOINTS
# ============================================================================

class ZepSyncRequest(BaseModel):
    """Request to sync profile to ZEP."""
    app_id: str = "relocation"


class ZepSyncResponse(BaseModel):
    """Response from ZEP sync."""
    success: bool
    user_id: str
    graph_id: Optional[str] = None
    episode_id: Optional[str] = None
    facts_synced: int = 0
    error: Optional[str] = None


@router.post("/profile/sync-to-zep")
async def sync_profile_to_zep(
    request: ZepSyncRequest,
    user_id: str = Depends(get_current_user)
) -> ZepSyncResponse:
    """
    Sync user profile and facts to ZEP knowledge graph.

    Call this after profile extraction to enable semantic search.
    """
    if not SERVICE_ENABLED:
        return ZepSyncResponse(
            success=False,
            user_id=user_id,
            error="Profile service not enabled"
        )

    if not ZEP_USER_GRAPH_ENABLED:
        return ZepSyncResponse(
            success=False,
            user_id=user_id,
            error="ZEP user graph service not enabled"
        )

    try:
        # Get profile from Neon
        profile = await user_profile_service.get_profile_by_stack_id(user_id)

        # Get facts from Neon
        facts = await user_profile_service.get_facts_by_stack_id(user_id, active_only=True)

        # Sync to ZEP
        result = await zep_user_graph_service.sync_user_profile(
            user_id=user_id,
            profile=profile or {},
            facts=facts,
            app_id=request.app_id
        )

        return ZepSyncResponse(
            success=result.get("success", False),
            user_id=user_id,
            graph_id=result.get("graph_id"),
            episode_id=result.get("episode_id"),
            facts_synced=result.get("facts_synced", 0),
            error=result.get("error")
        )

    except Exception as e:
        logger.error("sync_profile_to_zep_error", user_id=user_id, error=str(e))
        return ZepSyncResponse(
            success=False,
            user_id=user_id,
            error=str(e)
        )


@router.get("/profile/zep-search")
async def search_user_facts_in_zep(
    user_id: str = Depends(get_current_user),
    query: str = Query(..., description="Natural language search query"),
    limit: int = Query(10, ge=1, le=50)
) -> Dict[str, Any]:
    """
    Search user's facts in ZEP semantically.

    Enables natural language queries like "What countries is this user interested in?"
    """
    if not ZEP_USER_GRAPH_ENABLED:
        return {
            "success": False,
            "user_id": user_id,
            "query": query,
            "facts": [],
            "error": "ZEP user graph service not enabled"
        }

    try:
        result = await zep_user_graph_service.search_user_facts(
            user_id=user_id,
            query=query,
            limit=limit
        )
        return result

    except Exception as e:
        logger.error("search_user_facts_error", user_id=user_id, error=str(e))
        return {
            "success": False,
            "user_id": user_id,
            "query": query,
            "facts": [],
            "error": str(e)
        }


@router.get("/profile/zep-graph")
async def get_user_zep_graph(
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user's nodes and edges from ZEP for visualization.

    Returns data suitable for force-graph visualization.
    """
    if not ZEP_USER_GRAPH_ENABLED:
        return {
            "success": False,
            "nodes": [],
            "edges": [],
            "error": "ZEP user graph service not enabled"
        }

    try:
        result = await zep_user_graph_service.get_all_user_nodes(user_id)
        return result

    except Exception as e:
        logger.error("get_user_zep_graph_error", user_id=user_id, error=str(e))
        return {
            "success": False,
            "nodes": [],
            "edges": [],
            "error": str(e)
        }


@router.get("/profile/zep-context")
async def get_user_zep_context(
    user_id: str = Depends(get_current_user),
    topic: Optional[str] = Query(None, description="Optional topic to focus context on")
) -> Dict[str, Any]:
    """
    Get user context from ZEP for LLM prompts.

    Combines Neon profile context with ZEP semantic context.
    """
    neon_context = ""
    zep_context = ""

    if SERVICE_ENABLED:
        try:
            neon_context = await user_profile_service.get_profile_context_for_prompt(user_id)
        except Exception as e:
            logger.error("get_neon_context_error", user_id=user_id, error=str(e))

    if ZEP_USER_GRAPH_ENABLED:
        try:
            zep_context = await zep_user_graph_service.get_user_context_for_prompt(user_id, topic)
        except Exception as e:
            logger.error("get_zep_context_error", user_id=user_id, error=str(e))

    # Combine contexts
    combined = neon_context
    if zep_context and zep_context not in combined:
        combined += "\n" + zep_context

    return {
        "user_id": user_id,
        "context": combined,
        "sources": {
            "neon": bool(neon_context),
            "zep": bool(zep_context)
        }
    }


# ============================================================================
# DEBUG / HEALTH ENDPOINTS
# ============================================================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Check user profile service health."""
    return {
        "service": "user-profile",
        "enabled": SERVICE_ENABLED,
        "zep_enabled": ZEP_USER_GRAPH_ENABLED,
        "database_configured": bool(os.getenv("DATABASE_URL"))
    }
