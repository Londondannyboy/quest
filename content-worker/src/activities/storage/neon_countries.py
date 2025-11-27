"""
Neon PostgreSQL Database Activities for Countries

Save/update country data and facts for country guides.
"""

from __future__ import annotations

import psycopg
import json
from temporalio import activity
from typing import Dict, Any, Optional
from datetime import datetime

from src.utils.config import config


# Country metadata lookup (ISO 3166-1)
COUNTRY_METADATA = {
    "CY": {"name": "Cyprus", "region": "Europe", "continent": "Europe", "flag_emoji": "🇨🇾", "capital": "Nicosia", "currency_code": "EUR"},
    "PT": {"name": "Portugal", "region": "Europe", "continent": "Europe", "flag_emoji": "🇵🇹", "capital": "Lisbon", "currency_code": "EUR"},
    "TH": {"name": "Thailand", "region": "Southeast Asia", "continent": "Asia", "flag_emoji": "🇹🇭", "capital": "Bangkok", "currency_code": "THB"},
    "AE": {"name": "United Arab Emirates", "region": "Middle East", "continent": "Asia", "flag_emoji": "🇦🇪", "capital": "Abu Dhabi", "currency_code": "AED"},
    "SG": {"name": "Singapore", "region": "Southeast Asia", "continent": "Asia", "flag_emoji": "🇸🇬", "capital": "Singapore", "currency_code": "SGD"},
    "MT": {"name": "Malta", "region": "Europe", "continent": "Europe", "flag_emoji": "🇲🇹", "capital": "Valletta", "currency_code": "EUR"},
    "ES": {"name": "Spain", "region": "Europe", "continent": "Europe", "flag_emoji": "🇪🇸", "capital": "Madrid", "currency_code": "EUR"},
    "GR": {"name": "Greece", "region": "Europe", "continent": "Europe", "flag_emoji": "🇬🇷", "capital": "Athens", "currency_code": "EUR"},
    "HR": {"name": "Croatia", "region": "Europe", "continent": "Europe", "flag_emoji": "🇭🇷", "capital": "Zagreb", "currency_code": "EUR"},
    "EE": {"name": "Estonia", "region": "Europe", "continent": "Europe", "flag_emoji": "🇪🇪", "capital": "Tallinn", "currency_code": "EUR"},
    "MX": {"name": "Mexico", "region": "North America", "continent": "North America", "flag_emoji": "🇲🇽", "capital": "Mexico City", "currency_code": "MXN"},
    "CR": {"name": "Costa Rica", "region": "Central America", "continent": "North America", "flag_emoji": "🇨🇷", "capital": "San Jose", "currency_code": "CRC"},
    "CO": {"name": "Colombia", "region": "South America", "continent": "South America", "flag_emoji": "🇨🇴", "capital": "Bogota", "currency_code": "COP"},
    "ID": {"name": "Indonesia", "region": "Southeast Asia", "continent": "Asia", "flag_emoji": "🇮🇩", "capital": "Jakarta", "currency_code": "IDR"},
    "MY": {"name": "Malaysia", "region": "Southeast Asia", "continent": "Asia", "flag_emoji": "🇲🇾", "capital": "Kuala Lumpur", "currency_code": "MYR"},
    "PH": {"name": "Philippines", "region": "Southeast Asia", "continent": "Asia", "flag_emoji": "🇵🇭", "capital": "Manila", "currency_code": "PHP"},
    "VN": {"name": "Vietnam", "region": "Southeast Asia", "continent": "Asia", "flag_emoji": "🇻🇳", "capital": "Hanoi", "currency_code": "VND"},
    "JP": {"name": "Japan", "region": "East Asia", "continent": "Asia", "flag_emoji": "🇯🇵", "capital": "Tokyo", "currency_code": "JPY"},
    "KR": {"name": "South Korea", "region": "East Asia", "continent": "Asia", "flag_emoji": "🇰🇷", "capital": "Seoul", "currency_code": "KRW"},
    "AU": {"name": "Australia", "region": "Oceania", "continent": "Oceania", "flag_emoji": "🇦🇺", "capital": "Canberra", "currency_code": "AUD"},
    "NZ": {"name": "New Zealand", "region": "Oceania", "continent": "Oceania", "flag_emoji": "🇳🇿", "capital": "Wellington", "currency_code": "NZD"},
    "CA": {"name": "Canada", "region": "North America", "continent": "North America", "flag_emoji": "🇨🇦", "capital": "Ottawa", "currency_code": "CAD"},
    "GB": {"name": "United Kingdom", "region": "Europe", "continent": "Europe", "flag_emoji": "🇬🇧", "capital": "London", "currency_code": "GBP"},
    "IE": {"name": "Ireland", "region": "Europe", "continent": "Europe", "flag_emoji": "🇮🇪", "capital": "Dublin", "currency_code": "EUR"},
    "CH": {"name": "Switzerland", "region": "Europe", "continent": "Europe", "flag_emoji": "🇨🇭", "capital": "Bern", "currency_code": "CHF"},
    "DE": {"name": "Germany", "region": "Europe", "continent": "Europe", "flag_emoji": "🇩🇪", "capital": "Berlin", "currency_code": "EUR"},
    "FR": {"name": "France", "region": "Europe", "continent": "Europe", "flag_emoji": "🇫🇷", "capital": "Paris", "currency_code": "EUR"},
    "NL": {"name": "Netherlands", "region": "Europe", "continent": "Europe", "flag_emoji": "🇳🇱", "capital": "Amsterdam", "currency_code": "EUR"},
    "IT": {"name": "Italy", "region": "Europe", "continent": "Europe", "flag_emoji": "🇮🇹", "capital": "Rome", "currency_code": "EUR"},
}


