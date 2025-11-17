#!/usr/bin/env python3
import os
import json
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://neondb_owner:npg_LjBNF17HSTix@ep-green-smoke-ab3vtnw9-pooler.eu-west-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Get Evercore
    result1 = conn.execute(text("""
        SELECT 
            id, name, 
            payload->'section_count' as sections,
            payload->'total_content_length' as content_length,
            payload->'data_completeness_score' as completeness,
            created_at
        FROM companies 
        WHERE slug LIKE '%evercore%'
        ORDER BY created_at DESC 
        LIMIT 1
    """))
    
    evercore = result1.fetchone()
    
    # Get First Avenue
    result2 = conn.execute(text("""
        SELECT 
            id, name,
            payload->'section_count' as sections,
            payload->'total_content_length' as content_length,
            payload->'data_completeness_score' as completeness,
            created_at
        FROM companies 
        WHERE slug = 'firstavenue'
        ORDER BY created_at DESC 
        LIMIT 1
    """))
    
    firstavenue = result2.fetchone()
    
    print("COMPARISON:")
    print("=" * 60)
    if evercore:
        print(f"✅ Evercore:")
        print(f"   Sections: {evercore[2]}")
        print(f"   Content Length: {evercore[3]}")
        print(f"   Completeness: {evercore[4]}%")
        print(f"   Created: {evercore[5]}")
    else:
        print("❌ Evercore not found")
    
    print()
    
    if firstavenue:
        print(f"❌ First Avenue:")
        print(f"   Sections: {firstavenue[2]}")
        print(f"   Content Length: {firstavenue[3]}")
        print(f"   Completeness: {firstavenue[4]}%")
        print(f"   Created: {firstavenue[5]}")
    else:
        print("❌ First Avenue not found")
