"""
Link Validation Activities

Validate URLs using Railway Playwright service to detect:
- 404s and broken pages
- Paywalled content (JS-rendered paywalls, soft paywalls)
- CAPTCHA/anti-bot pages
- Redirects to error pages
- Pages with insufficient content

Uses real browser rendering via remote Playwright service.
"""

import asyncio
import httpx
from temporalio import activity
from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse

from src.utils.config import config


# Known paywall domains - skip these entirely (don't waste browser resources)
PAYWALL_DOMAINS = {
    'ft.com',  # Financial Times
    'wsj.com',  # Wall Street Journal
    'bloomberg.com',  # Bloomberg
    'privateequitynews.com',  # Private Equity News
    'economist.com',  # The Economist
    'nytimes.com',  # NY Times
    'theatlantic.com',  # The Atlantic
    'newyorker.com',  # New Yorker
}

# High authority domains - auto-approve (reliable, won't break)
HIGH_AUTHORITY_DOMAINS = {
    'wikipedia.org',
    'gov.uk', 'gov.us', 'gov.cy', 'europa.eu',
    'bbc.com', 'bbc.co.uk',
    'reuters.com',
    'un.org',
    'who.int',
    'oecd.org',
}

# Paywall indicators - strict ones always trigger (regardless of content)
PAYWALL_INDICATORS_STRICT = [
    'subscribe to read',
    'sign in to continue reading',
    'create an account to continue',
    'start your free trial',
    'unlock this article',
    'you have reached your limit',
    'free articles remaining',
    'register to continue reading',
]
# These only trigger on pages with limited content (< 1000 words)
# Avoids false positives from encyclopedias mentioning "subscription" in citations
PAYWALL_INDICATORS_WITH_CONTEXT = [
    'subscription required',
    'premium content',
    'members only',
    'already a subscriber',
]

# Error page indicators
ERROR_INDICATORS = [
    'page not found',
    '404 error',
    'page doesn\'t exist',
    'page does not exist',
    'no longer available',
    'has been removed',
    'access denied',
    'forbidden',
    'this page isn\'t available',
]

# CAPTCHA/bot indicators - these need context checking
BOT_BLOCK_INDICATORS_STRICT = [
    'verify you are human',
    'are you a robot',
    'ddos protection',
    'please wait while we verify',
    'checking your browser',
    'just a moment while we',
    'captcha-delivery.com',
    'datadome captcha',
    'hcaptcha',
    'recaptcha challenge',
]
# These only count if page has very little content (< 500 words)
BOT_BLOCK_INDICATORS_WITH_CONTEXT = [
    'cloudflare',
    'captcha',
]


async def validate_url_with_playwright_service(
    url: str,
    client: httpx.AsyncClient,
    service_url: str,
    timeout: float = 15.0
) -> Tuple[bool, str, str]:
    """
    Validate a single URL using the Railway Playwright service.

    Args:
        url: URL to validate
        client: httpx async client
        service_url: Base URL of Playwright service
        timeout: Request timeout in seconds

    Returns:
        Tuple of (is_valid, reason, html_snippet)
    """
    try:
        # Call Playwright service /html endpoint
        response = await client.post(
            f"{service_url.rstrip('/')}/html",
            json={
                "url": url,
                "wait_until": "domcontentloaded",  # Faster than networkidle
                "viewport": {"width": 1280, "height": 720}
            },
            timeout=timeout
        )

        if response.status_code == 422:
            # Validation error from service (bad URL format, etc.)
            return False, "invalid_url_format", ""

        if response.status_code >= 500:
            # Service error - treat as unknown (don't invalidate)
            return True, "service_error_passthrough", ""

        if response.status_code != 200:
            return False, f"http_{response.status_code}", ""

        # Parse response - expect HTML content
        try:
            data = response.json()
            html_content = data.get("html", "") if isinstance(data, dict) else str(data)
        except Exception:
            # Response might be raw HTML
            html_content = response.text

        html_lower = html_content.lower()

        # Check content length (very short = likely error page)
        # Count visible text roughly by stripping tags
        import re
        text_only = re.sub(r'<[^>]+>', ' ', html_content)
        word_count = len(text_only.split())

        if word_count < 30:
            return False, f"insufficient_content:{word_count}_words", html_content[:500]

        # Check for 404/error indicators in content
        for indicator in ERROR_INDICATORS:
            if indicator in html_lower:
                # Make sure it's prominent (in title or h1)
                if f'<title' in html_lower and indicator in html_lower[:2000]:
                    return False, f"error_page:{indicator[:20]}", html_content[:500]
                if f'<h1' in html_lower and indicator in html_lower[:3000]:
                    return False, f"error_page:{indicator[:20]}", html_content[:500]

        # Check for paywall indicators - strict ones always fail
        for indicator in PAYWALL_INDICATORS_STRICT:
            if indicator in html_lower:
                return False, f"paywall:{indicator[:20]}", html_content[:500]

        # Context-sensitive paywall indicators - only fail if limited content
        # (avoids false positives from Wikipedia mentioning "subscription required" in citations)
        if word_count < 1000:
            for indicator in PAYWALL_INDICATORS_WITH_CONTEXT:
                if indicator in html_lower:
                    return False, f"paywall:{indicator[:20]}", html_content[:500]

        # Check for bot/CAPTCHA blocks - strict indicators always block
        for indicator in BOT_BLOCK_INDICATORS_STRICT:
            if indicator in html_lower:
                return False, f"bot_block:{indicator[:20]}", html_content[:500]

        # Context-sensitive indicators only block if page has little real content
        # (avoids false positives from articles mentioning "captcha" or "cloudflare")
        if word_count < 500:
            for indicator in BOT_BLOCK_INDICATORS_WITH_CONTEXT:
                if indicator in html_lower:
                    return False, f"bot_block:{indicator[:20]}", html_content[:500]

        return True, "ok", ""

    except httpx.TimeoutException:
        return False, "timeout", ""
    except httpx.ConnectError:
        return False, "connection_error", ""
    except Exception as e:
        return False, f"error:{type(e).__name__}", ""


