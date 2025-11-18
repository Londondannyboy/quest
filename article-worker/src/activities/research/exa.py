"""
Exa Research for Articles

Deep AI-powered research using Exa API.
"""

from __future__ import annotations
from temporalio import activity
from exa_py import Exa
import os


@activity.defn
async def exa_research_topic(
    topic: str,
    app: str,
    target_word_count: int = 1500
) -> dict:
    """
    Perform deep research on topic using Exa.

    Args:
        topic: Article topic
        app: App context
        target_word_count: Target word count for article

    Returns:
        Dict with results, research_id, cost
    """
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        activity.logger.warning("EXA_API_KEY not set")
        return {"results": [], "cost": 0.0, "research_id": None}

    try:
        exa = Exa(api_key=api_key)

        activity.logger.info(f"Researching: {topic}")

        # Search for relevant content
        search_response = exa.search_and_contents(
            query=topic,
            type="auto",
            num_results=5,
            text={"max_characters": 2000},
            highlights=True
        )

        results = []
        for result in search_response.results:
            results.append({
                "title": result.title,
                "url": result.url,
                "text": result.text,
                "highlights": result.highlights if hasattr(result, 'highlights') else [],
                "score": result.score if hasattr(result, 'score') else 0.5
            })

        activity.logger.info(f"Exa research complete: {len(results)} results")

        return {
            "results": results,
            "cost": 0.04,  # Approximate cost
            "research_id": f"exa_{topic[:20]}"
        }

    except Exception as e:
        activity.logger.error(f"Exa research failed: {e}")
        return {"results": [], "cost": 0.0, "research_id": None}
