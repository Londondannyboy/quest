import json
import httpx
from typing import List, Optional
from temporalio import activity
from ..config.settings import get_settings
from ..models.classification import JobClassification, EmploymentType, SeniorityLevel


CLASSIFICATION_PROMPT = """Analyze this job listing and classify it.

Job Title: {title}
Company: {company}
Location: {location}
Department: {department}
Description: {description}

Classify this job and return JSON with these fields:
- is_fractional: boolean - True ONLY if this is a fractional executive role (C-suite/leadership working part-time for multiple companies, typically 10-20 hrs/week)
- employment_type: one of "fractional", "part_time", "contract", "temporary", "full_time", "unknown"
- seniority_level: one of "c_suite", "vp", "director", "manager", "senior", "mid", "junior", "unknown"
- confidence: float 0.0-1.0
- hours_per_week: string if mentioned (e.g., "10-15 hours"), null otherwise
- is_remote: boolean if mentioned, null otherwise
- reasoning: brief 1-sentence explanation

Return ONLY valid JSON, no markdown."""


@activity.defn
async def classify_jobs_with_gemini(jobs: List[dict]) -> List[dict]:
    """
    Classify jobs using Gemini Flash for fast, cheap classification.

    Uses Pydantic structured output via Gemini's JSON mode.
    """
    settings = get_settings()

    if not settings.google_api_key:
        activity.logger.warning("No Google API key, skipping classification")
        return jobs

    classified = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for job in jobs:
            try:
                prompt = CLASSIFICATION_PROMPT.format(
                    title=job.get("title", ""),
                    company=job.get("company_name", ""),
                    location=job.get("location", ""),
                    department=job.get("department", ""),
                    description=job.get("description", "")[:2000],  # Limit tokens
                )

                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent",
                    params={"key": settings.google_api_key},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.1,
                            "responseMimeType": "application/json",
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()

                # Extract text from Gemini response
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                result = json.loads(text)

                # Validate with Pydantic
                classification = JobClassification(
                    is_fractional=result.get("is_fractional", False),
                    employment_type=result.get("employment_type", "unknown"),
                    seniority_level=result.get("seniority_level", "unknown"),
                    confidence=result.get("confidence", 0.5),
                    hours_per_week=result.get("hours_per_week"),
                    is_remote=result.get("is_remote"),
                    reasoning=result.get("reasoning", ""),
                )

                # Add classification to job
                job["is_fractional"] = classification.is_fractional
                job["employment_type"] = classification.employment_type.value
                job["seniority_level"] = classification.seniority_level.value
                job["classification_confidence"] = classification.confidence
                job["classification_reasoning"] = classification.reasoning
                job["is_remote"] = classification.is_remote
                job["hours_per_week"] = classification.hours_per_week

            except Exception as e:
                activity.logger.error(f"Classification failed for {job.get('title')}: {e}")
                # Default to unknown
                job["is_fractional"] = False
                job["employment_type"] = "unknown"
                job["seniority_level"] = "unknown"
                job["classification_confidence"] = 0.0
                job["classification_error"] = str(e)

            classified.append(job)

    return classified


@activity.defn
async def deep_scrape_job_urls(jobs: List[dict]) -> List[dict]:
    """
    Deep scrape individual job URLs via Crawl4AI to get full descriptions.

    This is optional - if Crawl4AI is unavailable, returns jobs unchanged.
    The Greenhouse API already provides descriptions, this just enriches them.
    """
    settings = get_settings()

    if not settings.crawl4ai_url:
        activity.logger.warning("No Crawl4AI URL configured, skipping deep scrape")
        return jobs

    # First check if Crawl4AI is healthy
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            health = await client.get(f"{settings.crawl4ai_url}/health")
            if health.status_code != 200:
                activity.logger.warning("Crawl4AI health check failed, skipping deep scrape")
                return jobs
    except Exception as e:
        activity.logger.warning(f"Crawl4AI not reachable: {e}, skipping deep scrape")
        return jobs

    enriched = []
    scrape_success = 0
    scrape_failed = 0

    async with httpx.AsyncClient(timeout=60.0) as client:
        for job in jobs:
            url = job.get("url")
            if not url:
                enriched.append(job)
                continue

            try:
                response = await client.post(
                    f"{settings.crawl4ai_url}/scrape",
                    json={"url": url}
                )
                response.raise_for_status()
                data = response.json()

                # Check if scrape was successful
                if data.get("success") and data.get("markdown"):
                    # Use markdown content as enriched description
                    job["deep_scraped"] = True
                    if len(data["markdown"]) > len(job.get("description", "")):
                        job["description"] = data["markdown"][:10000]  # Limit size
                    scrape_success += 1
                else:
                    scrape_failed += 1
                    job["deep_scraped"] = False

            except Exception as e:
                activity.logger.debug(f"Deep scrape failed for {url}: {e}")
                job["deep_scraped"] = False
                scrape_failed += 1
                # Continue with existing data - don't fail the whole pipeline

            enriched.append(job)

    activity.logger.info(f"Deep scrape: {scrape_success} success, {scrape_failed} failed out of {len(jobs)} jobs")
    return enriched


