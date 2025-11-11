#!/usr/bin/env python3
"""
Extract logos and generate featured images for placement agent companies
"""
import asyncio
import os
import sys

# Add worker to path
worker_path = os.path.join(os.path.dirname(__file__), 'worker')
sys.path.insert(0, worker_path)

from activities.company import extract_company_logo, process_company_logo
from activities.images import generate_article_images
import psycopg

async def add_company_images():
    """Add logos and featured images to companies"""

    # Connect to database
    db_url = os.getenv("DATABASE_URL")
    conn = await psycopg.AsyncConnection.connect(db_url)

    # Get companies without logos
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT id, name, slug, website_url, description
            FROM companies
            WHERE company_type = 'placement_agent'
              AND status = 'published'
              AND logo_url IS NULL
            ORDER BY name
        """)
        companies = await cur.fetchall()

    print(f"Found {len(companies)} companies needing images\n")

    for company_id, name, slug, website_url, description in companies:
        print(f"Processing: {name}")
        print(f"Website: {website_url}")

        # Extract and process logo
        logo_url = None
        try:
            print("  Extracting logo...")
            logo_data = await extract_company_logo(website_url)

            if logo_data.get("logo_url"):
                print(f"  Found logo: {logo_data['logo_url']}")

                # Process and upload to Cloudinary
                cloudinary_url = await process_company_logo({
                    "company_id": company_id,
                    "company_name": name,
                    "company_type": "placement_agent",
                    "logo_data": logo_data
                })

                logo_url = cloudinary_url
                print(f"  ✅ Logo uploaded: {logo_url}")
            else:
                print("  ⚠️  No logo found")
        except Exception as e:
            print(f"  ❌ Logo extraction failed: {e}")

        # Generate featured image
        header_image_url = None
        try:
            print("  Generating featured image...")

            # Use image generation with company description
            prompt = f"Professional abstract business image for {name}, a placement agent firm. Modern, clean, corporate aesthetic with blue and white tones."

            images = await generate_article_images({
                "article_id": company_id,
                "title": name,
                "content": description or f"{name} - Placement Agent",
                "angle": "Corporate Profile",
                "app": "placement"
            })

            if images.get("featured"):
                header_image_url = images["featured"]
                print(f"  ✅ Featured image generated: {header_image_url}")
            else:
                print("  ⚠️  Featured image generation failed")

        except Exception as e:
            print(f"  ❌ Featured image generation failed: {e}")

        # Update database
        if logo_url or header_image_url:
            async with conn.cursor() as cur:
                if logo_url and header_image_url:
                    await cur.execute("""
                        UPDATE companies
                        SET logo_url = %s, header_image_url = %s
                        WHERE id = %s
                    """, (logo_url, header_image_url, company_id))
                elif logo_url:
                    await cur.execute("""
                        UPDATE companies
                        SET logo_url = %s
                        WHERE id = %s
                    """, (logo_url, company_id))
                elif header_image_url:
                    await cur.execute("""
                        UPDATE companies
                        SET header_image_url = %s
                        WHERE id = %s
                    """, (header_image_url, company_id))

                await conn.commit()
                print(f"  💾 Database updated\n")
        else:
            print(f"  ⚠️  No images to update\n")

    await conn.close()
    print("\n✅ All companies processed!")

if __name__ == "__main__":
    asyncio.run(add_company_images())
