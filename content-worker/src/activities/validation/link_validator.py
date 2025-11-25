"""
Link Validation Activities

Validate URLs to prevent 404s and paywalls in generated content.
Uses Crawl4AI browser automation for thorough validation.
"""

import asyncio
import aiohttp
import httpx
from temporalio import activity
from typing import List, Dict, Any
from urllib.parse import urlparse

from src.utils.config import config


# Known paywall domains - skip these entirely
PAYWALL_DOMAINS = {
    'ft.com',  # Financial Times
    'wsj.com',  # Wall Street Journal
    'bloomberg.com',  # Bloomberg
    'privateequitynews.com',  # Private Equity News
    'economist.com',  # The Economist
    'nytimes.com',  # NY Times
}

# High authority domains - always trust these
HIGH_AUTHORITY_DOMAINS = {
    'wikipedia.org',
    'gov.uk', 'gov.us', 'europa.eu',
    'bbc.com', 'bbc.co.uk',
    'reuters.com',
    'un.org',
    'who.int',
}


@activity.defn
async def playwright_url_cleanse(urls: List[str], use_browser: bool = True) -> Dict[str, Any]:
    """
    URL Validation using Crawl4AI browser automation.

    Filters out:
    - 404s (broken links)
    - Paywalled content (JS-rendered paywalls, soft paywalls)
    - CAPTCHA/anti-bot pages
    - Pages with insufficient content (<100 words)
    - Known paywall domains

    Auto-approves:
    - High authority domains (Wikipedia, .gov, BBC, Reuters)

    Args:
        urls: List of URLs to validate
        use_browser: If True, use Crawl4AI for thorough check. If False, use HEAD requests only.

    Returns:
        Dict with valid_urls, invalid_urls, and stats
    """
    activity.logger.info(f"[URL Validation] Checking {len(urls)} URLs (browser={use_browser})")

    valid_urls = []
    invalid_urls = []
    auto_approved = []

    # Pre-filter: known paywalls and high-authority domains
    urls_to_check = []
    for url in urls:
        domain = urlparse(url).netloc.lower()

        # Block known paywalls
        is_paywall = any(pw in domain for pw in PAYWALL_DOMAINS)
        if is_paywall:
            invalid_urls.append({"url": url, "reason": "known_paywall"})
            continue

        # Auto-approve high authority
        is_authority = any(auth in domain for auth in HIGH_AUTHORITY_DOMAINS)
        if is_authority:
            valid_urls.append(url)
            auto_approved.append(url)
            continue

        urls_to_check.append(url)

    activity.logger.info(
        f"Pre-filter: {len(auto_approved)} auto-approved, "
        f"{len(invalid_urls)} paywalls blocked, "
        f"{len(urls_to_check)} to check"
    )

    if not urls_to_check:
        return {
            "valid_urls": valid_urls,
            "invalid_urls": invalid_urls,
            "auto_approved": len(auto_approved),
            "total_checked": len(urls),
            "validation_rate": len(valid_urls) / len(urls) if urls else 0
        }

    # Use Crawl4AI for browser-based validation
    if use_browser and config.CRAWL4AI_SERVICE_URL:
        activity.logger.info(f"Using Crawl4AI browser validation for {len(urls_to_check)} URLs")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Call batch validation endpoint
                response = await client.post(
                    f"{config.CRAWL4AI_SERVICE_URL.rstrip('/')}/crawl-many",
                    json={"urls": urls_to_check},
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    data = response.json()
                    pages = data.get("pages", [])

                    # Build result map
                    result_map = {p.get("url"): p for p in pages}

                    for url in urls_to_check:
                        page = result_map.get(url, {})
                        content = page.get("content", "")
                        word_count = len(content.split()) if content else 0

                        # Check for paywall indicators
                        content_lower = content.lower()
                        has_paywall_text = any(x in content_lower for x in [
                            "subscribe to read", "subscription required",
                            "sign in to continue", "create an account",
                            "premium content", "members only"
                        ])

                        if word_count >= 100 and not has_paywall_text:
                            valid_urls.append(url)
                        else:
                            reason = "paywall_detected" if has_paywall_text else f"low_content:{word_count}_words"
                            invalid_urls.append({"url": url, "reason": reason})
                else:
                    activity.logger.warning(f"Crawl4AI returned {response.status_code}, falling back to HEAD")
                    # Fall through to HEAD request fallback
                    use_browser = False

        except Exception as e:
            activity.logger.warning(f"Crawl4AI error: {e}, falling back to HEAD")
            use_browser = False

    # Fallback: HEAD requests for remaining unchecked URLs
    if not use_browser or not config.CRAWL4AI_SERVICE_URL:
        unchecked = [u for u in urls_to_check if u not in valid_urls and u not in [x['url'] for x in invalid_urls]]

        if unchecked:
            activity.logger.info(f"HEAD request fallback for {len(unchecked)} URLs")

            async def check_url_head(url: str) -> tuple[str, bool, str]:
                try:
                    timeout = aiohttp.ClientTimeout(total=5)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.head(url, allow_redirects=True) as response:
                            if response.status == 200:
                                return (url, True, "ok")
                            elif response.status in [403, 401]:
                                return (url, False, f"{response.status}:forbidden")
                            elif response.status == 404:
                                return (url, False, "404:not_found")
                            else:
                                return (url, True, f"ok:{response.status}")
                except asyncio.TimeoutError:
                    return (url, False, "timeout")
                except Exception as e:
                    return (url, False, f"error:{type(e).__name__}")

            results = await asyncio.gather(*[check_url_head(u) for u in unchecked])

            for url, is_valid, reason in results:
                if is_valid:
                    valid_urls.append(url)
                else:
                    invalid_urls.append({"url": url, "reason": reason})

    activity.logger.info(
        f"Validation complete: {len(valid_urls)} valid, {len(invalid_urls)} invalid"
    )

    return {
        "valid_urls": valid_urls,
        "invalid_urls": invalid_urls,
        "auto_approved": len(auto_approved),
        "total_checked": len(urls),
        "validation_rate": len(valid_urls) / len(urls) if urls else 0
    }


@activity.defn
async def playwright_clean_links(profile_sections: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Playwright Clean Links - Remove broken links from generated content.

    Extracts all markdown links [text](url) from content,
    validates them, and removes broken ones.

    Args:
        profile_sections: Dict of profile sections with content

    Returns:
        Cleaned profile_sections dict
    """
    activity.logger.info(f"[Playwright Clean Links] Cleaning links from {len(profile_sections)} sections")

    import re

    # Extract all URLs from all sections
    all_urls = set()
    markdown_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'

    for section in profile_sections.values():
        content = section.get('content', '')
        matches = re.findall(markdown_link_pattern, content)
        for text, url in matches:
            # Skip internal links (start with /)
            if not url.startswith('/'):
                all_urls.add(url)

    activity.logger.info(f"Found {len(all_urls)} unique external links")

    # Validate URLs
    validation_result = await playwright_url_cleanse(list(all_urls))
    invalid_urls = set(item['url'] for item in validation_result['invalid_urls'])

    activity.logger.info(f"Removing {len(invalid_urls)} broken/paywalled links")

    # Remove broken links from content
    cleaned_sections = {}
    removed_count = 0

    for key, section in profile_sections.items():
        content = section.get('content', '')
        original_content = content

        # Find and remove broken links
        def replace_link(match):
            nonlocal removed_count
            text, url = match.groups()
            if url in invalid_urls:
                removed_count += 1
                # Just return the text without the link
                return text
            return match.group(0)

        cleaned_content = re.sub(markdown_link_pattern, replace_link, content)

        cleaned_sections[key] = {
            **section,
            'content': cleaned_content
        }

    activity.logger.info(f"Removed {removed_count} broken links from content")

    return cleaned_sections
