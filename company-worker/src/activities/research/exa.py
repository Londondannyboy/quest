"""
Exa Research Activity

High-quality company research using Exa's neural search.
Cost: $0.04 per query
"""

from temporalio import activity
from typing import Dict, Any
from exa_py import Exa

from src.utils.config import config


@activity.defn
async def exa_research_company(
    domain: str,
    company_name: str,
    category: str
) -> Dict[str, Any]:
    """
    Deep company research using Exa.

    Exa provides high-quality, AI-powered search that's better than
    Google for company research.

    Args:
        domain: Company domain
        company_name: Company name
        category: Company category

    Returns:
        Dict with results, cost, summary
    """
    activity.logger.info(f"Exa research for {company_name}")

    if not config.EXA_API_KEY:
        activity.logger.warning("EXA_API_KEY not configured")
        return {
            "results": [],
            "cost": 0.0,
            "summary": {},
            "error": "EXA_API_KEY not configured"
        }

    try:
        exa = Exa(api_key=config.EXA_API_KEY)

        # Construct instructions for research
        category_clean = category.replace('_', ' ')
        instructions = f"{company_name} {category_clean}"

        activity.logger.info(f"Exa research instructions: {instructions}")

        # Use Exa Research API
        research = exa.research.create(
            instructions=instructions,
            model="exa-research"
        )

        # Get research results (streaming)
        research_content = []
        for event in exa.research.get(research.research_id, stream=True):
            research_content.append(str(event))

        # Combine all research content
        full_research = "\n".join(research_content)

        # Build results structure
        results = [{
            "url": f"https://{domain}",
            "title": f"Exa Research: {company_name}",
            "content": full_research[:5000],  # Limit to 5000 chars
            "highlights": [],
            "published_date": None,
            "score": 1.0,  # Research is always high confidence
            "source": "exa-research"
        }]

        # Extract key facts
        summary = {
            "company_name": company_name,
            "found_information": len(full_research) > 0,
            "avg_score": 1.0,
            "key_topics": [],
            "source_count": 1,
            "research_length": len(full_research)
        }

        activity.logger.info(
            f"Exa research complete: {len(full_research)} chars, cost: $0.04"
        )

        return {
            "results": results,
            "cost": 0.04,
            "summary": summary,
            "query": instructions,
            "research_id": research.research_id
        }

    except Exception as e:
        activity.logger.error(f"Exa research failed: {e}")
        return {
            "results": [],
            "cost": 0.04,  # Still charged even on error
            "summary": {},
            "error": str(e)
        }


def extract_key_facts_from_exa(
    results: list[Dict[str, Any]],
    company_name: str
) -> Dict[str, Any]:
    """
    Extract key facts from Exa results.

    Args:
        results: Exa search results
        company_name: Company name

    Returns:
        Dict with extracted facts
    """
    facts = {
        "company_name": company_name,
        "found_information": len(results) > 0,
        "avg_score": 0.0,
        "key_topics": [],
        "source_count": len(results)
    }

    if not results:
        return facts

    # Calculate average score
    scores = [r.get("score", 0.0) for r in results]
    facts["avg_score"] = sum(scores) / len(scores) if scores else 0.0

    # Extract common topics from highlights
    all_highlights = []
    for result in results:
        highlights = result.get("highlights", [])
        all_highlights.extend(highlights)

    # Simple keyword extraction (in production, use NLP)
    common_words = set()
    for highlight in all_highlights:
        words = highlight.lower().split()
        # Filter for interesting words (length > 5)
        common_words.update(w for w in words if len(w) > 5)

    facts["key_topics"] = list(common_words)[:10]

    return facts


@activity.defn
async def exa_find_similar_companies(
    domain: str,
    company_name: str,
    num_results: int = 5
) -> Dict[str, Any]:
    """
    Find similar companies using Exa's find_similar feature.

    Args:
        domain: Company domain
        company_name: Company name
        num_results: Number of similar companies to find

    Returns:
        Dict with similar companies
    """
    activity.logger.info(f"Finding companies similar to {company_name}")

    if not config.EXA_API_KEY:
        return {
            "similar_companies": [],
            "cost": 0.0,
            "error": "EXA_API_KEY not configured"
        }

    try:
        exa = Exa(api_key=config.EXA_API_KEY)

        # Find similar based on domain
        url = f"https://{domain}" if not domain.startswith('http') else domain

        response = exa.find_similar(
            url=url,
            num_results=num_results
        )

        similar = [
            {
                "url": item.url,
                "title": item.title,
                "score": getattr(item, 'score', 0.0)
            }
            for item in response.results
        ]

        activity.logger.info(f"Found {len(similar)} similar companies")

        return {
            "similar_companies": similar,
            "cost": 0.04
        }

    except Exception as e:
        activity.logger.error(f"Exa find_similar failed: {e}")
        return {
            "similar_companies": [],
            "cost": 0.04,
            "error": str(e)
        }
