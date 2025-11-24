#!/usr/bin/env python3
"""
Test extracting job details from Ashby detail pages
Check if data is embedded in HTML like the listing page
"""

import asyncio
import httpx
import json
import re


async def test_ashby_job_detail():
    """Test if Ashby embeds job data in detail pages"""
    
    job_url = "https://jobs.ashbyhq.com/claylabs/55694518-a6ac-4f46-8ec8-ffbf8ab39917"
    
    print(f"Testing Ashby job detail page: {job_url}")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Get the raw HTML
        response = await client.get(job_url)
        
        if response.status_code == 200:
            html = response.text
            
            print(f"✅ Got HTML: {len(html)} chars")
            
            # Look for embedded data patterns
            patterns = [
                (r'window\.__appData\s*=\s*({.*?});', '__appData'),
                (r'window\.__INITIAL_STATE__\s*=\s*({.*?});', '__INITIAL_STATE__'),
                (r'<script[^>]*type="application/ld\+json"[^>]*>({.*?})</script>', 'ld+json'),
                (r'data-job="({.*?})"', 'data-job attribute'),
            ]
            
            for pattern, name in patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                if matches:
                    print(f"\n✅ Found {name}!")
                    for i, match in enumerate(matches[:1], 1):  # Just first match
                        try:
                            data = json.loads(match)
                            print(f"  Data keys: {list(data.keys())[:10]}")
                            
                            # Look for job-related fields
                            if 'jobPosting' in data:
                                job = data['jobPosting']
                                print(f"  Job title: {job.get('title', 'N/A')}")
                                print(f"  Description preview: {str(job.get('description', ''))[:200]}")
                            elif 'job' in data:
                                job = data['job']
                                print(f"  Job info found: {list(job.keys())[:5]}")
                            
                            # Check for nested job data
                            for key in ['props', 'pageProps', 'initialData']:
                                if key in data:
                                    nested = data[key]
                                    if isinstance(nested, dict):
                                        print(f"  Found {key}: {list(nested.keys())[:5]}")
                                        if 'job' in nested or 'jobPosting' in nested:
                                            print(f"    → Contains job data!")
                            
                        except json.JSONDecodeError as e:
                            print(f"  Could not parse JSON: {e}")
                            # Show raw content preview
                            print(f"  Raw preview: {match[:200]}...")
                else:
                    print(f"\n❌ No {name} found")
            
            # Check for other job content patterns in HTML
            print("\n🔍 Checking for job content in HTML...")
            
            # Look for job description sections
            if "About the Role" in html or "Responsibilities" in html or "Requirements" in html:
                print("✅ Found job section headers in HTML")
                
                # Count occurrences
                sections = ["About the Role", "Responsibilities", "Requirements", "Benefits", "Qualifications"]
                for section in sections:
                    if section in html:
                        print(f"  • {section}: Found")
            
            # Check if content might be server-rendered
            if "<h1" in html and ("Growth Strategist" in html or "Customer Success" in html):
                print("✅ Job title appears to be server-rendered")
            
            # Save a sample of HTML for inspection
            with open("/tmp/ashby_detail.html", "w") as f:
                f.write(html)
            print(f"\n💾 Saved HTML to /tmp/ashby_detail.html for inspection")
            
        else:
            print(f"❌ Failed to get page: {response.status_code}")


async def main():
    await test_ashby_job_detail()


if __name__ == "__main__":
    asyncio.run(main())