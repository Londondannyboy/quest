#!/usr/bin/env python3
"""
Job Scraper v2 - Uses Crawl4AI v5.0 with URL discovery
Demonstrates the new multi-page crawling capabilities
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncpg
from dotenv import load_dotenv

load_dotenv()


class JobScraperV2:
    """Enhanced job scraper using Crawl4AI v5.0 features"""
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.crawl4ai_url = "https://crawl4ai-production-6e85.up.railway.app"
    
    async def discover_and_scrape(self, board_url: str, company_name: str):
        """
        Use the new /discover endpoint to find all job URLs
        Then use /crawl-many to get details (if needed)
        """
        print(f"\n{'='*60}")
        print(f"DISCOVERING JOBS: {company_name}")
        print(f"{'='*60}")
        
        async with httpx.AsyncClient(timeout=60) as client:
            # Step 1: Discover all job URLs
            print(f"🔍 Discovering job URLs...")
            discovery_response = await client.post(
                f"{self.crawl4ai_url}/discover",
                json={
                    "url": board_url,
                    "max_urls": 100
                }
            )
            
            if discovery_response.status_code != 200:
                print(f"❌ Discovery failed: {discovery_response.status_code}")
                return []
            
            discovery_data = discovery_response.json()
            
            if not discovery_data.get("success"):
                print(f"❌ Discovery failed: {discovery_data.get('error')}")
                return []
            
            job_urls = discovery_data.get("urls", [])
            print(f"✅ Found {len(job_urls)} job postings!")
            
            # For Ashby boards, the discovery gives us the job URLs and titles
            # We already have the basic info from discovery
            jobs = []
            for url_info in job_urls:
                job = {
                    'external_id': url_info['url'].split('/')[-1],  # Extract ID from URL
                    'title': url_info['title'],
                    'url': url_info['url'],
                    'company_name': company_name,
                    'department': '',  # Would need to crawl individual pages
                    'location': '',  # Would need to crawl individual pages
                    'description_snippet': None  # Would need to crawl individual pages
                }
                jobs.append(job)
                print(f"  • {job['title']}")
            
            # Optional: If we wanted full descriptions, we'd use /crawl-many here
            # For now, we're demonstrating the discovery capability
            
            return jobs
    
    async def update_database_with_jobs(self, board_id: str, jobs: List[Dict]):
        """Store discovered jobs in database"""
        if not jobs:
            return
        
        conn = await asyncpg.connect(self.db_url)
        try:
            # Mark existing jobs as inactive
            await conn.execute(
                "UPDATE jobs SET is_active = false WHERE board_id = $1",
                board_id
            )
            
            # Insert new jobs
            for job in jobs:
                await conn.execute("""
                    INSERT INTO jobs (
                        board_id, external_id, title, department, 
                        location, url, company_name, is_active
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (board_id, external_id) 
                    DO UPDATE SET 
                        title = EXCLUDED.title,
                        is_active = true,
                        updated_date = CURRENT_TIMESTAMP
                """, board_id, job['external_id'], job['title'], 
                    job.get('department', ''), job.get('location', ''),
                    job['url'], job['company_name'], True)
            
            print(f"✅ Stored {len(jobs)} jobs in database")
        finally:
            await conn.close()
    
    async def demonstrate_new_features(self):
        """Show the new Crawl4AI v5.0 capabilities"""
        print("\n" + "="*80)
        print("CRAWL4AI v5.0 DEMONSTRATION")
        print("="*80)
        print("""
        NEW FEATURES IN ACTION:
        
        1. URL DISCOVERY (/discover endpoint)
           - Automatically finds all job URLs from a board
           - Extracts job IDs and titles
           - No manual URL construction needed
        
        2. MULTI-PAGE CRAWLING (/crawl-many endpoint)
           - Could crawl all job pages in parallel
           - Get full descriptions efficiently
           - Built-in rate limiting
        
        Let's discover jobs from multiple boards...
        """)
        
        # Get board info from database
        conn = await asyncpg.connect(self.db_url)
        try:
            boards = await conn.fetch("""
                SELECT id, company_name, url 
                FROM job_boards 
                WHERE is_active = true 
                AND board_type = 'ashby'
                LIMIT 3
            """)
            
            for board in boards:
                jobs = await self.discover_and_scrape(
                    board['url'], 
                    board['company_name']
                )
                
                await self.update_database_with_jobs(board['id'], jobs)
                
                # Record scrape history
                await conn.execute("""
                    INSERT INTO scrape_history (board_id, status, jobs_found)
                    VALUES ($1, 'success', $2)
                """, board['id'], len(jobs))
                
                await asyncio.sleep(2)  # Be respectful between boards
            
        finally:
            await conn.close()
        
        print("\n" + "="*80)
        print("DISCOVERY COMPLETE!")
        print("="*80)
        print("""
        ✅ Successfully demonstrated URL discovery
        ✅ Found and stored job URLs with titles
        ✅ Ready for full crawling with /crawl-many when needed
        
        Next step would be to use /crawl-many to get full job descriptions
        for all discovered URLs in parallel!
        """)


async def main():
    """Run the v2 scraper demonstration"""
    scraper = JobScraperV2()
    await scraper.demonstrate_new_features()


if __name__ == "__main__":
    asyncio.run(main())