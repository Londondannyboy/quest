"""
Data Completeness Calculation Activity

Calculate how complete a company profile is based on filled fields.
"""

from temporalio import activity
from typing import Dict, Any


# Field weights (some fields are more important than others)
FIELD_WEIGHTS = {
    # Critical fields (10 points each)
    "legal_name": 10,
    "tagline": 10,
    "description": 10,
    "headquarters_country": 10,
    "company_type": 10,

    # Important fields (5 points each)
    "industry": 5,
    "headquarters_city": 5,
    "website": 5,
    "phone": 5,
    "linkedin_url": 5,

    # Hero stats (7 points each)
    "hero_stats.employees": 7,
    "hero_stats.founded_year": 7,
    "hero_stats.countries_served": 7,

    # Medium importance (3 points each)
    "services": 3,
    "headcount": 3,
    "executives": 3,
    "office_locations": 3,
    "key_clients": 3,
    "recent_news": 3,

    # Nice to have (1 point each)
    "also_known_as": 1,
    "sub_industries": 1,
    "specializations": 1,
    "awards": 1,
    "competitors": 1,
}


@activity.defn
async def calculate_completeness_score(
    payload: Dict[str, Any]
) -> float:
    """
    Calculate data completeness score (0-100).

    Args:
        payload: CompanyPayload as dict

    Returns:
        Completeness score (0-100)
    """
    activity.logger.info("Calculating data completeness score")

    total_possible_points = sum(FIELD_WEIGHTS.values())
    earned_points = 0.0

    for field_path, points in FIELD_WEIGHTS.items():
        value = get_nested_value(payload, field_path)

        if is_field_filled(value):
            earned_points += points

    # Calculate percentage
    score = (earned_points / total_possible_points) * 100

    # Cap at 100
    score = min(100.0, score)

    activity.logger.info(
        f"Completeness: {score:.1f}% "
        f"({earned_points:.0f}/{total_possible_points} points)"
    )

    return round(score, 1)


def get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """
    Get value from nested dict using dot notation.

    Args:
        data: Dictionary
        path: Dot-separated path (e.g., "hero_stats.employees")

    Returns:
        Value or None
    """
    keys = path.split('.')
    value = data

    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None

    return value


def is_field_filled(value: Any) -> bool:
    """
    Check if a field is meaningfully filled.

    Args:
        value: Field value

    Returns:
        True if filled, False if empty
    """
    # None or empty string
    if value is None or value == "":
        return False

    # Empty list
    if isinstance(value, list) and len(value) == 0:
        return False

    # Empty dict
    if isinstance(value, dict) and len(value) == 0:
        return False

    # Dict with all None/empty values
    if isinstance(value, dict):
        filled_items = sum(
            1 for v in value.values()
            if is_field_filled(v)
        )
        return filled_items > 0

    # List with items
    if isinstance(value, list):
        return len(value) > 0

    # Any other value is considered filled
    return True


@activity.defn
async def get_missing_fields(
    payload: Dict[str, Any],
    importance: str = "critical"
) -> list[str]:
    """
    Get list of missing fields by importance level.

    Args:
        payload: CompanyPayload as dict
        importance: Filter by importance (critical, important, all)

    Returns:
        List of missing field names
    """
    activity.logger.info(f"Finding missing {importance} fields")

    # Define importance levels
    importance_levels = {
        "critical": 10,
        "important": 5,
        "all": 0
    }

    min_points = importance_levels.get(importance, 0)

    missing = []

    for field_path, points in FIELD_WEIGHTS.items():
        if points < min_points:
            continue

        value = get_nested_value(payload, field_path)

        if not is_field_filled(value):
            missing.append(field_path)

    activity.logger.info(f"Found {len(missing)} missing {importance} fields")

    return missing


@activity.defn
async def suggest_improvements(
    payload: Dict[str, Any],
    completeness_score: float
) -> list[str]:
    """
    Suggest improvements to increase completeness score.

    Args:
        payload: CompanyPayload as dict
        completeness_score: Current score

    Returns:
        List of improvement suggestions
    """
    activity.logger.info("Generating improvement suggestions")

    suggestions = []

    # Get missing critical fields
    critical_missing = await get_missing_fields(payload, "critical")

    if critical_missing:
        suggestions.append(
            f"Add {len(critical_missing)} critical fields: "
            f"{', '.join(critical_missing[:3])}"
        )

    # Check hero stats
    hero_stats = payload.get("hero_stats", {})
    empty_hero_stats = [
        key for key, value in hero_stats.items()
        if not is_field_filled(value)
    ]

    if empty_hero_stats:
        suggestions.append(
            f"Complete hero stats: {', '.join(empty_hero_stats[:3])}"
        )

    # Check if services are listed
    services = payload.get("services", [])
    if len(services) < 3:
        suggestions.append("Add more services (aim for 3-5)")

    # Check if executives are listed
    executives = payload.get("executives", [])
    if len(executives) == 0:
        suggestions.append("Add executive team members")

    # Check if recent news is included
    news = payload.get("recent_news", [])
    if len(news) < 3:
        suggestions.append("Add more recent news articles")

    activity.logger.info(f"Generated {len(suggestions)} suggestions")

    return suggestions
