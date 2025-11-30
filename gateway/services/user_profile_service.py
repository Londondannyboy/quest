"""
User Profile Service

Database operations for user profile facts and voice sessions.
Uses psycopg3 async for Neon PostgreSQL connections.
"""

import os
import json
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import structlog

logger = structlog.get_logger()

DATABASE_URL = os.getenv("DATABASE_URL")

# Import models
try:
    import sys
    gateway_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if gateway_dir not in sys.path:
        sys.path.insert(0, gateway_dir)
    from models.user_profile import (
        FactType, FactSource, SessionStatus,
        UserProfileFact, UserProfileFactCreate, UserProfileFactUpdate,
        VoiceSession, VoiceSessionCreate, UserProfileSnapshot,
        EXTRACTION_PATTERNS
    )
except ImportError as e:
    logger.warning("user_profile_models_import_failed", error=str(e))
    FactType = None
    EXTRACTION_PATTERNS = {}


class UserProfileService:
    """
    Service for managing user profile facts and voice sessions.

    Handles:
    - User profile creation/retrieval
    - Fact storage and updates
    - Voice session management
    - Profile snapshot generation
    """

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or DATABASE_URL
        self.enabled = bool(self.database_url)
        if self.enabled:
            logger.info("user_profile_service_initialized")
        else:
            logger.warning("user_profile_service_disabled", reason="No DATABASE_URL")

    # ========================================================================
    # USER PROFILE OPERATIONS
    # ========================================================================

    async def get_or_create_profile(self, stack_user_id: str, email: Optional[str] = None) -> Optional[UUID]:
        """
        Get existing user profile or create new one.

        Args:
            stack_user_id: Stack Auth user ID
            email: Optional email for profile

        Returns:
            UUID of user profile, or None on failure
        """
        if not self.enabled:
            return None

        try:
            import psycopg

            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    # Try to get existing profile
                    await cur.execute("""
                        SELECT id FROM user_profiles WHERE user_id = %s
                    """, (stack_user_id,))

                    row = await cur.fetchone()
                    if row:
                        logger.info("profile_found", stack_user_id=stack_user_id)
                        return row[0]

                    # Create new profile
                    await cur.execute("""
                        INSERT INTO user_profiles (user_id, email, created_at, updated_at)
                        VALUES (%s, %s, NOW(), NOW())
                        RETURNING id
                    """, (stack_user_id, email))

                    await conn.commit()
                    row = await cur.fetchone()

                    if row:
                        logger.info("profile_created", stack_user_id=stack_user_id, profile_id=str(row[0]))
                        return row[0]

                    return None

        except Exception as e:
            logger.error("get_or_create_profile_error", stack_user_id=stack_user_id, error=str(e))
            return None

    async def get_profile_by_stack_id(self, stack_user_id: str) -> Optional[Dict[str, Any]]:
        """Get full profile data for a user."""
        if not self.enabled:
            return None

        try:
            import psycopg

            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        SELECT
                            id, user_id, email,
                            current_country, current_city, nationality,
                            destination_countries, has_children, number_of_children,
                            employment_status, remote_work, industry, job_title,
                            income_range, budget_monthly, timeline,
                            created_at, updated_at
                        FROM user_profiles
                        WHERE user_id = %s
                    """, (stack_user_id,))

                    row = await cur.fetchone()
                    if not row:
                        return None

                    return {
                        "id": str(row[0]),
                        "user_id": row[1],
                        "email": row[2],
                        "current_country": row[3],
                        "current_city": row[4],
                        "nationality": row[5],
                        "destination_countries": row[6] or [],
                        "has_children": row[7],
                        "number_of_children": row[8],
                        "employment_status": row[9],
                        "remote_work": row[10],
                        "industry": row[11],
                        "job_title": row[12],
                        "income_range": row[13],
                        "budget_monthly": row[14],
                        "timeline": row[15],
                        "created_at": row[16].isoformat() if row[16] else None,
                        "updated_at": row[17].isoformat() if row[17] else None
                    }

        except Exception as e:
            logger.error("get_profile_error", stack_user_id=stack_user_id, error=str(e))
            return None

    # ========================================================================
    # FACT OPERATIONS
    # ========================================================================

    async def store_fact(
        self,
        user_profile_id: UUID,
        fact_type: str,
        fact_value: Dict[str, Any],
        source: str = "voice",
        confidence: float = 0.5,
        session_id: Optional[str] = None,
        extracted_from: Optional[str] = None
    ) -> Optional[int]:
        """
        Store a new fact for a user.

        Args:
            user_profile_id: UUID of user profile
            fact_type: Type of fact (destination, origin, etc.)
            fact_value: JSONB value containing fact details
            source: How fact was captured (voice, llm_refined, user_edit)
            confidence: Confidence score 0-1
            session_id: Voice session that extracted this
            extracted_from: Original message text

        Returns:
            ID of created fact, or None on failure
        """
        if not self.enabled:
            return None

        try:
            import psycopg

            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        INSERT INTO user_profile_facts (
                            user_profile_id, fact_type, fact_value,
                            source, confidence, session_id, extracted_from_message,
                            created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        RETURNING id
                    """, (
                        str(user_profile_id), fact_type, json.dumps(fact_value),
                        source, confidence, session_id, extracted_from
                    ))

                    await conn.commit()
                    row = await cur.fetchone()

                    if row:
                        logger.info("fact_stored",
                                   user_profile_id=str(user_profile_id),
                                   fact_type=fact_type,
                                   fact_id=row[0])
                        return row[0]

                    return None

        except Exception as e:
            logger.error("store_fact_error",
                        user_profile_id=str(user_profile_id),
                        fact_type=fact_type,
                        error=str(e))
            return None

    async def get_facts(
        self,
        user_profile_id: UUID,
        fact_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get facts for a user profile.

        Args:
            user_profile_id: UUID of user profile
            fact_type: Optional filter by type
            active_only: Only return active facts

        Returns:
            List of fact dictionaries
        """
        if not self.enabled:
            return []

        try:
            import psycopg

            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    query = """
                        SELECT
                            id, fact_type, fact_value, source, confidence,
                            session_id, extracted_from_message,
                            is_user_verified, is_active,
                            created_at, updated_at, verified_at
                        FROM user_profile_facts
                        WHERE user_profile_id = %s
                    """
                    params = [str(user_profile_id)]

                    if active_only:
                        query += " AND is_active = TRUE"

                    if fact_type:
                        query += " AND fact_type = %s"
                        params.append(fact_type)

                    query += " ORDER BY created_at DESC"

                    await cur.execute(query, params)
                    rows = await cur.fetchall()

                    facts = []
                    for row in rows:
                        facts.append({
                            "id": row[0],
                            "fact_type": row[1],
                            "fact_value": row[2] if isinstance(row[2], dict) else json.loads(row[2]) if row[2] else {},
                            "source": row[3],
                            "confidence": float(row[4]) if row[4] else 0.5,
                            "session_id": row[5],
                            "extracted_from_message": row[6],
                            "is_user_verified": row[7],
                            "is_active": row[8],
                            "created_at": row[9].isoformat() if row[9] else None,
                            "updated_at": row[10].isoformat() if row[10] else None,
                            "verified_at": row[11].isoformat() if row[11] else None
                        })

                    return facts

        except Exception as e:
            logger.error("get_facts_error",
                        user_profile_id=str(user_profile_id),
                        error=str(e))
            return []

    async def get_facts_by_stack_id(
        self,
        stack_user_id: str,
        fact_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get facts using Stack Auth user ID."""
        if not self.enabled:
            return []

        try:
            import psycopg

            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    # First get profile ID
                    await cur.execute("""
                        SELECT id FROM user_profiles WHERE user_id = %s
                    """, (stack_user_id,))

                    row = await cur.fetchone()
                    if not row:
                        return []

                    profile_id = row[0]
                    return await self.get_facts(profile_id, fact_type, active_only)

        except Exception as e:
            logger.error("get_facts_by_stack_id_error",
                        stack_user_id=stack_user_id,
                        error=str(e))
            return []

    async def update_fact(
        self,
        fact_id: int,
        fact_value: Optional[Dict[str, Any]] = None,
        is_user_verified: Optional[bool] = None
    ) -> bool:
        """
        Update a fact (typically user edit).

        Args:
            fact_id: ID of fact to update
            fact_value: New value (optional)
            is_user_verified: Mark as verified (optional)

        Returns:
            True on success
        """
        if not self.enabled:
            return False

        try:
            import psycopg

            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    updates = ["updated_at = NOW()"]
                    params = []

                    if fact_value is not None:
                        updates.append("fact_value = %s")
                        updates.append("source = 'user_edit'")
                        params.append(json.dumps(fact_value))

                    if is_user_verified is not None:
                        updates.append("is_user_verified = %s")
                        if is_user_verified:
                            updates.append("verified_at = NOW()")
                        params.append(is_user_verified)

                    params.append(fact_id)

                    await cur.execute(f"""
                        UPDATE user_profile_facts
                        SET {', '.join(updates)}
                        WHERE id = %s
                    """, params)

                    await conn.commit()

                    logger.info("fact_updated", fact_id=fact_id)
                    return True

        except Exception as e:
            logger.error("update_fact_error", fact_id=fact_id, error=str(e))
            return False

    async def delete_fact(self, fact_id: int, soft: bool = True) -> bool:
        """
        Delete a fact (soft delete by default).

        Args:
            fact_id: ID of fact to delete
            soft: Soft delete (set is_active=false) vs hard delete

        Returns:
            True on success
        """
        if not self.enabled:
            return False

        try:
            import psycopg

            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    if soft:
                        await cur.execute("""
                            UPDATE user_profile_facts
                            SET is_active = FALSE, updated_at = NOW()
                            WHERE id = %s
                        """, (fact_id,))
                    else:
                        await cur.execute("""
                            DELETE FROM user_profile_facts WHERE id = %s
                        """, (fact_id,))

                    await conn.commit()

                    logger.info("fact_deleted", fact_id=fact_id, soft=soft)
                    return True

        except Exception as e:
            logger.error("delete_fact_error", fact_id=fact_id, error=str(e))
            return False

    # ========================================================================
    # VOICE SESSION OPERATIONS
    # ========================================================================

    async def create_session(
        self,
        session_id: str,
        stack_user_id: Optional[str] = None
    ) -> Optional[int]:
        """Create a new voice session."""
        if not self.enabled:
            return None

        try:
            import psycopg

            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    # Get profile ID if user is logged in
                    profile_id = None
                    if stack_user_id:
                        await cur.execute("""
                            SELECT id FROM user_profiles WHERE user_id = %s
                        """, (stack_user_id,))
                        row = await cur.fetchone()
                        if row:
                            profile_id = row[0]

                    await cur.execute("""
                        INSERT INTO voice_sessions (
                            session_id, user_profile_id, stack_user_id,
                            status, messages, started_at, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, 'active', '[]'::jsonb, NOW(), NOW(), NOW())
                        RETURNING id
                    """, (session_id, str(profile_id) if profile_id else None, stack_user_id))

                    await conn.commit()
                    row = await cur.fetchone()

                    if row:
                        logger.info("session_created",
                                   session_id=session_id,
                                   db_id=row[0])
                        return row[0]

                    return None

        except Exception as e:
            logger.error("create_session_error", session_id=session_id, error=str(e))
            return None

    async def add_message_to_session(
        self,
        session_id: str,
        role: str,
        content: str,
        extracted_facts: Optional[List[Dict]] = None
    ) -> bool:
        """Add a message to a voice session."""
        if not self.enabled:
            return False

        try:
            import psycopg

            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "extracted_facts": extracted_facts or []
            }

            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        UPDATE voice_sessions
                        SET
                            messages = messages || %s::jsonb,
                            message_count = message_count + 1,
                            updated_at = NOW()
                        WHERE session_id = %s
                    """, (json.dumps([message]), session_id))

                    await conn.commit()
                    return True

        except Exception as e:
            logger.error("add_message_error", session_id=session_id, error=str(e))
            return False

    async def end_session(
        self,
        session_id: str,
        llm_refined_facts: Optional[Dict] = None
    ) -> bool:
        """End a voice session and store LLM-refined facts."""
        if not self.enabled:
            return False

        try:
            import psycopg

            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        UPDATE voice_sessions
                        SET
                            status = 'ended',
                            ended_at = NOW(),
                            llm_refined_facts = %s,
                            duration_seconds = EXTRACT(EPOCH FROM (NOW() - started_at))::integer,
                            updated_at = NOW()
                        WHERE session_id = %s
                    """, (json.dumps(llm_refined_facts or {}), session_id))

                    await conn.commit()

                    logger.info("session_ended", session_id=session_id)
                    return True

        except Exception as e:
            logger.error("end_session_error", session_id=session_id, error=str(e))
            return False

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a voice session by ID."""
        if not self.enabled:
            return None

        try:
            import psycopg

            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        SELECT
                            id, session_id, user_profile_id, stack_user_id,
                            status, messages, quick_extraction, llm_refined_facts,
                            message_count, duration_seconds,
                            started_at, ended_at, created_at, updated_at
                        FROM voice_sessions
                        WHERE session_id = %s
                    """, (session_id,))

                    row = await cur.fetchone()
                    if not row:
                        return None

                    return {
                        "id": row[0],
                        "session_id": row[1],
                        "user_profile_id": str(row[2]) if row[2] else None,
                        "stack_user_id": row[3],
                        "status": row[4],
                        "messages": row[5] if isinstance(row[5], list) else json.loads(row[5]) if row[5] else [],
                        "quick_extraction": row[6] if isinstance(row[6], dict) else json.loads(row[6]) if row[6] else {},
                        "llm_refined_facts": row[7] if isinstance(row[7], dict) else json.loads(row[7]) if row[7] else {},
                        "message_count": row[8],
                        "duration_seconds": row[9],
                        "started_at": row[10].isoformat() if row[10] else None,
                        "ended_at": row[11].isoformat() if row[11] else None,
                        "created_at": row[12].isoformat() if row[12] else None,
                        "updated_at": row[13].isoformat() if row[13] else None
                    }

        except Exception as e:
            logger.error("get_session_error", session_id=session_id, error=str(e))
            return None

    async def get_user_sessions(
        self,
        stack_user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent sessions for a user."""
        if not self.enabled:
            return []

        try:
            import psycopg

            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        SELECT
                            session_id, status, message_count, duration_seconds,
                            started_at, ended_at
                        FROM voice_sessions
                        WHERE stack_user_id = %s
                        ORDER BY started_at DESC
                        LIMIT %s
                    """, (stack_user_id, limit))

                    rows = await cur.fetchall()

                    sessions = []
                    for row in rows:
                        sessions.append({
                            "session_id": row[0],
                            "status": row[1],
                            "message_count": row[2],
                            "duration_seconds": row[3],
                            "started_at": row[4].isoformat() if row[4] else None,
                            "ended_at": row[5].isoformat() if row[5] else None
                        })

                    return sessions

        except Exception as e:
            logger.error("get_user_sessions_error", stack_user_id=stack_user_id, error=str(e))
            return []

    # ========================================================================
    # PROFILE SNAPSHOT (DENORMALIZED FOR QUICK ACCESS)
    # ========================================================================

    async def build_profile_snapshot(self, stack_user_id: str) -> Dict[str, Any]:
        """
        Build a snapshot of active facts for quick loading.

        Returns aggregated facts grouped by type for use in prompts.
        """
        facts = await self.get_facts_by_stack_id(stack_user_id, active_only=True)

        snapshot = {
            "destinations": [],
            "origin": None,
            "family_status": None,
            "children": None,
            "profession": None,
            "employer": None,
            "work_type": None,
            "budget": None,
            "timeline": None,
            "total_facts": len(facts)
        }

        for fact in facts:
            fact_type = fact.get("fact_type")
            value = fact.get("fact_value", {})

            if fact_type == "destination":
                dest = value.get("country") or value.get("value")
                if dest and dest not in snapshot["destinations"]:
                    snapshot["destinations"].append(dest)
            elif fact_type == "origin":
                snapshot["origin"] = value.get("country") or value.get("value")
            elif fact_type == "family":
                snapshot["family_status"] = value.get("status") or value.get("value")
            elif fact_type == "children":
                snapshot["children"] = value.get("count") or value.get("value")
            elif fact_type == "profession":
                snapshot["profession"] = value.get("title") or value.get("value")
            elif fact_type == "employer":
                snapshot["employer"] = value.get("name") or value.get("value")
            elif fact_type == "work_type":
                snapshot["work_type"] = value.get("type") or value.get("value")
            elif fact_type == "budget":
                snapshot["budget"] = value.get("monthly") or value.get("range") or value.get("value")
            elif fact_type == "timeline":
                snapshot["timeline"] = value.get("target") or value.get("value")

        return snapshot

    async def get_profile_context_for_prompt(self, stack_user_id: str) -> str:
        """
        Get profile context formatted for LLM prompts.

        Returns a natural language summary of what we know about the user.
        """
        snapshot = await self.build_profile_snapshot(stack_user_id)

        if snapshot["total_facts"] == 0:
            return ""

        parts = []

        if snapshot["origin"]:
            parts.append(f"Currently based in {snapshot['origin']}")

        if snapshot["destinations"]:
            if len(snapshot["destinations"]) == 1:
                parts.append(f"interested in relocating to {snapshot['destinations'][0]}")
            else:
                parts.append(f"considering destinations: {', '.join(snapshot['destinations'])}")

        if snapshot["family_status"]:
            parts.append(f"family status: {snapshot['family_status']}")

        if snapshot["children"]:
            parts.append(f"has {snapshot['children']} children")

        if snapshot["profession"]:
            parts.append(f"works as {snapshot['profession']}")

        if snapshot["employer"]:
            parts.append(f"at {snapshot['employer']}")

        if snapshot["work_type"]:
            parts.append(f"({snapshot['work_type']})")

        if snapshot["budget"]:
            parts.append(f"budget: {snapshot['budget']}")

        if snapshot["timeline"]:
            parts.append(f"timeline: {snapshot['timeline']}")

        if not parts:
            return ""

        return "User profile: " + "; ".join(parts) + "."

    # ========================================================================
    # QUICK EXTRACTION (REGEX-BASED)
    # ========================================================================

    def extract_facts_from_message(self, message: str) -> List[Dict[str, Any]]:
        """
        Quick regex-based extraction of facts from a message.

        Args:
            message: User message text

        Returns:
            List of extracted facts with type and value
        """
        extracted = []

        if not EXTRACTION_PATTERNS:
            return extracted

        for fact_type, patterns in EXTRACTION_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                for match in matches:
                    value = match.strip() if isinstance(match, str) else match[0].strip()
                    if value and len(value) > 1:
                        extracted.append({
                            "fact_type": fact_type.value if hasattr(fact_type, 'value') else str(fact_type),
                            "fact_value": {"value": value},
                            "confidence": 0.7,
                            "source": "voice"
                        })

        # Deduplicate by fact_type + value
        seen = set()
        unique = []
        for fact in extracted:
            key = (fact["fact_type"], fact["fact_value"]["value"].lower())
            if key not in seen:
                seen.add(key)
                unique.append(fact)

        return unique


# Singleton instance
user_profile_service = UserProfileService()
