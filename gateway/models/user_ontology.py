"""
User Ontology for ZEP Knowledge Graph

Comprehensive entity and edge types for user profiles across all Quest apps.
Supports:
- Personal relocation (digital nomads, expats)
- Corporate relocation (company reps, trust setup)
- Job seeking and career development
- Mixed motivations (personal + professional)

Limits (per Zep docs):
- Max 10 custom entity types
- Max 10 custom edge types
- Max 10 fields per model
"""

from pydantic import Field
from typing import Optional, List

# Import Zep's ontology classes
try:
    from zep_cloud.external_clients.ontology import EntityModel, EntityText, EdgeModel
    from zep_cloud import EntityEdgeSourceTarget
    ZEP_USER_ONTOLOGY_AVAILABLE = True
except ImportError:
    from pydantic import BaseModel as EntityModel
    EntityText = Optional[str]
    EdgeModel = EntityModel
    EntityEdgeSourceTarget = None
    ZEP_USER_ONTOLOGY_AVAILABLE = False


# ============================================================================
# ENTITY TYPES (10/10)
# ============================================================================

class UserEntity(EntityModel):
    """
    Central user node - the person using Quest apps.
    Can be an individual or company representative.
    """
    user_type: EntityText = Field(
        default=None,
        description="Type: individual, company_representative, both"
    )
    source_app: EntityText = Field(
        default=None,
        description="Primary app: relocation, placement, chief-of-staff, jobs"
    )
    stack_user_id: EntityText = Field(
        default=None,
        description="Stack Auth user ID for cross-app identity"
    )
    nationality: EntityText = Field(
        default=None,
        description="User's nationality/citizenship"
    )
    languages: EntityText = Field(
        default=None,
        description="Languages spoken (comma-separated)"
    )


class DestinationEntity(EntityModel):
    """
    A place the user is interested in relocating to.
    Could be for personal move, business setup, or both.
    """
    interest_level: EntityText = Field(
        default=None,
        description="Level: primary, exploring, backup, researching"
    )
    context: EntityText = Field(
        default=None,
        description="Context: personal, business, both"
    )
    visa_researched: EntityText = Field(
        default=None,
        description="Visa types they've researched"
    )
    last_updated: EntityText = Field(
        default=None,
        description="When interest was last expressed/updated"
    )


class OriginEntity(EntityModel):
    """
    User's current or previous location.
    """
    location_type: EntityText = Field(
        default=None,
        description="Type: current, previous, tax_residence"
    )
    duration: EntityText = Field(
        default=None,
        description="How long at this location"
    )


class CareerProfileEntity(EntityModel):
    """
    User's professional profile - job, skills, experience.
    Supports job seekers and career development tracking.
    """
    job_title: EntityText = Field(
        default=None,
        description="Current or target job title"
    )
    industry: EntityText = Field(
        default=None,
        description="Industry sector"
    )
    experience_level: EntityText = Field(
        default=None,
        description="Level: entry, mid, senior, executive, c-suite"
    )
    work_style: EntityText = Field(
        default=None,
        description="Style: remote, hybrid, office, freelance, founder"
    )
    skills: EntityText = Field(
        default=None,
        description="Key skills (comma-separated)"
    )


class OrganizationEntity(EntityModel):
    """
    Company the user works for OR represents for relocation.
    Supports both employment and corporate relocation use cases.
    """
    company_type: EntityText = Field(
        default=None,
        description="Type: employer, client_company, own_business, trust"
    )
    industry: EntityText = Field(
        default=None,
        description="Company industry"
    )
    size: EntityText = Field(
        default=None,
        description="Size: startup, sme, enterprise"
    )
    relocation_budget: EntityText = Field(
        default=None,
        description="Corporate relocation budget if applicable"
    )


