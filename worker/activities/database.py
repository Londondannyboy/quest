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
from psycopg.types.json import Json


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

                # Get images if present
                images = article.get("images", {})

                # Insert article with all required fields including images
                await cur.execute("""
                    INSERT INTO articles (
                        id, title, slug, content, excerpt,
                        word_count, citation_count,
                        status, published_at, app, zep_graph_id, images
                    ) VALUES (
                        %(id)s, %(title)s, %(slug)s, %(content)s, %(excerpt)s,
                        %(word_count)s, %(citation_count)s,
                        'published', NOW(), %(app)s, %(zep_graph_id)s, %(images)s
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
                        images = EXCLUDED.images,
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
                    "zep_graph_id": zep_graph_id,
                    "images": Json(images) if images else Json({})
                })

                result = await cur.fetchone()
                article_uuid = result[0] if result else article.get("id")
                article_slug = result[1] if result else article.get("slug", "")

                # Save images to images table and link via article_image_usage
                if images:
                    activity.logger.info(f"   Saving {len(images)} images to database...")

                    for role, cloudinary_url in images.items():
                        if cloudinary_url:
                            try:
                                # Extract public_id from Cloudinary URL
                                # URL format: https://res.cloudinary.com/{cloud}/image/upload/{version}/{public_id}.{format}
                                url_parts = cloudinary_url.split('/upload/')
                                if len(url_parts) == 2:
                                    # Remove version prefix (e.g., "v1762817386/")
                                    path_parts = url_parts[1].split('/', 1)
                                    if len(path_parts) == 2:
                                        public_id_with_ext = path_parts[1]
                                        # Remove file extension
                                        public_id = public_id_with_ext.rsplit('.', 1)[0]
                                    else:
                                        public_id = url_parts[1].rsplit('.', 1)[0]
                                else:
                                    public_id = f"quest-articles/{role}_{article_uuid}"

                                # Insert into images table
                                await cur.execute("""
                                    INSERT INTO images (
                                        cloudinary_url,
                                        cloudinary_public_id,
                                        tags,
                                        created_at,
                                        updated_at
                                    ) VALUES (
                                        %(cloudinary_url)s,
                                        %(cloudinary_public_id)s,
                                        %(tags)s,
                                        NOW(),
                                        NOW()
                                    )
                                    RETURNING id
                                """, {
                                    "cloudinary_url": cloudinary_url,
                                    "cloudinary_public_id": public_id,
                                    "tags": [str(article_uuid), article.get("title", "")[:100], role, "auto-generated"]
                                })

                                image_result = await cur.fetchone()
                                image_id = image_result[0] if image_result else None

                                if image_id:
                                    # Insert into article_image_usage table
                                    await cur.execute("""
                                        INSERT INTO article_image_usage (
                                            article_id,
                                            image_id,
                                            role,
                                            alt_text,
                                            created_at
                                        ) VALUES (
                                            %(article_id)s,
                                            %(image_id)s,
                                            %(role)s,
                                            %(alt_text)s,
                                            NOW()
                                        )
                                    """, {
                                        "article_id": article_uuid,
                                        "image_id": image_id,
                                        "role": role,
                                        "alt_text": f"{article.get('title', 'Article')} - {role} image"
                                    })

                                    activity.logger.info(f"      ✅ Saved {role} image (id={image_id})")
                                else:
                                    activity.logger.warning(f"      ⚠️  Failed to get image_id for {role}")

                            except Exception as e:
                                activity.logger.error(f"      ❌ Failed to save {role} image: {e}")
                                # Continue with other images even if one fails

                # Commit transaction
                await conn.commit()

                activity.logger.info(f"✅ Article saved: {article_slug}")
                activity.logger.info(f"   Words: {metadata['word_count']}, Citations: {metadata['citation_count']}, App: {app}")

                return True

    except Exception as e:
        activity.logger.error(f"❌ Failed to save article: {e}")
        raise


@activity.defn(name="save_company_profile")
async def save_company_profile(company_profile: Dict[str, Any]) -> bool:
    """
    Save company profile to existing companies table

    Args:
        company_profile: Company profile dict from workflow

    Returns:
        True if saved successfully
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set")

    activity.logger.info(f"💾 Saving company profile: {company_profile.get('company_name', 'Unknown')}")

    try:
        async with await psycopg.AsyncConnection.connect(database_url) as conn:
            async with conn.cursor() as cur:
                # Get data from profile
                company_name = company_profile.get("company_name", "Unknown")
                company_type = company_profile.get("company_type", "placement_company")

                # Create slug from company name
                import re
                slug = re.sub(r'[^a-z0-9]+', '-', company_name.lower()).strip('-')

                # Get logo data
                logo_data = company_profile.get("logo", {})
                logo_url = logo_data.get("original_logo_url") or logo_data.get("fallback_image_url")

                # Get validation data
                validation = company_profile.get("validation", {})
                completeness_score = validation.get("overall_score", 0.0)

                # Map to existing schema
                type_mapping = {
                    "placement_company": "placement_agent",
                    "relocation_company": "relocation_service"
                }
                db_type = type_mapping.get(company_type, "placement_agent")

                # Prepare specializations array
                specializations = company_profile.get("specializations", [])
                if not specializations:
                    specializations = company_profile.get("key_services", [])

                # Prepare key_facts JSONB
                key_facts = {
                    "services": company_profile.get("key_services", []),
                    "achievements": company_profile.get("notable_achievements", []),
                    "people": company_profile.get("key_people", []),
                }

                # Insert or update company profile using existing schema
                await cur.execute("""
                    INSERT INTO companies (
                        name, slug, type, description,
                        headquarters, website_url, logo_url,
                        specializations, key_facts, overview,
                        status, company_type
                    ) VALUES (
                        %(name)s, %(slug)s, %(type)s, %(description)s,
                        %(headquarters)s, %(website_url)s, %(logo_url)s,
                        %(specializations)s, %(key_facts)s, %(overview)s,
                        'published', %(company_type)s
                    )
                    ON CONFLICT (slug) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        headquarters = EXCLUDED.headquarters,
                        website_url = EXCLUDED.website_url,
                        logo_url = EXCLUDED.logo_url,
                        specializations = EXCLUDED.specializations,
                        key_facts = EXCLUDED.key_facts,
                        overview = EXCLUDED.overview,
                        company_type = EXCLUDED.company_type,
                        updated_at = NOW()
                    RETURNING id, slug
                """, {
                    "name": company_name,
                    "slug": slug,
                    "type": db_type,
                    "description": company_profile.get("description", "")[:500],  # Limit length
                    "headquarters": company_profile.get("headquarters_location", ""),
                    "website_url": company_profile.get("website", ""),
                    "logo_url": logo_url,
                    "specializations": specializations,
                    "key_facts": Json(key_facts),
                    "overview": company_profile.get("profile_summary", ""),
                    "company_type": company_type
                })

                result = await cur.fetchone()
                saved_id = result[0] if result else None
                saved_slug = result[1] if result else slug

                # Commit transaction
                await conn.commit()

                activity.logger.info(f"✅ Company profile saved: {company_name} (id={saved_id}, slug={saved_slug})")
                activity.logger.info(f"   Type: {db_type}, Completeness: {completeness_score:.1%}")

                return True

    except Exception as e:
        activity.logger.error(f"❌ Failed to save company profile: {e}")
        import traceback
        activity.logger.error(traceback.format_exc())
        # Don't raise - return False to allow workflow to continue
        return False
