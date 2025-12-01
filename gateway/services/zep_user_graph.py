"""
ZEP User Graph Service

Manages user profile facts in ZEP knowledge graph for semantic querying.
Each user gets their own subgraph within the "users" graph.
"""

import os
import json
from typing import Optional, List, Dict, Any
import structlog

logger = structlog.get_logger()

ZEP_API_KEY = os.getenv("ZEP_API_KEY")
ZEP_USERS_GRAPH_ID = os.getenv("ZEP_GRAPH_ID_USERS", "users")


class ZepUserGraphService:
    """
    Service for managing user facts in ZEP knowledge graph.

    Provides:
    - User graph creation/initialization
    - Fact syncing (profile data → ZEP nodes/edges)
    - Semantic search across user facts
    - User context retrieval for prompts
    """

    def __init__(self):
        self.enabled = bool(ZEP_API_KEY)
        self.graph_id = ZEP_USERS_GRAPH_ID
        self._client = None

        if self.enabled:
            logger.info("zep_user_graph_initialized", graph_id=self.graph_id)
        else:
            logger.warning("zep_user_graph_disabled", reason="No ZEP_API_KEY")

    @property
    def client(self):
        """Lazy-load ZEP client."""
        if not self._client and self.enabled:
            from zep_cloud.client import Zep
            self._client = Zep(api_key=ZEP_API_KEY)
        return self._client

    async def get_async_client(self):
        """Get async ZEP client."""
        if not self.enabled:
            return None
        from zep_cloud.client import AsyncZep
        return AsyncZep(api_key=ZEP_API_KEY)

    # ========================================================================
    # GRAPH INITIALIZATION
    # ========================================================================

    async def ensure_graph_exists(self) -> bool:
        """
        Ensure the users graph exists, creating it if needed.

        Returns:
            True if graph exists/created, False on failure
        """
        if not self.enabled:
            return False

        try:
            client = await self.get_async_client()

            # Try to create the graph (idempotent - will succeed if exists)
            try:
                await client.graph.create(
                    graph_id=self.graph_id,
                    name="User Profiles",
                    description="Knowledge graph of user relocation profiles, facts, and preferences"
                )
                logger.info("zep_users_graph_created", graph_id=self.graph_id)
            except Exception as e:
                # Graph likely already exists
                if "already exists" in str(e).lower():
                    logger.info("zep_users_graph_exists", graph_id=self.graph_id)
                else:
                    logger.warning("zep_graph_create_warning", error=str(e))

            return True

        except Exception as e:
            logger.error("ensure_graph_exists_error", error=str(e))
            return False

    # ========================================================================
    # USER FACT SYNCING
    # ========================================================================

    async def sync_user_profile(
        self,
        user_id: str,
        profile: Dict[str, Any],
        facts: List[Dict[str, Any]],
        app_id: str = "relocation"
    ) -> Dict[str, Any]:
        """
        Sync user profile and facts to ZEP graph.

        Creates nodes for:
        - User (central node)
        - Destinations (countries interested in)
        - Origin (current location)
        - Profession/work
        - Budget
        - Timeline
        - Motivations

        Args:
            user_id: Stack Auth user ID
            profile: User profile dict from Neon
            facts: List of user_profile_facts from Neon
            app_id: Source application

        Returns:
            Dict with success status and episode_id
        """
        if not self.enabled:
            return {"success": False, "error": "ZEP not configured"}

        try:
            client = await self.get_async_client()
            await self.ensure_graph_exists()

            # Build structured user data for ZEP
            user_data = self._build_user_graph_data(user_id, profile, facts, app_id)

            # Add to ZEP graph
            response = await client.graph.add(
                graph_id=self.graph_id,
                type="json",
                data=json.dumps(user_data)
            )

            episode_id = None
            if response and hasattr(response, 'episode_id'):
                episode_id = response.episode_id

            logger.info(
                "user_profile_synced_to_zep",
                user_id=user_id,
                graph_id=self.graph_id,
                episode_id=episode_id,
                facts_count=len(facts)
            )

            return {
                "success": True,
                "graph_id": self.graph_id,
                "episode_id": episode_id,
                "facts_synced": len(facts)
            }

        except Exception as e:
            logger.error("sync_user_profile_error", user_id=user_id, error=str(e))
            return {"success": False, "error": str(e)}

    def _build_user_graph_data(
        self,
        user_id: str,
        profile: Dict[str, Any],
        facts: List[Dict[str, Any]],
        app_id: str
    ) -> Dict[str, Any]:
        """
        Build structured data for ZEP ingestion.

        ZEP will extract entities and relationships from this.
        """
        # Core user entity
        user_entity = {
            "type": "User",
            "id": user_id,
            "app_id": app_id
        }

        # Build natural language summary for better entity extraction
        summary_parts = [f"User {user_id} from {app_id} application."]

        # Profile-based facts
        if profile:
            if profile.get("current_city") or profile.get("current_country"):
                location = ", ".join(filter(None, [
                    profile.get("current_city"),
                    profile.get("current_country")
                ]))
                summary_parts.append(f"Currently located in {location}.")
                user_entity["current_location"] = location

            if profile.get("destination_countries"):
                destinations = profile["destination_countries"]
                if isinstance(destinations, list) and destinations:
                    dest_str = ", ".join(destinations)
                    summary_parts.append(f"Interested in relocating to: {dest_str}.")
                    user_entity["destinations"] = destinations

            if profile.get("job_title"):
                summary_parts.append(f"Works as {profile['job_title']}.")
                user_entity["profession"] = profile["job_title"]

            if profile.get("industry"):
                summary_parts.append(f"Industry: {profile['industry']}.")
                user_entity["industry"] = profile["industry"]

            if profile.get("remote_work"):
                summary_parts.append("Has remote work capability.")
                user_entity["remote_work"] = True

            if profile.get("budget_monthly"):
                summary_parts.append(f"Monthly budget: ${profile['budget_monthly']}.")
                user_entity["budget"] = profile["budget_monthly"]

            if profile.get("timeline"):
                timeline_labels = {
                    'asap': 'as soon as possible',
                    '3-6months': '3-6 months',
                    '6-12months': '6-12 months',
                    '1-2years': '1-2 years',
                    'exploring': 'still exploring options'
                }
                tl = timeline_labels.get(profile["timeline"], profile["timeline"])
                summary_parts.append(f"Timeline: {tl}.")
                user_entity["timeline"] = profile["timeline"]

            if profile.get("relocation_motivation"):
                motives = profile["relocation_motivation"]
                if isinstance(motives, list) and motives:
                    summary_parts.append(f"Motivations: {', '.join(motives)}.")
                    user_entity["motivations"] = motives

        # Add facts from user_profile_facts table
        facts_summary = []
        for fact in facts:
            fact_type = fact.get("fact_type")
            fact_value = fact.get("fact_value", {})
            confidence = fact.get("confidence", 0.5)

            # Extract value
            value = fact_value.get("value") or fact_value.get("country") or json.dumps(fact_value)

            if fact_type == "destination":
                interest_level = fact_value.get("interest_level", "exploring")
                facts_summary.append(f"Destination interest: {value} ({interest_level}, {confidence:.0%} confidence)")
            elif fact_type == "origin":
                facts_summary.append(f"Origin: {value}")
            elif fact_type == "family":
                facts_summary.append(f"Family status: {value}")
            elif fact_type == "profession":
                facts_summary.append(f"Profession: {value}")
            elif fact_type == "budget":
                facts_summary.append(f"Budget: {value}")
            elif fact_type == "timeline":
                facts_summary.append(f"Timeline: {value}")
            else:
                facts_summary.append(f"{fact_type}: {value}")

        if facts_summary:
            summary_parts.append("Extracted facts: " + "; ".join(facts_summary))

        return {
            "user_id": user_id,
            "app_id": app_id,
            "entity": user_entity,
            "summary": " ".join(summary_parts),
            "facts": facts,
            "profile": profile,
            "entity_type": "user_profile"
        }

    # ========================================================================
    # QUERYING
    # ========================================================================

    async def search_user_facts(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search user's facts semantically.

        Args:
            user_id: User to search facts for
            query: Natural language query
            limit: Max results

        Returns:
            Dict with matching facts/edges
        """
        if not self.enabled:
            return {"success": False, "error": "ZEP not configured"}

        try:
            client = await self.get_async_client()

            # Search edges (facts) for this user
            search_query = f"user {user_id} {query}"

            results = await client.graph.search(
                graph_id=self.graph_id,
                query=search_query,
                scope="edges",
                limit=limit
            )

            facts = []
            if results and hasattr(results, 'edges') and results.edges:
                for edge in results.edges:
                    fact_text = edge.fact if hasattr(edge, 'fact') else str(edge)
                    score = edge.score if hasattr(edge, 'score') else None

                    # Filter to only this user's facts
                    if user_id in fact_text or not user_id:
                        facts.append({
                            "fact": fact_text,
                            "score": score,
                            "uuid": getattr(edge, 'uuid_', None) or getattr(edge, 'uuid', None)
                        })

            return {
                "success": True,
                "user_id": user_id,
                "query": query,
                "facts": facts,
                "count": len(facts)
            }

        except Exception as e:
            logger.error("search_user_facts_error", user_id=user_id, error=str(e))
            return {"success": False, "error": str(e)}

    async def get_user_context_for_prompt(
        self,
        user_id: str,
        topic: Optional[str] = None
    ) -> str:
        """
        Get user context from ZEP for LLM prompts.

        Searches ZEP for relevant user facts and formats them for prompt injection.

        Args:
            user_id: User to get context for
            topic: Optional topic to focus search (e.g., "Portugal", "visa")

        Returns:
            Formatted context string for prompts
        """
        if not self.enabled:
            return ""

        try:
            client = await self.get_async_client()

            # Build search query
            query = f"user profile {user_id}"
            if topic:
                query += f" {topic}"

            results = await client.graph.search(
                graph_id=self.graph_id,
                query=query,
                scope="edges",
                limit=20
            )

            if not results or not hasattr(results, 'edges') or not results.edges:
                return ""

            # Extract and format facts
            facts = []
            seen = set()

            for edge in results.edges:
                if hasattr(edge, 'fact') and edge.fact:
                    fact_text = edge.fact.strip()
                    # Deduplicate and filter short facts
                    if len(fact_text) > 10 and fact_text not in seen:
                        seen.add(fact_text)
                        facts.append(fact_text)

            if not facts:
                return ""

            # Format for prompt
            context = "Known facts about this user:\n"
            for i, fact in enumerate(facts[:10], 1):
                context += f"- {fact}\n"

            return context

        except Exception as e:
            logger.error("get_user_context_error", user_id=user_id, error=str(e))
            return ""

    async def get_all_user_nodes(self, user_id: str) -> Dict[str, Any]:
        """
        Get all nodes related to a user for visualization.

        Args:
            user_id: User to get nodes for

        Returns:
            Dict with nodes and edges for graph visualization
        """
        if not self.enabled:
            return {"nodes": [], "edges": [], "error": "ZEP not configured"}

        try:
            client = await self.get_async_client()

            # Search for user's nodes
            node_results = await client.graph.search(
                graph_id=self.graph_id,
                query=f"user {user_id}",
                scope="nodes",
                limit=50
            )

            # Search for user's edges
            edge_results = await client.graph.search(
                graph_id=self.graph_id,
                query=f"user {user_id}",
                scope="edges",
                limit=100
            )

            nodes = []
            edges = []

            if node_results and hasattr(node_results, 'nodes') and node_results.nodes:
                for node in node_results.nodes:
                    nodes.append({
                        "id": getattr(node, 'uuid', str(node)),
                        "name": getattr(node, 'name', ''),
                        "type": getattr(node, 'type', 'entity'),
                        "summary": getattr(node, 'summary', '')
                    })

            if edge_results and hasattr(edge_results, 'edges') and edge_results.edges:
                for edge in edge_results.edges:
                    edges.append({
                        "uuid": getattr(edge, 'uuid_', None) or getattr(edge, 'uuid', None),
                        "fact": getattr(edge, 'fact', ''),
                        "name": getattr(edge, 'name', ''),  # Relationship type
                        "source": getattr(edge, 'source_node_uuid', None),
                        "target": getattr(edge, 'target_node_uuid', None)
                    })

            return {
                "success": True,
                "user_id": user_id,
                "nodes": nodes,
                "edges": edges
            }

        except Exception as e:
            logger.error("get_all_user_nodes_error", user_id=user_id, error=str(e))
            return {"nodes": [], "edges": [], "error": str(e)}


# Singleton instance
zep_user_graph_service = ZepUserGraphService()
