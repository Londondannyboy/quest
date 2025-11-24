"""
News Monitor Activities

Activities for scheduled news monitoring:
- Fetch news by keywords
- AI assessment for relevance
- Duplicate checking
"""

import httpx
from temporalio import activity
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from typing import Literal, Optional
import anthropic

from src.utils.config import config


# Geo-targeting map
GEO_MAP = {
    "UK": "uk",
    "US": "us",
    "EU": "de",
    "Asia": "sg",
}


# ============================================================================
# NEWS FETCH ACTIVITY
# ============================================================================

@activity.defn(name="serper_news_search")
async def fetch_news_for_keywords(
    keywords: List[str],
    geographic_focus: List[str],
    num_results: int = 20
) -> Dict[str, Any]:
    """
    Fetch news using Serper based on keywords and geographic focus.

    Args:
        keywords: List of search keywords
        geographic_focus: List of regions (UK, US, EU, Asia)
        num_results: Number of results to fetch

    Returns:
        Dict with articles, cost
    """
    activity.logger.info(f"Fetching news for keywords: {keywords[:3]}...")

    if not config.SERPER_API_KEY:
        return {
            "articles": [],
            "cost": 0.0,
            "error": "SERPER_API_KEY not configured"
        }

    # Build query from top keywords
    query = " OR ".join(keywords[:3])

    # Determine location from geographic focus
    gl = "us"  # Default
    if "UK" in geographic_focus:
        gl = "uk"
    elif "US" in geographic_focus:
        gl = "us"
    elif "EU" in geographic_focus:
        gl = "de"

    all_articles = []

    async with httpx.AsyncClient() as client:
        try:
            # Fetch news (not organic search)
            response = await client.post(
                "https://google.serper.dev/news",
                headers={
                    "X-API-KEY": config.SERPER_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "q": query,
                    "gl": gl,
                    "num": num_results,
                    "tbs": "qdr:d"  # Last day
                },
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                news_items = data.get("news", [])

                for item in news_items:
                    all_articles.append({
                        "url": item.get("link", ""),
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "source": item.get("source", ""),
                        "date": item.get("date", ""),
                    })

                activity.logger.info(f"Found {len(all_articles)} news articles")
            else:
                activity.logger.error(f"Serper news search failed: {response.status_code}")

        except Exception as e:
            activity.logger.error(f"News fetch error: {e}")

    return {
        "articles": all_articles,
        "query": query,
        "location": gl,
        "cost": 0.001  # Serper cost per request
    }


# ============================================================================
# NEWS ASSESSMENT ACTIVITY
# ============================================================================

@activity.defn(name="claude_assess_news")
async def assess_news_batch(
    stories: List[Dict[str, Any]],
    app: str,
    app_context: Dict[str, Any],
    recent_articles: List[Dict[str, Any]],
    min_relevance_score: float = 0.6
) -> Dict[str, Any]:
    """
    Assess a batch of news stories for relevance using Claude.

    Args:
        stories: List of news stories
        app: App name
        app_context: Full app config with keywords, exclusions, interests, target_audience
        recent_articles: Recently published articles (for duplicate check)
        min_relevance_score: Minimum score to be considered relevant

    Returns:
        Assessment results with relevant and skipped stories
    """
    activity.logger.info(f"Assessing {len(stories)} stories for app: {app}")

    if not config.ANTHROPIC_API_KEY:
        return {
            "stories_assessed": 0,
            "relevant_stories": [],
            "error": "ANTHROPIC_API_KEY not configured"
        }

    # Extract app context
    keywords = app_context.get("keywords", [])
    exclusions = app_context.get("exclusions", [])
    interests = app_context.get("interests", [])
    target_audience = app_context.get("target_audience", "")

    relevant_stories = []

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    for story in stories:
        try:
            # Build assessment prompt
            prompt = f"""Assess this news story for relevance to the {app} app.

STORY:
Title: {story.get('title', '')}
Source: {story.get('source', '')}
Date: {story.get('date', '')}
Snippet: {story.get('snippet', '')}

APP CONTEXT:
Target Audience: {target_audience}

WHAT IS RELEVANT (mark as relevant if story is about ANY of these):
- Private placements (companies raising capital via private placement)
- Fund placements and fundraising
- Placement agents and their deals
- LP commitments and institutional investments
- Private equity fundraising
- Capital raising announcements

Keywords to look for: {', '.join(keywords[:5])}

Topics to EXCLUDE (mark NOT relevant if story is primarily about):
{', '.join(exclusions)}

RECENT ARTICLES (avoid exact duplicates):
{chr(10).join([f"- {a.get('title', '')}" for a in recent_articles[:5]])}

Be INCLUSIVE - if the story mentions private placement, fundraising, or capital raising, it IS relevant.

Respond with JSON only:
{{
    "is_relevant": true/false,
    "relevance_score": 0.0-1.0,
    "priority": "high"/"medium"/"low",
    "reasoning": "brief explanation",
    "suggested_angle": "angle for article if relevant"
}}"""

            response = client.messages.create(
                model="claude-3-5-haiku-20241022",  # Much cheaper than Sonnet for classification
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            import json
            response_text = response.content[0].text

            # Extract JSON from response
            if "{" in response_text:
                json_str = response_text[response_text.find("{"):response_text.rfind("}")+1]
                assessment = json.loads(json_str)
            else:
                assessment = {"is_relevant": False, "relevance_score": 0.0}

            # Handle string "true"/"false" values
            is_relevant = assessment.get("is_relevant", False)
            if isinstance(is_relevant, str):
                is_relevant = is_relevant.lower() == "true"

            relevance_score = float(assessment.get("relevance_score", 0))

            activity.logger.info(
                f"Story: {story.get('title', '')[:40]}... "
                f"relevant={is_relevant}, score={relevance_score}"
            )

            if is_relevant and relevance_score >= min_relevance_score:
                relevant_stories.append({
                    "story": story,
                    "relevance_score": relevance_score,
                    "priority": assessment.get("priority", "low"),
                    "reasoning": assessment.get("reasoning", ""),
                    "suggested_angle": assessment.get("suggested_angle", "")
                })
                activity.logger.info(f"✅ Added as relevant: {story.get('title', '')[:50]}...")

        except Exception as e:
            activity.logger.error(f"Assessment error: {e}")
            continue

    # Sort by relevance score
    relevant_stories.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    activity.logger.info(f"Assessment complete: {len(relevant_stories)} relevant stories")

    return {
        "stories_assessed": len(stories),
        "relevant_stories": relevant_stories,
        "total_high_priority": len([s for s in relevant_stories if s.get("priority") == "high"]),
        "total_medium_priority": len([s for s in relevant_stories if s.get("priority") == "medium"]),
        "total_low_priority": len([s for s in relevant_stories if s.get("priority") == "low"])
    }


# ============================================================================
# RECENT ARTICLES CHECK
# ============================================================================

@activity.defn(name="neon_get_recent_articles")
async def get_recent_articles_from_neon(
    app: str,
    days: int = 7,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get recently published articles from Neon database.

    Args:
        app: App name
        days: How many days back to check
        limit: Maximum articles to return

    Returns:
        List of recent articles
    """
    import psycopg
    from datetime import datetime, timedelta

    activity.logger.info(f"Fetching recent articles for {app} (last {days} days)")

    if not config.DATABASE_URL:
        activity.logger.warning("DATABASE_URL not configured")
        return []

    try:
        async with await psycopg.AsyncConnection.connect(config.DATABASE_URL) as conn:
            async with conn.cursor() as cur:
                cutoff = datetime.utcnow() - timedelta(days=days)

                await cur.execute(
                    """
                    SELECT id, title, slug, article_type, created_at
                    FROM articles
                    WHERE app = %s
                    AND created_at >= %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (app, cutoff, limit)
                )

                rows = await cur.fetchall()

                articles = []
                for row in rows:
                    articles.append({
                        "id": str(row[0]),
                        "title": row[1],
                        "slug": row[2],
                        "article_type": row[3],
                        "created_at": row[4].isoformat() if row[4] else None
                    })

                activity.logger.info(f"Found {len(articles)} recent articles")
                return articles

    except Exception as e:
        activity.logger.error(f"Failed to fetch recent articles: {e}")
        return []
