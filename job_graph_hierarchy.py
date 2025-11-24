#!/usr/bin/env python3
"""
Hierarchical Job Graph System
Manages master index and vertical-specific graphs
"""

import asyncio
import asyncpg
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import os
from zep_cloud.client import AsyncZep
from enum import Enum

load_dotenv()


class JobVertical(Enum):
    """Job market verticals"""
    TECH = "tech"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    RETAIL = "retail"
    EDUCATION = "education"
    GOVERNMENT = "government"
    

class GraphHierarchy:
    """Manages the hierarchical graph structure"""
    
    def __init__(self):
        self.zep_api_key = os.getenv("ZEP_API_KEY", "z_1dWlkIjoiMmNkYWVjZjktYTU5Ny00ZDlkLWIyMWItNTZjOWI5OTE5MTE4In0.Ssyb_PezcGgacQFq6Slg3fyFoqs8hBhvp6WsE8rO4VK_D70CT5tqDbFOs6ZTf8rw7qYfTRhLz5YFm8RR854rHg")
        self.client = AsyncZep(api_key=self.zep_api_key)
        
        # Define graph hierarchy
        self.graphs = {
            "master": {
                "id": "jobs",
                "name": "Jobs Master Index",
                "description": "Lightweight index of all jobs across verticals"
            },
            "verticals": {
                JobVertical.TECH: {
                    "id": "jobs-tech",
                    "name": "Technology Jobs",
                    "description": "Software, IT, AI, and tech industry positions",
                    "ontology": self.get_tech_ontology()
                },
                JobVertical.FINANCE: {
                    "id": "jobs-finance",
                    "name": "Finance Jobs",
                    "description": "Banking, fintech, trading, and financial services",
                    "ontology": self.get_finance_ontology()
                },
                JobVertical.HEALTHCARE: {
                    "id": "jobs-healthcare",
                    "name": "Healthcare Jobs",
                    "description": "Medical, biotech, and healthcare positions",
                    "ontology": self.get_healthcare_ontology()
                }
            },
            "cross_cutting": {
                "remote": {
                    "id": "jobs-remote",
                    "name": "Remote Jobs",
                    "description": "Fully remote positions across all industries"
                },
                "senior": {
                    "id": "jobs-senior",
                    "name": "Senior Positions",
                    "description": "Senior, Staff, Principal, and Executive roles"
                },
                "intern": {
                    "id": "jobs-intern",
                    "name": "Entry Level & Internships",
                    "description": "Internships and entry-level positions"
                }
            }
        }
    
    def get_tech_ontology(self) -> Dict:
        """Technology sector ontology"""
        return {
            "entities": {
                "TechCompany": ["startup", "scaleup", "enterprise", "unicorn"],
                "TechRole": ["engineering", "product", "design", "data", "devops", "security"],
                "TechSkill": ["language", "framework", "tool", "platform", "methodology"],
                "TechStack": ["frontend", "backend", "fullstack", "mobile", "embedded", "ml"]
            },
            "relationships": {
                "USES_TECH": {"properties": ["proficiency", "years"]},
                "REQUIRES_STACK": {"properties": ["primary", "secondary"]},
                "REPORTS_TO": {"properties": ["direct", "dotted"]},
                "WORKS_WITH": {"properties": ["team", "cross_functional"]}
            },
            "skills": {
                "languages": ["Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "C++"],
                "frameworks": ["React", "Vue", "Angular", "Django", "FastAPI", "Spring", "Next.js"],
                "platforms": ["AWS", "GCP", "Azure", "Kubernetes", "Docker"],
                "databases": ["PostgreSQL", "MongoDB", "Redis", "Elasticsearch"],
                "ml": ["TensorFlow", "PyTorch", "Scikit-learn", "Hugging Face", "LangChain"]
            }
        }
    
    def get_finance_ontology(self) -> Dict:
        """Finance sector ontology"""
        return {
            "entities": {
                "FinanceCompany": ["bank", "hedge_fund", "fintech", "insurance", "advisory"],
                "FinanceRole": ["trading", "risk", "compliance", "analysis", "advisory"],
                "FinanceSkill": ["modeling", "regulation", "products", "markets"],
                "FinanceProduct": ["equities", "fixed_income", "derivatives", "crypto"]
            },
            "relationships": {
                "TRADES_IN": {"properties": ["asset_class", "volume"]},
                "MANAGES_RISK": {"properties": ["type", "limit"]},
                "REPORTS_TO_REGULATOR": {"properties": ["jurisdiction", "framework"]}
            },
            "skills": {
                "technical": ["Excel", "Python", "R", "SQL", "Bloomberg", "Reuters"],
                "products": ["Equities", "FX", "Derivatives", "Fixed Income", "Crypto"],
                "regulations": ["MiFID", "Basel III", "Dodd-Frank", "GDPR"],
                "certifications": ["CFA", "FRM", "CPA", "Series 7", "Series 63"]
            }
        }
    
    def get_healthcare_ontology(self) -> Dict:
        """Healthcare sector ontology"""
        return {
            "entities": {
                "HealthcareOrg": ["hospital", "clinic", "pharma", "biotech", "healthtech"],
                "HealthcareRole": ["clinical", "research", "admin", "tech", "regulatory"],
                "Specialization": ["cardiology", "oncology", "neurology", "pediatrics"],
                "Credential": ["license", "certification", "degree", "fellowship"]
            },
            "relationships": {
                "SPECIALIZES_IN": {"properties": ["area", "years"]},
                "LICENSED_IN": {"properties": ["state", "country"]},
                "RESEARCHES": {"properties": ["phase", "indication"]}
            },
            "skills": {
                "clinical": ["Patient Care", "Diagnosis", "Surgery", "Emergency Medicine"],
                "research": ["Clinical Trials", "FDA Approval", "GxP", "Biostatistics"],
                "technology": ["EMR", "PACS", "Telemedicine", "Medical Devices"],
                "certifications": ["Board Certified", "ACLS", "BLS", "PALS"]
            }
        }
    
    async def create_all_graphs(self):
        """Create all graphs in the hierarchy"""
        print("🌐 Creating Hierarchical Graph Structure...")
        print("="*60)
        
        # Create master graph
        await self.create_or_update_graph(
            self.graphs["master"]["id"],
            self.graphs["master"]["name"],
            self.graphs["master"]["description"]
        )
        
        # Create vertical graphs (only tech for now)
        for vertical in [JobVertical.TECH]:
            graph_info = self.graphs["verticals"][vertical]
            await self.create_or_update_graph(
                graph_info["id"],
                graph_info["name"],
                graph_info["description"]
            )
        
        # Create cross-cutting graphs (optional for now)
        # for key, graph_info in self.graphs["cross_cutting"].items():
        #     await self.create_or_update_graph(
        #         graph_info["id"],
        #         graph_info["name"],
        #         graph_info["description"]
        #     )
        
        print("✅ Hierarchical graph structure created!")
    
    async def create_or_update_graph(self, graph_id: str, name: str, description: str):
        """Create or update a graph"""
        try:
            graph = await self.client.graph.create(
                graph_id=graph_id,
                name=name,
                description=description
            )
            print(f"  ✅ Created graph: {graph_id}")
        except Exception as e:
            if "already exists" in str(e).lower() or "409" in str(e):
                print(f"  ℹ️  Graph '{graph_id}' already exists")
            else:
                print(f"  ❌ Error with graph '{graph_id}': {e}")
    
    def determine_vertical(self, job_data: Dict) -> JobVertical:
        """Determine which vertical a job belongs to"""
        
        company = job_data.get("company_name", "").lower()
        title = job_data.get("title", "").lower()
        department = job_data.get("department", "").lower()
        
        # Tech indicators
        tech_indicators = ["software", "engineer", "developer", "tech", "ai", "ml", "data", "product", "design"]
        if any(ind in title for ind in tech_indicators) or \
           any(ind in company for ind in ["clay", "lovable", "hcompany", "anthropic", "openai"]):
            return JobVertical.TECH
        
        # Finance indicators
        finance_indicators = ["trading", "banking", "finance", "investment", "analyst", "risk"]
        if any(ind in title for ind in finance_indicators) or \
           any(ind in company for ind in ["jpmorgan", "goldman", "citi", "bank"]):
            return JobVertical.FINANCE
        
        # Healthcare indicators
        healthcare_indicators = ["medical", "clinical", "nurse", "doctor", "pharma", "health"]
        if any(ind in title for ind in healthcare_indicators):
            return JobVertical.HEALTHCARE
        
        # Default to tech for now
        return JobVertical.TECH
    
    async def add_job_to_graphs(self, job_data: Dict):
        """Add a job to appropriate graphs"""
        
        job_id = str(job_data.get("id", ""))
        
        # 1. Always add lightweight version to master graph
        master_data = {
            "entity_type": "job_index",
            "job_id": job_id,
            "title": job_data.get("title"),
            "company": job_data.get("company_name"),
            "vertical": self.determine_vertical(job_data).value,
            "location": job_data.get("location"),
            "posted_date": str(job_data.get("posted_date")) if job_data.get("posted_date") else None
        }
        
        await self.client.graph.add(
            graph_id="jobs",
            type="json",
            data=json.dumps(master_data)
        )
        
        # 2. Add full data to vertical graph
        vertical = self.determine_vertical(job_data)
        vertical_graph_id = self.graphs["verticals"][vertical]["id"]
        
        # Add vertical-specific enrichment
        if vertical == JobVertical.TECH:
            job_data["tech_stack"] = self.extract_tech_stack(job_data)
            job_data["seniority_level"] = self.determine_seniority(job_data.get("title", ""))
        
        await self.client.graph.add(
            graph_id=vertical_graph_id,
            type="json",
            data=json.dumps({
                "entity_type": "job_full",
                **job_data
            })
        )
        
        # 3. Add to cross-cutting graphs if applicable
        if self.is_remote(job_data):
            await self.client.graph.add(
                graph_id="jobs-remote",
                type="json",
                data=json.dumps({"job_id": job_id, "title": job_data.get("title")})
            )
        
        if self.is_senior(job_data):
            await self.client.graph.add(
                graph_id="jobs-senior",
                type="json",
                data=json.dumps({"job_id": job_id, "title": job_data.get("title")})
            )
    
    def extract_tech_stack(self, job_data: Dict) -> List[str]:
        """Extract technology stack from job data"""
        tech_ontology = self.get_tech_ontology()
        found_tech = []
        
        text_to_check = f"{job_data.get('title', '')} {job_data.get('description_snippet', '')}"
        text_lower = text_to_check.lower()
        
        for category in ["languages", "frameworks", "platforms", "databases", "ml"]:
            for tech in tech_ontology["skills"].get(category, []):
                if tech.lower() in text_lower:
                    found_tech.append(tech)
        
        return found_tech
    
    def determine_seniority(self, title: str) -> str:
        """Determine seniority level"""
        title_lower = title.lower()
        
        if any(term in title_lower for term in ["intern", "junior", "entry"]):
            return "Entry"
        elif any(term in title_lower for term in ["senior", "lead"]):
            return "Senior"
        elif any(term in title_lower for term in ["staff", "principal"]):
            return "Staff+"
        elif any(term in title_lower for term in ["director", "vp", "head"]):
            return "Executive"
        else:
            return "Mid-level"
    
    def is_remote(self, job_data: Dict) -> bool:
        """Check if job is remote"""
        workplace = job_data.get("workplace_type", "").lower()
        location = job_data.get("location", "").lower()
        return "remote" in workplace or "remote" in location
    
    def is_senior(self, job_data: Dict) -> bool:
        """Check if job is senior level"""
        seniority = self.determine_seniority(job_data.get("title", ""))
        return seniority in ["Senior", "Staff+", "Executive"]
    
    async def search_jobs(self, query: str, vertical: Optional[JobVertical] = None, 
                         cross_cutting: Optional[str] = None) -> Any:
        """Smart search across appropriate graphs"""
        
        # Determine which graph to search
        if vertical:
            graph_id = self.graphs["verticals"][vertical]["id"]
        elif cross_cutting and cross_cutting in self.graphs["cross_cutting"]:
            graph_id = self.graphs["cross_cutting"][cross_cutting]["id"]
        else:
            # Smart routing based on query content
            query_lower = query.lower()
            if any(term in query_lower for term in ["python", "react", "engineer", "developer"]):
                graph_id = "jobs-tech"
            elif any(term in query_lower for term in ["trading", "banking", "finance"]):
                graph_id = "jobs-finance"
            elif any(term in query_lower for term in ["remote", "wfh", "work from home"]):
                graph_id = "jobs-remote"
            else:
                graph_id = "jobs"  # Default to master
        
        print(f"🔍 Searching in graph: {graph_id}")
        
        try:
            results = await self.client.graph.search(
                graph_id=graph_id,
                query=query,
                limit=20
            )
            return results
        except Exception as e:
            print(f"Search error: {e}")
            # Fallback to master graph
            return await self.client.graph.search(
                graph_id="jobs",
                query=query,
                limit=20
            )


async def test_hierarchy():
    """Test the hierarchical graph system"""
    
    print("🧪 Testing Hierarchical Graph System")
    print("="*60)
    
    hierarchy = GraphHierarchy()
    
    # Create all graphs
    await hierarchy.create_all_graphs()
    
    # Test job classification
    test_jobs = [
        {"title": "Senior Software Engineer", "company_name": "Clay Labs", "location": "Remote"},
        {"title": "Investment Banking Analyst", "company_name": "JPMorgan", "location": "London"},
        {"title": "ML Engineer", "company_name": "hcompany", "location": "Paris"},
    ]
    
    print("\n📊 Job Classification Test:")
    for job in test_jobs:
        vertical = hierarchy.determine_vertical(job)
        seniority = hierarchy.determine_seniority(job["title"])
        print(f"  {job['title']} → Vertical: {vertical.value}, Seniority: {seniority}")
    
    # Test search routing
    print("\n🔍 Search Routing Test:")
    test_queries = [
        "Python developer remote",
        "Investment banking London",
        "Senior positions",
        "Machine learning engineer"
    ]
    
    for query in test_queries:
        print(f"  Query: '{query}' → ", end="")
        results = await hierarchy.search_jobs(query)
        if results and results.edges:
            print(f"Found {len(results.edges)} results")
        else:
            print("No results")


if __name__ == "__main__":
    asyncio.run(test_hierarchy())