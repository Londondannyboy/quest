from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict


class SkillImportance(str, Enum):
    ESSENTIAL = "essential"
    BENEFICIAL = "beneficial"
    BONUS = "bonus"


class Skill(BaseModel):
    name: str
    category: Optional[str] = None  # technical, soft, domain, tool
    importance: SkillImportance = SkillImportance.ESSENTIAL


class Job(BaseModel):
    id: Optional[str] = None
    title: str
    company_name: str
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    posted_date: Optional[datetime] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    skills: List[Skill] = []
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
    errors: List[str] = []
    duration_seconds: float


class CompanyTrend(BaseModel):
    company_name: str
    total_jobs: int
    recent_postings: int
    hiring_velocity: str  # high, medium, low
    top_departments: Dict[str, int]
    focus_areas: List[str]
