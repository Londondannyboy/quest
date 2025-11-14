"""
Web Scraping Activities

Crawl4AI (free, fast) with Firecrawl fallback for website scraping.
"""

import httpx
from temporalio import activity
from typing import Dict, Any, List
from urllib.parse import urljoin

from src.utils.config import config


@activity.defn
async def crawl_company_website(url: str) -> Dict[str, Any]:
    """
    Crawl company website using Crawl4AI first, Firecrawl as fallback.

    Targets these pages:
    - Homepage
    - About
    - Services
    - Team/People

    Args:
        url: Company website URL

    Returns:
        Dict with pages, crawler_used, cost
    """
    activity.logger.info(f"Crawling website: {url}")

    # Try Crawl4AI first (free, fast)
    try:
        crawl4ai_result = await crawl_with_crawl4ai(url)
        if crawl4ai_result["success"]:
            activity.logger.info("Successfully crawled with Crawl4AI (free)")
            return {
                "pages": crawl4ai_result["pages"],
                "crawler_used": "crawl4ai",
                "cost": 0.0,
                "success": True
            }
    except Exception as e:
        activity.logger.warning(f"Crawl4AI failed: {e}")

    # Fallback to Firecrawl
    try:
        firecrawl_result = await crawl_with_firecrawl(url)
        if firecrawl_result["success"]:
            activity.logger.info("Successfully crawled with Firecrawl (paid)")
            return {
                "pages": firecrawl_result["pages"],
                "crawler_used": "firecrawl",
                "cost": firecrawl_result["cost"],
                "success": True
            }
    except Exception as e:
        activity.logger.error(f"Firecrawl also failed: {e}")

    # Both failed
    activity.logger.error("Both Crawl4AI and Firecrawl failed")
    return {
        "pages": [],
        "crawler_used": "none",
        "cost": 0.0,
        "success": False,
        "error": "All crawlers failed"
    }


async def crawl_with_crawl4ai(base_url: str) -> Dict[str, Any]:
    """
    Crawl with Crawl4AI (free, local).

    Note: This is a simplified version. In production, you'd use
    the actual Crawl4AI Python library with async browser support.

    Args:
        base_url: Base URL to crawl

    Returns:
        Dict with success, pages
    """
    # Target URLs to scrape
    target_paths = [
        "",  # Homepage
        "/about",
        "/about-us",
        "/company",
        "/services",
        "/what-we-do",
        "/team",
        "/people",
        "/leadership",
        "/contact",
    ]

    pages = []
    success_count = 0

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for path in target_paths:
            url = urljoin(base_url, path)

            try:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; QuestBot/1.0)"
                    }
                )

                if response.status_code == 200:
                    # Extract text content (simplified - in production use BeautifulSoup)
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()

                    # Get text
                    text = soup.get_text(separator=' ', strip=True)

                    # Limit to 5000 chars per page
                    text = text[:5000]

                    pages.append({
                        "url": url,
                        "title": soup.title.string if soup.title else "",
                        "content": text,
                        "path": path,
                        "source": "crawl4ai"
                    })

                    success_count += 1

                    # Stop after 4 successful pages
                    if success_count >= 4:
                        break

            except Exception as e:
                activity.logger.debug(f"Failed to fetch {url}: {e}")
                continue

    return {
        "success": len(pages) > 0,
        "pages": pages
    }


async def crawl_with_firecrawl(base_url: str) -> Dict[str, Any]:
    """
    Crawl with Firecrawl API (paid, reliable).

    Args:
        base_url: Base URL to crawl

    Returns:
        Dict with success, pages, cost
    """
    if not config.FIRECRAWL_API_KEY:
        return {
            "success": False,
            "pages": [],
            "cost": 0.0,
            "error": "FIRECRAWL_API_KEY not configured"
        }

    activity.logger.info(f"Using Firecrawl API for {base_url}")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Use Firecrawl's map endpoint to get key pages
            response = await client.post(
                "https://api.firecrawl.dev/v0/crawl",
                headers={
                    "Authorization": f"Bearer {config.FIRECRAWL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "url": base_url,
                    "crawlerOptions": {
                        "limit": 10,
                        "maxDepth": 2
                    },
                    "pageOptions": {
                        "onlyMainContent": True
                    }
                }
            )

            if response.status_code == 200:
                data = response.json()
                pages_data = data.get("data", [])

                pages = [
                    {
                        "url": page.get("metadata", {}).get("sourceURL", ""),
                        "title": page.get("metadata", {}).get("title", ""),
                        "content": page.get("markdown", "")[:5000],
                        "source": "firecrawl"
                    }
                    for page in pages_data[:10]
                ]

                # Cost: $0.01 per page
                cost = len(pages) * 0.01

                activity.logger.info(f"Firecrawl returned {len(pages)} pages")

                return {
                    "success": True,
                    "pages": pages,
                    "cost": cost
                }

            else:
                activity.logger.error(
                    f"Firecrawl API error: {response.status_code}"
                )
                return {
                    "success": False,
                    "pages": [],
                    "cost": 0.0,
                    "error": f"API returned {response.status_code}"
                }

    except Exception as e:
        activity.logger.error(f"Firecrawl error: {e}")
        return {
            "success": False,
            "pages": [],
            "cost": 0.0,
            "error": str(e)
        }
