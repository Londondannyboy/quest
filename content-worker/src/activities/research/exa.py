"""
Exa Research Activity

High-quality company research using Exa's neural search.
Cost: $0.04 per query

Falls back to LinkUp Deep Research ($0.05) if Exa fails.
"""

from temporalio import activity
from typing import Dict, Any
from exa_py import Exa

from src.utils.config import config

# Optional LinkUp import - if not available, fallback won't work but Exa will
linkup_deep_research = None
try:
    from src.activities.research.linkup import linkup_deep_research
except ImportError:
    pass


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

        # Use Exa Research API (exa-research model) with simple domain-based instructions
        # This matches the working pattern: exa.research.create(instructions="evercore.com")
        category_clean = category.replace('_', ' ')
        instructions = f"Research {domain} - a {category_clean} company named {company_name}. Provide comprehensive information including company overview, services, leadership, deal history, and key facts."

        activity.logger.info(f"Creating Exa research for {domain}")

        # Create research job
        research = exa.research.create(
            instructions=instructions,
            model="exa-research"
        )

        activity.logger.info(f"Research created with ID: {research.research_id}")

        # Stream events and collect content from task outputs
        all_events = []
        task_outputs = []

        for event in exa.research.get(research.research_id, stream=True):
            all_events.append(event)

            # Extract content from ResearchTaskOutputEvent (where the actual research is!)
            if hasattr(event, 'event_type') and event.event_type == 'task-output':
                if hasattr(event, 'output') and hasattr(event.output, 'content'):
                    content = event.output.content
                    task_outputs.append(content)
                    activity.logger.info(f"Collected task output: {len(content)} chars")

            activity.logger.debug(f"Received event type: {type(event).__name__}")

        # Compile all research outputs
        full_content = "\n\n---\n\n".join(task_outputs)

        results = [{
            "url": f"https://{domain}",
            "title": f"{company_name} Research",
            "content": full_content[:5000] if full_content else "",
            "highlights": [],
            "published_date": None,
            "score": 1.0,
            "source": "exa-research",
            "research_id": research.research_id
        }]

        # Extract key facts
        summary = extract_key_facts_from_exa(results, company_name)
        summary["research_id"] = research.research_id
        summary["event_count"] = len(all_events)
        summary["task_outputs"] = len(task_outputs)
        summary["content_length"] = len(full_content)

        activity.logger.info(
            f"Exa research complete: {len(task_outputs)} task outputs, {len(full_content)} chars total, cost: $0.04"
        )

        return {
            "results": results,
            "cost": 0.04,
            "summary": summary,
            "research_id": research.research_id
        }

    except Exception as e:
        activity.logger.error(f"Exa research failed: {e}")

        # Fallback to LinkUp if configured and available
        if config.LINKUP_API_KEY and linkup_deep_research:
            activity.logger.warning("Falling back to LinkUp Deep Research")
            try:
                # Build query for LinkUp
                category_clean = category.replace('_', ' ')
                query = f"{company_name} {category_clean} deals transactions"

                linkup_result = await linkup_deep_research(query, company_name)

                # Mark result as from fallback
                linkup_result["fallback_from"] = "exa"
                linkup_result["exa_error"] = str(e)

                activity.logger.info(f"LinkUp fallback successful: {len(linkup_result.get('results', []))} results")
                return linkup_result

            except Exception as linkup_error:
                activity.logger.error(f"LinkUp fallback also failed: {linkup_error}")
                return {
                    "results": [],
                    "cost": 0.04,  # Exa charges even on error
                    "summary": {},
                    "error": f"Exa failed: {str(e)}, LinkUp fallback failed: {str(linkup_error)}"
                }

        # No fallback available or not installed
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
async def exa_research_topic(
    topic: str,
    article_type: str = "news",
    app: str = "placement"
) -> Dict[str, Any]:
    """
    Deep topic research using Exa for article generation.

    Unlike exa_research_company which focuses on company profiles,
    this function researches topics for news/guides/comparisons.

    Args:
        topic: Research topic (e.g., "Cyprus Digital Nomad Visa")
        article_type: Type of article (news, guide, comparison)
        app: App context for tailored research

    Returns:
        Dict with results, cost, summary
    """
    activity.logger.info(f"Exa topic research: {topic} ({article_type} for {app})")

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

        # Build topic-appropriate instructions based on article type
        if article_type == "news":
            instructions = f"Research the latest news and developments about: {topic}. Find recent articles, announcements, statistics, expert opinions, and key facts. Focus on what's happening now and recent changes."
        elif article_type == "guide":
            instructions = f"Research comprehensive information about: {topic}. Find detailed guides, requirements, processes, costs, timelines, tips, and expert advice. Focus on practical, actionable information."
        elif article_type == "comparison":
            instructions = f"Research comparisons and analysis of: {topic}. Find comparative data, pros and cons, alternatives, rankings, and expert evaluations."
        else:
            instructions = f"Research: {topic}. Find comprehensive, authoritative information including facts, statistics, expert opinions, and recent developments."

        activity.logger.info(f"Creating Exa research for topic: {topic}")

        # Create research job
        research = exa.research.create(
            instructions=instructions,
            model="exa-research"
        )

        activity.logger.info(f"Research created with ID: {research.research_id}")

        # Stream events and collect content
        all_events = []
        task_outputs = []

        for event in exa.research.get(research.research_id, stream=True):
            all_events.append(event)

            if hasattr(event, 'event_type') and event.event_type == 'task-output':
                if hasattr(event, 'output') and hasattr(event.output, 'content'):
                    content = event.output.content
                    task_outputs.append(content)
                    activity.logger.info(f"Collected task output: {len(content)} chars")

        # Compile all research outputs
        full_content = "\n\n---\n\n".join(task_outputs)

        results = [{
            "url": f"exa-research://{topic.lower().replace(' ', '-')}",
            "title": f"{topic} Research",
            "content": full_content[:10000] if full_content else "",  # More content for topics
            "text": full_content[:10000] if full_content else "",  # Also as text field
            "highlights": [],
            "published_date": None,
            "score": 1.0,
            "source": "exa-research",
            "research_id": research.research_id
        }]

        activity.logger.info(
            f"Exa topic research complete: {len(task_outputs)} outputs, {len(full_content)} chars, cost: $0.04"
        )

        return {
            "results": results,
            "cost": 0.04,
            "summary": {
                "topic": topic,
                "article_type": article_type,
                "research_id": research.research_id,
                "event_count": len(all_events),
                "task_outputs": len(task_outputs),
                "content_length": len(full_content)
            },
            "research_id": research.research_id
        }

    except Exception as e:
        activity.logger.error(f"Exa topic research failed: {e}")
        return {
            "results": [],
            "cost": 0.04,
            "summary": {},
            "error": str(e)
        }


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
