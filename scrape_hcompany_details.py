#!/usr/bin/env python3
"""
Deep scrape all hcompany jobs to get full descriptions
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def scrape_hcompany_details():
    """Get full details for all hcompany jobs"""
    
    db_url = os.getenv("DATABASE_URL")
    crawl4ai_url = "https://crawl4ai-production-6e85.up.railway.app"
    
    conn = await asyncpg.connect(db_url)
    
    try:
        print("="*80)
        print("DEEP SCRAPING HCOMPANY JOBS")
        print("="*80)
        
        # Get all hcompany jobs
        jobs = await conn.fetch("""
            SELECT id, title, url, description_snippet
            FROM jobs 
            WHERE company_name = 'hcompany' 
            AND is_active = true
            ORDER BY title
        """)
        
        print(f"\n📋 Found {len(jobs)} hcompany jobs to scrape")
        
        # Get URLs for crawling
        job_urls = [job['url'] for job in jobs]
        
        async with httpx.AsyncClient(timeout=120) as client:
            print(f"\n🕷️ Crawling all {len(job_urls)} job pages in parallel...")
            
            # Crawl all at once since there are only 15
            response = await client.post(
                f"{crawl4ai_url}/crawl-many",
                json={
                    "urls": job_urls,
                    "parallel": 5,
                    "delay_between": 0.5
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    print(f"✅ Successfully crawled {data['successful']}/{len(job_urls)} pages")
                    
                    # Update database with full descriptions
                    print("\n💾 Updating database with full job details...")
                    
                    for job, result in zip(jobs, data['results']):
                        if result.get('success') and result.get('content'):
                            content = result['content']
                            
                            # Parse the content to extract description
                            lines = content.split('\n')
                            description = []
                            in_description = False
                            
                            for line in lines:
                                if line.strip() == "## Description":
                                    in_description = True
                                    continue
                                elif in_description:
                                    if line.startswith("#") or line.startswith("**"):
                                        # End of description section
                                        break
                                    description.append(line)
                            
                            full_description = '\n'.join(description).strip()
                            snippet = full_description[:500] if full_description else ""
                            
                            # Extract other details
                            raw_data = {
                                "full_description": full_description,
                                "content_length": len(content),
                                "scraped_at": datetime.now().isoformat()
                            }
                            
                            # Look for salary info
                            if "Salary:" in content or "$" in content:
                                for line in lines:
                                    if "Salary:" in line or "$" in line:
                                        raw_data["salary_info"] = line.strip()
                                        break
                            
                            # Update the job
                            await conn.execute("""
                                UPDATE jobs 
                                SET description_snippet = $2,
                                    raw_data = COALESCE(raw_data, '{}'::jsonb) || $3::jsonb,
                                    updated_date = CURRENT_TIMESTAMP
                                WHERE id = $1
                            """, job['id'], snippet, json.dumps(raw_data))
                            
                            print(f"  ✅ {job['title']}: {len(full_description)} chars")
                    
                    print("\n" + "="*80)
                    print("FINAL RESULTS")
                    print("="*80)
                    
                    # Show final stats
                    stats = await conn.fetch("""
                        SELECT 
                            company_name,
                            COUNT(*) as total,
                            COUNT(CASE WHEN description_snippet IS NOT NULL AND description_snippet != '' THEN 1 END) as with_desc,
                            AVG(LENGTH(description_snippet)) as avg_length
                        FROM jobs 
                        WHERE is_active = true
                        GROUP BY company_name
                        ORDER BY company_name
                    """)
                    
                    total_jobs = 0
                    total_with_desc = 0
                    
                    print("\n📊 Jobs by company:")
                    for stat in stats:
                        coverage = stat['with_desc'] * 100 // stat['total'] if stat['total'] > 0 else 0
                        avg_len = int(stat['avg_length']) if stat['avg_length'] else 0
                        print(f"  • {stat['company_name']}: {stat['with_desc']}/{stat['total']} with descriptions ({coverage}%)")
                        if avg_len > 0:
                            print(f"    Average description length: {avg_len} chars")
                        total_jobs += stat['total']
                        total_with_desc += stat['with_desc']
                    
                    overall_coverage = total_with_desc * 100 // total_jobs if total_jobs > 0 else 0
                    print(f"\n📈 OVERALL: {total_with_desc}/{total_jobs} jobs with descriptions ({overall_coverage}%)")
                    
                    # Show sample hcompany job
                    sample = await conn.fetchrow("""
                        SELECT title, description_snippet
                        FROM jobs 
                        WHERE company_name = 'hcompany' 
                        AND description_snippet IS NOT NULL
                        AND LENGTH(description_snippet) > 100
                        LIMIT 1
                    """)
                    
                    if sample:
                        print(f"\n📝 Sample hcompany job description:")
                        print(f"  {sample['title']}:")
                        print(f"  {sample['description_snippet'][:300]}...")
                    
    finally:
        await conn.close()


async def main():
    await scrape_hcompany_details()


if __name__ == "__main__":
    asyncio.run(main())