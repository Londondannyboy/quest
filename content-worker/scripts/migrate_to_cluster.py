"""
Migration Script: Convert Legacy Content Columns to Cluster Architecture

This script converts articles that have content_story/content_guide/content_yolo columns
into separate cluster articles (one per mode) for SEO-friendly separate pages.

Usage:
    python scripts/migrate_to_cluster.py --dry-run  # Preview changes
    python scripts/migrate_to_cluster.py            # Execute migration

What it does:
1. Finds articles with legacy content columns (content_story, content_guide, content_yolo)
2. Generates a cluster_id for each article
3. Updates the original article to be the "story" parent
4. Creates new articles for guide, yolo, and voices modes
5. Links all articles via cluster_id and parent_id
"""

import os
import sys
import json
import uuid
import argparse
import psycopg2
from datetime import datetime

# Load environment
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    """Get database connection."""
    return psycopg2.connect(DATABASE_URL)

def find_legacy_articles(cursor):
    """Find articles with legacy content columns that need migration."""
    cursor.execute("""
        SELECT
            id, slug, title,
            content, content_story, content_guide, content_yolo, content_voices,
            meta_description, excerpt, video_playback_id, video_asset_id, video_url,
            payload, app, country, country_code,
            cluster_id, parent_id, article_mode
        FROM articles
        WHERE app = 'relocation'
          AND cluster_id IS NULL
          AND (content_story IS NOT NULL OR content_guide IS NOT NULL OR content_yolo IS NOT NULL)
        ORDER BY id
    """)

    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def create_cluster_article(cursor, parent_article, mode, cluster_id, content, meta_description, excerpt):
    """Create a new cluster article for a specific mode."""

    # Generate slug with mode suffix
    base_slug = parent_article['slug']
    new_slug = f"{base_slug}-{mode}"

    # Generate title with mode suffix
    base_title = parent_article['title']
    mode_titles = {
        'guide': f"{base_title} - Practical Guide",
        'yolo': f"{base_title} - YOLO Edition",
        'voices': f"{base_title} - Expat Voices"
    }
    new_title = mode_titles.get(mode, base_title)

    # Parse payload
    payload = parent_article.get('payload') or {}
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except:
            payload = {}

    # Add cluster metadata to payload
    payload['cluster_id'] = cluster_id
    payload['article_mode'] = mode
    payload['parent_slug'] = base_slug

    cursor.execute("""
        INSERT INTO articles (
            slug, title, content, meta_description, excerpt,
            app, country, country_code, status,
            payload, cluster_id, parent_id, article_mode,
            created_at, updated_at, published_at
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            NOW(), NOW(), NOW()
        )
        ON CONFLICT (slug) DO UPDATE SET
            title = EXCLUDED.title,
            content = EXCLUDED.content,
            meta_description = EXCLUDED.meta_description,
            excerpt = EXCLUDED.excerpt,
            payload = EXCLUDED.payload,
            cluster_id = EXCLUDED.cluster_id,
            parent_id = EXCLUDED.parent_id,
            article_mode = EXCLUDED.article_mode,
            updated_at = NOW(),
            published_at = COALESCE(articles.published_at, NOW())
        RETURNING id
    """, (
        new_slug,
        new_title,
        content or '',
        meta_description,
        excerpt,
        parent_article.get('app', 'relocation'),
        parent_article.get('country'),
        parent_article.get('country_code'),
        'published',
        json.dumps(payload),
        cluster_id,
        parent_article['id'],  # parent_id points to original article
        mode
    ))

    result = cursor.fetchone()
    return result[0] if result else None

def update_parent_article(cursor, article_id, cluster_id):
    """Update the original article to be the story parent with cluster metadata."""
    cursor.execute("""
        UPDATE articles
        SET
            cluster_id = %s,
            article_mode = 'story',
            updated_at = NOW()
        WHERE id = %s
        RETURNING id
    """, (cluster_id, article_id))

    return cursor.fetchone()

