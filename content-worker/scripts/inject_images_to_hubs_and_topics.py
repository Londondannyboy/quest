#!/usr/bin/env python3
"""
Inject Mux thumbnails into existing topic cluster articles and content hubs.

This script:
1. Finds topic cluster articles with parent video
2. Finds content hubs with video
3. Injects section images into their content
4. Updates the database

Usage:
    cd content-worker && python3 scripts/inject_images_to_hubs_and_topics.py
    cd content-worker && python3 scripts/inject_images_to_hubs_and_topics.py --apply
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg
from src.utils.inject_section_images import inject_section_images


DATABASE_URL = 'postgresql://neondb_owner:npg_LjBNF17HSTix@ep-green-smoke-ab3vtnw9-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require'


async def inject_images_to_topic_clusters(country_slug: str, dry_run: bool = True):
    """Inject images into topic cluster articles for a country."""

    print(f"\n{'='*60}")
    print(f"Processing topic cluster articles for {country_slug}")
    print(f"{'='*60}")

    async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            # Find topic cluster articles for this country
            # Topic clusters have parent_id set (they're children of main cluster articles)
            # and article_mode = 'topic' (distinct from story/guide/yolo/voices)
            await cur.execute("""
                SELECT a.id, a.slug, a.content, a.video_playback_id,
                       parent.video_playback_id as parent_video
                FROM articles a
                LEFT JOIN articles parent ON a.parent_id = parent.id
                WHERE a.slug LIKE %s
                  AND a.parent_id IS NOT NULL
                  AND a.article_mode = 'topic'
                  AND (a.video_playback_id IS NOT NULL OR parent.video_playback_id IS NOT NULL)
                ORDER BY a.id
            """, (f"{country_slug}%",))

            articles = await cur.fetchall()
            print(f"Found {len(articles)} topic cluster articles with videos")

            updated_count = 0

            for article in articles:
                article_id, slug, content, own_video, parent_video = article
                playback_id = own_video or parent_video

                if not playback_id:
                    continue

                print(f"\n  Article {article_id}: {slug}")
                print(f"  Video: {playback_id[:20]}...")

                # Check if already has injected images
                has_images = content and 'section-image' in content

                if has_images:
                    print(f"  ⏭️  Already has section images - skipping")
                    continue

                if not content or not content.strip():
                    print(f"  ⚠️  No content to process")
                    continue

                # Inject images
                updated_content = inject_section_images(
                    content,
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
                    await cur.execute("""
                        UPDATE articles
                        SET content = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (updated_content, article_id))
                    updated_count += 1
                else:
                    print(f"  [DRY RUN] Would update content ({len(updated_content)} chars)")

            if not dry_run:
                await conn.commit()

            print(f"\n{'='*60}")
            print(f"Updated {updated_count} topic cluster articles for {country_slug}")
            print(f"{'='*60}")

            return updated_count


async def inject_images_to_hubs(country_slug: str, dry_run: bool = True):
    """Inject images into content hub pages for a country."""

    print(f"\n{'='*60}")
    print(f"Processing content hubs for {country_slug}")
    print(f"{'='*60}")

    async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            # Find content hubs for this country
            await cur.execute("""
                SELECT id, location_name, slug, hub_content, video_playback_id
                FROM country_hubs
                WHERE slug LIKE %s
                  AND video_playback_id IS NOT NULL
                ORDER BY id
            """, (f"{country_slug}%",))

            hubs = await cur.fetchall()
            print(f"Found {len(hubs)} content hubs with videos")

            updated_count = 0

            for hub in hubs:
                hub_id, hub_name, slug, hub_content, playback_id = hub

                print(f"\n  Hub {hub_id} ({hub_name}): {slug}")
                print(f"  Video: {playback_id[:20]}...")

                # Check if already has injected images
                has_images = hub_content and 'section-image' in hub_content

                if has_images:
                    print(f"  ⏭️  Already has section images - skipping")
                    continue

                if not hub_content or not hub_content.strip():
                    print(f"  ⚠️  No hub content to process")
                    continue

                # Inject images
                updated_content = inject_section_images(
                    hub_content,
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
                    await cur.execute("""
                        UPDATE country_hubs
                        SET hub_content = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (updated_content, hub_id))
                    updated_count += 1
                else:
                    print(f"  [DRY RUN] Would update hub content ({len(updated_content)} chars)")

            if not dry_run:
                await conn.commit()

            print(f"\n{'='*60}")
            print(f"Updated {updated_count} content hubs for {country_slug}")
            print(f"{'='*60}")

            return updated_count


async def main():
    """Run image injection for topic clusters and hubs."""

    print("\n" + "="*60)
    print("HUB & TOPIC CLUSTER IMAGE INJECTION")
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

    total_topics_updated = 0
    total_hubs_updated = 0

    for country in countries:
        topics_count = await inject_images_to_topic_clusters(country, dry_run=dry_run)
        hubs_count = await inject_images_to_hubs(country, dry_run=dry_run)

        total_topics_updated += topics_count
        total_hubs_updated += hubs_count

    print(f"\n{'='*60}")
    print(f"TOTAL: {'Would update' if dry_run else 'Updated'}")
    print(f"  - {total_topics_updated} topic cluster articles")
    print(f"  - {total_hubs_updated} content hubs")
    print(f"{'='*60}")

    if dry_run:
        print("\nTo apply changes, run:")
        print("  python3 scripts/inject_images_to_hubs_and_topics.py --apply")


if __name__ == "__main__":
    asyncio.run(main())
