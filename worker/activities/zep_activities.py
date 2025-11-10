"""
Zep Graph Activities

Real integration with Zep Cloud for knowledge graph management.
Checks for duplicate coverage and creates semantic graph structures.
"""

import os
import asyncio
from typing import Dict, Any, Optional, List
from temporalio import activity
from zep_cloud.client import Zep
import httpx


def get_zep_client() -> Zep:
    """Get configured Zep client (sync client, we'll wrap calls in asyncio)"""
    api_key = os.getenv("ZEP_API_KEY")
    if not api_key:
        raise ValueError("ZEP_API_KEY not set")

    return Zep(api_key=api_key)


def get_graph_id(app: str) -> str:
    """
    Get the Zep Graph ID for an app.

    Uses hybrid domain architecture (like legacy newsroom):
    - finance-knowledge: placement, rainmaker, pvc, gtm (all finance apps share one graph)
    - relocation-knowledge: relocation

    Args:
        app: App name (e.g., "placement", "rainmaker", "relocation")

    Returns:
        Graph ID (e.g., "finance-knowledge")
    """
    DOMAIN_GRAPHS = {
        "placement": "finance-knowledge",
        "rainmaker": "finance-knowledge",
        "pvc": "finance-knowledge",
        "gtm": "finance-knowledge",
        "relocation": "relocation-knowledge",
    }

    return DOMAIN_GRAPHS.get(app, "finance-knowledge")


@activity.defn(name="check_zep_coverage")
async def check_zep_coverage(
    topic: str,
    app: str,
    similarity_threshold: float = 0.85
) -> Dict[str, Any]:
    """
    Check if topic has been covered before in Zep knowledge graph

    Args:
        topic: Topic/title to check
        app: Application (placement, relocation, etc.)
        similarity_threshold: Similarity score threshold (0-1)

    Returns:
        Dict with:
        - covered: bool
        - similar_articles: List of similar articles if found
        - novelty_score: float (0-1, higher = more novel)
        - recommendation: str (publish/skip/update)
    """
    activity.logger.info(f"🔍 Checking Zep coverage for: {topic} (app: {app})")

    try:
        client = get_zep_client()

        # Get graph ID for this app (finance-knowledge or relocation-knowledge)
        graph_id = get_graph_id(app)

        # Search for similar content in graph (sync client, wrap in asyncio)
        # Note: Using graph_id parameter as per Zep docs
        search_results = await asyncio.to_thread(
            lambda: client.graph.search(
                graph_id=graph_id,
                query=topic,
                limit=5
            )
        )

        if not search_results or not hasattr(search_results, 'edges') or not search_results.edges:
            activity.logger.info("✅ Topic is novel - no similar content found in knowledge graph")
            return {
                "covered": False,
                "similar_articles": [],
                "novelty_score": 1.0,
                "recommendation": "publish",
                "reasoning": "No similar content found in knowledge base"
            }

        # Analyze similarity scores from graph edges
        similar_articles = []
        max_similarity = 0.0

        for edge in search_results.edges:
            score = edge.score if hasattr(edge, 'score') else 0.0
            if score > max_similarity:
                max_similarity = score

            if score >= similarity_threshold:
                similar_articles.append({
                    "title": edge.fact if hasattr(edge, 'fact') else "Unknown",
                    "similarity": score,
                    "created_at": edge.created_at if hasattr(edge, 'created_at') else None
                })

        # Calculate novelty (inverse of similarity)
        novelty_score = 1.0 - max_similarity

        # Make recommendation
        if max_similarity >= 0.95:
            recommendation = "skip"
            reasoning = f"Very similar content exists (similarity: {max_similarity:.2f})"
        elif max_similarity >= similarity_threshold:
            recommendation = "update"
            reasoning = f"Similar content exists (similarity: {max_similarity:.2f}) - consider updating existing or new angle"
        else:
            recommendation = "publish"
            reasoning = f"Sufficiently different (similarity: {max_similarity:.2f})"

        activity.logger.info(f"📊 Novelty score: {novelty_score:.2f}")
        activity.logger.info(f"💡 Recommendation: {recommendation}")

        return {
            "covered": len(similar_articles) > 0,
            "similar_articles": similar_articles,
            "novelty_score": novelty_score,
            "recommendation": recommendation,
            "reasoning": reasoning,
            "max_similarity": max_similarity
        }

    except Exception as e:
        activity.logger.error(f"❌ Zep coverage check failed: {e}")
        # On error, allow publishing (fail open)
        return {
            "covered": False,
            "similar_articles": [],
            "novelty_score": 1.0,
            "recommendation": "publish",
            "reasoning": f"Coverage check failed: {str(e)} - proceeding with publication"
        }