def generate_country_slug(name: str) -> str:
    """Generate URL-friendly slug from country name."""
    return name.lower().replace(" ", "-").replace("'", "")


@activity.defn
async def save_or_create_country(
    country_name: str,
    country_code: str,
    language: Optional[str] = None,
    relocation_motivations: Optional[list] = None,
    relocation_tags: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Save or create a country row in the database.

    Auto-populates metadata (region, continent, flag, currency) from COUNTRY_METADATA.
    If country exists, updates it. If not, creates it.

    Args:
        country_name: Country name (e.g., "Cyprus")
        country_code: ISO 3166-1 alpha-2 code (e.g., "CY")
        language: Primary language(s) (optional)
        relocation_motivations: List of motivation IDs this country is good for
        relocation_tags: List of tags (e.g., "eu-member", "english-friendly")

    Returns:
        Dict with country_id, slug, created (bool)
    """
    activity.logger.info(f"Saving/creating country: {country_name} ({country_code})")

    # Get metadata from lookup or use defaults
    metadata = COUNTRY_METADATA.get(country_code.upper(), {})

    slug = generate_country_slug(country_name)
    region = metadata.get("region", "Unknown")
    continent = metadata.get("continent", "Unknown")
    flag_emoji = metadata.get("flag_emoji", "🌍")
    capital = metadata.get("capital", "")
    currency_code = metadata.get("currency_code", "")

    # Default motivations if not provided
    if relocation_motivations is None:
        relocation_motivations = ["digital-nomad", "lifestyle", "retirement"]

    # Default tags if not provided
    if relocation_tags is None:
        relocation_tags = []

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                # Check if country exists
                await cur.execute("""
                    SELECT id, slug FROM countries WHERE code = %s
                """, (country_code.upper(),))

                existing = await cur.fetchone()

                if existing:
                    # Update existing country
                    country_id = existing[0]
                    await cur.execute("""
                        UPDATE countries
                        SET
                            name = %s,
                            slug = %s,
                            region = %s,
                            continent = %s,
                            flag_emoji = %s,
                            capital = %s,
                            currency_code = %s,
                            language = COALESCE(%s, language),
                            relocation_motivations = COALESCE(%s, relocation_motivations),
                            relocation_tags = COALESCE(%s, relocation_tags),
                            updated_at = NOW()
                        WHERE code = %s
                    """, (
                        country_name,
                        slug,
                        region,
                        continent,
                        flag_emoji,
                        capital,
                        currency_code,
                        language,
                        relocation_motivations,
                        relocation_tags,
                        country_code.upper()
                    ))

                    await conn.commit()

                    activity.logger.info(f"Updated country: {slug} (ID: {country_id})")
                    return {
                        "country_id": country_id,
                        "slug": slug,
                        "created": False,
                        "code": country_code.upper()
                    }

                else:
                    # Insert new country
                    await cur.execute("""
                        INSERT INTO countries (
                            name,
                            code,
                            slug,
                            region,
                            continent,
                            flag_emoji,
                            capital,
                            currency_code,
                            language,
                            relocation_motivations,
                            relocation_tags,
                            facts,
                            status,
                            created_at,
                            updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        RETURNING id
                    """, (
                        country_name,
                        country_code.upper(),
                        slug,
                        region,
                        continent,
                        flag_emoji,
                        capital,
                        currency_code,
                        language or "",
                        relocation_motivations,
                        relocation_tags,
                        json.dumps({}),  # Empty facts initially
                        "draft"
                    ))

                    result = await cur.fetchone()
                    country_id = result[0]

                    await conn.commit()

                    activity.logger.info(f"Created country: {slug} (ID: {country_id})")
                    return {
                        "country_id": country_id,
                        "slug": slug,
                        "created": True,
                        "code": country_code.upper()
                    }

    except Exception as e:
        activity.logger.error(f"Failed to save/create country: {e}")
        raise


@activity.defn
async def update_country_facts(
    country_code: str,
    facts: Dict[str, Any],
    merge: bool = True
) -> bool:
    """
    Update the facts JSONB for a country.

    By default merges new facts with existing ones. Set merge=False to replace entirely.

    Args:
        country_code: ISO 3166-1 alpha-2 code (e.g., "CY")
        facts: Dict of facts to store (tax rates, visa costs, etc.)
        merge: If True, merge with existing facts. If False, replace.

    Returns:
        Success boolean
    """
    activity.logger.info(f"Updating facts for country: {country_code}")

    # Add timestamp
    facts["last_updated"] = datetime.utcnow().isoformat()

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                if merge:
                    # Merge with existing facts using || operator
                    await cur.execute("""
                        UPDATE countries
                        SET
                            facts = COALESCE(facts, '{}'::jsonb) || %s::jsonb,
                            updated_at = NOW()
                        WHERE code = %s
                    """, (json.dumps(facts), country_code.upper()))
                else:
                    # Replace facts entirely
                    await cur.execute("""
                        UPDATE countries
                        SET
                            facts = %s,
                            updated_at = NOW()
                        WHERE code = %s
                    """, (json.dumps(facts), country_code.upper()))

                await conn.commit()

                activity.logger.info(f"Updated {len(facts)} facts for {country_code}")
                return True

    except Exception as e:
        activity.logger.error(f"Failed to update country facts: {e}")
        return False


@activity.defn
async def update_country_seo_keywords(
    country_code: str,
    seo_keywords: Dict[str, Any]
) -> bool:
    """
    Update the seo_keywords JSONB for a country.

    Stores DataForSEO research results for the country.

    Args:
        country_code: ISO 3166-1 alpha-2 code (e.g., "CY")
        seo_keywords: Dict from research_country_seo_keywords activity

    Returns:
        Success boolean
    """
    activity.logger.info(f"Updating SEO keywords for country: {country_code}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE countries
                    SET
                        seo_keywords = %s,
                        updated_at = NOW()
                    WHERE code = %s
                """, (json.dumps(seo_keywords), country_code.upper()))

                await conn.commit()

                activity.logger.info(f"Updated SEO keywords for {country_code}")
                return True

    except Exception as e:
        activity.logger.error(f"Failed to update country SEO keywords: {e}")
        return False


@activity.defn
async def link_article_to_country(
    article_id: str,
    country_code: str,
    guide_type: str = "country_comprehensive"
) -> bool:
    """
    Link an article to a country by setting country_code and guide_type.

    Args:
        article_id: Article ID to link
        country_code: ISO 3166-1 alpha-2 code (e.g., "CY")
        guide_type: Type of guide (e.g., "country_comprehensive", "visa_guide")

    Returns:
        Success boolean
    """
    activity.logger.info(f"Linking article {article_id} to country {country_code}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE articles
                    SET
                        country_code = %s,
                        guide_type = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (country_code.upper(), guide_type, article_id))

                await conn.commit()

                activity.logger.info(f"Linked article {article_id} to {country_code}")
                return True

    except Exception as e:
        activity.logger.error(f"Failed to link article to country: {e}")
        return False


@activity.defn
async def publish_country(country_code: str) -> bool:
    """
    Set country status to 'published' making it visible on the site.

    Args:
        country_code: ISO 3166-1 alpha-2 code (e.g., "CY")

    Returns:
        Success boolean
    """
    activity.logger.info(f"Publishing country: {country_code}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE countries
                    SET
                        status = 'published',
                        updated_at = NOW()
                    WHERE code = %s
                """, (country_code.upper(),))

                await conn.commit()

                activity.logger.info(f"Published country {country_code}")
                return True

    except Exception as e:
        activity.logger.error(f"Failed to publish country: {e}")
        return False


@activity.defn
async def get_country_by_code(country_code: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve country data by code.

    Args:
        country_code: ISO 3166-1 alpha-2 code (e.g., "CY")

    Returns:
        Country data dict or None
    """
    activity.logger.info(f"Fetching country: {country_code}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT
                        id, name, code, slug, region, continent,
                        flag_emoji, capital, currency_code, language,
                        relocation_motivations, relocation_tags,
                        facts, seo_keywords, status,
                        created_at, updated_at
                    FROM countries
                    WHERE code = %s
                """, (country_code.upper(),))

                row = await cur.fetchone()

                if not row:
                    return None

                return {
                    "id": row[0],
                    "name": row[1],
                    "code": row[2],
                    "slug": row[3],
                    "region": row[4],
                    "continent": row[5],
                    "flag_emoji": row[6],
                    "capital": row[7],
                    "currency_code": row[8],
                    "language": row[9],
                    "relocation_motivations": row[10],
                    "relocation_tags": row[11],
                    "facts": row[12],
                    "seo_keywords": row[13],
                    "status": row[14],
                    "created_at": row[15].isoformat() if row[15] else None,
                    "updated_at": row[16].isoformat() if row[16] else None,
                }

    except Exception as e:
        activity.logger.error(f"Failed to fetch country: {e}")
        return None
