"""
SuperMemory Integration Service

Long-term conversational memory for personalized user experiences.
Complements ZEP knowledge graph with user-specific context.

Architecture:
- ZEP: Structured knowledge (countries, articles, facts, relationships)
- SuperMemory: User memory (preferences, history, personalization)
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime

import structlog

logger = structlog.get_logger()

SUPERMEMORY_API_KEY = os.getenv("SUPERMEMORY_API_KEY")


class SuperMemoryClient:
    """
    SuperMemory client for user-specific long-term memory.

    Use cases:
    - User preferences (budget, family size, work type)
    - Stated destinations and origins
    - Conversation history summaries
    - Personalization context
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or SUPERMEMORY_API_KEY
        self.enabled = bool(self.api_key)
        self.client = None

        if self.enabled:
            try:
                from supermemory import Supermemory
                self.client = Supermemory(api_key=self.api_key)
                logger.info("supermemory_client_initialized")
            except ImportError as e:
                logger.warning("supermemory_package_not_installed", error=str(e))
                self.enabled = False
            except Exception as e:
                logger.error("supermemory_init_error", error=str(e))
                self.enabled = False
        else:
            logger.warning("supermemory_not_configured", reason="No API key")

    async def add_memory(
        self,
        user_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_type: str = "conversation"
    ) -> Optional[Dict[str, Any]]:
        """
        Store a memory for a user using the memories API.

        Args:
            user_id: Unique user identifier
            content: The memory content (text, facts, preferences)
            metadata: Additional context (source, timestamp, type)
            memory_type: Category (conversation, preference, fact)

        Returns:
            Memory ID and status, or None on failure
        """
        if not self.enabled or not self.client:
            return None

        try:
            # Build metadata with user context (must be flat - no nested objects)
            full_metadata = {
                "user_id": user_id,
                "memory_type": memory_type,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "relocation_quest_voice"
            }
            # Flatten any additional metadata (SuperMemory only accepts primitives)
            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        full_metadata[key] = value
                    elif isinstance(value, dict):
                        # Flatten nested dicts with prefixed keys
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, (str, int, float, bool)):
                                full_metadata[f"{key}_{sub_key}"] = sub_value

            # Use the SDK's memories.add method
            result = self.client.memories.add(
                content=content,
                container_tag=f"user-{user_id}",
                metadata=full_metadata
            )

            logger.info("supermemory_add_success",
                       user_id=user_id,
                       memory_type=memory_type,
                       memory_id=getattr(result, 'id', None))

            return {
                "id": getattr(result, 'id', None),
                "status": "success"
            }

        except Exception as e:
            logger.error("supermemory_add_error",
                        user_id=user_id,
                        error=str(e))
            return None

    async def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search user's memories for relevant context.

        Args:
            user_id: User to search memories for
            query: Search query
            limit: Max results to return

        Returns:
            List of relevant memories with content and scores
        """
        if not self.enabled or not self.client:
            return []

        try:
            # Use the SDK's search.memories method with user container filter
            result = self.client.search.memories(
                q=query,
                container_tag=f"user-{user_id}",
                limit=limit
            )

            memories = []
            if hasattr(result, 'results'):
                for mem in result.results:
                    # SuperMemory uses 'memory' field for content, 'similarity' for score
                    content = getattr(mem, 'memory', '') or getattr(mem, 'content', '') or ''
                    memories.append({
                        "content": content,
                        "score": getattr(mem, 'similarity', 0.0) or getattr(mem, 'score', 0.0),
                        "metadata": getattr(mem, 'metadata', {}),
                        "id": getattr(mem, 'id', None)
                    })

            logger.info("supermemory_search_success",
                       user_id=user_id,
                       query=query[:50],
                       results=len(memories))

            return memories

        except Exception as e:
            logger.error("supermemory_search_error",
                        user_id=user_id,
                        error=str(e))
            return []

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Build a user profile from their stored memories.

        Searches for preference-type memories and compiles
        a structured profile for personalization.

        Args:
            user_id: User to get profile for

        Returns:
            User profile dict with preferences and context
        """
        if not self.enabled or not self.client:
            return {"user_id": user_id, "has_history": False}

        try:
            # Search for preference memories
            preferences = await self.search_memories(
                user_id=user_id,
                query="user preferences destination origin family work budget relocation",
                limit=10
            )

            profile = {
                "user_id": user_id,
                "has_history": len(preferences) > 0,
                "memories": preferences,
                "summary": self._summarize_preferences(preferences)
            }

            logger.info("supermemory_profile_built",
                       user_id=user_id,
                       memory_count=len(preferences))

            return profile

        except Exception as e:
            logger.error("supermemory_profile_error",
                        user_id=user_id,
                        error=str(e))
            return {"user_id": user_id, "has_history": False}

    def _summarize_preferences(self, memories: List[Dict]) -> str:
        """Extract key preferences from memories into a summary."""
        if not memories:
            return ""

        # Extract content from memories
        contents = []
        for mem in memories[:5]:  # Top 5 most relevant
            content = mem.get("content", "")
            if content and len(content) > 10:
                contents.append(content[:200])

        if not contents:
            return ""

        return "Previous context:\n" + "\n".join(f"- {c}" for c in contents)