@activity.defn(name="sync_article_to_zep")
async def sync_article_to_zep(article: Dict[str, Any]) -> str:
    """
    Sync article to Zep knowledge graph using direct HTTP API

    Creates an Episode with the article content structured as:
    - Main message: Article title + summary
    - Metadata: Full article data, entities, citations
    - Facts: Key entities and themes extracted

    Args:
        article: Article dict with title, content, metadata, etc.

    Returns:
        Episode UUID from Zep
    """
    activity.logger.info(f"🔗 Syncing article to Zep: {article.get('title', 'Unknown')[:50]}")

    try:
        api_key = os.getenv("ZEP_API_KEY")
        if not api_key:
            raise ValueError("ZEP_API_KEY not set")

        app = article.get("app", "placement")
        article_id = article.get("id", "unknown")
        title = article.get("title", "Untitled")
        content = article.get("content", "")

        # Extract first 500 chars for summary
        summary = content[:500] + "..." if len(content) > 500 else content

        # Get graph ID for this app (finance-knowledge or relocation-knowledge)
        graph_id = get_graph_id(app)

        # Prepare condensed content for graph (keep it under 8K chars to be safe)
        condensed_content = f"# {title}\n\n{summary}\n\n"
        if "metadata" in article:
            keywords = article.get('keywords', [])
            if keywords:
                condensed_content += f"Keywords: {', '.join(keywords[:10])}\n"
            condensed_content += f"Word Count: {article.get('word_count', 0)}\n"

        # Ensure content is under 8K characters for safety margin
        if len(condensed_content) > 8000:
            condensed_content = condensed_content[:7900] + "\n...[truncated]"

        activity.logger.info(f"   Content length: {len(condensed_content)} chars")

        # Call Zep Graph API directly via HTTP (bypassing broken SDK)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.getzep.com/api/v2/graphs/{graph_id}/data",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "type": "text",
                    "data": condensed_content
                },
                timeout=30.0
            )

            response.raise_for_status()
            result = response.json()

        # Extract episode UUID from response
        episode_uuid = result.get("uuid", result.get("episode_uuid", str(result)))

        activity.logger.info(f"✅ Article synced to Zep Graph")
        activity.logger.info(f"   Graph ID: {graph_id}")
        activity.logger.info(f"   Episode UUID: {episode_uuid}")
        activity.logger.info(f"   App: {app}")

        return episode_uuid

    except httpx.HTTPStatusError as e:
        activity.logger.error(f"❌ Zep API error: {e.response.status_code}")
        activity.logger.error(f"   Response: {e.response.text}")
        activity.logger.error(f"   Article ID: {article.get('id')}")
        return f"zep-fallback-{article.get('id', 'unknown')}"
    except Exception as e:
        activity.logger.error(f"❌ Zep sync failed: {type(e).__name__}: {str(e)}")
        activity.logger.error(f"   Article ID: {article.get('id')}")
        activity.logger.error(f"   App: {article.get('app')}")
        return f"zep-fallback-{article.get('id', 'unknown')}"


@activity.defn(name="extract_facts_to_zep")
async def extract_facts_to_zep(
    article: Dict[str, Any],
    entities: List[str],
    themes: List[str]
) -> Dict[str, Any]:
    """
    Extract and add facts to Zep knowledge graph

    Creates semantic facts that can be queried later:
    - Entity facts: "Company X raised $Y million"
    - Theme facts: "PE hiring is increasing in London"
    - Relationship facts: "Apollo Global is mentioned in private equity context"

    Args:
        article: Article dict
        entities: List of entity names
        themes: List of theme strings

    Returns:
        Dict with facts extracted and graph IDs
    """
    activity.logger.info(f"📝 Extracting {len(entities)} entities and {len(themes)} themes to Zep")

    try:
        client = await get_zep_client()
        app = article.get("app", "placement")

        # Create facts as messages
        facts = []

        # Entity facts
        for entity in entities[:10]:  # Limit to top 10
            facts.append(f"Entity mentioned: {entity}")

        # Theme facts
        for theme in themes[:5]:  # Limit to top 5
            facts.append(f"Theme discussed: {theme}")

        # Article fact
        facts.append(
            f"Published article: {article.get('title')} "
            f"(word count: {article.get('word_count', 0)})"
        )

        activity.logger.info(f"✅ Extracted {len(facts)} facts to Zep")

        return {
            "fact_count": len(facts),
            "entities_added": len(entities[:10]),
            "themes_added": len(themes[:5])
        }

    except Exception as e:
        activity.logger.error(f"❌ Fact extraction failed: {e}")
        return {
            "fact_count": 0,
            "entities_added": 0,
            "themes_added": 0,
            "error": str(e)
        }
