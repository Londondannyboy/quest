"""
URL Normalization and Company Existence Check Activities

Core activities for:
1. Normalizing company URLs
2. Checking if company already exists in database
"""

import psycopg
from temporalio import activity
from typing import Dict, Any

from src.utils.config import config
from src.utils.helpers import (
    normalize_url,
    extract_domain,
    guess_company_name,
)
from src.models.research import NormalizedURL, ExistingCompanyCheck


@activity.defn
async def normalize_company_url(url: str, category: str) -> Dict[str, Any]:
    """
    Normalize company URL and extract basic information.

    Args:
        url: Raw company URL
        category: Company category

    Returns:
        Dict with normalized_url, domain, company_name_guess
    """
    activity.logger.info(f"Normalizing URL: {url}")

    try:
        # Normalize URL
        clean_url = normalize_url(url)
        domain = extract_domain(clean_url)
        name_guess = guess_company_name(domain)

        result = NormalizedURL(
            normalized_url=clean_url,
            domain=domain,
            company_name_guess=name_guess,
            is_valid=True
        )

        activity.logger.info(
            f"Normalized: {domain} -> {name_guess}"
        )

        return result.model_dump()

    except Exception as e:
        activity.logger.error(f"Failed to normalize URL: {e}")
        return NormalizedURL(
            normalized_url=url,
            domain="",
            company_name_guess="Unknown",
            is_valid=False
        ).model_dump()


@activity.defn
async def check_company_exists(domain: str) -> Dict[str, Any]:
    """
    Check if company already exists in database by domain.

    Args:
        domain: Company domain

    Returns:
        Dict with exists, company_id, slug, needs_update
    """
    activity.logger.info(f"Checking if company exists: {domain}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                # Query for company by domain in payload
                await cur.execute("""
                    SELECT
                        id,
                        slug,
                        updated_at,
                        payload
                    FROM companies
                    WHERE payload->>'website' LIKE %s
                    OR payload->>'website' LIKE %s
                    LIMIT 1
                """, (
                    f"%{domain}%",
                    f"%www.{domain}%"
                ))

                row = await cur.fetchone()

                if row:
                    company_id, slug, updated_at, payload = row

                    # Check if needs update (>30 days old)
                    from datetime import datetime, timedelta
                    needs_update = False
                    if updated_at:
                        age = datetime.now() - updated_at
                        needs_update = age > timedelta(days=30)

                    result = ExistingCompanyCheck(
                        exists=True,
                        company_id=str(company_id),
                        slug=slug,
                        needs_update=needs_update,
                        last_updated=updated_at.isoformat() if updated_at else None
                    )

                    activity.logger.info(
                        f"Company exists: {slug} (ID: {company_id}, "
                        f"needs_update: {needs_update})"
                    )

                    return result.model_dump()

                else:
                    # Company doesn't exist
                    result = ExistingCompanyCheck(
                        exists=False,
                        company_id=None,
                        slug=None,
                        needs_update=False,
                        last_updated=None
                    )

                    activity.logger.info("Company does not exist in database")

                    return result.model_dump()

    except Exception as e:
        activity.logger.error(f"Failed to check company existence: {e}")
        # On error, assume company doesn't exist
        return ExistingCompanyCheck(
            exists=False,
            company_id=None,
            slug=None,
            needs_update=False,
            last_updated=None
        ).model_dump()
