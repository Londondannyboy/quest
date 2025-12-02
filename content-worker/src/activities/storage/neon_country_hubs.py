"""
Neon PostgreSQL Database Activities for Country Hubs.

CRUD operations for SEO-optimized hub pages that aggregate
all cluster content for a country or city.

Hub pages are:
- Separate entities from countries and articles
- Aggregated content from all cluster modes (Story/Guide/YOLO/Voices)
- SEO slugs up to 10 words
- Self-contained pillar pages with UPSERT capability
"""

from __future__ import annotations

import psycopg
import json
from temporalio import activity
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.utils.config import config
from src.utils.seo_slug import (
    generate_seo_slug,
    generate_hub_title,
    generate_meta_description,
    validate_seo_slug,
)


@activity.defn(name="generate_hub_seo_slug")
async def generate_hub_seo_slug(
    location_name: str,
    seo_keywords: Dict[str, Any],
    location_type: str = "country"
) -> Dict[str, Any]:
    """
    Generate an SEO-optimized slug for a hub page.

    Uses DataForSEO keywords to create a keyword-rich slug
    up to 10 words.

    Args:
        location_name: Country or city name (e.g., "Cyprus")
        seo_keywords: DataForSEO research results
        location_type: "country" or "city"

    Returns:
        Dict with slug, title, meta_description, seo_metadata
    """
    activity.logger.info(f"Generating SEO slug for hub: {location_name}")

    # Generate the slug
    slug, seo_metadata = generate_seo_slug(
        location_name=location_name,
        seo_keywords=seo_keywords,
        max_words=10,
        location_type=location_type
    )

    # Validate
    is_valid, message, score = validate_seo_slug(slug)
    activity.logger.info(f"Slug '{slug}' - valid: {is_valid}, score: {score}, message: {message}")

    # Generate title and meta description
    keyword_terms = seo_metadata.get("selected_keywords", [])
    # Extract just the terms for title/description
    terms_for_title = []
    for kw in keyword_terms[:3]:
        if kw:
            # Remove location name and clean
            clean_term = kw.lower().replace(location_name.lower(), "").strip()
            if clean_term:
                terms_for_title.append(clean_term)

    title = generate_hub_title(location_name, keyword_terms=terms_for_title)
    meta_description = generate_meta_description(
        location_name, keyword_terms=terms_for_title, location_type=location_type
    )

    return {
        "slug": slug,
        "title": title,
        "meta_description": meta_description,
        "seo_metadata": seo_metadata,
        "validation": {
            "is_valid": is_valid,
            "score": score,
            "message": message
        }
    }


