"""
Research Curation Activity

Stage 1 of article generation: Filter, dedupe, and summarize research sources
before passing to article generation.

Uses Gemini 2.5 Flash for curation (1M context window, cheap) while
article generation uses Sonnet (better writing quality).

Now also generates article outline/structure to guide Sonnet.
"""

import os
import re
import json
import google.generativeai as genai
from temporalio import activity
from typing import Dict, Any, List


def is_relevant_to_topic(title: str, content: str, topic: str) -> bool:
    """
    Quick relevance check to filter obviously off-topic sources.
    Returns True if source appears relevant to the topic.
    """
    # Extract key terms from topic (lowercase)
    topic_lower = topic.lower()
    title_lower = (title or "").lower()
    content_lower = (content or "")[:2000].lower()  # Check first 2k chars

    # Extract main subject words from topic
    # E.g., "Cyprus Digital Nomad Visa 2025" -> ["cyprus", "digital", "nomad", "visa"]
    topic_words = set(re.findall(r'\b[a-z]{4,}\b', topic_lower))

    # Must match at least 2 key topic words in title or content
    combined_text = f"{title_lower} {content_lower}"
    matches = sum(1 for word in topic_words if word in combined_text)

    return matches >= 2


def clean_json_response(response_text: str) -> dict:
    """
    Robustly extract and parse JSON from Gemini response.
    Handles markdown wrappers, truncated JSON, and common formatting issues.
    """
    # Remove markdown code blocks if present
    response_text = re.sub(r'^```json\s*', '', response_text, flags=re.MULTILINE)
    response_text = re.sub(r'^```\s*$', '', response_text, flags=re.MULTILINE)

    # Find JSON boundaries
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1

    if json_start < 0 or json_end <= json_start:
        return {}

    json_str = response_text[json_start:json_end]

    # Try to parse as-is first
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Try to fix common JSON issues
    # 1. Remove trailing commas before ] or }
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

    # 2. Fix unescaped quotes in strings (simple heuristic)
    # This is tricky - skip for now

    # 3. Try parsing again
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Log the error location for debugging
        activity.logger.warning(f"JSON parse error at position {e.pos}: {e.msg}")
        activity.logger.warning(f"Context: ...{json_str[max(0, e.pos-50):e.pos+50]}...")

        # Last resort: try to extract key arrays manually
        result = {}

        # Extract key_facts array
        facts_match = re.search(r'"key_facts"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
        if facts_match:
            try:
                facts_str = '[' + facts_match.group(1) + ']'
                result['key_facts'] = json.loads(facts_str)
            except:
                result['key_facts'] = []

        # Extract perspectives array
        persp_match = re.search(r'"perspectives"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
        if persp_match:
            try:
                persp_str = '[' + persp_match.group(1) + ']'
                result['perspectives'] = json.loads(persp_str)
            except:
                result['perspectives'] = []

        return result


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

    Uses Gemini 2.5 Flash to:
    1. Pre-filter obviously off-topic sources
    2. Remove duplicates (same story from multiple sources)
    3. Score relevance to topic (0-10)
    4. Extract key facts, quotes, statistics
    5. Generate article outline with suggested sections
    6. Identify high-authority sources for early placement

    Args:
        topic: Article topic
        crawled_pages: Full content from crawled URLs
        news_articles: News article metadata from DataForSEO/Serper
        exa_results: Research results from Exa
        max_sources: Maximum curated sources to return

    Returns:
        Dict with curated_sources, key_facts, perspectives, article_outline, metadata
    """
    activity.logger.info(f"Curating research for: {topic}")
    activity.logger.info(
        f"Input: {len(crawled_pages)} crawled, {len(news_articles)} news, {len(exa_results)} exa"
    )

    # Combine all sources into unified format WITH pre-filtering
    all_sources = []
    filtered_count = 0

    # Add crawled pages (richest content) - with relevance pre-filter
    for i, page in enumerate(crawled_pages[:75]):
        if page.get("content"):
            title = page.get("title", "")
            content = page.get("content", "")

            # Pre-filter: skip obviously off-topic sources
            if not is_relevant_to_topic(title, content, topic):
                filtered_count += 1
                continue

            all_sources.append({
                "id": f"crawl_{i}",
                "type": "crawled",
                "url": page.get("url", ""),
                "title": title,
                "content": content[:6000],  # 6k chars per source
                "source": page.get("source", "")
            })

    # Add news articles (metadata + snippets)
    for i, article in enumerate(news_articles[:50]):
        title = article.get("title", "")
        content = article.get("snippet", "") or article.get("description", "")

        if not is_relevant_to_topic(title, content, topic):
            filtered_count += 1
            continue

        all_sources.append({
            "id": f"news_{i}",
            "type": "news",
            "url": article.get("url", ""),
            "title": title,
            "content": content,
            "source": article.get("source", ""),
            "date": article.get("date", "") or article.get("timestamp", "")
        })

    # Add Exa results (research summaries)
    for i, result in enumerate(exa_results[:20]):
        title = result.get("title", "")
        content = result.get("content", "") or result.get("text", "")

        if not is_relevant_to_topic(title, content, topic):
            filtered_count += 1
            continue

        all_sources.append({
            "id": f"exa_{i}",
            "type": "research",
            "url": result.get("url", ""),
            "title": title,
            "content": content[:6000],
            "source": "exa"
        })

    activity.logger.info(f"Pre-filtered {filtered_count} off-topic sources")

    if not all_sources:
        activity.logger.warning("No relevant sources found after filtering")
        return {
            "curated_sources": [],
            "key_facts": [],
            "perspectives": [],
            "article_outline": [],
            "total_input": 0,
            "total_output": 0
        }

    activity.logger.info(f"Processing {len(all_sources)} relevant sources for curation")

    # Build curation prompt - simplified structure to reduce JSON errors
    sources_text = ""
    for s in all_sources:
        sources_text += f"\n\n--- SOURCE [{s['id']}] ---\n"
        sources_text += f"Title: {s['title']}\n"
        sources_text += f"URL: {s['url']}\n"
        if s.get('date'):
            sources_text += f"Date: {s['date']}\n"
        sources_text += f"Content:\n{s['content']}\n"

    # Simplified prompt with cleaner JSON structure
    prompt = f"""You are a research curator preparing sources for a comprehensive article about: "{topic}"

TASK: Analyze ALL {len(all_sources)} sources and extract:
1. Key facts (specific numbers, dates, requirements, costs, steps)
2. Different perspectives and viewpoints
3. Suggested article structure with sections
4. Best sources to cite (with URLs)

IMPORTANT: Output ONLY valid JSON. No markdown, no explanation. Just the JSON object.

{{
  "key_facts": [
    "Fact 1 with specific detail",
    "Fact 2 with numbers/dates",
    "... extract 30-50 specific facts"
  ],
  "perspectives": [
    "Government perspective: ...",
    "User/applicant perspective: ...",
    "Expert perspective: ...",
    "Pros: ...",
    "Cons: ..."
  ],
  "article_outline": [
    {{
      "section": "Introduction",
      "key_points": ["What is this topic", "Why it matters in 2025"],
      "suggested_sources": ["crawl_0", "news_2"]
    }},
    {{
      "section": "Requirements and Eligibility",
      "key_points": ["Income requirements", "Documents needed", "Who can apply"],
      "suggested_sources": ["crawl_1", "crawl_3"]
    }},
    {{
      "section": "Application Process",
      "key_points": ["Step-by-step process", "Timeline", "Fees"],
      "suggested_sources": ["crawl_0", "crawl_2"]
    }},
    {{
      "section": "Benefits and Advantages",
      "key_points": ["Tax benefits", "Lifestyle", "Family reunification"],
      "suggested_sources": ["news_1"]
    }},
    {{
      "section": "Limitations and Considerations",
      "key_points": ["Restrictions", "Renewal", "What to watch out for"],
      "suggested_sources": ["crawl_4"]
    }},
    {{
      "section": "Conclusion",
      "key_points": ["Summary", "Next steps"],
      "suggested_sources": []
    }}
  ],
  "high_authority_sources": [
    {{"id": "crawl_0", "url": "...", "authority": "government or official source"}},
    {{"id": "crawl_1", "url": "...", "authority": "major news outlet"}}
  ],
  "timeline": [
    "2021-10: Program launched",
    "2022-03: Cap increased to 500",
    "2025-03: Applications reopened"
  ],
  "best_sources": [
    {{"id": "crawl_0", "url": "...", "title": "...", "relevance": 9}},
    {{"id": "crawl_1", "url": "...", "title": "...", "relevance": 8}}
  ]
}}

Generate the article_outline sections based on what makes sense for THIS specific topic.
Include 4-6 sections that would create a comprehensive, well-structured article.
For each section, suggest which source IDs contain relevant information.

SOURCES TO ANALYZE:
{sources_text}

OUTPUT (JSON only, no markdown):"""

    # Use Gemini 2.5 Flash for curation (1M context window, very cheap)
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        activity.logger.error("GOOGLE_API_KEY not set for curation")
        return {
            "curated_sources": all_sources[:max_sources],
            "key_facts": [],
            "perspectives": [],
            "article_outline": [],
            "total_input": len(all_sources),
            "total_output": min(len(all_sources), max_sources),
            "error": "No API key, returned uncurated"
        }

    genai.configure(api_key=api_key)

    try:
        # Gemini 2.5 Flash - massive context window (1M tokens), perfect for curation
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=16384,
                temperature=0.2,  # Lower temp for more consistent JSON
            )
        )

        response_text = response.text
        activity.logger.info(f"Gemini response length: {len(response_text)} chars")

        # Use robust JSON parser
        curation_result = clean_json_response(response_text)

        if not curation_result:
            activity.logger.warning("Could not parse any JSON from curation response")
            # Return sources without curation
            return {
                "curated_sources": all_sources[:max_sources],
                "key_facts": [],
                "perspectives": [],
                "article_outline": [],
                "total_input": len(all_sources),
                "total_output": max_sources,
                "error": "JSON parsing failed"
            }

        # Build curated sources from best_sources in response
        source_map = {s["id"]: s for s in all_sources}
        curated_with_content = []

        for best in curation_result.get("best_sources", [])[:max_sources]:
            source_id = best.get("id", "")
            original = source_map.get(source_id, {})

            if original:
                curated_with_content.append({
                    "source_id": source_id,
                    "relevance_score": best.get("relevance", 5),
                    "url": original.get("url", "") or best.get("url", ""),
                    "title": original.get("title", "") or best.get("title", ""),
                    "full_content": original.get("content", ""),
                    "type": original.get("type", ""),
                    "date": original.get("date", "")
                })

        # If best_sources was empty, use first N sources
        if not curated_with_content:
            for s in all_sources[:max_sources]:
                curated_with_content.append({
                    "source_id": s["id"],
                    "relevance_score": 5,
                    "url": s.get("url", ""),
                    "title": s.get("title", ""),
                    "full_content": s.get("content", ""),
                    "type": s.get("type", ""),
                    "date": s.get("date", "")
                })

        key_facts = curation_result.get("key_facts", [])
        perspectives = curation_result.get("perspectives", [])
        article_outline = curation_result.get("article_outline", [])
        high_authority = curation_result.get("high_authority_sources", [])
        timeline = curation_result.get("timeline", [])

        activity.logger.info(
            f"Curation complete: {len(curated_with_content)} sources, "
            f"{len(key_facts)} facts, {len(perspectives)} perspectives, "
            f"{len(article_outline)} outline sections"
        )

        return {
            "curated_sources": curated_with_content,
            "key_facts": key_facts,
            "perspectives": perspectives,
            "article_outline": article_outline,
            "high_authority_sources": high_authority,
            "timeline": timeline,
            "total_input": len(all_sources),
            "total_output": len(curated_with_content),
            "filtered_count": filtered_count,
            "model": "gemini-2.5-flash"
        }

    except Exception as e:
        activity.logger.error(f"Curation failed: {e}", exc_info=True)
        # Fallback: return first N sources without curation
        return {
            "curated_sources": all_sources[:max_sources],
            "key_facts": [],
            "perspectives": [],
            "article_outline": [],
            "total_input": len(all_sources),
            "total_output": min(len(all_sources), max_sources),
            "error": str(e)
        }
