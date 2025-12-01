#!/usr/bin/env python3
"""
Inject Mux thumbnails into existing article content.

This script:
1. Finds articles with video_playback_id
2. Injects section images into their content
3. Updates the database

Usage:
    cd content-worker && python3 scripts/inject_images_to_articles.py
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg
from src.utils.inject_section_images import inject_section_images


DATABASE_URL = 'postgresql://neondb_owner:npg_LjBNF17HSTix@ep-green-smoke-ab3vtnw9-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require'


async def inject_images_for_country(country_name: str, dry_run: bool = True):
    """Inject images into all articles for a country."""

    print(f"\n{'='*60}")
    print(f"Processing {country_name} articles")
    print(f"{'='*60}")

    async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            # Find articles with video_playback_id for this country
            await cur.execute("""
                SELECT id, slug, article_mode, video_playback_id,
                       content, content_story, content_guide, content_yolo
                FROM articles
                WHERE slug LIKE %s
                  AND video_playback_id IS NOT NULL
                ORDER BY id
            """, (f"{country_name.lower()}%",))

            articles = await cur.fetchall()
            print(f"Found {len(articles)} articles with videos")

            updated_count = 0

            for article in articles:
                article_id, slug, mode, playback_id, content, content_story, content_guide, content_yolo = article

                print(f"\n  Article {article_id} ({mode}): {slug}")
                print(f"  Video: {playback_id[:20]}...")

                # Check if already has injected images
                has_images = content and 'section-image' in content

                if has_images:
                    print(f"  ⏭️  Already has section images - skipping")
                    continue

                # Determine which content to update based on mode
                content_to_update = content or ''

                if not content_to_update.strip():
                    print(f"  ⚠️  No content to process")
                    continue

                # Inject images
                updated_content = inject_section_images(
                    content_to_update,
                    playback_id,
                    image_width=1200,
                    max_sections=4
                )

                # Check if images were added
                if 'section-image' not in updated_content:
                    print(f"  ⚠️  No H2 sections found to inject images")
                    continue

                # Count added images
                image_count = updated_content.count('section-image')
                print(f"  ✅ Injected {image_count} section images")

                if not dry_run:
                    # Update the main content column
                    await cur.execute("""
                        UPDATE articles
                        SET content = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (updated_content, article_id))

                    # Also update mode-specific column if it exists
                    mode_column = f"content_{mode}" if mode in ['story', 'guide', 'yolo'] else None
                    if mode_column:
                        await cur.execute(f"""
                            UPDATE articles
                            SET {mode_column} = %s
                            WHERE id = %s
                        """, (updated_content, article_id))

                    updated_count += 1
                else:
                    print(f"  [DRY RUN] Would update content ({len(updated_content)} chars)")

            if not dry_run:
                await conn.commit()

            print(f"\n{'='*60}")
            print(f"Updated {updated_count} articles for {country_name}")
            print(f"{'='*60}")

            return updated_count


async def main():
    """Run image injection for specified countries."""

    print("\n" + "="*60)
    print("ARTICLE IMAGE INJECTION")
    print("="*60)

    # Check for --apply flag
    dry_run = "--apply" not in sys.argv

    if dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made")
        print("   Add --apply flag to actually update the database")
    else:
        print("\n✅ APPLY MODE - Will update the database")

    # Process countries
    countries = ["slovenia", "cyprus"]

    total_updated = 0
    for country in countries:
        count = await inject_images_for_country(country, dry_run=dry_run)
        total_updated += count

    print(f"\n{'='*60}")
    print(f"TOTAL: {'Would update' if dry_run else 'Updated'} {total_updated} articles")
    print(f"{'='*60}")

    if dry_run:
        print("\nTo apply changes, run:")
        print("  python3 scripts/inject_images_to_articles.py --apply")


if __name__ == "__main__":
    asyncio.run(main())
