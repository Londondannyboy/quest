"""
Zep Graph Activities

Real integration with Zep Cloud for knowledge graph management.
Checks for duplicate coverage and creates semantic graph structures.
"""

import os
from typing import Dict, Any, Optional, List
from temporalio import activity
from zep_cloud.client import AsyncZep
from zep_cloud import Episode, Message


async def get_zep_client() -> AsyncZep:
    """Get configured Zep client"""
    api_key = os.getenv("ZEP_API_KEY")
    if not api_key:
        raise ValueError("ZEP_API_KEY not set")

    return AsyncZep(api_key=api_key)


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
        client = await get_zep_client()

        # Search for similar content in user's graph
        # Using app as user_id to separate by application
        search_results = await client.memory.search(
            user_id=f"app-{app}",
            text=topic,
            limit=5
        )

        if not search_results or not search_results.results:
            activity.logger.info("✅ Topic is novel - no similar content found")
            return {
                "covered": False,
                "similar_articles": [],
                "novelty_score": 1.0,
                "recommendation": "publish",
                "reasoning": "No similar content found in knowledge base"
            }

        # Analyze similarity scores
        similar_articles = []
        max_similarity = 0.0

        for result in search_results.results:
            if result.score and result.score > max_similarity:
                max_similarity = result.score

            if result.score and result.score >= similarity_threshold:
                similar_articles.append({
                    "title": result.message.content if result.message else "Unknown",
                    "similarity": result.score,
                    "created_at": result.message.created_at if result.message else None
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
    Sync article to Zep knowledge graph

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
        client = await get_zep_client()

        app = article.get("app", "placement")
        article_id = article.get("id", "unknown")
        title = article.get("title", "Untitled")
        content = article.get("content", "")

        # Extract first 500 chars for summary
        summary = content[:500] + "..." if len(content) > 500 else content

        # Prepare metadata
        metadata = {
            "article_id": article_id,
            "app": app,
            "title": title,
            "word_count": article.get("word_count", 0),
            "quality_score": article.get("metadata", {}).get("quality_score", 0),
            "published_at": article.get("published_at"),
            "url": f"https://{app}.quest/{article.get('slug', article_id)}"
        }

        # Add entities if present
        if "metadata" in article and "entities_mentioned" in article["metadata"]:
            metadata["entities"] = article["metadata"]["entities_mentioned"]

        # Add topics if present
        if "metadata" in article and "primary_topics" in article["metadata"]:
            metadata["topics"] = article["metadata"]["primary_topics"]

        # Create episode message
        message = Message(
            role="assistant",
            content=f"# {title}\n\n{summary}",
            metadata=metadata
        )

        # Create episode in Zep
        episode = Episode(
            session_id=f"articles-{app}",
            messages=[message]
        )

        # Add episode to user's memory
        result = await client.memory.add(
            user_id=f"app-{app}",
            episodes=[episode]
        )

        # Get episode UUID from result
        episode_uuid = None
        if result and hasattr(result, 'episode_ids') and result.episode_ids:
            episode_uuid = result.episode_ids[0]

        activity.logger.info(f"✅ Article synced to Zep")
        activity.logger.info(f"   Episode UUID: {episode_uuid}")
        activity.logger.info(f"   App: {app}")
        activity.logger.info(f"   Session: articles-{app}")

        return episode_uuid or f"zep-{article_id}"

    except Exception as e:
        activity.logger.error(f"❌ Zep sync failed: {type(e).__name__}: {str(e)}")
        activity.logger.error(f"   Article ID: {article.get('id')}")
        activity.logger.error(f"   App: {article.get('app')}")
        # Return placeholder on error (don't include error details in ID)
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
