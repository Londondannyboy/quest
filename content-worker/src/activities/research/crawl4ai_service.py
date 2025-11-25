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
async def crawl4ai_batch_crawl(urls: list) -> Dict[str, Any]:
    """
    Batch crawl multiple URLs using Crawl4AI /crawl-many endpoint.

    Much more efficient than calling /scrape in a loop.

    Args:
        urls: List of URLs to crawl

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

    activity.logger.info(f"Crawl4AI batch crawl: {len(valid_urls)} URLs")

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

    async with httpx.AsyncClient(timeout=180.0) as client:  # 3 min timeout for batch
        try:
            response = await client.post(
                f"{service_url}/crawl-many",
                json={"urls": valid_urls},
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
                            "source": "crawl4ai_batch"
                        })

                activity.logger.info(
                    f"Crawl4AI batch complete: {data.get('successful', 0)}/{data.get('total_urls', 0)} successful"
                )

                return {
                    "success": True,
                    "pages": pages,
                    "stats": {
                        "total": data.get("total_urls", 0),
                        "successful": data.get("successful", 0),
                        "failed": data.get("failed", 0),
                        "crawler": "crawl4ai_batch"
                    }
                }
            else:
                activity.logger.error(f"Crawl4AI batch failed: HTTP {response.status_code}")
                return {
                    "success": False,
                    "pages": [],
                    "error": f"HTTP {response.status_code}",
                    "stats": {"crawler": "crawl4ai_batch"}
                }

        except Exception as e:
            activity.logger.error(f"Crawl4AI batch error: {e}")
            return {
                "success": False,
                "pages": [],
                "error": str(e),
                "stats": {"crawler": "crawl4ai_batch"}
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
