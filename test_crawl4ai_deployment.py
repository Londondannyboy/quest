#!/usr/bin/env python3
"""
Test script to verify Crawl4AI Railway deployment
Tests both job scraping and company scraping scenarios
"""

import asyncio
import httpx
import json
from datetime import datetime


CRAWL4AI_URL = "https://crawl4ai-production-6e85.up.railway.app"


async def test_service_info():
    """Check service version and endpoints"""
    print("\n" + "="*60)
    print("1. SERVICE INFO TEST")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{CRAWL4AI_URL}/")
        data = response.json()
        
        print(f"Service: {data.get('service', 'Unknown')}")
        print(f"Version: {data.get('version', 'Unknown')}")
        print("\nEndpoints:")
        for endpoint, desc in data.get('endpoints', {}).items():
            print(f"  {endpoint}: {desc}")
        
        # Check if it's the new version
        if "/crawl" in data.get('endpoints', {}):
            print("\n✅ New version deployed! Has /crawl endpoint")
            return True
        else:
            print("\n❌ Old version still running. Waiting for deployment...")
            return False


async def test_job_scraping():
    """Test Clay Labs job board scraping"""
    print("\n" + "="*60)
    print("2. JOB SCRAPING TEST (Clay Labs)")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test with JavaScript handling
        payload = {
            "url": "https://jobs.ashbyhq.com/claylabs/",
            "wait_for": "window.__appData",
            "js_code": "return window.__appData",
            "word_count_threshold": 10,
            "bypass_cache": True
        }
        
        print(f"Testing: {payload['url']}")
        print(f"Waiting for: {payload['wait_for']}")
        
        response = await client.post(
            f"{CRAWL4AI_URL}/scrape",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success', False)}")
            print(f"Content length: {data.get('content_length', 0):,} chars")
            
            # Check if we got job data
            content = data.get('markdown', '') or ''
            if content and ('Engineer' in content or 'Developer' in content or 'Manager' in content):
                job_count = content.count('Engineer') + content.count('Developer') + content.count('Manager')
                print(f"✅ Found job-related terms: ~{job_count} mentions")
            else:
                print("❌ No job data found in content")
        else:
            print(f"❌ HTTP {response.status_code}")


async def test_crawl_endpoint():
    """Test the /crawl endpoint for Quest worker"""
    print("\n" + "="*60)
    print("3. CRAWL ENDPOINT TEST (Quest Worker Compatibility)")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {
            "url": "https://www.clay.com",
            "max_pages": 2
        }
        
        print(f"Testing /crawl with: {payload['url']}")
        print(f"Max pages: {payload['max_pages']}")
        
        try:
            response = await client.post(
                f"{CRAWL4AI_URL}/crawl",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success: {data.get('success', False)}")
                print(f"Pages crawled: {data.get('total_pages', 0)}")
                
                # Show page titles
                pages = data.get('pages', [])
                if pages:
                    print("\nPages found:")
                    for i, page in enumerate(pages[:3], 1):
                        print(f"  {i}. {page.get('url', 'Unknown')}")
                        print(f"     Title: {page.get('title', 'No title')}")
                        print(f"     Content size: {len(page.get('content', ''))}")
                
                print("\n✅ /crawl endpoint working! Quest worker will be happy!")
            else:
                print(f"❌ HTTP {response.status_code}")
        except httpx.ConnectError:
            print("❌ /crawl endpoint not found (404)")


async def test_company_research():
    """Test company research scraping scenario"""
    print("\n" + "="*60)
    print("4. COMPANY RESEARCH TEST")
    print("="*60)
    
    test_companies = [
        {"name": "Stripe", "url": "https://stripe.com"},
        {"name": "Anthropic", "url": "https://www.anthropic.com"}
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for company in test_companies:
            print(f"\nTesting {company['name']}: {company['url']}")
            
            response = await client.post(
                f"{CRAWL4AI_URL}/scrape",
                json={
                    "url": company['url'],
                    "word_count_threshold": 10,
                    "bypass_cache": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Success: {data.get('success', False)}")
                print(f"  Content: {data.get('content_length', 0):,} chars")
                links = data.get('links') or []
                print(f"  Links found: {len(links)}")
            else:
                print(f"  ❌ Failed: HTTP {response.status_code}")


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("CRAWL4AI DEPLOYMENT VERIFICATION")
    print("="*70)
    print(f"Testing: {CRAWL4AI_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Check if new version is deployed
    is_new_version = await test_service_info()
    
    if not is_new_version:
        print("\n⏳ Waiting for Railway to deploy the new version...")
        print("   This usually takes 2-5 minutes after git push")
        print("   Run this script again in a minute to check")
        return
    
    # Run all tests
    await test_job_scraping()
    await test_crawl_endpoint()
    await test_company_research()
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("""
    If all tests passed:
    ✅ Crawl4AI is properly deployed
    ✅ Quest worker can now use /crawl endpoint
    ✅ Job scraping with JavaScript works
    ✅ Company research scraping works
    
    The Quest worker will now:
    - Successfully call /crawl endpoint (no more fallback!)
    - Get proper multi-page content
    - Handle JavaScript-heavy sites
    - No longer rely on BeautifulSoup fallback alone
    """)


if __name__ == "__main__":
    asyncio.run(main())