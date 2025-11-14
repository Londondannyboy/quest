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
async def crawl4ai_crawl(url: str) -> Dict[str, Any]:
    """
    Crawl company website using Crawl4AI (free, fast).

    Args:
        url: Company website URL

    Returns:
        Dict with pages, success, cost (always 0)
    """
    activity.logger.info(f"Crawl4AI crawling: {url}")

    try:
        result = await crawl_with_crawl4ai(url)
        activity.logger.info(f"Crawl4AI: {len(result.get('pages', []))} pages")
        return {
            "pages": result.get("pages", []),
            "success": result.get("success", False),
            "cost": 0.0,
            "crawler": "crawl4ai"
        }
    except Exception as e:
        activity.logger.error(f"Crawl4AI failed: {e}")
        return {
            "pages": [],
            "success": False,
            "cost": 0.0,
            "error": str(e),
            "crawler": "crawl4ai"
        }


@activity.defn
async def firecrawl_crawl(url: str) -> Dict[str, Any]:
    """
    Crawl company website using Firecrawl (paid, reliable).

    Args:
        url: Company website URL

    Returns:
        Dict with pages, success, cost
    """
    activity.logger.info(f"Firecrawl crawling: {url}")

    try:
        result = await crawl_with_firecrawl(url)
        activity.logger.info(f"Firecrawl: {len(result.get('pages', []))} pages, cost: ${result.get('cost', 0):.4f}")
        return {
            "pages": result.get("pages", []),
            "success": result.get("success", False),
            "cost": result.get("cost", 0.0),
            "error": result.get("error"),
            "crawler": "firecrawl"
        }
    except Exception as e:
        activity.logger.error(f"Firecrawl failed: {e}")
        return {
            "pages": [],
            "success": False,
            "cost": 0.0,
            "error": str(e),
            "crawler": "firecrawl"
        }


