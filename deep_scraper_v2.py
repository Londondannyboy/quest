#!/usr/bin/env python3
"""
Deep Scraper v2 - Uses Crawl4AI v5.0 /crawl-many for parallel job scraping
Gets FULL job details by crawling all job pages at once
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


class DeepScraperV2:
    """Uses Crawl4AI v5.0 to deeply scrape all jobs in parallel"""
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.crawl4ai_url = "https://crawl4ai-production-6e85.up.railway.app"
    
    async def get_jobs_needing_details(self, limit: int = 100) -> List[Dict]:
        """Get all jobs that need full descriptions"""
        conn = await asyncpg.connect(self.db_url)
        try:
            query = """
                SELECT id, title, url, company_name, department, location
                FROM jobs 
                WHERE is_active = true 
                AND (description_snippet IS NULL OR description_snippet = '')
                AND url IS NOT NULL
                ORDER BY company_name, title
                LIMIT $1
            """
            rows = await conn.fetch(query, limit)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def show_current_state(self):
        """Show what we currently have in the database"""
        conn = await asyncpg.connect(self.db_url)
        try:
            # Get summary statistics
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN description_snippet IS NOT NULL AND description_snippet != '' THEN 1 END) as jobs_with_descriptions,
                    COUNT(DISTINCT company_name) as companies
                FROM jobs 
                WHERE is_active = true
            """)
            
            print("\n" + "="*80)
            print("CURRENT DATABASE STATE")
            print("="*80)
            print(f"📊 Total active jobs: {stats['total_jobs']}")
            print(f"📝 Jobs with descriptions: {stats['jobs_with_descriptions']}")
            print(f"🏢 Companies: {stats['companies']}")
            print(f"❌ Missing descriptions: {stats['total_jobs'] - stats['jobs_with_descriptions']}")
            
            # Show sample of jobs without descriptions
            samples = await conn.fetch("""
                SELECT company_name, title, url
                FROM jobs 
                WHERE is_active = true 
                AND (description_snippet IS NULL OR description_snippet = '')
                LIMIT 5
            """)
            
            if samples:
                print("\n📋 Sample jobs needing descriptions:")
                for job in samples:
                    print(f"  • {job['company_name']}: {job['title']}")
                    print(f"    URL: {job['url']}")
            
            return stats
            
        finally:
            await conn.close()
    
    async def crawl_jobs_in_parallel(self, jobs: List[Dict]) -> Dict[str, Any]:
        """Use /crawl-many to get all job pages at once"""
        if not jobs:
            return {"success": False, "results": []}
        
        print(f"\n🚀 Crawling {len(jobs)} job pages in parallel...")
        
        async with httpx.AsyncClient(timeout=120) as client:
            # Prepare URLs for crawling
            job_urls = [job['url'] for job in jobs]
            
            # Split into batches if needed (API might have limits)
            batch_size = 20
            all_results = []
            
            for i in range(0, len(job_urls), batch_size):
                batch = job_urls[i:i + batch_size]
                print(f"\n  📦 Processing batch {i//batch_size + 1} ({len(batch)} URLs)...")
                
                response = await client.post(
                    f"{self.crawl4ai_url}/crawl-many",
                    json={
                        "urls": batch,
                        "parallel": 5,
                        "delay_between": 0.5
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        all_results.extend(data.get("results", []))
                        print(f"    ✅ Batch complete: {data['successful']}/{len(batch)} successful")
                    else:
                        print(f"    ❌ Batch failed: {data.get('error')}")
                else:
                    print(f"    ❌ HTTP error: {response.status_code}")
                
                # Small delay between batches
                if i + batch_size < len(job_urls):
                    await asyncio.sleep(2)
            
            return {"success": True, "results": all_results}
    
    def extract_job_details(self, content: str) -> Dict[str, Any]:
        """Extract structured details from job page content"""
        details = {
            "full_description": "",
            "requirements": [],
            "responsibilities": [],
            "benefits": [],
            "qualifications": [],
            "salary_info": None,
            "experience_level": None
        }
        
        if not content or len(content) < 50:
            return details
        
        # Clean and parse content
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        # Keywords for section detection
        section_keywords = {
            "requirements": ["requirements", "required", "you will need", "must have", "minimum qualifications"],
            "responsibilities": ["responsibilities", "what you'll do", "you will", "duties", "role responsibilities"],
            "benefits": ["benefits", "perks", "what we offer", "compensation", "why join"],
            "qualifications": ["qualifications", "nice to have", "preferred", "ideal candidate", "bonus points"],
            "about": ["about the role", "about this position", "overview", "description", "about you"]
        }
        
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
                
            line_lower = line_clean.lower()
            
            # Check for section headers
            section_found = False
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
                    section_found = True
                    break
            
            if not section_found and current_section:
                # Add content to current section
                # Check for bullet points or list items
                if line_clean.startswith(('•', '-', '*', '◦', '▪', '→')) or \
                   (len(line_clean) > 2 and line_clean[0].isdigit() and line_clean[1] in '.):'):
                    # Clean up bullet point
                    cleaned = line_clean.lstrip('•-*◦▪→').lstrip('0123456789.): ').strip()
                    if cleaned:
                        current_content.append(cleaned)
                elif current_section == "about":
                    current_content.append(line_clean)
                else:
                    # Check for special content
                    if any(term in line_lower for term in ["salary", "$", "compensation", "pay range"]):
                        if "$" in line_clean or any(c.isdigit() for c in line_clean):
                            details["salary_info"] = line_clean
                    
                    if any(term in line_lower for term in ["senior", "junior", "mid-level", "staff", "principal", "lead"]):
                        for level in ["Senior", "Junior", "Mid-level", "Staff", "Principal", "Lead"]:
                            if level.lower() in line_lower:
                                details["experience_level"] = level
                                break
                    
                    # Add to current section if it looks like content
                    if len(line_clean) > 20:
                        current_content.append(line_clean)
        
        # Save last section
        if current_section and current_content:
            if current_section in ["requirements", "responsibilities", "benefits", "qualifications"]:
                details[current_section] = current_content
            elif current_section == "about":
                details["full_description"] = '\n'.join(current_content)
        
        # If no structured description found, use the first part of content
        if not details["full_description"] and content:
            # Take first meaningful paragraph
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and len(p.strip()) > 50]
            if paragraphs:
                details["full_description"] = '\n\n'.join(paragraphs[:3])
            else:
                details["full_description"] = content[:2000]
        
        # Create snippet from description
        details["snippet"] = details["full_description"][:500] if details["full_description"] else ""
        
        return details
    
    async def update_job_with_details(self, job_id: str, url: str, content: str):
        """Update a job with scraped details"""
        # Extract structured details
        details = self.extract_job_details(content)
        
        # Prepare data for database
        description_snippet = details["snippet"][:500] if details["snippet"] else None
        
        raw_data = {
            "full_description": details["full_description"],
            "requirements": details["requirements"],
            "responsibilities": details["responsibilities"],
            "benefits": details["benefits"],
            "qualifications": details["qualifications"],
            "salary_info": details["salary_info"],
            "experience_level": details["experience_level"],
            "scraped_at": datetime.now().isoformat(),
            "content_length": len(content)
        }
        
        conn = await asyncpg.connect(self.db_url)
        try:
            await conn.execute("""
                UPDATE jobs 
                SET description_snippet = $2,
                    raw_data = COALESCE(raw_data, '{}'::jsonb) || $3::jsonb,
                    updated_date = CURRENT_TIMESTAMP
                WHERE id = $1
            """, job_id, description_snippet, json.dumps(raw_data))
        finally:
            await conn.close()
        
        return details
    
    async def deep_scrape_all_jobs(self):
        """Main function to deep scrape all jobs"""
        print("\n" + "="*80)
        print("DEEP SCRAPING WITH CRAWL4AI v5.0")
        print("="*80)
        
        # Show current state
        initial_stats = await self.show_current_state()
        
        # Get jobs needing details
        jobs = await self.get_jobs_needing_details(limit=100)
        
        if not jobs:
            print("\n✅ All jobs already have descriptions!")
            return
        
        print(f"\n📋 Found {len(jobs)} jobs needing full descriptions")
        print("Starting parallel crawling...")
        
        # Crawl all job pages in parallel
        crawl_results = await self.crawl_jobs_in_parallel(jobs)
        
        if not crawl_results.get("success"):
            print("❌ Crawling failed")
            return
        
        # Process results and update database
        print(f"\n💾 Updating database with scraped details...")
        
        successful_updates = 0
        jobs_with_content = 0
        total_requirements = 0
        total_benefits = 0
        salary_found = 0
        
        for job, result in zip(jobs, crawl_results["results"]):
            if result.get("success") and result.get("content"):
                content = result["content"]
                
                # Only update if we got meaningful content
                if len(content) > 100:
                    details = await self.update_job_with_details(
                        job['id'], 
                        job['url'], 
                        content
                    )
                    
                    successful_updates += 1
                    
                    # Track statistics
                    if details["full_description"]:
                        jobs_with_content += 1
                    if details["requirements"]:
                        total_requirements += len(details["requirements"])
                    if details["benefits"]:
                        total_benefits += len(details["benefits"])
                    if details["salary_info"]:
                        salary_found += 1
                    
                    # Show progress
                    if successful_updates % 10 == 0:
                        print(f"  ✅ Updated {successful_updates} jobs...")
        
        # Show results
        print("\n" + "="*80)
        print("DEEP SCRAPING COMPLETE!")
        print("="*80)
        print(f"📊 Results:")
        print(f"  • Jobs processed: {len(jobs)}")
        print(f"  • Successfully updated: {successful_updates}")
        print(f"  • Jobs with content: {jobs_with_content}")
        print(f"  • Total requirements extracted: {total_requirements}")
        print(f"  • Total benefits extracted: {total_benefits}")
        print(f"  • Jobs with salary info: {salary_found}")
        
        # Show updated state
        await self.show_updated_samples()
    
    async def show_updated_samples(self):
        """Show samples of updated jobs with descriptions"""
        conn = await asyncpg.connect(self.db_url)
        try:
            print("\n📝 Sample updated jobs with descriptions:")
            
            samples = await conn.fetch("""
                SELECT company_name, title, description_snippet, raw_data
                FROM jobs 
                WHERE is_active = true 
                AND description_snippet IS NOT NULL 
                AND description_snippet != ''
                ORDER BY updated_date DESC
                LIMIT 3
            """)
            
            for i, job in enumerate(samples, 1):
                print(f"\n{i}. {job['company_name']}: {job['title']}")
                print(f"   Description: {job['description_snippet'][:200]}...")
                
                if job['raw_data']:
                    data = json.loads(job['raw_data'])
                    if data.get('requirements'):
                        print(f"   Requirements: {len(data['requirements'])} items")
                    if data.get('benefits'):
                        print(f"   Benefits: {len(data['benefits'])} items")
                    if data.get('salary_info'):
                        print(f"   💰 Salary: {data['salary_info']}")
            
            # Final statistics
            final_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN description_snippet IS NOT NULL AND description_snippet != '' THEN 1 END) as jobs_with_descriptions
                FROM jobs 
                WHERE is_active = true
            """)
            
            print(f"\n📈 Final Status:")
            print(f"   Total jobs: {final_stats['total_jobs']}")
            print(f"   Jobs with descriptions: {final_stats['jobs_with_descriptions']}")
            print(f"   Coverage: {final_stats['jobs_with_descriptions']*100//final_stats['total_jobs']}%")
            
        finally:
            await conn.close()


async def main():
    """Run the deep scraper v2"""
    scraper = DeepScraperV2()
    await scraper.deep_scrape_all_jobs()


if __name__ == "__main__":
    asyncio.run(main())