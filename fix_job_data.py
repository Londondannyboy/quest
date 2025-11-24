#!/usr/bin/env python3
"""
Fix job data in Neon database:
1. Add proper columns for job details
2. Create job_details table for full descriptions
3. Re-extract data with all fields
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
import asyncpg
from dotenv import load_dotenv
import re

load_dotenv()


async def update_database_schema():
    """Add missing columns and create job_details table"""
    
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)
    
    try:
        print("📊 UPDATING DATABASE SCHEMA")
        print("="*60)
        
        # Add missing columns to jobs table
        columns_to_add = [
            ("employment_type", "VARCHAR(100)"),
            ("workplace_type", "VARCHAR(100)"),
            ("salary_min", "INTEGER"),
            ("salary_max", "INTEGER"),
            ("salary_currency", "VARCHAR(10)"),
            ("application_deadline", "DATE")
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                await conn.execute(f"""
                    ALTER TABLE jobs 
                    ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                """)
                print(f"✅ Added column: {column_name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  Column {column_name} already exists")
                else:
                    print(f"❌ Error adding {column_name}: {e}")
        
        # Create job_details table for full descriptions
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS job_details (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
                full_description TEXT,
                requirements TEXT[],
                responsibilities TEXT[],
                benefits TEXT[],
                qualifications TEXT[],
                nice_to_have TEXT[],
                about_team TEXT,
                about_company TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(job_id)
            )
        """)
        print("✅ Created job_details table")
        
        # Create a view for easy access
        await conn.execute("""
            CREATE OR REPLACE VIEW job_listings AS
            SELECT 
                j.id,
                j.company_name,
                j.title,
                j.department,
                j.location,
                j.employment_type,
                j.workplace_type,
                j.url,
                j.salary_min,
                j.salary_max,
                j.salary_currency,
                j.description_snippet,
                jd.full_description,
                jd.requirements,
                jd.responsibilities,
                jd.benefits,
                j.posted_date,
                j.updated_date
            FROM jobs j
            LEFT JOIN job_details jd ON j.id = jd.job_id
            WHERE j.is_active = true
        """)
        print("✅ Created job_listings view")
        
        print("\n✅ Schema updated successfully!")
        
    finally:
        await conn.close()


async def extract_job_from_ashby_page(url: str) -> dict:
    """Extract complete job data from an Ashby job page"""
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        
        if response.status_code != 200:
            return None
        
        html = response.text
        
        # Extract __appData
        match = re.search(r'window\.__appData\s*=\s*({.*?});', html, re.DOTALL)
        if not match:
            return None
        
        try:
            app_data = json.loads(match.group(1))
            posting = app_data.get('posting', {})
            org = app_data.get('organization', {})
            
            # Extract all fields
            job_data = {
                'title': posting.get('title', ''),
                'department': posting.get('departmentName', ''),
                'team': posting.get('teamName', ''),
                'location': posting.get('locationName', ''),
                'employment_type': posting.get('employmentType', ''),
                'workplace_type': posting.get('workplaceType', ''),
                'is_remote': posting.get('isRemote', False),
                'company_name': org.get('name', ''),
                'published_date': posting.get('publishedDate'),
                'application_deadline': posting.get('applicationDeadline'),
                
                # Full description
                'description_html': posting.get('descriptionHtml', ''),
                'description_plain': posting.get('descriptionPlainText', ''),
                
                # Compensation
                'compensation_summary': posting.get('scrapeableCompensationSalarySummary', ''),
                'compensation_tiers': posting.get('compensationTiers', []),
                
                # Additional fields
                'address': posting.get('address', {}),
                'job_id': posting.get('jobId', ''),
                'external_id': posting.get('id', ''),
            }
            
            # Parse description to extract sections
            sections = parse_job_description(job_data['description_plain'])
            job_data.update(sections)
            
            return job_data
            
        except Exception as e:
            print(f"Error parsing Ashby data: {e}")
            return None


