#!/usr/bin/env python3
"""
Test scraping hcompany job board and add to Neon database
Uses our v6.0 Crawl4AI service with full detail extraction
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def test_hcompany():
    """Test the new hcompany board"""
    
    board_url = "https://jobs.ashbyhq.com/hcompany"
    crawl4ai_url = "https://crawl4ai-production-6e85.up.railway.app"
    db_url = os.getenv("DATABASE_URL")
    
    print("="*80)
    print("TESTING NEW JOB BOARD: hcompany")
    print("="*80)
    print(f"URL: {board_url}\n")
    
    async with httpx.AsyncClient(timeout=60) as client:
        # Step 1: Discover all job URLs
        print("🔍 STEP 1: Discovering job URLs...")
        discovery_response = await client.post(
            f"{crawl4ai_url}/discover",
            json={"url": board_url, "max_urls": 100}
        )
        
        if discovery_response.status_code != 200:
            print(f"❌ Discovery failed: {discovery_response.status_code}")
            return
        
        discovery_data = discovery_response.json()
        
        if not discovery_data.get("success"):
            print(f"❌ Discovery failed: {discovery_data.get('error')}")
            return
        
        job_urls = discovery_data.get("urls", [])
        print(f"✅ Found {len(job_urls)} jobs!\n")
        
        # Show discovered jobs
        print("📋 Discovered jobs:")
        for i, job_info in enumerate(job_urls[:10], 1):  # Show first 10
            print(f"  {i}. {job_info['title']}")
        if len(job_urls) > 10:
            print(f"  ... and {len(job_urls) - 10} more")
        
        # Step 2: Add company to database
        print("\n💾 STEP 2: Adding to database...")
        conn = await asyncpg.connect(db_url)
        
        try:
            # Add to job_boards
            board_id = await conn.fetchval("""
                INSERT INTO job_boards (company_name, url, board_type, is_active)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (company_name, url) 
                DO UPDATE SET is_active = true
                RETURNING id
            """, "hcompany", board_url, "ashby", True)
            
            print(f"✅ Added hcompany to job_boards (ID: {board_id})")
            
            # Step 3: Crawl a few job detail pages to test
            print("\n🕷️ STEP 3: Testing detail page extraction...")
            
            # Take first 3 jobs to test
            test_urls = [job['url'] for job in job_urls[:3]]
            
            if test_urls:
                print(f"Crawling {len(test_urls)} job pages for details...")
                
                crawl_response = await client.post(
                    f"{crawl4ai_url}/crawl-many",
                    json={
                        "urls": test_urls,
                        "parallel": 3,
                        "delay_between": 0.5
                    }
                )
                
                if crawl_response.status_code == 200:
                    crawl_data = crawl_response.json()
                    
                    if crawl_data.get("success"):
                        print(f"✅ Successfully crawled {crawl_data['successful']}/{len(test_urls)} pages\n")
                        
                        # Show extracted content
                        print("📝 Sample extracted content:")
                        for result in crawl_data.get("results", []):
                            if result.get("success") and result.get("content"):
                                print(f"\n  Job: {result.get('title', 'Unknown')}")
                                print(f"  Content length: {result['content_length']} chars")
                                
                                # Show first 500 chars of content
                                content = result['content']
                                if len(content) > 500:
                                    lines = content.split('\n')
                                    preview = []
                                    char_count = 0
                                    for line in lines:
                                        preview.append(line)
                                        char_count += len(line)
                                        if char_count > 500:
                                            break
                                    print("  Preview:")
                                    for line in preview[:10]:  # Max 10 lines
                                        if line.strip():
                                            print(f"    {line[:80]}")
            
            # Step 4: Add all jobs to database
            print("\n💾 STEP 4: Adding all jobs to database...")
            
            # Mark existing jobs as inactive
            await conn.execute(
                "UPDATE jobs SET is_active = false WHERE board_id = $1",
                board_id
            )
            
            # Insert all discovered jobs
            added_count = 0
            for job_info in job_urls:
                job_id = job_info['url'].split('/')[-1]  # Extract ID from URL
                await conn.execute("""
                    INSERT INTO jobs (
                        board_id, external_id, title, url, 
                        company_name, is_active, department, location
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (board_id, external_id) 
                    DO UPDATE SET 
                        title = EXCLUDED.title,
                        is_active = true,
                        updated_date = CURRENT_TIMESTAMP
                """, board_id, job_id, job_info['title'], job_info['url'], 
                    "hcompany", True, "", "")
                added_count += 1
            
            print(f"✅ Added {added_count} jobs to database")
            
            # Record scrape history
            await conn.execute("""
                INSERT INTO scrape_history (board_id, status, jobs_found)
                VALUES ($1, 'success', $2)
            """, board_id, added_count)
            
            # Final stats
            total_jobs = await conn.fetchval("""
                SELECT COUNT(*) FROM jobs WHERE is_active = true
            """)
            
            companies = await conn.fetchval("""
                SELECT COUNT(DISTINCT company_name) FROM jobs WHERE is_active = true
            """)
            
            print("\n" + "="*80)
            print("📊 UPDATED DATABASE STATS:")
            print("="*80)
            print(f"  • Total active jobs: {total_jobs}")
            print(f"  • Companies tracked: {companies}")
            print(f"  • New jobs from hcompany: {added_count}")
            
        finally:
            await conn.close()


async def main():
    await test_hcompany()


if __name__ == "__main__":
    asyncio.run(main())