def migrate_article(cursor, article, dry_run=False):
    """Migrate a single article to cluster architecture."""

    print(f"\n{'='*60}")
    print(f"Migrating: {article['slug']} (ID: {article['id']})")
    print(f"{'='*60}")

    # Generate cluster UUID
    cluster_id = str(uuid.uuid4())
    print(f"Cluster ID: {cluster_id}")

    # Parse voices
    voices = article.get('content_voices') or []
    if isinstance(voices, str):
        try:
            voices = json.loads(voices)
        except:
            voices = []

    # Extract country name from title or slug
    country_name = article.get('country') or 'the country'

    # Define modes to create
    modes_to_create = []

    if article.get('content_guide'):
        modes_to_create.append({
            'mode': 'guide',
            'content': article['content_guide'],
            'meta_description': f"Practical guide for relocating to {country_name}. Step-by-step visa requirements, cost of living, and essential tips.",
            'excerpt': f"Your practical guide to relocating to {country_name}."
        })
        print(f"  - Guide: {len(article['content_guide'])} chars")

    if article.get('content_yolo'):
        modes_to_create.append({
            'mode': 'yolo',
            'content': article['content_yolo'],
            'meta_description': f"The adventurous guide to {country_name} relocation. Bold moves, unique experiences, and living life fully.",
            'excerpt': f"YOLO guide: {country_name} for the adventurous."
        })
        print(f"  - YOLO: {len(article['content_yolo'])} chars")

    if voices and len(voices) > 0:
        # For voices, store testimonials in payload, not content
        modes_to_create.append({
            'mode': 'voices',
            'content': '',  # Voices uses testimonials from payload
            'meta_description': f"Real expat voices and experiences from {country_name}. Authentic stories from people who made the move.",
            'excerpt': f"Hear from real expats in {country_name}."
        })
        print(f"  - Voices: {len(voices)} testimonials")

    if dry_run:
        print(f"\n[DRY RUN] Would create {len(modes_to_create)} cluster articles:")
        for m in modes_to_create:
            print(f"  - {article['slug']}-{m['mode']}")
        print(f"[DRY RUN] Would update parent article with cluster_id={cluster_id}")
        return {'parent_id': article['id'], 'cluster_id': cluster_id, 'created': len(modes_to_create)}

    # Execute migration
    created_articles = []

    # 1. Update parent article first
    update_parent_article(cursor, article['id'], cluster_id)
    print(f"\n✅ Updated parent article: {article['slug']} (cluster_id={cluster_id[:8]}...)")

    # 2. Create cluster articles
    for mode_config in modes_to_create:
        article_id = create_cluster_article(
            cursor,
            article,
            mode_config['mode'],
            cluster_id,
            mode_config['content'],
            mode_config['meta_description'],
            mode_config['excerpt']
        )

        if article_id:
            created_articles.append({
                'id': article_id,
                'mode': mode_config['mode'],
                'slug': f"{article['slug']}-{mode_config['mode']}"
            })
            print(f"✅ Created: {article['slug']}-{mode_config['mode']} (ID: {article_id})")
        else:
            print(f"❌ Failed to create: {article['slug']}-{mode_config['mode']}")

    return {
        'parent_id': article['id'],
        'cluster_id': cluster_id,
        'created': created_articles
    }

def main():
    parser = argparse.ArgumentParser(description='Migrate legacy content columns to cluster architecture')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without executing')
    parser.add_argument('--article-id', type=int, help='Migrate specific article by ID')
    args = parser.parse_args()

    print("="*60)
    print("Cluster Architecture Migration")
    print("="*60)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'EXECUTE'}")
    print(f"Database: {DATABASE_URL[:50]}...")
    print()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Find articles to migrate
        articles = find_legacy_articles(cursor)

        if args.article_id:
            articles = [a for a in articles if a['id'] == args.article_id]

        if not articles:
            print("No articles found to migrate.")
            return

        print(f"Found {len(articles)} article(s) to migrate:")
        for a in articles:
            story_len = len(a.get('content_story') or '')
            guide_len = len(a.get('content_guide') or '')
            yolo_len = len(a.get('content_yolo') or '')
            print(f"  - {a['slug']} (ID: {a['id']}) - Story: {story_len}, Guide: {guide_len}, YOLO: {yolo_len}")

        # Migrate each article
        results = []
        for article in articles:
            result = migrate_article(cursor, article, dry_run=args.dry_run)
            results.append(result)

        if not args.dry_run:
            conn.commit()
            print("\n" + "="*60)
            print("✅ Migration committed successfully!")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("DRY RUN complete - no changes made")
            print("Run without --dry-run to execute migration")
            print("="*60)

        # Summary
        print("\nSummary:")
        for r in results:
            print(f"  Cluster {r['cluster_id'][:8]}...: Parent ID {r['parent_id']}, Created {len(r.get('created', [])) if isinstance(r.get('created'), list) else r.get('created', 0)} articles")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
