from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class SkillImportance(str, Enum):
    ESSENTIAL = "essential"
    BENEFICIAL = "beneficial"
    BONUS = "bonus"


class Skill(BaseModel):
    name: str
    category: str | None = None  # technical, soft, domain, tool
    importance: SkillImportance = SkillImportance.ESSENTIAL


class Job(BaseModel):
    id: str | None = None
    title: str
    company_name: str
    department: str | None = None
    location: str | None = None
    employment_type: str | None = None
    description: str | None = None
    url: str | None = None
    posted_date: datetime | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    skills: list[Skill] = []
    vertical: str = "tech"  # tech, finance, healthcare, etc.


class Company(BaseModel):
    name: str
    board_type: str  # ashby, greenhouse, lever, unknown
    board_url: str
    industry: str = "Technology"
    vertical: str = "tech"


class ScrapingResult(BaseModel):
    company_name: str
    jobs_found: int
    jobs_added: int
    jobs_updated: int
    errors: list[str] = []
    duration_seconds: float


class CompanyTrend(BaseModel):
    company_name: str
    total_jobs: int
    recent_postings: int
    hiring_velocity: str  # high, medium, low
    top_departments: dict[str, int]
    focus_areas: list[str]
