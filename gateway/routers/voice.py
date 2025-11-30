"""
Voice Interface Router

WebSocket endpoint for Hume.ai EVI integration with Zep knowledge graph
and Gemini LLM for processing relocation queries.
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/voice", tags=["voice"])


# ============================================================================
# CONFIGURATION
# ============================================================================

HUME_API_KEY = os.getenv("HUME_API_KEY")
HUME_SECRET_KEY = os.getenv("HUME_SECRET_KEY")
ZEP_API_KEY = os.getenv("ZEP_API_KEY")
ZEP_PROJECT_ID = os.getenv("ZEP_PROJECT_ID", "e265b35c-69d8-4880-b2b5-ec6acb237a3e")
ZEP_GRAPH_ID = os.getenv("ZEP_GRAPH_ID", "relocation")  # Relocation knowledge graph (lowercase!)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Relocation-relevant ontology types for filtered searches
RELOCATION_ENTITY_TYPES = ["Location", "Country", "Company", "Article"]
RELOCATION_EDGE_TYPES = ["LOCATED_IN", "IN_COUNTRY", "HEADQUARTERED_IN", "MENTIONS"]


# ============================================================================
# ZEP KNOWLEDGE GRAPH INTEGRATION
# ============================================================================

class ZepKnowledgeGraph:
    """Interface to Zep knowledge graph for Quest project"""

    def __init__(self, api_key: str, project_id: str, graph_id: str):
        self.api_key = api_key
        self.project_id = project_id
        self.graph_id = graph_id
        try:
            from zep_cloud.client import Zep
            self.client = Zep(api_key=api_key)
            logger.info("zep_client_initialized", project_id=project_id, graph_id=graph_id)
        except ImportError:
            logger.warning("zep-cloud package not installed")
            self.client = None
        except Exception as e:
            logger.error("zep_init_error", error=str(e))
            self.client = None

    def _search_edges(self, query: str, limit: int = 10) -> list:
        """Search edges (facts/relationships) in the Relocation graph using graph_id."""
        try:
            edge_results = self.client.graph.search(
                graph_id=self.graph_id,  # Use graph_id, not user_id!
                query=query,
                scope="edges",
                limit=limit
            )

            formatted_edges = []
            if hasattr(edge_results, 'edges') and edge_results.edges:
                for edge in edge_results.edges:
                    formatted_edges.append({
                        "fact": getattr(edge, 'fact', str(edge)),
                        "type": getattr(edge, 'name', 'unknown'),
                        "score": getattr(edge, 'score', 0.0),
                        "attributes": getattr(edge, 'attributes', {}),
                        "valid_at": str(getattr(edge, 'valid_at', ''))
                    })

            return formatted_edges
        except Exception as e:
            logger.warning("edge_search_failed", error=str(e), query=query)
            return []

    def _search_nodes(self, query: str, limit: int = 10) -> list:
        """Search nodes (entities) in the Relocation graph using graph_id."""
        try:
            node_results = self.client.graph.search(
                graph_id=self.graph_id,  # Use graph_id, not user_id!
                query=query,
                scope="nodes",
                limit=limit
            )

            formatted_nodes = []
            if hasattr(node_results, 'nodes') and node_results.nodes:
                for node in node_results.nodes:
                    # Extract node type from labels
                    labels = getattr(node, 'labels', [])
                    node_type = 'Entity'
                    for label in labels:
                        if label in RELOCATION_ENTITY_TYPES:
                            node_type = label
                            break
                    if labels and node_type == 'Entity':
                        node_type = labels[0]

                    formatted_nodes.append({
                        "name": getattr(node, 'name', 'unknown'),
                        "type": node_type,
                        "summary": getattr(node, 'summary', ''),
                        "score": getattr(node, 'score', 0.0),
                        "attributes": getattr(node, 'attributes', {})
                    })

            return formatted_nodes
        except Exception as e:
            logger.warning("node_search_failed", error=str(e), query=query)
            return []

    def _format_for_llm(self, edges: list, nodes: list) -> str:
        """Format search results into structured context for the LLM prompt."""
        context_parts = []

        # Format FACTS from edges
        if edges:
            facts = []
            for edge in edges[:5]:  # Top 5 most relevant
                fact = edge.get("fact", "")
                if fact and len(fact) > 10:
                    facts.append(f"- {fact}")

            if facts:
                context_parts.append("FACTS:\n" + "\n".join(facts))

        # Format ENTITIES from nodes by type
        if nodes:
            by_type = {}
            for node in nodes[:8]:  # Top 8 nodes
                node_type = node.get("type", "Entity")
                if node_type not in by_type:
                    by_type[node_type] = []
                by_type[node_type].append(node)

            for node_type, type_nodes in by_type.items():
                type_name = node_type.upper() + "S"
                entries = []
                for node in type_nodes[:3]:  # Max 3 per type
                    name = node.get("name", "")
                    summary = node.get("summary", "")
                    if name:
                        entry = f"- {name}"
                        if summary:
                            entry += f": {summary[:150]}"
                        entries.append(entry)

                if entries:
                    context_parts.append(f"{type_name}:\n" + "\n".join(entries))

        return "\n\n".join(context_parts) if context_parts else ""

    async def search(self, query: str, include_nodes: bool = True) -> dict:
        """
        Search the Relocation knowledge graph for relevant information.

        Uses graph_id (not user_id) to query the Relocation graph directly.
        Searches both edges (facts/relationships) and nodes (entities) for
        comprehensive context.

        Args:
            query: Search query about relocation
            include_nodes: Whether to also search nodes (default True)

        Returns:
            Dictionary with edges, nodes, formatted_context, and success status
        """
        if not self.client:
            return {
                "error": "Zep client not initialized",
                "results": [],
                "edges": [],
                "nodes": [],
                "formatted_context": "",
                "success": False
            }

        try:
            # Search EDGES (facts/relationships)
            edges = self._search_edges(query)

            # Search NODES (entities) for richer context
            nodes = []
            if include_nodes:
                nodes = self._search_nodes(query)

            # Format results for LLM context
            formatted_context = self._format_for_llm(edges, nodes)

            # Backwards compatibility - simple results list
            results = [{"fact": e.get("fact", ""), "relevance": e.get("score", 1.0)} for e in edges[:5]]

            logger.info("zep_search_success",
                       query=query,
                       edges=len(edges),
                       nodes=len(nodes),
                       has_context=bool(formatted_context))

            return {
                "query": query,
                "results": results,
                "edges": edges,
                "nodes": nodes,
                "formatted_context": formatted_context,
                "success": True
            }

        except Exception as e:
            logger.error("zep_search_error", error=str(e), query=query)
            return {
                "error": str(e),
                "query": query,
                "results": [],
                "edges": [],
                "nodes": [],
                "formatted_context": "",
                "success": False
            }


# ============================================================================
# GEMINI LLM INTEGRATION
# ============================================================================

class GeminiAssistant:
    """Gemini LLM for processing queries with Zep knowledge graph context and Neon fallback"""

    def __init__(self, api_key: str, zep_graph: ZepKnowledgeGraph, neon_store: Optional['NeonKnowledgeStore'] = None):
        self.api_key = api_key
        self.zep_graph = zep_graph
        self.neon_store = neon_store  # Neon database fallback

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            logger.info("gemini_client_initialized")
        except ImportError:
            logger.warning("google-generativeai package not installed")
            self.model = None
        except Exception as e:
            logger.error("gemini_init_error", error=str(e))
            self.model = None

    async def process_query(self, query: str, thread_id: str = None) -> str:
        """
        Process a query using Gemini + Zep knowledge graph + Neon fallback

        Args:
            query: User's question
            thread_id: Optional ZEP thread ID for conversation memory

        Returns:
            Generated response text optimized for voice, with links section appended
        """
        if not self.model:
            return "I apologize, but the assistant is currently unavailable. Please try again later."

        try:
            # Get ZEP conversation context if thread exists
            zep_memory_context = ""
            if thread_id and self.zep_graph.client:
                try:
                    memory = self.zep_graph.client.thread.get_user_context(thread_id=thread_id)
                    if memory and hasattr(memory, 'context') and memory.context:
                        zep_memory_context = f"\n\nConversation context:\n{memory.context}"
                        logger.info("zep_memory_loaded", thread_id=thread_id)
                except Exception as e:
                    logger.warning("zep_memory_error", error=str(e), thread_id=thread_id)

            # Search knowledge graph for relevant context (using graph_id now)
            kg_results = await self.zep_graph.search(query)

            # Build context from knowledge graph using new formatted_context
            context = ""
            source = None
            related_links = {"articles": [], "companies": [], "countries": []}

            # Check if ZEP returned useful results (edges or nodes)
            has_zep_content = (
                kg_results.get("success") and
                (kg_results.get("edges") or kg_results.get("nodes") or kg_results.get("formatted_context"))
            )

            if has_zep_content and kg_results.get("formatted_context"):
                context = f"\n\nRelevant information from the knowledge base:\n{kg_results['formatted_context']}"
                source = "zep"
                logger.info("using_zep_context",
                           edges=len(kg_results.get("edges", [])),
                           nodes=len(kg_results.get("nodes", [])))

            # If ZEP empty/failed, try Neon database fallback
            elif self.neon_store:
                neon_results = await self.neon_store.search(query)
                if neon_results.get("success") and neon_results.get("results"):
                    context = self._format_neon_context(neon_results)
                    source = "neon"
                    # Extract links from Neon results for display
                    for result in neon_results.get("results", []):
                        if result.get("type") == "article":
                            related_links["articles"].append({
                                "title": result.get("title", ""),
                                "url": f"https://relocation.quest/{result.get('slug', '')}"
                            })
                        elif result.get("type") == "company":
                            related_links["companies"].append({
                                "name": result.get("name", ""),
                                "url": f"https://relocation.quest/companies/{result.get('slug', '')}"
                            })
                        elif result.get("type") == "country":
                            related_links["countries"].append({
                                "name": result.get("name", ""),
                                "url": f"https://relocation.quest/countries/{result.get('slug', '')}"
                            })
                    logger.info("using_neon_fallback",
                               results_count=len(neon_results["results"]),
                               types=neon_results.get("types", {}))

            # Log if no context found from either source
            if not context:
                logger.info("no_knowledge_found", query=query, zep_tried=True, neon_tried=bool(self.neon_store))

            # System prompt optimized for voice interaction
            system_prompt = """You are the voice assistant for Relocation Quest (relocation.quest), a comprehensive
