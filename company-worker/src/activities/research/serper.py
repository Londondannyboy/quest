"""
Serper.dev Research Activity

Google search with geo-targeting support for company research.
"""

import httpx
from temporalio import activity
from typing import Dict, Any, List

from src.utils.config import config


# Geo-targeting map (Serper gl parameter)
GEO_MAP = {
    "UK": "uk",
    "US": "us",
    "SG": "sg",
    "EU": "de",  # Default to Germany for EU
    "DE": "de",
    "FR": "fr",
    "NL": "nl",
    "CH": "ch",
    "AU": "au",
    "CA": "ca",
    "IN": "in",
    "CN": "cn",
    "JP": "jp",
    "HK": "hk",
    "AE": "ae",
}


@activity.defn
async def fetch_company_news(
    domain: str,
    company_name: str,
    category: str,
    jurisdiction: str
) -> Dict[str, Any]:
    """
    Fetch company news using Serper.dev with geo-targeting.

    Strategy:
    1. Try domain-specific search first
    2. If insufficient results, try category + jurisdiction search
    3. Return top 10 results

    Args:
        domain: Company domain
        company_name: Company name
        category: Company category
        jurisdiction: Jurisdiction code for geo-targeting

    Returns:
        Dict with articles, query_used, jurisdiction, cost
    """
    activity.logger.info(
        f"Fetching news for {company_name} in {jurisdiction}"
    )

    if not config.SERPER_API_KEY:
        activity.logger.warning("SERPER_API_KEY not configured")
        return {
            "articles": [],
            "query_used": "",
            "jurisdiction": jurisdiction,
            "cost": 0.0,
            "error": "SERPER_API_KEY not configured"
        }

    # Get geo code
    gl = GEO_MAP.get(jurisdiction.upper(), "us")

    async with httpx.AsyncClient() as client:
        all_results = []

        # ===== STRATEGY 1: Domain-specific search =====
        query1 = f"{company_name} site:{domain}"
        activity.logger.info(f"Serper query 1: {query1} (gl={gl})")

        try:
            response1 = await client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": config.SERPER_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "q": query1,
                    "gl": gl,
                    "num": 10
                },
                timeout=30.0
            )

            if response1.status_code == 200:
                data = response1.json()
                results1 = data.get("organic", [])
                all_results.extend(results1)
                activity.logger.info(f"Query 1 returned {len(results1)} results")
            else:
                activity.logger.warning(
                    f"Serper query 1 failed: {response1.status_code}"
                )

        except Exception as e:
            activity.logger.error(f"Serper query 1 error: {e}")

        # ===== STRATEGY 2: Category + jurisdiction search =====
        if len(all_results) < 5:
            # Clean category for search
            category_clean = category.replace('_', ' ')

            query2 = f"{company_name} {category_clean} {jurisdiction}"
            activity.logger.info(f"Serper query 2: {query2} (gl={gl})")

            try:
                response2 = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": config.SERPER_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": query2,
                        "gl": gl,
                        "num": 10
                    },
                    timeout=30.0
                )

                if response2.status_code == 200:
                    data = response2.json()
                    results2 = data.get("organic", [])
                    all_results.extend(results2)
                    activity.logger.info(f"Query 2 returned {len(results2)} results")
                else:
                    activity.logger.warning(
                        f"Serper query 2 failed: {response2.status_code}"
                    )

            except Exception as e:
                activity.logger.error(f"Serper query 2 error: {e}")

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []

        for item in all_results:
            url = item.get("link", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append({
                    "title": item.get("title", ""),
                    "url": url,
                    "snippet": item.get("snippet", ""),
                    "date": item.get("date"),
                    "source": "serper"
                })

        # Limit to top 10
        final_results = unique_results[:10]

        # Cost calculation ($0.02 per 10 results, rounded up)
        num_queries = 2 if len(all_results) >= 5 else 1
        cost = num_queries * 0.02

        activity.logger.info(
            f"Serper search complete: {len(final_results)} unique articles, "
            f"cost: ${cost:.4f}"
        )

        return {
            "articles": final_results,
            "query_used": query2 if len(all_results) >= 5 else query1,
            "jurisdiction": jurisdiction,
            "geo_code": gl,
            "cost": cost,
            "num_queries": num_queries
        }


@activity.defn
async def fetch_targeted_research(
    domain: str,
    refined_query: str,
    jurisdiction: str
) -> Dict[str, Any]:
    """
    Fetch targeted research with refined query (used after ambiguity check).

    Args:
        domain: Company domain
        refined_query: Refined search query
        jurisdiction: Jurisdiction code

    Returns:
        Dict with articles, cost
    """
    activity.logger.info(f"Fetching targeted research: {refined_query}")

    if not config.SERPER_API_KEY:
        return {
            "articles": [],
            "cost": 0.0,
            "error": "SERPER_API_KEY not configured"
        }

    gl = GEO_MAP.get(jurisdiction.upper(), "us")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": config.SERPER_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "q": refined_query,
                    "gl": gl,
                    "num": 10
                },
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("organic", [])

                articles = [
                    {
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "date": item.get("date"),
                        "source": "serper_targeted"
                    }
                    for item in results
                ]

                activity.logger.info(
                    f"Targeted search returned {len(articles)} articles"
                )

                return {
                    "articles": articles,
                    "cost": 0.02,
                    "query": refined_query
                }

            else:
                activity.logger.error(
                    f"Serper targeted search failed: {response.status_code}"
                )
                return {
                    "articles": [],
                    "cost": 0.02,
                    "error": f"API returned {response.status_code}"
                }

    except Exception as e:
        activity.logger.error(f"Targeted search error: {e}")
        return {
            "articles": [],
            "cost": 0.02,
            "error": str(e)
        }
