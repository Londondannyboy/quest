#!/usr/bin/env python3
"""
Deep Job Scraper - Gets FULL job details by visiting individual job pages
Uses Crawl4AI to extract complete job descriptions, requirements, and benefits
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


class DeepJobScraper:
    """Scrapes individual job pages for full details"""
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.crawl4ai_url = "https://crawl4ai-production-6e85.up.railway.app"
    
    async def get_jobs_without_descriptions(self, limit: int = 10) -> List[Dict]:
        """Get jobs that don't have descriptions yet"""
        conn = await asyncpg.connect(self.db_url)
        try:
            query = """
                SELECT id, title, url, company_name 
                FROM jobs 
                WHERE is_active = true 
                AND description_snippet IS NULL
                AND url IS NOT NULL
                ORDER BY posted_date DESC
                LIMIT $1
            """
            rows = await conn.fetch(query, limit)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def scrape_job_page(self, job_url: str) -> Dict[str, Any]:
        """Scrape a single job page for full details"""
        print(f"  🔍 Scraping job page: {job_url}")
        
        async with httpx.AsyncClient(timeout=30) as client:
            # Use Crawl4AI to get the job page
            response = await client.post(
                f"{self.crawl4ai_url}/scrape",
                json={"url": job_url}
            )
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if not data.get("success"):
                return {"success": False, "error": "Scraping failed"}
            
            content = data.get("markdown", "")
            
            # Extract job details from markdown
            job_details = self.extract_job_details(content)
            job_details["success"] = True
            job_details["url"] = job_url
            
            return job_details
    
    def extract_job_details(self, content: str) -> Dict[str, Any]:
        """Extract structured job details from markdown content"""
        
        # Initialize details
        details = {
            "full_description": "",
            "requirements": [],
            "responsibilities": [],
            "benefits": [],
            "qualifications": [],
            "salary_info": None,
            "application_deadline": None,
            "job_type": None,
            "experience_level": None
        }
        
        if not content:
            return details
        
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        # Keywords to identify sections
        section_keywords = {
            "requirements": ["requirements", "required", "you will need", "must have"],
            "responsibilities": ["responsibilities", "what you'll do", "you will", "duties"],
            "benefits": ["benefits", "perks", "what we offer", "compensation"],
            "qualifications": ["qualifications", "nice to have", "preferred", "ideal"],
            "about": ["about the role", "about this position", "overview", "description"]
        }
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if this line starts a new section
            for section, keywords in section_keywords.items():
                if any(keyword in line_lower for keyword in keywords):
                    # Save previous section
                    if current_section and current_content:
                        if current_section in ["requirements", "responsibilities", "benefits", "qualifications"]:
                            details[current_section] = current_content
                        elif current_section == "about":
                            details["full_description"] = '\n'.join(current_content)
                    
                    current_section = section
                    current_content = []
                    break
            else:
                # Add line to current section
                if line.strip():
                    # Check for salary information
                    if any(term in line_lower for term in ["salary", "$", "compensation", "pay"]):
                        if "$" in line or any(c.isdigit() for c in line):
                            details["salary_info"] = line.strip()
                    
                    # Check for experience level
                    if any(term in line_lower for term in ["senior", "junior", "mid-level", "entry", "staff", "principal"]):
                        if not details["experience_level"]:
                            for term in ["Senior", "Junior", "Mid-level", "Entry", "Staff", "Principal"]:
                                if term.lower() in line_lower:
                                    details["experience_level"] = term
                                    break
                    
                    current_content.append(line.strip())
        
        # Save last section
        if current_section and current_content:
            if current_section in ["requirements", "responsibilities", "benefits", "qualifications"]:
                details[current_section] = current_content
            elif current_section == "about":
                details["full_description"] = '\n'.join(current_content)
        
        # If no structured description found, use the first 500 chars
        if not details["full_description"] and content:
            details["full_description"] = content[:2000]
        
        # Create a summary snippet (first 500 chars of description)
        details["snippet"] = details["full_description"][:500] if details["full_description"] else ""
        
        return details
    
    async def update_job_in_db(self, job_id: str, details: Dict[str, Any]):
        """Update job in database with scraped details"""
        conn = await asyncpg.connect(self.db_url)
        try:
            # Prepare data for storage
            description_snippet = details.get("snippet", "")[:500]  # Limit to 500 chars
            
            # Store full details in raw_data JSON field
            raw_data = {
                "full_description": details.get("full_description"),
                "requirements": details.get("requirements", []),
                "responsibilities": details.get("responsibilities", []),
                "benefits": details.get("benefits", []),
                "qualifications": details.get("qualifications", []),
                "salary_info": details.get("salary_info"),
                "experience_level": details.get("experience_level"),
                "scraped_at": datetime.now().isoformat()
            }
            
            # Update the job record
            await conn.execute("""
                UPDATE jobs 
                SET description_snippet = $2,
                    raw_data = COALESCE(raw_data, '{}'::jsonb) || $3::jsonb,
                    updated_date = $4
                WHERE id = $1
            """, job_id, description_snippet, json.dumps(raw_data), datetime.now())
            
        finally:
            await conn.close()
    
    async def scrape_all_missing_descriptions(self, batch_size: int = 5):
        """Scrape descriptions for all jobs missing them"""
        
        while True:
            # Get batch of jobs without descriptions
            jobs = await self.get_jobs_without_descriptions(batch_size)
            
            if not jobs:
                print("✅ All jobs have descriptions!")
                break
            
            print(f"\n📚 Scraping {len(jobs)} job descriptions...")
            print("-" * 60)
            
            for job in jobs:
                print(f"\n{job['company_name']}: {job['title']}")
                
                # Scrape the job page
                details = await self.scrape_job_page(job['url'])
                
                if details.get("success"):
                    # Update database
                    await self.update_job_in_db(job['id'], details)
                    
                    # Show what we found
                    print(f"  ✅ Scraped successfully!")
                    if details.get("salary_info"):
                        print(f"  💰 Salary: {details['salary_info']}")
                    if details.get("experience_level"):
                        print(f"  📊 Level: {details['experience_level']}")
                    if details.get("requirements"):
                        print(f"  📋 Requirements: {len(details['requirements'])} items")
                    if details.get("benefits"):
                        print(f"  🎁 Benefits: {len(details['benefits'])} items")
                    
                    snippet = details.get("snippet", "")[:150]
                    if snippet:
                        print(f"  📝 Snippet: {snippet}...")
                else:
                    print(f"  ❌ Failed: {details.get('error', 'Unknown error')}")
                
                # Small delay to be respectful
                await asyncio.sleep(1)
            
            print(f"\nBatch complete. Checking for more jobs...")


