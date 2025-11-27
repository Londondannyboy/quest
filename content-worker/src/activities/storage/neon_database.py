"""
Neon PostgreSQL Database Activities

Save company profiles to Neon database.
"""

from __future__ import annotations

import psycopg
import json
from temporalio import activity
from typing import Dict, Any, Optional, List
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
    featured_asset_url: Optional[str],
    hero_asset_url: Optional[str] = None,
    video_url: Optional[str] = None,
    video_playback_id: Optional[str] = None,
    video_asset_id: Optional[str] = None
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
        featured_asset_url: URL to featured asset (GIF when video exists, image otherwise)
        hero_asset_url: URL to hero asset (null when video exists - video supersedes)
        video_url: Mux HLS stream URL
        video_playback_id: Mux playback ID for generating thumbnails/GIFs
        video_asset_id: Mux asset ID for management

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
                            featured_asset_url = %s,
                            hero_asset_url = %s,
                            meta_description = %s,
                            payload = %s,
                            video_url = %s,
                            video_playback_id = %s,
                            video_asset_id = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        RETURNING id
                    """, (
                        name,
                        slug,
                        app,
                        description,
                        overview,
                        featured_asset_url,
                        hero_asset_url,
                        meta_description,
                        json.dumps(payload),
                        video_url,
                        video_playback_id,
                        video_asset_id,
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
                            featured_asset_url,
                            hero_asset_url,
                            meta_description,
                            payload,
                            video_url,
                            video_playback_id,
                            video_asset_id,
                            created_at,
                            updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        ON CONFLICT (slug)
                        DO UPDATE SET
                            name = EXCLUDED.name,
                            description = EXCLUDED.description,
                            overview = EXCLUDED.overview,
                            featured_asset_url = EXCLUDED.featured_asset_url,
                            hero_asset_url = EXCLUDED.hero_asset_url,
                            meta_description = EXCLUDED.meta_description,
                            payload = EXCLUDED.payload,
                            video_url = EXCLUDED.video_url,
                            video_playback_id = EXCLUDED.video_playback_id,
                            video_asset_id = EXCLUDED.video_asset_id,
                            updated_at = NOW()
                        RETURNING id
                    """, (
                        slug,
                        name,
                        app,
                        description,
                        overview,
                        featured_asset_url,
                        hero_asset_url,
                        meta_description,
                        json.dumps(payload),
                        video_url,
                        video_playback_id,
                        video_asset_id
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
                    'featured_asset_url', 'hero_asset_url', 'meta_description',
                    'status', 'visibility', 'video_url', 'video_playback_id', 'video_asset_id'
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
                        featured_asset_url,
                        hero_asset_url,
                        meta_description,
                        payload,
                        created_at,
                        updated_at,
                        video_url,
                        video_playback_id
                    FROM companies
                    WHERE id = %s
                """, (company_id,))

                row = await cur.fetchone()

                if not row:
                    return None

                payload = row[7]
                return {
                    "id": str(row[0]),
                    "slug": row[1],
                    "name": row[2],
                    "app": row[3],
                    "logo_url": payload.get("logo_url") if payload else None,
                    "featured_asset_url": row[4],
                    "hero_asset_url": row[5],
                    "meta_description": row[6],
                    "payload": payload,
                    "created_at": row[8].isoformat() if row[8] else None,
                    "updated_at": row[9].isoformat() if row[9] else None,
                    "video_url": row[10],
                    "video_playback_id": row[11],
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
    featured_asset_url: Optional[str] = None,
    hero_asset_url: Optional[str] = None,
    mentioned_companies: Optional[list] = None,
    status: str = "draft",
    video_url: Optional[str] = None,
    video_playback_id: Optional[str] = None,
    video_asset_id: Optional[str] = None,
    raw_research: Optional[str] = None,
    video_narrative: Optional[Dict[str, Any]] = None,
    zep_facts: Optional[List[Dict[str, Any]]] = None
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
        featured_asset_url: URL to featured asset (GIF when video exists, image otherwise)
        hero_asset_url: URL to hero asset (null when video exists - video supersedes)
        mentioned_companies: List of company mentions with relevance scores
        status: Article status (draft, published, archived)
        video_url: Mux HLS stream URL
        video_playback_id: Mux playback ID for generating thumbnails/GIFs
        video_asset_id: Mux asset ID for management
        raw_research: Full raw research data (unlimited TEXT)
        video_narrative: 3-act narrative structure for video-first articles (JSONB)
        zep_facts: Facts from Zep knowledge graph used during generation (for audit)

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
                            featured_asset_url = %s,
                            hero_asset_url = %s,
                            payload = %s,
                            status = %s,
                            video_url = %s,
                            video_playback_id = %s,
                            video_asset_id = %s,
                            raw_research = %s,
                            video_narrative = %s,
                            zep_facts = COALESCE(%s, zep_facts),
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
                        featured_asset_url,
                        hero_asset_url,
                        json.dumps(payload),
                        status,
                        video_url,
                        video_playback_id,
                        video_asset_id,
                        raw_research,
                        json.dumps(video_narrative) if video_narrative else None,
                        json.dumps(zep_facts) if zep_facts is not None else None,  # Preserve empty array []
                        article_id
                    ))
                    activity.logger.info(f"zep_facts for UPDATE: {len(zep_facts) if zep_facts else 'None'} facts")

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
                            featured_asset_url,
                            hero_asset_url,
                            payload,
                            status,
                            video_url,
                            video_playback_id,
                            video_asset_id,
                            raw_research,
                            video_narrative,
                            zep_facts,
                            created_at,
                            updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        ON CONFLICT (slug)
                        DO UPDATE SET
                            title = EXCLUDED.title,
                            content = EXCLUDED.content,
                            excerpt = EXCLUDED.excerpt,
                            meta_description = EXCLUDED.meta_description,
                            word_count = EXCLUDED.word_count,
                            article_angle = EXCLUDED.article_angle,
                            featured_asset_url = EXCLUDED.featured_asset_url,
                            hero_asset_url = EXCLUDED.hero_asset_url,
                            payload = EXCLUDED.payload,
                            status = EXCLUDED.status,
                            video_url = EXCLUDED.video_url,
                            video_playback_id = EXCLUDED.video_playback_id,
                            video_asset_id = EXCLUDED.video_asset_id,
                            raw_research = EXCLUDED.raw_research,
                            video_narrative = EXCLUDED.video_narrative,
                            zep_facts = COALESCE(EXCLUDED.zep_facts, articles.zep_facts),
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
                        featured_asset_url,
                        hero_asset_url,
                        json.dumps(payload),
                        status,
                        video_url,
                        video_playback_id,
                        video_asset_id,
                        raw_research,
                        json.dumps(video_narrative) if video_narrative else None,
                        json.dumps(zep_facts) if zep_facts is not None else None  # Preserve empty array []
                    ))
                    activity.logger.info(f"zep_facts for INSERT: {len(zep_facts) if zep_facts else 'None'} facts")

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
                        featured_asset_url,
                        hero_asset_url,
                        meta_description,
                        word_count,
                        article_angle,
                        payload,
                        status,
                        published_at,
                        created_at,
                        updated_at,
                        video_url,
                        video_playback_id,
                        video_narrative
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
                    "featured_asset_url": row[6],
                    "hero_asset_url": row[7],
                    "meta_description": row[8],
                    "word_count": row[9],
                    "article_angle": row[10],
                    "payload": row[11],
                    "status": row[12],
                    "published_at": row[13].isoformat() if row[13] else None,
                    "created_at": row[14].isoformat() if row[14] else None,
                    "updated_at": row[15].isoformat() if row[15] else None,
                    "video_url": row[16],
                    "video_playback_id": row[17],
                    "video_narrative": row[18],
                }

    except Exception as e:
        activity.logger.error(f"Failed to fetch article: {e}")
        return None


@activity.defn
async def save_spawn_candidate(
    spawn_opportunity: Dict[str, Any],
    parent_article_id: str,
    app: str
) -> Optional[str]:
    """
    Save a spawn opportunity as a candidate article in the database.

    Creates a minimal article record with spawn_status='candidate' for later
    review and generation. The topic, confidence, and reason are stored.

    Args:
        spawn_opportunity: Dict with topic, reason, confidence, article_type, unique_angle
        parent_article_id: ID of the parent article that spawned this candidate
        app: App context (placement, relocation, etc.)

    Returns:
        Spawn candidate article ID (str) or None if failed
    """
    topic = spawn_opportunity.get("topic", "")
    reason = spawn_opportunity.get("reason", "")
    confidence = spawn_opportunity.get("confidence", 0.0)
    article_type = spawn_opportunity.get("article_type", "guide")
    unique_angle = spawn_opportunity.get("unique_angle", "")

    activity.logger.info(f"Saving spawn candidate: '{topic}' (confidence: {confidence})")

    if not topic:
        activity.logger.warning("No topic provided for spawn candidate")
        return None

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                # Generate a slug from the topic
                slug = generate_slug(topic, "spawn")

                # Store spawn metadata in payload
                payload = {
                    "topic": topic,
                    "article_type": article_type,
                    "unique_angle": unique_angle,
                    "spawn_metadata": {
                        "reason": reason,
                        "confidence": confidence,
                        "parent_article_id": parent_article_id
                    }
                }

                # Insert as candidate article
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
                        payload,
                        status,
                        spawn_status,
                        parent_article_id,
                        spawn_confidence,
                        spawn_reason,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (slug)
                    DO UPDATE SET
                        spawn_confidence = GREATEST(articles.spawn_confidence, EXCLUDED.spawn_confidence),
                        spawn_reason = EXCLUDED.spawn_reason,
                        updated_at = NOW()
                    RETURNING id
                """, (
                    slug,
                    topic,  # Use topic as title
                    app,
                    "",  # Empty content (not generated yet)
                    f"Spawn candidate: {unique_angle}" if unique_angle else "",
                    "",  # Empty meta description
                    0,  # No word count yet
                    article_type,
                    json.dumps(payload),
                    "draft",  # Status is draft
                    "candidate",  # spawn_status = candidate
                    parent_article_id,
                    confidence,
                    reason
                ))

                result = await cur.fetchone()
                spawn_id = str(result[0]) if result else None

                await conn.commit()

                activity.logger.info(f"Saved spawn candidate: {slug} (ID: {spawn_id})")
                return spawn_id

    except Exception as e:
        activity.logger.error(f"Failed to save spawn candidate: {e}")
        return None
