#!/usr/bin/env python3
"""
Create Job Market Knowledge Graph in Zep
Using proper API endpoints and entity relationships
"""

import asyncio
import asyncpg
import httpx
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import hashlib

load_dotenv()


class ZepJobGraph:
    """Create job market graph in Zep with proper relationships"""
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.zep_api_key = "z_1dWlkIjoiMmNkYWVjZjktYTU5Ny00ZDlkLWIyMWItNTZjOWI5OTE5MTE4In0.Ssyb_PezcGgacQFq6Slg3fyFoqs8hBhvp6WsE8rO4VK_D70CT5tqDbFOs6ZTf8rw7qYfTRhLz5YFm8RR854rHg"
        self.zep_base_url = "https://api.getzep.com"
        self.user_id = "job_graph_user"
        self.session_id = f"job_graph_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def fetch_graph_data(self):
        """Fetch job data with proper company relationships"""
        
        conn = await asyncpg.connect(self.db_url)
        try:
            print("📊 Fetching graph data from Neon...")
            
            # Get companies from job_boards table
            companies = await conn.fetch("""
                SELECT 
                    id as board_id,
                    company_name,
                    url,
                    board_type
                FROM job_boards
                WHERE is_active = true
            """)
            
            # Get jobs with proper foreign key relationships
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
                    j.requirements,
                    j.responsibilities,
                    j.benefits,
                    jb.company_name
                FROM jobs j
                JOIN job_boards jb ON j.board_id = jb.id
                WHERE j.is_active = true
            """)
            
            # Get unique locations
            locations = await conn.fetch("""
                SELECT DISTINCT 
                    location,
                    COUNT(*) as job_count
                FROM jobs
                WHERE is_active = true 
                    AND location IS NOT NULL 
                    AND location != ''
                GROUP BY location
            """)
            
            # Get unique departments by company
            departments = await conn.fetch("""
                SELECT DISTINCT 
                    j.department,
                    j.board_id,
                    jb.company_name,
                    COUNT(*) as job_count
                FROM jobs j
                JOIN job_boards jb ON j.board_id = jb.id
                WHERE j.is_active = true 
                    AND j.department IS NOT NULL 
                    AND j.department != ''
                GROUP BY j.department, j.board_id, jb.company_name
            """)
            
            print(f"✅ Fetched: {len(companies)} companies, {len(jobs)} jobs, {len(locations)} locations, {len(departments)} departments")
            
            return {
                "companies": [dict(c) for c in companies],
                "jobs": [dict(j) for j in jobs],
                "locations": [dict(l) for l in locations],
                "departments": [dict(d) for d in departments]
            }
            
        finally:
            await conn.close()
    
    def extract_skills(self, requirements: List[str], title: str) -> List[str]:
        """Extract skills from requirements and job title"""
        
        skills = set()
        
        # Technical skills to look for
        tech_keywords = {
            "Python", "JavaScript", "TypeScript", "React", "Node.js", "Go", "Rust",
            "Java", "C++", "SQL", "NoSQL", "PostgreSQL", "MongoDB", "Redis",
            "Docker", "Kubernetes", "AWS", "GCP", "Azure", "CI/CD", "DevOps",
            "Machine Learning", "AI", "LLM", "NLP", "Deep Learning",
            "REST", "GraphQL", "Microservices", "Cloud", "Security",
            "Git", "Linux", "Terraform", "Ansible", "Jenkins"
        }
        
        # Check requirements
        if requirements:
            req_text = ' '.join(requirements).lower()
            for skill in tech_keywords:
                if skill.lower() in req_text:
                    skills.add(skill)
        
        # Check title
        title_lower = title.lower()
        role_skills = {
            "backend": ["Python", "SQL", "REST", "Microservices"],
            "frontend": ["JavaScript", "React", "TypeScript"],
            "fullstack": ["JavaScript", "Python", "SQL"],
            "devops": ["Docker", "Kubernetes", "CI/CD", "Terraform"],
            "data": ["Python", "SQL", "Machine Learning"],
            "ai": ["Python", "Machine Learning", "AI", "LLM"],
            "security": ["Security", "Cloud", "DevOps"]
        }
        
        for role, role_skills_list in role_skills.items():
            if role in title_lower:
                skills.update(role_skills_list)
        
        return list(skills)
    
    async def create_graph_entities(self, data: Dict):
        """Create entities and relationships in Zep"""
        
        print("\n🌐 Creating Knowledge Graph in Zep...")
        print("="*60)
        
        async with httpx.AsyncClient(timeout=60) as client:
            headers = {
                "Authorization": f"Api-Key {self.zep_api_key}",
                "Content-Type": "application/json"
            }
            
            # First, create or get the user
            user_response = await client.get(
                f"{self.zep_base_url}/api/v2/users/{self.user_id}",
                headers=headers
            )
            
            if user_response.status_code == 404:
                # Create user
                user_data = {
                    "user_id": self.user_id,
                    "email": "job_graph@quest.ai",
                    "first_name": "Job",
                    "last_name": "Graph"
                }
                await client.post(
                    f"{self.zep_base_url}/api/v2/users",
                    headers=headers,
                    json=user_data
                )
                print(f"✅ Created user: {self.user_id}")
            else:
                print(f"✅ Using existing user: {self.user_id}")
            
            # Create a session for the graph
            session_data = {
                "user_id": self.user_id,
                "session_id": self.session_id
            }
            
            session_response = await client.post(
                f"{self.zep_base_url}/api/v2/sessions",
                headers=headers,
                json=session_data
            )
            
            if session_response.status_code in [200, 201]:
                print(f"✅ Created session: {self.session_id}")
            
            # Store entities as memory facts in the session
            facts = []
            
            # Add companies as facts
            for company in data["companies"]:
                fact = {
                    "type": "company",
                    "name": company["company_name"],
                    "id": str(company["board_id"]),
                    "url": company["url"],
                    "board_type": company["board_type"]
                }
                facts.append(fact)
            
            # Add locations as facts
            for location in data["locations"]:
                fact = {
                    "type": "location",
                    "name": location["location"],
                    "job_count": location["job_count"]
                }
                facts.append(fact)
            
            # Add jobs as facts with relationships
            for job in data["jobs"][:20]:  # Limit for testing
                skills = self.extract_skills(job.get("requirements", []), job["title"])
                
                fact = {
                    "type": "job",
                    "id": str(job["id"]),
                    "title": job["title"],
                    "company": job["company_name"],
                    "company_id": str(job["board_id"]),
                    "department": job["department"],
                    "location": job["location"],
                    "employment_type": job["employment_type"],
                    "workplace_type": job["workplace_type"],
                    "skills": skills,
                    "has_requirements": len(job.get("requirements", [])) > 0,
                    "has_benefits": len(job.get("benefits", [])) > 0
                }
                
                if job["full_description"]:
                    fact["description_preview"] = job["full_description"][:200]
                
                facts.append(fact)
            
            # Create memory with all facts
            memory_data = {
                "messages": [
                    {
                        "role": "assistant",
                        "role_type": "assistant",
                        "content": f"Job market graph with {len(data['companies'])} companies and {len(data['jobs'])} jobs",
                        "metadata": {
                            "graph_type": "job_market",
                            "created_at": datetime.now().isoformat()
                        }
                    }
                ],
                "metadata": {
                    "facts": facts,
                    "graph_stats": {
                        "total_companies": len(data["companies"]),
                        "total_jobs": len(data["jobs"]),
                        "total_locations": len(data["locations"]),
                        "total_departments": len(data["departments"])
                    }
                }
            }
            
            # Add memory to session
            memory_response = await client.post(
                f"{self.zep_base_url}/api/v2/sessions/{self.session_id}/memory",
                headers=headers,
                json=memory_data
            )
            
            if memory_response.status_code in [200, 201]:
                print(f"✅ Added graph data to session memory")
                print(f"   • {len(data['companies'])} companies")
                print(f"   • {len(data['jobs'])} jobs") 
                print(f"   • {len(data['locations'])} locations")
                print(f"   • {len(data['departments'])} departments")
            else:
                print(f"❌ Failed to add memory: {memory_response.status_code}")
                print(memory_response.text[:500])
            
            return self.session_id
    
    async def query_graph(self, query: str):
        """Query the graph using Zep's search"""
        
        async with httpx.AsyncClient(timeout=60) as client:
            headers = {
                "Authorization": f"Api-Key {self.zep_api_key}",
                "Content-Type": "application/json"
            }
            
            # Search in session memory
            search_data = {
                "text": query,
                "search_scope": "facts",
                "limit": 10
            }
            
            response = await client.post(
                f"{self.zep_base_url}/api/v2/sessions/{self.session_id}/search",
                headers=headers,
                json=search_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Search failed: {response.status_code}")
                return None


async def main():
    """Create the job market graph in Zep"""
    
    print("🚀 CREATING JOB MARKET GRAPH IN ZEP")
    print("="*80)
    
    graph = ZepJobGraph()
    
    # Fetch data
    data = await graph.fetch_graph_data()
    
    # Create graph
    session_id = await graph.create_graph_entities(data)
    
    print("\n📊 EXAMPLE QUERIES:")
    print("-"*60)
    
    queries = [
        "jobs at hcompany",
        "engineering roles in Paris",
        "remote Python jobs",
        "fullstack positions"
    ]
    
    for query_text in queries:
        print(f"\n🔍 Query: {query_text}")
        results = await graph.query_graph(query_text)
        if results:
            print(f"   Found {len(results.get('results', []))} results")
    
    print("\n✅ Job Market Graph successfully created in Zep!")
    print(f"   Session ID: {session_id}")
    print(f"   User ID: {graph.user_id}")


if __name__ == "__main__":
    asyncio.run(main())