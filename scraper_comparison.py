#!/usr/bin/env python3
"""
Comprehensive Job Scraper Comparison
Tests BeautifulSoup vs Crawl4AI across multiple job boards
"""

import asyncio
import json
import re
import time
import os
from datetime import datetime
from typing import Dict, Any, List
import httpx
from bs4 import BeautifulSoup
import asyncpg
from dotenv import load_dotenv

load_dotenv()


class ScraperComparison:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.crawl4ai_url = "https://crawl4ai-production-6e85.up.railway.app"
        self.results = []
    
    async def get_job_boards(self) -> List[Dict]:
        """Get all active job boards from Neon"""
        conn = await asyncpg.connect(self.db_url)
        try:
            query = "SELECT id, company_name, url, board_type FROM job_boards WHERE is_active = true ORDER BY company_name"
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def test_beautifulsoup(self, url: str, board_type: str) -> Dict[str, Any]:
        """Test BeautifulSoup scraping"""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; JobScraper/1.0)'
                })
                
                if response.status_code != 200:
                    return {
                        "method": "BeautifulSoup",
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "time_taken": round(time.time() - start_time, 2)
                    }
                
                html = response.text
                jobs = []
                
                # Extract based on board type
                if board_type == "ashby":
                    # Look for embedded JSON
                    match = re.search(r'window\.__appData\s*=\s*({.*?});', html, re.DOTALL)
                    if match:
                        try:
                            app_data = json.loads(match.group(1))
                            job_postings = app_data.get('jobBoard', {}).get('jobPostings', [])
                            
                            for job in job_postings:
                                if job.get('isListed'):
                                    jobs.append({
                                        'title': job.get('title'),
                                        'department': job.get('departmentName'),
                                        'location': job.get('locationName'),
                                        'type': job.get('employmentType'),
                                        'workplace': job.get('workplaceType'),
                                        'posted': job.get('publishedDate'),
                                        'has_salary': bool(job.get('compensationTierSummary'))
                                    })
                        except json.JSONDecodeError:
                            pass
                else:
                    # Generic extraction
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Common job selectors
                    job_selectors = [
                        'div[class*="job"]',
                        'div[class*="position"]',
                        'div[class*="opening"]',
                        'a[href*="/careers/"]',
                        'a[href*="/jobs/"]'
                    ]
                    
                    for selector in job_selectors:
                        elements = soup.select(selector)[:50]  # Limit to 50
                        for elem in elements:
                            title = elem.get_text(strip=True)
                            if len(title) > 5 and len(title) < 200:
                                jobs.append({'title': title})
                
                return {
                    "method": "BeautifulSoup",
                    "success": True,
                    "jobs_found": len(jobs),
                    "jobs": jobs[:5],  # First 5 for preview
                    "time_taken": round(time.time() - start_time, 2),
                    "cost": 0.0,
                    "data_quality": self.assess_quality(jobs)
                }
                
        except Exception as e:
            return {
                "method": "BeautifulSoup",
                "success": False,
                "error": str(e),
                "time_taken": round(time.time() - start_time, 2)
            }
    
    async def test_crawl4ai(self, url: str, board_type: str) -> Dict[str, Any]:
        """Test Crawl4AI scraping"""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                # Use /scrape for Ashby boards, /crawl for others
                if board_type == "ashby":
                    endpoint = "/scrape"
                    payload = {"url": url}
                else:
                    endpoint = "/crawl"
                    payload = {"url": url, "max_pages": 1}
                
                response = await client.post(
                    f"{self.crawl4ai_url}{endpoint}",
                    json=payload
                )
                
                if response.status_code != 200:
                    return {
                        "method": "Crawl4AI",
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "time_taken": round(time.time() - start_time, 2)
                    }
                
                data = response.json()
                jobs = []
                
                if endpoint == "/scrape":
                    # Parse markdown content
                    content = data.get('markdown', '')
                    if content:
                        # Extract job info from markdown
                        lines = content.split('\n')
                        current_job = {}
                        
                        for line in lines:
                            if line.startswith('## '):
                                if current_job:
                                    jobs.append(current_job)
                                current_job = {'title': line[3:]}
                            elif '**Department:**' in line:
                                current_job['department'] = line.split('**Department:**')[1].strip()
                            elif '**Location:**' in line:
                                current_job['location'] = line.split('**Location:**')[1].strip()
                            elif '**Type:**' in line:
                                current_job['type'] = line.split('**Type:**')[1].strip()
                            elif '**Workplace:**' in line:
                                current_job['workplace'] = line.split('**Workplace:**')[1].strip()
                            elif '**Posted:**' in line:
                                current_job['posted'] = line.split('**Posted:**')[1].strip()
                        
                        if current_job:
                            jobs.append(current_job)
                else:
                    # Parse from /crawl response
                    pages = data.get('pages', [])
                    if pages:
                        content = pages[0].get('content', '')
                        # Simple extraction from content
                        for line in content.split('\n'):
                            if ' - ' in line and len(line) < 200:
                                parts = line.split(' - ')
                                if len(parts) >= 2:
                                    jobs.append({
                                        'title': parts[0].strip(),
                                        'department': parts[1].strip() if len(parts) > 1 else '',
                                        'location': parts[2].strip() if len(parts) > 2 else ''
                                    })
                
                return {
                    "method": "Crawl4AI",
                    "success": data.get('success', False),
                    "jobs_found": len(jobs),
                    "jobs": jobs[:5],
                    "time_taken": round(time.time() - start_time, 2),
                    "cost": 0.0,
                    "data_quality": self.assess_quality(jobs)
                }
                
        except Exception as e:
            return {
                "method": "Crawl4AI",
                "success": False,
                "error": str(e),
                "time_taken": round(time.time() - start_time, 2)
            }
    
    def assess_quality(self, jobs: List[Dict]) -> Dict[str, Any]:
        """Assess the quality of extracted job data"""
        if not jobs:
            return {"score": 0, "completeness": 0, "fields": []}
        
        # Check which fields are present
        field_counts = {
            'title': sum(1 for j in jobs if j.get('title')),
            'department': sum(1 for j in jobs if j.get('department')),
            'location': sum(1 for j in jobs if j.get('location')),
            'type': sum(1 for j in jobs if j.get('type')),
            'posted': sum(1 for j in jobs if j.get('posted')),
            'salary': sum(1 for j in jobs if j.get('has_salary'))
        }
        
        total_jobs = len(jobs)
        completeness = {
            field: (count / total_jobs * 100) if total_jobs > 0 else 0
            for field, count in field_counts.items()
        }
        
        # Calculate quality score (0-100)
        weights = {
            'title': 30,
            'department': 20,
            'location': 20,
            'type': 15,
            'posted': 10,
            'salary': 5
        }
        
        score = sum(
            completeness[field] * weight / 100
            for field, weight in weights.items()
        )
        
        return {
            "score": round(score, 1),
            "completeness": completeness,
            "total_fields": field_counts
        }
    
    async def compare_all_boards(self):
        """Run comparison across all job boards"""
        boards = await self.get_job_boards()
        
        print("\n" + "="*80)
        print("JOB SCRAPER COMPARISON - BEAUTIFULSOUP VS CRAWL4AI")
        print("="*80)
        print(f"Testing {len(boards)} job boards...")
        
        results = []
        
        for board in boards:
            print(f"\n📋 Testing: {board['company_name']} ({board['url'][:50]}...)")
            print("-" * 60)
            
            # Test both scrapers
            bs_result = await self.test_beautifulsoup(board['url'], board['board_type'])
            c4ai_result = await self.test_crawl4ai(board['url'], board['board_type'])
            
            # Store results
            result = {
                'company': board['company_name'],
                'url': board['url'],
                'board_type': board['board_type'],
                'beautifulsoup': bs_result,
                'crawl4ai': c4ai_result
            }
            results.append(result)
            
            # Display results
            print(f"\n{'Method':<15} {'Success':<10} {'Jobs':<10} {'Time':<10} {'Quality':<10}")
            print("-" * 60)
            
            for method_name, method_result in [('BeautifulSoup', bs_result), ('Crawl4AI', c4ai_result)]:
                if method_result['success']:
                    print(f"{method_name:<15} {'✅':<10} {method_result.get('jobs_found', 0):<10} "
                          f"{method_result.get('time_taken', 0):.2f}s{'':<7} "
                          f"{method_result.get('data_quality', {}).get('score', 0):.1f}/100")
                else:
                    print(f"{method_name:<15} {'❌':<10} {'N/A':<10} "
                          f"{method_result.get('time_taken', 0):.2f}s{'':<7} N/A")
            
            # Show sample jobs
            winner = bs_result if bs_result.get('jobs_found', 0) > c4ai_result.get('jobs_found', 0) else c4ai_result
            if winner.get('jobs'):
                print(f"\nSample jobs from {winner['method']}:")
                for i, job in enumerate(winner['jobs'][:3], 1):
                    print(f"  {i}. {job.get('title', 'N/A')}")
                    if job.get('department'):
                        print(f"     Dept: {job['department']}")
                    if job.get('location'):
                        print(f"     Loc: {job['location']}")
        
        # Summary
        self.print_summary(results)
        
        # Save to database
        await self.save_results(results)
        
        return results
    
    def print_summary(self, results: List[Dict]):
        """Print comparison summary"""
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        
        # Calculate totals
        bs_success = sum(1 for r in results if r['beautifulsoup']['success'])
        c4ai_success = sum(1 for r in results if r['crawl4ai']['success'])
        
        bs_jobs = sum(r['beautifulsoup'].get('jobs_found', 0) for r in results)
        c4ai_jobs = sum(r['crawl4ai'].get('jobs_found', 0) for r in results)
        
        bs_time = sum(r['beautifulsoup'].get('time_taken', 0) for r in results)
        c4ai_time = sum(r['crawl4ai'].get('time_taken', 0) for r in results)
        
        bs_quality = [r['beautifulsoup'].get('data_quality', {}).get('score', 0) 
                     for r in results if r['beautifulsoup']['success']]
        c4ai_quality = [r['crawl4ai'].get('data_quality', {}).get('score', 0) 
                       for r in results if r['crawl4ai']['success']]
        
        print(f"\n{'Metric':<20} {'BeautifulSoup':<20} {'Crawl4AI':<20}")
        print("-" * 60)
        print(f"{'Success Rate:':<20} {bs_success}/{len(results):<20} {c4ai_success}/{len(results):<20}")
        print(f"{'Total Jobs Found:':<20} {bs_jobs:<20} {c4ai_jobs:<20}")
        print(f"{'Total Time:':<20} {f'{bs_time:.1f}s':<20} {f'{c4ai_time:.1f}s':<20}")
        print(f"{'Avg Time/Board:':<20} {f'{bs_time/len(results):.1f}s':<20} {f'{c4ai_time/len(results):.1f}s':<20}")
        
        if bs_quality:
            print(f"{'Avg Quality Score:':<20} {f'{sum(bs_quality)/len(bs_quality):.1f}/100':<20}", end="")
        else:
            print(f"{'Avg Quality Score:':<20} {'N/A':<20}", end="")
        
        if c4ai_quality:
            print(f"{f'{sum(c4ai_quality)/len(c4ai_quality):.1f}/100':<20}")
        else:
            print("N/A")
        
        # Winners by category
        print("\n🏆 WINNERS BY CATEGORY:")
        print("-" * 40)
        
        # By board type
        ashby_boards = [r for r in results if r['board_type'] == 'ashby']
        if ashby_boards:
            ashby_bs = sum(r['beautifulsoup'].get('jobs_found', 0) for r in ashby_boards)
            ashby_c4ai = sum(r['crawl4ai'].get('jobs_found', 0) for r in ashby_boards)
            
            winner = "BeautifulSoup" if ashby_bs > ashby_c4ai else "Crawl4AI"
            print(f"Ashby Boards: {winner} ({max(ashby_bs, ashby_c4ai)} jobs vs {min(ashby_bs, ashby_c4ai)})")
        
        # Overall winner
        if bs_jobs > c4ai_jobs:
            print(f"\n📊 OVERALL WINNER: BeautifulSoup ({bs_jobs} total jobs)")
        elif c4ai_jobs > bs_jobs:
            print(f"\n📊 OVERALL WINNER: Crawl4AI ({c4ai_jobs} total jobs)")
        else:
            print(f"\n📊 TIE: Both found {bs_jobs} jobs")
    
    async def save_results(self, results: List[Dict]):
        """Save comparison results to database"""
        conn = await asyncpg.connect(self.db_url)
        try:
            for result in results:
                # Update scrape history for tracking
                board_id = await conn.fetchval(
                    "SELECT id FROM job_boards WHERE url = $1",
                    result['url']
                )
                
                if board_id:
                    # Save BeautifulSoup result
                    if result['beautifulsoup']['success']:
                        await conn.execute("""
                            INSERT INTO scrape_history 
                            (board_id, status, jobs_found, execution_time_ms)
                            VALUES ($1, 'success', $2, $3)
                        """, board_id, result['beautifulsoup'].get('jobs_found', 0),
                            int(result['beautifulsoup'].get('time_taken', 0) * 1000))
                    
                    # Update last_scraped_at
                    await conn.execute(
                        "UPDATE job_boards SET last_scraped_at = $1 WHERE id = $2",
                        datetime.now(), board_id
                    )
        finally:
            await conn.close()


