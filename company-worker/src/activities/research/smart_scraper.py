"""
Smart Scraper Strategy
Intelligently chooses between Crawl4AI, BeautifulSoup, and Firecrawl based on the site

Strategy:
1. Check if site has embedded JSON (Ashby, etc.) -> Use BeautifulSoup (fastest, free)
2. Check if site needs JavaScript -> Use Crawl4AI (free, handles JS)
3. Fallback to Firecrawl only if credits available and other methods fail
"""

import httpx
import re
import json
from temporalio import activity
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from src.utils.config import config


# Known patterns for different site types
EMBEDDED_JSON_SITES = {
    "ashbyhq.com": {"pattern": r'window\.__appData\s*=\s*({.*?});', "key": "jobBoard"},
    "greenhouse.io": {"pattern": r'window\.jobData\s*=\s*({.*?});', "key": "jobs"},
    "lever.co": {"pattern": r'window\.leverJobsData\s*=\s*({.*?});', "key": "jobs"},
}

JAVASCRIPT_REQUIRED_SITES = [
    "workday.com",
    "taleo.net",
    "ultipro.com",
    "icims.com",
]


@activity.defn
async def smart_scrape(url: str) -> Dict[str, Any]:
    """
    Intelligently scrape a website using the best available method.
    
    Decision tree:
    1. Try BeautifulSoup for embedded JSON (fastest, free)
    2. Use Crawl4AI for JS-heavy sites (free, handles JS)
    3. Fallback to Firecrawl only if necessary (paid)
    
    Args:
        url: Website URL to scrape
        
    Returns:
        Dict with success, content, method_used, cost
    """
    activity.logger.info(f"Smart scraping: {url}")
    
    domain = urlparse(url).netloc
    
    # Step 1: Check if it's a known embedded JSON site
    for pattern_domain, pattern_info in EMBEDDED_JSON_SITES.items():
        if pattern_domain in domain:
            result = await scrape_embedded_json(url, pattern_info)
            if result["success"]:
                activity.logger.info(f"✅ BeautifulSoup succeeded for {domain}")
                return result
    
    # Step 2: Try BeautifulSoup first (it's free and fast)
    bs_result = await scrape_with_beautifulsoup(url)
    if bs_result["success"] and bs_result.get("content_length", 0) > 1000:
        activity.logger.info(f"✅ BeautifulSoup succeeded for {url}")
        return bs_result
    
    # Step 3: Check if JavaScript is required
    needs_js = any(js_site in domain for js_site in JAVASCRIPT_REQUIRED_SITES)
    
    if needs_js or bs_result.get("content_length", 0) < 1000:
        # Try Crawl4AI for JavaScript rendering
        if config.CRAWL4AI_SERVICE_URL:
            crawl4ai_result = await scrape_with_crawl4ai(url)
            if crawl4ai_result["success"]:
                activity.logger.info(f"✅ Crawl4AI succeeded for {url}")
                return crawl4ai_result
    
    # Step 4: Last resort - Firecrawl (only if we have credits)
    if config.FIRECRAWL_API_KEY:
        # Check if we should use credits
        if should_use_firecrawl_credits():
            firecrawl_result = await scrape_with_firecrawl_minimal(url)
            if firecrawl_result["success"]:
                activity.logger.info(f"✅ Firecrawl succeeded for {url}")
                return firecrawl_result
    
    # Return the best result we got
    return bs_result if bs_result.get("content_length", 0) > 0 else {
        "success": False,
        "error": "All scraping methods failed",
        "method_used": "none",
        "cost": 0.0
    }


