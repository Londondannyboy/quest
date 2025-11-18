"""
Neon Database Operations for Articles

Save and retrieve articles from PostgreSQL.
"""

from __future__ import annotations
from temporalio import activity
import psycopg
import json
import os
from datetime import datetime


@activity.defn
async def save_article_to_neon(
    existing_id: str | None,
    slug: str,
    payload: dict,
    app: str
) -> str:
    """
    Save article to Neon PostgreSQL database.

    Args:
        existing_id: Existing article ID (if updating)
        slug: Article slug
        payload: Article payload dict
        app: App context

    Returns:
        Article ID (UUID string)
    """
    async with await psycopg.AsyncConnection.connect(
        os.getenv("DATABASE_URL")
    ) as conn:
        async with conn.cursor() as cur:
            if existing_id:
                # Update existing article
                await cur.execute(
                    """
                    UPDATE articles
                    SET
                        title = %s,
                        content = %s,
                        excerpt = %s,
                        payload = %s,
                        updated_at = NOW(),
                        word_count = %s,
                        featured_image_url = %s,
                        hero_image_url = %s
                    WHERE id = %s
                    RETURNING id
                    """,
                    (
                        payload.get("title"),
                        payload.get("content"),
                        payload.get("excerpt"),
                        json.dumps(payload),
                        payload.get("word_count"),
                        payload.get("featured_image_url"),
                        payload.get("hero_image_url"),
                        existing_id
                    )
                )
                result = await cur.fetchone()
                article_id = str(result[0])
                activity.logger.info(f"Updated article: {article_id}")

            else:
                # Insert new article
                await cur.execute(
                    """
                    INSERT INTO articles (
                        slug,
                        title,
                        content,
                        excerpt,
                        payload,
                        app,
                        status,
                        word_count,
                        featured_image_url,
                        hero_image_url,
                        published_at,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id
                    """,
                    (
                        slug,
                        payload.get("title"),
                        payload.get("content"),
                        payload.get("excerpt"),
                        json.dumps(payload),
                        app,
                        payload.get("status", "draft"),
                        payload.get("word_count"),
                        payload.get("featured_image_url"),
                        payload.get("hero_image_url"),
                        payload.get("published_at")
                    )
                )
                result = await cur.fetchone()
                article_id = str(result[0])
                activity.logger.info(f"Created article: {article_id}")

            await conn.commit()
            return article_id


@activity.defn
async def link_companies_to_article(
    article_id: str,
    companies: list[dict]
) -> dict:
    """
    Link companies to article in article_companies junction table.

    Args:
        article_id: Article ID
        companies: List of company mention dicts

    Returns:
        Dict with links_created count
    """
    if not companies:
        return {"links_created": 0}

    links_created = 0

    async with await psycopg.AsyncConnection.connect(
        os.getenv("DATABASE_URL")
    ) as conn:
        async with conn.cursor() as cur:
            for company in companies:
                company_id = company.get("company_id")
                if not company_id:
                    continue

                try:
                    await cur.execute(
                        """
                        INSERT INTO article_companies (article_id, company_id, relevance_score, created_at, updated_at)
                        VALUES (%s, %s, %s, NOW(), NOW())
                        ON CONFLICT (article_id, company_id) DO UPDATE
                        SET relevance_score = EXCLUDED.relevance_score, updated_at = NOW()
                        """,
                        (article_id, company_id, company.get("relevance_score", 0.5))
                    )
                    links_created += 1
                except Exception as e:
                    activity.logger.warning(f"Failed to link company {company_id}: {e}")

            await conn.commit()

    activity.logger.info(f"Linked {links_created} companies to article")

    return {"links_created": links_created}