@activity.defn
async def playwright_pre_cleanse(urls: List[str]) -> Dict[str, Any]:
    """
    PHASE 4b: Score source URLs before article generation via Playwright.

    Returns scored URLs so Sonnet can prioritize reliable sources.
    NON-BLOCKING: If validation fails, returns default scores.

    Scores:
    - 1.0: trusted (high authority domains)
    - 0.9: validated (browser check passed)
    - 0.6: unvalidated (default if check fails)
    - 0.5: uncertain (timeout/error)
    - 0.3: bot_blocked
    - 0.2: paywall
    - 0.1: broken (404/empty)

    Args:
        urls: List of URLs to score

    Returns:
        Dict with scored_urls for Sonnet to prioritize
    """
    activity.logger.info(f"[Playwright Pre-Cleanse] Scoring {len(urls)} URLs for article generation")
    return await _validate_urls_internal(urls, use_browser=True)


@activity.defn
async def playwright_post_cleanse(urls: List[str]) -> Dict[str, Any]:
    """
    PHASE 5b: Validate links in final article via Playwright.

    After article is written, validate cited links and return
    broken ones for Haiku to fix/remove.

    Args:
        urls: List of URLs from article content

    Returns:
        Dict with scored_urls, broken links identified for fixing
    """
    activity.logger.info(f"[Playwright Post-Cleanse] Checking {len(urls)} links in final article")
    return await _validate_urls_internal(urls, use_browser=True)


@activity.defn
async def playwright_url_cleanse(urls: List[str], use_browser: bool = True) -> Dict[str, Any]:
    """
    Generic URL validation using Railway Playwright service.

    DEPRECATED: Use playwright_pre_cleanse (Phase 4b) or playwright_post_cleanse (Phase 5b) instead.

    Args:
        urls: List of URLs to validate
        use_browser: If True, use Playwright service. If False, use quick HEAD requests.

    Returns:
        Dict with valid_urls, invalid_urls, scored_urls, and stats
    """
    return await _validate_urls_internal(urls, use_browser)


