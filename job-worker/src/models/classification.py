from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class EmploymentType(str, Enum):
    FRACTIONAL = "fractional"  # C-suite/exec working part-time for multiple companies
    PART_TIME = "part_time"    # Regular part-time role
    CONTRACT = "contract"      # Fixed-term contract
    TEMPORARY = "temporary"    # Temporary/interim role
    FULL_TIME = "full_time"    # Standard full-time
    UNKNOWN = "unknown"


class SeniorityLevel(str, Enum):
    C_SUITE = "c_suite"        # CEO, CFO, CTO, etc.
    VP = "vp"                  # Vice President level
    DIRECTOR = "director"      # Director level
    MANAGER = "manager"        # Manager level
    SENIOR = "senior"          # Senior IC
    MID = "mid"                # Mid-level IC
    JUNIOR = "junior"          # Junior/Entry level
    UNKNOWN = "unknown"


class JobClassification(BaseModel):
    """Pydantic model for AI classification output"""

    is_fractional: bool = Field(
        description="True if this is a fractional/part-time executive role"
    )
    employment_type: EmploymentType = Field(
        description="Type of employment arrangement"
    )
    seniority_level: SeniorityLevel = Field(
        description="Seniority level of the role"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score for the classification"
    )
    hours_per_week: Optional[str] = Field(
        default=None,
        description="Estimated hours per week if mentioned"
    )
    is_remote: Optional[bool] = Field(
        default=None,
        description="Whether the role is remote"
    )
    reasoning: str = Field(
        description="Brief explanation for the classification"
    )


class DeepScrapedJob(BaseModel):
    """Job with full description from deep scrape"""

    title: str
    company_name: str
    location: Optional[str] = None
    department: Optional[str] = None
    url: Optional[str] = None
    full_description: Optional[str] = None
    requirements: Optional[List[str]] = None
    responsibilities: Optional[List[str]] = None
    salary_info: Optional[str] = None
    benefits: Optional[List[str]] = None


class ClassifiedJob(BaseModel):
    """Job with classification data"""

    # Original job fields
    title: str
    company_name: str
    location: Optional[str] = None
    department: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None

    # Classification fields
    is_fractional: bool = False
    employment_type: EmploymentType = EmploymentType.UNKNOWN
    seniority_level: SeniorityLevel = SeniorityLevel.UNKNOWN
    classification_confidence: float = 0.0
    classification_reasoning: Optional[str] = None

    # Enrichment fields
    skills: List[dict] = []
    is_remote: Optional[bool] = None
    hours_per_week: Optional[str] = None
