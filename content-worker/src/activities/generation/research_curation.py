"""
Research Curation Activity

Stage 1 of article generation: Filter, dedupe, and deeply analyze research sources
before passing to article generation.

Uses Gemini 2.5 Pro for curation (1M context window, best reasoning/extraction).
Pro is ~2x better at fact extraction (SimpleQA: 54.5% vs Flash's 29.7%).
This ensures we capture all nuances, opinions, unique angles, and interesting facts
that Sonnet needs to write a comprehensive, insightful article.
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
    Deeply analyze and curate research sources before article generation.

    Uses Gemini 2.5 Pro (best-in-class reasoning) to:
    1. Pre-filter obviously off-topic sources
    2. Remove duplicates (same story from multiple sources)
    3. Extract ALL key facts, statistics, quotes, dates, costs
    4. Identify opinions, sentiment, and unique perspectives
    5. Find interesting nuances and angles others might miss
    6. Generate article outline with suggested sections
    7. Identify high-authority sources for credibility
    8. Build timeline of events/changes

    Pro is chosen over Flash because:
    - 2x better at fact extraction (SimpleQA: 54.5% vs 29.7%)
    - Better reasoning for nuance detection
    - Cost is ~$0.40 vs $0.04 per curation - worth it for quality

    Args:
        topic: Article topic
        crawled_pages: Full content from crawled URLs
        news_articles: News article metadata from DataForSEO/Serper
        exa_results: Research results from Exa
        max_sources: Maximum curated sources to return

    Returns:
        Dict with curated_sources, key_facts, perspectives, opinions,
        unique_angles, article_outline, timeline, metadata
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
                "content": content[:15000],  # 15k chars per source for richer voice extraction
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
            "content": content[:15000],  # 15k chars per source for richer voice extraction
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

    # Deep analysis prompt for Pro model - extract everything Sonnet needs
    prompt = f"""You are an expert research analyst preparing comprehensive source analysis for a professional writer.

TOPIC: "{topic}"

YOUR TASK: Deeply analyze ALL {len(all_sources)} sources and extract EVERYTHING valuable:

1. FACTS - Every specific number, date, cost, requirement, statistic, deadline
2. OPINIONS - What do different stakeholders think? Controversies? Debates?
3. SENTIMENT - How do people feel about this? Frustrations? Enthusiasm?
4. UNIQUE ANGLES - What interesting perspectives or nuances might others miss?
5. QUOTES - Direct quotes that add credibility or color
6. COMPARISONS - How does this compare to alternatives?
7. CHANGES - What's new in 2024-2025? What changed recently?
8. GOTCHAS - Common mistakes, warnings, things people overlook
9. VOICES - Extract 5-10 human perspectives (experts, testimonials, officials, media) with attribution

Be EXHAUSTIVE. The writer needs EVERYTHING to create a comprehensive, insightful article.
Missing a key fact or interesting angle = lower quality article.

OUTPUT ONLY VALID JSON (no markdown, no explanation):

