import re
import json
from temporalio import activity
from openai import AsyncOpenAI
from ..config.settings import get_settings


SKILL_PATTERNS = {
    "essential": [
        r"must have[:\s]+(.+?)(?:\.|,|$)",
        r"required[:\s]+(.+?)(?:\.|,|$)",
        r"you have[:\s]+(.+?)(?:\.|,|$)",
    ],
    "beneficial": [
        r"nice to have[:\s]+(.+?)(?:\.|,|$)",
        r"beneficial[:\s]+(.+?)(?:\.|,|$)",
        r"preferred[:\s]+(.+?)(?:\.|,|$)",
    ]
}


@activity.defn
async def extract_job_skills(jobs: list[dict]) -> list[dict]:
    """Extract skills from job descriptions with importance levels"""
    settings = get_settings()

    if not settings.openai_api_key:
        # Fallback to regex extraction
        return [_extract_skills_regex(job) for job in jobs]

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    enriched_jobs = []
    for job in jobs:
        if not job.get("description"):
            job["skills"] = []
            enriched_jobs.append(job)
            continue

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """Extract skills from job descriptions. Return JSON:
{
  "skills": [
    {"name": "Python", "importance": "essential", "category": "technical"},
    {"name": "TypeScript", "importance": "beneficial", "category": "technical"}
  ]
}
Categories: technical, soft, domain, tool
Importance: essential (required/must have), beneficial (nice to have), bonus"""
                    },
                    {
                        "role": "user",
                        "content": job["description"][:4000]  # Limit tokens
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )

            skills_data = json.loads(response.choices[0].message.content)
            job["skills"] = skills_data.get("skills", [])

        except Exception as e:
            # Fallback to regex
            job = _extract_skills_regex(job)

        enriched_jobs.append(job)

    return enriched_jobs


def _extract_skills_regex(job: dict) -> dict:
    """Fallback regex-based skill extraction"""
    description = job.get("description", "")
    skills = []

    for importance, patterns in SKILL_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                skills.append({
                    "name": match.strip()[:100],
                    "importance": importance,
                    "category": "unknown"
                })

    job["skills"] = skills
    return job


@activity.defn
async def calculate_company_trends(company_names: list[str]) -> dict:
    """Calculate hiring trends for companies"""
    import asyncpg
    from collections import Counter

    settings = get_settings()
    conn = await asyncpg.connect(settings.database_url)

    trends = {}

    try:
        for company_name in company_names:
            # Get jobs for company
            rows = await conn.fetch("""
                SELECT j.title, j.department, j.location, j.posted_date
                FROM jobs j
                JOIN job_boards jb ON j.job_board_id = jb.id
                WHERE jb.name = $1
            """, company_name)

            if not rows:
                continue

            jobs = [dict(row) for row in rows]

            # Count departments
            dept_counts = Counter(j.get("department") for j in jobs if j.get("department"))

            # Count locations
            loc_counts = Counter(j.get("location") for j in jobs if j.get("location"))

            # Hiring velocity (simplified)
            total = len(jobs)
            velocity = "high" if total > 20 else "medium" if total > 5 else "low"

            trends[company_name] = {
                "total_jobs": total,
                "hiring_velocity": velocity,
                "top_departments": dict(dept_counts.most_common(5)),
                "top_locations": dict(loc_counts.most_common(5)),
            }

        return trends

    finally:
        await conn.close()
