"""
Duplicate Check Activity

Checks Neon database to avoid publishing duplicate articles.
"""

import os
from typing import Dict
from temporalio import activity
import psycopg


@activity.defn(name="check_for_duplicates")
async def check_for_duplicates(
    topic: str,
    app: str,
    days_back: int = 7
) -> Dict[str, any]:
    """
    Check if we've published similar articles in the last N days

    Args:
        topic: Search topic/keywords
        app: Application name (e.g., 'chief-of-staff')
        days_back: Number of days to look back (default 7)

    Returns:
        Dict with is_duplicate (bool) and existing_articles (list)
    """
    activity.logger.info(f"🔍 Checking for duplicates: '{topic}' (last {days_back} days)")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        activity.logger.warning("DATABASE_URL not set, skipping duplicate check")
        return {"is_duplicate": False, "existing_articles": []}

    try:
        # Connect to database
        async with await psycopg.AsyncConnection.connect(database_url) as conn:
            async with conn.cursor() as cur:
                # Search for similar articles in last N days
                # Simple keyword matching on title and content
                keywords = topic.lower().split()[:3]  # Take first 3 words
                keyword_pattern = '%' + '%'.join(keywords) + '%'

                await cur.execute("""
                    SELECT id, title, created_at, slug
                    FROM articles
                    WHERE app = %s
                      AND created_at >= NOW() - INTERVAL '%s days'
                      AND (
                        LOWER(title) LIKE %s
                        OR LOWER(content) LIKE %s
                      )
                    ORDER BY created_at DESC
                    LIMIT 5
                """, (app, days_back, keyword_pattern, keyword_pattern))

                results = await cur.fetchall()

                existing_articles = [
                    {
                        "id": row[0],
                        "title": row[1],
                        "created_at": str(row[2]),
                        "slug": row[3]
                    }
                    for row in results
                ]

                is_duplicate = len(existing_articles) > 0

                if is_duplicate:
                    activity.logger.info(f"   ⚠️  Found {len(existing_articles)} similar articles")
                    for article in existing_articles:
                        activity.logger.info(f"      - {article['title']}")
                else:
                    activity.logger.info(f"   ✅ No duplicates found")

                return {
                    "is_duplicate": is_duplicate,
                    "existing_articles": existing_articles
                }

    except Exception as e:
        activity.logger.error(f"❌ Duplicate check failed: {e}")
        # On error, allow article generation to proceed
        return {"is_duplicate": False, "existing_articles": []}
