"""
Event Publisher Service

Publishes real-time events to SSE clients for dashboard updates.
Uses asyncio queues for in-process pub/sub (upgrade to Redis for multi-instance).
"""

import asyncio
import json
from typing import Dict, Set, Any, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()

# Store of active SSE connections per user
# user_id -> set of asyncio.Queue
_user_queues: Dict[str, Set[asyncio.Queue]] = {}
_lock = asyncio.Lock()


async def subscribe(user_id: str) -> asyncio.Queue:
    """
    Subscribe to events for a user.
    Returns a queue that will receive events.
    """
    async with _lock:
        if user_id not in _user_queues:
            _user_queues[user_id] = set()

        queue = asyncio.Queue()
        _user_queues[user_id].add(queue)
        logger.info("sse_subscribed", user_id=user_id, total_connections=len(_user_queues[user_id]))
        return queue


async def unsubscribe(user_id: str, queue: asyncio.Queue):
    """
    Unsubscribe from events.
    """
    async with _lock:
        if user_id in _user_queues:
            _user_queues[user_id].discard(queue)
            if not _user_queues[user_id]:
                del _user_queues[user_id]
            logger.info("sse_unsubscribed", user_id=user_id)


async def publish(user_id: str, event_type: str, data: Dict[str, Any]):
    """
    Publish an event to all subscribers for a user.

    Args:
        user_id: Target user
        event_type: Event name (e.g., 'fact_extracted', 'content_suggestion')
        data: Event data dict
    """
    async with _lock:
        queues = _user_queues.get(user_id, set())

    if not queues:
        logger.debug("no_subscribers", user_id=user_id, event_type=event_type)
        return

    event = {
        "event": event_type,
        "data": json.dumps(data),
        "id": datetime.utcnow().isoformat(),
    }

    for queue in queues:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("queue_full", user_id=user_id, event_type=event_type)

    logger.info("event_published", user_id=user_id, event_type=event_type, subscribers=len(queues))


# ============================================================================
# CONVENIENCE FUNCTIONS FOR SPECIFIC EVENT TYPES
# ============================================================================

async def emit_fact_extracted(user_id: str, fact: Dict[str, Any]):
    """Emit when a new fact is extracted from conversation."""
    await publish(user_id, "fact_extracted", {
        "id": fact.get("id"),
        "fact_type": fact.get("fact_type"),
        "fact_value": fact.get("fact_value"),
        "confidence": fact.get("confidence", 0.8),
        "source": fact.get("source", "voice"),
        "timestamp": datetime.utcnow().isoformat(),
    })


async def emit_fact_updated(user_id: str, fact_id: int, old_value: Any, new_value: Any, fact_type: str):
    """Emit when an existing fact is updated."""
    await publish(user_id, "fact_updated", {
        "id": fact_id,
        "fact_type": fact_type,
        "old_value": old_value,
        "new_value": new_value,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def emit_profile_suggestion(
    user_id: str,
    suggestion_id: str,
    fact_type: str,
    suggested_value: str,
    reasoning: str,
    current_value: Optional[str] = None
):
    """Emit when AI suggests a profile change (human-in-the-loop)."""
    await publish(user_id, "profile_suggestion", {
        "id": suggestion_id,
        "fact_type": fact_type,
        "suggested_value": suggested_value,
        "current_value": current_value,
        "reasoning": reasoning,
        "requires_confirmation": True,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def emit_content_suggestion(
    user_id: str,
    content_type: str,
    content_id: int,
    title: str,
    slug: str,
    excerpt: Optional[str] = None,
    country: Optional[str] = None,
    country_flag: Optional[str] = None,
    match_reason: Optional[str] = None,
    search_context: Optional[str] = None
):
    """Emit when relevant content is found from Neon."""
    await publish(user_id, "content_suggestion", {
        "type": content_type,
        "id": content_id,
        "title": title,
        "slug": slug,
        "excerpt": excerpt,
        "country": country,
        "country_flag": country_flag,
        "match_reason": match_reason,
        "search_context": search_context,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def emit_content_no_results(user_id: str, query: str):
    """Emit when no content is found for a query."""
    await publish(user_id, "content_no_results", {
        "query": query,
        "message": f"No articles found for '{query}'",
        "timestamp": datetime.utcnow().isoformat(),
    })


async def emit_transcript_message(
    user_id: str,
    role: str,
    content: str,
    source: str = "voice",
    message_id: Optional[str] = None,
    emotions: Optional[Dict[str, float]] = None
):
    """Emit a transcript message for live display."""
    await publish(user_id, "transcript_message", {
        "id": message_id or datetime.utcnow().isoformat(),
        "role": role,
        "content": content,
        "source": source,
        "emotions": emotions,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def emit_tool_start(user_id: str, tool_id: str, tool_name: str, tool_input: Optional[Dict] = None):
    """Emit when a tool/function starts executing."""
    await publish(user_id, "tool_start", {
        "id": tool_id,
        "name": tool_name,
        "input": tool_input,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def emit_tool_end(user_id: str, tool_id: str, tool_name: str, result: Optional[str] = None):
    """Emit when a tool/function completes."""
    await publish(user_id, "tool_end", {
        "id": tool_id,
        "name": tool_name,
        "result": result,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def emit_summary_update(user_id: str, summary: str, key_topics: Optional[list] = None):
    """Emit an updated conversation summary."""
    await publish(user_id, "summary_update", {
        "summary": summary,
        "key_topics": key_topics or [],
        "timestamp": datetime.utcnow().isoformat(),
    })


async def emit_session_start(user_id: str, session_id: str, source: str = "voice"):
    """Emit when a new session starts."""
    await publish(user_id, "session_start", {
        "session_id": session_id,
        "source": source,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def emit_session_end(user_id: str, session_id: str):
    """Emit when a session ends."""
    await publish(user_id, "session_end", {
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
    })
