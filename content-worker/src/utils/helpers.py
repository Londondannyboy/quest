"""
Helper Utilities

Common utility functions used across activities.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse
from slugify import slugify as python_slugify
from typing import Any, Optional


def normalize_url(url: str) -> str:
    """
    Normalize a URL to a standard format.

    Args:
        url: Raw URL string

    Returns:
        Normalized URL with https:// and no trailing slash
    """
    url = url.strip().lower()

    # Add https if no protocol
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    # Remove trailing slash
    if url.endswith('/'):
        url = url[:-1]

    return url


def extract_domain(url: str) -> str:
    """
    Extract domain from URL.

    Args:
        url: URL string

    Returns:
        Domain name (e.g., "evercore.com")
    """
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path

    # Remove www.
    if domain.startswith('www.'):
        domain = domain[4:]

    return domain


def guess_company_name(domain: str) -> str:
    """
    Guess company name from domain.

    Args:
        domain: Domain name

    Returns:
        Guessed company name
    """
    # Remove TLD
    name = domain.split('.')[0]

    # Convert to title case
    name = name.replace('-', ' ').replace('_', ' ')
    name = ' '.join(word.capitalize() for word in name.split())

    return name


def generate_slug(name: str, domain: str) -> str:
    """
    Generate URL-friendly slug from company name and domain.

    Args:
        name: Company name
        domain: Company domain

    Returns:
        URL slug
    """
    # Try name first
    slug = python_slugify(name)

    # If slug is too generic, use domain
    if len(slug) < 3 or slug in ['inc', 'llc', 'ltd', 'company']:
        slug = python_slugify(domain.split('.')[0])

    return slug


def extract_year_from_text(text: str) -> int | None:
    """
    Extract a year (1900-2099) from text.

    Args:
        text: Text to search

    Returns:
        Year as integer or None
    """
    match = re.search(r'\b(19|20)\d{2}\b', text)
    if match:
        year = int(match.group())
        if 1900 <= year <= 2099:
            return year
    return None


def clean_text(text: str) -> str:
    """
    Clean and normalize text.

    Args:
        text: Raw text

    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove special characters
    text = re.sub(r'[^\w\s\-.,!?;:\'"()]', '', text)

    return text.strip()


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate text to max length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)].rsplit(' ', 1)[0] + suffix


def calculate_completeness(data: dict[str, Any], total_fields: int = 60) -> float:
    """
    Calculate data completeness score.

    Args:
        data: Data dictionary
        total_fields: Total expected fields

    Returns:
        Completeness score (0-100)
    """
    def count_filled(obj: Any) -> int:
        """Recursively count non-empty fields"""
        if obj is None or obj == "" or obj == []:
            return 0

        if isinstance(obj, dict):
            return sum(count_filled(v) for v in obj.values())

        if isinstance(obj, list):
            return 1 if len(obj) > 0 else 0

        return 1

    filled_fields = count_filled(data)
    score = (filled_fields / total_fields) * 100

    return min(100.0, score)


def merge_dicts(base: dict, update: dict) -> dict:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary
        update: Update dictionary

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def format_number(num: int | float) -> str:
    """
    Format number with commas.

    Args:
        num: Number to format

    Returns:
        Formatted string
    """
    if isinstance(num, float):
        return f"{num:,.2f}"
    return f"{num:,}"


def extract_email(text: str) -> str | None:
    """
    Extract email address from text.

    Args:
        text: Text to search

    Returns:
        Email address or None
    """
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, text)
    return match.group() if match else None


def extract_phone(text: str) -> str | None:
    """
    Extract phone number from text.

    Args:
        text: Text to search

    Returns:
        Phone number or None
    """
    # Simple pattern for international phone numbers
    pattern = r'\+?[\d\s\-\(\)]{10,}'
    match = re.search(pattern, text)
    return match.group().strip() if match else None


def geo_code_to_country(code: str) -> str:
    """
    Convert jurisdiction code to country name.

    Args:
        code: Jurisdiction code (UK, US, SG, etc.)

    Returns:
        Country name
    """
    mapping = {
        "UK": "United Kingdom",
        "US": "United States",
        "SG": "Singapore",
        "EU": "European Union",
        "DE": "Germany",
        "FR": "France",
        "NL": "Netherlands",
        "CH": "Switzerland",
        "AU": "Australia",
        "CA": "Canada",
        "IN": "India",
        "CN": "China",
        "JP": "Japan",
        "HK": "Hong Kong",
        "AE": "United Arab Emirates",
    }

    return mapping.get(code.upper(), code)
