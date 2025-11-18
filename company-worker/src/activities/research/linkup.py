"""
LinkUp Deep Research Activity

High-quality company research using LinkUp's Deep Research API.
Cost: $0.05 per deep research query
Provides synthesized answers with sources and snippets.
"""

from temporalio import activity
from typing import Dict, Any
from linkup import LinkupClient

from src.utils.config import config


@activity.defn
async def linkup_deep_research(
    query: str,
    company_name: str
) -> Dict[str, Any]:
    """
    Deep company research using LinkUp.

    LinkUp provides comprehensive research with synthesized answers,
    sources, and content snippets. Great fallback for Exa.

    Args:
        query: Research query (e.g., "Campbell Lutyens deals")
        company_name: Company name for context

    Returns:
        Dict with results, cost, summary
    """
    activity.logger.info(f"LinkUp deep research for: {query}")

    if not config.LINKUP_API_KEY:
        activity.logger.warning("LINKUP_API_KEY not configured")
        return {
            "results": [],
            "cost": 0.0,
            "summary": {},
            "error": "LINKUP_API_KEY not configured"
        }

    try:
        client = LinkupClient(api_key=config.LINKUP_API_KEY)

        activity.logger.info(f"Calling LinkUp deep research API")

        # Use Deep Research with sourcedAnswer output
        response = client.search(
            query=query,
            depth="deep",
            output_type="sourcedAnswer",
            include_images=False,
            include_inline_citations=False,
        )

        # Extract answer and sources
        answer = response.get("answer", "") if isinstance(response, dict) else getattr(response, "answer", "")
        sources = response.get("sources", []) if isinstance(response, dict) else getattr(response, "sources", [])

        # Convert to results format matching Exa structure
        results = []
        for source in sources[:10]:  # Limit to 10 sources
            results.append({
                "url": source.get("url", ""),
                "title": source.get("name", ""),
                "content": source.get("snippet", ""),
                "highlights": [source.get("snippet", "")],
                "published_date": None,
                "score": 1.0,
                "source": "linkup-deep-research"
            })

        # Add synthesized answer as first result
        if answer:
            results.insert(0, {
                "url": f"https://{company_name.lower().replace(' ', '-')}.com",
                "title": f"{company_name} - LinkUp Deep Research",
                "content": answer,
                "highlights": [],
                "published_date": None,
                "score": 1.0,
                "source": "linkup-synthesis"
            })

        summary = {
            "company_name": company_name,
            "found_information": len(results) > 0,
            "source_count": len(sources),
            "has_synthesis": bool(answer),
            "answer_length": len(answer)
        }

        activity.logger.info(
            f"LinkUp research complete: {len(results)} results, "
            f"{len(answer)} char synthesis, cost: $0.05"
        )

        return {
            "results": results,
            "cost": 0.05,
            "summary": summary,
            "answer": answer,
            "source_count": len(sources)
        }

    except Exception as e:
        activity.logger.error(f"LinkUp research failed: {e}")
        return {
            "results": [],
            "cost": 0.05,  # Still charged even on error
            "summary": {},
            "error": str(e)
        }
