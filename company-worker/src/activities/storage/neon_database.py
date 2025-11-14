"""
Neon PostgreSQL Database Activities

Save company profiles to Neon database.
"""

import psycopg
import json
from temporalio import activity
from typing import Dict, Any
from datetime import datetime

from src.utils.config import config
from src.utils.helpers import generate_slug


@activity.defn
async def save_company_to_neon(
    company_id: str | None,
    domain: str,
    name: str,
    app: str,
    category: str,
    payload: Dict[str, Any],
    logo_url: str | None,
    featured_image_url: str | None
) -> str:
    """
    Save or update company profile in Neon database.

    Args:
        company_id: Existing company ID (None for new)
        domain: Company domain
        name: Company name
        app: App context (placement, relocation, etc.)
        category: Company category
        payload: Full CompanyPayload as dict
        logo_url: URL to company logo
        featured_image_url: URL to featured image

    Returns:
        Company ID (str)
    """
    activity.logger.info(f"Saving {name} to Neon database")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                # Generate slug
                slug = generate_slug(name, domain)

                # Extract meta description from payload
                meta_description = (
                    payload.get("tagline") or
                    payload.get("short_description") or
                    (payload.get("description") or "")[:160]
                )

                # Store logo_url in payload (schema doesn't have logo_url column)
                if logo_url:
                    payload["logo_url"] = logo_url

                if company_id:
                    # Update existing company
                    await cur.execute("""
                        UPDATE companies
                        SET
                            name = %s,
                            slug = %s,
                            app = %s,
                            featured_image_url = %s,
                            meta_description = %s,
                            payload = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        RETURNING id
                    """, (
                        name,
                        slug,
                        app,
                        featured_image_url,
                        meta_description,
                        json.dumps(payload),
                        company_id
                    ))

                    result = await cur.fetchone()
                    final_id = result[0] if result else company_id

                    activity.logger.info(f"Updated company: {slug} (ID: {final_id})")

                else:
                    # Insert new company
                    await cur.execute("""
                        INSERT INTO companies (
                            slug,
                            name,
                            app,
                            featured_image_url,
                            meta_description,
                            payload,
                            created_at,
                            updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                        ON CONFLICT (slug)
                        DO UPDATE SET
                            name = EXCLUDED.name,
                            featured_image_url = EXCLUDED.featured_image_url,
                            meta_description = EXCLUDED.meta_description,
                            payload = EXCLUDED.payload,
                            updated_at = NOW()
                        RETURNING id
                    """, (
                        slug,
                        name,
                        app,
                        featured_image_url,
                        meta_description,
                        json.dumps(payload)
                    ))

                    result = await cur.fetchone()
                    final_id = str(result[0])

                    activity.logger.info(f"Inserted company: {slug} (ID: {final_id})")

                await conn.commit()

                return final_id

    except Exception as e:
        activity.logger.error(f"Failed to save company to Neon: {e}")
        raise


@activity.defn
async def update_company_metadata(
    company_id: str,
    metadata: Dict[str, Any]
) -> bool:
    """
    Update company metadata fields.

    Args:
        company_id: Company ID
        metadata: Metadata to update

    Returns:
        Success boolean
    """
    activity.logger.info(f"Updating metadata for company {company_id}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                # Build SET clause dynamically
                # Note: logo_url is stored in payload JSONB, not as a column
                allowed_fields = [
                    'featured_image_url', 'meta_description',
                    'status', 'visibility'
                ]

                set_parts = []
                values = []

                for key, value in metadata.items():
                    if key in allowed_fields:
                        set_parts.append(f"{key} = %s")
                        values.append(value)

                if not set_parts:
                    activity.logger.warning("No valid metadata fields to update")
                    return False

                set_clause = ", ".join(set_parts)
                values.append(company_id)

                await cur.execute(f"""
                    UPDATE companies
                    SET {set_clause}, updated_at = NOW()
                    WHERE id = %s
                """, values)

                await conn.commit()

                activity.logger.info("Metadata updated successfully")
                return True

    except Exception as e:
        activity.logger.error(f"Failed to update metadata: {e}")
        return False


@activity.defn
async def get_company_by_id(company_id: str) -> Dict[str, Any] | None:
    """
    Retrieve company by ID.

    Args:
        company_id: Company ID

    Returns:
        Company data dict or None
    """
    activity.logger.info(f"Fetching company {company_id}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT
                        id,
                        slug,
                        name,
                        app,
                        featured_image_url,
                        meta_description,
                        payload,
                        created_at,
                        updated_at
                    FROM companies
                    WHERE id = %s
                """, (company_id,))

                row = await cur.fetchone()

                if not row:
                    return None

                payload = row[6]
                return {
                    "id": str(row[0]),
                    "slug": row[1],
                    "name": row[2],
                    "app": row[3],
                    "logo_url": payload.get("logo_url") if payload else None,
                    "featured_image_url": row[4],
                    "meta_description": row[5],
                    "payload": payload,
                    "created_at": row[7].isoformat() if row[7] else None,
                    "updated_at": row[8].isoformat() if row[8] else None,
                }

    except Exception as e:
        activity.logger.error(f"Failed to fetch company: {e}")
        return None
