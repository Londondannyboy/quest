"""
Neon PostgreSQL Database Activities

Save company profiles to Neon database.
"""

from __future__ import annotations

import psycopg
import json
from temporalio import activity
from typing import Dict, Any, Optional
from datetime import datetime

from src.utils.config import config
from src.utils.helpers import generate_slug


@activity.defn
async def save_company_to_neon(
    company_id: Optional[str],
    domain: str,
    name: str,
    app: str,
    category: str,
    payload: Dict[str, Any],
    logo_url: Optional[str],
    featured_image_url: Optional[str],
    hero_image_url: Optional[str] = None
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
        hero_image_url: URL to hero image

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

                # Extract content from V2 profile_sections for legacy columns
                description = None
                overview = None

                # Priority 1: Use short_description if available (clean, purpose-written)
                if "short_description" in payload and payload["short_description"]:
                    description = payload["short_description"]

                if "profile_sections" in payload:
                    sections = payload["profile_sections"]
                    # Use overview section
                    if "overview" in sections:
                        overview_content = sections["overview"].get("content", "")
                        overview = overview_content

                        # Priority 2: If no short_description, create clean excerpt from overview
                        if not description and overview_content:
                            import re
                            # Strip markdown links: [text](url) -> text
                            clean_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', overview_content)
                            # Strip standalone URLs
                            clean_text = re.sub(r'https?://\S+', '', clean_text)
                            # Strip markdown bold
                            clean_text = re.sub(r'\*\*(.+?)\*\*', r'\1', clean_text)
                            # Clean up extra whitespace
                            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                            # Take first 200 chars, break at sentence
                            if len(clean_text) > 200:
                                # Try to break at sentence
                                sentences = clean_text[:200].split('. ')
                                if len(sentences) > 1:
                                    description = sentences[0] + '.'
                                else:
                                    description = clean_text[:200].rsplit(' ', 1)[0] + '...'
                            else:
                                description = clean_text

                    # Combine all sections for overview if no dedicated overview
                    if not overview and sections:
                        overview = "\n\n".join([
                            f"**{s.get('title', k.title())}**\n{s.get('content', '')}"
                            for k, s in sections.items()
                        ])

                # Extract meta description from payload (max 160 chars for VARCHAR(160))
                meta_description = (
                    payload.get("short_description") or
                    payload.get("tagline") or
                    (description[:160] if description else "") or
                    ""
                )[:160]  # Ensure never exceeds database limit

                # Store logo_url in payload
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
                            description = %s,
                            overview = %s,
                            featured_image_url = %s,
                            hero_image_url = %s,
                            meta_description = %s,
                            payload = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        RETURNING id
                    """, (
                        name,
                        slug,
                        app,
                        description,
                        overview,
                        featured_image_url,
                        hero_image_url,
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
                            description,
                            overview,
                            featured_image_url,
                            hero_image_url,
                            meta_description,
                            payload,
                            created_at,
                            updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        ON CONFLICT (slug)
                        DO UPDATE SET
                            name = EXCLUDED.name,
                            description = EXCLUDED.description,
                            overview = EXCLUDED.overview,
                            featured_image_url = EXCLUDED.featured_image_url,
                            hero_image_url = EXCLUDED.hero_image_url,
                            meta_description = EXCLUDED.meta_description,
                            payload = EXCLUDED.payload,
                            updated_at = NOW()
                        RETURNING id
                    """, (
                        slug,
                        name,
                        app,
                        description,
                        overview,
                        featured_image_url,
                        hero_image_url,
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
async def get_company_by_id(company_id: str) -> Optional[Dict[str, Any]]:
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


@activity.defn
async def save_article_to_neon(
    article_id: Optional[str],
    slug: str,
    title: str,
    app: str,
    article_type: str,
    payload: Dict[str, Any],
    featured_image_url: Optional[str] = None,
    hero_image_url: Optional[str] = None,
    mentioned_companies: Optional[list] = None,
    status: str = "draft"
) -> str:
    """
    Save or update article in Neon database.

    Args:
        article_id: Existing article ID (None for new)
        slug: Article slug
        title: Article title
        app: App context (placement, relocation, etc.)
        article_type: Type (news, guide, comparison) - stored in payload
        payload: Full ArticlePayload as dict
        featured_image_url: URL to featured image
        hero_image_url: URL to hero image
        mentioned_companies: List of company mentions with relevance scores
        status: Article status (draft, published, archived)

    Returns:
        Article ID (str)
    """
    activity.logger.info(f"Saving article '{title}' to Neon database")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                # Extract key fields from payload
                content = payload.get("content", "")
                excerpt = payload.get("excerpt", "")[:500] if payload.get("excerpt") else ""
                meta_description = payload.get("meta_description", "")[:160] if payload.get("meta_description") else ""
                word_count = payload.get("word_count", 0)
                article_angle = payload.get("article_angle") or article_type  # Use article_type as angle

                if article_id:
                    # Update existing article
                    await cur.execute("""
                        UPDATE articles
                        SET
                            slug = %s,
                            title = %s,
                            app = %s,
                            content = %s,
                            excerpt = %s,
                            meta_description = %s,
                            word_count = %s,
                            article_angle = %s,
                            featured_image_url = %s,
                            hero_image_url = %s,
                            payload = %s,
                            status = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        RETURNING id
                    """, (
                        slug,
                        title,
                        app,
                        content,
                        excerpt,
                        meta_description,
                        word_count,
                        article_angle,
                        featured_image_url,
                        hero_image_url,
                        json.dumps(payload),
                        status,
                        article_id
                    ))

                    result = await cur.fetchone()
                    final_id = result[0] if result else article_id

                    activity.logger.info(f"Updated article: {slug} (ID: {final_id})")

                else:
                    # Insert new article
                    await cur.execute("""
                        INSERT INTO articles (
                            slug,
                            title,
                            app,
                            content,
                            excerpt,
                            meta_description,
                            word_count,
                            article_angle,
                            featured_image_url,
                            hero_image_url,
                            payload,
                            status,
                            created_at,
                            updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        ON CONFLICT (slug)
                        DO UPDATE SET
                            title = EXCLUDED.title,
                            content = EXCLUDED.content,
                            excerpt = EXCLUDED.excerpt,
                            meta_description = EXCLUDED.meta_description,
                            word_count = EXCLUDED.word_count,
                            article_angle = EXCLUDED.article_angle,
                            featured_image_url = EXCLUDED.featured_image_url,
                            hero_image_url = EXCLUDED.hero_image_url,
                            payload = EXCLUDED.payload,
                            status = EXCLUDED.status,
                            updated_at = NOW()
                        RETURNING id
                    """, (
                        slug,
                        title,
                        app,
                        content,
                        excerpt,
                        meta_description,
                        word_count,
                        article_angle,
                        featured_image_url,
                        hero_image_url,
                        json.dumps(payload),
                        status
                    ))

                    result = await cur.fetchone()
                    final_id = str(result[0])

                    activity.logger.info(f"Inserted article: {slug} (ID: {final_id})")

                # Link to mentioned companies
                if mentioned_companies:
                    for company in mentioned_companies:
                        company_name = company.get("name", "")
                        relevance_score = company.get("relevance_score", 0.5)

                        # Try to find company by name
                        await cur.execute("""
                            SELECT id FROM companies
                            WHERE LOWER(name) = LOWER(%s)
                            LIMIT 1
                        """, (company_name,))

                        company_row = await cur.fetchone()

                        if company_row:
                            company_id = str(company_row[0])

                            # Create link
                            await cur.execute("""
                                INSERT INTO article_companies (
                                    article_id,
                                    company_id,
                                    relevance_score,
                                    created_at
                                )
                                VALUES (%s, %s, %s, NOW())
                                ON CONFLICT (article_id, company_id)
                                DO UPDATE SET
                                    relevance_score = EXCLUDED.relevance_score,
                                    updated_at = NOW()
                            """, (final_id, company_id, relevance_score))

                            activity.logger.info(
                                f"Linked article to company: {company_name}"
                            )

                await conn.commit()

                return str(final_id)

    except Exception as e:
        activity.logger.error(f"Failed to save article to Neon: {e}")
        raise


@activity.defn
async def get_article_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve article by slug.

    Args:
        slug: Article slug

    Returns:
        Article data dict or None
    """
    activity.logger.info(f"Fetching article: {slug}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT
                        id,
                        slug,
                        title,
                        app,
                        content,
                        excerpt,
                        featured_image_url,
                        hero_image_url,
                        meta_description,
                        word_count,
                        article_angle,
                        payload,
                        status,
                        published_at,
                        created_at,
                        updated_at
                    FROM articles
                    WHERE slug = %s
                """, (slug,))

                row = await cur.fetchone()

                if not row:
                    return None

                return {
                    "id": str(row[0]),
                    "slug": row[1],
                    "title": row[2],
                    "app": row[3],
                    "content": row[4],
                    "excerpt": row[5],
                    "featured_image_url": row[6],
                    "hero_image_url": row[7],
                    "meta_description": row[8],
                    "word_count": row[9],
                    "article_angle": row[10],
                    "payload": row[11],
                    "status": row[12],
                    "published_at": row[13].isoformat() if row[13] else None,
                    "created_at": row[14].isoformat() if row[14] else None,
                    "updated_at": row[15].isoformat() if row[15] else None,
                }

    except Exception as e:
        activity.logger.error(f"Failed to fetch article: {e}")
        return None
