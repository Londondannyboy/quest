#!/usr/bin/env python3
"""Verify Campbell Lutyens was saved"""

import asyncio
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

async def verify():
    database_url = os.getenv("DATABASE_URL")

    async with await psycopg.AsyncConnection.connect(database_url) as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT
                    id, name, slug, type, company_type,
                    description, headquarters, website_url,
                    logo_url, specializations, created_at
                FROM companies
                WHERE name LIKE '%Campbell%'
                ORDER BY created_at DESC
                LIMIT 1
            """)

            result = await cur.fetchone()
            if result:
                print("✅ Campbell Lutyens found in database!")
                print(f"\n📋 Company Record:")
                print(f"  ID: {result[0]}")
                print(f"  Name: {result[1]}")
                print(f"  Slug: {result[2]}")
                print(f"  Type: {result[3]}")
                print(f"  Company Type: {result[4]}")
                print(f"  Description: {result[5][:100]}...")
                print(f"  HQ: {result[6]}")
                print(f"  Website: {result[7]}")
                print(f"  Logo: {result[8][:60] if result[8] else 'None'}...")
                print(f"  Specializations: {result[9]}")
                print(f"  Created: {result[10]}")
            else:
                print("❌ Campbell Lutyens not found")

if __name__ == "__main__":
    asyncio.run(verify())
