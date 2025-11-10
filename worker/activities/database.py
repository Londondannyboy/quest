"""
Database Activities for Temporal Workflows

Simple activities for saving articles to Neon PostgreSQL.
"""

import os
import re
from typing import List, Dict, Any
from temporalio import activity
import psycopg
from psycopg.rows import dict_row


def calculate_metadata(content: str, excerpt: str = None) -> dict:
    """
    Calculate article metadata from content

    Returns:
        dict with word_count, citation_count, and excerpt
    """
    # Calculate word count
    word_count = len(content.split())

    # Count citations (markdown links)
    citation_count = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content))

    # Generate excerpt if not provided
    if not excerpt or excerpt.strip() == "":
        # Remove markdown formatting
        clean_content = re.sub(r'[#*\[\]()]', '', content)
        # Take first 160 chars
        excerpt = clean_content[:160].strip()
        if len(clean_content) > 160:
            excerpt += "..."

    return {
        "word_count": word_count,
        "citation_count": citation_count,
        "excerpt": excerpt
    }


@activity.defn(name="save_to_neon")
async def save_to_neon(article: Dict[str, Any], brief: Dict[str, Any]) -> bool:
    """
    Save article to Neon PostgreSQL database

    Automatically sets:
    - status = 'published'
    - published_at = NOW()
    - word_count (calculated)
    - citation_count (calculated)
    - excerpt (auto-generated if missing)

    Args:
        article: Article dict from workflow
        brief: Brief dict with metadata

    Returns:
        True if saved successfully
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set")

    activity.logger.info(f"💾 Saving article to Neon: {article.get('title', 'Unknown')}")

    try:
        async with await psycopg.AsyncConnection.connect(database_url) as conn:
            async with conn.cursor() as cur:
                # Calculate metadata
                content = article.get("content", "")
                excerpt = article.get("excerpt", "")
                metadata = calculate_metadata(content, excerpt)

                # Get app from article or default to placement
                app = article.get("app", "placement")

                # Get Zep graph ID if present
                zep_graph_id = article.get("zep_graph_id") or article.get("zep_episode_id")

                # Log what we're about to save
                activity.logger.info(f"   Status from article data: {article.get('status', 'NOT SET')}")
                activity.logger.info(f"   Zep graph ID: {zep_graph_id}")

                # Insert article with all required fields
                await cur.execute("""
                    INSERT INTO articles (
                        id, title, slug, content, excerpt,
                        word_count, citation_count,
                        status, published_at, app, zep_graph_id
                    ) VALUES (
                        %(id)s, %(title)s, %(slug)s, %(content)s, %(excerpt)s,
                        %(word_count)s, %(citation_count)s,
                        'published', NOW(), %(app)s, %(zep_graph_id)s
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        content = EXCLUDED.content,
                        excerpt = EXCLUDED.excerpt,
                        word_count = EXCLUDED.word_count,
                        citation_count = EXCLUDED.citation_count,
                        status = 'published',
                        published_at = COALESCE(articles.published_at, NOW()),
                        app = EXCLUDED.app,
                        zep_graph_id = COALESCE(EXCLUDED.zep_graph_id, articles.zep_graph_id),
                        updated_at = NOW()
                    RETURNING id, slug
                """, {
                    "id": article.get("id"),
                    "title": article.get("title", "Untitled"),
                    "slug": article.get("slug", "untitled"),
                    "content": content,
                    "excerpt": metadata["excerpt"],
                    "word_count": metadata["word_count"],
                    "citation_count": metadata["citation_count"],
                    "app": app,
                    "zep_graph_id": zep_graph_id
                })

                result = await cur.fetchone()
                article_id = result[1] if result else article.get("slug", "")

                # Commit transaction
                await conn.commit()

                activity.logger.info(f"✅ Article saved: {article_id}")
                activity.logger.info(f"   Words: {metadata['word_count']}, Citations: {metadata['citation_count']}, App: {app}")

                return True

    except Exception as e:
        activity.logger.error(f"❌ Failed to save article: {e}")
        raise
