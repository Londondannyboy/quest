"""
Reddit Research Activity

Uses Reddit's public JSON API for searching expat/relocation experiences.
No OAuth required - just append .json to any Reddit URL.

Rate limited: ~60 requests/minute without auth.
"""

import httpx
from temporalio import activity
from typing import Dict, Any, List
import asyncio


# Subreddits relevant for relocation/expat content
EXPAT_SUBREDDITS = [
    "expats",
    "digitalnomad",
    "IWantOut",
    "ExpatFIRE",
    "expatriates",
    "AmerExit",
    "euexpats",
]

# Country-specific subreddits (will be searched if country matches)
COUNTRY_SUBREDDITS = {
    "portugal": ["portugal", "PortugalExpats", "Lisboa", "Porto"],
    "spain": ["spain", "SpainExpats", "Madrid", "Barcelona"],
    "cyprus": ["cyprus"],
    "greece": ["greece", "Athens"],
    "italy": ["italy", "ItalyExpats", "rome", "Milan"],
    "france": ["france", "Paris", "expat_france"],
    "germany": ["germany", "Berlin", "Munich"],
    "netherlands": ["Netherlands", "Amsterdam"],
    "thailand": ["Thailand", "Bangkok"],
    "mexico": ["mexico", "MexicoCity", "expatsmexico"],
    "costa rica": ["costarica"],
    "panama": ["Panama"],
    "colombia": ["Colombia", "Medellin"],
    "uk": ["unitedkingdom", "AskUK", "London"],
    "ireland": ["ireland", "Dublin"],
    "canada": ["canada", "ImmigrationCanada"],
    "australia": ["australia", "AusFinance"],
    "new zealand": ["newzealand"],
    "japan": ["japan", "JapanFinance", "movingtojapan"],
    "singapore": ["singapore"],
    "uae": ["dubai", "UAE"],
}


async def fetch_reddit_json(url: str, timeout: int = 15) -> Dict[str, Any]:
    """
    Fetch JSON from Reddit URL.

    Args:
        url: Reddit URL (will append .json if needed)
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON response
    """
    # Ensure .json suffix
    if not url.endswith('.json'):
        url = url.rstrip('/') + '.json'

    headers = {
        "User-Agent": "RelocationQuest/1.0 (research bot for expat content)"
    }

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


def extract_posts_from_listing(data: Dict) -> List[Dict[str, Any]]:
    """Extract post data from Reddit listing response."""
    posts = []

    children = data.get("data", {}).get("children", [])
    for child in children:
        post_data = child.get("data", {})
        if not post_data:
            continue

        # Skip removed/deleted posts
        if post_data.get("removed_by_category") or post_data.get("selftext") == "[removed]":
            continue

        posts.append({
            "title": post_data.get("title", ""),
            "selftext": post_data.get("selftext", "")[:2000],  # Cap text length
            "subreddit": post_data.get("subreddit", ""),
            "author": post_data.get("author", ""),
            "score": post_data.get("score", 0),
            "num_comments": post_data.get("num_comments", 0),
            "url": f"https://reddit.com{post_data.get('permalink', '')}",
            "created_utc": post_data.get("created_utc", 0),
            "upvote_ratio": post_data.get("upvote_ratio", 0),
        })

    return posts


