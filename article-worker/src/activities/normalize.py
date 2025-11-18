"""
Article Normalization Activities

Normalize topic and check for existing articles.
"""

from __future__ import annotations
from temporalio import activity
from src.utils.helpers import generate_article_slug, clean_text
import psycopg
import os


@activity.defn
async def normalize_article_topic(topic: str, app: str) -> dict:
    """
    Normalize article topic and generate slug.

    Args:
        topic: Raw article topic
        app: App context

    Returns:
        Dict with cleaned_topic, slug
    """
    cleaned_topic = clean_text(topic)
    slug = generate_article_slug(cleaned_topic)

    activity.logger.info(f"Normalized topic: {cleaned_topic} -> {slug}")

    return {
        "topic": cleaned_topic,
        "slug": slug,
        "app": app
    }


@activity.defn
async def check_article_exists(slug: str) -> dict:
    """
    Check if article with slug already exists.

    Args:
        slug: Article slug

    Returns:
        Dict with exists, article_id
    """
    try:
        async with await psycopg.AsyncConnection.connect(
            os.getenv("DATABASE_URL")
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id FROM articles WHERE slug = %s LIMIT 1",
                    (slug,)
                )
                result = await cur.fetchone()

                if result:
                    activity.logger.info(f"Article exists: {result[0]}")
                    return {
                        "exists": True,
                        "article_id": str(result[0])
                    }
                else:
                    activity.logger.info("Article does not exist")
                    return {
                        "exists": False,
                        "article_id": None
                    }

    except Exception as e:
        activity.logger.error(f"Error checking article existence: {e}")
        return {
            "exists": False,
            "article_id": None
        }
