"""
Research Activities

Core activities for news search, scraping, and entity extraction.
Simplified version focusing on essential working functions.
"""

import os
import json
from typing import List, Dict, Any
from temporalio import activity
import httpx
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


@activity.defn(name="search_news_serper")
async def search_news_serper(search_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search Google News via Serper.dev

    Args:
        search_input: Dict with keyword, location, language, num_results

    Returns:
        Dict with news_items list
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        raise ValueError("SERPER_API_KEY not set")

    keyword = search_input.get("keyword", "")
    location = search_input.get("location", "UK")
    language = search_input.get("language", "en")
    num_results = search_input.get("num_results", 5)

    activity.logger.info(f"🔍 Searching news: {keyword}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://google.serper.dev/news",
            json={
                "q": keyword,
                "num": num_results,
                "gl": location.lower(),
                "hl": language,
                "tbs": "qdr:d"  # Last 24 hours
            },
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            }
        )
        response.raise_for_status()
        data = response.json()

    news_items = data.get("news", [])

    activity.logger.info(f"✅ Found {len(news_items)} news articles")

    return {
        "news_items": news_items,
        "total_results": len(news_items)
    }


@activity.defn(name="deep_scrape_sources")
async def deep_scrape_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Scrape content from source URLs using Tavily

    Args:
        sources: List of Source dicts with URLs

    Returns:
        List of Source dicts with enriched content
    """
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        activity.logger.warning("TAVILY_API_KEY not set, returning sources as-is")
        return sources

    activity.logger.info(f"📚 Scraping {len(sources)} sources with Tavily")

    enriched_sources = []

    for source in sources:
        url = source.get("url", "")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.tavily.com/crawl",
                    json={
                        "url": url,
                        "api_key": tavily_key,
                        "extract_depth": "advanced"
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()

                # Update source with scraped content and images
                content = data.get("content") or data.get("raw_content", "")
                images = data.get("images", [])  # Tavily returns image URLs

                if content:
                    source["content"] = content
                    source["images"] = images  # Store article images
                    activity.logger.info(f"✅ Scraped: {url[:60]}... ({len(images)} images)")
                else:
                    activity.logger.warning(f"⚠️  No content: {url[:60]}...")

        except Exception as e:
            activity.logger.warning(f"❌ Failed to scrape {url[:60]}: {e}")

        enriched_sources.append(source)

    return enriched_sources


@activity.defn(name="extract_entities_from_news")
async def extract_entities_from_news(scraped_news: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Extract entities and themes from scraped breaking news using Gemini Flash

    Args:
        scraped_news: List of Source dicts with content

    Returns:
        Dict with "entities" and "themes" lists
    """
    activity.logger.info(f"🔍 Extracting entities from {len(scraped_news)} sources")

    try:
        # Combine news content
        news_content = "\n\n---\n\n".join([
            f"Article {i+1}:\n{source.get('content', '')[:2000]}"
            for i, source in enumerate(scraped_news)
        ])

        extraction_prompt = f"""Extract key entities and themes from this breaking news:

{news_content}

Return ONLY a JSON object:
{{
  "entities": ["Entity 1", "Entity 2", "Entity 3"],
  "themes": ["Theme 1", "Theme 2"],
  "key_topics": ["Topic 1", "Topic 2"]
}}

Focus on: Companies, people, deal types, sectors, geographic regions."""

        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(extraction_prompt)
        content = response.text

        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        extracted_data = json.loads(content)

        activity.logger.info(f"✅ Extracted {len(extracted_data.get('entities', []))} entities, "
                           f"{len(extracted_data.get('themes', []))} themes")

        return extracted_data

    except Exception as e:
        activity.logger.error(f"❌ Entity extraction failed: {e}")
        return {"entities": [], "themes": [], "key_topics": []}


@activity.defn(name="extract_entities_citations")
async def extract_entities_citations(
    brief: Dict[str, Any],
    sources: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Extract entities and citations from research sources using Gemini Flash

    Args:
        brief: ArticleBrief dict with context
        sources: List of Source dicts with content

    Returns:
        ResearchBrief dict with entities, citations, key_findings
    """
    activity.logger.info(f"🔍 Extracting entities/citations from {len(sources)} sources")

    try:
        # Combine source content
        combined_content = "\n\n---\n\n".join([
            f"Source: {s.get('title', 'Unknown')}\n{s.get('content', '')[:3000]}"
            for s in sources
        ])

        extraction_prompt = f"""Analyze this research content and extract:

1. Entities (people, organizations, technologies, products)
2. Key facts
3. Quotable passages for citations

Article Context:
Title: {brief.get('title', '')}
Angle: {brief.get('angle', '')}

Research Content:
{combined_content[:5000]}

Return ONLY a JSON object with this structure:
{{
  "entities": [
    {{"name": "...", "type": "...", "description": "...", "relevance": 8.0}}
  ],
  "citations": [
    {{"source_url": "...", "source_title": "...", "quote": "...", "context": "..."}}
  ],
  "key_findings": ["finding 1", "finding 2"],
  "research_summary": "Brief summary..."
}}"""

        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(extraction_prompt)
        content = response.text

        # Extract JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        extraction_data = json.loads(content)

        # Convert to proper structure
        result = {
            "sources": sources,
            "citations": extraction_data.get("citations", [])[:5],
            "entities": extraction_data.get("entities", [])[:10],
            "key_findings": extraction_data.get("key_findings", []),
            "research_summary": extraction_data.get("research_summary", "")
        }

        activity.logger.info(f"✅ Extracted {len(result['entities'])} entities, "
                           f"{len(result['citations'])} citations")

        return result

    except Exception as e:
        activity.logger.error(f"❌ Extraction failed: {e}")
        # Return minimal valid structure
        return {
            "sources": sources,
            "citations": [],
            "entities": [],
            "key_findings": [],
            "research_summary": "Extraction failed"
        }


@activity.defn(name="calculate_quality_score")
async def calculate_quality_score(article: Dict[str, Any]) -> float:
    """
    Calculate article quality score (simple heuristic)

    Args:
        article: Article dict

    Returns:
        Quality score (0-10)
    """
    score = 5.0  # Base score

    # Word count scoring
    word_count = article.get("word_count", 0)
    if word_count >= 1500:
        score += 2.0
    elif word_count >= 1000:
        score += 1.0

    # Citation scoring
    citations = len(article.get("citations", []))
    if citations >= 5:
        score += 2.0
    elif citations >= 3:
        score += 1.0

    # Cap at 10
    score = min(score, 10.0)

    activity.logger.info(f"📊 Quality score: {score:.1f}/10")

    return score


@activity.defn(name="sync_to_zep")
async def sync_to_zep(article: Dict[str, Any]) -> str:
    """
    Sync article to Zep knowledge base

    Args:
        article: Article dict

    Returns:
        Zep graph ID
    """
    # Placeholder - Zep integration to be added
    activity.logger.info("🔗 Zep sync (placeholder - to be implemented)")

    return f"zep-{article.get('id', 'unknown')}"