international relocation platform helping people move to new countries. Relocation Quest provides:
- In-depth country guides and visa requirement articles
- Cost of living comparisons and practical relocation advice
- Curated directory of trusted relocation service providers
- Information on digital nomad visas, work permits, and residency options

ABOUT RELOCATION QUEST:
Relocation Quest is designed for digital nomads, remote workers, expats, and anyone considering
international relocation. Our mission is to make moving abroad less overwhelming by providing
accurate, up-to-date information gathered from official sources and real experiences.

CRITICAL KNOWLEDGE BASE RULES:
1. If there is a "Relevant information from the knowledge base" section below AND it contains
   SPECIFIC information about the country/topic the user asked about:
   - Start with something like "Great news! We have info on that." or "Yes, we cover [country/topic]!"
   - Use the knowledge base information as your primary source
   - If articles are mentioned with URLs, recommend them: "Check out our guide at relocation.quest/[slug]"

2. If the knowledge base contains only TANGENTIAL mentions (e.g., the country appears in a
   "best countries" list but we don't have a dedicated guide):
   - Say something like "We mention [country] in some of our comparison articles, but we don't
     have a dedicated guide yet."
   - Don't pretend to have comprehensive coverage if we don't

3. If there is NO relevant information in the knowledge base:
   - Be honest: "We don't have detailed coverage of [country/topic] yet, but I can share some general info."
   - Provide brief general knowledge if helpful
   - Suggest they check back as we're always adding new country guides

4. For authoritative external sources, you may reference:
   - Official government immigration websites (e.g., "You'll want to check the [country] immigration portal")
   - Numbeo for cost of living comparisons
   - Expat communities like InterNations
   Always mention these as supplementary resources.

VOICE RESPONSE GUIDELINES:
- Keep responses under 100 words (this is voice interaction)
- Be conversational and natural - this is spoken, not written
- Use simple language, avoid jargon
- Provide specific, actionable information
- When mentioning article links, speak them naturally: "Check out our Cyprus digital nomad guide on relocation dot quest"

NATURAL THINKING PHRASES (use these to sound human while processing):
- When switching topics or thinking: "Let me check on that...", "Good question, let me think...", "Hmm, let me see..."
- When looking something up: "Give me two ticks...", "Let me pull that up...", "One moment..."
- When transitioning: "So...", "Right, so...", "Okay, so..."
- Acknowledgment starters: "Ah yes...", "Oh interesting...", "I see what you mean..."
Use these naturally - don't overuse them, but sprinkle them in to make responses feel more human and conversational.

TONE:
- Friendly, supportive, and encouraging
- Professional but warm and personable
- Empathetic to the challenges of relocating abroad
- Excited to help people achieve their relocation dreams
"""

            # Generate response with memory context included
            full_prompt = f"{system_prompt}{zep_memory_context}\n\nUser question: {query}{context}\n\nProvide a brief, conversational voice response:"

            response = self.model.generate_content(full_prompt)

            if response and response.text:
                response_text = response.text

                # Store conversation in ZEP thread for memory (async fire-and-forget)
                if thread_id and self.zep_graph.client:
                    try:
                        self.zep_graph.client.thread.add_messages(
                            thread_id=thread_id,
                            messages=[
                                {"role": "user", "content": query},
                                {"role": "assistant", "content": response_text}
                            ]
                        )
                        logger.info("zep_memory_stored", thread_id=thread_id)
                    except Exception as e:
                        logger.warning("zep_memory_store_error", error=str(e))

                # Append links section if we have any (JSON format for frontend parsing)
                has_links = any([
                    related_links.get("articles"),
                    related_links.get("companies"),
                    related_links.get("countries")
                ])

                if has_links:
                    import json
                    links_json = json.dumps(related_links)
                    response_text = f"{response_text}\n\n---LINKS---\n{links_json}"

                logger.info("gemini_response_generated", query=query, length=len(response_text), has_links=has_links)
                return response_text
            else:
                return "I'm having trouble generating a response. Could you rephrase your question?"

        except Exception as e:
            logger.error("gemini_error", error=str(e), query=query)
            return "I apologize, I encountered an error. Please try asking your question again."

    def _format_neon_context(self, neon_results: dict) -> str:
        """Format Neon database results for Gemini context"""
        context = "\n\nRelevant information from the knowledge base:\n"

        for result in neon_results.get("results", []):
            result_type = result.get("type")

            if result_type == "country":
                slug = result.get('slug', result.get('name', '').lower().replace(' ', '-'))
                country_url = f"relocation.quest/countries/{slug}" if slug else "relocation.quest/countries"
                context += f"- {result['name']} ({result.get('region', 'Unknown region')}) [Country guide: {country_url}]: "
                if result.get('capital'):
                    context += f"Capital is {result['capital']}. "
                if result.get('currency_code'):
                    context += f"Currency: {result['currency_code']}. "
                if result.get('language'):
                    context += f"Language: {result['language']}. "
                facts = result.get('facts', {})
                if facts:
                    if facts.get('visa_info'):
                        context += f"Visa: {facts['visa_info']}. "
                    if facts.get('cost_of_living'):
                        context += f"Cost of living: {facts['cost_of_living']}. "
                    if facts.get('tax_info'):
                        context += f"Tax: {facts['tax_info']}. "
                if result.get('motivations'):
                    context += f"Good for: {', '.join(result['motivations'])}. "
                context += "\n"

            elif result_type == "article":
                slug = result.get('slug', '')
                url = f"relocation.quest/{slug}" if slug else "relocation.quest"
                context += f"- Article '{result['title']}' (URL: {url}): {result.get('excerpt') or result.get('description', '')}\n"

            elif result_type == "company":
                desc = result.get('description', '')[:200] or result.get('overview', '')[:200]
                context += f"- Service provider '{result['name']}': {desc}\n"

        return context


# ============================================================================
# NEON DATABASE FALLBACK
# ============================================================================

class NeonKnowledgeStore:
    """Direct database fallback when ZEP returns empty results"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        logger.info("neon_store_initialized")

    def _extract_keywords(self, query: str) -> list:
        """Extract meaningful keywords from a query, filtering out common words."""
        stop_words = {
            'what', 'is', 'the', 'a', 'an', 'of', 'in', 'to', 'for', 'and', 'or',
            'how', 'much', 'does', 'it', 'cost', 'can', 'i', 'do', 'about', 'tell',
            'me', 'living', 'live', 'move', 'moving', 'relocate', 'relocating',
            'visa', 'requirements', 'best', 'good', 'where', 'which', 'are', 'there'
        }
        words = query.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords if keywords else words[:3]  # Fallback to first 3 words

    async def search_countries(self, query: str) -> list:
        """Search countries by name, region, or keywords"""
        try:
            import psycopg

            # Extract keywords from query
            keywords = self._extract_keywords(query)
            if not keywords:
                return []

            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    # Build OR conditions for each keyword
                    conditions = []
                    params = []
                    for keyword in keywords[:3]:  # Limit to 3 keywords
                        pattern = f"%{keyword}%"
                        conditions.append("""(
                            LOWER(name) LIKE %s
                            OR LOWER(region) LIKE %s
                            OR LOWER(continent) LIKE %s
                            OR LOWER(capital) LIKE %s
                        )""")
                        params.extend([pattern, pattern, pattern, pattern])

                    where_clause = " OR ".join(conditions)

                    await cur.execute(f"""
                        SELECT
                            name, code, slug, region, continent,
                            flag_emoji, capital, currency_code, language,
                            relocation_motivations, relocation_tags, facts
                        FROM countries
                        WHERE status = 'published'
                        AND ({where_clause})
                        LIMIT 3
                    """, params)

                    rows = await cur.fetchall()

                    results = []
                    for row in rows:
                        results.append({
                            "type": "country",
                            "name": row[0],
                            "code": row[1],
                            "slug": row[2],
                            "region": row[3],
                            "continent": row[4],
                            "flag_emoji": row[5],
                            "capital": row[6],
                            "currency_code": row[7],
                            "language": row[8],
                            "motivations": row[9] or [],
                            "tags": row[10] or [],
                            "facts": row[11] or {}
                        })

                    return results

        except Exception as e:
            logger.error("neon_country_search_error", error=str(e))
            return []

    async def search_articles(self, query: str) -> list:
        """Search articles by title and content"""
        try:
            import psycopg

            # Extract keywords from query
            keywords = self._extract_keywords(query)
            if not keywords:
                return []

            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    # Build OR conditions for each keyword
                    conditions = []
                    params = []
                    for keyword in keywords[:3]:
                        pattern = f"%{keyword}%"
                        conditions.append("""(
                            LOWER(title) LIKE %s
                            OR LOWER(excerpt) LIKE %s
                            OR LOWER(meta_description) LIKE %s
                        )""")
                        params.extend([pattern, pattern, pattern])

                    where_clause = " OR ".join(conditions)

                    await cur.execute(f"""
                        SELECT
                            id, slug, title, excerpt,
                            article_angle, country_code, meta_description
                        FROM articles
                        WHERE app = 'relocation'
                        AND status = 'published'
                        AND ({where_clause})
                        ORDER BY published_at DESC NULLS LAST
                        LIMIT 10
                    """, params)

                    rows = await cur.fetchall()

                    results = []
                    for row in rows:
                        results.append({
                            "type": "article",
                            "id": str(row[0]),
                            "slug": row[1],
                            "title": row[2],
                            "excerpt": row[3] or "",
                            "article_type": row[4],
                            "country_code": row[5],
                            "description": row[6] or ""
                        })

                    return results

        except Exception as e:
            logger.error("neon_article_search_error", error=str(e))
            return []

    async def search_companies(self, query: str) -> list:
        """Search companies by name and description"""
        try:
            import psycopg

            # Extract keywords from query
            keywords = self._extract_keywords(query)
            if not keywords:
                return []

            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    # Build OR conditions for each keyword
                    conditions = []
                    params = []
                    for keyword in keywords[:3]:
                        pattern = f"%{keyword}%"
                        conditions.append("""(
                            LOWER(name) LIKE %s
                            OR LOWER(description) LIKE %s
                        )""")
                        params.extend([pattern, pattern])

                    where_clause = " OR ".join(conditions)

                    await cur.execute(f"""
                        SELECT
                            id, slug, name, description, overview
                        FROM companies
                        WHERE app = 'relocation'
                        AND ({where_clause})
                        LIMIT 3
                    """, params)

                    rows = await cur.fetchall()

                    results = []
                    for row in rows:
                        results.append({
                            "type": "company",
                            "id": str(row[0]),
                            "slug": row[1],
                            "name": row[2],
                            "description": row[3] or "",
                            "overview": row[4] or ""
                        })

                    return results

        except Exception as e:
            logger.error("neon_company_search_error", error=str(e))
            return []

    async def search(self, query: str) -> dict:
        """
        Combined search across all tables.
        Returns aggregated results with source types.
        """
        logger.info("neon_fallback_search", query=query)

        # Run all searches in parallel
        countries, articles, companies = await asyncio.gather(
            self.search_countries(query),
            self.search_articles(query),
            self.search_companies(query),
            return_exceptions=True
        )

        # Handle any exceptions from gather
        countries = countries if isinstance(countries, list) else []
        articles = articles if isinstance(articles, list) else []
        companies = companies if isinstance(companies, list) else []

        all_results = countries + articles + companies

        logger.info("neon_fallback_results",
                   countries=len(countries),
                   articles=len(articles),
                   companies=len(companies))

        return {
            "query": query,
            "results": all_results,
            "types": {
                "countries": len(countries),
                "articles": len(articles),
                "companies": len(companies)
            },
            "success": len(all_results) > 0
        }


# ============================================================================
# HUME EVI INTEGRATION
# ============================================================================

class HumeEVIConnection:
    """Handler for Hume Empathic Voice Interface connections"""

    def __init__(self, api_key: str, assistant: GeminiAssistant):
        self.api_key = api_key
        self.assistant = assistant
        self.config_id = None  # Will be set when EVI config is created

        try:
            from hume import AsyncHumeClient
            from hume.empathic_voice import ChatConnectOptions

            self.client = AsyncHumeClient(api_key=api_key)
            self.ChatConnectOptions = ChatConnectOptions
            logger.info("hume_client_initialized")
        except ImportError:
            logger.warning("hume package not installed")
            self.client = None
            self.ChatConnectOptions = None
        except Exception as e:
            logger.error("hume_init_error", error=str(e))
            self.client = None

    async def handle_evi_connection(
        self,
        websocket: WebSocket,
        user_id: str,
        config_id: Optional[str] = None
    ):
        """
        Handle EVI voice connection via WebSocket

        This connects the frontend WebSocket to Hume's EVI,
        processes queries through Gemini + Zep, and returns voice responses.

        Args:
            websocket: Frontend WebSocket connection
            user_id: User identifier
            config_id: Optional EVI configuration ID
        """
        if not self.client:
            await websocket.send_json({
                "type": "error",
                "message": "Hume EVI not available"
            })
            return

        logger.info("evi_connection_started", user_id=user_id)

        try:
            # For now, handle text queries through our assistant
            # Full audio streaming would require more complex EVI setup
            while True:
                data = await websocket.receive_json()

                message_type = data.get("type")

                if message_type == "query":
                    query_text = data.get("text", "")

                    if not query_text:
                        await websocket.send_json({
                            "type": "error",
                            "message": "No query text provided"
                        })
                        continue

                    logger.info("processing_query", query=query_text, user_id=user_id)

                    # Process through our assistant (Gemini + Zep)
                    response = await self.assistant.process_query(query_text)

                    await websocket.send_json({
                        "type": "response",
                        "text": response,
                        "query": query_text,
                        "timestamp": datetime.utcnow().isoformat()
                    })

                elif message_type == "ping":
                    await websocket.send_json({"type": "pong"})

                else:
                    logger.warning("unknown_message_type", type=message_type)

        except WebSocketDisconnect:
            logger.info("websocket_disconnected", user_id=user_id)
        except Exception as e:
            logger.error("evi_connection_error", error=str(e), user_id=user_id)
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": "Connection error occurred"
                })
            except:
                pass


