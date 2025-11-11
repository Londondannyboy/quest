#!/usr/bin/env python3
"""Check the database schema for images and article_image_usage tables"""

import os
import asyncio
import psycopg
from dotenv import load_dotenv

load_dotenv()

async def main():
    database_url = os.getenv("DATABASE_URL")

    async with await psycopg.AsyncConnection.connect(database_url) as conn:
        async with conn.cursor() as cur:
            # Check images table
            print("=" * 60)
            print("IMAGES TABLE SCHEMA")
            print("=" * 60)
            await cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'images'
                ORDER BY ordinal_position
            """)
            rows = await cur.fetchall()
            for row in rows:
                print(f"  {row[0]:20s} {row[1]:20s} NULL:{row[2]:3s} DEFAULT:{row[3] or 'None'}")

            print("\n")

            # Check article_image_usage table
            print("=" * 60)
            print("ARTICLE_IMAGE_USAGE TABLE SCHEMA")
            print("=" * 60)
            await cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'article_image_usage'
                ORDER BY ordinal_position
            """)
            rows = await cur.fetchall()
            for row in rows:
                print(f"  {row[0]:20s} {row[1]:20s} NULL:{row[2]:3s} DEFAULT:{row[3] or 'None'}")

            print("\n")

            # Show an example from images table
            print("=" * 60)
            print("SAMPLE IMAGE RECORD")
            print("=" * 60)
            await cur.execute("SELECT * FROM images LIMIT 1")
            rows = await cur.fetchall()
            colnames = [desc[0] for desc in cur.description]
            if rows:
                for i, col in enumerate(colnames):
                    print(f"  {col}: {rows[0][i]}")

            print("\n")

            # Show an example from article_image_usage
            print("=" * 60)
            print("SAMPLE ARTICLE_IMAGE_USAGE RECORD")
            print("=" * 60)
            await cur.execute("SELECT * FROM article_image_usage LIMIT 1")
            rows = await cur.fetchall()
            colnames = [desc[0] for desc in cur.description]
            if rows:
                for i, col in enumerate(colnames):
                    print(f"  {col}: {rows[0][i]}")

if __name__ == "__main__":
    asyncio.run(main())
