#!/usr/bin/env python3
"""
Smart Job Scraper using Crawl4AI's native multi-page crawling
Uses sitemap discovery and pattern matching to find and crawl job detail pages
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


class SmartJobScraper:
    """Uses Crawl4AI's multi-page crawling to scrape job boards intelligently"""
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.crawl4ai_url = "https://crawl4ai-production-6e85.up.railway.app"
    
    async def discover_job_urls(self, board_url: str) -> Dict[str, Any]:
        """
        Use Crawl4AI to discover all job URLs from a board
        This would use sitemap discovery or pattern-based crawling
        """
        print(f"🔍 Discovering job URLs from: {board_url}")
        
        async with httpx.AsyncClient(timeout=30) as client:
            # First, get the main page and extract job links
            response = await client.post(
                f"{self.crawl4ai_url}/crawl",
                json={
                    "url": board_url,
                    "max_pages": 1  # Get the main page first
                }
            )
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if not data.get("success"):
                return {"success": False, "error": "Discovery failed"}
            
            # Extract job URLs from the response
            job_urls = []
            
            # For Ashby boards, we can extract job URLs from the data
            if "ashbyhq.com" in board_url:
                # The jobs are embedded in the page, extract URLs
                pages = data.get("pages", [])
                if pages:
                    content = pages[0].get("content", "")
                    # Parse for job URLs (simplified - in reality would parse the JSON)
                    # Ashby job URLs follow pattern: /jobs.ashbyhq.com/{company}/{job-id}
                    import re
                    # Extract job IDs from content
                    # This is simplified - we'd need to parse the actual structure
                    print(f"  Found main job listing page")
                    
                    # In a real implementation, we'd extract individual job URLs here
                    # For now, we'll return the discovered structure
            
            return {
                "success": True,
                "board_url": board_url,
                "job_urls": job_urls,
                "main_page_data": data
            }
    
    async def crawl_multiple_jobs(self, job_urls: List[str]) -> List[Dict[str, Any]]:
        """
        Use Crawl4AI's multi-URL crawling to scrape multiple job pages
        This would use arun_many() in the actual Crawl4AI implementation
        """
        print(f"🕷️ Crawling {len(job_urls)} job pages...")
        
        results = []
        
        # In the actual implementation, this would be a single call to arun_many()
        # For our service, we'll need to implement batch processing
        async with httpx.AsyncClient(timeout=60) as client:
            # Batch request to crawl multiple URLs
            response = await client.post(
                f"{self.crawl4ai_url}/crawl-batch",  # Hypothetical endpoint
                json={
                    "urls": job_urls,
                    "pattern": "*/jobs/*",  # Pattern matching for job pages
                    "extract_details": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
        
        return results
    
    async def smart_scrape_ashby_board(self, board_url: str, company_name: str):
        """
        Smart scraping approach:
        1. Use Crawl4AI to get the main page
        2. Extract all job URLs from the embedded data
        3. Use multi-URL crawling to get all job details
        """
        print(f"\n{'='*60}")
        print(f"SMART SCRAPING: {company_name}")
        print(f"{'='*60}")
        
        # Step 1: Discover job URLs
        discovery = await self.discover_job_urls(board_url)
        
        if not discovery.get("success"):
            print(f"❌ Discovery failed: {discovery.get('error')}")
            return
        
        # Step 2: Extract job information from the main page
        # For Ashby, all data is in the main page already
        main_data = discovery.get("main_page_data", {})
        pages = main_data.get("pages", [])
        
        if pages:
            content = pages[0].get("content", "")
            print(f"  ✅ Got main page content: {len(content)} chars")
            
            # Parse the content to extract job listings
            jobs = self.extract_jobs_from_content(content, company_name)
            print(f"  📊 Found {len(jobs)} jobs in listing")
            
            # Step 3: For each job, we could crawl the detail page
            # But for Ashby, the data is already complete in the listing
            if jobs and not self.has_full_descriptions(jobs):
                print(f"  🔍 Jobs need deep crawling for full descriptions")
                # Here we would use arun_many() to crawl all job detail pages
                # job_urls = [job['url'] for job in jobs]
                # detailed_jobs = await self.crawl_multiple_jobs(job_urls)
            else:
                print(f"  ✅ Jobs already have complete data")
            
            return jobs
        
        return []
    
    def extract_jobs_from_content(self, content: str, company_name: str) -> List[Dict]:
        """Extract job data from page content"""
        jobs = []
        
        # Parse content looking for job listings
        # This is simplified - actual parsing would be more sophisticated
        lines = content.split('\n')
        
        current_job = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for job titles (simplified pattern matching)
            if any(keyword in line.lower() for keyword in ['engineer', 'designer', 'manager', 'analyst', 'developer']):
                if current_job:
                    jobs.append(current_job)
                
                current_job = {
                    'title': line.split('-')[0].strip() if '-' in line else line,
                    'company': company_name,
                    'department': '',
                    'location': '',
                    'description': ''
                }
            elif current_job:
                # Add details to current job
                if any(loc in line for loc in ['Remote', 'NY', 'SF', 'London']):
                    current_job['location'] = line
                elif any(dept in line.lower() for dept in ['engineering', 'design', 'product', 'sales']):
                    current_job['department'] = line
        
        if current_job:
            jobs.append(current_job)
        
        return jobs
    
    def has_full_descriptions(self, jobs: List[Dict]) -> bool:
        """Check if jobs have full descriptions or just snippets"""
        if not jobs:
            return False
        
        # Check if any job has a substantial description
        for job in jobs:
            desc = job.get('description', '')
            if len(desc) > 500:  # Arbitrary threshold for "full" description
                return True
        
        return False
    
    async def demonstrate_smart_approach(self):
        """Demonstrate the smart scraping approach"""
        
        print("\n" + "="*80)
        print("SMART JOB SCRAPING WITH CRAWL4AI")
        print("="*80)
        
        print("""
        🎯 TRADITIONAL APPROACH (what we've been doing):
        1. Scrape the job listing page
        2. Extract basic job info
        3. Store in database
        4. Later, manually visit each job URL for details
        
        🚀 SMART CRAWL4AI APPROACH:
        1. Use sitemap discovery or pattern matching to find all job URLs
        2. Use arun_many() to crawl multiple pages in parallel
        3. Extract full details from each job page efficiently
        4. Store complete data in one operation
        
        📊 BENEFITS:
        - Single operation instead of multiple rounds
        - Parallel processing for speed
        - Automatic URL discovery
        - Pattern-based filtering
        - Built-in rate limiting and error handling
        """)
        
        # Example with Clay Labs
        await self.smart_scrape_ashby_board(
            "https://jobs.ashbyhq.com/claylabs",
            "Clay Labs"
        )
        
        print("\n" + "="*80)
        print("KEY INSIGHT")
        print("="*80)
        print("""
        Instead of:
        1. Scraping job list → 2. Storing basic info → 3. Later scraping each job
        
        We should:
        1. Discover all URLs → 2. Crawl all pages at once → 3. Store complete data
        
        This is what Crawl4AI's multi-URL crawling is designed for!
        """)


async def main():
    """Main function to demonstrate smart scraping"""
    scraper = SmartJobScraper()
    await scraper.demonstrate_smart_approach()
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("""
    To fully implement this in our Crawl4AI service, we need to:
    
    1. Add a /discover endpoint for URL discovery
    2. Add a /crawl-many endpoint for multi-URL crawling
    3. Implement arun_many() with proper dispatchers
    4. Add pattern matching for job URLs
    5. Use sitemap discovery where available
    
    This would make our scraping much more efficient!
    """)


if __name__ == "__main__":
    asyncio.run(main())