@activity.defn
async def save_jobs_to_zep(jobs: List[dict]) -> dict:
    """
    Save classified jobs to Zep knowledge graph with deduplication.

    Uses job URL as unique identifier to prevent duplicates.
    """
    from zep_cloud.client import AsyncZep

    settings = get_settings()

    if not settings.zep_api_key:
        activity.logger.warning("No Zep API key, skipping graph save")
        return {"jobs_saved_to_graph": 0, "skipped_duplicates": 0}

    try:
        zep = AsyncZep(api_key=settings.zep_api_key)
        saved = 0
        skipped = 0

        for job in jobs:
            job_url = job.get("url", "")
            job_title = job.get("title", "")

            # Create unique ID from URL (or title+company as fallback)
            unique_id = job_url or f"{job_title}_{job.get('company_name', '')}"

            # Check if job already exists in graph by searching
            try:
                search_result = await zep.graph.search(
                    graph_id="jobs",
                    query=unique_id,
                    limit=1,
                )

                # If exact match found, skip
                if search_result and len(search_result.edges) > 0:
                    for edge in search_result.edges:
                        if edge.fact and unique_id in edge.fact:
                            activity.logger.info(f"Skipping duplicate job: {job_title}")
                            skipped += 1
                            continue
            except Exception as search_err:
                # Search failed, proceed with add (might be new graph)
                activity.logger.debug(f"Zep search failed, proceeding: {search_err}")

            # Build rich text episode with entity hints for ZEP to extract
            # This allows ZEP to create proper entity nodes and relationships
            company_name = job.get("company_name", "Unknown Company")
            location = job.get("location", "Location not specified")
            department = job.get("department", "")
            seniority = job.get("seniority_level", "")
            is_fractional = job.get("is_fractional", False)
            is_remote = job.get("is_remote", False)

            episode_text = f"""Job Posting: {job_title} at {company_name}

The company {company_name} has posted a position for {job_title}"""

            if department:
                episode_text += f" in the {department} department"

            episode_text += ".\n\n"

            # Add job details
            if location:
                episode_text += f"Location: {location}\n"
            if seniority:
                episode_text += f"Seniority Level: {seniority}\n"
            if is_remote:
                episode_text += f"Remote Work: Yes\n"
            if job.get("employment_type"):
                episode_text += f"Employment Type: {job.get('employment_type')}\n"

            # Add fractional flag
            if is_fractional:
                episode_text += "\nThis is a fractional role, suitable for experienced professionals seeking part-time or contract opportunities.\n"

            # Add description if available
            description = job.get("description", "")
            if description:
                # Limit description to avoid token limits
                episode_text += f"\nJob Description:\n{description[:500]}"
                if len(description) > 500:
                    episode_text += "..."
                episode_text += "\n"

            # Add skills as entities
            skills = job.get("skills", [])
            if skills:
                episode_text += "\nRequired Skills:\n"
                for skill in skills[:10]:  # Limit to top 10 skills
                    if isinstance(skill, dict):
                        skill_name = skill.get("name", "")
                        importance = skill.get("importance", "")
                        if skill_name:
                            episode_text += f"- {skill_name}"
                            if importance:
                                episode_text += f" ({importance})"
                            episode_text += "\n"
                    elif isinstance(skill, str):
                        episode_text += f"- {skill}\n"

            # Add job URL
            if job_url:
                episode_text += f"\nApply: {job_url}"

            try:
                await zep.graph.add(
                    graph_id="jobs",
                    type="text",  # Changed from "json" to "text" for entity extraction
                    data=episode_text
                )
                saved += 1
                activity.logger.info(f"Added job to ZEP: {job_title} at {company_name}")
            except Exception as e:
                # Check if it's a duplicate error
                if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
                    skipped += 1
                    activity.logger.info(f"Duplicate job in Zep: {job_title}")
                else:
                    activity.logger.warning(f"Failed to add job to Zep: {e}")

        return {"jobs_saved_to_graph": saved, "skipped_duplicates": skipped}

    except Exception as e:
        activity.logger.error(f"Zep connection failed: {e}")
        return {"jobs_saved_to_graph": 0, "skipped_duplicates": 0, "error": str(e)}
