#!/usr/bin/env python3
"""
Backfill images for articles without images

Generates hero, featured, and content images for all articles that don't have them yet.
Saves to both JSONB column and legacy images/article_image_usage tables.
"""

import os
import asyncio
import time
from dotenv import load_dotenv
import psycopg
from psycopg.types.json import Json
import replicate
import cloudinary
import cloudinary.uploader

load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


async def generate_images_for_app(article_id: str, title: str, angle: str, app: str) -> dict:
    """Generate 3 images based on app type"""
    
    if app == "placement":
        # Bloomberg-style corporate imagery
        prompts = {
            "hero": f"Professional financial concept illustration, {title}, corporate style, clean modern design, Bloomberg aesthetic, sophisticated business imagery, professional photography",
            "featured": f"Financial data visualization, {angle}, clean modern infographic, professional business concept, sophisticated design",
            "content": f"Professional business imagery, {title}, corporate photography, modern office environment, business concept visualization"
        }
    elif app == "relocation":
        # Travel/lifestyle imagery
        prompts = {
            "hero": f"Vibrant travel photography, {title}, lifestyle scene, welcoming atmosphere, professional travel photography, city life, warm natural lighting",
            "featured": f"Travel destination imagery, {angle}, aspirational photography, golden hour lighting, cultural authenticity",
            "content": f"Practical lifestyle scene, {title}, authentic photography, real-world scenarios, natural lighting"
        }
    else:
        # Generic fallback
        prompts = {
            "hero": f"Professional hero image for article: {title}",
            "featured": f"Featured image for: {angle}",
            "content": f"Content image for: {title}"
        }
    
    replicate_urls = {}
    for purpose, prompt in prompts.items():
        try:
            print(f"      Generating {purpose} image...")
            
            output = replicate.run(
                "ideogram-ai/ideogram-v3-turbo",
                input={
                    "prompt": prompt,
                    "aspect_ratio": "16:9" if purpose == "hero" else ("3:2" if purpose == "featured" else "4:3"),
                    "magic_prompt_option": "Auto",
                    "style_type": "General"
                }
            )
            
            # Handle output
            if isinstance(output, str):
                url = output
            elif isinstance(output, list) and len(output) > 0:
                url = str(output[0])
            elif hasattr(output, 'url'):
                url = output.url
            else:
                url = str(output)
            
            replicate_urls[purpose] = url
            print(f"      ✅ Generated {purpose}")
            
            # Rate limit: wait 2 seconds between image generations
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"      ❌ Failed {purpose}: {e}")
            replicate_urls[purpose] = None
    
    # Upload to Cloudinary
    print(f"      Uploading to Cloudinary...")
    cloudinary_urls = {}
    for purpose, url in replicate_urls.items():
        if url:
            try:
                result = await asyncio.to_thread(
                    cloudinary.uploader.upload,
                    url,
                    folder="quest-articles",
                    public_id=f"{app}_{purpose}_{article_id}",
                    overwrite=True,
                    resource_type="image"
                )
                cloudinary_urls[purpose] = result["secure_url"]
                print(f"      ✅ Uploaded {purpose}")
            except Exception as e:
                print(f"      ❌ Upload failed {purpose}: {e}")
                cloudinary_urls[purpose] = None
        else:
            cloudinary_urls[purpose] = None
    
    return cloudinary_urls


async def save_images_to_db(conn, article_id: str, article_title: str, images: dict):
    """Save images to both JSONB column and legacy tables"""
    
    async with conn.cursor() as cur:
        # Update JSONB column
        await cur.execute("""
            UPDATE articles
            SET images = %(images)s,
                updated_at = NOW()
            WHERE id = %(article_id)s
        """, {
            "article_id": article_id,
            "images": Json(images)
        })
        
        # Save to legacy tables
        for role, cloudinary_url in images.items():
            if cloudinary_url:
                try:
                    # Extract public_id from Cloudinary URL
                    url_parts = cloudinary_url.split('/upload/')
                    if len(url_parts) == 2:
                        path_parts = url_parts[1].split('/', 1)
                        if len(path_parts) == 2:
                            public_id_with_ext = path_parts[1]
                            public_id = public_id_with_ext.rsplit('.', 1)[0]
                        else:
                            public_id = url_parts[1].rsplit('.', 1)[0]
                    else:
                        public_id = f"quest-articles/{role}_{article_id}"
                    
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
                        "tags": [str(article_id), article_title[:100], role, "backfilled"]
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
                            "article_id": article_id,
                            "image_id": image_id,
                            "role": role,
                            "alt_text": f"{article_title} - {role} image"
                        })
                
                except Exception as e:
                    print(f"      ❌ Failed to save {role} to legacy tables: {e}")
        
        await conn.commit()


async def main():
    """Main backfill process"""
    database_url = os.getenv("DATABASE_URL")
    
    print("=" * 80)
    print("🎨 BACKFILLING ARTICLE IMAGES")
    print("=" * 80)
    print()
    
    # Check API keys
    if not os.getenv("REPLICATE_API_TOKEN"):
        print("❌ REPLICATE_API_TOKEN not set")
        return
    
    if not os.getenv("CLOUDINARY_CLOUD_NAME"):
        print("❌ Cloudinary not configured")
        return
    
    async with await psycopg.AsyncConnection.connect(database_url) as conn:
        async with conn.cursor() as cur:
            # Find articles without images
            await cur.execute("""
                SELECT 
                    a.id,
                    a.title,
                    a.article_angle,
                    a.app,
                    a.images
                FROM articles a
                WHERE a.status = 'published'
                  AND (
                    a.images IS NULL 
                    OR a.images = '{}'::jsonb
                    OR NOT (a.images ? 'hero' AND a.images ? 'featured' AND a.images ? 'content')
                  )
                ORDER BY a.created_at DESC
            """)
            
            articles = await cur.fetchall()
            
            if not articles:
                print("✅ All articles already have images!")
                return
            
            print(f"📊 Found {len(articles)} articles without images")
            print()
            
            for i, (article_id, title, angle, app, existing_images) in enumerate(articles, 1):
                print(f"[{i}/{len(articles)}] Processing: {title[:60]}...")
                print(f"   App: {app}")
                print(f"   ID: {article_id}")
                
                try:
                    # Generate images
                    images = await generate_images_for_app(
                        article_id=article_id,
                        title=title,
                        angle=angle or title,
                        app=app or "placement"
                    )
                    
                    # Save to database
                    print(f"      💾 Saving to database...")
                    await save_images_to_db(conn, article_id, title, images)
                    
                    success_count = len([u for u in images.values() if u])
                    print(f"   ✅ Completed: {success_count}/3 images saved")
                    print()
                    
                    # Rate limit: wait 5 seconds between articles
                    if i < len(articles):
                        print(f"   ⏳ Waiting 5 seconds before next article...")
                        await asyncio.sleep(5)
                        print()
                    
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
                    print()
                    continue
    
    print("=" * 80)
    print("✅ BACKFILL COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
