"""
ZEP retrieval activities for job skill graphs
"""

import json
from temporalio import activity
from zep_cloud.client import AsyncZep
from ..config.settings import get_settings


@activity.defn
async def get_job_skill_graph(job_id: str) -> dict:
    """
    Retrieve skill graph for a specific job from ZEP

    Returns a graph of skills and related jobs that can be used
    to display skill requirements and similar opportunities
    """
    settings = get_settings()

    if not settings.zep_api_key:
        activity.logger.warning("No Zep API key, cannot retrieve skill graph")
        return {"skills": [], "related_jobs": [], "error": "No ZEP API key"}

    try:
        zep = AsyncZep(api_key=settings.zep_api_key)

        # Search for the specific job
        job_results = await zep.graph.search(
            graph_id="jobs",
            query=f"job id {job_id}",
            limit=5
        )

        skills = []
        related_jobs = []

        # Extract skills from edges and nodes
        if hasattr(job_results, 'edges') and job_results.edges:
            for edge in job_results.edges:
                if hasattr(edge, 'fact'):
                    fact = edge.fact
                    # Parse skills from facts
                    if "skill" in fact.lower() or "requires" in fact.lower():
                        skills.append({
                            "fact": fact,
                            "source": "edge"
                        })

        if hasattr(job_results, 'nodes') and job_results.nodes:
            for node in job_results.nodes:
                if hasattr(node, 'name'):
                    # Check if node represents a skill or related job
                    node_name = node.name
                    if any(skill_keyword in node_name.lower() for skill_keyword in
                           ["python", "javascript", "react", "aws", "docker", "kubernetes"]):
                        skills.append({
                            "name": node_name,
                            "source": "node"
                        })

        # Search for jobs with similar skills
        if skills:
            # Get first few skill names for similarity search
            skill_names = [s.get("name", "") for s in skills if s.get("name")]
            if skill_names:
                similarity_query = f"jobs requiring {' or '.join(skill_names[:3])}"

                similar_results = await zep.graph.search(
                    graph_id="jobs",
                    query=similarity_query,
                    limit=5
                )

                if hasattr(similar_results, 'nodes') and similar_results.nodes:
                    for node in similar_results.nodes:
                        if hasattr(node, 'name'):
                            related_jobs.append({
                                "title": node.name,
                                "source": "similarity"
                            })

        activity.logger.info(f"Retrieved skill graph: {len(skills)} skills, {len(related_jobs)} related jobs")

        return {
            "job_id": job_id,
            "skills": skills[:10],  # Limit to top 10
            "related_jobs": related_jobs[:5],  # Limit to top 5
            "total_skills": len(skills),
            "total_related": len(related_jobs)
        }

    except Exception as e:
        activity.logger.error(f"Failed to retrieve skill graph: {e}")
        return {
            "job_id": job_id,
            "skills": [],
            "related_jobs": [],
            "error": str(e)
        }


@activity.defn
async def get_skills_for_company(company_name: str) -> dict:
    """
    Get aggregated skill requirements for all jobs at a company

    Useful for showing "Skills we look for" on company pages
    """
    settings = get_settings()

    if not settings.zep_api_key:
        return {"skills": [], "error": "No ZEP API key"}

    try:
        zep = AsyncZep(api_key=settings.zep_api_key)

        # Search for all jobs from this company
        results = await zep.graph.search(
            graph_id="jobs",
            query=f"jobs at {company_name} required skills",
            limit=20
        )

        skill_counts = {}

        # Extract and count skills
        if hasattr(results, 'edges') and results.edges:
            for edge in results.edges:
                if hasattr(edge, 'fact'):
                    fact = edge.fact.lower()
                    # Simple skill extraction from facts
                    for skill in ["python", "javascript", "typescript", "react", "node.js",
                                 "aws", "docker", "kubernetes", "postgresql", "mongodb"]:
                        if skill in fact:
                            skill_counts[skill] = skill_counts.get(skill, 0) + 1

        # Sort skills by frequency
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            "company_name": company_name,
            "skills": [{"name": skill, "count": count} for skill, count in top_skills[:10]],
            "total_skills": len(skill_counts)
        }

    except Exception as e:
        activity.logger.error(f"Failed to get company skills: {e}")
        return {"company_name": company_name, "skills": [], "error": str(e)}


@activity.defn
async def search_jobs_by_skills(skill_names: list[str], limit: int = 10) -> dict:
    """
    Search for jobs that require specific skills

    Useful for "Find jobs using Python" type searches
    """
    settings = get_settings()

    if not settings.zep_api_key:
        return {"jobs": [], "error": "No ZEP API key"}

    try:
        zep = AsyncZep(api_key=settings.zep_api_key)

        # Build search query
        query = f"jobs requiring {' and '.join(skill_names)}"

        results = await zep.graph.search(
            graph_id="jobs",
            query=query,
            limit=limit
        )

        jobs = []

        if hasattr(results, 'nodes') and results.nodes:
            for node in results.nodes:
                if hasattr(node, 'name'):
                    jobs.append({
                        "title": node.name,
                        "relevance": "high"  # Could extract relevance score if available
                    })

        return {
            "skills_searched": skill_names,
            "jobs": jobs,
            "total_found": len(jobs)
        }

    except Exception as e:
        activity.logger.error(f"Failed to search jobs by skills: {e}")
        return {"skills_searched": skill_names, "jobs": [], "error": str(e)}
