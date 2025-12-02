"""
Dashboard Router

SSE endpoints for real-time dashboard updates and content recommendations.
"""

import os
import sys
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, Header, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Import event publisher
try:
    gateway_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if gateway_dir not in sys.path:
        sys.path.insert(0, gateway_dir)
    from services.event_publisher import subscribe, unsubscribe
    EVENT_PUBLISHER_ENABLED = True
except ImportError as e:
    EVENT_PUBLISHER_ENABLED = False
    logger.warning("event_publisher_import_failed", error=str(e))

# Import content service for Neon queries
try:
    from services.content_service import content_service
    CONTENT_SERVICE_ENABLED = content_service.enabled if hasattr(content_service, 'enabled') else True
except ImportError:
    content_service = None
    CONTENT_SERVICE_ENABLED = False
    logger.warning("content_service_not_available")


# ============================================================================
# AUTH
# ============================================================================

async def get_current_user(
    x_stack_user_id: Optional[str] = Header(None)
) -> str:
    """Get current user from Stack Auth headers."""
    if x_stack_user_id:
        return x_stack_user_id
    raise HTTPException(status_code=401, detail="Authentication required")


# ============================================================================
# SSE EVENTS ENDPOINT
# ============================================================================

@router.get("/events")
async def stream_dashboard_events(
    user_id: str = Query(..., description="User ID for event stream"),
    x_stack_user_id: Optional[str] = Header(None)
):
    """
    SSE stream of real-time dashboard events.

    Events emitted:
    - fact_extracted: New fact from conversation
    - fact_updated: Existing fact changed
    - profile_suggestion: AI suggests profile change (human-in-the-loop)
    - content_suggestion: Relevant content from Neon
    - content_no_results: No content found for query
    - transcript_message: Live conversation message
    - tool_start/tool_end: Tool execution visibility
    - summary_update: Conversation summary
    - session_start/session_end: Session lifecycle
    - heartbeat: Connection keep-alive
    """
    effective_user_id = x_stack_user_id or user_id

    if not EVENT_PUBLISHER_ENABLED:
        # Fallback: just send heartbeats
        async def heartbeat_only():
            while True:
                yield {
                    "event": "heartbeat",
                    "data": datetime.utcnow().isoformat(),
                }
                await asyncio.sleep(30)
        return EventSourceResponse(heartbeat_only())

    # Subscribe to user's event stream
    queue = await subscribe(effective_user_id)

    async def event_generator():
        try:
            while True:
                try:
                    # Wait for event with timeout (for heartbeat)
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield {
                        "event": "heartbeat",
                        "data": datetime.utcnow().isoformat(),
                    }
        except asyncio.CancelledError:
            pass
        finally:
            await unsubscribe(effective_user_id, queue)

    return EventSourceResponse(event_generator())


# ============================================================================
# CONTENT RECOMMENDATIONS
# ============================================================================

class ContentRecommendation(BaseModel):
    id: int
    type: str
    title: str
    slug: str
    excerpt: Optional[str] = None
    country: Optional[str] = None
    country_flag: Optional[str] = None
    match_reason: Optional[str] = None


@router.get("/content/recommendations")
async def get_content_recommendations(
    user_id: str = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50)
) -> Dict[str, Any]:
    """
    Get personalized content recommendations based on user profile.

    Returns country guides, articles, jobs, and deals relevant to user.
    """
    if not CONTENT_SERVICE_ENABLED:
        return {"articles": [], "error": "Content service not available"}

    try:
        # Get user's destinations/interests from profile
        from services.user_profile_service import user_profile_service

        facts = await user_profile_service.get_facts_by_stack_id(user_id, active_only=True)

        # Extract destinations and interests
        destinations = []
        interests = []
        for fact in facts:
            if fact.get("fact_type") == "destination":
                value = fact.get("fact_value", {})
                if isinstance(value, dict):
                    destinations.append(value.get("value") or value.get("country"))
                else:
                    destinations.append(str(value))
            elif fact.get("fact_type") in ["visa_interest", "profession", "work_type"]:
                value = fact.get("fact_value", {})
                if isinstance(value, dict):
                    interests.append(value.get("value"))
                else:
                    interests.append(str(value))

        # Query content based on destinations
        articles = []
        for dest in destinations[:3]:  # Top 3 destinations
            if dest:
                country_content = await content_service.search_by_country(dest, limit=3)
                articles.extend(country_content)

        return {
            "articles": articles[:limit],
            "based_on": {
                "destinations": destinations[:3],
                "interests": interests[:5]
            }
        }

    except Exception as e:
        logger.error("get_recommendations_error", user_id=user_id, error=str(e))
        return {"articles": [], "error": str(e)}


