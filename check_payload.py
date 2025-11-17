#!/usr/bin/env python3
import os
import json
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://neondb_owner:npg_LjBNF17HSTix@ep-green-smoke-ab3vtnw9-pooler.eu-west-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT payload
        FROM companies 
        WHERE slug = 'firstavenue' 
        ORDER BY created_at DESC 
        LIMIT 1
    """))
    
    row = result.fetchone()
    if row:
        payload = row[0]
        print(json.dumps(payload, indent=2))
