#!/usr/bin/env python3
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

print("Adding images column to articles table...")

cur.execute("""
    ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS images JSONB DEFAULT '{}'::jsonb
""")

conn.commit()

print("✅ Column added successfully")

# Verify
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'articles' AND column_name = 'images'
""")

row = cur.fetchone()
if row:
    print(f"✅ Verified: {row[0]} ({row[1]})")
else:
    print("❌ Column not found")

cur.close()
conn.close()
