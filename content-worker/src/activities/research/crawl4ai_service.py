"""
Crawl4AI Service Client

Calls external Railway Crawl4AI microservice for browser automation.
Falls back to httpx + BeautifulSoup if service unavailable.
"""

import httpx
from temporalio import activity
from typing import Dict, Any
from bs4 import BeautifulSoup

from src.utils.config import config


def normalize_url(url: str) -> str:
    """Ensure URL has a protocol and is valid."""
    if not url:
        return None
    url = url.strip()

    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        if url.startswith('//'):
            url = 'https:' + url
        else:
            url = 'https://' + url

    # Validate URL has a domain (not just protocol)
    # "https://" or "https:///" are invalid
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        if not parsed.netloc or len(parsed.netloc) < 3:
            return None  # No valid domain
        if '.' not in parsed.netloc:
            return None  # Domain must have at least one dot
    except Exception:
        return None

    return url


@activity.defn(name="crawl4ai_crawl")  # Alias for backward compatibility with old workflows
async def crawl4ai_service_crawl(url: str) -> Dict[str, Any]:
    """
    Crawl company website using external Crawl4AI service (browser automation).

    Strategy:
    1. Try external Crawl4AI service first (handles JavaScript-heavy sites)
    2. Fall back to httpx + BeautifulSoup if service unavailable

    Args:
        url: Company website URL

    Returns:
        Dict with success, pages, links, crawler (crawl4ai_service or httpx_fallback)
    """
    # Normalize URL to ensure it has a protocol
    url = normalize_url(url)

    if not url:
        return {
            "success": False,
            "error": "Empty URL provided",
            "crawler": "none"
        }

    activity.logger.info(f"Crawl4AI service crawl: {url}")

    # Try external service first
    if config.CRAWL4AI_SERVICE_URL:
        try:
            service_result = await call_crawl4ai_service(url)
            if service_result.get("success"):
                activity.logger.info(f"Crawl4AI service success: {url}")
                return service_result
            else:
                activity.logger.warning(
                    f"Crawl4AI service returned failure, falling back to httpx: {url}"
                )
        except Exception as e:
            activity.logger.warning(
                f"Crawl4AI service error, falling back to httpx: {e}"
            )
    else:
        activity.logger.info("CRAWL4AI_SERVICE_URL not configured, using httpx")

    # Fallback to httpx
    httpx_result = await crawl_with_httpx_fallback(url)
    return httpx_result


async def call_crawl4ai_service(base_url: str) -> Dict[str, Any]:
    """
    Call external Railway Crawl4AI microservice.

    Args:
        base_url: Company website URL

    Returns:
        Dict with success, pages, links, crawler="crawl4ai_service"
    """
    service_url = config.CRAWL4AI_SERVICE_URL

    if not service_url:
        raise ValueError("CRAWL4AI_SERVICE_URL not configured")

    # Remove trailing slash
    service_url = service_url.rstrip("/")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Call the scrape endpoint (matches job-worker pattern)
            response = await client.post(
                f"{service_url}/scrape",
                json={"url": base_url},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()

                # Transform service response to match expected format
                return {
                    "success": data.get("success", False),
                    "pages": data.get("pages", []),
                    "links": data.get("links", []),
                    "crawler": "crawl4ai_service",
                    "service_url": service_url
                }
            else:
                return {
                    "success": False,
                    "error": f"Service returned {response.status_code}",
                    "crawler": "crawl4ai_service"
                }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Service timeout",
                "crawler": "crawl4ai_service"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "crawler": "crawl4ai_service"
            }


@activity.defn(name="crawl4ai_batch")
async def crawl4ai_batch_crawl(urls: list, topic: str = "", keywords: list = None) -> Dict[str, Any]:
    """
    Batch crawl multiple URLs using Crawl4AI /crawl-articles endpoint.

    Uses BM25 content filtering to extract only topic-relevant content.
    Falls back to /crawl-many if topic not provided.

    Args:
        urls: List of URLs to crawl
        topic: Topic for BM25 relevance filtering (e.g., "Cyprus Digital Nomad Visa")
        keywords: Additional keywords for filtering

    Returns:
        Dict with success, pages, stats
    """
    if not urls:
        return {"success": True, "pages": [], "stats": {"total": 0}}

    # Normalize and filter URLs
    valid_urls = []
    for url in urls:
        normalized = normalize_url(url)
        if normalized:
            valid_urls.append(normalized)

    if not valid_urls:
        return {"success": True, "pages": [], "stats": {"total": 0, "invalid": len(urls)}}

    activity.logger.info(f"Crawl4AI batch crawl: {len(valid_urls)} URLs, topic: '{topic}'")

    if not config.CRAWL4AI_SERVICE_URL:
        activity.logger.warning("CRAWL4AI_SERVICE_URL not configured, falling back to httpx")
        # Fallback: crawl each URL individually with httpx
        pages = []
        for url in valid_urls[:20]:  # Limit to 20 for httpx fallback
            result = await crawl_with_httpx_fallback(url)
            if result.get("success") and result.get("pages"):
                pages.extend(result["pages"])
        return {
            "success": True,
            "pages": pages,
            "stats": {"total": len(valid_urls), "crawled": len(pages), "crawler": "httpx_fallback"}
        }

    service_url = config.CRAWL4AI_SERVICE_URL.rstrip("/")

    async with httpx.AsyncClient(timeout=270.0) as client:  # 4.5 min timeout (buffer before 5 min activity timeout)
        try:
            # Use /crawl-articles if topic provided, else /crawl-many
            if topic:
                # Optimized article research with BM25 filtering
                payload = {
                    "urls": valid_urls,
                    "topic": topic,
                    "keywords": keywords or [],
                    "parallel": 5,
                    "min_word_count": 50,
                    "use_pruning": True,
                    "use_bm25": True
                }
                endpoint = f"{service_url}/crawl-articles"
                activity.logger.info(f"Using /crawl-articles with BM25 filtering for: '{topic}'")
            else:
                # Basic batch crawl
                payload = {"urls": valid_urls}
                endpoint = f"{service_url}/crawl-many"
                activity.logger.info("Using /crawl-many (no topic filtering)")

            response = await client.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()

                # Transform results to pages format
                pages = []
                for result in data.get("results", []):
                    if result.get("success"):
                        pages.append({
                            "url": result.get("url"),
                            "title": result.get("title", ""),
                            "content": result.get("content", ""),
                            "filtered": result.get("filtered", False),
                            "source": "crawl4ai_articles" if topic else "crawl4ai_batch"
                        })

                filters_used = data.get("filters_used", {})
                activity.logger.info(
                    f"Crawl4AI complete: {data.get('successful', 0)}/{data.get('total_urls', 0)} successful, "
                    f"BM25={filters_used.get('bm25', False)}, Pruning={filters_used.get('pruning', False)}"
                )

                return {
                    "success": True,
                    "pages": pages,
                    "stats": {
                        "total": data.get("total_urls", 0),
                        "successful": data.get("successful", 0),
                        "failed": data.get("failed", 0),
                        "crawler": "crawl4ai_articles" if topic else "crawl4ai_batch",
                        "filters": filters_used
                    }
                }
            else:
                activity.logger.error(f"Crawl4AI failed: HTTP {response.status_code}")
                return {
                    "success": False,
                    "pages": [],
                    "error": f"HTTP {response.status_code}",
                    "stats": {"crawler": "crawl4ai"}
                }

        except Exception as e:
            activity.logger.error(f"Crawl4AI error: {e}")
            return {
                "success": False,
                "pages": [],
                "error": str(e),
                "stats": {"crawler": "crawl4ai"}
            }


