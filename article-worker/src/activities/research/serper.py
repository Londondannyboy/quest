"""
Serper News Search for Articles

Google search for news articles related to topic.
"""

from __future__ import annotations
from temporalio import activity
import httpx
import os


@activity.defn
async def fetch_topic_news(
    topic: str,
    app: str,
    jurisdiction: str | None,
    num_sources: int = 10
) -> dict:
    """
    Fetch news articles about topic using Serper.dev.

    Args:
        topic: Article topic
        app: App context
        jurisdiction: Optional jurisdiction for geo-targeting
        num_sources: Number of sources to fetch

    Returns:
        Dict with articles, cost, num_queries
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        activity.logger.warning("SERPER_API_KEY not set")
        return {"articles": [], "cost": 0.0, "num_queries": 0}

    # Build queries
    queries = []

    # Query 1: Topic + news
    query1 = f"{topic} news"
    if jurisdiction:
        query1 += f" {jurisdiction}"
    queries.append(query1)

    # Query 2: Topic + app context
    query2 = f"{topic} {app}"
    queries.append(query2)

    all_articles = []
    total_cost = 0.0
    seen_urls = set()

    try:
        async with httpx.AsyncClient() as client:
            for query in queries:
                activity.logger.info(f"Searching: {query}")

                response = await client.post(
                    "https://google.serper.dev/search",
                    json={
                        "q": query,
                        "num": min(num_sources, 10),
                        "gl": jurisdiction.lower() if jurisdiction else "us"
                    },
                    headers={
                        "X-API-KEY": api_key,
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    total_cost += 0.02  # $0.02 per query

                    for item in data.get("organic", [])[:num_sources]:
                        url = item.get("link")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            all_articles.append({
                                "title": item.get("title", ""),
                                "snippet": item.get("snippet", ""),
                                "url": url,
                                "date": item.get("date")
                            })

                    activity.logger.info(f"Found {len(data.get('organic', []))} results")

    except Exception as e:
        activity.logger.error(f"Serper search failed: {e}")

    activity.logger.info(f"Total articles found: {len(all_articles)}, cost: ${total_cost:.4f}")

    return {
        "articles": all_articles[:num_sources],
        "cost": total_cost,
        "num_queries": len(queries)
    }