async def explore_crawl4ai_features():
    """Explore advanced Crawl4AI features for deeper scraping"""
    print("\n" + "="*80)
    print("CRAWL4AI ADVANCED FEATURES FOR DEEPER SCRAPING")
    print("="*80)
    
    print("""
    📚 FEATURES WE COULD USE FOR DEEPER JOB SCRAPING:
    
    1. **CSS/JSON Extraction Strategy** (/extract endpoint)
       - Define exact selectors for job fields
       - Get structured JSON output
       - Example: Extract salary ranges, benefits, requirements
    
    2. **Multi-page Crawling** (/crawl with max_pages)
       - Follow pagination links
       - Crawl entire job sections
       - Get ALL jobs, not just first page
    
    3. **Custom JavaScript Execution**
       - Click "Load More" buttons
       - Scroll infinite feeds
       - Expand collapsed job descriptions
    
    4. **Link Following Strategy**
       - Crawl from job list → individual job pages
       - Extract full job descriptions
       - Get application requirements
    
    5. **Content Filtering**
       - Focus on specific sections
       - Remove noise (ads, navigation)
       - Extract only job-relevant content
    
    6. **Batch Processing**
       - Process multiple job boards in parallel
       - Aggregate results
       - Compare across companies
    
    IMPLEMENTATION EXAMPLE:
    """)
    
    # Show example of deeper extraction
    example_code = '''
    # Deep job extraction with Crawl4AI
    
    async def deep_job_scrape(job_board_url):
        # Step 1: Get all job listing pages
        crawl_response = await client.post(
            f"{CRAWL4AI_URL}/crawl",
            json={
                "url": job_board_url,
                "max_pages": 10,  # Get up to 10 pages of listings
                "follow_links": True
            }
        )
        
        all_job_urls = []
        for page in crawl_response["pages"]:
            # Extract individual job URLs
            job_urls = extract_job_urls(page["content"])
            all_job_urls.extend(job_urls)
        
        # Step 2: Scrape each job page for full details
        detailed_jobs = []
        for job_url in all_job_urls:
            job_response = await client.post(
                f"{CRAWL4AI_URL}/extract",
                json={
                    "url": job_url,
                    "schema": {
                        "title": "h1.job-title",
                        "description": "div.job-description",
                        "requirements": "ul.requirements li",
                        "benefits": "div.benefits",
                        "salary": "span.salary-range",
                        "apply_url": "a.apply-button@href"
                    }
                }
            )
            detailed_jobs.append(job_response["data"])
        
        return detailed_jobs
    '''
    
    print(example_code)
    
    print("""
    🎯 CURRENT LIMITATIONS:
    
    1. Railway deployment doesn't have all features enabled
    2. JavaScript execution is limited
    3. No LLM extraction (would need API keys)
    4. Session persistence not implemented
    
    💡 RECOMMENDATIONS:
    
    For DEEPER job scraping, we should:
    1. Implement multi-page crawling (follow pagination)
    2. Extract individual job pages (not just listings)
    3. Use CSS selectors for structured data
    4. Store raw HTML for later re-parsing
    5. Track changes over time (new/removed jobs)
    """)


async def main():
    # Run comparison
    comparison = ScraperComparison()
    results = await comparison.compare_all_boards()
    
    # Show advanced features
    await explore_crawl4ai_features()
    
    print("\n✅ Comparison complete! Check the results above.")
    print("📊 Data saved to Neon database for tracking.")


if __name__ == "__main__":
    asyncio.run(main())