#!/usr/bin/env python3
"""
Enhanced Crawl4AI Scraper for Quest
Uses advanced Crawl4AI features for intelligent data extraction
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime


CRAWL4AI_URL = "https://crawl4ai-production-6e85.up.railway.app"


class EnhancedCrawl4AIScraper:
    """
    Advanced Crawl4AI scraper using full feature set:
    1. Natural language prompts for extraction
    2. Structured JSON with schemas
    3. Batch scraping
    4. Actions (click, scroll, wait)
    5. Multiple output formats
    """
    
    def __init__(self):
        self.base_url = CRAWL4AI_URL
    
    async def extract_jobs_with_ai(self, url: str) -> Dict[str, Any]:
        """
        Use Crawl4AI's /extract endpoint with natural language prompts
        This is what we SHOULD be using for job boards!
        """
        
        # Define the exact structure we want
        job_schema = {
            "type": "object",
            "properties": {
                "jobs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "department": {"type": "string"},
                            "location": {"type": "string"},
                            "employment_type": {"type": "string"},
                            "posted_date": {"type": "string"},
                            "url": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    }
                },
                "company": {"type": "string"},
                "total_jobs": {"type": "integer"}
            }
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/extract",
                json={
                    "url": url,
                    "schema": job_schema,
                    "strategy": "json_css"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            return {"success": False}
    
    async def scrape_with_actions(self, url: str) -> Dict[str, Any]:
        """
        Scrape with page interactions (click Load More, scroll, etc.)
        Perfect for infinite scroll job boards or paginated content
        """
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/scrape",
                json={
                    "url": url,
                    "actions": [
                        {"type": "scroll", "selector": "body"},  # Scroll to load content
                        {"type": "wait", "duration": 2},         # Wait for content
                        {"type": "click", "selector": ".load-more"},  # Click load more
                        {"type": "wait", "duration": 2}
                    ],
                    "wait_for": "[data-testid='job-listing']",  # Wait for jobs
                    "strategy": "markdown"
                }
            )
            
            return response.json() if response.status_code == 200 else {"success": False}
    
    async def batch_scrape_companies(self, company_urls: List[str]) -> List[Dict]:
        """
        Scrape multiple company sites in parallel
        This is what Quest worker SHOULD do for company research!
        """
        
        async def scrape_company(url: str) -> Dict:
            async with httpx.AsyncClient(timeout=60) as client:
                # Use natural language to extract company info
                prompt = """
                Extract the following information from this company website:
                1. Company name
                2. Industry/sector
                3. Key products or services
                4. Recent news or announcements
                5. Leadership team members
                6. Office locations
                7. Contact information
                """
                
                response = await client.post(
                    f"{self.base_url}/scrape",
                    json={
                        "url": url,
                        "prompt": prompt,
                        "strategy": "markdown",
                        "max_pages": 3  # Crawl up to 3 pages
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "url": url,
                        "success": True,
                        "content": data.get("markdown", ""),
                        "extracted_at": datetime.now().isoformat()
                    }
                
                return {"url": url, "success": False}
        
        # Run all scrapes in parallel
        tasks = [scrape_company(url) for url in company_urls]
        results = await asyncio.gather(*tasks)
        
        return results
    
    async def extract_news_articles(self, news_site_url: str) -> Dict[str, Any]:
        """
        Extract structured article data from news sites
        Perfect for Quest's article discovery!
        """
        
        article_schema = {
            "type": "object",
            "properties": {
                "articles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "headline": {"type": "string"},
                            "author": {"type": "string"},
                            "published_date": {"type": "string"},
                            "category": {"type": "string"},
                            "summary": {"type": "string"},
                            "url": {"type": "string"},
                            "mentions_companies": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
        
        prompt = """
        Extract all news articles from this page.
        For each article, identify:
        - The headline
        - Author name
        - Publication date
        - Article category or section
        - Brief summary (first 2 sentences)
        - Direct URL to the full article
        - Any companies mentioned in the headline or summary
        """
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/extract",
                json={
                    "url": news_site_url,
                    "prompt": prompt,
                    "schema": article_schema,
                    "strategy": "json_css"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            return {"success": False}
    
    async def deep_crawl_with_search(self, domain: str, search_terms: List[str]) -> Dict:
        """
        Deep crawl a site looking for specific content
        Perfect for finding specific information about companies
        """
        
        search_query = " OR ".join(search_terms)
        
        async with httpx.AsyncClient(timeout=60) as client:
            # First, map the site
            map_response = await client.post(
                f"{self.base_url}/map",
                json={"url": f"https://{domain}"}
            )
            
            if map_response.status_code != 200:
                return {"success": False}
            
            urls = map_response.json().get("urls", [])
            
            # Then search for specific content
            relevant_pages = []
            for url in urls[:20]:  # Limit to 20 pages
                response = await client.post(
                    f"{self.base_url}/scrape",
                    json={
                        "url": url,
                        "strategy": "markdown"
                    }
                )
                
                if response.status_code == 200:
                    content = response.json().get("markdown", "")
                    
                    # Check if any search terms appear
                    if any(term.lower() in content.lower() for term in search_terms):
                        relevant_pages.append({
                            "url": url,
                            "matches": [term for term in search_terms if term.lower() in content.lower()],
                            "preview": content[:500]
                        })
            
            return {
                "success": True,
                "domain": domain,
                "total_pages": len(urls),
                "relevant_pages": relevant_pages
            }


class QuestWorkerEnhancements:
    """
    Specific enhancements for Quest worker using Crawl4AI
    """
    
    def __init__(self):
        self.scraper = EnhancedCrawl4AIScraper()
    
    async def intelligent_company_research(self, company_name: str, company_url: str) -> Dict:
        """
        Full company research using AI extraction
        This replaces the basic crawl with intelligent extraction
        """
        
        print(f"\n🔍 Researching {company_name}...")
        
        # 1. Extract structured company data
        company_prompt = f"""
        Research {company_name} and extract:
        1. Company Overview:
           - Founded year
           - Headquarters location
           - Number of employees
           - Annual revenue (if public)
           - Industry/sector
        
        2. Business Model:
           - Main products/services
           - Target customers
           - Key differentiators
           - Pricing model (if available)
        
        3. Recent Developments:
           - Latest news (last 3 months)
           - Product launches
           - Partnerships
           - Funding rounds
        
        4. Leadership:
           - CEO name
           - Key executives
           - Board members
        
        5. Technology Stack:
           - Technologies used
           - Open source contributions
           - Engineering blog topics
        
        6. Culture:
           - Company values
           - Remote/hybrid policy
           - Benefits mentioned
        """
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{CRAWL4AI_URL}/crawl",
                json={
                    "url": company_url,
                    "max_pages": 5,  # Crawl up to 5 pages
                    "prompt": company_prompt
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Structure the extracted information
                return {
                    "company": company_name,
                    "url": company_url,
                    "pages_analyzed": len(data.get("pages", [])),
                    "research_data": data.get("pages", []),
                    "timestamp": datetime.now().isoformat()
                }
        
        return {"success": False}
    
    async def discover_company_articles(self, company_name: str, news_sites: List[str]) -> List[Dict]:
        """
        Find articles mentioning a specific company across news sites
        """
        
        all_articles = []
        
        for news_site in news_sites:
            # Search for company mentions
            search_result = await self.scraper.deep_crawl_with_search(
                domain=news_site,
                search_terms=[company_name, f'"{company_name}"']
            )
            
            if search_result.get("success"):
                for page in search_result.get("relevant_pages", []):
                    all_articles.append({
                        "source": news_site,
                        "url": page["url"],
                        "mentions": page["matches"],
                        "preview": page["preview"]
                    })
        
        return all_articles
    
    async def monitor_competitor_jobs(self, competitors: List[Dict[str, str]]) -> Dict:
        """
        Monitor job postings from multiple competitors
        """
        
        results = {}
        
        for competitor in competitors:
            name = competitor["name"]
            job_board_url = competitor["job_board_url"]
            
            # Extract jobs with AI
            job_data = await self.scraper.extract_jobs_with_ai(job_board_url)
            
            if job_data.get("success"):
                results[name] = {
                    "total_jobs": job_data.get("data", {}).get("total_jobs", 0),
                    "jobs": job_data.get("data", {}).get("jobs", []),
                    "last_checked": datetime.now().isoformat()
                }
        
        return results


async def demonstrate_enhanced_features():
    """
    Demonstrate what we COULD be doing with Crawl4AI
    """
    print("=" * 60)
    print("CRAWL4AI ENHANCED FEATURES DEMONSTRATION")
    print("=" * 60)
    
    scraper = EnhancedCrawl4AIScraper()
    worker = QuestWorkerEnhancements()
    
    print("\n1. INTELLIGENT COMPANY RESEARCH")
    print("-" * 40)
    print("Instead of just crawling, we could extract structured data:")
    print("  • Company overview with founded year, revenue, employees")
    print("  • Business model and products")
    print("  • Recent news and developments")
    print("  • Leadership team")
    print("  • Technology stack")
    
    print("\n2. BATCH COMPANY SCRAPING")
    print("-" * 40)
    print("Scrape 10+ companies in parallel instead of sequentially")
    
    print("\n3. NEWS ARTICLE DISCOVERY")
    print("-" * 40)
    print("Extract structured article data:")
    print("  • Headlines, authors, dates")
    print("  • Company mentions")
    print("  • Categories and summaries")
    
    print("\n4. DEEP SEARCH CAPABILITIES")
    print("-" * 40)
    print("Search entire websites for specific mentions:")
    print("  • Find all pages mentioning a company")
    print("  • Extract relevant context")
    print("  • Track competitor mentions")
    
    print("\n5. INTERACTIVE SCRAPING")
    print("-" * 40)
    print("Handle dynamic content with actions:")
    print("  • Click 'Load More' buttons")
    print("  • Scroll infinite feeds")
    print("  • Wait for content to load")
    print("  • Fill search forms")
    
    print("\n" + "=" * 60)
    print("CURRENT VS POTENTIAL")
    print("=" * 60)
    
    print("\nCURRENT Quest Worker:")
    print("  ❌ Basic /crawl endpoint")
    print("  ❌ No structured extraction")
    print("  ❌ Sequential processing")
    print("  ❌ No AI intelligence")
    
    print("\nPOTENTIAL with Enhanced Crawl4AI:")
    print("  ✅ AI-powered extraction with schemas")
    print("  ✅ Parallel batch processing")
    print("  ✅ Natural language prompts")
    print("  ✅ Deep search and discovery")
    print("  ✅ Interactive page handling")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(demonstrate_enhanced_features())