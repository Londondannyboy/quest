"""
Content Service

Queries Neon database for content (countries, articles, jobs, deals).
Used by dashboard to surface relevant content based on user queries.
"""

import os
from typing import Optional, List, Dict, Any
import structlog

logger = structlog.get_logger()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")


class ContentService:
    """Service for querying content from Neon database."""

    def __init__(self):
        self.enabled = bool(DATABASE_URL)
        self._pool = None

    async def _get_pool(self):
        """Get or create connection pool."""
        if self._pool is None:
            try:
                import asyncpg
                self._pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
            except Exception as e:
                logger.error("database_pool_error", error=str(e))
                self._pool = None
        return self._pool

    async def search(
        self,
        query: str,
        content_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search all content types for a query.

        Args:
            query: Search term
            content_type: Optional filter (country_guide, article, job, deal)
            limit: Max results

        Returns:
            List of matching content items
        """
        results = []

        if content_type is None or content_type == "country_guide":
            countries = await self.search_countries(query, limit=limit)
            results.extend(countries)

        if content_type is None or content_type == "article":
            articles = await self.search_articles(query, limit=limit)
            results.extend(articles)

        if content_type is None or content_type == "job":
            jobs = await self.search_jobs(query, limit=limit)
            results.extend(jobs)

        if content_type is None or content_type == "deal":
            deals = await self.search_deals(query, limit=limit)
            results.extend(deals)

        return results[:limit]

    async def search_countries(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search countries by name, region, or tags."""
        pool = await self._get_pool()
        if not pool:
            return []

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, name, slug, flag_emoji, region, continent,
                           visa_types, work_permit_requirements
                    FROM countries
                    WHERE status = 'published'
                    AND (
                        name ILIKE $1
                        OR region ILIKE $1
                        OR continent ILIKE $1
                        OR visa_types ILIKE $1
                        OR $2 = ANY(relocation_tags)
                    )
                    LIMIT $3
                """, f"%{query}%", query.lower(), limit)

                return [{
                    "id": row["id"],
                    "type": "country_guide",
                    "title": f"{row['name']} Relocation Guide",
                    "slug": row["slug"],
                    "country": row["name"],
                    "country_flag": row["flag_emoji"],
                    "excerpt": f"Visa info, cost of living, and relocation guide for {row['name']}",
                    "region": row["region"]
                } for row in rows]

        except Exception as e:
            logger.error("search_countries_error", query=query, error=str(e))
            return []

    async def search_articles(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search articles by title or content."""
        pool = await self._get_pool()
        if not pool:
            return []

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, title, slug, excerpt, country,
                           featured_asset_url, hero_asset_url
                    FROM articles
                    WHERE status = 'published'
                    AND app = 'relocation'
                    AND (
                        title ILIKE $1
                        OR excerpt ILIKE $1
                        OR content ILIKE $1
                        OR country ILIKE $1
                    )
                    ORDER BY published_at DESC
                    LIMIT $2
                """, f"%{query}%", limit)

                return [{
                    "id": row["id"],
                    "type": "article",
                    "title": row["title"],
                    "slug": row["slug"],
                    "excerpt": row["excerpt"],
                    "country": row["country"],
                    "featured_image": row["featured_asset_url"],
                    "hero_image": row["hero_asset_url"],
                } for row in rows]

        except Exception as e:
            logger.error("search_articles_error", query=query, error=str(e))
            return []

    async def search_jobs(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search jobs by title, company, or location."""
        pool = await self._get_pool()
        if not pool:
            return []

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, title, company_name, location, salary_min, salary_max, currency
                    FROM jobs
                    WHERE (
                        title ILIKE $1
                        OR company_name ILIKE $1
                        OR location ILIKE $1
                    )
                    AND is_active = true
                    ORDER BY created_at DESC
                    LIMIT $2
                """, f"%{query}%", limit)

                return [{
                    "id": row["id"],
                    "type": "job",
                    "title": row["title"],
                    "slug": str(row["id"]),  # Jobs use ID as slug
                    "excerpt": f"{row['company_name']} - {row['location']}",
                    "salary": f"{row['currency']} {row['salary_min']}-{row['salary_max']}" if row['salary_min'] else None
                } for row in rows]

        except Exception as e:
            logger.error("search_jobs_error", query=query, error=str(e))
            return []

    async def search_deals(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search deals by title or description."""
        pool = await self._get_pool()
        if not pool:
            return []

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, title, slug, description, discount_percent
                    FROM deals
                    WHERE (
                        title ILIKE $1
                        OR description ILIKE $1
                    )
                    AND is_active = true
                    ORDER BY created_at DESC
                    LIMIT $2
                """, f"%{query}%", limit)

                return [{
                    "id": row["id"],
                    "type": "deal",
                    "title": row["title"],
                    "slug": row["slug"],
                    "excerpt": row["description"][:200] if row["description"] else None,
                    "discount": f"{row['discount_percent']}% off" if row['discount_percent'] else None
                } for row in rows]

        except Exception as e:
            logger.error("search_deals_error", query=query, error=str(e))
            return []

    async def search_by_country(self, country_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all content related to a specific country."""
        results = []

        # Get country guide
        countries = await self.search_countries(country_name, limit=1)
        results.extend(countries)

        # Get articles about this country
        articles = await self.search_articles(country_name, limit=limit - 1)
        results.extend(articles)

        return results[:limit]

    async def get_country_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get a country by its slug."""
        pool = await self._get_pool()
        if not pool:
            return None

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT id, name, slug, flag_emoji, region, continent,
                           visa_types, work_permit_requirements, tax_overview,
                           language, processing_time, facts
                    FROM countries
                    WHERE slug = $1 AND status = 'published'
                """, slug)

                if not row:
                    return None

                return {
                    "id": row["id"],
                    "name": row["name"],
                    "slug": row["slug"],
                    "flag_emoji": row["flag_emoji"],
                    "region": row["region"],
                    "continent": row["continent"],
                    "visa_types": row["visa_types"],
                    "work_permit_requirements": row["work_permit_requirements"],
                    "tax_overview": row["tax_overview"],
                    "language": row["language"],
                    "processing_time": row["processing_time"],
                    "facts": row["facts"]
                }

        except Exception as e:
            logger.error("get_country_error", slug=slug, error=str(e))
            return None


    async def get_recent_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent published relocation articles."""
        pool = await self._get_pool()
        if not pool:
            return []

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, title, slug, excerpt, country,
                           featured_asset_url, hero_asset_url
                    FROM articles
                    WHERE status = 'published'
                    AND app = 'relocation'
                    AND published_at IS NOT NULL
                    ORDER BY published_at DESC
                    LIMIT $1
                """, limit)

                return [{
                    "id": row["id"],
                    "type": "article",
                    "title": row["title"],
                    "slug": row["slug"],
                    "excerpt": row["excerpt"],
                    "country": row["country"],
                    "featured_image": row["featured_asset_url"],
                    "hero_image": row["hero_asset_url"],
                } for row in rows]

        except Exception as e:
            logger.error("get_recent_articles_error", error=str(e))
            return []

    async def get_all_articles(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all published relocation articles with full metadata."""
        pool = await self._get_pool()
        if not pool:
            return []

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT a.id, a.title, a.slug, a.excerpt, a.country, a.article_mode,
                           a.featured_asset_url, a.hero_asset_url, a.published_at,
                           a.word_count, a.is_featured, a.video_playback_id,
                           c.name as country_name, c.flag_emoji
                    FROM articles a
                    LEFT JOIN countries c ON c.code = a.country_code
                    WHERE a.status = 'published'
                    AND a.app = 'relocation'
                    ORDER BY
                        a.is_featured DESC NULLS LAST,
                        a.published_at DESC NULLS LAST
                    LIMIT $1
                """, limit)

                return [{
                    "id": row["id"],
                    "slug": row["slug"],
                    "title": row["title"],
                    "excerpt": row["excerpt"],
                    "country": row["country"],
                    "country_name": row["country_name"],
                    "flag_emoji": row["flag_emoji"],
                    "article_mode": row["article_mode"] or "topic",
                    "featured_asset_url": row["featured_asset_url"],
                    "hero_asset_url": row["hero_asset_url"],
                    "video_playback_id": row["video_playback_id"],
                    "published_at": row["published_at"].isoformat() if row["published_at"] else None,
                    "word_count": row["word_count"],
                    "is_featured": row["is_featured"],
                } for row in rows]

        except Exception as e:
            logger.error("get_all_articles_error", error=str(e))
            return []

    async def get_article_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get a single article by slug with full content."""
        pool = await self._get_pool()
        if not pool:
            return None

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT a.id, a.title, a.slug, a.excerpt, a.content, a.country, a.article_mode,
                           a.featured_asset_url, a.hero_asset_url, a.published_at,
                           a.word_count, a.is_featured, a.video_playback_id,
                           c.name as country_name, c.flag_emoji
                    FROM articles a
                    LEFT JOIN countries c ON c.code = a.country_code
                    WHERE a.slug = $1
                    AND a.status = 'published'
                    AND a.app = 'relocation'
                """, slug)

                if not row:
                    return None

                return {
                    "id": row["id"],
                    "slug": row["slug"],
                    "title": row["title"],
                    "excerpt": row["excerpt"],
                    "content": row["content"],
                    "country": row["country"],
                    "country_name": row["country_name"],
                    "flag_emoji": row["flag_emoji"],
                    "article_mode": row["article_mode"] or "topic",
                    "featured_asset_url": row["featured_asset_url"],
                    "hero_asset_url": row["hero_asset_url"],
                    "video_playback_id": row["video_playback_id"],
                    "published_at": row["published_at"].isoformat() if row["published_at"] else None,
                    "word_count": row["word_count"],
                    "is_featured": row["is_featured"],
                }

        except Exception as e:
            logger.error("get_article_by_slug_error", slug=slug, error=str(e))
            return None


# Singleton instance
content_service = ContentService()