class GoalEntity(EntityModel):
    """
    User goals - career, personal development, business.
    Supports career coaching and personal development tracking.
    """
    goal_type: EntityText = Field(
        default=None,
        description="Type: career, personal, business, financial, lifestyle"
    )
    timeframe: EntityText = Field(
        default=None,
        description="When: short_term, medium_term, long_term"
    )
    priority: EntityText = Field(
        default=None,
        description="Priority: high, medium, low"
    )
    status: EntityText = Field(
        default=None,
        description="Status: active, achieved, paused, abandoned"
    )


class MotivationEntity(EntityModel):
    """
    Why the user wants to relocate or make a change.
    Supports both personal and professional motivations.
    """
    motivation_type: EntityText = Field(
        default=None,
        description="Type: personal, professional, both"
    )
    category: EntityText = Field(
        default=None,
        description="Category: tax, lifestyle, family, career, adventure, cost_of_living, weather, business_setup"
    )
    strength: EntityText = Field(
        default=None,
        description="How important: critical, important, nice_to_have"
    )


class FamilyUnitEntity(EntityModel):
    """
    User's family composition affecting relocation decisions.
    """
    status: EntityText = Field(
        default=None,
        description="Status: single, partnered, married, family"
    )
    partner_relocating: EntityText = Field(
        default=None,
        description="Is partner relocating: yes, no, maybe"
    )
    children_count: EntityText = Field(
        default=None,
        description="Number of children"
    )
    children_ages: EntityText = Field(
        default=None,
        description="Children's ages (comma-separated)"
    )
    school_requirements: EntityText = Field(
        default=None,
        description="School needs: international, local, homeschool"
    )


class FinancialProfileEntity(EntityModel):
    """
    User's financial situation for relocation/job decisions.
    """
    monthly_budget: EntityText = Field(
        default=None,
        description="Monthly budget for relocation destination"
    )
    income_range: EntityText = Field(
        default=None,
        description="Current/target income range"
    )
    currency_preference: EntityText = Field(
        default=None,
        description="Preferred currency: USD, EUR, GBP"
    )
    tax_situation: EntityText = Field(
        default=None,
        description="Tax consideration level: critical, important, not_priority"
    )
    savings_runway: EntityText = Field(
        default=None,
        description="Months of savings available"
    )


class PreferenceEntity(EntityModel):
    """
    User preferences for destination, lifestyle, job.
    Generic preferences that apply across use cases.
    """
    category: EntityText = Field(
        default=None,
        description="Category: climate, culture, language, safety, healthcare, cost, infrastructure"
    )
    importance: EntityText = Field(
        default=None,
        description="How important: must_have, important, nice_to_have"
    )
    specific_value: EntityText = Field(
        default=None,
        description="Specific preference value"
    )


# ============================================================================
# EDGE TYPES (10/10)
# ============================================================================

class InterestedInEdge(EdgeModel):
    """User is interested in a destination for relocation/business."""
    interest_level: EntityText = Field(
        default=None,
        description="Level: primary, exploring, backup"
    )
    context: EntityText = Field(
        default=None,
        description="Context: personal, business, both"
    )
    first_mentioned: EntityText = Field(
        default=None,
        description="When first expressed interest"
    )


class LocatedInEdge(EdgeModel):
    """User's current or previous location."""
    location_type: EntityText = Field(
        default=None,
        description="Type: current, previous, tax_residence"
    )


class HasCareerEdge(EdgeModel):
    """User's career/professional profile."""
    status: EntityText = Field(
        default=None,
        description="Status: current, target, previous"
    )


class EmployedByEdge(EdgeModel):
    """User works for an organization."""
    role: EntityText = Field(
        default=None,
        description="Role: employee, founder, executive, contractor"
    )
    start_date: EntityText = Field(
        default=None,
        description="When started"
    )


class RepresentsEdge(EdgeModel):
    """User represents an organization for relocation/business setup."""
    capacity: EntityText = Field(
        default=None,
        description="Capacity: decision_maker, researcher, influencer"
    )


