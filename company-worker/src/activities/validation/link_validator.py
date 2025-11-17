"""
Link Validation Activities

Validate URLs to prevent 404s and paywalls in generated content.
"""

import asyncio
import aiohttp
from temporalio import activity
from typing import List, Dict, Any
from urllib.parse import urlparse


# Known paywall domains
PAYWALL_DOMAINS = {
    'ft.com',  # Financial Times
    'wsj.com',  # Wall Street Journal
    'bloomberg.com',  # Bloomberg
    'privateequitynews.com',  # Private Equity News
    'economist.com',  # The Economist
    'nytimes.com',  # NY Times
}


@activity.defn
async def playwright_url_cleanse(urls: List[str]) -> Dict[str, Any]:
    """
    Playwright URL Cleanse - Validate URLs before AI generation.

    Filters out:
    - 404s (broken links)
    - 403s (potential paywalls)
    - Timeouts (>3s)
    - Known paywall domains

    Args:
        urls: List of URLs to validate

    Returns:
        Dict with valid_urls, invalid_urls, and stats
    """
    activity.logger.info(f"[Playwright URL Cleanse] Validating {len(urls)} URLs")

    valid_urls = []
    invalid_urls = []
    paywall_urls = []

    async def check_url(url: str) -> tuple[str, bool, str]:
        """Check a single URL with HEAD request"""
        try:
            # Check if known paywall domain
            domain = urlparse(url).netloc.lower()
            for paywall in PAYWALL_DOMAINS:
                if paywall in domain:
                    return (url, False, f"paywall:{paywall}")

            # Make HEAD request with timeout
            timeout = aiohttp.ClientTimeout(total=3)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.head(url, allow_redirects=True) as response:
                    if response.status == 200:
                        return (url, True, "ok")
                    elif response.status == 403:
                        return (url, False, "403:forbidden")
                    elif response.status == 404:
                        return (url, False, "404:not_found")
                    elif response.status >= 500:
                        return (url, False, f"{response.status}:server_error")
                    else:
                        # Other status codes - might be ok
                        return (url, True, f"ok:{response.status}")

        except asyncio.TimeoutError:
            return (url, False, "timeout")
        except Exception as e:
            activity.logger.warning(f"Error checking {url}: {e}")
            return (url, False, f"error:{type(e).__name__}")

    # Validate all URLs in parallel
    results = await asyncio.gather(*[check_url(url) for url in urls])

    # Process results
    for url, is_valid, reason in results:
        if is_valid:
            valid_urls.append(url)
        else:
            invalid_urls.append({"url": url, "reason": reason})
            if "paywall" in reason:
                paywall_urls.append(url)

    activity.logger.info(
        f"Validation complete: {len(valid_urls)} valid, "
        f"{len(invalid_urls)} invalid ({len(paywall_urls)} paywalls)"
    )

    return {
        "valid_urls": valid_urls,
        "invalid_urls": invalid_urls,
        "paywall_count": len(paywall_urls),
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