async def scrape_embedded_json(url: str, pattern_info: Dict) -> Dict[str, Any]:
    """
    Extract embedded JSON data (e.g., Ashby job boards).
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; QuestBot/1.0)"
            })
            
            if response.status_code == 200:
                html = response.text
                
                # Look for the pattern
                match = re.search(pattern_info["pattern"], html, re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
                    
                    # Extract relevant data
                    content = json.dumps(data.get(pattern_info["key"], data), indent=2)
                    
                    return {
                        "success": True,
                        "content": content,
                        "content_length": len(content),
                        "method_used": "beautifulsoup_json",
                        "cost": 0.0,
                        "data_type": "structured_json"
                    }
    except Exception as e:
        activity.logger.warning(f"Embedded JSON extraction failed: {e}")
    
    return {"success": False, "method_used": "beautifulsoup_json", "cost": 0.0}


async def scrape_with_beautifulsoup(url: str) -> Dict[str, Any]:
    """
    Scrape with BeautifulSoup (free, fast, no JS).
    """
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; QuestBot/1.0)"
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(["script", "style", "nav", "footer", "header"]):
                    element.decompose()
                
                # Get text content
                text = soup.get_text(separator=' ', strip=True)
                
                # Get title
                title = soup.title.string if soup.title else ""
                
                # Get links
                links = []
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    if href.startswith('http'):
                        links.append(href)
                
                return {
                    "success": True,
                    "content": text[:50000],  # Limit to 50k chars
                    "content_length": len(text),
                    "title": title,
                    "links": links[:100],
                    "method_used": "beautifulsoup",
                    "cost": 0.0,
                    "data_type": "html_text"
                }
    
    except Exception as e:
        activity.logger.warning(f"BeautifulSoup failed: {e}")
    
    return {
        "success": False,
        "method_used": "beautifulsoup",
        "cost": 0.0,
        "error": str(e) if 'e' in locals() else "Failed to scrape"
    }


async def scrape_with_crawl4ai(url: str) -> Dict[str, Any]:
    """
    Scrape with Crawl4AI Railway service (free, handles JS).
    """
    if not config.CRAWL4AI_SERVICE_URL:
        return {"success": False, "method_used": "crawl4ai", "cost": 0.0}
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Check domain for specific wait conditions
            domain = urlparse(url).netloc
            
            payload = {
                "url": url,
                "word_count_threshold": 10,
                "remove_overlay_elements": True,
                "process_iframes": True,
                "bypass_cache": True
            }
            
            # Add JS wait conditions for known sites
            if "ashbyhq.com" in domain:
                payload["wait_for"] = "window.__appData"
            elif "greenhouse.io" in domain:
                payload["wait_for"] = ".job-board"
            elif "lever.co" in domain:
                payload["wait_for"] = ".postings-wrapper"
            elif "workday.com" in domain:
                payload["wait_for"] = "[data-automation-id='jobItem']"
                payload["wait_timeout"] = 15000
            
            response = await client.post(
                f"{config.CRAWL4AI_SERVICE_URL}/scrape",
                json=payload,
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") and data.get("markdown"):
                    return {
                        "success": True,
                        "content": data["markdown"],
                        "content_length": data.get("content_length", len(data["markdown"])),
                        "title": data.get("title", ""),
                        "links": data.get("links", []),
                        "method_used": "crawl4ai",
                        "cost": 0.0,
                        "data_type": "markdown"
                    }
    
    except Exception as e:
        activity.logger.warning(f"Crawl4AI failed: {e}")
    
    return {"success": False, "method_used": "crawl4ai", "cost": 0.0}


async def scrape_with_firecrawl_minimal(url: str) -> Dict[str, Any]:
    """
    Minimal Firecrawl usage (only essential pages, markdown only).
    """
    if not config.FIRECRAWL_API_KEY:
        return {"success": False, "method_used": "firecrawl", "cost": 0.0}
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Use scrape endpoint (cheaper than crawl)
            response = await client.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={
                    "Authorization": f"Bearer {config.FIRECRAWL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "url": url,
                    "formats": ["markdown"],  # Only markdown to save credits
                    "onlyMainContent": True,   # Skip navigation, ads, etc.
                    "waitFor": 3000            # Quick wait for JS
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    markdown = data.get("data", {}).get("markdown", "")
                    
                    return {
                        "success": True,
                        "content": markdown,
                        "content_length": len(markdown),
                        "method_used": "firecrawl",
                        "cost": 0.001,  # Approximate cost per scrape
                        "data_type": "markdown"
                    }
            
            elif response.status_code == 402:
                activity.logger.warning("Firecrawl: Out of credits")
                return {
                    "success": False,
                    "method_used": "firecrawl",
                    "cost": 0.0,
                    "error": "Out of credits"
                }
    
    except Exception as e:
        activity.logger.warning(f"Firecrawl failed: {e}")
    
    return {"success": False, "method_used": "firecrawl", "cost": 0.0}


def should_use_firecrawl_credits() -> bool:
    """
    Decide if we should use Firecrawl credits.
    Could check remaining credits, importance of request, etc.
    """
    # For now, only use if other methods failed
    # In production, could check credit balance via API
    return False  # Conservative: don't use credits unless absolutely necessary


@activity.defn
async def smart_crawl_multiple_pages(url: str, max_pages: int = 5) -> Dict[str, Any]:
    """
    Crawl multiple pages intelligently.
    Uses Crawl4AI's /crawl endpoint or falls back to following links with BeautifulSoup.
    """
    pages = []
    visited = set()
    to_visit = [url]
    
    while to_visit and len(pages) < max_pages:
        current_url = to_visit.pop(0)
        
        if current_url in visited:
            continue
        
        visited.add(current_url)
        
        # Scrape current page
        result = await smart_scrape(current_url)
        
        if result["success"]:
            pages.append({
                "url": current_url,
                "content": result.get("content", ""),
                "method": result.get("method_used", "unknown")
            })
            
            # Add new links to visit
            for link in result.get("links", [])[:10]:
                if link not in visited and len(to_visit) < max_pages * 2:
                    # Only follow same-domain links
                    if urlparse(link).netloc == urlparse(url).netloc:
                        to_visit.append(link)
    
    return {
        "success": len(pages) > 0,
        "pages": pages,
        "total_pages": len(pages),
        "total_cost": sum(p.get("cost", 0) for p in pages)
    }


# Export for use in workflows
__all__ = ["smart_scrape", "smart_crawl_multiple_pages"]