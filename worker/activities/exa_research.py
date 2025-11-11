"""
Exa Research Activities

Activities for direct article research using Exa search and content retrieval.
Used for topic-based article creation without news assessment.
"""

import os
import json
from typing import List, Dict, Any
from temporalio import activity
from exa_py import Exa
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


@activity.defn(name="exa_research_topic")
async def exa_research_topic(research_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Research a topic using Exa search with full content retrieval

    Args:
        research_input: Dict with topic, num_results, and optional filters

    Returns:
        Dict with research_results list containing full content
    """
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        raise ValueError("EXA_API_KEY not set")

    topic = research_input.get("topic", "")
    num_results = research_input.get("num_results", 5)
    use_autoprompt = research_input.get("use_autoprompt", True)
    category = research_input.get("category", "research paper")  # or "news", "company", etc.

    activity.logger.info(f"🔍 Researching topic with Exa: {topic}")

    exa = Exa(api_key=api_key)

    try:
        # Exa search with full content retrieval
        # Note: Using basic parameters - Exa API has changed
        search_response = exa.search_and_contents(
            topic,
            num_results=num_results,
            text=True,  # Get full text content
        )

        research_results = []
        for result in search_response.results:
            research_results.append({
                "title": result.title,
                "url": result.url,
                "content": result.text or "",
                "summary": getattr(result, 'summary', '') or "",
                "highlights": getattr(result, 'highlights', []) or [],
                "published_date": getattr(result, 'published_date', None),
                "author": getattr(result, 'author', None),
                "score": getattr(result, 'score', None)
            })

        activity.logger.info(f"✅ Found {len(research_results)} high-quality sources via Exa")

        return {
            "research_results": research_results,
            "total_results": len(research_results),
            "autoprompt_string": None  # Autoprompt not currently supported
        }

    except Exception as e:
        activity.logger.error(f"❌ Exa research failed: {e}")
        raise


@activity.defn(name="exa_find_similar")
async def exa_find_similar(reference_url: str, num_results: int = 3) -> List[Dict[str, Any]]:
    """
    Find similar content to a reference URL using Exa

    Args:
        reference_url: URL to find similar content to
        num_results: Number of similar results to return

    Returns:
        List of similar sources with content
    """
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        raise ValueError("EXA_API_KEY not set")

    activity.logger.info(f"🔗 Finding similar content to: {reference_url}")

    exa = Exa(api_key=api_key)

    try:
        similar_response = exa.find_similar_and_contents(
            reference_url,
            num_results=num_results,
            text=True
        )

        similar_results = []
        for result in similar_response.results:
            similar_results.append({
                "title": result.title,
                "url": result.url,
                "content": result.text or "",
                "summary": getattr(result, 'summary', '') or ""
            })

        activity.logger.info(f"✅ Found {len(similar_results)} similar sources")

        return similar_results

    except Exception as e:
        activity.logger.error(f"❌ Find similar failed: {e}")
        return []


@activity.defn(name="deep_research_with_firecrawl")
async def deep_research_with_firecrawl(urls: List[str]) -> List[Dict[str, Any]]:
    """
    Deep scrape additional URLs using FireCrawl for comprehensive research

    Args:
        urls: List of URLs to scrape

    Returns:
        List of scraped content dicts
    """
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    if not firecrawl_key:
        activity.logger.warning("FIRECRAWL_API_KEY not set, skipping deep crawl")
        return []

    activity.logger.info(f"🕷️  Deep crawling {len(urls)} URLs with FireCrawl")

    import httpx

    scraped_results = []

    for url in urls[:5]:  # Limit to 5 URLs to avoid long running times
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v0/scrape",
                    json={
                        "url": url,
                        "pageOptions": {
                            "onlyMainContent": True
                        }
                    },
                    headers={
                        "Authorization": f"Bearer {firecrawl_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                data = response.json()

                content = data.get("data", {}).get("markdown") or data.get("data", {}).get("content", "")

                if content:
                    scraped_results.append({
                        "url": url,
                        "content": content,
                        "title": data.get("data", {}).get("metadata", {}).get("title", "")
                    })
                    activity.logger.info(f"✅ Scraped: {url[:60]}...")

        except Exception as e:
            activity.logger.warning(f"⚠️  Failed to scrape {url[:60]}: {e}")

    activity.logger.info(f"✅ Deep crawled {len(scraped_results)} URLs")

    return scraped_results


@activity.defn(name="extract_research_insights")
async def extract_research_insights(
    topic: str,
    research_results: List[Dict[str, Any]],
    app: str = "placement"
) -> Dict[str, Any]:
    """
    Extract key insights, entities, and citations from Exa research results

    Args:
        topic: The research topic
        research_results: List of Exa research results with content
        app: App context for domain-specific extraction

    Returns:
        ResearchBrief dict with entities, citations, key_findings
    """
    activity.logger.info(f"🔍 Extracting insights from {len(research_results)} research sources")

    try:
        # Import config to get app-specific extraction guidance
        from config.app_configs import get_app_config
        app_config = get_app_config(app)

        # Combine research content
        combined_content = "\n\n---\n\n".join([
            f"Source: {r.get('title', 'Unknown')}\nURL: {r.get('url', '')}\n"
            f"Summary: {r.get('summary', '')}\n"
            f"Content: {r.get('content', '')[:3000]}"
            for r in research_results
        ])

        extraction_prompt = f"""You are researching: "{topic}"

Target audience: {app_config.target_audience}
Content focus: {app_config.content_focus}
Content angle: {app_config.content_angle}

Analyze this research and extract:
1. Key entities (people, organizations, concepts, technologies)
2. Quotable facts and statistics for citations
3. Core findings and insights
4. Themes and patterns

Research Content:
{combined_content[:8000]}

Return ONLY a JSON object with this structure:
{{
  "entities": [
    {{"name": "...", "type": "person|organization|concept|technology", "description": "...", "relevance": 8.0}}
  ],
  "citations": [
    {{"source_url": "...", "source_title": "...", "fact": "...", "context": "..."}}
  ],
  "key_findings": ["finding 1", "finding 2", "finding 3"],
  "themes": ["theme 1", "theme 2"],
  "research_summary": "2-3 sentence overview of what you learned"
}}

Focus on {app_config.content_focus}. Extract at least 5-8 citations."""

        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(extraction_prompt)
        content = response.text

        # Extract JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        extraction_data = json.loads(content)

        # Build ResearchBrief structure
        result = {
            "sources": research_results,
            "entities": extraction_data.get("entities", [])[:15],
            "citations": extraction_data.get("citations", [])[:10],
            "key_findings": extraction_data.get("key_findings", []),
            "themes": extraction_data.get("themes", []),
            "research_summary": extraction_data.get("research_summary", "")
        }

        activity.logger.info(f"✅ Extracted {len(result['entities'])} entities, "
                           f"{len(result['citations'])} citations, "
                           f"{len(result['key_findings'])} findings")

        return result

    except Exception as e:
        activity.logger.error(f"❌ Research extraction failed: {e}")
        # Return minimal valid structure
        return {
            "sources": research_results,
            "entities": [],
            "citations": [],
            "key_findings": [],
            "themes": [],
            "research_summary": f"Research on {topic}"
        }