async def demonstrate_deep_scraping():
    """Show the difference between list scraping and deep scraping"""
    
    print("\n" + "="*80)
    print("DEEP JOB SCRAPING DEMONSTRATION")
    print("="*80)
    
    print("""
    🔍 CURRENT SITUATION:
    - We have 82 jobs from Clay Labs and Lovable
    - But we only have basic info (title, department, location)
    - Description snippets are ALL NULL
    - We haven't visited individual job pages
    
    📊 WHAT WE'RE MISSING:
    - Full job descriptions (responsibilities, day-to-day)
    - Requirements and qualifications
    - Benefits and perks
    - Salary information
    - Application instructions
    - Company culture details
    
    🚀 WHAT DEEP SCRAPING WILL GET US:
    """)
    
    # Scrape a few jobs to demonstrate
    scraper = DeepJobScraper()
    
    # Get first 3 jobs to demonstrate
    jobs = await scraper.get_jobs_without_descriptions(3)
    
    if jobs:
        print(f"\n  Demonstrating with {len(jobs)} jobs...")
        print("-" * 60)
        
        for job in jobs:
            print(f"\n  Job: {job['title']} at {job['company_name']}")
            details = await scraper.scrape_job_page(job['url'])
            
            if details.get("success"):
                await scraper.update_job_in_db(job['id'], details)
                print(f"    ✅ Successfully scraped full details!")
            
            await asyncio.sleep(1)
    
    print("\n" + "="*80)
    print("DEEP SCRAPING COMPLETE")
    print("="*80)


async def main():
    """Main function to run deep scraping"""
    
    # First show the demonstration
    await demonstrate_deep_scraping()
    
    # Then ask if user wants to scrape all
    print("\n" + "="*80)
    print("Ready to deep scrape ALL 82 jobs?")
    print("This will visit each job page and extract full details.")
    print("Estimated time: ~2 minutes")
    print("="*80)
    
    # For now, just scrape first 10 as example
    scraper = DeepJobScraper()
    await scraper.scrape_all_missing_descriptions(batch_size=10)


if __name__ == "__main__":
    asyncio.run(main())