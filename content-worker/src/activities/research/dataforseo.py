"""
DataForSEO API Activities
Primary source for news and SERP data with ISO timestamps
"""

import os
import base64
import json
import aiohttp
from typing import Any
from temporalio import activity

# DataForSEO location codes
LOCATION_CODES = {
    "UK": 2826,
    "US": 2840,
    "SG": 2702,  # Singapore
    "DE": 2276,  # Germany
    "FR": 2250,  # France
    "AU": 2036,  # Australia
    "CA": 2124,  # Canada
    "JP": 2392,  # Japan
    "HK": 2344,  # Hong Kong
}


def get_auth_header() -> str:
    """Get DataForSEO Basic Auth header"""
    login = os.getenv("DATAFORSEO_LOGIN", "")
    password = os.getenv("DATAFORSEO_PASSWORD", "")
    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()
    return f"Basic {credentials}"


@activity.defn
async def dataforseo_news_search(
    keywords: list[str],
    regions: list[str] = None,
    depth: int = 70
) -> dict[str, Any]:
    """
    Search news using DataForSEO Google News API

    Args:
        keywords: List of search keywords
        regions: List of region codes (UK, US, SG, etc.)
        depth: Number of results per query (1-200, default 10, recommended 70)

    Returns:
        Dict with articles list and metadata
    """
    if regions is None:
        regions = ["UK", "US", "SG"]

    url = "https://api.dataforseo.com/v3/serp/google/news/live/advanced"
    auth = get_auth_header()

    all_results = []
    total_cost = 0

    async with aiohttp.ClientSession() as session:
        for keyword in keywords:
            for region in regions:
                location_code = LOCATION_CODES.get(region, 2826)

                payload = [{
                    "keyword": keyword,
                    "location_code": location_code,
                    "language_code": "en",
                    "depth": depth,
                    "calculate_rectangles": False
                }]

                try:
                    async with session.post(
                        url,
                        json=payload,
                        headers={
                            "Authorization": auth,
                            "Content-Type": "application/json"
                        },
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()

                            if data.get("tasks") and data["tasks"][0].get("result"):
                                items = data["tasks"][0]["result"][0].get("items", [])
                                cost = data["tasks"][0].get("cost", 0)
                                total_cost += cost

                                for item in items:
                                    all_results.append({
                                        "title": item.get("title", ""),
                                        "url": item.get("url", ""),
                                        "source": item.get("domain", "").replace("www.", ""),
                                        "timestamp": item.get("timestamp", ""),
                                        "time_published": item.get("time_published", ""),
                                        "snippet": item.get("snippet", ""),
                                        "image_url": item.get("image_url", ""),
                                        "rank": item.get("rank_absolute", 0),
                                        "region": region,
                                        "keyword": keyword,
                                        "api_source": "dataforseo"
                                    })

                                activity.logger.info(
                                    f"DataForSEO news: {len(items)} results for '{keyword}' in {region}"
                                )
                        else:
                            activity.logger.error(
                                f"DataForSEO error: {response.status} for '{keyword}' in {region}"
                            )

                except Exception as e:
                    activity.logger.error(f"DataForSEO exception: {e}")
                    continue

    return {
        "articles": all_results,
        "total": len(all_results),
        "cost": total_cost,
        "regions": regions,
        "keywords": keywords
    }


@activity.defn
async def dataforseo_serp_search(
    query: str,
    region: str = "UK",
    depth: int = 50,
    include_ai_overview: bool = True,
    people_also_ask_depth: int = 4
) -> dict[str, Any]:
    """
    Search organic SERP results using DataForSEO with AI Overview and People Also Ask.
    Extracts URLs from ALL SERP features, not just organic results.

    Args:
        query: Search query
        region: Region code (UK, US, SG, etc.)
        depth: Number of results (1-200, default 50 = ~5 pages)
        include_ai_overview: Include Google AI Overview results
        people_also_ask_depth: Depth for "People also ask" results (0-4)

    Returns:
        Dict with organic results, feature URLs, AI overview, and metadata
    """
    url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
    auth = get_auth_header()
    location_code = LOCATION_CODES.get(region, 2826)

    payload = [{
        "keyword": query,
        "location_code": location_code,
        "language_code": "en",
        "device": "desktop",
        "os": "windows",
        "depth": depth,
        "group_organic_results": True,
        "load_async_ai_overview": include_ai_overview,
        "people_also_ask_click_depth": people_also_ask_depth,
        "calculate_rectangles": False
    }]

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                url,
                json=payload,
                headers={
                    "Authorization": auth,
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    organic_results = []
                    feature_urls = []  # URLs from SERP features
                    ai_overview_urls = []
                    paa_questions = []
                    cost = 0

                    if data.get("tasks") and data["tasks"][0].get("result"):
                        items = data["tasks"][0]["result"][0].get("items", [])
                        cost = data["tasks"][0].get("cost", 0)

                        for item in items:
                            item_type = item.get("type", "")

                            # Organic results - primary
                            if item_type == "organic":
                                organic_results.append({
                                    "title": item.get("title", ""),
                                    "url": item.get("url", ""),
                                    "source": item.get("domain", "").replace("www.", ""),
                                    "snippet": item.get("description", ""),
                                    "rank": item.get("rank_absolute", 0),
                                    "region": region,
                                    "type": "organic",
                                    "api_source": "dataforseo"
                                })

                            # Featured snippet
                            elif item_type == "featured_snippet":
                                if item.get("url"):
                                    feature_urls.append({
                                        "url": item.get("url"),
                                        "title": item.get("title", ""),
                                        "type": "featured_snippet"
                                    })

                            # People Also Ask - extract URLs from expanded answers
                            elif item_type == "people_also_ask":
                                paa_items = item.get("items", [])
                                for paa in paa_items:
                                    paa_questions.append(paa.get("title", ""))
                                    if paa.get("url"):
                                        feature_urls.append({
                                            "url": paa.get("url"),
                                            "title": paa.get("title", ""),
                                            "type": "people_also_ask"
                                        })

                            # AI Overview - extract reference URLs
                            elif item_type == "ai_overview":
                                refs = item.get("references", [])
                                for ref in refs:
                                    if ref.get("url"):
                                        ai_overview_urls.append({
                                            "url": ref.get("url"),
                                            "title": ref.get("title", ""),
                                            "type": "ai_overview"
                                        })

                            # Top stories (news)
                            elif item_type == "top_stories":
                                stories = item.get("items", [])
                                for story in stories:
                                    if story.get("url"):
                                        feature_urls.append({
                                            "url": story.get("url"),
                                            "title": story.get("title", ""),
                                            "type": "top_stories"
                                        })

                            # Video results
                            elif item_type == "video":
                                if item.get("url"):
                                    feature_urls.append({
                                        "url": item.get("url"),
                                        "title": item.get("title", ""),
                                        "type": "video"
                                    })

                            # Knowledge panel - extract URLs
                            elif item_type == "knowledge_panel":
                                if item.get("url"):
                                    feature_urls.append({
                                        "url": item.get("url"),
                                        "title": item.get("title", ""),
                                        "type": "knowledge_panel"
                                    })

                    # Combine all URLs for crawling
                    all_urls = []
                    seen_urls = set()

                    # Priority: organic first, then AI overview, then features
                    for r in organic_results:
                        if r["url"] and r["url"] not in seen_urls:
                            all_urls.append(r)
                            seen_urls.add(r["url"])

                    for r in ai_overview_urls:
                        if r["url"] and r["url"] not in seen_urls:
                            all_urls.append(r)
                            seen_urls.add(r["url"])

                    for r in feature_urls:
                        if r["url"] and r["url"] not in seen_urls:
                            all_urls.append(r)
                            seen_urls.add(r["url"])

                    activity.logger.info(
                        f"DataForSEO SERP: {len(organic_results)} organic, "
                        f"{len(ai_overview_urls)} AI overview, {len(feature_urls)} features "
                        f"= {len(all_urls)} unique URLs for '{query}'"
                    )

                    return {
                        "results": organic_results,
                        "all_urls": all_urls,  # All unique URLs for crawling
                        "ai_overview_urls": ai_overview_urls,
                        "feature_urls": feature_urls,
                        "paa_questions": paa_questions,
                        "total": len(all_urls),
                        "cost": cost,
                        "query": query,
                        "region": region
                    }
                else:
                    activity.logger.error(f"DataForSEO SERP error: {response.status}")
                    return {"results": [], "all_urls": [], "total": 0, "cost": 0, "error": f"HTTP {response.status}"}

        except Exception as e:
            activity.logger.error(f"DataForSEO SERP exception: {e}")
            return {"results": [], "all_urls": [], "total": 0, "cost": 0, "error": str(e)}


@activity.defn
async def dataforseo_keyword_research(
    seed_keyword: str,
    region: str = "UK",
    limit: int = 20
) -> dict[str, Any]:
    """
    Research keywords for SEO targeting using DataForSEO Keywords Data API.

    Returns keyword suggestions with search volume, difficulty, and CPC data.
    Use this to find the best keyword to target for an article.

    Args:
        seed_keyword: Topic or seed keyword to research (e.g., "private equity law firms")
        region: Region code (UK, US, SG, etc.)
        limit: Max number of keyword suggestions to return

    Returns:
        Dict with keyword suggestions including:
        - keyword: The keyword phrase
        - search_volume: Monthly search volume
        - competition: Competition level (LOW, MEDIUM, HIGH)
        - competition_index: 0-100 competition score
        - cpc: Cost per click (indicates commercial intent)
        - difficulty_score: Calculated difficulty (volume/competition balance)
    """
    url = "https://api.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/live"
    auth = get_auth_header()
    location_code = LOCATION_CODES.get(region, 2826)

    payload = [{
        "keywords": [seed_keyword],
        "location_code": location_code,
        "language_code": "en",
        "include_seed_keyword": True,
        "sort_by": "search_volume"
    }]

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                url,
                json=payload,
                headers={
                    "Authorization": auth,
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    keywords = []
                    cost = 0

                    if data.get("tasks") and data["tasks"][0].get("result"):
                        results = data["tasks"][0]["result"]
                        cost = data["tasks"][0].get("cost", 0)

                        for item in results[:limit]:
                            search_volume = item.get("search_volume", 0) or 0
                            competition_index = item.get("competition_index", 50) or 50
                            cpc = item.get("cpc", 0) or 0

                            # Calculate a simple difficulty score (lower is easier)
                            # Balances: high volume good, high competition bad
                            # Score = competition_index - (search_volume bonus)
                            volume_bonus = min(search_volume / 100, 30)  # Cap bonus at 30
                            difficulty_score = max(0, competition_index - volume_bonus)

                            # Calculate opportunity score (higher is better)
                            # High volume + low competition = high opportunity
                            opportunity_score = (search_volume / 10) * (100 - competition_index) / 100

                            keywords.append({
                                "keyword": item.get("keyword", ""),
                                "search_volume": search_volume,
                                "competition": item.get("competition", "UNKNOWN"),
                                "competition_index": competition_index,
                                "cpc": round(cpc, 2),
                                "difficulty_score": round(difficulty_score, 1),
                                "opportunity_score": round(opportunity_score, 1),
                            })

                        # Sort by opportunity score (best opportunities first)
                        keywords.sort(key=lambda x: x["opportunity_score"], reverse=True)

                    activity.logger.info(
                        f"DataForSEO keywords: {len(keywords)} results for '{seed_keyword}' in {region}"
                    )

                    return {
                        "keywords": keywords,
                        "seed_keyword": seed_keyword,
                        "region": region,
                        "total": len(keywords),
                        "cost": cost,
                        "best_keyword": keywords[0] if keywords else None
                    }
                else:
                    error_text = await response.text()
                    activity.logger.error(f"DataForSEO keywords error: {response.status} - {error_text}")
                    return {
                        "keywords": [],
                        "seed_keyword": seed_keyword,
                        "total": 0,
                        "cost": 0,
                        "error": f"HTTP {response.status}"
                    }

        except Exception as e:
            activity.logger.error(f"DataForSEO keywords exception: {e}")
            return {
                "keywords": [],
                "seed_keyword": seed_keyword,
                "total": 0,
                "cost": 0,
                "error": str(e)
            }


@activity.defn
async def dataforseo_keyword_difficulty(
    keywords: list[str],
    region: str = "UK"
) -> dict[str, Any]:
    """
    Get detailed keyword difficulty and SERP analysis for specific keywords.

    Use this after keyword_research to get detailed difficulty metrics
    for your top keyword candidates.

    Args:
        keywords: List of keywords to analyze (max 10 recommended)
        region: Region code (UK, US, SG, etc.)

    Returns:
        Dict with difficulty analysis for each keyword
    """
    url = "https://api.dataforseo.com/v3/dataforseo_labs/google/keyword_ideas/live"
    auth = get_auth_header()
    location_code = LOCATION_CODES.get(region, 2826)

    payload = [{
        "keywords": keywords[:10],  # Limit to 10 keywords
        "location_code": location_code,
        "language_code": "en",
        "include_serp_info": True,
        "include_seed_keyword": True
    }]

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                url,
                json=payload,
                headers={
                    "Authorization": auth,
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    results = []
                    cost = 0

                    if data.get("tasks") and data["tasks"][0].get("result"):
                        items = data["tasks"][0]["result"]
                        cost = data["tasks"][0].get("cost", 0)

                        for item in items:
                            keyword_info = item.get("keyword_info", {})
                            serp_info = item.get("serp_info", {})

                            results.append({
                                "keyword": item.get("keyword", ""),
                                "search_volume": keyword_info.get("search_volume", 0),
                                "competition_index": keyword_info.get("competition_index", 0),
                                "cpc": keyword_info.get("cpc", 0),
                                "keyword_difficulty": item.get("keyword_difficulty", 50),
                                "serp_features": serp_info.get("serp_item_types", []),
                                "has_featured_snippet": "featured_snippet" in serp_info.get("serp_item_types", []),
                                "has_people_also_ask": "people_also_ask" in serp_info.get("serp_item_types", []),
                            })

                    activity.logger.info(
                        f"DataForSEO difficulty: analyzed {len(results)} keywords"
                    )

                    return {
                        "results": results,
                        "total": len(results),
                        "cost": cost
                    }
                else:
                    activity.logger.error(f"DataForSEO difficulty error: {response.status}")
                    return {"results": [], "total": 0, "cost": 0, "error": f"HTTP {response.status}"}

        except Exception as e:
            activity.logger.error(f"DataForSEO difficulty exception: {e}")
            return {"results": [], "total": 0, "cost": 0, "error": str(e)}
