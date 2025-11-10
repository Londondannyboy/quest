#!/usr/bin/env python3
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

cur.execute("""
    SELECT slug, title, images
    FROM articles
    WHERE slug = 'barclays-expands-apac-investment-banking'
    ORDER BY created_at DESC
    LIMIT 1
""")

row = cur.fetchone()
if row:
    slug, title, images = row
    print(f"Slug: {slug}")
    print(f"Title: {title}")
    print(f"Images JSON: {images}")
else:
    print("Article not found")

cur.close()
conn.close()