@activity.defn
async def reddit_search_expat_content(
    country_name: str,
    search_terms: List[str] = None,
    max_posts: int = 30,
    sort: str = "relevance",  # relevance, hot, top, new
    time_filter: str = "year"  # hour, day, week, month, year, all
) -> Dict[str, Any]:
    """
    Search Reddit for expat/relocation content about a country.

    Uses Reddit's public JSON API (no auth required).

    Args:
        country_name: Country to search for (e.g., "Portugal")
        search_terms: Additional search terms (default: relocation-related)
        max_posts: Maximum posts to return
        sort: Sort order (relevance, hot, top, new)
        time_filter: Time range (hour, day, week, month, year, all)

    Returns:
        Dict with posts, subreddits_searched, stats
    """
    activity.logger.info(f"Searching Reddit for {country_name} expat content")

    country_lower = country_name.lower()

    # Build search terms
    if not search_terms:
        search_terms = [
            f"{country_name} expat",
            f"{country_name} relocation",
            f"{country_name} moving",
            f"{country_name} visa",
            f"{country_name} cost of living",
            f"moved to {country_name}",
            f"living in {country_name}",
        ]

    all_posts = []
    subreddits_searched = []
    errors = []

    # 1. Search general expat subreddits
    for subreddit in EXPAT_SUBREDDITS[:5]:  # Limit to avoid rate limits
        try:
            # Search within subreddit for country
            search_url = f"https://www.reddit.com/r/{subreddit}/search.json"
            search_url += f"?q={country_name}&restrict_sr=1&sort={sort}&t={time_filter}&limit=10"

            data = await fetch_reddit_json(search_url)
            posts = extract_posts_from_listing(data)

            all_posts.extend(posts)
            subreddits_searched.append(subreddit)

            activity.logger.info(f"  r/{subreddit}: {len(posts)} posts")

            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)

        except Exception as e:
            errors.append(f"r/{subreddit}: {str(e)}")
            activity.logger.warning(f"Failed to search r/{subreddit}: {e}")

    # 2. Search country-specific subreddits
    country_subs = COUNTRY_SUBREDDITS.get(country_lower, [])
    for subreddit in country_subs[:3]:  # Limit
        try:
            # Get hot posts from country subreddit with expat-related search
            search_url = f"https://www.reddit.com/r/{subreddit}/search.json"
            search_url += f"?q=expat OR moving OR relocate OR visa OR cost&restrict_sr=1&sort={sort}&t={time_filter}&limit=10"

            data = await fetch_reddit_json(search_url)
            posts = extract_posts_from_listing(data)

            all_posts.extend(posts)
            subreddits_searched.append(subreddit)

            activity.logger.info(f"  r/{subreddit}: {len(posts)} posts")

            await asyncio.sleep(0.5)

        except Exception as e:
            errors.append(f"r/{subreddit}: {str(e)}")

    # 3. Global Reddit search for country + expat terms
    try:
        search_url = f"https://www.reddit.com/search.json"
        search_url += f"?q={country_name}+expat+OR+relocation+OR+visa&sort={sort}&t={time_filter}&limit=15"

        data = await fetch_reddit_json(search_url)
        posts = extract_posts_from_listing(data)

        all_posts.extend(posts)
        subreddits_searched.append("(global search)")

        activity.logger.info(f"  Global search: {len(posts)} posts")

    except Exception as e:
        errors.append(f"global search: {str(e)}")

    # Deduplicate by URL
    seen_urls = set()
    unique_posts = []
    for post in all_posts:
        if post["url"] not in seen_urls:
            seen_urls.add(post["url"])
            unique_posts.append(post)

    # Sort by score and limit
    unique_posts.sort(key=lambda x: x.get("score", 0), reverse=True)
    final_posts = unique_posts[:max_posts]

    # Format for voices extraction
    voices = []
    for post in final_posts:
        if post.get("selftext") and len(post["selftext"]) > 50:
            # Increase from 500 to 2000 chars for richer context and transformation stories
            full_text = post["selftext"][:2000]
            voices.append({
                "type": "reddit",
                "source": f"u/{post['author']} on r/{post['subreddit']}",
                "author": f"Reddit user ({post.get('subreddit', 'expat community')})",
                "credibility": f"Score: {post['score']}, {post['num_comments']} comments",
                "stance": "mixed",  # Will be analyzed during curation
                "quote": full_text,
                "text": full_text,  # Duplicate for compatibility
                "title": post["title"],  # Include post title for context
                "context": post["title"],
                "key_insight": "",  # To be extracted during curation
                "url": post["url"],
                "upvotes": post["score"],  # Social proof
                "score": post["score"],
                "date": post.get("created_utc", ""),
            })

    activity.logger.info(
        f"✅ Reddit search complete: {len(final_posts)} posts, {len(voices)} with content, "
        f"{len(subreddits_searched)} subreddits searched"
    )

    return {
        "posts": final_posts,
        "voices": voices,
        "subreddits_searched": subreddits_searched,
        "total_found": len(all_posts),
        "unique_posts": len(unique_posts),
        "errors": errors if errors else None,
        "country": country_name,
    }