class UserMemoryManager:
    """
    High-level manager for user memory operations.

    Extracts and stores relevant information from conversations,
    and retrieves personalized context for responses.
    """

    def __init__(self, client: Optional[SuperMemoryClient] = None):
        self.client = client or SuperMemoryClient()

    async def store_conversation_turn(
        self,
        user_id: str,
        user_message: str,
        assistant_response: str,
        extracted_info: Optional[Dict[str, Any]] = None
    ):
        """
        Store a conversation turn with extracted user information.

        Args:
            user_id: User identifier
            user_message: What the user said
            assistant_response: What we responded
            extracted_info: Extracted preferences, destinations, etc.
        """
        if not self.client.enabled:
            return

        # Store the conversation exchange
        conversation_content = f"User asked: {user_message}\nAssistant responded about relocation topics."

        await self.client.add_memory(
            user_id=user_id,
            content=conversation_content,
            memory_type="conversation",
            metadata={
                "turn_type": "exchange",
                "extracted": extracted_info or {}
            }
        )

        # If we extracted specific preferences, store them separately for better retrieval
        if extracted_info:
            if extracted_info.get("destination"):
                await self.client.add_memory(
                    user_id=user_id,
                    content=f"User is interested in relocating to {extracted_info['destination']}. This is their target destination country.",
                    memory_type="preference",
                    metadata={"preference_type": "destination", "value": extracted_info['destination']}
                )

            if extracted_info.get("origin"):
                await self.client.add_memory(
                    user_id=user_id,
                    content=f"User is currently based in {extracted_info['origin']}. This is their origin location.",
                    memory_type="preference",
                    metadata={"preference_type": "origin", "value": extracted_info['origin']}
                )

            if extracted_info.get("family"):
                await self.client.add_memory(
                    user_id=user_id,
                    content=f"User's family situation: {extracted_info['family']}. Important for relocation planning.",
                    memory_type="preference",
                    metadata={"preference_type": "family", "value": extracted_info['family']}
                )

            if extracted_info.get("work_type"):
                await self.client.add_memory(
                    user_id=user_id,
                    content=f"User's work type: {extracted_info['work_type']}. Affects visa and relocation options.",
                    memory_type="preference",
                    metadata={"preference_type": "work", "value": extracted_info['work_type']}
                )

    async def get_personalized_context(
        self,
        user_id: str,
        current_query: str
    ) -> str:
        """
        Get personalized context for the current query.

        Combines user profile with query-relevant memories.

        Args:
            user_id: User identifier
            current_query: The current question being asked

        Returns:
            Formatted context string for LLM prompt
        """
        if not self.client.enabled:
            return ""

        try:
            # Get user profile
            profile = await self.client.get_user_profile(user_id)

            # Search for query-relevant memories
            relevant_memories = await self.client.search_memories(
                user_id=user_id,
                query=current_query,
                limit=3
            )

            context_parts = []

            # Add profile summary
            if profile.get("summary"):
                context_parts.append(profile["summary"])

            # Add relevant past conversations
            if relevant_memories:
                past_context = []
                for mem in relevant_memories:
                    content = mem.get("content", "")
                    if content and len(content) > 20:
                        past_context.append(f"- {content[:150]}")

                if past_context:
                    context_parts.append("Relevant past interactions:\n" + "\n".join(past_context))

            if context_parts:
                return "\n\n".join(context_parts)

            return ""

        except Exception as e:
            logger.error("personalized_context_error",
                        user_id=user_id,
                        error=str(e))
            return ""


# Singleton instances
supermemory_client = SuperMemoryClient()
user_memory_manager = UserMemoryManager(supermemory_client)
