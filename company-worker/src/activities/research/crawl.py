"""
Web Scraping Activities

Crawl4AI (free, fast) with Firecrawl fallback for website scraping.
"""

import httpx
import re
from temporalio import activity
from typing import Dict, Any, List
from urllib.parse import urljoin, urlparse

from src.utils.config import config


@activity.defn(name="crawl4ai_crawl")  # Alias for backward compatibility with old workflows
async def httpx_crawl(url: str) -> Dict[str, Any]:
    """
    Crawl company website using httpx + BeautifulSoup (free, fast).

    Args:
        url: Company website URL

    Returns:
        Dict with pages, success, cost (always 0)
    """
    activity.logger.info(f"HTTPX crawling: {url}")

    try:
        result = await crawl_with_httpx(url)
        activity.logger.info(f"HTTPX: {len(result.get('pages', []))} pages")
        return {
            "pages": result.get("pages", []),
            "success": result.get("success", False),
            "cost": 0.0,
            "crawler": "httpx"
        }
    except Exception as e:
        activity.logger.error(f"HTTPX crawl failed: {e}")
        return {
            "pages": [],
            "success": False,
            "cost": 0.0,
            "error": str(e),
            "crawler": "httpx"
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


async def crawl_with_httpx(base_url: str) -> Dict[str, Any]:
    """
    Crawl with httpx + BeautifulSoup (free, local).

    Uses httpx for HTTP requests and BeautifulSoup for HTML parsing.
    No browser automation - pure HTTP scraping.

    Args:
        base_url: Base URL to crawl

    Returns:
        Dict with success, pages
    """
    # Target URLs to scrape
    # PRIORITY: Dynamic content pages (blogs, news, announcements) often have recent updates
    target_paths = [
        "",  # Homepage

        # Company info (static)
        "/about",
        "/about-us",
        "/company",

        # Services
        "/services",
        "/what-we-do",
        "/solutions",
        "/expertise",

        # Team/Leadership
        "/team",
        "/people",
        "/leadership",
        "/our-team",

        # Deals/Portfolio/Transactions (HIGH PRIORITY - structured deal data)
        "/deals",
        "/portfolio",
        "/transactions",
        "/our-transactions",
        "/track-record",
        "/investments",
        "/companies",
        "/case-studies",

        # News/Blog/Announcements (HIGH PRIORITY - recent updates)
        "/news",
        "/news-insights",
        "/news-insights/news",
        "/newsroom",
        "/blog",
        "/insights",
        "/articles",
        "/press",
        "/press-releases",
        "/media",
        "/announcements",
        "/updates",
        "/perspectives",
        "/thought-leadership",
        "/latest-news",
        "/news-and-insights",

        # Clients/Contact
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


# Keywords to identify relevant pages
RELEVANT_URL_KEYWORDS = [
    "news",
    "insights",
    "deals",
    "transactions",
    "portfolio",
    "case-studies",
    "announcements",
    "press",
    "media",
    "blog",
    "articles",
    "updates",
    "perspectives",
    "thought-leadership",
]


def extract_urls_from_markdown(markdown: str, base_url: str) -> List[str]:
    """
    Extract URLs from Firecrawl markdown output.

    Args:
        markdown: Firecrawl markdown output
        base_url: Base URL for resolving relative links

    Returns:
        List of absolute URLs
    """
    # Match markdown links: [text](url)
    markdown_links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', markdown)

    urls = []
    for text, url in markdown_links:
        # Skip anchors, mailto, tel
        if url.startswith(('#', 'mailto:', 'tel:')):
            continue

        # Resolve relative URLs
        absolute_url = urljoin(base_url, url)

        # Only include URLs from same domain
        base_domain = urlparse(base_url).netloc
        url_domain = urlparse(absolute_url).netloc

        if url_domain == base_domain:
            urls.append(absolute_url)

    return list(set(urls))  # Deduplicate


def filter_relevant_urls(urls: List[str]) -> List[str]:
    """
    Filter URLs to only those containing relevant keywords.

    Args:
        urls: List of URLs

    Returns:
        Filtered list of relevant URLs
    """
    relevant = []

    for url in urls:
        url_lower = url.lower()

        # Check if URL contains any relevant keyword
        if any(keyword in url_lower for keyword in RELEVANT_URL_KEYWORDS):
            relevant.append(url)

    return relevant


@activity.defn(name="firecrawl_crawl4ai_discover_and_scrape")  # Alias for backward compatibility
async def firecrawl_httpx_discover(base_url: str) -> Dict[str, Any]:
    """
    Use Firecrawl to discover URLs, then httpx to scrape relevant pages.

    Strategy:
    1. Firecrawl homepage → get markdown with navigation links
    2. Extract all URLs from markdown
    3. Filter to relevant keywords (news, insights, deals, etc.)
    4. HTTPX scrapes discovered URLs in parallel

    Args:
        base_url: Company website URL

    Returns:
        Dict with pages, discovered_urls, crawlers_used, cost
    """
    activity.logger.info(f"Firecrawl discovering URLs, then HTTPX scraping: {base_url}")

    # Step 1: Firecrawl homepage to discover URLs
    firecrawl_result = await crawl_with_firecrawl(base_url)

    if not firecrawl_result.get("success"):
        activity.logger.warning("Firecrawl failed, falling back to HTTPX only")
        httpx_result = await crawl_with_httpx(base_url)
        return {
            "pages": httpx_result.get("pages", []),
            "discovered_urls": [],
            "crawlers_used": ["httpx"],
            "cost": 0.0,
            "success": httpx_result.get("success", False)
        }

    # Step 2: Extract URLs from Firecrawl markdown
    firecrawl_pages = firecrawl_result.get("pages", [])
    all_discovered_urls = []

    for page in firecrawl_pages:
        markdown = page.get("content", "")
        page_url = page.get("url", base_url)

        urls = extract_urls_from_markdown(markdown, page_url)
        all_discovered_urls.extend(urls)

    # Deduplicate
    all_discovered_urls = list(set(all_discovered_urls))

    activity.logger.info(f"Firecrawl discovered {len(all_discovered_urls)} URLs from markdown")

    # Step 3: Filter to relevant URLs
    relevant_urls = filter_relevant_urls(all_discovered_urls)

    activity.logger.info(
        f"Filtered to {len(relevant_urls)} relevant URLs "
        f"(keywords: {', '.join(RELEVANT_URL_KEYWORDS[:5])}...)"
    )

    # Step 4: HTTPX scrapes discovered URLs (limit to 10)
    crawled_pages = []

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for url in relevant_urls[:10]:
            try:
                activity.logger.info(f"HTTPX scraping discovered URL: {url}")

                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; QuestBot/1.0)"
                    }
                )

                if response.status_code == 200:
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()

                    # Get text
                    text = soup.get_text(separator=' ', strip=True)

                    # Limit to 5000 chars
                    text = text[:5000]

                    crawled_pages.append({
                        "url": url,
                        "title": soup.title.string if soup.title else "",
                        "content": text,
                        "source": "crawl4ai_discovered"
                    })

                    activity.logger.info(f"Crawl4AI success: {len(text)} chars from {url}")

            except Exception as e:
                activity.logger.debug(f"Failed to scrape {url}: {e}")
                continue

    # Combine Firecrawl pages + HTTPX discovered pages
    all_pages = firecrawl_pages + crawled_pages

    firecrawl_cost = firecrawl_result.get("cost", 0.0)

    activity.logger.info(
        f"Discovery complete: {len(all_pages)} total pages "
        f"(Firecrawl: {len(firecrawl_pages)}, HTTPX discovered: {len(crawled_pages)}), "
        f"cost: ${firecrawl_cost:.4f}"
    )

    return {
        "pages": all_pages,
        "discovered_urls": relevant_urls[:10],
        "crawlers_used": ["firecrawl", "httpx_discovered"],
        "cost": firecrawl_cost,
        "success": len(all_pages) > 0,
        "firecrawl_pages": len(firecrawl_pages),
        "httpx_discovered_pages": len(crawled_pages)
    }
