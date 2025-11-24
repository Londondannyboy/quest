#!/usr/bin/env python3
"""
Simplify database structure - merge everything into jobs table
No need for separate tables or views
"""

import asyncio
import asyncpg
import json
import os
from dotenv import load_dotenv

load_dotenv()


async def simplify_database():
    """Merge job_details into jobs table and remove unnecessary complexity"""
    
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)
    
    try:
        print("🔧 SIMPLIFYING DATABASE STRUCTURE")
        print("="*60)
        
        # Add missing columns directly to jobs table
        new_columns = [
            ("full_description", "TEXT"),
            ("requirements", "TEXT[]"),
            ("responsibilities", "TEXT[]"),
            ("benefits", "TEXT[]"),
            ("qualifications", "TEXT[]"),
            ("nice_to_have", "TEXT[]"),
            ("about_team", "TEXT"),
            ("about_company", "TEXT"),
            ("skills_required", "TEXT[]"),
            ("seniority_level", "VARCHAR(50)"),
            ("role_category", "VARCHAR(100)")
        ]
        
        print("Adding columns to jobs table...")
        for column_name, column_type in new_columns:
            try:
                await conn.execute(f"""
                    ALTER TABLE jobs 
                    ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                """)
                print(f"  ✅ Added {column_name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  • {column_name} already exists")
                else:
                    print(f"  ❌ Error: {e}")
        
        # Copy data from job_details to jobs table if it exists
        try:
            print("\nMerging data from job_details into jobs table...")
            await conn.execute("""
                UPDATE jobs j
                SET 
                    full_description = jd.full_description,
                    requirements = jd.requirements,
                    responsibilities = jd.responsibilities,
                    benefits = jd.benefits,
                    qualifications = jd.qualifications,
                    about_team = jd.about_team,
                    about_company = jd.about_company
                FROM job_details jd
                WHERE j.id = jd.job_id
            """)
            
            count = await conn.fetchval("SELECT COUNT(*) FROM job_details")
            print(f"  ✅ Merged {count} records")
            
            # Drop the unnecessary tables/views
            print("\nCleaning up...")
            await conn.execute("DROP VIEW IF EXISTS job_listings")
            print("  ✅ Removed job_listings view")
            
            await conn.execute("DROP TABLE IF EXISTS job_details")
            print("  ✅ Removed job_details table")
            
        except Exception as e:
            print(f"  Note: {e}")
        
        # Show final structure
        print("\n📊 FINAL SIMPLIFIED STRUCTURE:")
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'jobs'
            ORDER BY ordinal_position
        """)
        
        print("\njobs table columns:")
        for col in columns:
            print(f"  • {col['column_name']}: {col['data_type']}")
        
        # Quick stats
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_jobs,
                COUNT(full_description) as with_full_desc,
                COUNT(CASE WHEN array_length(requirements, 1) > 0 THEN 1 END) as with_requirements,
                COUNT(CASE WHEN department != '' THEN 1 END) as with_department,
                COUNT(CASE WHEN location != '' THEN 1 END) as with_location
            FROM jobs
            WHERE is_active = true
        """)
        
        print(f"\n📈 Data completeness:")
        print(f"  Total jobs: {stats['total_jobs']}")
        print(f"  With full descriptions: {stats['with_full_desc']}")
        print(f"  With requirements: {stats['with_requirements']}")
        print(f"  With department: {stats['with_department']}")
        print(f"  With location: {stats['with_location']}")
        
        print("\n✅ Database simplified! Everything is now in the 'jobs' table.")
        
    finally:
        await conn.close()


async def main():
    await simplify_database()


if __name__ == "__main__":
    asyncio.run(main())