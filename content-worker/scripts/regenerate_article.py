"""
Regenerate Article Content Script

Usage: python scripts/regenerate_article.py --article-id 92

Regenerates just the article text while preserving video, images, and other assets.
Uses zep_facts from the database as research context.
"""

import asyncio
import argparse
import json
import psycopg
from datetime import datetime

# Add parent to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import config
from src.activities.generation.article_generation import generate_four_act_article


async def get_article_data(article_id: int) -> dict:
    """Fetch article data from database."""
    async with await psycopg.AsyncConnection.connect(config.DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT
                    id, title, slug, app, target_keyword,
                    zep_facts, payload, video_playback_id,
                    article_angle
                FROM articles
                WHERE id = %s
            """, (article_id,))
            row = await cur.fetchone()

            if not row:
                raise ValueError(f"Article {article_id} not found")

            return {
                "id": row[0],
                "title": row[1],
                "slug": row[2],
                "app": row[3],
                "target_keyword": row[4],
                "zep_facts": row[5] or [],
                "payload": row[6] or {},
                "video_playback_id": row[7],
                "article_angle": row[8]
            }


def build_research_context_from_facts(zep_facts: list, topic: str) -> dict:
    """Build research context from Zep facts for article generation."""

    # Extract valid facts (not invalidated)
    valid_facts = [
        f["fact"] for f in zep_facts
        if f.get("invalid_at") is None
    ]

    # Group facts by type for better context
    key_facts = []
    for fact in valid_facts:
        key_facts.append({
            "fact": fact,
            "source_ids": ["zep_knowledge_graph"]
        })

    return {
        "topic": topic,
        "curation": {
            "curated_sources": [
                {
                    "source_id": "zep_0",
                    "title": f"Knowledge Graph: {topic}",
                    "url": "zep://knowledge-graph",
                    "type": "knowledge_graph",
                    "relevance_score": 10,
                    "full_content": "\n".join(valid_facts)
                }
            ],
            "key_facts": key_facts,
            "article_outline": [
                {"section": "Introduction", "key_points": ["Hook with lifestyle transformation"]},
                {"section": "Requirements", "key_points": ["Income, documents, eligibility"]},
                {"section": "Application Process", "key_points": ["Step by step guide"]},
                {"section": "Costs & Timeline", "key_points": ["Fees, processing time"]},
                {"section": "Living in Cyprus", "key_points": ["Lifestyle benefits"]},
                {"section": "Conclusion", "key_points": ["Call to action"]}
            ],
            "high_authority_sources": [],
            "opinions_and_sentiment": [],
            "unique_angles": [
                "Cyprus offers 340 days of sunshine vs UK's 149",
                "Non-dom tax status means 0% on foreign income for 17 years"
            ],
            "warnings_and_gotchas": [
                "Must apply within 3 months of arrival",
                "Family members cannot work locally"
            ]
        }
    }


async def update_article_content(article_id: int, result: dict) -> bool:
    """Update article with regenerated content."""

    article_data = result.get("article", {})

    async with await psycopg.AsyncConnection.connect(config.DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            # Update content fields while preserving video/images
            await cur.execute("""
                UPDATE articles
                SET
                    title = %s,
                    content = %s,
                    excerpt = %s,
                    meta_description = %s,
                    word_count = %s,
                    payload = payload || %s::jsonb,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                article_data.get("title"),
                article_data.get("content"),
                article_data.get("excerpt"),
                article_data.get("meta_description"),
                article_data.get("word_count"),
                json.dumps({
                    "regenerated_at": datetime.utcnow().isoformat(),
                    "model_used": result.get("model_used"),
                    "four_act_content": article_data.get("four_act_content", []),
                    "structured_data": article_data.get("structured_data", {}),
                    "yolo_mode": article_data.get("yolo_mode", {})
                }),
                article_id
            ))

            await conn.commit()
            return True


async def regenerate_article(article_id: int, dry_run: bool = False):
    """Main regeneration function."""

    print(f"\n{'='*60}")
    print(f"Regenerating Article ID: {article_id}")
    print(f"{'='*60}\n")

    # 1. Fetch article data
    print("1. Fetching article data...")
    article = await get_article_data(article_id)
    print(f"   Title: {article['title']}")
    print(f"   App: {article['app']}")
    print(f"   Zep Facts: {len(article['zep_facts'])} facts")
    print(f"   Video: {article['video_playback_id'] or 'None'}")

    # 2. Build research context from facts
    print("\n2. Building research context from Zep facts...")
    topic = article['target_keyword'] or article['title']
    research_context = build_research_context_from_facts(
        article['zep_facts'],
        topic
    )
    print(f"   Topic: {topic}")
    print(f"   Key facts: {len(research_context['curation']['key_facts'])}")

    # 3. Generate article
    print("\n3. Generating article content...")
    print("   (This may take 30-60 seconds)")

    result = await generate_four_act_article(
        topic=topic,
        research_context=research_context,
        app=article['app'],
        article_type=article['article_angle'] or "guide"
    )

    if not result.get("success"):
        print(f"\n   ERROR: {result.get('error')}")
        return False

    print(f"   Success! Word count: {result['article'].get('word_count')}")
    print(f"   Model used: {result.get('model_used')}")

    # 4. Preview
    print("\n4. Content Preview:")
    content = result['article'].get('content', '')
    print(f"   {content[:500]}...")

    # 5. Update database
    if dry_run:
        print("\n5. DRY RUN - Skipping database update")
        print("   Run without --dry-run to save changes")
    else:
        print("\n5. Updating database...")
        success = await update_article_content(article_id, result)
        if success:
            print("   Database updated successfully!")
        else:
            print("   ERROR: Failed to update database")
            return False

    print(f"\n{'='*60}")
    print("REGENERATION COMPLETE")
    print(f"{'='*60}\n")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regenerate article content")
    parser.add_argument("--article-id", type=int, required=True, help="Article ID to regenerate")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")

    args = parser.parse_args()

    asyncio.run(regenerate_article(args.article_id, args.dry_run))