async def _validate_urls_internal(urls: List[str], use_browser: bool = True) -> Dict[str, Any]:
    """
    Internal URL validation logic - shared by all validation activities.
    """
    activity.logger.info(f"[Playwright URL Cleanse] Validating {len(urls)} URLs (browser={use_browser})")

    valid_urls = []
    invalid_urls = []
    auto_approved = []
    paywall_blocked = []

    # Pre-filter: known paywalls and high-authority domains
    urls_to_check = []
    for url in urls:
        try:
            domain = urlparse(url).netloc.lower()
        except Exception:
            invalid_urls.append({"url": url, "reason": "invalid_url_format"})
            continue

        # Block known paywalls (don't waste browser resources)
        is_paywall = any(pw in domain for pw in PAYWALL_DOMAINS)
        if is_paywall:
            invalid_urls.append({"url": url, "reason": "known_paywall_domain"})
            paywall_blocked.append(url)
            continue

        # Auto-approve high authority domains
        is_authority = any(auth in domain for auth in HIGH_AUTHORITY_DOMAINS)
        if is_authority:
            valid_urls.append(url)
            auto_approved.append(url)
            continue

        urls_to_check.append(url)

    activity.logger.info(
        f"Pre-filter: {len(auto_approved)} auto-approved, "
        f"{len(paywall_blocked)} paywall domains blocked, "
        f"{len(urls_to_check)} URLs to browser-check"
    )

    if not urls_to_check:
        return {
            "valid_urls": valid_urls,
            "invalid_urls": invalid_urls,
            "auto_approved": len(auto_approved),
            "paywall_blocked": len(paywall_blocked),
            "browser_checked": 0,
            "total_checked": len(urls),
            "validation_rate": len(valid_urls) / len(urls) if urls else 0
        }

    # Use Railway Playwright service for browser-based validation
    service_url = config.PLAYWRIGHT_SERVICE_URL

    if use_browser and service_url:
        activity.logger.info(f"Using Playwright service at {service_url} for {len(urls_to_check)} URLs")

        # Process ALL URLs in parallel (Playwright service handles one at a time, but we can fire many requests)
        # Use semaphore to limit concurrency to avoid overwhelming the service
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests

        async def check_with_semaphore(url: str, client: httpx.AsyncClient) -> Tuple[str, bool, str]:
            async with semaphore:
                is_valid, reason, _ = await validate_url_with_playwright_service(
                    url, client, service_url, timeout=12.0
                )
                return url, is_valid, reason

        try:
            async with httpx.AsyncClient() as client:
                # Fire all requests in parallel
                tasks = [check_with_semaphore(url, client) for url in urls_to_check]

                # Heartbeat while waiting
                activity.heartbeat(f"Validating {len(urls_to_check)} URLs in parallel")

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        activity.logger.warning(f"Validation error: {result}")
                        continue

                    url, is_valid, reason = result
                    if is_valid:
                        valid_urls.append(url)
                    else:
                        invalid_urls.append({"url": url, "reason": reason})

            activity.logger.info(
                f"Playwright service validation complete: {len(valid_urls)} valid, {len(invalid_urls)} invalid"
            )

        except Exception as e:
            activity.logger.error(f"Playwright service error: {e}")
            # Fall back to HEAD requests
            use_browser = False

    # Fallback: HEAD requests (fast but less thorough)
    if not use_browser or not service_url:
        import aiohttp

        unchecked = [u for u in urls_to_check if u not in valid_urls and u not in [x['url'] for x in invalid_urls]]

        if unchecked:
            activity.logger.info(f"HEAD request fallback for {len(unchecked)} URLs")

            async def check_url_head(url: str) -> Tuple[str, bool, str]:
                try:
                    timeout = aiohttp.ClientTimeout(total=5)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.head(url, allow_redirects=True) as response:
                            if response.status == 200:
                                return (url, True, "ok_head")
                            elif response.status in [403, 401]:
                                return (url, False, f"{response.status}_forbidden")
                            elif response.status == 404:
                                return (url, False, "404_not_found")
                            elif response.status >= 400:
                                return (url, False, f"{response.status}_error")
                            else:
                                return (url, True, f"ok_{response.status}")
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

    browser_checked = len([x for x in invalid_urls if x.get("reason", "").startswith(("paywall:", "error_page:", "bot_block:", "ok"))]) + \
                      len([u for u in valid_urls if u not in auto_approved])

    activity.logger.info(
        f"Validation complete: {len(valid_urls)} valid, {len(invalid_urls)} invalid "
        f"({len(auto_approved)} auto-approved, {browser_checked} browser-checked)"
    )

    # Build scored results for Sonnet/Gemini
    # High confidence = definitely use, Low confidence = use with caution
    scored_urls = []

    # Auto-approved (high authority) = highest confidence
    for url in auto_approved:
        scored_urls.append({"url": url, "score": 1.0, "status": "trusted", "reason": "high_authority_domain"})

    # Browser-validated OK = high confidence
    for url in valid_urls:
        if url not in auto_approved:
            scored_urls.append({"url": url, "score": 0.9, "status": "validated", "reason": "browser_check_passed"})

    # Failed validation = low confidence (but still usable with caution)
    for item in invalid_urls:
        url = item["url"]
        reason = item.get("reason", "unknown")

        # Known paywalls = very low but not zero (might have free preview)
        if "paywall" in reason:
            scored_urls.append({"url": url, "score": 0.2, "status": "paywall", "reason": reason})
        # Bot blocks = medium-low (might work for users)
        elif "bot_block" in reason:
            scored_urls.append({"url": url, "score": 0.3, "status": "bot_blocked", "reason": reason})
        # Timeouts/errors = medium (might be temporary)
        elif "timeout" in reason or "error" in reason:
            scored_urls.append({"url": url, "score": 0.5, "status": "uncertain", "reason": reason})
        # 404/broken = very low
        elif "404" in reason or "insufficient" in reason:
            scored_urls.append({"url": url, "score": 0.1, "status": "broken", "reason": reason})
        else:
            scored_urls.append({"url": url, "score": 0.4, "status": "flagged", "reason": reason})

    activity.logger.info(
        f"Validation complete: {len(valid_urls)} valid, {len(invalid_urls)} flagged "
        f"({len(auto_approved)} trusted, {browser_checked} browser-checked)"
    )

    return {
        "valid_urls": valid_urls,
        "invalid_urls": invalid_urls,
        "scored_urls": scored_urls,  # For Sonnet/Gemini to prioritize
        "auto_approved": len(auto_approved),
        "paywall_blocked": len(paywall_blocked),
        "browser_checked": browser_checked,
        "total_checked": len(urls),
        "validation_rate": len(valid_urls) / len(urls) if urls else 0
    }