@router.get("/content/recent")
async def get_recent_articles(
    limit: int = Query(10, ge=1, le=50)
) -> Dict[str, Any]:
    """
    Get recent published articles from relocation.quest.

    No auth required - public content.
    """
    if not CONTENT_SERVICE_ENABLED:
        return {"articles": [], "error": "Content service not available"}

    try:
        articles = await content_service.get_recent_articles(limit=limit)
        return {"articles": articles, "count": len(articles)}

    except Exception as e:
        logger.error("get_recent_articles_error", error=str(e))
        return {"articles": [], "error": str(e)}


@router.get("/content/articles")
async def get_all_articles(
    limit: int = Query(100, ge=1, le=200)
) -> Dict[str, Any]:
    """
    Get all published relocation articles with metadata.

    No auth required - public content.
    Returns articles grouped by article_mode for display.
    """
    if not CONTENT_SERVICE_ENABLED:
        return {"articles": [], "error": "Content service not available"}

    try:
        articles = await content_service.get_all_articles(limit=limit)
        return {"articles": articles, "count": len(articles)}

    except Exception as e:
        logger.error("get_all_articles_error", error=str(e))
        return {"articles": [], "error": str(e)}


@router.post("/content/search")
async def search_content(
    query: str = Query(..., description="Search query"),
    user_id: str = Depends(get_current_user),
    content_type: Optional[str] = Query(None, description="Filter by type: country_guide, article, job, deal"),
    limit: int = Query(10, ge=1, le=50)
) -> Dict[str, Any]:
    """
    Search content in Neon database.

    Searches countries, articles, jobs, and deals.
    Emits content_suggestion events for real-time display.
    """
    if not CONTENT_SERVICE_ENABLED:
        return {"results": [], "query": query, "error": "Content service not available"}

    try:
        from services.event_publisher import emit_content_suggestion, emit_content_no_results

        results = await content_service.search(query, content_type=content_type, limit=limit)

        if not results:
            await emit_content_no_results(user_id, query)
            return {"results": [], "query": query, "no_results": True}

        # Emit each result as an SSE event
        for result in results:
            await emit_content_suggestion(
                user_id=user_id,
                content_type=result.get("type", "article"),
                content_id=result.get("id"),
                title=result.get("title"),
                slug=result.get("slug"),
                excerpt=result.get("excerpt"),
                country=result.get("country"),
                country_flag=result.get("country_flag"),
                match_reason=f"Matches '{query}'",
                search_context=query,
                featured_image=result.get("featured_image"),
                hero_image=result.get("hero_image"),
            )

        return {"results": results, "query": query, "count": len(results)}

    except Exception as e:
        logger.error("search_content_error", query=query, error=str(e))
        return {"results": [], "query": query, "error": str(e)}


# ============================================================================
# TRANSCRIPT
# ============================================================================

@router.get("/transcript/recent")
async def get_recent_transcript(
    user_id: str = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200)
) -> Dict[str, Any]:
    """
    Get recent transcript messages for current session.
    """
    try:
        from services.user_profile_service import user_profile_service

        # Get most recent session
        sessions = await user_profile_service.get_user_sessions(user_id, limit=1)

        if not sessions:
            return {"messages": [], "session_id": None}

        session = sessions[0]
        session_id = session.get("session_id")

        # Get messages from session
        messages = session.get("messages", [])

        return {
            "messages": messages[-limit:],
            "session_id": session_id,
            "total": len(messages)
        }

    except Exception as e:
        logger.error("get_transcript_error", user_id=user_id, error=str(e))
        return {"messages": [], "error": str(e)}


# ============================================================================
# SUMMARY
# ============================================================================

