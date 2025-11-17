#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://neondb_owner:npg_LjBNF17HSTix@ep-green-smoke-ab3vtnw9-pooler.eu-west-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # First get table structure
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'companies'
        ORDER BY ordinal_position
    """))
    
    print("Companies table columns:")
    for row in result:
        print(f"  - {row[0]}: {row[1]}")
    
    print("\n" + "="*60 + "\n")
    
    # Then get the company
    result2 = conn.execute(text("""
        SELECT id, name, slug, featured_image_url, hero_image_url
        FROM companies 
        WHERE slug = 'firstavenue' 
        ORDER BY created_at DESC 
        LIMIT 1
    """))
    
    row = result2.fetchone()
    if row:
        print(f"Company found:")
        print(f"  ID: {row[0]}")
        print(f"  Name: {row[1]}")
        print(f"  Slug: {row[2]}")
        print(f"  Featured: {row[3]}")
        print(f"  Hero: {row[4]}")
