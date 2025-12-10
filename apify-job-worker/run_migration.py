#!/usr/bin/env python3
"""Run database migrations against Neon."""

import asyncio
import sys
import os
from dotenv import load_dotenv
import asyncpg
import logging

# Load environment
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def run_migrations():
    """Run all migrations in migrations/ directory."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("❌ DATABASE_URL not set")
        sys.exit(1)

    migrations_dir = "migrations"
    if not os.path.exists(migrations_dir):
        logger.error(f"❌ {migrations_dir}/ directory not found")
        sys.exit(1)

    # Get all SQL migration files in order
    migration_files = sorted([
        f for f in os.listdir(migrations_dir)
        if f.endswith('.sql')
    ])

    if not migration_files:
        logger.warning("⚠️  No migration files found")
        return

    try:
        conn = await asyncpg.connect(db_url)
        logger.info(f"✅ Connected to Neon database\n")

        for migration_file in migration_files:
            migration_path = os.path.join(migrations_dir, migration_file)
            logger.info(f"📝 Running migration: {migration_file}")

            with open(migration_path, 'r') as f:
                sql = f.read()

            try:
                # Execute the migration
                result = await conn.execute(sql)
                logger.info(f"   ✅ Migration complete\n")
            except Exception as e:
                logger.error(f"   ❌ Migration failed: {e}")
                await conn.close()
                sys.exit(1)

        await conn.close()
        logger.info("✅ All migrations completed successfully!")

    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_migrations())