@router.get("/summaries/recent")
async def get_recent_summaries(
    user_id: str = Depends(get_current_user),
    limit: int = Query(5, ge=1, le=20)
) -> Dict[str, Any]:
    """
    Get recent conversation summaries.
    """
    try:
        from services.user_profile_service import user_profile_service

        sessions = await user_profile_service.get_user_sessions(user_id, limit=limit)

        summaries = []
        for session in sessions:
            if session.get("summary"):
                summaries.append({
                    "id": session.get("session_id"),
                    "date": session.get("created_at"),
                    "summary": session.get("summary"),
                    "key_topics": session.get("key_topics", []),
                    "facts_extracted": session.get("facts_extracted", 0),
                    "sentiment": session.get("sentiment", "neutral")
                })

        return {"summaries": summaries}

    except Exception as e:
        logger.error("get_summaries_error", user_id=user_id, error=str(e))
        return {"summaries": [], "error": str(e)}


@router.post("/summary/generate")
async def generate_summary(
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate a summary of the current/recent conversation.
    """
    try:
        from services.user_profile_service import user_profile_service
        from services.event_publisher import emit_summary_update

        # Get recent session
        sessions = await user_profile_service.get_user_sessions(user_id, limit=1)

        if not sessions:
            return {"summary": "No recent conversations to summarize.", "key_topics": []}

        session = sessions[0]
        messages = session.get("messages", [])

        if not messages:
            return {"summary": "No messages in current session.", "key_topics": []}

        # Build conversation text
        conversation = "\n".join([
            f"{m.get('role', 'unknown')}: {m.get('content', '')}"
            for m in messages
        ])

        # Use LLM to generate summary
        # For now, return a placeholder - in production, call your LLM service
        summary = f"Conversation with {len(messages)} messages about relocation planning."
        key_topics = ["relocation", "planning"]

        # Emit update
        await emit_summary_update(user_id, summary, key_topics)

        return {
            "summary": summary,
            "key_topics": key_topics,
            "message_count": len(messages)
        }

    except Exception as e:
        logger.error("generate_summary_error", user_id=user_id, error=str(e))
        return {"summary": "", "key_topics": [], "error": str(e)}


# ============================================================================
# VERIFIED PROFILE (Human-controlled)
# ============================================================================

@router.get("/profile/verified")
async def get_verified_profile(
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get only human-verified profile facts.

    These are facts the user has explicitly confirmed.
    """
    try:
        from services.user_profile_service import user_profile_service

        facts = await user_profile_service.get_facts_by_stack_id(user_id, active_only=True)

        # Filter to only verified facts
        verified = [f for f in facts if f.get("is_user_verified")]

        return {"facts": verified, "count": len(verified)}

    except Exception as e:
        logger.error("get_verified_profile_error", user_id=user_id, error=str(e))
        return {"facts": [], "error": str(e)}


@router.post("/profile/verify")
async def verify_profile_fact(
    suggestion_id: str = Query(...),
    fact_type: str = Query(...),
    value: str = Query(...),
    action: str = Query(..., description="accept or reject"),
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Accept or reject an AI-suggested profile change.

    Human-in-the-loop: user must explicitly verify before fact is added to profile.
    """
    try:
        from services.user_profile_service import user_profile_service
        from services.event_publisher import publish

        if action == "accept":
            # Get or create profile
            profile_id = await user_profile_service.get_or_create_profile(user_id)

            # Store as verified fact
            fact_id = await user_profile_service.store_fact(
                user_profile_id=profile_id,
                fact_type=fact_type,
                fact_value={"value": value},
                source="user_verified",
                confidence=1.0,
                is_verified=True
            )

            # Emit verified event
            await publish(user_id, "profile_verified", {
                "suggestion_id": suggestion_id,
                "fact_type": fact_type,
                "value": value,
                "fact_id": fact_id
            })

            return {"success": True, "action": "accepted", "fact_id": fact_id}
        else:
            # Just acknowledge rejection
            return {"success": True, "action": "rejected"}

    except Exception as e:
        logger.error("verify_profile_error", user_id=user_id, error=str(e))
        return {"success": False, "error": str(e)}


# ============================================================================
# HEALTH
# ============================================================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Check dashboard service health."""
    return {
        "service": "dashboard",
        "event_publisher": EVENT_PUBLISHER_ENABLED,
        "content_service": CONTENT_SERVICE_ENABLED
    }
