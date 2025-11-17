#!/usr/bin/env python3
import os
import asyncio
from temporalio import activity
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            id, name, domain, 
            featured_image_url, hero_image_url,
            payload->'profile_sections' as sections,
            payload->'section_count' as section_count,
            payload->'total_content_length' as content_length
        FROM companies 
        WHERE domain = 'firstavenue' 
        ORDER BY created_at DESC 
        LIMIT 1
    """))
    
    row = result.fetchone()
    if row:
        print(f"ID: {row[0]}")
        print(f"Name: {row[1]}")
        print(f"Domain: {row[2]}")
        print(f"Featured Image: {row[3]}")
        print(f"Hero Image: {row[4]}")
        print(f"Sections: {row[5]}")
        print(f"Section Count: {row[6]}")
        print(f"Content Length: {row[7]}")