{{
  "key_facts": [
    "Extract 40-60 specific facts with exact numbers/dates/costs",
    "Include ALL requirements, steps, deadlines, fees mentioned",
    "Be precise: '€3,500/month minimum' not 'income requirement'"
  ],
  "opinions_and_sentiment": [
    {{"source": "expat forum", "sentiment": "frustrated", "opinion": "Processing takes 3-6 months despite 30-day promise"}},
    {{"source": "government official", "sentiment": "positive", "opinion": "Program attracting high-quality applicants"}},
    {{"source": "tax advisor", "sentiment": "cautious", "opinion": "Tax benefits often overstated, check your specific situation"}}
  ],
  "unique_angles": [
    "Angle most articles miss: ...",
    "Interesting nuance: ...",
    "Counter-intuitive finding: ...",
    "Lesser-known benefit/drawback: ..."
  ],
  "direct_quotes": [
    {{"quote": "Exact quote from source", "attribution": "Who said it", "source_id": "crawl_0"}},
    {{"quote": "Another valuable quote", "attribution": "Expert name", "source_id": "news_2"}}
  ],
  "voices": [
    {{
      "type": "expert",
      "source": "Name, Title/Role",
      "credibility": "Why they're credible (e.g., '15 years immigration law')",
      "stance": "positive|negative|neutral|mixed",
      "quote": "Their exact words or paraphrased insight",
      "context": "What they were discussing",
      "key_insight": "The main takeaway from this voice",
      "source_id": "crawl_0"
    }},
    {{
      "type": "testimonial",
      "source": "Name, Background",
      "credibility": "Their relevant experience (e.g., 'Relocated from UK to Cyprus in 2024')",
      "stance": "positive",
      "quote": "Their personal experience",
      "context": "Discussing their relocation journey",
      "before_after": {{
        "before": "What their situation was before",
        "after": "What it is now"
      }},
      "key_insight": "Main lesson from their experience",
      "source_id": "crawl_1"
    }},
    {{
      "type": "official",
      "source": "Government agency/official name",
      "credibility": "Official capacity",
      "stance": "neutral",
      "quote": "Official statement or policy",
      "context": "Policy announcement/clarification",
      "key_insight": "Key policy point",
      "source_id": "news_0"
    }},
    {{
      "type": "media",
      "source": "Publication/journalist name",
      "credibility": "Publication reputation",
      "stance": "mixed",
      "quote": "Commentary or analysis",
      "context": "News coverage context",
      "key_insight": "Key observation",
      "source_id": "news_1"
    }}
  ],
  "comparisons": [
    "Compared to Portugal: ...",
    "Compared to previous version: ...",
    "Compared to similar programs: ..."
  ],
  "recent_changes": [
    "2025: What changed this year",
    "2024: Previous changes",
    "Upcoming: What's expected"
  ],
  "warnings_and_gotchas": [
    "Common mistake: ...",
    "Often overlooked: ...",
    "Watch out for: ..."
  ],
  "article_outline": [
    {{
      "section": "Introduction",
      "key_points": ["Hook with surprising fact", "Why this matters now", "What reader will learn"],
      "tone": "engaging, not generic",
      "suggested_sources": ["crawl_0"]
    }},
    {{
      "section": "Section title based on topic",
      "key_points": ["Specific points to cover"],
      "facts_to_include": ["From key_facts above"],
      "suggested_sources": ["crawl_1", "crawl_3"]
    }}
  ],
  "high_authority_sources": [
    {{"id": "crawl_0", "url": "...", "authority": "government/official", "why_cite": "Primary source for requirements"}},
    {{"id": "news_1", "url": "...", "authority": "major outlet", "why_cite": "Recent coverage with expert quotes"}}
  ],
  "timeline": [
    "YYYY-MM: Event/change with specific detail"
  ],
  "best_sources": [
    {{"id": "crawl_0", "url": "...", "title": "...", "relevance": 9, "unique_value": "What this source adds"}},
    {{"id": "crawl_1", "url": "...", "title": "...", "relevance": 8, "unique_value": "Different perspective"}}
  ],
  "spawn_opportunities": [
    {{"topic": "Related topic that deserves its own article", "reason": "Why it merits a separate article (e.g., mentioned in 5+ sources)", "confidence": 0.85, "article_type": "guide", "unique_angle": "What makes this different from main article"}}
  ]
}}

SPAWN OPPORTUNITIES (max 2):
Look for RELATED topics that appear frequently in sources but are DIFFERENT enough to merit their own articles:
- Competing alternatives (if Cyprus visa, look for Malta/Portugal mentions)
- Complementary topics (if visa, look for "tax residency", "cost of living" angles)
- Only include if confidence >= 0.7 (mentioned substantially in multiple sources)

VOICES (5-10 required):
Extract human perspectives that bring the topic to life. Prioritize diversity of voice types:
- "expert": Immigration lawyers, tax advisors, industry professionals with credentials
- "testimonial": Real people who experienced this (expats, relocators, users) with before/after transformations
- "official": Government statements, policy announcements, regulatory bodies
- "media": Journalists, commentators, publications with analysis

For each voice, capture:
- The exact quote or close paraphrase
- Full attribution (name + role/background)
- Credibility signal (why should readers trust this voice?)
- Stance (positive/negative/neutral/mixed on the topic)
- Context (what were they discussing?)
- Key insight (the main takeaway)
- For testimonials: include before_after transformation if available