@activity.defn(name="aggregate_cluster_to_hub_payload")
async def aggregate_cluster_to_hub_payload(
    location_name: str,
    country_code: str,
    cluster_articles: List[Dict[str, Any]],
    country_facts: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Aggregate all cluster articles into a hub payload.

    Combines content from Story, Guide, YOLO, and Voices modes
    into a comprehensive hub page payload.

    Args:
        location_name: Country or city name
        country_code: ISO 3166-1 alpha-2 code
        cluster_articles: List of cluster article data
        country_facts: Country facts JSONB from countries table

    Returns:
        Hub payload dict ready for storage
    """
    activity.logger.info(f"Aggregating {len(cluster_articles)} cluster articles for {location_name} hub")

    # Initialize payload structure
    payload = {
        "location_name": location_name,
        "country_code": country_code,
        "aggregated_at": datetime.utcnow().isoformat(),

        # Quick stats bar (extracted from facts)
        "quick_stats": {},

        # Cluster navigation
        "cluster_articles": [],

        # Embedded content sections (full content for each mode)
        "embedded_sections": {},

        # Aggregated FAQ (combined from all articles)
        "faq_aggregated": [],

        # Aggregated sources/references
        "sources_aggregated": [],

        # Voices/testimonials
        "voices": [],
    }

    # Process each cluster article
    for article in cluster_articles:
        mode = article.get("article_mode", article.get("mode", "unknown"))

        # Add to cluster navigation
        payload["cluster_articles"].append({
            "article_id": article.get("article_id"),
            "slug": article.get("slug"),
            "mode": mode,
            "title": article.get("title"),
            "excerpt": article.get("excerpt", ""),
            "video_playback_id": article.get("video_playback_id"),
        })

        # Extract content for embedded sections
        content = article.get("content", "")
        if content and mode != "unknown":
            payload["embedded_sections"][mode] = {
                "content": content,
                "word_count": len(content.split()) if content else 0,
            }

        # Extract FAQ from article payload
        article_payload = article.get("payload", {})
        if isinstance(article_payload, dict):
            faq = article_payload.get("faq", [])
            if faq:
                for item in faq:
                    if item not in payload["faq_aggregated"]:
                        payload["faq_aggregated"].append(item)

            # Extract sources
            sources = article_payload.get("sources", [])
            if sources:
                for src in sources:
                    if src not in payload["sources_aggregated"]:
                        payload["sources_aggregated"].append(src)

            # Extract voices
            voices = article_payload.get("voices", [])
            if not voices:
                voices = article_payload.get("content_voices", [])
            if voices:
                for voice in voices:
                    if voice not in payload["voices"]:
                        payload["voices"].append(voice)

    # Build quick stats from country facts
    if country_facts:
        payload["quick_stats"] = {
            "cost_of_living": country_facts.get("cost_of_living", {}),
            "visa_types": country_facts.get("visa_types", []),
            "tax_rates": country_facts.get("tax_rates", {}),
            "climate": country_facts.get("climate", ""),
            "language": country_facts.get("language", ""),
            "currency": country_facts.get("currency", ""),
            "timezone": country_facts.get("timezone", ""),
        }

    activity.logger.info(
        f"Hub payload aggregated: {len(payload['cluster_articles'])} articles, "
        f"{len(payload['embedded_sections'])} sections, "
        f"{len(payload['faq_aggregated'])} FAQ items, "
        f"{len(payload['voices'])} voices"
    )

    return payload


@activity.defn(name="save_or_update_country_hub")
async def save_or_update_country_hub(
    country_code: str,
    location_name: str,
    cluster_id: str,
    slug: str,
    title: str,
    meta_description: str,
    hub_content: str,
    payload: Dict[str, Any],
    seo_data: Dict[str, Any],
    primary_keyword: Optional[str] = None,
    keyword_volume: Optional[int] = None,
    keyword_difficulty: Optional[int] = None,
    video_playback_id: Optional[str] = None,
    location_type: str = "country"
) -> Dict[str, Any]:
    """
    Save or update a country hub (UPSERT).

    If hub exists for country_code, updates it with new data.
    If not, creates a new hub.

    Args:
        country_code: ISO 3166-1 alpha-2 code
        location_name: Country or city name
        cluster_id: UUID linking to article cluster
        slug: SEO-optimized slug
        title: Hub page title
        meta_description: SEO meta description
        hub_content: Full HTML content
        payload: Aggregated data payload
        seo_data: SEO keywords and metadata
        primary_keyword: Main targeting keyword
        keyword_volume: Monthly search volume
        keyword_difficulty: Keyword difficulty score
        video_playback_id: Mux playback ID for hero video
        location_type: "country" or "city"

    Returns:
        Dict with hub_id, slug, created (bool), updated_at
    """
    activity.logger.info(f"Saving/updating hub for {location_name} ({country_code})")

    # Legacy slug for redirects
    legacy_slug = f"guides/{location_name.lower().replace(' ', '-')}"

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                # Check if hub exists for this country
                await cur.execute("""
                    SELECT id, slug FROM country_hubs WHERE country_code = %s
                """, (country_code.upper(),))

                existing = await cur.fetchone()

                if existing:
                    # UPDATE existing hub
                    hub_id = existing[0]
                    old_slug = existing[1]

                    await cur.execute("""
                        UPDATE country_hubs
                        SET
                            location_name = %s,
                            cluster_id = %s,
                            location_type = %s,
                            slug = %s,
                            legacy_slug = COALESCE(legacy_slug, %s),
                            title = %s,
                            meta_description = %s,
                            hub_content = %s,
                            payload = %s,
                            seo_data = %s,
                            primary_keyword = COALESCE(%s, primary_keyword),
                            keyword_volume = COALESCE(%s, keyword_volume),
                            keyword_difficulty = COALESCE(%s, keyword_difficulty),
                            video_playback_id = COALESCE(%s, video_playback_id),
                            updated_at = NOW()
                        WHERE country_code = %s
                    """, (
                        location_name,
                        cluster_id,
                        location_type,
                        slug,
                        legacy_slug,
                        title,
                        meta_description,
                        hub_content,
                        json.dumps(payload),
                        json.dumps(seo_data),
                        primary_keyword,
                        keyword_volume,
                        keyword_difficulty,
                        video_playback_id,
                        country_code.upper()
                    ))

                    await conn.commit()

                    activity.logger.info(f"Updated hub: {slug} (ID: {hub_id})")
                    return {
                        "hub_id": hub_id,
                        "slug": slug,
                        "old_slug": old_slug,
                        "created": False,
                        "updated_at": datetime.utcnow().isoformat()
                    }

                else:
                    # INSERT new hub
                    await cur.execute("""
                        INSERT INTO country_hubs (
                            country_code,
                            location_name,
                            cluster_id,
                            location_type,
                            slug,
                            legacy_slug,
                            title,
                            meta_description,
                            hub_content,
                            payload,
                            seo_data,
                            primary_keyword,
                            keyword_volume,
                            keyword_difficulty,
                            video_playback_id,
                            status,
                            created_at,
                            updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        RETURNING id
                    """, (
                        country_code.upper(),
                        location_name,
                        cluster_id,
                        location_type,
                        slug,
                        legacy_slug,
                        title,
                        meta_description,
                        hub_content,
                        json.dumps(payload),
                        json.dumps(seo_data),
                        primary_keyword,
                        keyword_volume,
                        keyword_difficulty,
                        video_playback_id,
                        "draft"
                    ))

                    result = await cur.fetchone()
                    hub_id = result[0]

                    await conn.commit()

                    activity.logger.info(f"Created hub: {slug} (ID: {hub_id})")
                    return {
                        "hub_id": hub_id,
                        "slug": slug,
                        "created": True,
                        "updated_at": datetime.utcnow().isoformat()
                    }

    except Exception as e:
        activity.logger.error(f"Failed to save/update hub: {e}")
        raise


@activity.defn(name="get_country_hub")
async def get_country_hub(
    country_code: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieve a country hub by country code.

    Args:
        country_code: ISO 3166-1 alpha-2 code

    Returns:
        Hub data dict or None if not found
    """
    activity.logger.info(f"Fetching hub for: {country_code}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT
                        id, country_code, location_name, cluster_id,
                        location_type, slug, legacy_slug, title,
                        meta_description, hub_content, payload, seo_data,
                        primary_keyword, keyword_volume, keyword_difficulty,
                        video_playback_id, video_thumbnail_url,
                        status, published_at, created_at, updated_at
                    FROM country_hubs
                    WHERE country_code = %s
                """, (country_code.upper(),))

                row = await cur.fetchone()

                if not row:
                    return None

                return {
                    "hub_id": row[0],
                    "country_code": row[1],
                    "location_name": row[2],
                    "cluster_id": str(row[3]) if row[3] else None,
                    "location_type": row[4],
                    "slug": row[5],
                    "legacy_slug": row[6],
                    "title": row[7],
                    "meta_description": row[8],
                    "hub_content": row[9],
                    "payload": row[10],
                    "seo_data": row[11],
                    "primary_keyword": row[12],
                    "keyword_volume": row[13],
                    "keyword_difficulty": row[14],
                    "video_playback_id": row[15],
                    "video_thumbnail_url": row[16],
                    "status": row[17],
                    "published_at": row[18].isoformat() if row[18] else None,
                    "created_at": row[19].isoformat() if row[19] else None,
                    "updated_at": row[20].isoformat() if row[20] else None,
                }

    except Exception as e:
        activity.logger.error(f"Failed to fetch hub: {e}")
        return None


@activity.defn(name="get_hub_by_slug")
async def get_hub_by_slug(
    slug: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieve a country hub by slug (for routing).

    Also checks legacy_slug for redirects.

    Args:
        slug: SEO slug or legacy slug

    Returns:
        Hub data dict or None if not found
    """
    activity.logger.info(f"Fetching hub by slug: {slug}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                # Check both slug and legacy_slug
                await cur.execute("""
                    SELECT
                        id, country_code, location_name, cluster_id,
                        location_type, slug, legacy_slug, title,
                        meta_description, hub_content, payload, seo_data,
                        primary_keyword, keyword_volume,
                        video_playback_id, status
                    FROM country_hubs
                    WHERE slug = %s OR legacy_slug = %s
                """, (slug, slug))

                row = await cur.fetchone()

                if not row:
                    return None

                is_redirect = row[6] == slug  # legacy_slug matches

                return {
                    "hub_id": row[0],
                    "country_code": row[1],
                    "location_name": row[2],
                    "cluster_id": str(row[3]) if row[3] else None,
                    "location_type": row[4],
                    "slug": row[5],
                    "legacy_slug": row[6],
                    "title": row[7],
                    "meta_description": row[8],
                    "hub_content": row[9],
                    "payload": row[10],
                    "seo_data": row[11],
                    "primary_keyword": row[12],
                    "keyword_volume": row[13],
                    "video_playback_id": row[14],
                    "status": row[15],
                    "is_redirect": is_redirect,  # True if matched on legacy_slug
                    "redirect_to": row[5] if is_redirect else None,
                }

    except Exception as e:
        activity.logger.error(f"Failed to fetch hub by slug: {e}")
        return None


@activity.defn(name="publish_country_hub")
async def publish_country_hub(
    country_code: str
) -> bool:
    """
    Publish a country hub (set status to 'published').

    Args:
        country_code: ISO 3166-1 alpha-2 code

    Returns:
        Success boolean
    """
    activity.logger.info(f"Publishing hub for: {country_code}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE country_hubs
                    SET
                        status = 'published',
                        published_at = NOW(),
                        updated_at = NOW()
                    WHERE country_code = %s
                """, (country_code.upper(),))

                await conn.commit()

                activity.logger.info(f"Published hub for {country_code}")
                return True

    except Exception as e:
        activity.logger.error(f"Failed to publish hub: {e}")
        return False


@activity.defn(name="generate_hub_content")
async def generate_hub_content(
    location_name: str,
    payload: Dict[str, Any],
    style: str = "conde_nast"
) -> str:
    """
    Generate full HTML content for a hub page.

    Combines embedded sections into a cohesive pillar page
    with Conde Nast styling.

    Args:
        location_name: Country or city name
        payload: Hub payload with embedded_sections
        style: Template style ("conde_nast", "minimal", etc.)

    Returns:
        Full HTML content string
    """
    activity.logger.info(f"Generating hub content for {location_name} (style: {style})")

    embedded = payload.get("embedded_sections", {})
    quick_stats = payload.get("quick_stats", {})
    faq = payload.get("faq_aggregated", [])
    voices = payload.get("voices", [])
    sources = payload.get("sources_aggregated", [])

    # Build content sections
    sections = []

    # Introduction (from story mode)
    if "story" in embedded:
        story_content = embedded["story"].get("content", "")
        # Extract first few paragraphs as intro
        paragraphs = story_content.split("\n\n")[:3]
        intro = "\n\n".join(paragraphs)
        sections.append(f"## Why {location_name}?\n\n{intro}")

    # Quick Stats section
    if quick_stats:
        stats_md = f"## {location_name} at a Glance\n\n"
        if quick_stats.get("cost_of_living"):
            col = quick_stats["cost_of_living"]
            if isinstance(col, dict):
                stats_md += f"- **Monthly Cost of Living:** ${col.get('monthly_estimate', 'N/A')}\n"
        if quick_stats.get("visa_types"):
            stats_md += f"- **Visa Options:** {', '.join(quick_stats['visa_types'][:3])}\n"
        if quick_stats.get("language"):
            stats_md += f"- **Language:** {quick_stats['language']}\n"
        if quick_stats.get("timezone"):
            stats_md += f"- **Timezone:** {quick_stats['timezone']}\n"
        sections.append(stats_md)

    # Practical Guide section (from guide mode)
    if "guide" in embedded:
        guide_content = embedded["guide"].get("content", "")
        sections.append(f"## The Practical Guide\n\n{guide_content}")

    # YOLO Adventure section
    if "yolo" in embedded:
        yolo_content = embedded["yolo"].get("content", "")
        sections.append(f"## The Adventure Awaits\n\n{yolo_content}")

    # Voices section
    if "voices" in embedded:
        voices_content = embedded["voices"].get("content", "")
        sections.append(f"## Real Voices from {location_name}\n\n{voices_content}")
    elif voices:
        # Use aggregated voices
        voices_md = f"## What Expats Say About {location_name}\n\n"
        for i, voice in enumerate(voices[:5]):
            if isinstance(voice, dict):
                quote = voice.get("quote", voice.get("text", ""))
                author = voice.get("author", voice.get("username", "Expat"))
                source = voice.get("source", "")
                voices_md += f"> \"{quote}\"\n> — {author}"
                if source:
                    voices_md += f" ({source})"
                voices_md += "\n\n"
            elif isinstance(voice, str):
                voices_md += f"> {voice}\n\n"
        sections.append(voices_md)

    # Topic Clusters section (SEO-targeted articles)
    topic_articles = [
        article for article in embedded.values()
        if isinstance(article, dict) and article.get("mode") == "topic"
    ]
    if not topic_articles and payload.get("cluster_articles"):
        # Extract from cluster_articles if not in embedded
        topic_articles = [
            article for article in payload["cluster_articles"]
            if article.get("mode") == "topic"
        ]

    if topic_articles:
        topic_md = f"## Essential Guides for {location_name}\n\n"
        topic_md += f"Explore our in-depth guides covering specific topics about relocating to {location_name}:\n\n"

        # Group by planning_type
        by_type = {}
        for article in topic_articles:
            p_type = "General"
            if isinstance(article, dict):
                payload_data = article.get("payload", {})
                p_type = payload_data.get("planning_type", "general").title()
            by_type.setdefault(p_type, []).append(article)

        # Display by category
        for category, articles in sorted(by_type.items()):
            topic_md += f"### {category}\n\n"
            for article in articles[:5]:  # Max 5 per category
                if isinstance(article, dict):
                    title = article.get("title", "")
                    slug = article.get("slug", "")
                    excerpt = article.get("excerpt", "")
                    video = article.get("video_playback_id", "")

                    if slug and title:
                        topic_md += f"- **[{title}](/{slug})**"
                        if excerpt:
                            topic_md += f" - {excerpt}"
                        topic_md += "\n"

            topic_md += "\n"

        sections.append(topic_md)

    # FAQ section
    if faq:
        faq_md = f"## Frequently Asked Questions\n\n"
        for item in faq[:10]:
            if isinstance(item, dict):
                q = item.get("question", item.get("q", ""))
                a = item.get("answer", item.get("a", ""))
                if q and a:
                    faq_md += f"### {q}\n\n{a}\n\n"
        sections.append(faq_md)

    # Sources section
    if sources:
        sources_md = "## Sources & References\n\n"
        for src in sources[:12]:
            if isinstance(src, dict):
                title = src.get("title", src.get("name", "Source"))
                url = src.get("url", src.get("link", ""))
                if url:
                    sources_md += f"- [{title}]({url})\n"
            elif isinstance(src, str):
                sources_md += f"- {src}\n"
        sections.append(sources_md)

    # Combine all sections
    full_content = "\n\n---\n\n".join(sections)

    # Inject section images into hub content if video exists
    hub_video_playback_id = payload.get("video_playback_id")
    if hub_video_playback_id and full_content:
        activity.logger.info("Injecting section images into hub content...")
        from src.utils.inject_section_images import inject_section_images

        full_content = inject_section_images(
            full_content,
            hub_video_playback_id,
            image_width=1200,
            max_sections=None  # Unlimited - inject for ALL H2 sections
        )
        activity.logger.info("Section images injected to hub")

    activity.logger.info(f"Generated hub content: {len(full_content)} chars, {len(sections)} sections")

    return full_content