class HasGoalEdge(EdgeModel):
    """User has a goal (career, personal, business)."""
    priority: EntityText = Field(
        default=None,
        description="Priority: high, medium, low"
    )


class MotivatedByEdge(EdgeModel):
    """User is motivated by a factor."""
    strength: EntityText = Field(
        default=None,
        description="Strength: critical, important, nice_to_have"
    )


class HasFamilyEdge(EdgeModel):
    """User's family unit."""
    pass  # Attributes on FamilyUnit entity


class HasFinancesEdge(EdgeModel):
    """User's financial profile."""
    pass  # Attributes on FinancialProfile entity


class PrefersEdge(EdgeModel):
    """User preference."""
    importance: EntityText = Field(
        default=None,
        description="Importance: must_have, important, nice_to_have"
    )


# ============================================================================
# ONTOLOGY CONFIGURATION
# ============================================================================

USER_ENTITY_TYPES = {
    "User": UserEntity,
    "Destination": DestinationEntity,
    "Origin": OriginEntity,
    "CareerProfile": CareerProfileEntity,
    "Organization": OrganizationEntity,
    "Goal": GoalEntity,
    "Motivation": MotivationEntity,
    "FamilyUnit": FamilyUnitEntity,
    "FinancialProfile": FinancialProfileEntity,
    "Preference": PreferenceEntity,
}

USER_EDGE_TYPES_CONFIG = {
    "INTERESTED_IN": {
        "model": InterestedInEdge,
        "source": "User",
        "target": "Destination",
        "description": "User interested in destination for relocation/business"
    },
    "LOCATED_IN": {
        "model": LocatedInEdge,
        "source": "User",
        "target": "Origin",
        "description": "User's current or previous location"
    },
    "HAS_CAREER": {
        "model": HasCareerEdge,
        "source": "User",
        "target": "CareerProfile",
        "description": "User's professional profile"
    },
    "EMPLOYED_BY": {
        "model": EmployedByEdge,
        "source": "User",
        "target": "Organization",
        "description": "User works for organization"
    },
    "REPRESENTS": {
        "model": RepresentsEdge,
        "source": "User",
        "target": "Organization",
        "description": "User represents org for relocation/business"
    },
    "HAS_GOAL": {
        "model": HasGoalEdge,
        "source": "User",
        "target": "Goal",
        "description": "User's goals (career, personal, business)"
    },
    "MOTIVATED_BY": {
        "model": MotivatedByEdge,
        "source": "User",
        "target": "Motivation",
        "description": "User's motivations for change"
    },
    "HAS_FAMILY": {
        "model": HasFamilyEdge,
        "source": "User",
        "target": "FamilyUnit",
        "description": "User's family composition"
    },
    "HAS_FINANCES": {
        "model": HasFinancesEdge,
        "source": "User",
        "target": "FinancialProfile",
        "description": "User's financial situation"
    },
    "PREFERS": {
        "model": PrefersEdge,
        "source": "User",
        "target": "Preference",
        "description": "User's preferences"
    },
}


def get_user_ontology_config():
    """
    Get the user ontology configuration in Zep's expected format.

    Returns dict with 'entities' and 'edges' ready for set_ontology().
    """
    if not ZEP_USER_ONTOLOGY_AVAILABLE:
        raise ImportError("zep-cloud package required for ontology setup")

    entities = USER_ENTITY_TYPES

    edges = {}
    for edge_name, config in USER_EDGE_TYPES_CONFIG.items():
        source_target = []
        if config.get("source") and config.get("target"):
            source_target.append(
                EntityEdgeSourceTarget(
                    source=config["source"],
                    target=config["target"]
                )
            )

        edges[edge_name] = (config["model"], source_target)

    return {
        "entities": entities,
        "edges": edges
    }


# ============================================================================
# HELPER FUNCTIONS FOR PROFILE → ENTITY EXTRACTION
# ============================================================================

