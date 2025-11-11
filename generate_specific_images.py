#!/usr/bin/env python3
"""
Generate images for specific articles that are missing images
"""
import os
import asyncio
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json
import replicate
import cloudinary
import cloudinary.uploader

# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Articles to fix
ARTICLES_TO_FIX = [
    'private-equity-latest-developments',
    'barclays-expands-investment-banking-asia-pacific'
]


async def generate_placement_images(article_id: str, article_title: str, article_angle: str):
    """Generate 4 Bloomberg-style images for placement articles"""
    print(f"🎨 Generating images for: {article_title[:60]}")

    prompts = {
        "hero": f"Professional financial concept illustration, {article_title}, corporate style, clean modern design, Bloomberg aesthetic, sophisticated color palette, data visualization elements, minimalist composition",
        "featured": f"Financial data visualization, {article_angle}, clean modern infographic, corporate color scheme, business intelligence aesthetic",
        "content": f"Professional business imagery, {article_title}, corporate photography, modern professional aesthetic, financial district or boardroom",
        "content2": f"Executive business setting, {article_angle}, modern office environment, professional corporate atmosphere, global business imagery"
    }

    # Generate all images
    replicate_urls = {}
    for purpose, prompt in prompts.items():
        try:
            print(f"   Generating {purpose} image...")

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

            print(f"   ✅ Generated {purpose}")
            replicate_urls[purpose] = url

            # Rate limit
            await asyncio.sleep(2)

        except Exception as e:
            print(f"   ❌ Failed {purpose}: {e}")
            replicate_urls[purpose] = None

    # Upload to Cloudinary
    print("☁️  Uploading to Cloudinary...")
    cloudinary_urls = {}
    for purpose, url in replicate_urls.items():
        if url:
            try:
                print(f"   Uploading {purpose}...")

                result = await asyncio.to_thread(
                    cloudinary.uploader.upload,
                    url,
                    folder="quest-articles",
                    public_id=f"placement_{purpose}_{article_id}",
                    overwrite=True,
                    resource_type="image"
                )

                cloudinary_urls[purpose] = result["secure_url"]
                print(f"   ✅ Uploaded {purpose}")

            except Exception as e:
                print(f"   ❌ Upload failed {purpose}: {e}")
                cloudinary_urls[purpose] = None
        else:
            cloudinary_urls[purpose] = None

    return cloudinary_urls


async def save_images_to_db(article_id: str, images: dict, conn):
    """Save images to both JSONB and legacy tables"""
    print(f"💾 Saving images to database...")

    async with conn.cursor() as cur:
        # Update JSONB column
        await cur.execute(
            """
            UPDATE articles
            SET images = %(images)s
            WHERE id = %(article_id)s
            """,
            {"article_id": article_id, "images": Json(images)}
        )

        # Save to legacy tables
        for role, cloudinary_url in images.items():
            if cloudinary_url:
                try:
                    # Extract public_id from Cloudinary URL
                    url_parts = cloudinary_url.split('/upload/')
                    if len(url_parts) == 2:
                        path_parts = url_parts[1].split('/', 1)
                        if len(path_parts) == 2:
                            public_id = path_parts[1].rsplit('.', 1)[0]
                        else:
                            public_id = url_parts[1].rsplit('.', 1)[0]
                    else:
                        public_id = f"quest-articles/{role}_{article_id}"

                    # Insert into images table
                    await cur.execute(
                        """
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
                        """,
                        {
                            "cloudinary_url": cloudinary_url,
                            "cloudinary_public_id": public_id,
                            "tags": [str(article_id), role, "auto-generated"]
                        }
                    )

                    image_result = await cur.fetchone()
                    image_id = image_result[0] if image_result else None

                    if image_id:
                        # Insert into article_image_usage table
                        await cur.execute(
                            """
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
                            """,
                            {
                                "article_id": article_id,
                                "image_id": image_id,
                                "role": role,
                                "alt_text": f"Article - {role} image"
                            }
                        )
                        print(f"   ✅ Saved {role} image to database")

                except Exception as e:
                    print(f"   ❌ Failed to save {role} image: {e}")

        await conn.commit()


async def main():
    print("=" * 80)
    print("🎨 GENERATING IMAGES FOR SPECIFIC ARTICLES")
    print("=" * 80)

    # Connect to database
    conn = await psycopg.AsyncConnection.connect(
        os.getenv("DATABASE_URL"),
        row_factory=dict_row
    )

    try:
        for slug in ARTICLES_TO_FIX:
            print(f"\n📄 Processing article: {slug}")

            # Get article
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, title, article_angle
                    FROM articles
                    WHERE slug = %s AND app = 'placement'
                    """,
                    (slug,)
                )
                article = await cur.fetchone()

            if not article:
                print(f"   ❌ Article not found: {slug}")
                continue

            print(f"   Title: {article['title']}")
            print(f"   Angle: {article['article_angle']}")

            # Generate images
            images = await generate_placement_images(
                str(article['id']),
                article['title'],
                article['article_angle'] or article['title']
            )

            # Save to database
            if any(images.values()):
                await save_images_to_db(str(article['id']), images, conn)
                print(f"✅ Completed: {slug}")
            else:
                print(f"❌ No images generated for: {slug}")

            # Rate limit between articles
            await asyncio.sleep(5)

        print("\n" + "=" * 80)
        print("✅ ALL DONE!")
        print("=" * 80)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
