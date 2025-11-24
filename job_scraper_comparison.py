#!/usr/bin/env python3
"""
Job Scraper Comparison: Crawl4AI vs Firecrawl vs BeautifulSoup
Testing different scraping approaches for job boards
"""

import asyncio
import json
import re
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


class JobScraperComparison:
    """Compare different scraping methods for job boards"""
    
    def __init__(self):
        self.crawl4ai_url = "https://crawl4ai-production-6e85.up.railway.app"
        self.firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY", "fc-ccb4f4c998e44d0a8281abb8d92056ef")
        self.test_url = "https://jobs.ashbyhq.com/claylabs/"
        
    async def test_crawl4ai_basic(self) -> Dict[str, Any]:
        """Test basic Crawl4AI scraping"""
        print("\n🤖 Testing Crawl4AI (basic)...")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "url": self.test_url,
                    "word_count_threshold": 5,
                    "excluded_tags": [],
                    "remove_overlay_elements": False
                }
                
                async with session.post(
                    f"{self.crawl4ai_url}/scrape",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    data = await response.json()
                    
                    jobs = self.extract_jobs_from_content(data.get("markdown", ""))
                    
                    return {
                        "method": "Crawl4AI (basic)",
                        "success": data.get("success", False),
                        "content_length": data.get("content_length", 0),
                        "jobs_found": len(jobs),
                        "time_taken": round(time.time() - start_time, 2),
                        "jobs": jobs[:3]  # First 3 for preview
                    }
                    
        except Exception as e:
            return {
                "method": "Crawl4AI (basic)",
                "success": False,
                "error": str(e),
                "time_taken": round(time.time() - start_time, 2)
            }
    
    async def test_crawl4ai_with_js(self) -> Dict[str, Any]:
        """Test Crawl4AI with JavaScript waiting"""
        print("\n🤖 Testing Crawl4AI (with JS wait)...")
        start_time = time.time()
        
        try:
            # Based on the article, we need to pass JavaScript execution parameters
            async with aiohttp.ClientSession() as session:
                payload = {
                    "url": self.test_url,
                    "js_code": "window.__appData",  # Check for Ashby's data
                    "wait_for": "window.__appData && window.__appData.jobBoard",  # Wait for job data
                    "word_count_threshold": 5,
                    "process_iframes": True,
                    "remove_overlay_elements": True
                }
                
                async with session.post(
                    f"{self.crawl4ai_url}/scrape",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    data = await response.json()
                    
                    # Try to extract from markdown or raw content
                    content = data.get("markdown", "") or data.get("content", "")
                    jobs = self.extract_jobs_from_content(content)
                    
                    return {
                        "method": "Crawl4AI (with JS)",
                        "success": data.get("success", False),
                        "content_length": len(content),
                        "jobs_found": len(jobs),
                        "time_taken": round(time.time() - start_time, 2),
                        "jobs": jobs[:3]
                    }
                    
        except Exception as e:
            return {
                "method": "Crawl4AI (with JS)",
                "success": False,
                "error": str(e),
                "time_taken": round(time.time() - start_time, 2)
            }
    
    async def test_firecrawl(self) -> Dict[str, Any]:
        """Test Firecrawl API"""
        print("\n🔥 Testing Firecrawl...")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Firecrawl v2 API endpoint
                headers = {
                    "Authorization": f"Bearer {self.firecrawl_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "url": self.test_url,
                    "formats": ["markdown", "html"],
                    "onlyMainContent": True,
                    "waitFor": 5000  # Wait 5 seconds for JS
                }
                
                async with session.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract markdown content
                        markdown = data.get("data", {}).get("markdown", "")
                        jobs = self.extract_jobs_from_content(markdown)
                        
                        return {
                            "method": "Firecrawl",
                            "success": data.get("success", False),
                            "content_length": len(markdown),
                            "jobs_found": len(jobs),
                            "time_taken": round(time.time() - start_time, 2),
                            "jobs": jobs[:3]
                        }
                    else:
                        error_data = await response.text()
                        return {
                            "method": "Firecrawl",
                            "success": False,
                            "error": f"HTTP {response.status}: {error_data}",
                            "time_taken": round(time.time() - start_time, 2)
                        }
                        
        except Exception as e:
            return {
                "method": "Firecrawl",
                "success": False,
                "error": str(e),
                "time_taken": round(time.time() - start_time, 2)
            }
    
    async def test_beautifulsoup(self) -> Dict[str, Any]:
        """Test BeautifulSoup (direct HTTP)"""
        print("\n🍲 Testing BeautifulSoup...")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                
                async with session.get(self.test_url, headers=headers, ssl=False) as response:
                    html = await response.text()
                    
                    # Extract jobs from embedded JSON
                    jobs = self.extract_ashby_jobs(html)
                    
                    return {
                        "method": "BeautifulSoup",
                        "success": True,
                        "content_length": len(html),
                        "jobs_found": len(jobs),
                        "time_taken": round(time.time() - start_time, 2),
                        "jobs": jobs[:3]
                    }
                    
        except Exception as e:
            return {
                "method": "BeautifulSoup",
                "success": False,
                "error": str(e),
                "time_taken": round(time.time() - start_time, 2)
            }
    
    def extract_ashby_jobs(self, html: str) -> list:
        """Extract jobs from Ashby embedded JSON"""
        jobs = []
        
        # Find __appData in script tag
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
                            'location': job.get('locationName')
                        })
            except:
                pass
        
        return jobs
    
    def extract_jobs_from_content(self, content: str) -> list:
        """Extract job listings from markdown/text content"""
        jobs = []
        
        # Try to find job-like patterns in the content
        # Look for common job title patterns
        job_patterns = [
            r'(?:^|\n)([A-Z][A-Za-z\s,]+(?:Engineer|Developer|Manager|Designer|Analyst|Specialist|Lead|Director))',
            r'(?:^|\n)##?\s*([A-Z][A-Za-z\s,]+)',
        ]
        
        for pattern in job_patterns:
            matches = re.findall(pattern, content)
            for match in matches[:10]:  # Limit to prevent false positives
                if len(match) > 5 and len(match) < 100:
                    jobs.append({'title': match.strip()})
        
        # Also check for embedded JSON
        if '__appData' in content:
            extracted = self.extract_ashby_jobs(content)
            if extracted:
                return extracted
        
        return jobs
    
    async def run_comparison(self):
        """Run all scraping methods and compare results"""
        print("\n" + "=" * 60)
        print("JOB SCRAPER COMPARISON TEST")
        print("=" * 60)
        print(f"Testing URL: {self.test_url}")
        
        # Run all tests
        results = await asyncio.gather(
            self.test_beautifulsoup(),
            self.test_crawl4ai_basic(),
            self.test_crawl4ai_with_js(),
            self.test_firecrawl(),
            return_exceptions=True
        )
        
        # Display comparison
        print("\n" + "=" * 60)
        print("RESULTS COMPARISON:")
        print("=" * 60)
        
        for result in results:
            if isinstance(result, Exception):
                print(f"\n❌ Error: {result}")
            else:
                print(f"\n📊 {result['method']}:")
                print(f"   Success: {'✅' if result.get('success') else '❌'}")
                if result.get('success'):
                    print(f"   Jobs found: {result.get('jobs_found', 0)}")
                    print(f"   Content size: {result.get('content_length', 0):,} chars")
                    print(f"   Time taken: {result.get('time_taken', 0)}s")
                    
                    if result.get('jobs'):
                        print(f"   Sample jobs:")
                        for job in result['jobs'][:3]:
                            print(f"     - {job.get('title', 'N/A')}")
                else:
                    print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Determine winner
        print("\n" + "=" * 60)
        print("ANALYSIS:")
        print("=" * 60)
        
        successful_results = [r for r in results if isinstance(r, dict) and r.get('success')]
        
        if successful_results:
            # Sort by jobs found
            best = max(successful_results, key=lambda x: x.get('jobs_found', 0))
            fastest = min(successful_results, key=lambda x: x.get('time_taken', 999))
            
            print(f"🏆 Most jobs found: {best['method']} ({best['jobs_found']} jobs)")
            print(f"⚡ Fastest: {fastest['method']} ({fastest['time_taken']}s)")
            
            # Recommendations
            print("\n📝 RECOMMENDATIONS:")
            print("-" * 40)
            
            bs_result = next((r for r in successful_results if r['method'] == 'BeautifulSoup'), None)
            if bs_result and bs_result['jobs_found'] > 0:
                print("• For Ashby boards: Use BeautifulSoup (embedded JSON)")
            
            if any('Crawl4AI' in r['method'] for r in successful_results):
                print("• For JS-heavy sites: Use Crawl4AI with wait conditions")
            
            if any('Firecrawl' in r['method'] for r in successful_results):
                print("• For production/scale: Consider Firecrawl (managed service)")
        
        print("=" * 60)
        
        return results