def extract_user_entity(user_id: str, profile: dict, app_id: str = "relocation") -> dict:
    """Extract User entity from profile data."""
    return {
        "name": f"User {user_id}",
        "user_type": profile.get("user_type", "individual"),
        "source_app": app_id,
        "stack_user_id": user_id,
        "nationality": profile.get("nationality"),
        "languages": profile.get("languages")
    }


def extract_destination_entity(country: str, interest_info: dict = None) -> dict:
    """Extract Destination entity."""
    info = interest_info or {}
    return {
        "name": country,
        "interest_level": info.get("interest_level", "exploring"),
        "context": info.get("context", "personal"),
        "visa_researched": info.get("visa_researched"),
        "last_updated": info.get("last_updated")
    }


def extract_career_entity(profile: dict) -> dict:
    """Extract CareerProfile entity from profile."""
    return {
        "name": profile.get("job_title") or "Career Profile",
        "job_title": profile.get("job_title"),
        "industry": profile.get("industry"),
        "experience_level": profile.get("experience_level"),
        "work_style": "remote" if profile.get("remote_work") else profile.get("work_style"),
        "skills": profile.get("skills")
    }


def extract_organization_entity(profile: dict) -> dict:
    """Extract Organization entity."""
    return {
        "name": profile.get("employer") or profile.get("company_name") or "Organization",
        "company_type": profile.get("company_type", "employer"),
        "industry": profile.get("company_industry"),
        "size": profile.get("company_size")
    }


def extract_goal_entity(goal_data: dict) -> dict:
    """Extract Goal entity."""
    return {
        "name": goal_data.get("description") or goal_data.get("name") or "Goal",
        "goal_type": goal_data.get("type", "personal"),
        "timeframe": goal_data.get("timeframe"),
        "priority": goal_data.get("priority", "medium"),
        "status": goal_data.get("status", "active")
    }


def extract_motivation_entity(motive: str, category: str = None) -> dict:
    """Extract Motivation entity."""
    # Map common motivations to categories
    category_map = {
        "tax": "tax",
        "taxes": "tax",
        "lower taxes": "tax",
        "lifestyle": "lifestyle",
        "adventure": "adventure",
        "family": "family",
        "children": "family",
        "career": "career",
        "job": "career",
        "cost": "cost_of_living",
        "cheaper": "cost_of_living",
        "weather": "weather",
        "climate": "weather",
        "sun": "weather",
        "business": "business_setup",
        "startup": "business_setup",
        "company": "business_setup",
    }

    detected_category = category
    if not detected_category:
        motive_lower = motive.lower()
        for keyword, cat in category_map.items():
            if keyword in motive_lower:
                detected_category = cat
                break

    return {
        "name": motive,
        "motivation_type": "both",  # Default to both, can be refined
        "category": detected_category or "lifestyle",
        "strength": "important"
    }


def extract_family_entity(profile: dict) -> dict:
    """Extract FamilyUnit entity."""
    return {
        "name": "Family",
        "status": profile.get("family_status", "unknown"),
        "partner_relocating": profile.get("partner_relocating"),
        "children_count": str(profile.get("number_of_children")) if profile.get("number_of_children") else None,
        "children_ages": profile.get("children_ages"),
        "school_requirements": profile.get("school_requirements")
    }


def extract_financial_entity(profile: dict) -> dict:
    """Extract FinancialProfile entity."""
    return {
        "name": "Finances",
        "monthly_budget": str(profile.get("budget_monthly")) if profile.get("budget_monthly") else None,
        "income_range": profile.get("income_range"),
        "currency_preference": profile.get("currency_preference"),
        "tax_situation": profile.get("tax_priority"),
        "savings_runway": profile.get("savings_runway")
    }


def extract_preference_entity(category: str, value: str, importance: str = "important") -> dict:
    """Extract Preference entity."""
    return {
        "name": f"{category}: {value}",
        "category": category,
        "importance": importance,
        "specific_value": value
    }
