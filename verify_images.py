#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://neondb_owner:npg_LjBNF17HSTix@ep-green-smoke-ab3vtnw9-pooler.eu-west-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            id, name, slug,
            featured_image_url,
            hero_image_url,
            logo_url
        FROM companies 
        WHERE slug = 'firstavenue'
        ORDER BY created_at DESC 
        LIMIT 1
    """))
    
    row = result.fetchone()
    if row:
        print(f"Company: {row[1]}")
        print(f"Slug: {row[2]}")
        print(f"\n✅ Image URLs in database:")
        print(f"  Logo: {row[5]}")
        print(f"  Featured: {row[3]}")
        print(f"  Hero: {row[4]}")
        
        # Check if URLs are valid
        for name, url in [("Logo", row[5]), ("Featured", row[3]), ("Hero", row[4])]:
            if url:
                print(f"\n{name} URL valid: ✅")
            else:
                print(f"\n{name} URL missing: ❌")