def parse_job_description(description: str) -> dict:
    """Parse job description into structured sections"""
    
    sections = {
        'requirements': [],
        'responsibilities': [],
        'benefits': [],
        'qualifications': [],
        'nice_to_have': [],
        'about_team': '',
        'about_company': '',
        'overview': ''
    }
    
    if not description:
        return sections
    
    lines = description.split('\n')
    current_section = None
    current_content = []
    
    section_patterns = {
        'requirements': r'(?i)(requirements?|required|you.?ll need|must have|minimum qualifications)',
        'responsibilities': r'(?i)(responsibilities|what you.?ll do|key responsibilities|you will)',
        'benefits': r'(?i)(benefits|perks|what we offer|compensation)',
        'qualifications': r'(?i)(qualifications|nice to have|preferred|ideal|bonus)',
        'about_team': r'(?i)(about the team|team)',
        'about_company': r'(?i)(about (h|clay|lovable|the company))',
        'overview': r'(?i)(overview|about the role|position)'
    }
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this is a section header
        section_found = False
        for section_name, pattern in section_patterns.items():
            if re.search(pattern, line):
                # Save previous section
                if current_section and current_content:
                    if current_section in ['requirements', 'responsibilities', 'benefits', 'qualifications', 'nice_to_have']:
                        sections[current_section] = clean_list_items(current_content)
                    else:
                        sections[current_section] = '\n'.join(current_content)
                
                current_section = section_name
                current_content = []
                section_found = True
                break
        
        if not section_found and current_section:
            current_content.append(line)
    
    # Save last section
    if current_section and current_content:
        if current_section in ['requirements', 'responsibilities', 'benefits', 'qualifications', 'nice_to_have']:
            sections[current_section] = clean_list_items(current_content)
        else:
            sections[current_section] = '\n'.join(current_content)
    
    # If no overview found, use first paragraph
    if not sections['overview'] and description:
        paragraphs = description.split('\n\n')
        sections['overview'] = paragraphs[0] if paragraphs else ''
    
    return sections


def clean_list_items(items: list) -> list:
    """Clean and format list items"""
    cleaned = []
    for item in items:
        # Remove bullet points and numbers
        item = re.sub(r'^[\s\-\*\•\◦\▪\→\d\.]+', '', item).strip()
        if item and len(item) > 5:  # Skip very short items
            cleaned.append(item)
    return cleaned