@activity.defn
async def playwright_clean_links(profile_sections: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Clean broken links from generated content using Playwright validation.

    Extracts all markdown links [text](url) from content,
    validates them with browser automation, and removes broken ones.

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
            if url.startswith('http'):
                all_urls.add(url)

    activity.logger.info(f"Found {len(all_urls)} unique external links to validate")

    if not all_urls:
        return profile_sections

    # Validate URLs with Playwright service
    validation_result = await playwright_url_cleanse(list(all_urls), use_browser=True)
    invalid_urls = set(item['url'] for item in validation_result['invalid_urls'])

    activity.logger.info(f"Removing {len(invalid_urls)} broken/paywalled links from content")

    # Remove broken links from content
    cleaned_sections = {}
    removed_count = 0

    for key, section in profile_sections.items():
        content = section.get('content', '')

        def replace_link(match):
            nonlocal removed_count
            text, url = match.groups()
            if url in invalid_urls:
                removed_count += 1
                return text  # Just return the text without the link
            return match.group(0)

        cleaned_content = re.sub(markdown_link_pattern, replace_link, content)

        cleaned_sections[key] = {
            **section,
            'content': cleaned_content
        }

    activity.logger.info(f"Removed {removed_count} broken links from content")

    return cleaned_sections


@activity.defn
async def finesse_internal_links(
    cluster_articles: List[Dict[str, Any]],
    primary_article_id: int
) -> List[Dict[str, Any]]:
    """
    Post-generation phase to optimize internal links between cluster articles.

    After all cluster articles are created, this activity:
    1. Analyzes each article's target keywords
    2. Finds opportunities to link using those keywords as anchor text
    3. Prioritizes links to the primary article (highest value)
    4. Ensures no article links to itself
    5. Uses short anchor text (2-4 words)

    Args:
        cluster_articles: List of article dicts with {id, slug, content, target_keyword, article_mode}
        primary_article_id: ID of the primary (story) article to prioritize

    Returns:
        Updated cluster_articles with improved internal linking
    """
    import re

    activity.logger.info(f"[Finesse Internal Links] Processing {len(cluster_articles)} cluster articles")

    # Build lookup of slugs and keywords
    article_lookup = {}
    for article in cluster_articles:
        article_lookup[article['id']] = {
            'slug': article.get('slug', ''),
            'target_keyword': article.get('target_keyword', ''),
            'article_mode': article.get('article_mode', ''),
            'title': article.get('title', '')
        }

    # Short anchor text options for each mode
    mode_anchors = {
        'story': ['relocation guide', 'complete guide', 'full guide'],
        'guide': ['practical guide', 'step-by-step', 'how-to guide'],
        'yolo': ['adventure guide', 'YOLO guide', 'bold approach'],
        'voices': ['expat stories', 'real experiences', 'expat voices']
    }

    updated_articles = []

    for article in cluster_articles:
        article_id = article['id']
        content = article.get('content', '')
        current_slug = article.get('slug', '')

        # Get sibling articles (not self)
        siblings = [(aid, info) for aid, info in article_lookup.items() if aid != article_id]

        # Sort siblings: primary first, then by mode importance
        mode_priority = {'story': 0, 'guide': 1, 'yolo': 2, 'voices': 3}
        siblings.sort(key=lambda x: (
            0 if x[0] == primary_article_id else 1,
            mode_priority.get(x[1]['article_mode'], 99)
        ))

        # Check existing internal links
        existing_links = set(re.findall(r'\]\(/([^)]+)\)', content))

        links_added = 0
        max_links_to_add = 3  # Don't over-link

        for sibling_id, sibling_info in siblings:
            if links_added >= max_links_to_add:
                break

            sibling_slug = sibling_info['slug']

            # Skip if already linked
            if sibling_slug in existing_links:
                continue

            sibling_mode = sibling_info['article_mode']
            sibling_keyword = sibling_info.get('target_keyword', '')

            # Try to find natural insertion points
            # Look for mentions of related terms that could become links
            anchor_options = mode_anchors.get(sibling_mode, ['guide'])

            for anchor in anchor_options:
                # Find the anchor text in content (case insensitive)
                pattern = rf'\b({re.escape(anchor)})\b'
                match = re.search(pattern, content, re.IGNORECASE)

                if match and f'](/' not in content[max(0, match.start()-5):match.end()+5]:
                    # Found unlinked text - make it a link
                    original_text = match.group(1)
                    replacement = f'[{original_text}](/{sibling_slug})'
                    content = content[:match.start()] + replacement + content[match.end():]
                    links_added += 1
                    activity.logger.info(f"  Added link: '{original_text}' -> /{sibling_slug}")
                    break

        # Update article with new content
        updated_article = {**article, 'content': content}
        updated_articles.append(updated_article)

        activity.logger.info(f"Article {article_id}: Added {links_added} internal links")

    return updated_articles


@activity.defn
async def verify_external_links(
    content: str,
    min_links: int = 10
) -> Dict[str, Any]:
    """
    Verify that content has sufficient external links backing up claims.

    Checks:
    1. Count of external links
    2. Link quality (domains)
    3. Identifies claims without sources

    Args:
        content: Article content (HTML or markdown)
        min_links: Minimum required external links

    Returns:
        Dict with link_count, quality_score, suggestions
    """
    import re

    activity.logger.info("[Verify External Links] Checking content for source links")

    # Find all external links
    markdown_links = re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', content)
    html_links = re.findall(r'<a[^>]+href=["\']?(https?://[^"\'>\s]+)["\']?[^>]*>([^<]+)</a>', content)

    all_links = markdown_links + [(text, url) for url, text in html_links]

    # Categorize by domain authority
    high_authority = []
    medium_authority = []
    low_authority = []

    authority_domains = {
        'high': ['gov', 'europa.eu', 'un.org', 'who.int', 'oecd.org', 'worldbank.org', 'imf.org'],
        'medium': ['wikipedia.org', 'bbc.com', 'reuters.com', 'numbeo.com', 'expatistan.com', 'taxfoundation.org']
    }

    for text, url in all_links:
        domain = urlparse(url).netloc.lower()

        if any(auth in domain for auth in authority_domains['high']):
            high_authority.append({'text': text, 'url': url, 'domain': domain})
        elif any(auth in domain for auth in authority_domains['medium']):
            medium_authority.append({'text': text, 'url': url, 'domain': domain})
        else:
            low_authority.append({'text': text, 'url': url, 'domain': domain})

    total_links = len(all_links)
    quality_score = (len(high_authority) * 1.0 + len(medium_authority) * 0.7 + len(low_authority) * 0.4) / max(total_links, 1)

    # Check for unsourced claims (numbers without nearby links)
    # Look for percentages, currency amounts, years without links nearby
    claim_pattern = r'(\d+(?:\.\d+)?%|\€\d+|\$\d+|\d{4})'
    claims = re.findall(claim_pattern, content)

    result = {
        'total_links': total_links,
        'high_authority': len(high_authority),
        'medium_authority': len(medium_authority),
        'low_authority': len(low_authority),
        'quality_score': round(quality_score, 2),
        'meets_minimum': total_links >= min_links,
        'potential_claims': len(claims),
        'suggestions': []
    }

    if total_links < min_links:
        result['suggestions'].append(f"Add {min_links - total_links} more external source links")

    if len(high_authority) < 3:
        result['suggestions'].append("Add more links to government/official sources")

    activity.logger.info(
        f"External links: {total_links} total ({len(high_authority)} high authority), "
        f"quality score: {quality_score:.2f}, meets minimum: {result['meets_minimum']}"
    )

    return result