# Test MCP integration possibilities
async def test_mcp_integration():
    """Explore MCP integration for scraping"""
    print("\n" + "=" * 60)
    print("MCP (Model Context Protocol) Integration Ideas:")
    print("=" * 60)
    
    print("""
    🔌 MCP could enhance job scraping by:
    
    1. **Unified Scraping Interface**:
       - Single MCP server that abstracts Crawl4AI, Firecrawl, BeautifulSoup
       - Claude/LLMs can choose the best method automatically
       
    2. **Intelligent Job Parsing**:
       - MCP server with LLM-powered extraction
       - Understands different job board formats
       - Returns structured data consistently
       
    3. **Workflow Automation**:
       - MCP tool to trigger Temporal workflows
       - Schedule scraping jobs
       - Monitor scraping health
       
    4. **Database Integration**:
       - Direct MCP tools for Neon queries
       - "Find new jobs since yesterday"
       - "Show jobs matching criteria"
    
    Example MCP server structure:
    
    ```python
    @mcp.tool()
    async def scrape_job_board(url: str, strategy: str = "auto"):
        # Auto-detect board type
        # Choose best scraper
        # Return structured jobs
        
    @mcp.tool()
    async def find_matching_jobs(
        keywords: List[str],
        location: Optional[str],
        posted_after: Optional[datetime]
    ):
        # Query Neon database
        # Return filtered results
    ```
    
    This would let Claude/LLMs:
    - "Scrape all tech jobs from Stripe"
    - "Find remote Python jobs posted this week"
    - "Set up daily scraping for these 10 companies"
    """)
    
    print("=" * 60)


async def main():
    """Run comparison and show MCP possibilities"""
    # Run scraper comparison
    comparison = JobScraperComparison()
    await comparison.run_comparison()
    
    # Show MCP integration ideas
    await test_mcp_integration()
    
    print("\n✅ Test complete! Check results above for best approach.")


if __name__ == "__main__":
    asyncio.run(main())