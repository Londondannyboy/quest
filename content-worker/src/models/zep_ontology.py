"""
Zep Ontology Definitions

Define custom entity types for the Zep knowledge graph that align with our domain.
These provide structured entity extraction while keeping Neon payload flexible.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class CompanyEntity(BaseModel):
    """
    Company entity type for Zep graph.

    Extracted from flexible Neon V2 payload when fields are available.
    """
    name: str = Field(description="Company legal name")
    domain: str = Field(description="Company domain (e.g., evercore.com)")

    # Optional structured fields - extracted from payload if available
    industry: Optional[str] = Field(None, description="Primary industry")
    headquarters_city: Optional[str] = Field(None, description="HQ city")
    headquarters_country: Optional[str] = Field(None, description="HQ country")
    founded_year: Optional[int] = Field(None, description="Year founded")
    employee_range: Optional[str] = Field(None, description="Employee count range")
    company_type: Optional[str] = Field(None, description="Type: placement_agent, etc.")


class DealEntity(BaseModel):
    """
    Deal/Transaction entity type for Zep graph.

    Extracted from narrative sections when deal information is found.
    """
    deal_name: str = Field(description="Deal name or description")
    deal_type: Optional[str] = Field(None, description="M&A, capital_raising, IPO, etc.")
    value: Optional[str] = Field(None, description="Deal value (e.g., '$7.4B')")
    date: Optional[str] = Field(None, description="Deal date or timeframe")
    parties: Optional[List[str]] = Field(None, description="Companies involved")


class PersonEntity(BaseModel):
    """
    Person entity type for Zep graph.

    Extracted when key people/executives are mentioned.
    """
    name: str = Field(description="Person's full name")
    role: Optional[str] = Field(None, description="Job title or role")
    company: Optional[str] = Field(None, description="Associated company")


class JobEntity(BaseModel):
    """
    Job entity type for Zep graph.

    Extracted from job postings and placement content.
    """
    title: str = Field(description="Job title (e.g., 'Managing Director', 'VP of Sales')")
    company: Optional[str] = Field(None, description="Company name posting the job")
    location: Optional[str] = Field(None, description="Job location (city, country)")
    salary_range: Optional[str] = Field(None, description="Salary range if known")
    employment_type: Optional[str] = Field(None, description="full-time, contract, part-time")
    seniority: Optional[str] = Field(None, description="junior, mid, senior, executive")
    industry: Optional[str] = Field(None, description="Industry sector")
    posted_date: Optional[str] = Field(None, description="When the job was posted")


class LocationEntity(BaseModel):
    """
    Location entity type for Zep graph.

    Cities and regions for relocation and job placement context.
    """
    city: str = Field(description="City name")
    country: Optional[str] = Field(None, description="Country name")
    region: Optional[str] = Field(None, description="Region/state/province")
    cost_of_living: Optional[str] = Field(None, description="Cost of living indicator (low/medium/high)")
    quality_of_life: Optional[str] = Field(None, description="Quality of life score or description")
    timezone: Optional[str] = Field(None, description="Timezone")


class CountryEntity(BaseModel):
    """
    Country entity type for Zep graph.

    Country-level information for relocation context.
    """
    name: str = Field(description="Country name")
    code: Optional[str] = Field(None, description="ISO country code (UK, US, CY)")
    visa_types: Optional[str] = Field(None, description="Available visa types for workers")
    work_permit_requirements: Optional[str] = Field(None, description="Work permit requirements")
    tax_overview: Optional[str] = Field(None, description="Basic tax information for expats")
    language: Optional[str] = Field(None, description="Primary language(s)")


class SkillEntity(BaseModel):
    """
    Skill entity type for Zep graph.

    Technical and professional skills for job matching.
    """
    name: str = Field(description="Skill name (e.g., 'Python', 'Financial Modeling')")
    category: Optional[str] = Field(None, description="Category: technical, soft, domain, language")


# Entity type configurations for Zep
COMPANY_ENTITY_TYPE = {
    "type": "Company",
    "description": "Investment banking firms, placement agents, financial institutions",
    "properties": {
        "name": {"type": "string", "required": True},
        "domain": {"type": "string", "required": True},
        "industry": {"type": "string"},
        "headquarters_city": {"type": "string"},
        "headquarters_country": {"type": "string"},
        "founded_year": {"type": "integer"},
        "employee_range": {"type": "string"},
        "company_type": {"type": "string"}
    }
}

DEAL_ENTITY_TYPE = {
    "type": "Deal",
    "description": "Transactions, M&A deals, capital raises, IPOs",
    "properties": {
        "deal_name": {"type": "string", "required": True},
        "deal_type": {"type": "string"},
        "value": {"type": "string"},
        "date": {"type": "string"},
        "parties": {"type": "array"}
    }
}

PERSON_ENTITY_TYPE = {
    "type": "Person",
    "description": "Executives, key people, board members",
    "properties": {
        "name": {"type": "string", "required": True},
        "role": {"type": "string"},
        "company": {"type": "string"}
    }
}

JOB_ENTITY_TYPE = {
    "type": "Job",
    "description": "Job postings and roles for recruitment/placement",
    "properties": {
        "title": {"type": "string", "required": True},
        "company": {"type": "string"},
        "location": {"type": "string"},
        "salary_range": {"type": "string"},
        "employment_type": {"type": "string"},
        "seniority": {"type": "string"},
        "industry": {"type": "string"},
        "posted_date": {"type": "string"}
    }
}

LOCATION_ENTITY_TYPE = {
    "type": "Location",
    "description": "Cities and regions for relocation and job placement",
    "properties": {
        "city": {"type": "string", "required": True},
        "country": {"type": "string"},
        "region": {"type": "string"},
        "cost_of_living": {"type": "string"},
        "quality_of_life": {"type": "string"},
        "timezone": {"type": "string"}
    }
}

COUNTRY_ENTITY_TYPE = {
    "type": "Country",
    "description": "Countries with relocation-relevant information",
    "properties": {
        "name": {"type": "string", "required": True},
        "code": {"type": "string"},
        "visa_types": {"type": "string"},
        "work_permit_requirements": {"type": "string"},
        "tax_overview": {"type": "string"},
        "language": {"type": "string"}
    }
}

SKILL_ENTITY_TYPE = {
    "type": "Skill",
    "description": "Technical and professional skills for job matching",
    "properties": {
        "name": {"type": "string", "required": True},
        "category": {"type": "string"}
    }
}

# Edge types for relationships
EDGE_TYPES = {
    # Existing edges
    "ADVISED_ON": {
        "from": "Company",
        "to": "Deal",
        "description": "Company advised on a deal"
    },
    "WORKS_AT": {
        "from": "Person",
        "to": "Company",
        "description": "Person works at company"
    },
    "PARTNERED_WITH": {
        "from": "Company",
        "to": "Company",
        "description": "Companies have partnership"
    },
    # New edges for Jobs
    "REQUIRES_ESSENTIAL": {
        "from": "Job",
        "to": "Skill",
        "description": "Job requires this skill as essential/must-have"
    },
    "REQUIRES_PREFERRED": {
        "from": "Job",
        "to": "Skill",
        "description": "Job prefers this skill as nice-to-have"
    },
    "HAS_SKILL": {
        "from": "Person",
        "to": "Skill",
        "description": "Person has this skill"
    },
    "POSTED_BY": {
        "from": "Job",
        "to": "Company",
        "description": "Job is posted by this company"
    },
    # New edges for Locations
    "LOCATED_IN": {
        "from": "Job",
        "to": "Location",
        "description": "Job is located in this city/region"
    },
    "HEADQUARTERED_IN": {
        "from": "Company",
        "to": "Location",
        "description": "Company headquarters in this location"
    },
    "IN_COUNTRY": {
        "from": "Location",
        "to": "Country",
        "description": "Location is in this country"
    }
}


def extract_company_entity_from_payload(company_name: str, domain: str, payload: dict) -> dict:
    """
    Extract structured company entity data from flexible V2 payload.

    Args:
        company_name: Company name
        domain: Company domain
        payload: V2 flexible payload

    Returns:
        Dict with Company entity attributes
    """
    return {
        "name": company_name,
        "domain": domain,
        "industry": payload.get("industry"),
        "headquarters_city": payload.get("headquarters_city"),
        "headquarters_country": payload.get("headquarters_country"),
        "founded_year": payload.get("founded_year"),
        "employee_range": payload.get("employee_range"),
        "company_type": payload.get("company_type", "unknown")
    }


def extract_job_entity_from_payload(job_data: dict) -> dict:
    """
    Extract structured job entity data from job payload.

    Args:
        job_data: Job data dict

    Returns:
        Dict with Job entity attributes
    """
    return {
        "title": job_data.get("title", ""),
        "company": job_data.get("company_name") or job_data.get("company"),
        "location": job_data.get("location"),
        "salary_range": job_data.get("salary_range") or job_data.get("compensation"),
        "employment_type": job_data.get("employment_type"),
        "seniority": job_data.get("seniority_level") or job_data.get("seniority"),
        "industry": job_data.get("industry") or job_data.get("role_category"),
        "posted_date": str(job_data.get("posted_date")) if job_data.get("posted_date") else None
    }


def extract_location_entity(city: str, country: str = None, region: str = None) -> dict:
    """
    Create a location entity dict.

    Args:
        city: City name
        country: Country name (optional)
        region: Region/state (optional)

    Returns:
        Dict with Location entity attributes
    """
    return {
        "city": city,
        "country": country,
        "region": region,
        "cost_of_living": None,
        "quality_of_life": None,
        "timezone": None
    }


def extract_country_entity(name: str, code: str = None) -> dict:
    """
    Create a country entity dict.

    Args:
        name: Country name
        code: ISO country code (optional)

    Returns:
        Dict with Country entity attributes
    """
    return {
        "name": name,
        "code": code,
        "visa_types": None,
        "work_permit_requirements": None,
        "tax_overview": None,
        "language": None
    }


def extract_skill_entity(name: str, category: str = None) -> dict:
    """
    Create a skill entity dict.

    Args:
        name: Skill name
        category: Skill category (optional)

    Returns:
        Dict with Skill entity attributes
    """
    return {
        "name": name,
        "category": category
    }


# All entity types for easy access
ALL_ENTITY_TYPES = {
    "Company": COMPANY_ENTITY_TYPE,
    "Deal": DEAL_ENTITY_TYPE,
    "Person": PERSON_ENTITY_TYPE,
    "Job": JOB_ENTITY_TYPE,
    "Location": LOCATION_ENTITY_TYPE,
    "Country": COUNTRY_ENTITY_TYPE,
    "Skill": SKILL_ENTITY_TYPE,
}