# ============================================================================
# INITIALIZE SERVICES
# ============================================================================

# Initialize services if API keys are available
zep_graph = None
neon_store = None
gemini_assistant = None
hume_handler = None

if ZEP_API_KEY and ZEP_PROJECT_ID:
    zep_graph = ZepKnowledgeGraph(ZEP_API_KEY, ZEP_PROJECT_ID, ZEP_GRAPH_ID)
    logger.info("zep_configured", graph_id=ZEP_GRAPH_ID)

# Initialize Neon fallback
if DATABASE_URL:
    neon_store = NeonKnowledgeStore(DATABASE_URL)
    logger.info("neon_fallback_configured")

if GEMINI_API_KEY and zep_graph:
    gemini_assistant = GeminiAssistant(GEMINI_API_KEY, zep_graph, neon_store)

if HUME_API_KEY and gemini_assistant:
    hume_handler = HumeEVIConnection(HUME_API_KEY, gemini_assistant)


# ============================================================================
# TEXT CHAT HANDLER (WITHOUT HUME)
# ============================================================================

async def handle_text_chat(websocket: WebSocket, user_id: str, assistant: GeminiAssistant):
    """
    Handle text-only chat without Hume EVI

    This is a fallback for when Hume SDK isn't available,
    going directly to Gemini + Zep for text queries.
    """
    logger.info("text_chat_started", user_id=user_id, mode="text_only")

    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "query":
                query_text = data.get("text", "")

                if not query_text:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No query text provided"
                    })
                    continue

                logger.info("processing_text_query", query=query_text, user_id=user_id)

                # Process through Gemini + Zep
                response = await assistant.process_query(query_text)

                await websocket.send_json({
                    "type": "response",
                    "text": response,
                    "query": query_text,
                    "timestamp": datetime.utcnow().isoformat()
                })

            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                logger.warning("unknown_message_type", type=message_type)

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", user_id=user_id)
    except Exception as e:
        logger.error("text_chat_error", error=str(e), user_id=user_id)
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Connection error occurred"
            })
        except:
            pass


