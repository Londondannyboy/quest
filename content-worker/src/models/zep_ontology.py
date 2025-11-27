"""
Zep Ontology Definitions

Custom entity and edge types for the Zep knowledge graph.
Uses Zep's EntityModel format for proper ontology registration.

Limits (per Zep docs):
- Max 10 custom entity types
- Max 10 custom edge types
- Max 10 fields per model
"""

from pydantic import Field
from typing import Optional, List

# Try to import Zep's ontology classes, fall back to basic Pydantic if not available
try:
    from zep_cloud.external_clients.ontology import EntityModel, EntityText, EdgeModel
    from zep_cloud import EntityEdgeSourceTarget
    ZEP_ONTOLOGY_AVAILABLE = True
except ImportError:
    # Fallback for environments without zep-cloud
    from pydantic import BaseModel as EntityModel
    EntityText = Optional[str]
    EdgeModel = EntityModel
    EntityEdgeSourceTarget = None
    ZEP_ONTOLOGY_AVAILABLE = False


# ============================================================================
# ENTITY TYPES (max 10)
# ============================================================================

class CompanyEntity(EntityModel):
    """
    Investment banks, placement agents, financial institutions.
    Extracted from company profiles and articles.
    """
    industry: EntityText = Field(default=None, description="Primary industry (e.g., Investment Banking, Private Equity)")
    headquarters: EntityText = Field(default=None, description="HQ location (city, country)")
    company_type: EntityText = Field(default=None, description="Type: placement_agent, investment_bank, pe_firm, etc.")
    employee_range: EntityText = Field(default=None, description="Employee count range (e.g., 1000-5000)")
    founded_year: EntityText = Field(default=None, description="Year company was founded")


class DealEntity(EntityModel):
    """
    M&A deals, capital raises, IPOs, fundraises.
    Extracted from news articles and company deal history.
    """
    deal_type: EntityText = Field(default=None, description="Type: M&A, capital_raise, IPO, fundraise, restructuring")
    deal_value: EntityText = Field(default=None, description="Deal value (e.g., $7.4B, $500M)")
    deal_date: EntityText = Field(default=None, description="Date or year of deal")
    status: EntityText = Field(default=None, description="Status: announced, completed, pending")


class PersonEntity(EntityModel):
    """
    Executives, key people, board members.
    Extracted from company profiles and news.
    """
    role: EntityText = Field(default=None, description="Job title (e.g., CEO, Managing Director)")
    company: EntityText = Field(default=None, description="Primary company affiliation")
    seniority: EntityText = Field(default=None, description="Level: executive, senior, mid-level")


class ArticleEntity(EntityModel):
    """
    News articles, guides, comparisons we've published.
    Created when articles are synced to Zep.
    """
    article_type: EntityText = Field(default=None, description="Type: news, guide, comparison")
    app: EntityText = Field(default=None, description="App context: placement, relocation, jobs")
    topic: EntityText = Field(default=None, description="Main topic or subject")


class LocationEntity(EntityModel):
    """
    Cities and regions for relocation and job placement.
    """
    country: EntityText = Field(default=None, description="Country name")
    region: EntityText = Field(default=None, description="Region/state/province")
    cost_of_living: EntityText = Field(default=None, description="Cost indicator: low, medium, high")


class CountryEntity(EntityModel):
    """
    Countries with visa/relocation information.
    """
    code: EntityText = Field(default=None, description="ISO country code (UK, US, CY)")
    visa_types: EntityText = Field(default=None, description="Available visa types")
    tax_overview: EntityText = Field(default=None, description="Basic tax info for expats")


class JobEntity(EntityModel):
    """
    Job postings for recruitment/placement.
    """
    company: EntityText = Field(default=None, description="Hiring company")
    location: EntityText = Field(default=None, description="Job location")
    seniority: EntityText = Field(default=None, description="Level: junior, mid, senior, executive")
    salary_range: EntityText = Field(default=None, description="Compensation range")


class SkillEntity(EntityModel):
    """
    Technical and professional skills.
    """
    category: EntityText = Field(default=None, description="Category: technical, soft, domain, language")


# ============================================================================
# EDGE TYPES (max 10)
# ============================================================================

class AdvisedOnEdge(EdgeModel):
    """Company advised on a deal/transaction."""
    role: EntityText = Field(default=None, description="Advisory role: lead_advisor, co-advisor, etc.")


class WorksAtEdge(EdgeModel):
    """Person works at a company."""
    start_date: EntityText = Field(default=None, description="When they started")


class HeadquarteredInEdge(EdgeModel):
    """Company is headquartered in a location."""
    pass  # No additional properties needed


class MentionsEdge(EdgeModel):
    """Article mentions a company/person/deal."""
    relevance: EntityText = Field(default=None, description="Relevance: primary, secondary, mentioned")


class LocatedInEdge(EdgeModel):
    """Job/Company is located in a city/region."""
    pass


