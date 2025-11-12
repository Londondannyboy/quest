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
async def save_company_profile(
    company_profile: Dict[str, Any],
    zep_graph_id: Optional[str] = None,
    condensed_summary: Optional[str] = None
) -> bool:
    """
    Save company profile to existing companies table with enriched data

    Args:
        company_profile: Company profile dict from workflow
        zep_graph_id: Optional Zep episode UUID (from sync_company_to_zep)
        condensed_summary: Optional condensed summary for Zep (<10k chars)

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

                # Map company_type to allowed database values
                # For company_type column, use the exact workflow type
                # For type column, use simplified category
                type_mapping = {
                    "placement_company": "placement_agent",
                    "relocation_company": "other"  # or add to constraint
                }
                db_type = type_mapping.get(company_type, "placement_agent")

                # For company_type column, map to allowed constraint values
                company_type_mapping = {
                    "placement_company": "placement_agent",
                    "placement_agent": "placement_agent",
                    "relocation_company": "relocation_company",
                    "executive_assistant_recruiters": "executive_assistant_recruiters",
                }
                db_company_type = company_type_mapping.get(company_type, "other")

                # Map company_type to app for database constraint
                app_mapping = {
                    "placement_agent": "placement",
                    "executive_assistant_recruiters": "chief-of-staff",
                    "relocation_company": "relocation",
                }
                db_app = app_mapping.get(db_company_type, "placement")

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

                # Extract enriched data fields
                founded_year = company_profile.get("founded_year")
                if founded_year and isinstance(founded_year, str):
                    try:
                        founded_year = int(founded_year)
                    except (ValueError, TypeError):
                        founded_year = None

                employee_count = company_profile.get("employee_count")
                if employee_count and isinstance(employee_count, str):
                    # Handle ranges like "250-500" by taking midpoint
                    if '-' in employee_count:
                        try:
                            parts = employee_count.split('-')
                            employee_count = int((int(parts[0]) + int(parts[1])) / 2)
                        except (ValueError, TypeError):
                            employee_count = None
                    else:
                        try:
                            employee_count = int(employee_count.replace(',', ''))
                        except (ValueError, TypeError):
                            employee_count = None

                # Extract contact info
                contact_info = company_profile.get("contact_info", {})
                phone = contact_info.get("phone") if contact_info else None
                email = contact_info.get("email") if contact_info else None

                # Extract AUM from additional_data (for placement agents)
                additional_data = company_profile.get("additional_data", {})
                aum = additional_data.get("aum") or additional_data.get("assets_under_management")

                # Extract geographic focus/regions served
                geographic_focus = additional_data.get("regions_served") or additional_data.get("geographic_focus")
                if isinstance(geographic_focus, list):
                    geographic_focus = geographic_focus  # Keep as array
                elif geographic_focus:
                    geographic_focus = [geographic_focus]  # Convert string to array
                else:
                    geographic_focus = []

                # Parse headquarters for primary_country and primary_region
                headquarters = company_profile.get("headquarters_location", "")
                primary_country = None
                primary_region = None
                if headquarters:
                    # Split on comma: "London, UK" -> ["London", "UK"]
                    parts = [p.strip() for p in headquarters.split(',')]
                    if len(parts) >= 2:
                        primary_country = parts[-1]  # Last part is usually country
                        primary_region = parts[0]  # First part is usually city/region
                    elif len(parts) == 1:
                        primary_country = parts[0]

                # Use provided zep_graph_id or get from profile
                final_zep_graph_id = zep_graph_id or company_profile.get("zep_graph_id")

                # Use provided condensed_summary or get from profile
                final_condensed_summary = condensed_summary or company_profile.get("condensed_summary")

                # Insert or update company profile using existing schema + new fields
                await cur.execute("""
                    INSERT INTO companies (
                        name, slug, type, description,
                        headquarters, website_url, logo_url,
                        specializations, key_facts, overview,
                        status, company_type, app,
                        founded_year, employee_count, phone, email,
                        capital_raised_total, geographic_focus,
                        primary_country, primary_region,
                        zep_graph_id, condensed_summary,
                        serviced_companies, serviced_deals, serviced_investors
                    ) VALUES (
                        %(name)s, %(slug)s, %(type)s, %(description)s,
                        %(headquarters)s, %(website_url)s, %(logo_url)s,
                        %(specializations)s, %(key_facts)s, %(overview)s,
                        'published', %(company_type)s, %(app)s,
                        %(founded_year)s, %(employee_count)s, %(phone)s, %(email)s,
                        %(capital_raised_total)s, %(geographic_focus)s,
                        %(primary_country)s, %(primary_region)s,
                        %(zep_graph_id)s, %(condensed_summary)s,
                        %(serviced_companies)s, %(serviced_deals)s, %(serviced_investors)s
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
                        app = EXCLUDED.app,
                        founded_year = EXCLUDED.founded_year,
                        employee_count = EXCLUDED.employee_count,
                        phone = EXCLUDED.phone,
                        email = EXCLUDED.email,
                        capital_raised_total = EXCLUDED.capital_raised_total,
                        geographic_focus = EXCLUDED.geographic_focus,
                        primary_country = EXCLUDED.primary_country,
                        primary_region = EXCLUDED.primary_region,
                        zep_graph_id = EXCLUDED.zep_graph_id,
                        condensed_summary = EXCLUDED.condensed_summary,
                        serviced_companies = EXCLUDED.serviced_companies,
                        serviced_deals = EXCLUDED.serviced_deals,
                        serviced_investors = EXCLUDED.serviced_investors,
                        updated_at = NOW()
                    RETURNING id, slug
                """, {
                    "name": company_name,
                    "slug": slug,
                    "type": db_type,
                    "description": company_profile.get("description", "")[:500],  # Limit length
                    "headquarters": headquarters,
                    "website_url": company_profile.get("website", ""),
                    "logo_url": logo_url,
                    "specializations": specializations,
                    "key_facts": Json(key_facts),
                    "overview": company_profile.get("profile_summary", ""),
                    "company_type": db_company_type,  # Use mapped value
                    "app": db_app,  # Use mapped app value
                    "founded_year": founded_year,
                    "employee_count": employee_count,
                    "phone": phone,
                    "email": email,
                    "capital_raised_total": aum,
                    "geographic_focus": geographic_focus,
                    "primary_country": primary_country,
                    "primary_region": primary_region,
                    "zep_graph_id": final_zep_graph_id,
                    "condensed_summary": final_condensed_summary,
                    "serviced_companies": None,  # Will be populated manually/later
                    "serviced_deals": None,  # Will be populated manually/later
                    "serviced_investors": None,  # Will be populated manually/later
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
