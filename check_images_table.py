#!/usr/bin/env python3
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

print("Images table schema:")
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'images'
    ORDER BY ordinal_position
""")

for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\nSample images:")
cur.execute("SELECT id, article_id, image_type, url FROM images LIMIT 3")
for row in cur.fetchall():
    print(f"  {row}")

cur.close()
conn.close()