# ============================================================================
# ROUTES
# ============================================================================

@router.get("/health")
async def voice_health():
    """Check if voice services are configured and ready"""
    status = {
        "hume": {
            "configured": HUME_API_KEY is not None,
            "client_ready": hume_handler is not None and hume_handler.client is not None
        },
        "zep": {
            "configured": ZEP_API_KEY is not None,
            "client_ready": zep_graph is not None and zep_graph.client is not None
        },
        "gemini": {
            "configured": GEMINI_API_KEY is not None,
            "client_ready": gemini_assistant is not None and gemini_assistant.model is not None
        },
        "neon": {
            "configured": DATABASE_URL is not None,
            "client_ready": neon_store is not None
        },
        "ready": all([
            hume_handler and hume_handler.client,
            gemini_assistant and gemini_assistant.model,
            zep_graph and zep_graph.client
        ]),
        "timestamp": datetime.utcnow().isoformat()
    }

    logger.info("health_check", status=status)
    return status


@router.websocket("/chat")
async def voice_chat(
    websocket: WebSocket,
    user_id: Optional[str] = Query(default="anonymous"),
    config_id: Optional[str] = Query(default=None)
):
    """
    WebSocket endpoint for voice chat

    Connects frontend to Hume EVI + Gemini + Zep pipeline for voice-enabled
    relocation assistance.

    Query Parameters:
        user_id: User identifier (default: "anonymous")
        config_id: Optional Hume EVI config ID
    """
    await websocket.accept()

    logger.info("websocket_connected", user_id=user_id)

    # Check if essential services are initialized (Gemini + Zep required, Hume optional for text chat)
    if not gemini_assistant or not zep_graph:
        missing = []
        if not gemini_assistant: missing.append("Gemini")
        if not zep_graph: missing.append("Zep")

        await websocket.send_json({
            "type": "error",
            "message": f"Services not configured: {', '.join(missing)}"
        })
        await websocket.close()
        logger.error("websocket_rejected_missing_services", missing=missing)
        return

    # Send welcome message
    await websocket.send_json({
        "type": "connected",
        "message": "Voice assistant ready! Ask me anything about international relocation.",
        "user_id": user_id
    })

    # Handle the conversation
    # For text chat, we don't need Hume - go directly to Gemini + Zep
    if hume_handler and hume_handler.client:
        await hume_handler.handle_evi_connection(websocket, user_id, config_id)
    else:
        # Text-only mode (no Hume voice)
        await handle_text_chat(websocket, user_id, gemini_assistant)


