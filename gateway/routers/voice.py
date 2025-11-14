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

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.responses import JSONResponse
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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ============================================================================
# ZEP KNOWLEDGE GRAPH INTEGRATION
# ============================================================================

class ZepKnowledgeGraph:
    """Interface to Zep knowledge graph for Quest project"""

    def __init__(self, api_key: str, project_id: str):
        self.api_key = api_key
        self.project_id = project_id
        try:
            from zep_cloud.client import Zep
            self.client = Zep(api_key=api_key)
            logger.info("zep_client_initialized", project_id=project_id)
        except ImportError:
            logger.warning("zep-cloud package not installed")
            self.client = None
        except Exception as e:
            logger.error("zep_init_error", error=str(e))
            self.client = None

    async def search(self, query: str, user_id: str = "quest") -> dict:
        """
        Search the knowledge graph for relevant relocation information

        Args:
            query: Search query about relocation
            user_id: User identifier for personalization

        Returns:
            Dictionary with search results
        """
        if not self.client:
            return {
                "error": "Zep client not initialized",
                "results": [],
                "success": False
            }

        try:
            # Search for edges (relationships) which contain rich context
            results = self.client.graph.search(
                user_id=user_id,
                query=query,
                scope="edges",
            )

            formatted_results = {
                "query": query,
                "results": [],
                "success": True
            }

            if hasattr(results, 'edges') and results.edges:
                for edge in results.edges[:5]:  # Top 5 most relevant
                    formatted_results["results"].append({
                        "fact": edge.fact if hasattr(edge, 'fact') else str(edge),
                        "relevance": edge.score if hasattr(edge, 'score') else 1.0
                    })
                logger.info("zep_search_success", query=query, count=len(formatted_results["results"]))
            else:
                logger.info("zep_search_no_results", query=query)

            return formatted_results

        except Exception as e:
            logger.error("zep_search_error", error=str(e), query=query)
            return {
                "error": str(e),
                "query": query,
                "results": [],
                "success": False
            }


# ============================================================================
# GEMINI LLM INTEGRATION
# ============================================================================

class GeminiAssistant:
    """Gemini LLM for processing queries with Zep knowledge graph context"""

    def __init__(self, api_key: str, zep_graph: ZepKnowledgeGraph):
        self.api_key = api_key
        self.zep_graph = zep_graph

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

    async def process_query(self, query: str, user_id: str = "relocation_user") -> str:
        """
        Process a relocation query using Gemini + Zep knowledge graph

        Args:
            query: User's question about relocation
            user_id: User identifier

        Returns:
            Generated response text optimized for voice
        """
        if not self.model:
            return "I apologize, but the assistant is currently unavailable. Please try again later."

        try:
            # Search knowledge graph for relevant context
            kg_results = await self.zep_graph.search(query, user_id)

            # Build context from knowledge graph
            context = ""
            if kg_results.get("success") and kg_results.get("results"):
                context = "\n\nRelevant information from the knowledge base:\n"
                for result in kg_results["results"]:
                    context += f"- {result['fact']}\n"
                logger.info("using_kg_context", facts_count=len(kg_results["results"]))

            # System prompt optimized for voice interaction
            system_prompt = """You are a helpful relocation assistant for relocation.quest.
You help people with questions about international relocation, corporate mobility,
visa requirements, cost of living, and moving to new countries.

IMPORTANT GUIDELINES FOR VOICE RESPONSES:
- Keep responses under 100 words (this is voice interaction)
- Be conversational and natural
- Use simple language, avoid jargon
- Provide specific, actionable information
- If you don't know something, say so briefly
- Suggest they visit relocation.quest for more detailed information

TONE:
- Friendly and supportive
- Professional but not stuffy
- Empathetic to relocation challenges
"""

            # Generate response
            full_prompt = f"{system_prompt}\n\nUser question: {query}{context}\n\nProvide a brief, conversational voice response:"

            response = self.model.generate_content(full_prompt)

            if response and response.text:
                logger.info("gemini_response_generated", query=query, length=len(response.text))
                return response.text
            else:
                return "I'm having trouble generating a response. Could you rephrase your question?"

        except Exception as e:
            logger.error("gemini_error", error=str(e), query=query)
            return "I apologize, I encountered an error. Please try asking your question again."


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
                    response = await self.assistant.process_query(query_text, user_id)

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
gemini_assistant = None
hume_handler = None

if ZEP_API_KEY and ZEP_PROJECT_ID:
    zep_graph = ZepKnowledgeGraph(ZEP_API_KEY, ZEP_PROJECT_ID)

if GEMINI_API_KEY and zep_graph:
    gemini_assistant = GeminiAssistant(GEMINI_API_KEY, zep_graph)

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
                response = await assistant.process_query(query_text, user_id)

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

    response = await gemini_assistant.process_query(query, user_id)

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
        context = request.get("context", {})
        user_id = context.get("user_id", "hume_user")

        logger.info("hume_llm_request", query=user_message, user_id=user_id)

        # Process through Gemini + Zep
        response = await gemini_assistant.process_query(user_message, user_id)

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


@router.post("/chat/completions")
async def custom_llm_endpoint(request: dict):
    """
    OpenAI-compatible endpoint alias (same as /llm-endpoint)

    Allows using standard OpenAI API format if needed.
    """
    return await _handle_llm_request(request)


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
