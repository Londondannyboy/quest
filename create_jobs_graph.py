#!/usr/bin/env python3
"""
Create 'jobs' Knowledge Graph in Zep
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


class JobsGraph:
    """Create jobs graph with all job market data"""
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.zep_api_key = "z_1dWlkIjoiMmNkYWVjZjktYTU5Ny00ZDlkLWIyMWItNTZjOWI5OTE5MTE4In0.Ssyb_PezcGgacQFq6Slg3fyFoqs8hBhvp6WsE8rO4VK_D70CT5tqDbFOs6ZTf8rw7qYfTRhLz5YFm8RR854rHg"
        self.graph_id = "jobs"
        self.client = AsyncZep(api_key=self.zep_api_key)
    
    async def create_graph(self):
        """Create the jobs graph"""
        
        try:
            print("🌐 Creating 'jobs' graph...")
            
            # Create the new graph
            graph = await self.client.graph.create(
                graph_id=self.graph_id,
                name="Jobs",
                description="Job market knowledge graph with companies, positions, locations, and skills"
            )
            
            print(f"✅ Created graph: {self.graph_id}")
            return True
            
        except Exception as e:
            if "already exists" in str(e).lower() or "409" in str(e):
                print(f"ℹ️  Graph '{self.graph_id}' already exists, will use existing")
                return True
            else:
                print(f"❌ Error creating graph: {e}")
                return False
    
    async def fetch_data(self) -> Dict:
        """Fetch job data from Neon"""
        
        conn = await asyncpg.connect(self.db_url)
        try:
            print("\n📊 Fetching data from Neon...")
            
            # Companies
            companies = await conn.fetch("""
                SELECT 
                    jb.id as board_id,
                    jb.company_name,
                    jb.url,
                    COUNT(j.id) as job_count
                FROM job_boards jb
                LEFT JOIN jobs j ON j.board_id = jb.id AND j.is_active = true
                WHERE jb.is_active = true
                GROUP BY jb.id
            """)
            
            # Jobs
            jobs = await conn.fetch("""
                SELECT 
                    j.*,
                    jb.company_name
                FROM jobs j
                JOIN job_boards jb ON j.board_id = jb.id
                WHERE j.is_active = true
            """)
            
            # Locations
            locations = await conn.fetch("""
                SELECT 
                    j.location,
                    COUNT(*) as job_count,
                    array_agg(DISTINCT jb.company_name) as companies
                FROM jobs j
                JOIN job_boards jb ON j.board_id = jb.id
                WHERE j.is_active = true AND j.location IS NOT NULL
                GROUP BY j.location
            """)
            
            print(f"✅ Fetched {len(companies)} companies, {len(jobs)} jobs, {len(locations)} locations")
            
            return {
                "companies": [dict(c) for c in companies],
                "jobs": [dict(j) for j in jobs],
                "locations": [dict(l) for l in locations]
            }
            
        finally:
            await conn.close()
    
    async def populate_graph(self, data: Dict):
        """Add data to the graph"""
        
        print("\n📝 Adding data to graph...")
        
        try:
            # Add companies
            for company in data["companies"]:
                await self.client.graph.add(
                    graph_id=self.graph_id,
                    type="json",
                    data=json.dumps({
                        "type": "company",
                        "id": str(company["board_id"]),
                        "name": company["company_name"],
                        "jobs": company["job_count"]
                    })
                )
            print(f"✅ Added {len(data['companies'])} companies")
            
            # Add locations
            for loc in data["locations"][:20]:
                await self.client.graph.add(
                    graph_id=self.graph_id,
                    type="json",
                    data=json.dumps({
                        "type": "location",
                        "name": loc["location"],
                        "jobs": loc["job_count"]
                    })
                )
            print(f"✅ Added {min(20, len(data['locations']))} locations")
            
            # Add jobs
            for job in data["jobs"][:50]:
                await self.client.graph.add(
                    graph_id=self.graph_id,
                    type="json",
                    data=json.dumps({
                        "type": "job",
                        "id": str(job["id"]),
                        "title": job["title"],
                        "company": job["company_name"],
                        "location": job["location"],
                        "department": job["department"]
                    })
                )
            print(f"✅ Added {min(50, len(data['jobs']))} jobs")
            
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    graph = JobsGraph()
    
    if await graph.create_graph():
        data = await graph.fetch_data()
        await graph.populate_graph(data)
        
        print(f"\n✅ Graph 'jobs' created and populated!")


if __name__ == "__main__":
    asyncio.run(main())