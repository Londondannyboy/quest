"""Pydantic AI-powered job classification activity."""

from typing import List, Dict
from temporalio import activity
import logging
from ..models.job_classification import classify_job, JobClassification

logger = logging.getLogger(__name__)


@activity.defn
async def classify_jobs_with_pydantic_ai(jobs: List[Dict]) -> List[Dict]:
    """
    Classify jobs using Pydantic AI with Gemini.

    Extracts:
    - Employment type and fractional status
    - Country, city, remote status
    - Job category, seniority, normalized title
    - Company industry and size
    - Required and nice-to-have skills
    - Salary information
    - Site tags for targeting

    Args:
        jobs: List of raw job dictionaries from Apify

    Returns:
        List of jobs with comprehensive AI classification
    """
    activity.logger.info(f"Classifying {len(jobs)} jobs with Pydantic AI (Gemini)")

    classified_jobs = []
    failed = 0

    for i, job in enumerate(jobs):
        try:
            # Extract fields for classification
            title = job.get("title") or job.get("job_title", "")
            description = job.get("full_description") or job.get("job_description") or job.get("description", "")
            company_name = job.get("company_name", "Unknown")
            location = job.get("location", "")
            employment_type = job.get("employment_type")
            seniority_level = job.get("seniority_level")

            # Run Pydantic AI classification
            classification: JobClassification = await classify_job(
                job_title=title,
                job_description=description,
                company_name=company_name,
                location=location,
                employment_type=employment_type,
                seniority_level=seniority_level
            )

            # Merge classification back into job dict
            job_classified = job.copy()
            job_classified.update({
                # Employment
                "employment_type": classification.employment_type,
                "is_fractional": classification.is_fractional,

                # Location
                "country": classification.country,
                "city": classification.city,
                "is_remote": classification.is_remote,
                "workplace_type": classification.workplace_type,

                # Role
                "category": classification.category,
                "seniority_level": classification.seniority_level,
                "role_title": classification.role_title,

                # Company
                "company_name": classification.company_name,
                "company_industry": classification.company_industry,
                "company_size": classification.company_size,

                # Skills
                "required_skills": classification.required_skills,
                "nice_to_have_skills": classification.nice_to_have_skills,
                "years_experience": classification.years_experience,

                # Compensation
                "salary_min": classification.salary_min,
                "salary_max": classification.salary_max,
                "salary_currency": classification.salary_currency,

                # Metadata
                "classification_confidence": classification.classification_confidence,
                "classification_reasoning": classification.reasoning,
                "site_tags": classification.site_tags,
            })

            classified_jobs.append(job_classified)

            if (i + 1) % 10 == 0:
                activity.logger.info(f"Classified {i + 1}/{len(jobs)} jobs")

        except Exception as e:
            activity.logger.warning(f"Failed to classify job {i}: {e}, using basic classification")
            failed += 1

            # Fallback: keep original job with minimal classification
            job_fallback = job.copy()
            job_fallback.update({
                "employment_type": "unknown",
                "is_fractional": False,
                "classification_confidence": 0.0,
                "classification_reasoning": f"AI classification failed: {str(e)}",
                "site_tags": []
            })
            classified_jobs.append(job_fallback)

    activity.logger.info(
        f"Classification complete: {len(classified_jobs) - failed} successful, {failed} failed"
    )

    return classified_jobs
