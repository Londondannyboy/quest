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
    zep_facts: Optional[List[Dict[str, Any]]] = None,
    # SEO keyword targeting
    target_keyword: Optional[str] = None,
    keyword_volume: Optional[int] = None,
    keyword_difficulty: Optional[float] = None,
    secondary_keywords: Optional[List[str]] = None,
    # Country guide content modes (legacy - single article approach)
    content_story: Optional[str] = None,
    content_guide: Optional[str] = None,
    content_yolo: Optional[str] = None,
    content_voices: Optional[List[Dict[str, Any]]] = None,
    # Cluster architecture (new - separate articles per mode)
    cluster_id: Optional[str] = None,
    parent_id: Optional[int] = None,
    article_mode: Optional[str] = None  # story, guide, yolo, voices
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
        target_keyword: Primary SEO target keyword
        keyword_volume: Monthly search volume for target keyword
        keyword_difficulty: Difficulty score (0-100) for target keyword
        secondary_keywords: List of secondary keywords to target
        content_story: Story mode content (narrative style) for country guides
        content_guide: Guide mode content (practical style) for country guides
        content_yolo: YOLO mode content (adventure style) for country guides
        content_voices: Curated expat voices/testimonials for enrichment
        cluster_id: UUID grouping related articles (Story/Guide/YOLO/Voices variants)
        parent_id: ID of parent article in cluster (NULL for parent/Story article)
        article_mode: Content mode: story, guide, yolo, or voices

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

                # Extract content modes from payload if not explicitly provided
                # These are used for country guide articles with story/guide/yolo modes
                _content_story = content_story or payload.get("content_story")
                _content_guide = content_guide or payload.get("content_guide")
                _content_yolo = content_yolo or payload.get("content_yolo")
                _content_voices = content_voices or payload.get("curation", {}).get("voices") or payload.get("content_voices")

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
                            target_keyword = COALESCE(%s, target_keyword),
                            keyword_volume = COALESCE(%s, keyword_volume),
                            keyword_difficulty = COALESCE(%s, keyword_difficulty),
                            secondary_keywords = COALESCE(%s, secondary_keywords),
                            content_story = COALESCE(%s, content_story),
                            content_guide = COALESCE(%s, content_guide),
                            content_yolo = COALESCE(%s, content_yolo),
                            content_voices = COALESCE(%s, content_voices),
                            cluster_id = COALESCE(%s, cluster_id),
                            parent_id = COALESCE(%s, parent_id),
                            article_mode = COALESCE(%s, article_mode),
                            updated_at = NOW(),
                            published_at = CASE
                                WHEN %s = 'published' AND published_at IS NULL THEN NOW()
                                ELSE published_at
                            END
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
                        target_keyword,
                        keyword_volume,
                        keyword_difficulty,
                        json.dumps(secondary_keywords) if secondary_keywords else None,
                        _content_story,
                        _content_guide,
                        _content_yolo,
                        json.dumps(_content_voices) if _content_voices else None,
                        cluster_id,
                        parent_id,
                        article_mode,
                        status,  # For published_at CASE
                        article_id
                    ))
                    activity.logger.info(f"zep_facts for UPDATE: {len(zep_facts) if zep_facts else 'None'} facts")
                    if _content_story:
                        activity.logger.info(f"Content modes: story={len(_content_story)} chars, guide={len(_content_guide or '')} chars, yolo={len(_content_yolo or '')} chars")
                    if target_keyword:
                        activity.logger.info(f"SEO keyword: '{target_keyword}' (vol={keyword_volume}, diff={keyword_difficulty})")

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
                            target_keyword,
                            keyword_volume,
                            keyword_difficulty,
                            secondary_keywords,
                            content_story,
                            content_guide,
                            content_yolo,
                            content_voices,
                            cluster_id,
                            parent_id,
                            article_mode,
                            created_at,
                            updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
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
                            target_keyword = COALESCE(EXCLUDED.target_keyword, articles.target_keyword),
                            keyword_volume = COALESCE(EXCLUDED.keyword_volume, articles.keyword_volume),
                            keyword_difficulty = COALESCE(EXCLUDED.keyword_difficulty, articles.keyword_difficulty),
                            secondary_keywords = COALESCE(EXCLUDED.secondary_keywords, articles.secondary_keywords),
                            content_story = COALESCE(EXCLUDED.content_story, articles.content_story),
                            content_guide = COALESCE(EXCLUDED.content_guide, articles.content_guide),
                            content_yolo = COALESCE(EXCLUDED.content_yolo, articles.content_yolo),
                            content_voices = COALESCE(EXCLUDED.content_voices, articles.content_voices),
                            cluster_id = COALESCE(EXCLUDED.cluster_id, articles.cluster_id),
                            parent_id = COALESCE(EXCLUDED.parent_id, articles.parent_id),
                            article_mode = COALESCE(EXCLUDED.article_mode, articles.article_mode),
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
                        json.dumps(zep_facts) if zep_facts is not None else None,  # Preserve empty array []
                        target_keyword,
                        keyword_volume,
                        keyword_difficulty,
                        json.dumps(secondary_keywords) if secondary_keywords else None,
                        _content_story,
                        _content_guide,
                        _content_yolo,
                        json.dumps(_content_voices) if _content_voices else None,
                        cluster_id,
                        parent_id,
                        article_mode
                    ))
                    activity.logger.info(f"zep_facts for INSERT: {len(zep_facts) if zep_facts else 'None'} facts")
                    if _content_story:
                        activity.logger.info(f"Content modes: story={len(_content_story)} chars, guide={len(_content_guide or '')} chars, yolo={len(_content_yolo or '')} chars")
                    if cluster_id:
                        activity.logger.info(f"Cluster: id={cluster_id}, parent_id={parent_id}, mode={article_mode}")
                    if target_keyword:
                        activity.logger.info(f"SEO keyword: '{target_keyword}' (vol={keyword_volume}, diff={keyword_difficulty})")

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
async def update_article_four_act_content(
    article_id: str,
    four_act_content: List[Dict[str, Any]],
    video_prompt: Optional[str] = None
) -> bool:
    """
    Update article's four_act_content (video prompt briefs) in database.

    Called after generate_four_act_video_prompt_brief to store the briefs.
    Optionally also stores the assembled video_prompt for debugging.

    Args:
        article_id: Article ID
        four_act_content: List of 4 sections with video hints
        video_prompt: Optional assembled video prompt for Replicate

    Returns:
        Success boolean
    """
    activity.logger.info(f"Updating four_act_content for article {article_id}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                # Update payload with four_act_content, and optionally video_prompt
                # First get existing payload
                await cur.execute("""
                    SELECT payload FROM articles WHERE id = %s
                """, (article_id,))

                row = await cur.fetchone()
                if not row:
                    activity.logger.error(f"Article {article_id} not found")
                    return False

                payload = row[0] if row[0] else {}

                # Update payload with four_act_content
                payload["four_act_content"] = four_act_content

                # Optionally store the video_prompt for debugging
                if video_prompt:
                    payload["video_prompt"] = video_prompt

                # Update the payload column
                await cur.execute("""
                    UPDATE articles
                    SET
                        payload = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (json.dumps(payload), article_id))

                await conn.commit()

                activity.logger.info(f"✅ Updated four_act_content for article {article_id} ({len(four_act_content)} sections)")
                return True

    except Exception as e:
        activity.logger.error(f"Failed to update four_act_content: {e}")
        return False


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


@activity.defn
async def save_video_tags(
    video_playback_id: str,
    mux_asset_id: str,
    cluster_id: Optional[str] = None,
    article_id: Optional[int] = None,
    country: Optional[str] = None,
    article_mode: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Optional[int]:
    """
    Save video metadata to the video_tags table for queryability.

    This mirrors the MUX passthrough metadata and enables:
    - Querying videos by country, mode, or cluster
    - Building video galleries and collections
    - Analytics on video content

    Args:
        video_playback_id: MUX playback ID (required)
        mux_asset_id: MUX asset ID
        cluster_id: UUID grouping related videos
        article_id: Associated article ID
        country: Country name for the video
        article_mode: Content mode (story, guide, yolo, voices)
        tags: List of tags for categorization

    Returns:
        video_tags row ID or None if failed
    """
    activity.logger.info(f"Saving video tags for playback_id: {video_playback_id}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO video_tags (
                        video_playback_id,
                        mux_asset_id,
                        cluster_id,
                        article_id,
                        country,
                        article_mode,
                        tags,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    RETURNING id
                """, (
                    video_playback_id,
                    mux_asset_id,
                    cluster_id,
                    article_id,
                    country,
                    article_mode,
                    json.dumps(tags) if tags else '[]'
                ))

                result = await cur.fetchone()
                tag_id = result[0] if result else None

                await conn.commit()

                activity.logger.info(
                    f"Saved video tags: id={tag_id}, playback={video_playback_id}, "
                    f"country={country}, mode={article_mode}"
                )
                return tag_id

    except Exception as e:
        activity.logger.error(f"Failed to save video tags: {e}")
        return None


@activity.defn
async def get_videos_by_cluster(cluster_id: str) -> List[Dict[str, Any]]:
    """
    Get all videos in a cluster.

    Args:
        cluster_id: Cluster UUID

    Returns:
        List of video_tags records
    """
    activity.logger.info(f"Fetching videos for cluster: {cluster_id}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT
                        id,
                        video_playback_id,
                        mux_asset_id,
                        cluster_id,
                        article_id,
                        country,
                        article_mode,
                        tags,
                        created_at
                    FROM video_tags
                    WHERE cluster_id = %s
                    ORDER BY created_at ASC
                """, (cluster_id,))

                rows = await cur.fetchall()

                return [
                    {
                        "id": row[0],
                        "video_playback_id": row[1],
                        "mux_asset_id": row[2],
                        "cluster_id": str(row[3]) if row[3] else None,
                        "article_id": row[4],
                        "country": row[5],
                        "article_mode": row[6],
                        "tags": row[7] if row[7] else [],
                        "created_at": row[8].isoformat() if row[8] else None
                    }
                    for row in rows
                ]

    except Exception as e:
        activity.logger.error(f"Failed to fetch videos by cluster: {e}")
        return []


@activity.defn
async def get_videos_by_country(country: str) -> List[Dict[str, Any]]:
    """
    Get all videos for a country.

    Args:
        country: Country name

    Returns:
        List of video_tags records
    """
    activity.logger.info(f"Fetching videos for country: {country}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT
                        id,
                        video_playback_id,
                        mux_asset_id,
                        cluster_id,
                        article_id,
                        country,
                        article_mode,
                        tags,
                        created_at
                    FROM video_tags
                    WHERE LOWER(country) = LOWER(%s)
                    ORDER BY created_at DESC
                """, (country,))

                rows = await cur.fetchall()

                return [
                    {
                        "id": row[0],
                        "video_playback_id": row[1],
                        "mux_asset_id": row[2],
                        "cluster_id": str(row[3]) if row[3] else None,
                        "article_id": row[4],
                        "country": row[5],
                        "article_mode": row[6],
                        "tags": row[7] if row[7] else [],
                        "created_at": row[8].isoformat() if row[8] else None
                    }
                    for row in rows
                ]

    except Exception as e:
        activity.logger.error(f"Failed to fetch videos by country: {e}")
        return []


@activity.defn(name="inherit_parent_video_to_children")
async def inherit_parent_video_to_children(
    parent_id: int
) -> Dict[str, Any]:
    """
    Copy parent article's video_playback_id to all child topic cluster articles.

    Topic cluster articles don't generate their own videos - they inherit
    from the parent (Story) article for thumbnail display.

    Args:
        parent_id: ID of the parent article (Story mode)

    Returns:
        Dict with updated_count and video_playback_id used
    """
    activity.logger.info(f"Inheriting video from parent {parent_id} to children")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                # Get parent's video
                await cur.execute("""
                    SELECT video_playback_id FROM articles WHERE id = %s
                """, (parent_id,))

                parent = await cur.fetchone()
                if not parent or not parent[0]:
                    activity.logger.warning(f"Parent {parent_id} has no video_playback_id")
                    return {"updated_count": 0, "video_playback_id": None}

                parent_video = parent[0]

                # Update all children that don't have their own video
                await cur.execute("""
                    UPDATE articles
                    SET video_playback_id = %s
                    WHERE parent_id = %s
                      AND (video_playback_id IS NULL OR video_playback_id = '')
                    RETURNING id
                """, (parent_video, parent_id))

                updated = await cur.fetchall()
                updated_count = len(updated)

                await conn.commit()

                activity.logger.info(f"Updated {updated_count} children with video {parent_video[:20]}...")
                return {
                    "updated_count": updated_count,
                    "video_playback_id": parent_video
                }

    except Exception as e:
        activity.logger.error(f"Failed to inherit video to children: {e}")
        return {"updated_count": 0, "error": str(e)}


@activity.defn(name="get_cluster_videos")
async def get_cluster_videos(
    cluster_id: str
) -> Dict[str, Any]:
    """
    Get all videos from a cluster for hub section assignment.

    Returns video_playback_ids organized by article_mode, ready for
    hub template to assign to different sections.

    Args:
        cluster_id: UUID of the cluster

    Returns:
        Dict with videos by mode and recommended section assignments
    """
    activity.logger.info(f"Getting cluster videos for {cluster_id}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT article_mode, video_playback_id, title, slug
                    FROM articles
                    WHERE cluster_id = %s
                      AND video_playback_id IS NOT NULL
                      AND article_mode IN ('story', 'guide', 'yolo', 'voices')
                    ORDER BY article_mode
                """, (cluster_id,))

                rows = await cur.fetchall()

                videos_by_mode = {}
                for row in rows:
                    mode = row[0]
                    videos_by_mode[mode] = {
                        "video_playback_id": row[1],
                        "title": row[2],
                        "slug": row[3]
                    }

                # Recommended section assignments for hub template
                section_videos = {
                    "hero": videos_by_mode.get("story", {}).get("video_playback_id"),
                    "intro_background": videos_by_mode.get("yolo", {}).get("video_playback_id"),
                    "practical_section": videos_by_mode.get("guide", {}).get("video_playback_id"),
                    "lifestyle_section": videos_by_mode.get("yolo", {}).get("video_playback_id"),
                    "voices_section": videos_by_mode.get("voices", {}).get("video_playback_id"),
                    "cta_background": videos_by_mode.get("story", {}).get("video_playback_id"),
                }

                activity.logger.info(f"Found {len(videos_by_mode)} cluster videos")
                return {
                    "videos_by_mode": videos_by_mode,
                    "section_videos": section_videos,
                    "primary_video": videos_by_mode.get("story", {}).get("video_playback_id")
                }

    except Exception as e:
        activity.logger.error(f"Failed to get cluster videos: {e}")
        return {"videos_by_mode": {}, "section_videos": {}, "primary_video": None}


@activity.defn(name="get_cluster_story_video")
async def get_cluster_story_video(cluster_id: str) -> Dict[str, Any]:
    """
    Get the Story mode video from a cluster for reuse by other modes.

    Used by video cost optimization: Guide, Voices, and Nomad modes
    reuse the Story video instead of generating their own (60% savings).

    Args:
        cluster_id: UUID of the cluster

    Returns:
        Dict with video_playback_id and video_asset_id, or empty dict if not found
    """
    activity.logger.info(f"Getting Story video from cluster {cluster_id}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT video_playback_id, video_asset_id
                    FROM articles
                    WHERE cluster_id = %s
                      AND article_mode = 'story'
                      AND video_playback_id IS NOT NULL
                    LIMIT 1
                """, (cluster_id,))

                row = await cur.fetchone()

                if row:
                    return {
                        "video_playback_id": row[0],
                        "video_asset_id": row[1]
                    }
                else:
                    activity.logger.warning(f"No Story video found in cluster {cluster_id}")
                    return {}

    except Exception as e:
        activity.logger.error(f"Failed to get Story video: {e}")
        return {}


@activity.defn(name="get_cluster_videos_with_topics")
async def get_cluster_videos_with_topics(
    cluster_id: str
) -> Dict[str, Any]:
    """
    Get all videos from a cluster with their topic metadata.

    Returns video_playback_ids with topics and descriptions for
    intelligent section-to-video matching in hub creation.

    Args:
        cluster_id: UUID of the cluster

    Returns:
        Dict with videos_by_mode (including topics) and topic_index for matching
    """
    activity.logger.info(f"Getting cluster videos with topics for {cluster_id}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT article_mode, video_playback_id, title, slug,
                           video_topics, video_description
                    FROM articles
                    WHERE cluster_id = %s
                      AND video_playback_id IS NOT NULL
                      AND article_mode IN ('story', 'guide', 'yolo', 'voices')
                    ORDER BY article_mode
                """, (cluster_id,))

                rows = await cur.fetchall()

                videos_by_mode = {}
                topic_index = {}  # topic -> video_playback_id mapping

                for row in rows:
                    mode = row[0]
                    video_id = row[1]
                    topics = row[4] if row[4] else []

                    videos_by_mode[mode] = {
                        "video_playback_id": video_id,
                        "title": row[2],
                        "slug": row[3],
                        "topics": topics,
                        "description": row[5]
                    }

                    # Build reverse index: topic -> video
                    for topic in topics:
                        if topic not in topic_index:
                            topic_index[topic] = []
                        topic_index[topic].append({
                            "mode": mode,
                            "video_playback_id": video_id
                        })

                # Smart section assignments based on topics
                section_videos = {
                    "hero": videos_by_mode.get("story", {}).get("video_playback_id"),
                    "introduction": videos_by_mode.get("story", {}).get("video_playback_id"),
                    "practical_guide": videos_by_mode.get("guide", {}).get("video_playback_id"),
                    "visa_section": videos_by_mode.get("guide", {}).get("video_playback_id"),
                    "lifestyle": videos_by_mode.get("yolo", {}).get("video_playback_id"),
                    "adventure": videos_by_mode.get("yolo", {}).get("video_playback_id"),
                    "community": videos_by_mode.get("voices", {}).get("video_playback_id"),
                    "expat_stories": videos_by_mode.get("voices", {}).get("video_playback_id"),
                    "cta": videos_by_mode.get("story", {}).get("video_playback_id"),
                }

                activity.logger.info(
                    f"Found {len(videos_by_mode)} videos with {len(topic_index)} unique topics"
                )

                return {
                    "videos_by_mode": videos_by_mode,
                    "section_videos": section_videos,
                    "topic_index": topic_index,
                    "primary_video": videos_by_mode.get("story", {}).get("video_playback_id")
                }

    except Exception as e:
        activity.logger.error(f"Failed to get cluster videos with topics: {e}")
        return {"videos_by_mode": {}, "section_videos": {}, "topic_index": {}, "primary_video": None}


@activity.defn(name="match_video_to_section")
async def match_video_to_section(
    section_keywords: list,
    cluster_id: str
) -> Optional[Dict[str, Any]]:
    """
    Find the best matching video for a content section based on keywords.

    Args:
        section_keywords: Keywords describing the section (e.g., ["visa", "permits", "legal"])
        cluster_id: UUID of the cluster to search in

    Returns:
        Dict with best matching video or None
    """
    activity.logger.info(f"Matching video for keywords: {section_keywords}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                # Find videos with overlapping topics
                await cur.execute("""
                    SELECT article_mode, video_playback_id, video_topics, video_description,
                           (SELECT COUNT(*) FROM jsonb_array_elements_text(video_topics) t
                            WHERE t = ANY(%s)) as match_count
                    FROM articles
                    WHERE cluster_id = %s
                      AND video_playback_id IS NOT NULL
                      AND article_mode IN ('story', 'guide', 'yolo', 'voices')
                    ORDER BY match_count DESC
                    LIMIT 1
                """, (section_keywords, cluster_id))

                row = await cur.fetchone()

                if row and row[4] > 0:  # Has at least one matching topic
                    return {
                        "mode": row[0],
                        "video_playback_id": row[1],
                        "topics": row[2],
                        "description": row[3],
                        "match_count": row[4]
                    }

                # Fallback to story video if no match
                await cur.execute("""
                    SELECT video_playback_id FROM articles
                    WHERE cluster_id = %s AND article_mode = 'story'
                    LIMIT 1
                """, (cluster_id,))
                fallback = await cur.fetchone()

                if fallback:
                    return {
                        "mode": "story",
                        "video_playback_id": fallback[0],
                        "topics": [],
                        "description": "Fallback to story video",
                        "match_count": 0
                    }

                return None

    except Exception as e:
        activity.logger.error(f"Failed to match video to section: {e}")
        return None


@activity.defn(name="finesse_cluster_media")
async def finesse_cluster_media(
    cluster_id: str
) -> Dict[str, Any]:
    """
    Comprehensive video/media finessing for a cluster.

    This runs at the end of the workflow to ensure:
    1. All core articles (story/guide/yolo/voices) have videos
    2. Topic cluster articles inherit appropriate videos
    3. Hub has video_playback_id set
    4. Every article has a displayable thumbnail

    Args:
        cluster_id: UUID of the cluster to finesse

    Returns:
        Dict with finessing stats and what was updated
    """
    activity.logger.info(f"Finessing media for cluster {cluster_id}")

    stats = {
        "core_articles_checked": 0,
        "topic_articles_updated": 0,
        "hub_updated": False,
        "videos_propagated": [],
        "errors": []
    }

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                # 1. Get all core cluster articles with videos
                await cur.execute("""
                    SELECT id, article_mode, video_playback_id, title, is_primary
                    FROM articles
                    WHERE cluster_id = %s
                      AND article_mode IN ('story', 'guide', 'yolo', 'voices')
                      AND app = 'relocation'
                    ORDER BY
                      CASE article_mode
                        WHEN 'story' THEN 1
                        WHEN 'guide' THEN 2
                        WHEN 'yolo' THEN 3
                        WHEN 'voices' THEN 4
                      END
                """, (cluster_id,))

                core_articles = await cur.fetchall()
                stats["core_articles_checked"] = len(core_articles)

                # Build video lookup by mode
                videos_by_mode = {}
                primary_article_id = None
                for row in core_articles:
                    article_id, mode, video_id, title, is_primary = row
                    if video_id:
                        videos_by_mode[mode] = {
                            "id": article_id,
                            "video_playback_id": video_id,
                            "title": title
                        }
                    if is_primary:
                        primary_article_id = article_id

                # Determine primary video (story > guide > yolo > voices)
                primary_video = (
                    videos_by_mode.get("story", {}).get("video_playback_id") or
                    videos_by_mode.get("guide", {}).get("video_playback_id") or
                    videos_by_mode.get("yolo", {}).get("video_playback_id") or
                    videos_by_mode.get("voices", {}).get("video_playback_id")
                )

                if not primary_video:
                    activity.logger.warning(f"No videos found in cluster {cluster_id}")
                    return stats

                # 1.5. VIDEO OPTIMIZATION: Explicitly map non-video modes to Story video
                # Guide, Voices, Nomad should always use Story video (cost savings)
                VIDEO_FALLBACK_MAP = {
                    "guide": "story",
                    "voices": "story",
                    "nomad": "story"
                }

                story_video = videos_by_mode.get("story", {}).get("video_playback_id")
                if story_video:
                    for mode, fallback in VIDEO_FALLBACK_MAP.items():
                        # If this mode doesn't have a video, assign Story video
                        if mode not in videos_by_mode and fallback == "story":
                            await cur.execute("""
                                UPDATE articles
                                SET video_playback_id = %s,
                                    video_asset_id = (
                                        SELECT video_asset_id FROM articles
                                        WHERE cluster_id = %s AND article_mode = 'story'
                                        LIMIT 1
                                    )
                                WHERE cluster_id = %s
                                  AND article_mode = %s
                                  AND (video_playback_id IS NULL OR video_playback_id = '')
                                RETURNING id
                            """, (story_video, cluster_id, cluster_id, mode))

                            updated = await cur.fetchone()
                            if updated:
                                activity.logger.info(f"Assigned Story video to {mode} mode (optimization)")
                                stats["videos_propagated"].append({
                                    "target": f"{mode}_mode",
                                    "video": story_video[:20] + "..."
                                })

                # 2. Update hub video if missing
                await cur.execute("""
                    UPDATE country_hubs
                    SET video_playback_id = %s
                    WHERE cluster_id = %s
                      AND (video_playback_id IS NULL OR video_playback_id = '')
                    RETURNING id
                """, (primary_video, cluster_id))

                hub_updated = await cur.fetchone()
                if hub_updated:
                    stats["hub_updated"] = True
                    stats["videos_propagated"].append({
                        "target": "hub",
                        "video": primary_video[:20] + "..."
                    })

                # 3. Update topic cluster articles (children of primary)
                if primary_article_id:
                    await cur.execute("""
                        UPDATE articles
                        SET video_playback_id = %s
                        WHERE parent_id = %s
                          AND (video_playback_id IS NULL OR video_playback_id = '')
                        RETURNING id, title
                    """, (primary_video, primary_article_id))

                    updated_topics = await cur.fetchall()
                    stats["topic_articles_updated"] = len(updated_topics)

                    for topic in updated_topics:
                        stats["videos_propagated"].append({
                            "target": f"topic:{topic[0]}",
                            "title": topic[1][:30] + "..." if len(topic[1]) > 30 else topic[1]
                        })

                # 4. Cross-pollinate: articles without videos get closest match
                await cur.execute("""
                    UPDATE articles a
                    SET video_playback_id = %s
                    WHERE a.cluster_id = %s
                      AND a.app = 'relocation'
                      AND (a.video_playback_id IS NULL OR a.video_playback_id = '')
                    RETURNING id
                """, (primary_video, cluster_id))

                additional = await cur.fetchall()
                if additional:
                    stats["videos_propagated"].append({
                        "target": "additional_articles",
                        "count": len(additional)
                    })

                await conn.commit()

                activity.logger.info(
                    f"Finessed cluster {cluster_id}: "
                    f"{stats['core_articles_checked']} core, "
                    f"{stats['topic_articles_updated']} topics updated, "
                    f"hub={'yes' if stats['hub_updated'] else 'no'}"
                )

                return stats

    except Exception as e:
        activity.logger.error(f"Failed to finesse cluster media: {e}")
        stats["errors"].append(str(e))
        return stats


@activity.defn(name="finesse_all_cluster_media")
async def finesse_all_cluster_media() -> Dict[str, Any]:
    """
    Run media finessing across all clusters that have videos.

    Use this for a one-time cleanup or scheduled maintenance job.

    Returns:
        Dict with total stats across all clusters
    """
    activity.logger.info("Running media finessing across all clusters")

    total_stats = {
        "clusters_processed": 0,
        "total_topics_updated": 0,
        "hubs_updated": 0,
        "clusters_with_errors": []
    }

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                # Get all clusters that have at least one video
                await cur.execute("""
                    SELECT DISTINCT cluster_id
                    FROM articles
                    WHERE cluster_id IS NOT NULL
                      AND video_playback_id IS NOT NULL
                      AND app = 'relocation'
                """)

                clusters = await cur.fetchall()

        # Process each cluster
        for (cluster_id,) in clusters:
            result = await finesse_cluster_media(cluster_id)
            total_stats["clusters_processed"] += 1
            total_stats["total_topics_updated"] += result.get("topic_articles_updated", 0)
            if result.get("hub_updated"):
                total_stats["hubs_updated"] += 1
            if result.get("errors"):
                total_stats["clusters_with_errors"].append(cluster_id)

        activity.logger.info(
            f"Finessed {total_stats['clusters_processed']} clusters, "
            f"updated {total_stats['total_topics_updated']} topic articles, "
            f"{total_stats['hubs_updated']} hubs"
        )

        return total_stats

    except Exception as e:
        activity.logger.error(f"Failed to finesse all clusters: {e}")
        return {"error": str(e)}
