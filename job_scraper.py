#!/usr/bin/env python3
"""
Universal Job Board Scraper for Quest
Supports multiple job board platforms (Ashby, Greenhouse, Lever, etc.)
Can use Crawl4AI service or direct scraping
"""

import asyncio
import json
import re
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
import asyncpg
from dotenv import load_dotenv

load_dotenv()


class JobScraper:
    """Universal job board scraper with Neon DB integration"""
    
    def __init__(self):
        # Get database URL from environment
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL not set in environment")
        
        # Optional Crawl4AI service URL
        self.crawl4ai_url = os.getenv("CRAWL4AI_SERVICE_URL")
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    async def get_db_connection(self):
        """Get database connection"""
        return await asyncpg.connect(self.db_url)
    
    async def get_active_job_boards(self) -> List[Dict[str, Any]]:
        """Get all active job boards from database"""
        conn = await self.get_db_connection()
        try:
            query = """
                SELECT id, company_name, url, board_type, selectors, api_endpoint
                FROM job_boards 
                WHERE is_active = true
                ORDER BY company_name
            """
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def scrape_with_crawl4ai(self, url: str) -> Optional[str]:
        """Use Crawl4AI service if available"""
        if not self.crawl4ai_url:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"url": url}
                async with session.post(
                    f"{self.crawl4ai_url}/scrape",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("markdown") or data.get("content")
        except Exception as e:
            print(f"Crawl4AI service error: {e}")
        
        return None
    
    async def scrape_direct(self, url: str) -> Optional[str]:
        """Direct HTTP scraping fallback"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, ssl=False) as response:
                    if response.status == 200:
                        return await response.text()
        except Exception as e:
            print(f"Direct scrape error: {e}")
        return None
    
    async def scrape_job_board(self, board: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape a single job board"""
        print(f"\n📋 Scraping {board['company_name']} ({board['board_type']})...")
        print(f"   URL: {board['url']}")
        
        # Record start time
        start_time = datetime.now()
        scrape_id = await self.start_scrape_record(board['id'])
        
        try:
            # Get page content (try Crawl4AI first, then direct)
            html = await self.scrape_with_crawl4ai(board['url'])
            if not html:
                print("   Using direct HTTP scraping...")
                html = await self.scrape_direct(board['url'])
            
            if not html:
                raise Exception("Failed to fetch page content")
            
            # Parse jobs based on board type
            jobs = await self.parse_jobs(html, board)
            
            # Save to database
            stats = await self.save_jobs(board['id'], board['company_name'], jobs)
            
            # Update scrape record
            await self.complete_scrape_record(scrape_id, 'success', stats, start_time)
            
            print(f"   ✅ Found {stats['total']} jobs ({stats['new']} new, {stats['updated']} updated)")
            return stats
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            await self.complete_scrape_record(scrape_id, 'failed', None, start_time, str(e))
            return {"error": str(e)}
    
    async def parse_jobs(self, html: str, board: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse jobs based on board type"""
        board_type = board['board_type']
        
        if board_type == 'ashby':
            return self.parse_ashby_jobs(html)
        elif board_type == 'greenhouse':
            return self.parse_greenhouse_jobs(html)
        elif board_type == 'lever':
            return self.parse_lever_jobs(html)
        else:
            return self.parse_generic_jobs(html, board.get('selectors'))
    
    def parse_ashby_jobs(self, html: str) -> List[Dict[str, Any]]:
        """Parse Ashby job board (embedded JSON)"""
        jobs = []
        
        # Extract __appData from script tag
        match = re.search(r'window\.__appData\s*=\s*({.*?});', html, re.DOTALL)
        if match:
            try:
                app_data = json.loads(match.group(1))
                job_postings = app_data.get('jobBoard', {}).get('jobPostings', [])
                
                for job_data in job_postings:
                    if not job_data.get('isListed', False):
                        continue
                    
                    jobs.append({
                        'external_id': job_data.get('id'),
                        'title': job_data.get('title'),
                        'department': job_data.get('departmentName'),
                        'team': job_data.get('teamName'),
                        'location': job_data.get('locationName'),
                        'locations': [loc.get('locationName') for loc in job_data.get('secondaryLocations', [])],
                        'employment_type': job_data.get('employmentType'),
                        'workplace_type': job_data.get('workplaceType'),
                        'url': f"https://jobs.ashbyhq.com/claylabs/{job_data.get('id')}",
                        'compensation': job_data.get('compensationTierSummary'),
                        'posted_date': job_data.get('publishedDate'),
                        'updated_date': job_data.get('updatedAt'),
                        'raw_data': job_data
                    })
            except json.JSONDecodeError as e:
                print(f"   Error parsing Ashby JSON: {e}")
        
        return jobs
    
    def parse_greenhouse_jobs(self, html: str) -> List[Dict[str, Any]]:
        """Parse Greenhouse job board"""
        jobs = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Greenhouse typically has job listings in divs with class "opening"
        for job_elem in soup.find_all('div', class_='opening'):
            job = {}
            
            # Extract link and title
            link_elem = job_elem.find('a')
            if link_elem:
                job['url'] = link_elem.get('href', '')
                job['title'] = link_elem.get_text(strip=True)
                job['external_id'] = job['url'].split('/')[-1] if job['url'] else ''
            
            # Extract location
            location_elem = job_elem.find(class_='location')
            if location_elem:
                job['location'] = location_elem.get_text(strip=True)
            
            if job.get('title'):
                jobs.append(job)
        
        return jobs
    
    def parse_lever_jobs(self, html: str) -> List[Dict[str, Any]]:
        """Parse Lever job board"""
        jobs = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Lever typically has postings in divs with class "posting"
        for job_elem in soup.find_all('div', class_='posting'):
            job = {}
            
            # Extract link and title
            title_elem = job_elem.find('h5')
            if title_elem:
                job['title'] = title_elem.get_text(strip=True)
                link_elem = title_elem.find_parent('a')
                if link_elem:
                    job['url'] = link_elem.get('href', '')
                    job['external_id'] = job['url'].split('/')[-1] if job['url'] else ''
            
            # Extract categories
            for cat in job_elem.find_all(class_='posting-categories'):
                text = cat.get_text(strip=True)
                if 'location' in cat.get('class', []):
                    job['location'] = text
                elif 'department' in cat.get('class', []):
                    job['department'] = text
                elif 'team' in cat.get('class', []):
                    job['team'] = text
            
            if job.get('title'):
                jobs.append(job)
        
        return jobs
    
    def parse_generic_jobs(self, html: str, selectors: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Generic job parser using CSS selectors"""
        jobs = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Default selectors if none provided
        if not selectors:
            selectors = {
                'job_container': 'a[href*="job"], .job-listing, .opening, .position',
                'title': 'h3, h4, h5, .title, .job-title',
                'location': '.location, .office',
                'department': '.department, .team'
            }
        
        # Find job containers
        for job_elem in soup.select(selectors.get('job_container', 'a')):
            job = {}
            
            # Extract title
            if selectors.get('title'):
                title_elem = job_elem.select_one(selectors['title'])
                if title_elem:
                    job['title'] = title_elem.get_text(strip=True)
            
            # Extract URL
            if job_elem.name == 'a':
                job['url'] = job_elem.get('href', '')
            else:
                link = job_elem.find('a')
                if link:
                    job['url'] = link.get('href', '')
            
            # Extract location
            if selectors.get('location'):
                loc_elem = job_elem.select_one(selectors['location'])
                if loc_elem:
                    job['location'] = loc_elem.get_text(strip=True)
            
            # Generate external ID from URL
            if job.get('url'):
                job['external_id'] = job['url'].split('/')[-1] or job['url']
            
            if job.get('title'):
                jobs.append(job)
        
        return jobs
    
    async def save_jobs(self, board_id: str, company_name: str, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Save jobs to database and return statistics"""
        conn = await self.get_db_connection()
        stats = {'total': len(jobs), 'new': 0, 'updated': 0, 'removed': 0}
        
        try:
            # Get existing jobs for this board
            existing = await conn.fetch(
                "SELECT external_id FROM jobs WHERE board_id = $1 AND is_active = true",
                board_id
            )
            existing_ids = {row['external_id'] for row in existing}
            
            # Process each scraped job
            scraped_ids = set()
            for job in jobs:
                external_id = job.get('external_id')
                if not external_id:
                    continue
                
                scraped_ids.add(external_id)
                
                # Prepare job data
                job_data = {
                    'board_id': board_id,
                    'external_id': external_id,
                    'company_name': company_name,
                    'title': job.get('title', ''),
                    'department': job.get('department'),
                    'team': job.get('team'),
                    'location': job.get('location'),
                    'locations': json.dumps(job.get('locations', [])),
                    'employment_type': job.get('employment_type'),
                    'workplace_type': job.get('workplace_type'),
                    'url': job.get('url', ''),
                    'compensation': job.get('compensation'),
                    'posted_date': datetime.strptime(job.get('posted_date'), '%Y-%m-%d').date() if job.get('posted_date') else None,
                    'updated_date': datetime.now(),  # Use current time for simplicity
                    'description_snippet': job.get('description_snippet'),
                    'raw_data': json.dumps(job.get('raw_data', {})),
                    'last_seen_at': datetime.now()
                }
                
                if external_id in existing_ids:
                    # Update existing job
                    await conn.execute("""
                        UPDATE jobs 
                        SET title = $3, department = $4, team = $5, location = $6,
                            locations = $7, employment_type = $8, workplace_type = $9,
                            url = $10, compensation = $11, posted_date = $12,
                            updated_date = $13, description_snippet = $14,
                            raw_data = $15, last_seen_at = $16
                        WHERE board_id = $1 AND external_id = $2
                    """, board_id, external_id, job_data['title'], job_data['department'],
                        job_data['team'], job_data['location'], job_data['locations'],
                        job_data['employment_type'], job_data['workplace_type'],
                        job_data['url'], job_data['compensation'], job_data['posted_date'],
                        job_data['updated_date'], job_data['description_snippet'],
                        job_data['raw_data'], job_data['last_seen_at'])
                    stats['updated'] += 1
                else:
                    # Insert new job
                    await conn.execute("""
                        INSERT INTO jobs (
                            board_id, external_id, company_name, title, department, team,
                            location, locations, employment_type, workplace_type, url,
                            compensation, posted_date, updated_date, description_snippet,
                            raw_data, first_seen_at, last_seen_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $17)
                    """, board_id, external_id, company_name, job_data['title'],
                        job_data['department'], job_data['team'], job_data['location'],
                        job_data['locations'], job_data['employment_type'],
                        job_data['workplace_type'], job_data['url'], job_data['compensation'],
                        job_data['posted_date'], job_data['updated_date'],
                        job_data['description_snippet'], job_data['raw_data'], datetime.now())
                    stats['new'] += 1
            
            # Mark removed jobs as inactive
            removed_ids = existing_ids - scraped_ids
            if removed_ids:
                await conn.execute("""
                    UPDATE jobs 
                    SET is_active = false, last_seen_at = $2
                    WHERE board_id = $1 AND external_id = ANY($3::text[])
                """, board_id, datetime.now(), list(removed_ids))
                stats['removed'] = len(removed_ids)
            
            # Update last scraped time for board
            await conn.execute("""
                UPDATE job_boards 
                SET last_scraped_at = $2, last_error = NULL
                WHERE id = $1
            """, board_id, datetime.now())
            
        finally:
            await conn.close()
        
        return stats
    
    async def start_scrape_record(self, board_id: str) -> str:
        """Create a scrape history record"""
        conn = await self.get_db_connection()
        try:
            scrape_id = await conn.fetchval("""
                INSERT INTO scrape_history (board_id, status)
                VALUES ($1, 'running')
                RETURNING id
            """, board_id)
            return scrape_id
        finally:
            await conn.close()
    
    async def complete_scrape_record(self, scrape_id: str, status: str, stats: Optional[Dict], 
                                    start_time: datetime, error: Optional[str] = None):
        """Update scrape history record"""
        conn = await self.get_db_connection()
        try:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if stats:
                await conn.execute("""
                    UPDATE scrape_history 
                    SET status = $2, completed_at = $3, execution_time_ms = $4,
                        jobs_found = $5, new_jobs = $6, removed_jobs = $7, updated_jobs = $8
                    WHERE id = $1
                """, scrape_id, status, datetime.now(), execution_time,
                    stats.get('total'), stats.get('new'), stats.get('removed'), stats.get('updated'))
            else:
                await conn.execute("""
                    UPDATE scrape_history 
                    SET status = $2, completed_at = $3, execution_time_ms = $4, error_message = $5
                    WHERE id = $1
                """, scrape_id, status, datetime.now(), execution_time, error)
        finally:
            await conn.close()
    
    async def scrape_all_boards(self):
        """Scrape all active job boards"""
        boards = await self.get_active_job_boards()
        
        print(f"\n{'='*60}")
        print(f"JOB BOARD SCRAPER")
        print(f"{'='*60}")
        print(f"Found {len(boards)} active job board(s) to scrape")
        
        if self.crawl4ai_url:
            print(f"Using Crawl4AI service: {self.crawl4ai_url}")
        else:
            print("Crawl4AI service not configured, using direct scraping")
        
        total_stats = {'boards': 0, 'jobs': 0, 'new': 0, 'errors': 0}
        
        for board in boards:
            result = await self.scrape_job_board(board)
            if 'error' in result:
                total_stats['errors'] += 1
            else:
                total_stats['boards'] += 1
                total_stats['jobs'] += result.get('total', 0)
                total_stats['new'] += result.get('new', 0)
        
        print(f"\n{'='*60}")
        print(f"SUMMARY:")
        print(f"  Boards scraped: {total_stats['boards']}")
        print(f"  Total jobs: {total_stats['jobs']}")
        print(f"  New jobs: {total_stats['new']}")
        if total_stats['errors'] > 0:
            print(f"  Errors: {total_stats['errors']}")
        print(f"{'='*60}\n")
        
        return total_stats


async def add_job_board(company_name: str, url: str, board_type: str = 'custom'):
    """Add a new job board to scrape"""
    scraper = JobScraper()
    conn = await scraper.get_db_connection()
    
    try:
        # Auto-detect board type if not specified
        if board_type == 'auto':
            if 'ashbyhq.com' in url:
                board_type = 'ashby'
            elif 'greenhouse.io' in url:
                board_type = 'greenhouse'
            elif 'lever.co' in url:
                board_type = 'lever'
            elif 'workday.com' in url:
                board_type = 'workday'
            else:
                board_type = 'custom'
        
        board_id = await conn.fetchval("""
            INSERT INTO job_boards (company_name, url, board_type)
            VALUES ($1, $2, $3)
            ON CONFLICT (url) DO UPDATE
            SET company_name = EXCLUDED.company_name,
                board_type = EXCLUDED.board_type,
                is_active = true
            RETURNING id
        """, company_name, url, board_type)
        
        print(f"✅ Added job board: {company_name} ({board_type})")
        print(f"   URL: {url}")
        print(f"   ID: {board_id}")
        
        return board_id
    finally:
        await conn.close()


async def main():
    """Main entry point"""
    scraper = JobScraper()
    
    # Example: Add more job boards
    # await add_job_board("Stripe", "https://stripe.com/jobs", "auto")
    # await add_job_board("Anthropic", "https://jobs.ashbyhq.com/anthropic", "ashby")
    
    # Scrape all boards
    await scraper.scrape_all_boards()


if __name__ == "__main__":
    asyncio.run(main())