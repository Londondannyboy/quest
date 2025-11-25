"""
Research Curation Activity

Stage 1 of article generation: Filter, dedupe, and summarize research sources
before passing to article generation.
"""

import os
import anthropic
from temporalio import activity
from typing import Dict, Any, List


@activity.defn
async def curate_research_sources(
    topic: str,
    crawled_pages: List[Dict[str, Any]],
    news_articles: List[Dict[str, Any]],
    exa_results: List[Dict[str, Any]],
    max_sources: int = 20
) -> Dict[str, Any]:
    """
    Curate and summarize research sources before article generation.

    Uses Haiku to:
    1. Remove duplicates (same story from multiple sources)
    2. Score relevance to topic (0-10)
    3. Extract key facts, quotes, statistics
    4. Identify contradictions or multiple perspectives
    5. Summarize each source concisely

    Args:
        topic: Article topic
        crawled_pages: Full content from crawled URLs
        news_articles: News article metadata from DataForSEO/Serper
        exa_results: Research results from Exa
        max_sources: Maximum curated sources to return

    Returns:
        Dict with curated_sources, key_facts, perspectives, metadata
    """
    activity.logger.info(f"Curating research for: {topic}")
    activity.logger.info(
        f"Input: {len(crawled_pages)} crawled, {len(news_articles)} news, {len(exa_results)} exa"
    )

    # Combine all sources into unified format
    all_sources = []

    # Add crawled pages (richest content)
    for i, page in enumerate(crawled_pages[:50]):  # Up to 50 crawled pages
        if page.get("content"):
            all_sources.append({
                "id": f"crawl_{i}",
                "type": "crawled",
                "url": page.get("url", ""),
                "title": page.get("title", ""),
                "content": page.get("content", "")[:4000],  # 4k chars per source
                "source": page.get("source", "")
            })

    # Add news articles (metadata + snippets)
    for i, article in enumerate(news_articles[:30]):  # Up to 30 news
        all_sources.append({
            "id": f"news_{i}",
            "type": "news",
            "url": article.get("url", ""),
            "title": article.get("title", ""),
            "content": article.get("snippet", "") or article.get("description", ""),
            "source": article.get("source", ""),
            "date": article.get("date", "") or article.get("timestamp", "")
        })

    # Add Exa results (research summaries)
    for i, result in enumerate(exa_results[:10]):  # Up to 10 Exa
        content = result.get("content", "") or result.get("text", "")
        all_sources.append({
            "id": f"exa_{i}",
            "type": "research",
            "url": result.get("url", ""),
            "title": result.get("title", ""),
            "content": content[:4000],
            "source": "exa"
        })

    if not all_sources:
        activity.logger.warning("No sources to curate")
        return {
            "curated_sources": [],
            "key_facts": [],
            "perspectives": [],
            "total_input": 0,
            "total_output": 0
        }

    activity.logger.info(f"Combined {len(all_sources)} sources for curation")

    # Build curation prompt
    sources_text = ""
    for s in all_sources:
        sources_text += f"\n\n--- SOURCE [{s['id']}] ---\n"
        sources_text += f"Type: {s['type']}\n"
        sources_text += f"Title: {s['title']}\n"
        sources_text += f"URL: {s['url']}\n"
        if s.get('date'):
            sources_text += f"Date: {s['date']}\n"
        sources_text += f"Content:\n{s['content']}\n"

    prompt = f"""You are a research curator preparing sources for an article about: "{topic}"

Analyze these {len(all_sources)} sources and provide:

1. **CURATED SOURCES** (top {max_sources} most relevant, no duplicates)
   For each source, provide:
   - source_id (from the SOURCE ID above)
   - relevance_score (1-10, where 10 is highly relevant)
   - summary (2-3 sentences capturing key information)
   - key_quote (one important quote if available)
   - why_relevant (brief explanation)

2. **KEY FACTS** (bullet points of verified facts from multiple sources)
   - Facts that appear in multiple sources are more reliable
   - Include statistics, dates, names, amounts

3. **PERSPECTIVES** (different viewpoints on the topic)
   - Note any contradictions between sources
   - Identify different stakeholder perspectives

4. **DUPLICATES** (sources covering the same story)
   - Group duplicates by story, keep the most detailed version

Output as JSON:
{{
  "curated_sources": [
    {{"source_id": "crawl_0", "relevance_score": 9, "summary": "...", "key_quote": "...", "why_relevant": "..."}}
  ],
  "key_facts": ["fact 1", "fact 2"],
  "perspectives": ["perspective 1", "perspective 2"],
  "duplicate_groups": [["news_1", "news_5", "crawl_3"]]
}}

SOURCES:
{sources_text}"""

    # Call Haiku for curation (cheap and fast)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        activity.logger.error("ANTHROPIC_API_KEY not set")
        # Fallback: return first N sources without curation
        return {
            "curated_sources": all_sources[:max_sources],
            "key_facts": [],
            "perspectives": [],
            "total_input": len(all_sources),
            "total_output": min(len(all_sources), max_sources),
            "error": "No API key, returned uncurated"
        }

    client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text

        # Parse JSON response
        import json

        # Extract JSON from response (might have markdown wrapper)
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            curation_result = json.loads(json_str)
        else:
            activity.logger.warning("Could not parse JSON from curation response")
            curation_result = {"curated_sources": [], "key_facts": [], "perspectives": []}

        # Enrich curated sources with full content from original sources
        curated_with_content = []
        source_map = {s["id"]: s for s in all_sources}

        for curated in curation_result.get("curated_sources", [])[:max_sources]:
            source_id = curated.get("source_id", "")
            original = source_map.get(source_id, {})

            curated_with_content.append({
                **curated,
                "url": original.get("url", ""),
                "title": original.get("title", ""),
                "full_content": original.get("content", ""),
                "type": original.get("type", ""),
                "date": original.get("date", "")
            })

        activity.logger.info(
            f"Curation complete: {len(curated_with_content)} sources, "
            f"{len(curation_result.get('key_facts', []))} facts, "
            f"{len(curation_result.get('perspectives', []))} perspectives"
        )

        return {
            "curated_sources": curated_with_content,
            "key_facts": curation_result.get("key_facts", []),
            "perspectives": curation_result.get("perspectives", []),
            "duplicate_groups": curation_result.get("duplicate_groups", []),
            "total_input": len(all_sources),
            "total_output": len(curated_with_content),
            "model": "claude-3-5-haiku-20241022"
        }

    except Exception as e:
        activity.logger.error(f"Curation failed: {e}")
        # Fallback: return first N sources without curation
        return {
            "curated_sources": all_sources[:max_sources],
            "key_facts": [],
            "perspectives": [],
            "total_input": len(all_sources),
            "total_output": min(len(all_sources), max_sources),
            "error": str(e)
        }
