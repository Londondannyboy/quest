"""Data models for Apify API interactions."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class ApifyRunStatus(str, Enum):
    """Status of an Apify actor run."""

    READY = "READY"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED-OUT"
    ABORTED = "ABORTED"


class ApifyRunInput(BaseModel):
    """Input configuration for LinkedIn Jobs Scraper actor."""

    job_title: str = "Fractional"
    location: str = "United Kingdom"
    searchKeywords: str = "fractional"
    jobs_entries: int = 100
    start_jobs: int = 0
    scrapeJobDetails: bool = True
    job_post_time: Optional[str] = None  # e.g., "r86400" for last 24 hours


class ApifyRunResponse(BaseModel):
    """Response from starting an Apify run."""

    id: str  # runId
    actId: str
    status: ApifyRunStatus
    defaultDatasetId: Optional[str] = None
    startedAt: Optional[datetime] = None


class ApifyJob(BaseModel):
    """Job data returned from Apify LinkedIn scraper."""

    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    employmentType: Optional[str] = None
    seniority: Optional[str] = None
    postedDate: Optional[str] = None

    def to_internal_job(self) -> dict:
        """Convert to internal job format for database storage."""
        return {
            "title": self.title or "",
            "company_name": self.company or "",
            "location": self.location or "",
            "description": self.description or "",
            "url": self.url or "",
            "employment_type": self.employmentType or "",
            "seniority_level": self.seniority or "",
            "source": "linkedin_apify",
        }