@router.post("/query")
async def text_query(
    query: str,
    user_id: str = "anonymous"
):
    """
    HTTP endpoint for text queries (non-voice interface)

    Useful for testing and direct API access without WebSocket

    Args:
        query: The relocation question
        user_id: User identifier

    Returns:
        JSON response with answer
    """
    if not gemini_assistant:
        raise HTTPException(
            status_code=503,
            detail="Assistant not configured. Check API keys."
        )

    logger.info("text_query_received", query=query, user_id=user_id)

    response = await gemini_assistant.process_query(query)

    return {
        "query": query,
        "response": response,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }


async def _handle_llm_request(request: dict):
    """
    Shared handler for Hume EVI custom LLM requests

    Processes conversation context and returns responses from
    our Gemini + Zep pipeline.
    """
    if not gemini_assistant:
        return {
            "response": "I apologize, but the assistant is currently unavailable.",
            "error": "Assistant not configured"
        }

    try:
        # Extract the latest user message
        messages = request.get("messages", [])
        if not messages:
            return {"response": "I didn't receive a message. Could you please try again?"}

        # Get the last user message
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content")
                break

        if not user_message:
            return {"response": "I didn't understand that. Could you rephrase?"}

        # Extract user_id from context if available
        # Default to 'newsroom-system' where all Quest knowledge is stored
        context = request.get("context", {})
        user_id = context.get("user_id", "newsroom-system")

        logger.info("hume_llm_request", query=user_message, user_id=user_id)

        # Process through Gemini + Zep with newsroom-system knowledge
        response = await gemini_assistant.process_query(user_message)

        return {
            "response": response
        }

    except Exception as e:
        logger.error("custom_llm_error", error=str(e))
        return {
            "response": "I apologize, I encountered an error. Please try asking again.",
            "error": str(e)
        }


