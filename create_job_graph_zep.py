#!/usr/bin/env python3
"""
Create a comprehensive job market graph in Zep
Maps job data from Neon to a knowledge graph structure
"""

import asyncio
import asyncpg
import httpx
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv
import uuid

load_dotenv()


class JobMarketGraphBuilder:
    """Build a knowledge graph of the tech job market"""
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.zep_api_key = "z_1dWlkIjoiMmNkYWVjZjktYTU5Ny00ZDlkLWIyMWItNTZjOWI5OTE5MTE4In0.Ssyb_PezcGgacQFq6Slg3fyFoqs8hBhvp6WsE8rO4VK_D70CT5tqDbFOs6ZTf8rw7qYfTRhLz5YFm8RR854rHg"
        self.zep_base_url = "https://api.getzep.com"
        
        # Define ontology for the job market
        self.ontology = {
            "entities": {
                "Company": ["name", "industry", "location", "size"],
                "Job": ["title", "posted_date", "status", "url"],
                "Department": ["name", "function"],
                "Location": ["city", "country", "region", "remote_friendly"],
                "Role": ["title", "seniority_level", "category"],
                "Skill": ["name", "type", "level"],
                "EmploymentType": ["type", "full_time", "part_time", "contract"],
                "WorkplaceType": ["type", "remote", "hybrid", "onsite"],
                "Requirement": ["description", "is_required", "category"],
                "Benefit": ["description", "category"],
                "Industry": ["name", "sector"]
            },
            "relationships": {
                "POSTED_BY": ("Job", "Company"),
                "BELONGS_TO_DEPT": ("Job", "Department"),
                "LOCATED_IN": ("Job", "Location"),
                "HAS_ROLE": ("Job", "Role"),
                "REQUIRES_SKILL": ("Job", "Skill"),
                "HAS_EMPLOYMENT_TYPE": ("Job", "EmploymentType"),
                "HAS_WORKPLACE_TYPE": ("Job", "WorkplaceType"),
                "HAS_REQUIREMENT": ("Job", "Requirement"),
                "OFFERS_BENEFIT": ("Job", "Benefit"),
                "DEPARTMENT_OF": ("Department", "Company"),
                "COMPANY_IN_LOCATION": ("Company", "Location"),
                "SIMILAR_TO": ("Job", "Job"),
                "REPORTS_TO": ("Role", "Role"),
                "IN_INDUSTRY": ("Company", "Industry")
            }
        }
        
        self.graph_user_id = f"job_graph_{datetime.now().strftime('%Y%m%d')}"
    
    async def fetch_job_data(self) -> Dict[str, List]:
        """Fetch all job data from Neon database"""
        
        conn = await asyncpg.connect(self.db_url)
        try:
            print("📊 Fetching job data from Neon...")
            
            # Get all jobs with details from single table
            jobs = await conn.fetch("""
                SELECT 
                    id,
                    title,
                    company_name,
                    department,
                    location,
                    employment_type,
                    workplace_type,
                    url,
                    posted_date,
                    description_snippet,
                    full_description,
                    requirements,
                    responsibilities,
                    benefits,
                    qualifications,
                    about_company,
                    about_team
                FROM jobs
                WHERE is_active = true
            """)
            
            # Get companies
            companies = await conn.fetch("""
                SELECT DISTINCT 
                    company_name,
                    COUNT(*) as job_count
                FROM jobs
                WHERE is_active = true
                GROUP BY company_name
            """)
            
            # Get departments
            departments = await conn.fetch("""
                SELECT DISTINCT 
                    company_name,
                    department,
                    COUNT(*) as job_count
                FROM jobs
                WHERE is_active = true AND department IS NOT NULL AND department != ''
                GROUP BY company_name, department
            """)
            
            # Get locations
            locations = await conn.fetch("""
                SELECT DISTINCT 
                    location,
                    COUNT(*) as job_count
                FROM jobs
                WHERE is_active = true AND location IS NOT NULL AND location != ''
                GROUP BY location
            """)
            
            print(f"✅ Fetched {len(jobs)} jobs, {len(companies)} companies, {len(departments)} departments, {len(locations)} locations")
            
            return {
                "jobs": [dict(j) for j in jobs],
                "companies": [dict(c) for c in companies],
                "departments": [dict(d) for d in departments],
                "locations": [dict(l) for l in locations]
            }
            
        finally:
            await conn.close()
    
    def extract_skills_from_requirements(self, requirements: List[str]) -> List[str]:
        """Extract skills from job requirements"""
        
        # Common tech skills to look for
        tech_skills = [
            "Python", "JavaScript", "TypeScript", "React", "Node.js", "Go", "Rust",
            "Java", "C++", "SQL", "NoSQL", "PostgreSQL", "MongoDB", "Redis",
            "Docker", "Kubernetes", "AWS", "GCP", "Azure", "CI/CD", "DevOps",
            "Machine Learning", "AI", "LLM", "NLP", "Computer Vision",
            "REST API", "GraphQL", "Microservices", "Cloud", "Security",
            "Agile", "Scrum", "Git", "Linux", "Terraform", "Ansible"
        ]
        
        found_skills = []
        if requirements:
            req_text = ' '.join(requirements).lower()
            for skill in tech_skills:
                if skill.lower() in req_text:
                    found_skills.append(skill)
        
        return found_skills
    
    def determine_seniority_level(self, title: str) -> str:
        """Determine seniority level from job title"""
        
        title_lower = title.lower()
        
        if any(term in title_lower for term in ["intern", "graduate", "entry", "apprentice"]):
            return "Entry"
        elif any(term in title_lower for term in ["junior", "associate"]):
            return "Junior"
        elif any(term in title_lower for term in ["senior", "lead"]):
            return "Senior"
        elif any(term in title_lower for term in ["principal", "staff", "architect"]):
            return "Principal"
        elif any(term in title_lower for term in ["head", "director", "vp", "vice president"]):
            return "Leadership"
        elif any(term in title_lower for term in ["manager"]):
            return "Management"
        else:
            return "Mid-level"
    
    def categorize_role(self, title: str, department: str) -> str:
        """Categorize role based on title and department"""
        
        combined = f"{title} {department}".lower()
        
        if any(term in combined for term in ["engineer", "developer", "programmer", "coding"]):
            return "Engineering"
        elif any(term in combined for term in ["product", "pm"]):
            return "Product"
        elif any(term in combined for term in ["design", "ux", "ui"]):
            return "Design"
        elif any(term in combined for term in ["data", "analytics", "scientist"]):
            return "Data"
        elif any(term in combined for term in ["sales", "account", "business development"]):
            return "Sales"
        elif any(term in combined for term in ["marketing", "growth"]):
            return "Marketing"
        elif any(term in combined for term in ["customer", "support", "success"]):
            return "Customer Success"
        elif any(term in combined for term in ["hr", "recruiting", "people", "talent"]):
            return "People"
        elif any(term in combined for term in ["finance", "accounting"]):
            return "Finance"
        elif any(term in combined for term in ["legal", "compliance"]):
            return "Legal"
        elif any(term in combined for term in ["research"]):
            return "Research"
        else:
            return "Other"
    
    async def create_graph_in_zep(self, data: Dict[str, List]):
        """Create the job market graph in Zep"""
        
        print("\n🌐 Creating Job Market Graph in Zep...")
        print("="*60)
        
        async with httpx.AsyncClient(timeout=60) as client:
            headers = {
                "Authorization": f"Api-Key {self.zep_api_key}",
                "Content-Type": "application/json"
            }
            
            # Track created entities for relationships
            entity_ids = {
                "companies": {},
                "jobs": {},
                "departments": {},
                "locations": {},
                "roles": {},
                "skills": set(),
                "employment_types": set(),
                "workplace_types": set()
            }
            
            # 1. Create Company nodes
            print("\n1️⃣ Creating Company nodes...")
            for company in data["companies"]:
                node_data = {
                    "user_id": self.graph_user_id,
                    "type": "Company",
                    "data": {
                        "name": company["company_name"],
                        "job_count": company["job_count"],
                        "industry": "Technology",  # Default for now
                        "entity_type": "Company"
                    }
                }
                
                try:
                    response = await client.post(
                        f"{self.zep_base_url}/api/v2/graph/{self.graph_user_id}/add",
                        headers=headers,
                        json=node_data
                    )
                    if response.status_code == 200:
                        entity_ids["companies"][company["company_name"]] = company["company_name"]
                        print(f"  ✅ Created company: {company['company_name']}")
                    else:
                        print(f"  ❌ Failed to create company: {response.status_code}")
                except Exception as e:
                    print(f"  ❌ Error creating company: {e}")
            
            # 2. Create Location nodes
            print("\n2️⃣ Creating Location nodes...")
            for location in data["locations"]:
                # Parse location (e.g., "Paris" or "London - Remote")
                loc_parts = location["location"].split(" - ")
                city = loc_parts[0] if loc_parts else location["location"]
                is_remote = "Remote" in location["location"]
                
                node_data = {
                    "user_id": self.graph_user_id,
                    "type": "Location",
                    "data": {
                        "city": city,
                        "country": "UK" if "London" in city else "France" if "Paris" in city else "Sweden",
                        "remote_friendly": is_remote,
                        "job_count": location["job_count"],
                        "entity_type": "Location"
                    }
                }
                
                try:
                    response = await client.post(
                        f"{self.zep_base_url}/api/v2/graph/{self.graph_user_id}/add",
                        headers=headers,
                        json=node_data
                    )
                    if response.status_code == 200:
                        entity_ids["locations"][location["location"]] = location["location"]
                        print(f"  ✅ Created location: {city}")
                except Exception as e:
                    print(f"  ❌ Error creating location: {e}")
            
            # 3. Create Department nodes
            print("\n3️⃣ Creating Department nodes...")
            for dept in data["departments"]:
                if dept["department"]:
                    node_data = {
                        "user_id": self.graph_user_id,
                        "type": "Department",
                        "data": {
                            "name": dept["department"],
                            "company": dept["company_name"],
                            "job_count": dept["job_count"],
                            "entity_type": "Department"
                        }
                    }
                    
                    try:
                        response = await client.post(
                            f"{self.zep_base_url}/api/v2/graph/{self.graph_user_id}/add",
                            headers=headers,
                            json=node_data
                        )
                        if response.status_code == 200:
                            dept_id = f"{dept['company_name']}_{dept['department']}"
                            entity_ids["departments"][dept_id] = dept_id
                            print(f"  ✅ Created department: {dept['department']} at {dept['company_name']}")
                    except Exception as e:
                        print(f"  ❌ Error creating department: {e}")
            
            # 4. Create Job nodes and relationships
            print("\n4️⃣ Creating Job nodes and relationships...")
            for i, job in enumerate(data["jobs"][:50], 1):  # Limit to first 50 for demo
                # Extract job details
                job_id = str(job["id"])
                seniority = self.determine_seniority_level(job["title"])
                category = self.categorize_role(job["title"], job["department"] or "")
                skills = self.extract_skills_from_requirements(job["requirements"] or [])
                
                # Create Job node
                node_data = {
                    "user_id": self.graph_user_id,
                    "type": "Job",
                    "data": {
                        "id": job_id,
                        "title": job["title"],
                        "company": job["company_name"],
                        "department": job["department"],
                        "location": job["location"],
                        "employment_type": job["employment_type"],
                        "workplace_type": job["workplace_type"],
                        "seniority_level": seniority,
                        "category": category,
                        "url": job["url"],
                        "description": job["description_snippet"][:500] if job["description_snippet"] else "",
                        "skills": skills,
                        "posted_date": job["posted_date"].isoformat() if job["posted_date"] else None,
                        "entity_type": "Job"
                    }
                }
                
                try:
                    response = await client.post(
                        f"{self.zep_base_url}/api/v2/graph/{self.graph_user_id}/add",
                        headers=headers,
                        json=node_data
                    )
                    
                    if response.status_code == 200:
                        entity_ids["jobs"][job_id] = job["title"]
                        print(f"  ✅ {i}. Created job: {job['title']} at {job['company_name']}")
                        
                        # Create relationships
                        # Job -> Company
                        if job["company_name"] in entity_ids["companies"]:
                            rel_data = {
                                "user_id": self.graph_user_id,
                                "type": "POSTED_BY",
                                "source_id": job_id,
                                "target_id": job["company_name"],
                                "data": {"relationship": "posted_by"}
                            }
                            await client.post(
                                f"{self.zep_base_url}/api/v2/graph/{self.graph_user_id}/relationship",
                                headers=headers,
                                json=rel_data
                            )
                        
                        # Job -> Location
                        if job["location"] and job["location"] in entity_ids["locations"]:
                            rel_data = {
                                "user_id": self.graph_user_id,
                                "type": "LOCATED_IN",
                                "source_id": job_id,
                                "target_id": job["location"],
                                "data": {"relationship": "located_in"}
                            }
                            await client.post(
                                f"{self.zep_base_url}/api/v2/graph/{self.graph_user_id}/relationship",
                                headers=headers,
                                json=rel_data
                            )
                        
                        # Job -> Department
                        if job["department"]:
                            dept_id = f"{job['company_name']}_{job['department']}"
                            if dept_id in entity_ids["departments"]:
                                rel_data = {
                                    "user_id": self.graph_user_id,
                                    "type": "BELONGS_TO_DEPT",
                                    "source_id": job_id,
                                    "target_id": dept_id,
                                    "data": {"relationship": "belongs_to"}
                                }
                                await client.post(
                                    f"{self.zep_base_url}/api/v2/graph/{self.graph_user_id}/relationship",
                                    headers=headers,
                                    json=rel_data
                                )
                    
                except Exception as e:
                    print(f"  ❌ Error creating job: {e}")
                
                # Add delay to avoid rate limiting
                if i % 10 == 0:
                    await asyncio.sleep(1)
            
            print("\n✅ Job Market Graph created successfully!")
            print(f"   Graph User ID: {self.graph_user_id}")
            print(f"   Total nodes created: ~{len(entity_ids['companies']) + len(entity_ids['jobs']) + len(entity_ids['departments']) + len(entity_ids['locations'])}")
            
            return self.graph_user_id
    
    async def query_graph(self, query: str):
        """Query the created graph"""
        
        async with httpx.AsyncClient(timeout=60) as client:
            headers = {
                "Authorization": f"Api-Key {self.zep_api_key}",
                "Content-Type": "application/json"
            }
            
            query_data = {
                "user_id": self.graph_user_id,
                "query": query
            }
            
            response = await client.post(
                f"{self.zep_base_url}/api/v2/graph/{self.graph_user_id}/search",
                headers=headers,
                json=query_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Query failed: {response.status_code}")
                return None


async def main():
    """Create the job market graph"""
    
    print("🚀 UK/EU TECH JOB MARKET GRAPH BUILDER")
    print("="*80)
    print("""
    This will create a knowledge graph in Zep with:
    • Companies as nodes
    • Jobs as nodes with properties (title, department, location, etc.)
    • Locations as nodes (cities, remote options)
    • Departments as nodes
    • Relationships between entities
    • Skills extracted from requirements
    """)
    
    builder = JobMarketGraphBuilder()
    
    # Fetch data from Neon
    data = await builder.fetch_job_data()
    
    # Create graph in Zep
    graph_id = await builder.create_graph_in_zep(data)
    
    # Example queries
    print("\n📊 Example Graph Queries:")
    print("-"*60)
    example_queries = [
        "Show all jobs in Paris",
        "Find engineering roles at hcompany",
        "What companies are hiring for remote positions?",
        "Show senior level positions",
        "Find jobs requiring Python"
    ]
    
    for query in example_queries:
        print(f"\nQuery: {query}")
        result = await builder.query_graph(query)
        if result:
            print(f"Results: {json.dumps(result, indent=2)[:200]}...")


if __name__ == "__main__":
    asyncio.run(main())