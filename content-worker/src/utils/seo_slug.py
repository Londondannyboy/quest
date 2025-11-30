"""
SEO Slug Generation for Country Hub Pages.

Generates keyword-rich slugs from DataForSEO research data.

Algorithm:
1. Extract top keywords by volume from seo_keywords
2. Select diverse keywords across categories (visa, cost, tax, lifestyle)
3. Generate slug: {action}-{location}-{diverse-keywords}
4. Validate length (max 10 words) and format

Example output:
- "relocating-to-cyprus-visa-cost-of-living-golden-visa-guide"
- "moving-to-portugal-digital-nomad-visa-tax-benefits-guide"
"""

import re
from typing import Dict, Any, List, Optional, Tuple


# Slug format patterns (location comes first for better SEO)
# Format: {location}-relocation-{keywords}-guide
SLUG_FORMAT = "location-first"  # "cyprus-relocation-visa-..." vs "relocating-to-cyprus-..."

# Keyword categories for diversity selection
KEYWORD_CATEGORIES = {
    "visa": ["visa", "permit", "residency", "immigration", "golden visa", "digital nomad"],
    "cost": ["cost of living", "expenses", "budget", "affordable", "cheap", "prices"],
    "tax": ["tax", "taxes", "taxation", "income tax", "corporate tax", "vat"],
    "lifestyle": ["lifestyle", "quality of life", "culture", "weather", "beaches", "expat"],
    "work": ["remote work", "jobs", "employment", "business", "freelance", "startup"],
    "property": ["property", "real estate", "housing", "rent", "buy", "apartment"],
    "healthcare": ["healthcare", "health", "medical", "hospital", "insurance"],
    "family": ["family", "children", "schools", "education", "retirement"],
}


def categorize_keyword(keyword: str) -> str:
    """Categorize a keyword into one of the main SEO categories."""
    kw_lower = keyword.lower()
    for category, terms in KEYWORD_CATEGORIES.items():
        if any(term in kw_lower for term in terms):
            return category
    return "general"


def select_diverse_keywords(
    keywords: List[Dict[str, Any]],
    max_keywords: int = 5,
    min_volume: int = 10
) -> List[Dict[str, Any]]:
    """
    Select keywords ensuring category diversity.

    Picks top keywords by volume but ensures coverage across
    visa, cost, tax, lifestyle categories.

    Args:
        keywords: List of keyword dicts with 'keyword' and 'volume'
        max_keywords: Maximum keywords to select
        min_volume: Minimum volume threshold

    Returns:
        List of diverse keywords sorted by volume
    """
    # Filter by minimum volume
    filtered = [kw for kw in keywords if kw.get("volume", 0) >= min_volume]

    if not filtered:
        return keywords[:max_keywords]

    # Group by category
    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for kw in filtered:
        cat = categorize_keyword(kw.get("keyword", ""))
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(kw)

    # Sort each category by volume
    for cat in by_category:
        by_category[cat].sort(key=lambda x: x.get("volume", 0), reverse=True)

    # Round-robin selection ensuring diversity
    selected = []
    priority_cats = ["visa", "cost", "tax", "lifestyle", "work", "property", "general"]

    round_num = 0
    while len(selected) < max_keywords:
        added_this_round = False
        for cat in priority_cats:
            if cat in by_category and len(by_category[cat]) > round_num:
                kw = by_category[cat][round_num]
                if kw not in selected:
                    selected.append(kw)
                    added_this_round = True
                    if len(selected) >= max_keywords:
                        break
        round_num += 1
        if not added_this_round:
            break

    # If we didn't fill up, add remaining high-volume keywords
    remaining = sorted(filtered, key=lambda x: x.get("volume", 0), reverse=True)
    for kw in remaining:
        if kw not in selected and len(selected) < max_keywords:
            selected.append(kw)

    return selected[:max_keywords]


def extract_keyword_terms(keyword: str, location_name: str) -> List[str]:
    """
    Extract meaningful terms from a keyword, removing location name.

    Args:
        keyword: Full keyword phrase
        location_name: Country/city name to remove

    Returns:
        List of meaningful terms
    """
    # Remove location name (case-insensitive)
    kw_clean = re.sub(
        rf"\b{re.escape(location_name)}\b",
        "",
        keyword,
        flags=re.IGNORECASE
    )

    # Remove common filler words
    filler_words = {"in", "to", "for", "the", "a", "an", "of", "and", "from", "with"}

    terms = []
    for word in kw_clean.split():
        word_clean = re.sub(r"[^\w-]", "", word.lower())
        if word_clean and word_clean not in filler_words and len(word_clean) > 1:
            terms.append(word_clean)

    return terms