@router.post("/llm-endpoint")
async def llm_endpoint(request: dict):
    """
    Custom LLM endpoint for Hume EVI (primary endpoint)

    This endpoint is called by Hume EVI when using CUSTOM_LANGUAGE_MODEL.
    It receives the conversation context and returns a response from
    our Gemini + Zep pipeline.

    Expected request format from Hume:
    {
        "messages": [
            {"role": "user", "content": "user message"},
            {"role": "assistant", "content": "previous response"}
        ],
        "context": {...}
    }

    Expected response format:
    {
        "response": "assistant response text"
    }
    """
    return await _handle_llm_request(request)


async def _generate_sse_response(messages: list):
    """
    Generate SSE-formatted streaming response compatible with Hume EVI.

    Streams response in OpenAI chat completions chunk format.
    """
    if not gemini_assistant:
        error_event = {
            "id": "error-1",
            "object": "chat.completion.chunk",
            "created": int(datetime.utcnow().timestamp()),
            "model": "gemini-2.0-flash",
            "choices": [{
                "index": 0,
                "delta": {"content": "I apologize, but the assistant is currently unavailable."},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(error_event)}\n\n"
        yield "data: [DONE]\n\n"
        return

    # Extract latest user message
    user_message = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            # Handle content that could be string or list of content blocks
            if isinstance(content, list):
                # Extract text from content blocks
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        user_message = block.get("text", "")
                        break
            else:
                user_message = content
            break

    if not user_message:
        error_event = {
            "id": "error-2",
            "object": "chat.completion.chunk",
            "created": int(datetime.utcnow().timestamp()),
            "model": "gemini-2.0-flash",
            "choices": [{
                "index": 0,
                "delta": {"content": "I didn't understand that. Could you rephrase?"},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(error_event)}\n\n"
        yield "data: [DONE]\n\n"
        return

    logger.info("sse_streaming_request", query=user_message[:100])

    try:
        # Get response from Gemini + Zep
        response_text = await gemini_assistant.process_query(user_message)

        # Stream response in chunks (simulating streaming for better UX)
        chunk_id = f"chatcmpl-{int(datetime.utcnow().timestamp())}"
        words = response_text.split()

        for i, word in enumerate(words):
            is_last = i == len(words) - 1
            chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(datetime.utcnow().timestamp()),
                "model": "gemini-2.0-flash",
                "choices": [{
                    "index": 0,
                    "delta": {"content": word + ("" if is_last else " ")},
                    "finish_reason": "stop" if is_last else None
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"

        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error("sse_streaming_error", error=str(e))
        error_event = {
            "id": "error-3",
            "object": "chat.completion.chunk",
            "created": int(datetime.utcnow().timestamp()),
            "model": "gemini-2.0-flash",
            "choices": [{
                "index": 0,
                "delta": {"content": "I apologize, I encountered an error. Please try again."},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(error_event)}\n\n"
        yield "data: [DONE]\n\n"


@router.post("/chat/completions")
async def custom_llm_endpoint_sse(request: Request):
    """
    SSE-compatible endpoint for Hume EVI Custom Language Model.

    Returns Server-Sent Events in OpenAI chat completions streaming format.
    This is the recommended endpoint for Hume EVI integration as it supports
    real-time streaming responses.

    Expected request format:
    {
        "messages": [
            {"role": "user", "content": "user message"},
            {"role": "assistant", "content": "previous response"}
        ],
        "stream": true  // Hume will typically set this
    }
    """
    try:
        request_json = await request.json()
    except Exception:
        request_json = {}

    messages = request_json.get("messages", [])

    return StreamingResponse(
        _generate_sse_response(messages),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/status")
async def service_status():
    """
    Detailed service status for debugging

    Returns information about all configured services and their readiness
    """
    return {
        "services": {
            "hume_evi": {
                "api_key_set": bool(HUME_API_KEY),
                "secret_key_set": bool(HUME_SECRET_KEY),
                "handler_initialized": hume_handler is not None,
                "client_ready": hume_handler is not None and hume_handler.client is not None
            },
            "zep_knowledge_graph": {
                "api_key_set": bool(ZEP_API_KEY),
                "client_initialized": zep_graph is not None,
                "client_ready": zep_graph is not None and zep_graph.client is not None
            },
            "gemini_llm": {
                "api_key_set": bool(GEMINI_API_KEY),
                "assistant_initialized": gemini_assistant is not None,
                "model_ready": gemini_assistant is not None and gemini_assistant.model is not None
            }
        },
        "overall_ready": all([
            hume_handler and hume_handler.client,
            gemini_assistant and gemini_assistant.model,
            zep_graph and zep_graph.client
        ]),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/access-token")
async def get_access_token(request: Optional[Dict[str, Any]] = None):
    """
    Generate Hume API access token for client-side voice interface

    This endpoint creates a short-lived access token that allows the frontend
    React component to connect directly to Hume's EVI service.

    Uses OAuth2 client credentials flow as per Hume API documentation.

    Returns:
        JSON with accessToken and expiresIn fields
    """
    if not HUME_API_KEY or not HUME_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Hume credentials not configured"
        )

    try:
        import base64
        import httpx

        # Create Basic auth credentials (API key:Secret key base64 encoded)
        credentials = f"{HUME_API_KEY}:{HUME_SECRET_KEY}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        # OAuth2 client credentials flow
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.hume.ai/oauth2-cc/token",
                headers={
                    "Authorization": f"Basic {encoded_credentials}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={"grant_type": "client_credentials"}
            )
            response.raise_for_status()
            token_data = response.json()

        logger.info("access_token_generated")

        return {
            "accessToken": token_data["access_token"],
            "expiresIn": token_data.get("expires_in", 1800)  # Default 30 minutes
        }

    except httpx.HTTPStatusError as e:
        logger.error("access_token_http_error", status=e.response.status_code, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate access token: HTTP {e.response.status_code}"
        )
    except Exception as e:
        logger.error("access_token_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate access token: {str(e)}"
        )


# ============================================================================
# RELATED CONTENT ENDPOINT (for facts panel)
# ============================================================================

@router.post("/related-content")
async def get_related_content(request: Request):
    """
    Fetch related content (articles, companies, countries) for a given query.
    This is used to display a "facts panel" below the voice widget.

    Also handles ZEP memory - stores conversation messages for context continuity.

    Returns structured data that can be displayed in the UI.
    """
    try:
        body = await request.json()
        query = body.get("query", "")
        session_id = body.get("session_id")
        messages = body.get("messages", [])

        if not query:
            return {"articles": [], "companies": [], "countries": [], "external": [], "memory_context": None}

        logger.info("related_content_request", query=query, session_id=session_id, message_count=len(messages))

        # AI-powered topic extraction with categorization
        ai_topics = []
        ai_country = None
        categorized_facts = {
            "visa": {"icon": "🛂", "color": "#3b82f6", "label": "Visa & Immigration", "facts": [], "links": []},
            "tax": {"icon": "💰", "color": "#10b981", "label": "Tax & Finance", "facts": [], "links": []},
            "cost_of_living": {"icon": "🏠", "color": "#f59e0b", "label": "Cost of Living", "facts": [], "links": []},
            "companies": {"icon": "🏢", "color": "#8b5cf6", "label": "Service Providers", "facts": [], "links": []},
            "education": {"icon": "🎓", "color": "#ec4899", "label": "Education", "facts": [], "links": []},
            "healthcare": {"icon": "🏥", "color": "#ef4444", "label": "Healthcare", "facts": [], "links": []},
            "lifestyle": {"icon": "🌴", "color": "#06b6d4", "label": "Lifestyle", "facts": [], "links": []},
            "general": {"icon": "📋", "color": "#6b7280", "label": "General Info", "facts": [], "links": []}
        }

        if gemini_assistant and gemini_assistant.model:
            try:
                extraction_prompt = f"""Analyze this relocation query and categorize the topics.

User query: "{query}"

Return JSON with:
1. "country": country mentioned (or null)
2. "categories": array of relevant categories from: visa, tax, cost_of_living, companies, education, healthcare, lifestyle, general
3. "zep_queries": array of 2-3 specific search queries for a knowledge base

Only return valid JSON. Example:
{{"country": "Cyprus", "categories": ["tax", "companies"], "zep_queries": ["Cyprus corporation tax rate", "relocation companies Cyprus"]}}"""

                response = gemini_assistant.model.generate_content(extraction_prompt)
                if response and response.text:
                    import re
                    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if json_match:
                        extracted = json.loads(json_match.group())
                        ai_topics = extracted.get("categories", [])
                        ai_country = extracted.get("country")
                        ai_zep_queries = extracted.get("zep_queries", [])
                        logger.info("ai_topic_extraction", topics=ai_topics, country=ai_country, zep_queries=ai_zep_queries)

                        # Query ZEP and categorize facts
                        if ai_zep_queries and zep_graph and zep_graph.client:
                            for zep_query in ai_zep_queries[:3]:
                                try:
                                    results = await zep_graph.search(zep_query)
                                    if results.get("success") and results.get("edges"):
                                        for edge in results["edges"][:3]:
                                            fact = edge.get("fact", "")
                                            if fact:
                                                # Categorize fact based on content
                                                fact_lower = fact.lower()
                                                category = "general"
                                                if any(w in fact_lower for w in ["visa", "permit", "immigration", "residency"]):
                                                    category = "visa"
                                                elif any(w in fact_lower for w in ["tax", "corporate", "income", "vat", "financial"]):
                                                    category = "tax"
                                                elif any(w in fact_lower for w in ["cost", "rent", "living", "expense", "price"]):
                                                    category = "cost_of_living"
                                                elif any(w in fact_lower for w in ["company", "service", "relocat", "specialist"]):
                                                    category = "companies"
                                                elif any(w in fact_lower for w in ["school", "education", "university"]):
                                                    category = "education"
                                                elif any(w in fact_lower for w in ["health", "hospital", "medical"]):
                                                    category = "healthcare"
                                                elif any(w in fact_lower for w in ["lifestyle", "culture", "weather", "beach"]):
                                                    category = "lifestyle"

                                                if fact not in categorized_facts[category]["facts"]:
                                                    categorized_facts[category]["facts"].append(fact)
                                except Exception as e:
                                    logger.warning("zep_query_error", error=str(e), query=zep_query)
            except Exception as e:
                logger.warning("ai_extraction_error", error=str(e))

        # Handle ZEP memory if session_id provided
        memory_context = None
        if session_id and zep_graph and zep_graph.client:
            try:
                thread_id = f"relocation_{session_id}"

                # Try to get existing thread context
                try:
                    memory = zep_graph.client.thread.get_user_context(thread_id=thread_id)
                    if memory and hasattr(memory, 'context') and memory.context:
                        memory_context = memory.context
                        logger.info("zep_memory_retrieved", thread_id=thread_id)
                except Exception:
                    # Thread doesn't exist yet, create it
                    try:
                        zep_graph.client.thread.create(thread_id=thread_id)
                        logger.info("zep_thread_created", thread_id=thread_id)
                    except Exception as e:
                        logger.warning("zep_thread_create_error", error=str(e))

                # Store new messages in ZEP
                if messages and len(messages) >= 2:
                    # Get last user and assistant message pair
                    last_messages = messages[-2:] if len(messages) >= 2 else messages
                    zep_messages = [
                        {"role": m.get("role", "user"), "content": m.get("content", "")}
                        for m in last_messages
                    ]
                    try:
                        zep_graph.client.thread.add_messages(thread_id=thread_id, messages=zep_messages)
                        logger.info("zep_messages_stored", thread_id=thread_id, count=len(zep_messages))
                    except Exception as e:
                        logger.warning("zep_message_store_error", error=str(e))

            except Exception as e:
                logger.warning("zep_memory_error", error=str(e), session_id=session_id)

        # Initialize Neon store
        neon_store = None
        if DATABASE_URL:
            neon_store = NeonKnowledgeStore(DATABASE_URL)

        articles = []
        companies = []
        countries = []

        if neon_store:
            # Fetch from database
            country_results = await neon_store.search_countries(query)
            article_results = await neon_store.search_articles(query)
            company_results = await neon_store.search_companies(query)

            # Format countries
            for c in country_results:
                countries.append({
                    "name": c.get("name"),
                    "flag": c.get("flag_emoji", "🌍"),
                    "url": f"/countries/{c.get('slug', c.get('name', '').lower().replace(' ', '-'))}",
                    "region": c.get("region"),
                    "capital": c.get("capital"),
                    "highlights": c.get("motivations", [])[:3]
                })

            # Format articles with abbreviated names
            for a in article_results:
                full_title = a.get("title", "")
                # Create short name: remove common suffixes, truncate
                short_title = full_title
                for suffix in [": Complete Expat Guide", ": What Expats Need to Know", ": Step-by-Step Guide", " 2025", " 2024", " Guide"]:
                    short_title = short_title.replace(suffix, "")
                if len(short_title) > 35:
                    short_title = short_title[:32] + "..."

                articles.append({
                    "title": full_title,
                    "short_title": short_title,
                    "url": f"/{a.get('slug', '')}",
                    "excerpt": (a.get("excerpt") or a.get("description", ""))[:150],
                    "type": a.get("article_type", "guide")
                })

            # Format companies
            for co in company_results:
                companies.append({
                    "name": co.get("name"),
                    "url": f"/companies/{co.get('slug', '')}",
                    "description": (co.get("description") or co.get("overview", ""))[:100],
                    "services": co.get("services", [])[:3]
                })

        # Suggest external resources based on query keywords
        external = []
        query_lower = query.lower()

        if any(word in query_lower for word in ["visa", "permit", "immigration"]):
            external.append({
                "title": "Official Immigration Portals",
                "description": "Always verify visa requirements with official government sources",
                "type": "government"
            })

        if any(word in query_lower for word in ["cost", "living", "rent", "salary", "expensive"]):
            external.append({
                "title": "Numbeo Cost of Living",
                "url": "https://www.numbeo.com/cost-of-living/",
                "description": "Compare cost of living data worldwide",
                "type": "reference"
            })

        if any(word in query_lower for word in ["expat", "community", "moving", "relocate"]):
            external.append({
                "title": "InterNations Expat Community",
                "url": "https://www.internations.org/",
                "description": "Connect with expats and get local insights",
                "type": "community"
            })

        if any(word in query_lower for word in ["school", "education", "kids", "children", "university"]):
            external.append({
                "title": "International Schools Database",
                "url": "https://www.international-schools-database.com/",
                "description": "Find international schools worldwide",
                "type": "education"
            })

        if any(word in query_lower for word in ["health", "hospital", "doctor", "medical", "healthcare"]):
            external.append({
                "title": "Healthcare Resources",
                "description": "Research local healthcare systems and insurance options",
                "type": "healthcare"
            })

        if any(word in query_lower for word in ["job", "work", "career", "employment", "remote"]):
            external.append({
                "title": "Remote Job Boards",
                "url": "https://weworkremotely.com/",
                "description": "Find remote-friendly employers",
                "type": "employment"
            })

        if any(word in query_lower for word in ["bank", "banking", "finance", "money", "transfer"]):
            external.append({
                "title": "Wise (TransferWise)",
                "url": "https://wise.com/",
                "description": "International money transfers and multi-currency accounts",
                "type": "finance"
            })

        # Add relevant links to each category from articles
        for article in articles[:8]:
            title_lower = article.get("title", "").lower()
            slug = article.get("url", "")

            link_data = {
                "title": article.get("short_title") or article.get("title"),
                "url": f"https://relocation.quest{slug}",
                "type": "article"
            }

            if any(w in title_lower for w in ["visa", "permit", "immigration"]):
                categorized_facts["visa"]["links"].append(link_data)
            elif any(w in title_lower for w in ["tax", "corporate", "income"]):
                categorized_facts["tax"]["links"].append(link_data)
            elif any(w in title_lower for w in ["cost", "living", "rent"]):
                categorized_facts["cost_of_living"]["links"].append(link_data)

        # Add companies to the companies category
        for company in companies[:5]:
            categorized_facts["companies"]["links"].append({
                "title": company.get("name"),
                "url": f"https://relocation.quest{company.get('url', '')}",
                "type": "company"
            })

        # Add country guide link
        for country in countries[:1]:
            categorized_facts["general"]["links"].append({
                "title": f"{country.get('name')} Country Guide",
                "url": f"https://relocation.quest{country.get('url', '')}",
                "type": "country"
            })

        # Add external links to appropriate categories
        for ext in external:
            ext_type = ext.get("type", "")
            if ext_type == "education":
                categorized_facts["education"]["links"].append({"title": ext["title"], "url": ext.get("url"), "type": "external"})
            elif ext_type == "healthcare":
                categorized_facts["healthcare"]["links"].append({"title": ext["title"], "url": ext.get("url"), "type": "external"})
            elif ext_type in ["finance", "reference"]:
                categorized_facts["tax"]["links"].append({"title": ext["title"], "url": ext.get("url"), "type": "external"})
            elif ext_type == "government":
                categorized_facts["visa"]["links"].append({"title": ext["title"], "url": ext.get("url"), "type": "external"})
            elif ext_type == "community":
                categorized_facts["lifestyle"]["links"].append({"title": ext["title"], "url": ext.get("url"), "type": "external"})

        # Filter to only categories with content
        active_categories = {
            k: v for k, v in categorized_facts.items()
            if v["facts"] or v["links"]
        }

        logger.info("related_content_found",
                   articles=len(articles),
                   companies=len(companies),
                   countries=len(countries),
                   active_categories=list(active_categories.keys()))

        return {
            "articles": articles[:8],
            "companies": companies[:5],
            "countries": countries[:3],
            "external": external,
            "memory_context": memory_context,
            "categorized_facts": active_categories,  # New categorized structure
            "topics": ai_topics,
            "country": ai_country
        }

    except Exception as e:
        logger.error("related_content_error", error=str(e))
        return {"articles": [], "companies": [], "countries": [], "external": [], "memory_context": None, "categorized_facts": {}, "topics": [], "country": None}
