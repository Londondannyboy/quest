#!/usr/bin/env python3
"""Check company_type constraint"""

import asyncio
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

async def check_constraint():
    database_url = os.getenv("DATABASE_URL")

    async with await psycopg.AsyncConnection.connect(database_url) as conn:
        async with conn.cursor() as cur:
            # Get constraint definition
            await cur.execute("""
                SELECT con.conname, pg_get_constraintdef(con.oid)
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                WHERE rel.relname = 'companies'
                AND con.contype = 'c'
                AND con.conname LIKE '%company_type%'
            """)

            result = await cur.fetchone()
            if result:
                print(f"Constraint: {result[0]}")
                print(f"Definition: {result[1]}")
            else:
                print("No company_type constraint found")

if __name__ == "__main__":
    asyncio.run(check_constraint())
