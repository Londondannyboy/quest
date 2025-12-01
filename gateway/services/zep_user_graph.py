"""
ZEP User Graph Service

Manages user profile facts in ZEP knowledge graph for semantic querying.
Uses the user ontology (User, Destination, CareerProfile, etc.) for structured extraction.
"""

import os
import json
from typing import Optional, List, Dict, Any
import structlog

logger = structlog.get_logger()

ZEP_API_KEY = os.getenv("ZEP_API_KEY")
ZEP_USERS_GRAPH_ID = os.getenv("ZEP_GRAPH_ID_USERS", "users")

# Import ontology helpers
try:
    import sys
    gateway_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if gateway_dir not in sys.path:
        sys.path.insert(0, gateway_dir)
    from models.user_ontology import (
        extract_user_entity,
        extract_destination_entity,
        extract_career_entity,
        extract_organization_entity,
        extract_motivation_entity,
        extract_family_entity,
        extract_financial_entity,
        extract_preference_entity,
    )
    ONTOLOGY_HELPERS_AVAILABLE = True
except ImportError as e:
    ONTOLOGY_HELPERS_AVAILABLE = False
    logger.warning("user_ontology_helpers_not_available", error=str(e))


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
        Build structured data for ZEP ingestion using ontology entity types.

        Creates structured entities that ZEP can extract as:
        - User entity (central node)
        - Destination entities (INTERESTED_IN edge)
        - Origin entity (LOCATED_IN edge)
        - CareerProfile entity (HAS_CAREER edge)
        - Organization entity (EMPLOYED_BY edge)
        - Motivation entities (MOTIVATED_BY edge)
        - FamilyUnit entity (HAS_FAMILY edge)
        - FinancialProfile entity (HAS_FINANCES edge)
        """
        profile = profile or {}

        # Build entities list for structured extraction
        entities = []
        relationships = []

        # 1. USER ENTITY (central node)
        user_entity = {
            "entity_type": "User",
            "name": f"User {user_id}",
            "user_type": profile.get("user_type", "individual"),
            "source_app": app_id,
            "stack_user_id": user_id,
            "nationality": profile.get("nationality"),
        }
        entities.append(user_entity)

        # 2. ORIGIN (current location) - LOCATED_IN edge
        if profile.get("current_city") or profile.get("current_country"):
            location = ", ".join(filter(None, [
                profile.get("current_city"),
                profile.get("current_country")
            ]))
            origin_entity = {
                "entity_type": "Origin",
                "name": location,
                "location_type": "current",
            }
            entities.append(origin_entity)
            relationships.append({
                "edge_type": "LOCATED_IN",
                "source": f"User {user_id}",
                "target": location,
                "location_type": "current"
            })

        # 3. DESTINATIONS - INTERESTED_IN edges
        if profile.get("destination_countries"):
            destinations = profile["destination_countries"]
            if isinstance(destinations, list):
                for i, country in enumerate(destinations):
                    # First destination is primary, rest are exploring
                    interest_level = "primary" if i == 0 else "exploring"
                    dest_entity = {
                        "entity_type": "Destination",
                        "name": country,
                        "interest_level": interest_level,
                        "context": "personal",  # Default, can be overridden by facts
                    }
                    entities.append(dest_entity)
                    relationships.append({
                        "edge_type": "INTERESTED_IN",
                        "source": f"User {user_id}",
                        "target": country,
                        "interest_level": interest_level,
                        "context": "personal"
                    })

        # 4. CAREER PROFILE - HAS_CAREER edge
        if profile.get("job_title") or profile.get("industry"):
            work_style = "remote" if profile.get("remote_work") else "office"
            career_entity = {
                "entity_type": "CareerProfile",
                "name": profile.get("job_title") or f"Career in {profile.get('industry')}",
                "job_title": profile.get("job_title"),
                "industry": profile.get("industry"),
                "work_style": work_style,
            }
            entities.append(career_entity)
            relationships.append({
                "edge_type": "HAS_CAREER",
                "source": f"User {user_id}",
                "target": career_entity["name"],
                "status": "current"
            })

        # 5. ORGANIZATION (employer) - EMPLOYED_BY edge
        if profile.get("employer") or profile.get("company_name"):
            org_entity = {
                "entity_type": "Organization",
                "name": profile.get("employer") or profile.get("company_name"),
                "company_type": "employer",
                "industry": profile.get("company_industry"),
            }
            entities.append(org_entity)
            relationships.append({
                "edge_type": "EMPLOYED_BY",
                "source": f"User {user_id}",
                "target": org_entity["name"],
                "role": "employee"
            })

        # 6. FINANCIAL PROFILE - HAS_FINANCES edge
        if profile.get("budget_monthly") or profile.get("income_range"):
            finance_entity = {
                "entity_type": "FinancialProfile",
                "name": "Finances",
                "monthly_budget": str(profile.get("budget_monthly")) if profile.get("budget_monthly") else None,
                "income_range": profile.get("income_range"),
            }
            entities.append(finance_entity)
            relationships.append({
                "edge_type": "HAS_FINANCES",
                "source": f"User {user_id}",
                "target": "Finances"
            })

        # 7. MOTIVATIONS - MOTIVATED_BY edges
        if profile.get("relocation_motivation"):
            motives = profile["relocation_motivation"]
            if isinstance(motives, list):
                for motive in motives:
                    motive_entity = {
                        "entity_type": "Motivation",
                        "name": motive,
                        "motivation_type": "both",  # personal + professional
                        "category": self._categorize_motivation(motive),
                        "strength": "important"
                    }
                    entities.append(motive_entity)
                    relationships.append({
                        "edge_type": "MOTIVATED_BY",
                        "source": f"User {user_id}",
                        "target": motive,
                        "strength": "important"
                    })

        # 8. FAMILY - HAS_FAMILY edge
        if profile.get("has_children") or profile.get("family_status"):
            family_entity = {
                "entity_type": "FamilyUnit",
                "name": "Family",
                "status": profile.get("family_status", "unknown"),
                "children_count": str(profile.get("number_of_children")) if profile.get("number_of_children") else None,
            }
            entities.append(family_entity)
            relationships.append({
                "edge_type": "HAS_FAMILY",
                "source": f"User {user_id}",
                "target": "Family"
            })

        # Process additional facts from user_profile_facts table
        for fact in facts:
            fact_type = fact.get("fact_type")
            fact_value = fact.get("fact_value", {})

            if fact_type == "destination":
                country = fact_value.get("country") or fact_value.get("value")
                if country:
                    interest_level = fact_value.get("interest_level", "exploring")
                    dest_entity = {
                        "entity_type": "Destination",
                        "name": country,
                        "interest_level": interest_level,
                        "context": fact_value.get("context", "personal"),
                    }
                    entities.append(dest_entity)
                    relationships.append({
                        "edge_type": "INTERESTED_IN",
                        "source": f"User {user_id}",
                        "target": country,
                        "interest_level": interest_level
                    })

            elif fact_type == "goal":
                goal_entity = {
                    "entity_type": "Goal",
                    "name": fact_value.get("description") or fact_value.get("value"),
                    "goal_type": fact_value.get("type", "personal"),
                    "priority": fact_value.get("priority", "medium"),
                }
                entities.append(goal_entity)
                relationships.append({
                    "edge_type": "HAS_GOAL",
                    "source": f"User {user_id}",
                    "target": goal_entity["name"]
                })

        # Build narrative summary for better semantic search
        summary = self._build_narrative_summary(user_id, app_id, entities, relationships)

        return {
            "user_id": user_id,
            "app_id": app_id,
            "entities": entities,
            "relationships": relationships,
            "summary": summary,
            "entity_type": "user_profile_structured"
        }

    def _categorize_motivation(self, motive: str) -> str:
        """Map motivation text to ontology category."""
        motive_lower = motive.lower()
        category_map = {
            "tax": "tax", "taxes": "tax", "lower taxes": "tax",
            "lifestyle": "lifestyle", "quality of life": "lifestyle",
            "adventure": "adventure", "travel": "adventure",
            "family": "family", "children": "family", "schools": "family",
            "career": "career", "job": "career", "work": "career",
            "cost": "cost_of_living", "cheaper": "cost_of_living", "affordable": "cost_of_living",
            "weather": "weather", "climate": "weather", "sun": "weather", "warm": "weather",
            "business": "business_setup", "startup": "business_setup", "company": "business_setup",
        }
        for keyword, cat in category_map.items():
            if keyword in motive_lower:
                return cat
        return "lifestyle"  # default

    def _build_narrative_summary(
        self,
        user_id: str,
        app_id: str,
        entities: List[Dict],
        relationships: List[Dict]
    ) -> str:
        """Build natural language summary for semantic search."""
        parts = [f"User {user_id} from {app_id} application."]

        for entity in entities:
            etype = entity.get("entity_type")
            name = entity.get("name", "")

            if etype == "Origin":
                parts.append(f"Currently located in {name}.")
            elif etype == "Destination":
                level = entity.get("interest_level", "exploring")
                context = entity.get("context", "personal")
                parts.append(f"Interested in relocating to {name} ({level} interest, {context} reasons).")
            elif etype == "CareerProfile":
                title = entity.get("job_title")
                industry = entity.get("industry")
                style = entity.get("work_style")
                if title:
                    parts.append(f"Works as {title}.")
                if industry:
                    parts.append(f"Industry: {industry}.")
                if style == "remote":
                    parts.append("Has remote work capability.")
            elif etype == "Organization":
                parts.append(f"Employed by {name}.")
            elif etype == "FinancialProfile":
                budget = entity.get("monthly_budget")
                if budget:
                    parts.append(f"Monthly budget: ${budget}.")
            elif etype == "Motivation":
                category = entity.get("category", "lifestyle")
                parts.append(f"Motivated by {name} ({category}).")
            elif etype == "FamilyUnit":
                status = entity.get("status")
                children = entity.get("children_count")
                if status:
                    parts.append(f"Family status: {status}.")
                if children:
                    parts.append(f"Has {children} children.")
            elif etype == "Goal":
                goal_type = entity.get("goal_type", "personal")
                parts.append(f"{goal_type.capitalize()} goal: {name}.")

        return " ".join(parts)

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