Aim for balance: at least 2 expert, 2 testimonial, and mix of stances (not all positive).

Generate 5-7 article_outline sections that create a COMPREHENSIVE article structure.
Each section should have specific key_points, not generic placeholders.

SOURCES TO ANALYZE:
{sources_text}

OUTPUT (JSON only):"""

    # Use Gemini 2.5 Pro for curation - best reasoning, 2x better fact extraction
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        activity.logger.error("GOOGLE_API_KEY not set for curation")
        return {
            "curated_sources": all_sources[:max_sources],
            "key_facts": [],
            "opinions_and_sentiment": [],
            "unique_angles": [],
            "voices": [],
            "article_outline": [],
            "total_input": len(all_sources),
            "total_output": min(len(all_sources), max_sources),
            "error": "No API key, returned uncurated"
        }

    genai.configure(api_key=api_key)

    try:
        # Gemini 2.5 Pro - best reasoning, ~2x better at fact extraction than Flash
        # Cost: ~$0.40 vs $0.04 per curation - worth it for quality
        model = genai.GenerativeModel("gemini-2.5-pro-preview-06-05")
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
                "voices": [],
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

        # Extract all the rich analysis from Pro
        key_facts = curation_result.get("key_facts", [])
        opinions_and_sentiment = curation_result.get("opinions_and_sentiment", [])
        unique_angles = curation_result.get("unique_angles", [])
        direct_quotes = curation_result.get("direct_quotes", [])
        voices = curation_result.get("voices", [])
        comparisons = curation_result.get("comparisons", [])
        recent_changes = curation_result.get("recent_changes", [])
        warnings = curation_result.get("warnings_and_gotchas", [])
        article_outline = curation_result.get("article_outline", [])
        high_authority = curation_result.get("high_authority_sources", [])
        timeline = curation_result.get("timeline", [])
        spawn_opportunities = curation_result.get("spawn_opportunities", [])

        # Count voice types for logging
        voice_types = {}
        for v in voices:
            vtype = v.get("type", "unknown")
            voice_types[vtype] = voice_types.get(vtype, 0) + 1

        activity.logger.info(
            f"Curation complete: {len(curated_with_content)} sources, "
            f"{len(key_facts)} facts, {len(opinions_and_sentiment)} opinions, "
            f"{len(unique_angles)} angles, {len(article_outline)} outline sections, "
            f"{len(voices)} voices ({voice_types})"
        )

        # Log spawn opportunities if found
        if spawn_opportunities:
            activity.logger.info(f"Found {len(spawn_opportunities)} spawn opportunities: {[s.get('topic') for s in spawn_opportunities]}")

        return {
            "curated_sources": curated_with_content,
            "key_facts": key_facts,
            "opinions_and_sentiment": opinions_and_sentiment,
            "unique_angles": unique_angles,
            "direct_quotes": direct_quotes,
            "voices": voices,
            "comparisons": comparisons,
            "recent_changes": recent_changes,
            "warnings_and_gotchas": warnings,
            "article_outline": article_outline,
            "high_authority_sources": high_authority,
            "timeline": timeline,
            "spawn_opportunities": spawn_opportunities,
            "total_input": len(all_sources),
            "total_output": len(curated_with_content),
            "filtered_count": filtered_count,
            "model": "gemini-2.5-pro"
        }

    except Exception as e:
        activity.logger.error(f"Curation failed: {e}", exc_info=True)
        # Fallback: return first N sources without curation
        return {
            "curated_sources": all_sources[:max_sources],
            "key_facts": [],
            "opinions_and_sentiment": [],
            "unique_angles": [],
            "direct_quotes": [],
            "voices": [],
            "comparisons": [],
            "recent_changes": [],
            "warnings_and_gotchas": [],
            "article_outline": [],
            "high_authority_sources": [],
            "timeline": [],
            "spawn_opportunities": [],
            "total_input": len(all_sources),
            "total_output": min(len(all_sources), max_sources),
            "error": str(e)
        }
