"""
Research Curation Activity

Stage 1 of article generation: Filter, dedupe, and summarize research sources
before passing to article generation.

Uses Gemini 2.5 Flash for curation (1M context window, cheap) while
article generation uses Sonnet (better writing quality).
"""

import os
import google.generativeai as genai
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

    # Add crawled pages (richest content) - increased limits for comprehensive articles
    for i, page in enumerate(crawled_pages[:75]):  # Up to 75 crawled pages
        if page.get("content"):
            all_sources.append({
                "id": f"crawl_{i}",
                "type": "crawled",
                "url": page.get("url", ""),
                "title": page.get("title", ""),
                "content": page.get("content", "")[:8000],  # 8k chars per source for rich content
                "source": page.get("source", "")
            })

    # Add news articles (metadata + snippets)
    for i, article in enumerate(news_articles[:50]):  # Up to 50 news articles
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
    for i, result in enumerate(exa_results[:20]):  # Up to 20 Exa results
        content = result.get("content", "") or result.get("text", "")
        all_sources.append({
            "id": f"exa_{i}",
            "type": "research",
            "url": result.get("url", ""),
            "title": result.get("title", ""),
            "content": content[:8000],  # 8k chars for rich research content
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

    prompt = f"""You are a research curator preparing sources for a COMPREHENSIVE 3000+ word article about: "{topic}"

Analyze ALL {len(all_sources)} sources thoroughly and provide EXTENSIVE curation:

1. **CURATED SOURCES** (top {max_sources} most relevant, no duplicates)
   For each source, provide:
   - source_id (from the SOURCE ID above)
   - relevance_score (1-10, where 10 is highly relevant)
   - summary (3-5 sentences capturing ALL key information - be thorough)
   - key_quote (one or two important quotes if available)
   - key_facts_from_source (list of specific facts, numbers, dates from this source)
   - why_relevant (brief explanation)

2. **KEY FACTS** (50+ bullet points of verified facts - BE EXHAUSTIVE)
   - Extract EVERY statistic, date, name, amount, requirement, and specific detail
   - Facts that appear in multiple sources are more reliable
   - Include: costs, timelines, requirements, eligibility criteria, process steps
   - Include: historical context, recent changes, future implications
   - Include: expert opinions, official statements, regulatory details

3. **PERSPECTIVES** (different viewpoints on the topic - at least 5-10)
   - Note any contradictions between sources
   - Identify different stakeholder perspectives (government, users, experts, critics)
   - Include pros and cons, benefits and drawbacks

4. **DUPLICATES** (sources covering the same story)
   - Group duplicates by story, keep the most detailed version

5. **TIMELINE** (if applicable - chronological events related to topic)
   - Key dates and milestones mentioned in sources

Output as JSON:
{{
  "curated_sources": [
    {{"source_id": "crawl_0", "relevance_score": 9, "summary": "...", "key_quote": "...", "key_facts_from_source": ["fact1", "fact2"], "why_relevant": "..."}}
  ],
  "key_facts": ["fact 1", "fact 2", "... at least 50 facts"],
  "perspectives": ["perspective 1", "perspective 2", "... at least 5-10 perspectives"],
  "duplicate_groups": [["news_1", "news_5", "crawl_3"]],
  "timeline": ["2024-01: Event 1", "2024-06: Event 2"]
}}

SOURCES:
{sources_text}"""

    # Use Gemini 2.5 Flash for curation (1M context window, very cheap)
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        activity.logger.error("GOOGLE_API_KEY not set for curation")
        # Fallback: return first N sources without curation
        return {
            "curated_sources": all_sources[:max_sources],
            "key_facts": [],
            "perspectives": [],
            "total_input": len(all_sources),
            "total_output": min(len(all_sources), max_sources),
            "error": "No API key, returned uncurated"
        }

    genai.configure(api_key=api_key)

    try:
        # Gemini 2.5 Flash - massive context window, perfect for curation
        model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=16384,
                temperature=0.3,  # Lower temp for more factual extraction
            )
        )

        response_text = response.text

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
            "model": "gemini-2.5-flash-preview-05-20"
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
