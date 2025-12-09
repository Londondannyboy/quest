"""
Normalization activity for converting raw scraped jobs to normalized format.

Uses Pydantic models for validation and normalization of job data.
"""

from temporalio import activity
from typing import List, Dict, Any

from ..models.normalized import (
    NormalizedJob,
    NormalizedLocation,
    NormalizedCompany,
    NormalizedSalary,
)


def normalize_job(raw_job: dict, source: str = "unknown") -> dict:
    """
    Normalize a single job using Pydantic models.

    Returns a dict ready for database insertion with all normalized fields.
    """
    try:
        # Parse location
        location_str = raw_job.get("location")
        location = NormalizedLocation.from_string(location_str)

        # Parse salary if present
        salary = None
        salary_str = raw_job.get("compensation") or raw_job.get("salary_info") or raw_job.get("salary")
        if salary_str:
            salary = NormalizedSalary.from_string(salary_str)

        # Create normalized job
        normalized = NormalizedJob.from_raw(raw_job, source=source)

        # Convert back to dict for database
        return {
            # Core fields
            "title": normalized.title,
            "company_name": normalized.company.name,
            "url": normalized.url,

            # Location (normalized)
            "location": location.city or location.raw_location,
            "location_city": location.city,
            "location_country": location.country.value if location.country else None,
            "is_remote": location.is_remote or normalized.workplace_type.value == "Remote",

            # Classification (normalized)
            "employment_type": normalized.employment_type.value,
            "seniority_level": normalized.seniority_level.value,
            "department": normalized.department.value,
            "is_fractional": normalized.is_fractional,
            "executive_role": normalized.executive_role.value if normalized.executive_role else None,
            "workplace_type": normalized.workplace_type.value,

            # Salary (normalized)
            "salary_min": salary.min_amount if salary else None,
            "salary_max": salary.max_amount if salary else None,
            "salary_currency": salary.currency if salary else None,

            # Time commitment
            "hours_per_week": normalized.hours_per_week,

            # Description
            "description_snippet": normalized.description_snippet,
            "full_description": normalized.full_description,

            # Structured content
            "responsibilities": normalized.responsibilities,
            "requirements": normalized.requirements,
            "qualifications": normalized.qualifications,
            "benefits": normalized.benefits,
            "skills_required": normalized.skills_required,

            # Company context
            "about_company": normalized.about_company,
            "about_team": normalized.about_team,

            # Dates
            "posted_date": normalized.posted_date,

            # Classification metadata
            "classification_confidence": normalized.classification_confidence,
            "classification_reasoning": normalized.classification_reasoning,

            # Site routing
            "site_tags": normalized.site_tags,

            # Raw data for reference
            "raw_data": raw_job,
        }

    except Exception as e:
        # If normalization fails, return basic fields
        return {
            "title": raw_job.get("title", "Unknown"),
            "company_name": raw_job.get("company_name", "Unknown"),
            "url": raw_job.get("url", ""),
            "location": raw_job.get("location"),
            "department": raw_job.get("department"),
            "employment_type": raw_job.get("employment_type"),
            "full_description": raw_job.get("description") or raw_job.get("full_description"),
            "is_fractional": False,
            "site_tags": ["all"],
            "normalization_error": str(e),
            "raw_data": raw_job,
        }


@activity.defn
async def normalize_jobs(data: dict) -> dict:
    """
    Normalize a batch of scraped jobs.

    Input: {"company": {...}, "jobs": [...], "source": "ashby"}
    Output: {"company": {...}, "jobs": [...normalized...]}
    """
    company = data["company"]
    jobs = data["jobs"]
    source = data.get("source", "unknown")

    normalized_jobs = []
    errors = []

    for raw_job in jobs:
        try:
            # Add company name if not present
            if "company_name" not in raw_job:
                raw_job["company_name"] = company.get("name", "Unknown")

            normalized = normalize_job(raw_job, source=source)
            normalized_jobs.append(normalized)

        except Exception as e:
            errors.append({
                "title": raw_job.get("title", "Unknown"),
                "error": str(e)
            })

    return {
        "company": company,
        "jobs": normalized_jobs,
        "normalization_errors": errors,
    }


@activity.defn
async def normalize_single_job(job_data: dict) -> dict:
    """
    Normalize a single job (for real-time processing).
    """
    source = job_data.pop("source", "unknown")
    return normalize_job(job_data, source=source)


def compute_enhanced_site_tags(job: dict) -> List[str]:
    """
    Compute site tags based on normalized classification.

    This replaces the basic compute_site_tags function with
    more granular routing based on normalized data.
    """
    tags = ["all"]  # Every job goes to master list

    # Fractional jobs
    if job.get("is_fractional"):
        tags.append("fractional")

    # Part-time/contract executive roles also go to fractional
    employment_type = (job.get("employment_type") or "").lower()
    seniority = (job.get("seniority_level") or "").lower()

    if employment_type in ("part-time", "contract", "interim", "temporary", "fractional"):
        if seniority in ("c-suite", "vp", "director", "head"):
            if "fractional" not in tags:
                tags.append("fractional")

    # Department-specific tags
    department = (job.get("department") or "").lower()
    if "finance" in department:
        tags.append("finance-jobs")
    if "marketing" in department:
        tags.append("marketing-jobs")
    if "engineering" in department or "technology" in department:
        tags.append("tech-jobs")
    if "operations" in department:
        tags.append("operations-jobs")
    if "sales" in department:
        tags.append("sales-jobs")
    if "product" in department:
        tags.append("product-jobs")

    # Executive role tags
    exec_role = job.get("executive_role", "")
    if exec_role:
        role_lower = exec_role.lower()
        if "cfo" in role_lower:
            tags.append("cfo-jobs")
        if "cmo" in role_lower:
            tags.append("cmo-jobs")
        if "cto" in role_lower:
            tags.append("cto-jobs")
        if "coo" in role_lower:
            tags.append("coo-jobs")
        if "ceo" in role_lower:
            tags.append("ceo-jobs")

    # Location tags
    location_country = job.get("location_country", "")
    location_city = (job.get("location_city") or job.get("location") or "").lower()

    if location_country == "GB":
        tags.append("uk-jobs")
        if "london" in location_city:
            tags.append("london-jobs")
        elif "manchester" in location_city:
            tags.append("manchester-jobs")
        elif "bristol" in location_city:
            tags.append("bristol-jobs")
        elif "birmingham" in location_city:
            tags.append("birmingham-jobs")
    elif location_country == "US":
        tags.append("us-jobs")

    # Remote jobs
    if job.get("is_remote"):
        tags.append("remote-jobs")

    # All startup/tech jobs
    tags.append("startup-jobs")

    return list(set(tags))  # Deduplicate