class PartneredWithEdge(EdgeModel):
    """Companies have a partnership."""
    partnership_type: EntityText = Field(default=None, description="Type: strategic, distribution, etc.")


class RequiresSkillEdge(EdgeModel):
    """Job requires a skill."""
    importance: EntityText = Field(default=None, description="essential, preferred, nice-to-have")


class InCountryEdge(EdgeModel):
    """Location is in a country."""
    pass


# ============================================================================
# ONTOLOGY CONFIGURATION
# ============================================================================

# Entity types to register with Zep
ENTITY_TYPES = {
    "Company": CompanyEntity,
    "Deal": DealEntity,
    "Person": PersonEntity,
    "Article": ArticleEntity,
    "Location": LocationEntity,
    "Country": CountryEntity,
    "Job": JobEntity,
    "Skill": SkillEntity,
}

# Edge types with source/target constraints
# Format: "EDGE_NAME": (EdgeModel, [EntityEdgeSourceTarget(source="X", target="Y")])
EDGE_TYPES_CONFIG = {
    "ADVISED_ON": {
        "model": AdvisedOnEdge,
        "source": "Company",
        "target": "Deal",
        "description": "Company advised on a deal"
    },
    "WORKS_AT": {
        "model": WorksAtEdge,
        "source": "Person",
        "target": "Company",
        "description": "Person works at company"
    },
    "HEADQUARTERED_IN": {
        "model": HeadquarteredInEdge,
        "source": "Company",
        "target": "Location",
        "description": "Company HQ location"
    },
    "MENTIONS": {
        "model": MentionsEdge,
        "source": "Article",
        "target": None,  # Can mention Company, Person, Deal
        "description": "Article mentions entity"
    },
    "LOCATED_IN": {
        "model": LocatedInEdge,
        "source": None,  # Job or Company
        "target": "Location",
        "description": "Entity located in city"
    },
    "PARTNERED_WITH": {
        "model": PartneredWithEdge,
        "source": "Company",
        "target": "Company",
        "description": "Partnership between companies"
    },
    "REQUIRES_SKILL": {
        "model": RequiresSkillEdge,
        "source": "Job",
        "target": "Skill",
        "description": "Job requires skill"
    },
    "IN_COUNTRY": {
        "model": InCountryEdge,
        "source": "Location",
        "target": "Country",
        "description": "Location is in country"
    },
}


def get_zep_ontology_config():
    """
    Get the ontology configuration in Zep's expected format.

    Returns dict with 'entities' and 'edges' ready for set_ontology().
    """
    if not ZEP_ONTOLOGY_AVAILABLE:
        raise ImportError("zep-cloud package required for ontology setup")

    entities = ENTITY_TYPES

    edges = {}
    for edge_name, config in EDGE_TYPES_CONFIG.items():
        source_target = []
        if config.get("source") and config.get("target"):
            source_target.append(
                EntityEdgeSourceTarget(
                    source=config["source"],
                    target=config["target"]
                )
            )
        elif config.get("source"):
            source_target.append(
                EntityEdgeSourceTarget(source=config["source"])
            )
        elif config.get("target"):
            source_target.append(
                EntityEdgeSourceTarget(target=config["target"])
            )

        edges[edge_name] = (config["model"], source_target)

    return {
        "entities": entities,
        "edges": edges
    }


# ============================================================================
# LEGACY HELPER FUNCTIONS (for backwards compatibility)
# ============================================================================

def extract_company_entity_from_payload(company_name: str, domain: str, payload: dict) -> dict:
    """
    Extract structured company entity data from flexible V2 payload.
    """
    return {
        "name": company_name,
        "domain": domain,
        "industry": payload.get("industry"),
        "headquarters": payload.get("headquarters") or payload.get("headquarters_city"),
        "company_type": payload.get("company_type", "unknown"),
        "employee_range": payload.get("employee_range"),
        "founded_year": str(payload.get("founded_year")) if payload.get("founded_year") else None
    }


def extract_deal_entity(deal_data: dict) -> dict:
    """Extract deal entity from deal data."""
    return {
        "name": deal_data.get("deal_name") or deal_data.get("name", "Unknown Deal"),
        "deal_type": deal_data.get("deal_type"),
        "deal_value": deal_data.get("value") or deal_data.get("deal_value"),
        "deal_date": deal_data.get("date") or deal_data.get("deal_date"),
        "status": deal_data.get("status", "completed")
    }


def extract_person_entity(person_data: dict) -> dict:
    """Extract person entity from person data."""
    return {
        "name": person_data.get("name", "Unknown"),
        "role": person_data.get("role") or person_data.get("title"),
        "company": person_data.get("company"),
        "seniority": person_data.get("seniority")
    }


def extract_article_entity(article_data: dict) -> dict:
    """Extract article entity from article data."""
    return {
        "name": article_data.get("title", "Untitled"),
        "article_type": article_data.get("article_type"),
        "app": article_data.get("app"),
        "topic": article_data.get("topic")
    }