async def crawl_with_httpx_fallback(base_url: str) -> Dict[str, Any]:
    """
    Fallback crawling with httpx + BeautifulSoup (free, local).

    Uses httpx for HTTP requests and BeautifulSoup for HTML parsing.
    No browser automation - pure HTTP scraping.

    Args:
        base_url: Company website URL

    Returns:
        Dict with success, pages, links, crawler="httpx_fallback"
    """
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            response = await client.get(
                base_url,
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

                # Extract links
                links = []
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    if href.startswith('http'):
                        links.append(href)
                    elif href.startswith('/'):
                        # Convert relative to absolute
                        from urllib.parse import urljoin
                        links.append(urljoin(base_url, href))

                # Limit to first 100 links
                links = links[:100]

                return {
                    "success": True,
                    "pages": [{
                        "url": base_url,
                        "content": text[:10000],  # Limit to 10k chars
                        "title": soup.title.string if soup.title else "",
                        "links": links
                    }],
                    "links": links,
                    "crawler": "httpx_fallback"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "crawler": "httpx_fallback"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "crawler": "httpx_fallback"
            }


@activity.defn(name="prefilter_urls_by_relevancy")
async def prefilter_urls_by_relevancy(
    url_candidates: list,
    topic: str,
    min_keyword_matches: int = 2,
    max_urls: int = 30
) -> Dict[str, Any]:
    """
    Pre-filter URLs by topic relevancy BEFORE crawling.

    Checks if title/snippet contains topic keywords to avoid crawling irrelevant pages.
    This saves crawl time and improves content quality.

    Args:
        url_candidates: List of dicts with {url, title, snippet, source}
        topic: Article topic for keyword extraction
        min_keyword_matches: Minimum keywords that must match (default 2)
        max_urls: Maximum URLs to return (default 30)

    Returns:
        Dict with relevant_urls, skipped_count, stats
    """
    activity.logger.info(f"Pre-filtering {len(url_candidates)} URLs for topic: '{topic}'")

    # Extract keywords from topic (words > 2 chars, lowercase)
    topic_keywords = [w.lower() for w in topic.split() if len(w) > 2]
    activity.logger.info(f"Topic keywords: {topic_keywords}")

    def is_relevant(title: str, snippet: str) -> bool:
        """Check if title/snippet mentions enough topic keywords."""
        text = f"{title} {snippet}".lower()
        matches = sum(1 for kw in topic_keywords if kw in text)
        return matches >= min_keyword_matches

    relevant_urls = []
    skipped = []

    for candidate in url_candidates:
        url = candidate.get("url", "")
        title = candidate.get("title", "")
        snippet = candidate.get("snippet", "")
        source = candidate.get("source", "unknown")

        if not url:
            continue

        if is_relevant(title, snippet):
            relevant_urls.append(url)
        else:
            skipped.append({
                "url": url,
                "title": title[:100],
                "source": source,
                "reason": "no_topic_match"
            })

    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for url in relevant_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    # Cap at max_urls
    capped = len(unique_urls) > max_urls
    final_urls = unique_urls[:max_urls]

    activity.logger.info(
        f"Pre-filter result: {len(final_urls)} relevant (from {len(url_candidates)} candidates), "
        f"{len(skipped)} skipped, capped={capped}"
    )

    return {
        "relevant_urls": final_urls,
        "skipped_count": len(skipped),
        "skipped_samples": skipped[:5],  # First 5 for debugging
        "total_candidates": len(url_candidates),
        "unique_before_cap": len(unique_urls),
        "capped": capped,
        "keywords_used": topic_keywords
    }