@activity.defn
async def crawl_company_website(url: str) -> Dict[str, Any]:
    """
    Crawl company website using BOTH Crawl4AI and Firecrawl in parallel.

    This maximizes data coverage by using two different crawling strategies:
    - Crawl4AI: Free, fast, targets specific paths
    - Firecrawl: Paid, reliable, intelligent page discovery

    Targets these pages:
    - Homepage
    - About
    - Services
    - Team/People
    - Deals/Portfolio
    - Clients

    Args:
        url: Company website URL

    Returns:
        Dict with pages (from both), crawlers_used, cost, source breakdown
    """
    activity.logger.info(f"Crawling website with both Crawl4AI and Firecrawl: {url}")

    # Run BOTH crawlers in parallel
    import asyncio
    crawl4ai_task = crawl_with_crawl4ai(url)
    firecrawl_task = crawl_with_firecrawl(url)

    try:
        crawl4ai_result, firecrawl_result = await asyncio.gather(
            crawl4ai_task,
            firecrawl_task,
            return_exceptions=True
        )
    except Exception as e:
        activity.logger.error(f"Failed to run parallel crawls: {e}")
        crawl4ai_result = {"success": False, "pages": [], "error": str(e)}
        firecrawl_result = {"success": False, "pages": [], "cost": 0.0, "error": str(e)}

    # Handle exceptions
    if isinstance(crawl4ai_result, Exception):
        activity.logger.warning(f"Crawl4AI failed: {crawl4ai_result}")
        crawl4ai_result = {"success": False, "pages": [], "error": str(crawl4ai_result)}

    if isinstance(firecrawl_result, Exception):
        activity.logger.warning(f"Firecrawl failed: {firecrawl_result}")
        firecrawl_result = {"success": False, "pages": [], "cost": 0.0, "error": str(firecrawl_result)}

    # Combine results
    all_pages = []
    crawlers_used = []

    if crawl4ai_result.get("success"):
        all_pages.extend(crawl4ai_result["pages"])
        crawlers_used.append("crawl4ai")
        activity.logger.info(f"Crawl4AI returned {len(crawl4ai_result['pages'])} pages")

    if firecrawl_result.get("success"):
        all_pages.extend(firecrawl_result["pages"])
        crawlers_used.append("firecrawl")
        activity.logger.info(f"Firecrawl returned {len(firecrawl_result['pages'])} pages")

    total_cost = firecrawl_result.get("cost", 0.0)

    activity.logger.info(
        f"Combined crawl results: {len(all_pages)} total pages "
        f"(Crawl4AI: {len(crawl4ai_result.get('pages', []))}, "
        f"Firecrawl: {len(firecrawl_result.get('pages', []))}), "
        f"cost: ${total_cost:.4f}"
    )

    return {
        "pages": all_pages,
        "crawlers_used": crawlers_used,
        "cost": total_cost,
        "success": len(all_pages) > 0,
        "crawl4ai_pages": len(crawl4ai_result.get("pages", [])),
        "firecrawl_pages": len(firecrawl_result.get("pages", [])),
        "crawl4ai_success": crawl4ai_result.get("success", False),
        "firecrawl_success": firecrawl_result.get("success", False),
        "crawl4ai_error": crawl4ai_result.get("error"),
        "firecrawl_error": firecrawl_result.get("error")
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
        "/solutions",
        "/team",
        "/people",
        "/leadership",
        "/our-team",
        "/deals",
        "/portfolio",
        "/transactions",
        "/track-record",
        "/investments",
        "/clients",
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

                    # Stop after 8 successful pages (increased for better coverage)
                    if success_count >= 8:
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
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Step 1: Start Firecrawl v2 crawl job
            response = await client.post(
                "https://api.firecrawl.dev/v2/crawl",
                headers={
                    "Authorization": f"Bearer {config.FIRECRAWL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "url": base_url,
                    "sitemap": "include",
                    "crawlEntireDomain": False,
                    "limit": 10,
                    "scrapeOptions": {
                        "onlyMainContent": False,
                        "maxAge": 172800000,  # 48 hours
                        "parsers": ["pdf"],
                        "formats": ["markdown"]
                    }
                }
            )

            if response.status_code != 200:
                activity.logger.error(
                    f"Firecrawl API error: {response.status_code} - {response.text}"
                )
                return {
                    "success": False,
                    "pages": [],
                    "cost": 0.0,
                    "error": f"API returned {response.status_code}"
                }

            # Get crawl ID from response
            data = response.json()
            crawl_id = data.get("id")

            if not crawl_id:
                return {
                    "success": False,
                    "pages": [],
                    "cost": 0.0,
                    "error": "No crawl ID returned"
                }

            activity.logger.info(f"Firecrawl crawl started: {crawl_id}")

            # Step 2: Poll for completion (v2 API is async)
            import asyncio
            max_polls = 30  # 30 polls * 3 seconds = 90 seconds max

            for poll_count in range(max_polls):
                await asyncio.sleep(3)  # Wait 3 seconds between polls

                status_response = await client.get(
                    f"https://api.firecrawl.dev/v2/crawl/{crawl_id}",
                    headers={
                        "Authorization": f"Bearer {config.FIRECRAWL_API_KEY}"
                    }
                )

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    crawl_status = status_data.get("status")

                    activity.logger.info(f"Firecrawl poll {poll_count+1}: status={crawl_status}")

                    if crawl_status == "completed":
                        # Extract pages from completed crawl
                        pages_data = status_data.get("data", [])

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

                        activity.logger.info(f"Firecrawl completed: {len(pages)} pages")

                        return {
                            "success": True,
                            "pages": pages,
                            "cost": cost
                        }

                    elif crawl_status == "failed":
                        return {
                            "success": False,
                            "pages": [],
                            "cost": 0.0,
                            "error": "Crawl failed"
                        }

                    # Still in progress, continue polling

            # Timeout - crawl didn't complete in time
            activity.logger.warning("Firecrawl crawl timeout after 90 seconds")
            return {
                "success": False,
                "pages": [],
                "cost": 0.0,
                "error": "Crawl timeout"
            }

    except Exception as e:
        activity.logger.error(f"Firecrawl error: {e}")
        return {
            "success": False,
            "pages": [],
            "cost": 0.0,
            "error": str(e)
        }