def generate_seo_slug(
    location_name: str,
    seo_keywords: Dict[str, Any],
    max_words: int = 12,
    location_type: str = "country"
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate an SEO-optimized slug from DataForSEO keywords.

    Args:
        location_name: Country or city name (e.g., "Cyprus", "Lisbon")
        seo_keywords: DataForSEO research results
        max_words: Maximum words in slug (default 10)
        location_type: "country" or "city"

    Returns:
        Tuple of (slug, seo_metadata)

    Example:
        "relocating-to-cyprus-visa-cost-of-living-golden-visa-guide"
    """
    location_slug = location_name.lower().replace(" ", "-")

    # Extract keywords from seo_keywords structure
    all_keywords = []

    # Primary keywords (highest volume)
    primary = seo_keywords.get("primary_keywords", [])
    for pk in primary:
        if isinstance(pk, dict):
            all_keywords.append(pk)
        elif isinstance(pk, str):
            all_keywords.append({"keyword": pk, "volume": 100})

    # Long-tail keywords
    long_tail = seo_keywords.get("long_tail", [])
    for lt in long_tail:
        if isinstance(lt, dict):
            all_keywords.append(lt)
        elif isinstance(lt, str):
            all_keywords.append({"keyword": lt, "volume": 50})

    # Select diverse keywords
    diverse_keywords = select_diverse_keywords(all_keywords, max_keywords=5, min_volume=10)

    # Extract unique terms from diverse keywords
    used_terms = set()
    keyword_terms = []

    for kw_dict in diverse_keywords:
        keyword = kw_dict.get("keyword", "")
        terms = extract_keyword_terms(keyword, location_name)
        for term in terms:
            if term not in used_terms and term != location_slug:
                used_terms.add(term)
                keyword_terms.append(term)

    # Build slug: {location}-relocation-{keywords}-guide
    # Example: "cyprus-relocation-visa-cost-of-living-golden-visa-guide"
    suffix = "guide"

    # Calculate available words for keywords
    # Format: {location}-relocation-{keywords}-guide
    location_words = len(location_slug.split("-"))  # usually 1
    relocation_word = 1  # "relocation"
    suffix_words = 1  # "guide"
    available_words = max_words - location_words - relocation_word - suffix_words

    # Take top terms up to available words
    selected_terms = keyword_terms[:available_words]

    # Build the slug: location-relocation-keywords-guide
    slug_parts = [location_slug, "relocation"] + selected_terms + [suffix]
    slug = "-".join(slug_parts)

    # Clean up double dashes
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")

    # Build SEO metadata for storage
    seo_metadata = {
        "selected_keywords": [kw.get("keyword") for kw in diverse_keywords],
        "keyword_volumes": {kw.get("keyword"): kw.get("volume", 0) for kw in diverse_keywords},
        "total_volume": sum(kw.get("volume", 0) for kw in diverse_keywords),
        "primary_keyword": diverse_keywords[0].get("keyword") if diverse_keywords else None,
        "categories_covered": list(set(categorize_keyword(kw.get("keyword", "")) for kw in diverse_keywords)),
    }

    return slug, seo_metadata


def validate_seo_slug(
    slug: str,
    max_words: int = 12,
    min_words: int = 4
) -> Tuple[bool, str, int]:
    """
    Validate an SEO slug and return score.

    Args:
        slug: The slug to validate
        max_words: Maximum allowed words
        min_words: Minimum required words

    Returns:
        Tuple of (is_valid, message, score 0-100)
    """
    words = slug.split("-")
    word_count = len(words)

    issues = []
    score = 100

    # Check length
    if word_count > max_words:
        issues.append(f"Too long: {word_count} words (max {max_words})")
        score -= 30
    elif word_count < min_words:
        issues.append(f"Too short: {word_count} words (min {min_words})")
        score -= 20

    # Check for invalid characters
    if not re.match(r"^[a-z0-9-]+$", slug):
        issues.append("Contains invalid characters (only lowercase, numbers, hyphens allowed)")
        score -= 40

    # Check for double hyphens
    if "--" in slug:
        issues.append("Contains double hyphens")
        score -= 10

    # Check for starting/ending hyphen
    if slug.startswith("-") or slug.endswith("-"):
        issues.append("Starts or ends with hyphen")
        score -= 10

    # Bonus for good patterns
    if "guide" in slug:
        score += 5
    if "relocation" in slug:
        score += 5

    is_valid = len(issues) == 0
    message = "Valid" if is_valid else "; ".join(issues)

    return is_valid, message, min(100, max(0, score))


def generate_hub_title(
    location_name: str,
    primary_keyword: Optional[str] = None,
    keyword_terms: Optional[List[str]] = None
) -> str:
    """
    Generate a compelling hub page title.

    Args:
        location_name: Country or city name
        primary_keyword: Main targeting keyword
        keyword_terms: Additional terms to include

    Returns:
        SEO-optimized title

    Example:
        "Relocating to Cyprus: Visa, Cost of Living & Golden Visa Guide"
    """
    if not keyword_terms:
        keyword_terms = ["visa", "cost of living"]

    # Take top 2-3 terms for title
    title_terms = keyword_terms[:3]

    # Capitalize and format
    formatted_terms = [term.replace("-", " ").title() for term in title_terms]

    if len(formatted_terms) >= 3:
        terms_str = f"{formatted_terms[0]}, {formatted_terms[1]} & {formatted_terms[2]}"
    elif len(formatted_terms) == 2:
        terms_str = f"{formatted_terms[0]} & {formatted_terms[1]}"
    else:
        terms_str = formatted_terms[0] if formatted_terms else "Complete"

    return f"Relocating to {location_name}: {terms_str} Guide"


def generate_meta_description(
    location_name: str,
    keyword_terms: Optional[List[str]] = None,
    location_type: str = "country"
) -> str:
    """
    Generate an SEO meta description (155-160 chars ideal).

    Args:
        location_name: Country or city name
        keyword_terms: Terms to include
        location_type: "country" or "city"

    Returns:
        Meta description string
    """
    if not keyword_terms:
        keyword_terms = ["visa requirements", "cost of living", "tax benefits"]

    # Build dynamic description
    terms_formatted = [term.replace("-", " ") for term in keyword_terms[:3]]
    terms_str = ", ".join(terms_formatted)

    desc = (
        f"Your complete guide to relocating to {location_name}. "
        f"Everything you need to know about {terms_str}, and more. "
        f"Updated 2024."
    )

    # Truncate to ~155 chars if needed
    if len(desc) > 160:
        desc = desc[:157] + "..."

    return desc