async def rescrape_all_jobs():
    """Rescrape all jobs to get complete data"""
    
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)
    
    try:
        print("\n🕷️ RESCRAPING ALL JOBS FOR COMPLETE DATA")
        print("="*60)
        
        # Get all jobs
        jobs = await conn.fetch("""
            SELECT id, title, url, company_name
            FROM jobs 
            WHERE is_active = true 
            AND url IS NOT NULL
            ORDER BY company_name, title
        """)
        
        print(f"Found {len(jobs)} jobs to rescrape\n")
        
        success_count = 0
        for i, job in enumerate(jobs, 1):
            print(f"{i}/{len(jobs)}: {job['company_name']} - {job['title']}")
            
            # Extract complete job data
            job_data = await extract_job_from_ashby_page(job['url'])
            
            if job_data:
                # Update jobs table
                await conn.execute("""
                    UPDATE jobs SET
                        department = $2,
                        location = $3,
                        employment_type = $4,
                        workplace_type = $5,
                        description_snippet = $6,
                        updated_date = CURRENT_TIMESTAMP
                    WHERE id = $1
                """, job['id'], 
                    job_data.get('department', ''),
                    job_data.get('location', ''),
                    job_data.get('employment_type', ''),
                    job_data.get('workplace_type', ''),
                    job_data.get('overview', '')[:500]
                )
                
                # Insert/update job_details
                await conn.execute("""
                    INSERT INTO job_details (
                        job_id, full_description, requirements, responsibilities, 
                        benefits, qualifications, about_team, about_company
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (job_id) DO UPDATE SET
                        full_description = EXCLUDED.full_description,
                        requirements = EXCLUDED.requirements,
                        responsibilities = EXCLUDED.responsibilities,
                        benefits = EXCLUDED.benefits,
                        qualifications = EXCLUDED.qualifications,
                        about_team = EXCLUDED.about_team,
                        about_company = EXCLUDED.about_company,
                        updated_at = CURRENT_TIMESTAMP
                """, job['id'],
                    job_data.get('description_plain', ''),
                    job_data.get('requirements', []),
                    job_data.get('responsibilities', []),
                    job_data.get('benefits', []),
                    job_data.get('qualifications', []),
                    job_data.get('about_team', ''),
                    job_data.get('about_company', '')
                )
                
                # Update raw_data with complete info
                await conn.execute("""
                    UPDATE jobs SET
                        raw_data = $2::jsonb
                    WHERE id = $1
                """, job['id'], json.dumps(job_data))
                
                success_count += 1
                print(f"  ✅ Updated with {len(job_data.get('requirements', []))} requirements, {len(job_data.get('responsibilities', []))} responsibilities")
            else:
                print(f"  ❌ Failed to extract data")
            
            # Small delay to be respectful
            if i % 10 == 0:
                await asyncio.sleep(1)
        
        print(f"\n✅ Successfully updated {success_count}/{len(jobs)} jobs")
        
    finally:
        await conn.close()


async def show_final_results():
    """Show the improved data"""
    
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)
    
    try:
        print("\n📊 FINAL RESULTS - COMPLETE JOB DATA")
        print("="*60)
        
        # Sample from job_listings view
        samples = await conn.fetch("""
            SELECT * FROM job_listings 
            WHERE full_description IS NOT NULL
            LIMIT 3
        """)
        
        for job in samples:
            print(f"\n🎯 {job['company_name']}: {job['title']}")
            print(f"  📍 Location: {job['location']}")
            print(f"  🏢 Department: {job['department']}")
            print(f"  💼 Type: {job['employment_type']}")
            print(f"  🏠 Workplace: {job['workplace_type']}")
            
            if job['requirements']:
                print(f"  📋 Requirements: {len(job['requirements'])} items")
                for req in job['requirements'][:3]:
                    print(f"    • {req[:80]}")
            
            if job['full_description']:
                print(f"  📝 Description: {job['full_description'][:200]}...")
        
        # Overall stats
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_jobs,
                COUNT(CASE WHEN department IS NOT NULL AND department != '' THEN 1 END) as with_dept,
                COUNT(CASE WHEN location IS NOT NULL AND location != '' THEN 1 END) as with_location,
                COUNT(CASE WHEN employment_type IS NOT NULL AND employment_type != '' THEN 1 END) as with_type,
                COUNT(jd.job_id) as with_details
            FROM jobs j
            LEFT JOIN job_details jd ON j.id = jd.job_id
            WHERE j.is_active = true
        """)
        
        print(f"\n📈 COVERAGE:")
        print(f"  Total jobs: {stats['total_jobs']}")
        print(f"  With department: {stats['with_dept']} ({stats['with_dept']*100//stats['total_jobs']}%)")
        print(f"  With location: {stats['with_location']} ({stats['with_location']*100//stats['total_jobs']}%)")
        print(f"  With employment type: {stats['with_type']} ({stats['with_type']*100//stats['total_jobs']}%)")
        print(f"  With full details: {stats['with_details']} ({stats['with_details']*100//stats['total_jobs']}%)")
        
    finally:
        await conn.close()


async def main():
    # Step 1: Update schema
    await update_database_schema()
    
    # Step 2: Rescrape all jobs
    await rescrape_all_jobs()
    
    # Step 3: Show results
    await show_final_results()


if __name__ == "__main__":
    asyncio.run(main())