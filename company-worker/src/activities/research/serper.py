"""
Serper.dev Research Activity

Google search with geo-targeting support for company research.
"""

import httpx
from temporalio import activity
from typing import Dict, Any, List

from src.utils.config import config
from bs4 import BeautifulSoup


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
        ran_query2 = False
        query2 = None

        if len(all_results) < 5:
            ran_query2 = True
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
        num_queries = 2 if ran_query2 else 1
        cost = num_queries * 0.02

        activity.logger.info(
            f"Serper search complete: {len(final_results)} unique articles, "
            f"cost: ${cost:.4f}"
        )

        return {
            "articles": final_results,
            "query_used": query2 if ran_query2 else query1,
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


# Paywall domains to exclude
PAYWALL_DOMAINS = {
    "wsj.com",
    "ft.com",
    "bloomberg.com",
    "economist.com",
    "nytimes.com",
    "washingtonpost.com",
    "telegraph.co.uk",
    "thetimes.co.uk",
    "barrons.com",
    "foreignpolicy.com",
    "theinformation.com",
}


@activity.defn
async def serper_httpx_deep_articles(
    articles: List[Dict[str, Any]],
    max_articles: int = 4
) -> Dict[str, Any]:
    """
    Deep crawl news articles found by Serper using httpx + BeautifulSoup.

    Filters out paywalled content and scrapes full article text.

    Args:
        articles: List of articles from fetch_company_news
        max_articles: Maximum articles to crawl (default 4)

    Returns:
        Dict with crawled_articles, skipped_paywalled, cost (always 0)
    """
    activity.logger.info(f"Deep crawling {len(articles)} articles (max {max_articles})")

    crawled_articles = []
    skipped_paywalled = []

    # Filter out paywalled domains
    non_paywalled = []
    for article in articles:
        url = article.get("url", "")
        domain = url.split("//")[-1].split("/")[0].replace("www.", "")

        if any(paywall in domain for paywall in PAYWALL_DOMAINS):
            activity.logger.debug(f"Skipping paywalled domain: {domain}")
            skipped_paywalled.append({
                "url": url,
                "domain": domain,
                "title": article.get("title", "")
            })
        else:
            non_paywalled.append(article)

    activity.logger.info(
        f"Filtered: {len(non_paywalled)} non-paywalled, "
        f"{len(skipped_paywalled)} paywalled"
    )

    # Crawl top N non-paywalled articles
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for article in non_paywalled[:max_articles]:
            url = article.get("url", "")

            try:
                activity.logger.info(f"Crawl4AI scraping: {url}")

                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; QuestBot/1.0)"
                    }
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Remove script, style, nav, footer
                    for element in soup(["script", "style", "nav", "footer", "header"]):
                        element.decompose()

                    # Get text
                    text = soup.get_text(separator=' ', strip=True)

                    # Check if likely paywalled (very short content)
                    if len(text) < 500:
                        activity.logger.warning(
                            f"Article too short ({len(text)} chars), likely paywalled: {url}"
                        )
                        skipped_paywalled.append({
                            "url": url,
                            "reason": "content_too_short",
                            "title": article.get("title", "")
                        })
                        continue

                    # Limit to 10,000 chars
                    text = text[:10000]

                    crawled_articles.append({
                        "url": url,
                        "title": article.get("title", ""),
                        "content": text,
                        "original_snippet": article.get("snippet", ""),
                        "date": article.get("date"),
                        "source": "serper_crawl4ai_deep"
                    })

                    activity.logger.info(
                        f"Crawl4AI success: {len(text)} chars from {url}"
                    )

                else:
                    activity.logger.warning(
                        f"Crawl4AI failed: {response.status_code} for {url}"
                    )

            except Exception as e:
                activity.logger.error(f"Crawl4AI error for {url}: {e}")
                continue

    activity.logger.info(
        f"Deep crawl complete: {len(crawled_articles)} articles, "
        f"{len(skipped_paywalled)} skipped (paywalled)"
    )

    return {
        "crawled_articles": crawled_articles,
        "skipped_paywalled": skipped_paywalled,
        "articles_crawled": len(crawled_articles),
        "cost": 0.0,  # Free - using Crawl4AI
        "success": len(crawled_articles) > 0
    }
