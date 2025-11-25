"""
Fetch Related Articles Activity

Retrieve articles that mention or relate to a company.
This is KEY for the article display USP!
"""

import psycopg
from temporalio import activity
from typing import Dict, Any, List

from src.utils.config import config


@activity.defn
async def fetch_related_articles(
    company_id: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Fetch articles related to a company.

    This is a KEY activity for our USP - showing article coverage
    that Crunchbase and PitchBook don't show!

    Args:
        company_id: Company database ID
        limit: Max number of articles to return

    Returns:
        List of article dicts with slug, title, excerpt, etc.
    """
    activity.logger.info(f"Fetching related articles for company {company_id}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                # Query articles table with company relationship
                # This assumes you have an article_companies junction table
                await cur.execute("""
                    SELECT
                        a.id,
                        a.slug,
                        a.title,
                        a.payload->>'excerpt' as excerpt,
                        a.published_at,
                        a.featured_asset_url,
                        ac.relevance_score
                    FROM articles a
                    INNER JOIN article_companies ac ON a.id = ac.article_id
                    WHERE ac.company_id = %s
                    AND a.status = 'published'
                    ORDER BY a.published_at DESC
                    LIMIT %s
                """, (company_id, limit))

                rows = await cur.fetchall()

                articles = []
                for row in rows:
                    articles.append({
                        "id": str(row[0]),
                        "slug": row[1],
                        "title": row[2],
                        "excerpt": row[3],
                        "published_at": row[4].isoformat() if row[4] else None,
                        "featured_asset_url": row[5],
                        "relevance_score": float(row[6]) if row[6] else 0.0
                    })

                activity.logger.info(
                    f"Found {len(articles)} related articles"
                )

                return articles

    except Exception as e:
        activity.logger.error(f"Failed to fetch related articles: {e}")
        # Return empty list on error
        return []


@activity.defn
async def link_article_to_company(
    article_id: str,
    company_id: str,
    relevance_score: float = 1.0
) -> bool:
    """
    Create relationship between article and company.

    Args:
        article_id: Article database ID
        company_id: Company database ID
        relevance_score: Relevance score (0-1)

    Returns:
        Success boolean
    """
    activity.logger.info(
        f"Linking article {article_id} to company {company_id}"
    )

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
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
                """, (article_id, company_id, relevance_score))

                await conn.commit()

                activity.logger.info("Article-company link created")
                return True

    except Exception as e:
        activity.logger.error(f"Failed to link article to company: {e}")
        return False


@activity.defn
async def get_article_timeline(
    company_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get article timeline for company (for timeline view).

    Returns articles with relationship metadata for building
    the article timeline feature.

    Args:
        company_id: Company ID
        limit: Max articles

    Returns:
        List of articles with relationship data
    """
    activity.logger.info(f"Getting article timeline for company {company_id}")

    try:
        async with await psycopg.AsyncConnection.connect(
            config.DATABASE_URL
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT
                        a.id,
                        a.slug,
                        a.title,
                        a.payload->>'excerpt' as excerpt,
                        a.published_at,
                        a.featured_asset_url,
                        a.payload->>'reading_time_minutes' as reading_time,
                        ac.relevance_score,
                        -- Get mentioned companies
                        (
                            SELECT json_agg(
                                json_build_object(
                                    'id', c2.id,
                                    'slug', c2.slug,
                                    'name', c2.name
                                )
                            )
                            FROM article_companies ac2
                            INNER JOIN companies c2 ON ac2.company_id = c2.id
                            WHERE ac2.article_id = a.id
                            AND ac2.company_id != %s
                        ) as mentioned_companies
                    FROM articles a
                    INNER JOIN article_companies ac ON a.id = ac.article_id
                    WHERE ac.company_id = %s
                    AND a.status = 'published'
                    ORDER BY a.published_at DESC
                    LIMIT %s
                """, (company_id, company_id, limit))

                rows = await cur.fetchall()

                timeline = []
                for row in rows:
                    timeline.append({
                        "id": str(row[0]),
                        "slug": row[1],
                        "title": row[2],
                        "excerpt": row[3],
                        "published_at": row[4].isoformat() if row[4] else None,
                        "featured_asset_url": row[5],
                        "reading_time_minutes": row[6],
                        "relevance_score": float(row[7]) if row[7] else 0.0,
                        "mentioned_companies": row[8] or []
                    })

                activity.logger.info(
                    f"Timeline has {len(timeline)} articles"
                )

                return timeline

    except Exception as e:
        activity.logger.error(f"Failed to get article timeline: {e}")
        return []
