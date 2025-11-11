#!/usr/bin/env python3
"""Check companies table schema in Neon database"""

import asyncio
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

async def check_companies_table():
    database_url = os.getenv("DATABASE_URL")

    async with await psycopg.AsyncConnection.connect(database_url) as conn:
        async with conn.cursor() as cur:
            # Check if companies table exists
            await cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name = 'companies'
            """)

            result = await cur.fetchone()

            if result:
                print("✅ Companies table exists")
                print("\n📋 Table Schema:")

                # Get column info
                await cur.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'companies'
                    ORDER BY ordinal_position
                """)

                columns = await cur.fetchall()
                for col in columns:
                    nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
                    default = f"DEFAULT {col[3]}" if col[3] else ""
                    print(f"  - {col[0]}: {col[1]} {nullable} {default}")
            else:
                print("❌ Companies table does not exist")
                print("\nCreating companies table...")

                await cur.execute("""
                    CREATE TABLE companies (
                        id TEXT PRIMARY KEY,
                        company_name TEXT NOT NULL,
                        company_type TEXT NOT NULL,
                        website TEXT,
                        description TEXT,
                        industry TEXT,
                        headquarters_location TEXT,
                        logo_url TEXT,
                        profile_data JSONB,
                        completeness_score FLOAT,
                        status TEXT DEFAULT 'published',
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """)

                await conn.commit()
                print("✅ Companies table created successfully")

if __name__ == "__main__":
    asyncio.run(check_companies_table())
