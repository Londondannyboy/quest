#!/usr/bin/env python3
"""
Create UK/EU Tech Job Market Graph in Zep
Using AsyncZep client with proper graph API
"""

import asyncio
import asyncpg
import json
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv
import os
from zep_cloud.client import AsyncZep

load_dotenv()


class JobMarketGraph:
    """Build job market knowledge graph in Zep"""
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.zep_api_key = "z_1dWlkIjoiMmNkYWVjZjktYTU5Ny00ZDlkLWIyMWItNTZjOWI5OTE5MTE4In0.Ssyb_PezcGgacQFq6Slg3fyFoqs8hBhvp6WsE8rO4VK_D70CT5tqDbFOs6ZTf8rw7qYfTRhLz5YFm8RR854rHg"
        self.graph_id = "finance-knowledge"  # Using existing graph
        self.client = AsyncZep(api_key=self.zep_api_key)
    
    async def fetch_data(self) -> Dict:
        """Fetch job data with proper company relationships from Neon"""
        
        conn = await asyncpg.connect(self.db_url)
        try:
            print("📊 Fetching job market data from Neon...")
            
            # Get companies (job_boards table)
            companies = await conn.fetch("""
                SELECT 
                    id as board_id,
                    company_name,
                    url as website,
                    board_type,
                    (SELECT COUNT(*) FROM jobs WHERE board_id = job_boards.id) as job_count
                FROM job_boards
                WHERE is_active = true
            """)
            
            # Get jobs with all details
            jobs = await conn.fetch("""
                SELECT 
                    j.id,
                    j.board_id,
                    j.title,
                    j.department,
                    j.location,
                    j.employment_type,
                    j.workplace_type,
                    j.url,
                    j.posted_date,
                    j.full_description,
                    j.description_snippet,
                    j.requirements,
                    j.responsibilities,
                    j.benefits,
                    jb.company_name,
                    jb.url as company_website
                FROM jobs j
                JOIN job_boards jb ON j.board_id = jb.id
                WHERE j.is_active = true
                ORDER BY j.company_name, j.title
            """)
            
            # Get unique locations with counts
            locations = await conn.fetch("""
                SELECT 
                    j.location,
                    COUNT(*) as job_count,
                    array_agg(DISTINCT jb.company_name) as companies
                FROM jobs j
                JOIN job_boards jb ON j.board_id = jb.id
                WHERE j.is_active = true 
                    AND j.location IS NOT NULL 
                    AND j.location != ''
                GROUP BY j.location
                ORDER BY job_count DESC
            """)
            
            # Get departments by company
            departments = await conn.fetch("""
                SELECT 
                    j.department,
                    jb.company_name,
                    j.board_id,
                    COUNT(*) as job_count,
                    array_agg(DISTINCT j.title) as job_titles
                FROM jobs j
                JOIN job_boards jb ON j.board_id = jb.id
                WHERE j.is_active = true 
                    AND j.department IS NOT NULL 
                    AND j.department != ''
                GROUP BY j.department, jb.company_name, j.board_id
                ORDER BY jb.company_name, j.department
            """)
            
            print(f"✅ Fetched:")
            print(f"   • {len(companies)} companies")
            print(f"   • {len(jobs)} active jobs")
            print(f"   • {len(locations)} locations")
            print(f"   • {len(departments)} departments")
            
            return {
                "companies": [dict(c) for c in companies],
                "jobs": [dict(j) for j in jobs],
                "locations": [dict(l) for l in locations],
                "departments": [dict(d) for d in departments]
            }
            
        finally:
            await conn.close()
    
    def extract_skills(self, job: Dict) -> List[str]:
        """Extract technical skills from job data"""
        
        skills = set()
        
        # Common tech skills to identify
        tech_skills = {
            # Languages
            "Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "C++", "Ruby", "Swift", "Kotlin",
            # Frontend
            "React", "Vue", "Angular", "Next.js", "HTML", "CSS", "Tailwind",
            # Backend
            "Node.js", "Django", "FastAPI", "Flask", "Spring", "Express",
            # Databases
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
            # Cloud & DevOps
            "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform", "CI/CD",
            # AI/ML
            "Machine Learning", "Deep Learning", "NLP", "LLM", "TensorFlow", "PyTorch",
            # Other
            "GraphQL", "REST", "Microservices", "Git", "Linux", "Agile"
        }
        
        # Check title, requirements, and description
        text_to_check = f"{job.get('title', '')} {' '.join(job.get('requirements', []))} {job.get('description_snippet', '')}"
        text_lower = text_to_check.lower()
        
        for skill in tech_skills:
            if skill.lower() in text_lower:
                skills.add(skill)
        
        return list(skills)
    
    def determine_seniority(self, title: str) -> str:
        """Determine seniority level from job title"""
        
        title_lower = title.lower()
        
        if any(term in title_lower for term in ["intern", "graduate", "entry", "junior"]):
            return "Junior"
        elif any(term in title_lower for term in ["senior", "sr.", "lead"]):
            return "Senior"
        elif any(term in title_lower for term in ["staff", "principal", "architect"]):
            return "Staff+"
        elif any(term in title_lower for term in ["head", "director", "vp", "chief"]):
            return "Executive"
        elif "manager" in title_lower:
            return "Manager"
        else:
            return "Mid-level"
    
    async def create_graph(self, data: Dict):
        """Create the job market graph in Zep"""
        
        print("\n🌐 Creating Job Market Graph in Zep...")
        print("="*60)
        
        try:
            # Create companies as graph entities
            print("\n1️⃣ Adding companies to graph...")
            for company in data["companies"]:
                company_data = {
                    "type": "company",
                    "id": str(company["board_id"]),
                    "name": company["company_name"],
                    "website": company["website"],
                    "board_type": company["board_type"],
                    "job_count": company["job_count"],
                    "industry": "Technology"
                }
                
                response = await self.client.graph.add(
                    graph_id=self.graph_id,
                    type="json",
                    data=json.dumps(company_data)
                )
                print(f"  ✅ Added company: {company['company_name']} ({company['job_count']} jobs)")
            
            # Create locations as graph entities
            print("\n2️⃣ Adding locations to graph...")
            for location in data["locations"][:10]:  # Top 10 locations
                location_data = {
                    "type": "location",
                    "name": location["location"],
                    "job_count": location["job_count"],
                    "companies": location["companies"][:5]  # First 5 companies
                }
                
                response = await self.client.graph.add(
                    graph_id=self.graph_id,
                    type="json",
                    data=json.dumps(location_data)
                )
                print(f"  ✅ Added location: {location['location']} ({location['job_count']} jobs)")
            
            # Create departments as graph entities
            print("\n3️⃣ Adding departments to graph...")
            for dept in data["departments"][:20]:  # Top 20 departments
                dept_data = {
                    "type": "department",
                    "name": dept["department"],
                    "company": dept["company_name"],
                    "company_id": str(dept["board_id"]),
                    "job_count": dept["job_count"],
                    "job_titles": dept["job_titles"][:5]  # Sample job titles
                }
                
                response = await self.client.graph.add(
                    graph_id=self.graph_id,
                    type="json",
                    data=json.dumps(dept_data)
                )
                print(f"  ✅ Added department: {dept['department']} at {dept['company_name']}")
            
            # Create jobs with relationships
            print("\n4️⃣ Adding jobs to graph...")
            
            # Group jobs by company for better organization
            jobs_by_company = {}
            for job in data["jobs"]:
                company = job["company_name"]
                if company not in jobs_by_company:
                    jobs_by_company[company] = []
                jobs_by_company[company].append(job)
            
            total_jobs_added = 0
            for company_name, company_jobs in jobs_by_company.items():
                print(f"\n  Adding jobs for {company_name}...")
                
                for job in company_jobs[:20]:  # Limit per company for demo
                    skills = self.extract_skills(job)
                    seniority = self.determine_seniority(job["title"])
                    
                    job_data = {
                        "type": "job",
                        "id": str(job["id"]),
                        "title": job["title"],
                        "company": job["company_name"],
                        "company_id": str(job["board_id"]),
                        "department": job["department"] or "General",
                        "location": job["location"] or "Remote",
                        "employment_type": job["employment_type"] or "FullTime",
                        "workplace_type": job["workplace_type"] or "Hybrid",
                        "seniority": seniority,
                        "skills": skills,
                        "url": job["url"],
                        "description": job["description_snippet"][:500] if job["description_snippet"] else "",
                        "has_requirements": bool(job["requirements"]),
                        "has_benefits": bool(job["benefits"]),
                        "posted_date": job["posted_date"].isoformat() if job["posted_date"] else None,
                        # Relationships
                        "relationships": {
                            "company": job["company_name"],
                            "location": job["location"],
                            "department": job["department"]
                        }
                    }
                    
                    response = await self.client.graph.add(
                        graph_id=self.graph_id,
                        type="json",
                        data=json.dumps(job_data)
                    )
                    
                    total_jobs_added += 1
                    if total_jobs_added % 10 == 0:
                        print(f"    Added {total_jobs_added} jobs...")
            
            print(f"\n✅ Successfully created job market graph!")
            print(f"   Graph ID: {self.graph_id}")
            print(f"   Total entities added:")
            print(f"   • {len(data['companies'])} companies")
            print(f"   • {min(10, len(data['locations']))} locations")
            print(f"   • {min(20, len(data['departments']))} departments")
            print(f"   • {total_jobs_added} jobs")
            
        except Exception as e:
            print(f"❌ Error creating graph: {e}")
            import traceback
            traceback.print_exc()
    
    async def query_graph(self, query: str):
        """Query the job market graph"""
        
        try:
            results = await self.client.graph.search(
                graph_id=self.graph_id,
                query=query,
                limit=10
            )
            
            print(f"\n🔍 Query: '{query}'")
            if results and results.edges:
                print(f"   Found {len(results.edges)} results")
                for i, edge in enumerate(results.edges[:5], 1):
                    fact = getattr(edge, 'fact', '')
                    print(f"   {i}. {fact[:100]}...")
            else:
                print("   No results found")
            
            return results
            
        except Exception as e:
            print(f"❌ Query error: {e}")
            return None


async def main():
    """Create and query the job market graph"""
    
    print("🚀 UK/EU TECH JOB MARKET GRAPH")
    print("="*80)
    print("""
    Creating comprehensive knowledge graph with:
    • Companies (from job_boards table)
    • Jobs with full details
    • Locations with job counts
    • Departments by company
    • Skills extracted from requirements
    • Seniority levels
    • Proper relationships between entities
    """)
    
    graph = JobMarketGraph()
    
    # Fetch data
    data = await graph.fetch_data()
    
    # Create graph
    await graph.create_graph(data)
    
    # Example queries
    print("\n📊 TESTING GRAPH QUERIES:")
    print("-"*60)
    
    queries = [
        "jobs at hcompany",
        "Python developer roles",
        "remote engineering positions",
        "jobs in Paris",
        "senior positions"
    ]
    
    for query in queries:
        await graph.query_graph(query)
        await asyncio.sleep(1)  # Rate limiting
    
    print("\n✅ Job Market Graph successfully created and tested!")


if __name__ == "__main__":
    asyncio.run(main())