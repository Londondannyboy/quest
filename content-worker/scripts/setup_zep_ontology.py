"""
Setup Zep Ontology - Run once to configure project-wide ontology

This script sets up the custom entity and edge types for the Quest knowledge graph.
Run this once to configure Zep, or when ontology changes.

Usage:
    python scripts/setup_zep_ontology.py
"""

import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from pydantic import Field
from zep_cloud.client import AsyncZep
from zep_cloud import EntityEdgeSourceTarget
from zep_cloud.external_clients.ontology import EntityModel, EntityText, EntityInt, EdgeModel

load_dotenv()


# Define entity models using Zep's EntityModel with pydantic Field
class Company(EntityModel):
    """Company entity for financial services firms, investment banks, etc."""
    domain: EntityText = Field(description="Company domain (e.g., evercore.com)", default=None)
    industry: EntityText = Field(description="Primary industry or sector", default=None)
    headquarters_city: EntityText = Field(description="Headquarters city location", default=None)
    headquarters_country: EntityText = Field(description="Headquarters country", default=None)
    founded_year: EntityText = Field(description="Year the company was founded", default=None)
    employee_range: EntityText = Field(description="Employee count range", default=None)
    company_type: EntityText = Field(description="Type: placement_agent, investment_bank, etc.", default=None)


class Deal(EntityModel):
    """Deal entity for transactions, M&A, capital raises, etc."""
    deal_type: EntityText = Field(description="Type: M&A, capital_raising, IPO, etc.", default=None)
    value: EntityText = Field(description="Deal value (e.g., '$7.4B', '€500M')", default=None)
    date: EntityText = Field(description="Deal date or timeframe", default=None)
    status: EntityText = Field(description="Status: completed, announced, pending", default=None)
    sector: EntityText = Field(description="Industry sector of the deal", default=None)


class Person(EntityModel):
    """Person entity for executives, key people, board members."""
    role: EntityText = Field(description="Job title or role (e.g., 'CEO', 'Managing Director')", default=None)
    company: EntityText = Field(description="Associated company name", default=None)
    linkedin: EntityText = Field(description="LinkedIn profile URL", default=None)


class Job(EntityModel):
    """Job entity for job postings and roles."""
    company: EntityText = Field(description="Company name posting the job", default=None)
    location: EntityText = Field(description="Job location (city, country)", default=None)
    salary_range: EntityText = Field(description="Salary range if known", default=None)
    employment_type: EntityText = Field(description="full-time, contract, part-time", default=None)
    seniority: EntityText = Field(description="junior, mid, senior, executive", default=None)
    industry: EntityText = Field(description="Industry sector", default=None)
    posted_date: EntityText = Field(description="When the job was posted", default=None)


class Location(EntityModel):
    """Location entity for cities and regions."""
    country: EntityText = Field(description="Country name", default=None)
    region: EntityText = Field(description="Region/state/province", default=None)
    cost_of_living: EntityText = Field(description="Cost of living indicator (low/medium/high)", default=None)
    quality_of_life: EntityText = Field(description="Quality of life score or description", default=None)
    timezone: EntityText = Field(description="Timezone", default=None)


class Country(EntityModel):
    """Country entity with relocation-relevant information."""
    code: EntityText = Field(description="ISO country code (UK, US, CY)", default=None)
    visa_types: EntityText = Field(description="Available visa types for workers", default=None)
    work_permit_requirements: EntityText = Field(description="Work permit requirements", default=None)
    tax_overview: EntityText = Field(description="Basic tax information for expats", default=None)
    language: EntityText = Field(description="Primary language(s)", default=None)


class Skill(EntityModel):
    """Skill entity for technical and professional skills."""
    category: EntityText = Field(description="Category: technical, soft, domain, language", default=None)


# Edge type models using EdgeModel
class AdvisedOn(EdgeModel):
    """Company advised on a deal."""
    pass


class WorksAt(EdgeModel):
    """Person works at company."""
    pass


class PartneredWith(EdgeModel):
    """Companies have partnership."""
    pass


class RequiresEssential(EdgeModel):
    """Job requires this skill as essential/must-have."""
    pass


class RequiresPreferred(EdgeModel):
    """Job prefers this skill as nice-to-have."""
    pass


class HasSkill(EdgeModel):
    """Person has this skill."""
    pass


class PostedBy(EdgeModel):
    """Job is posted by this company."""
    pass


class LocatedIn(EdgeModel):
    """Job is located in this city/region."""
    pass


class HeadquarteredIn(EdgeModel):
    """Company headquarters in this location."""
    pass


class InCountry(EdgeModel):
    """Location is in this country."""
    pass


async def setup_ontology():
    """Set up the Zep ontology project-wide."""
    api_key = os.getenv("ZEP_API_KEY")
    if not api_key:
        print("ERROR: ZEP_API_KEY not set in environment")
        sys.exit(1)

    print("Connecting to Zep...")
    client = AsyncZep(api_key=api_key)

    print("\nSetting up ontology with:")
    print("  Entities: Company, Deal, Person, Job, Location, Country, Skill")
    print("  Edge types: 10 relationship types")

    try:
        # Set ontology project-wide (no graph_ids or user_ids)
        await client.graph.set_ontology(
            entities={
                "Company": Company,
                "Deal": Deal,
                "Person": Person,
                "Job": Job,
                "Location": Location,
                "Country": Country,
                "Skill": Skill,
            },
            edges={
                # Existing edges
                "ADVISED_ON": (
                    AdvisedOn,
                    [EntityEdgeSourceTarget(source="Company", target="Deal")]
                ),
                "WORKS_AT": (
                    WorksAt,
                    [EntityEdgeSourceTarget(source="Person", target="Company")]
                ),
                "PARTNERED_WITH": (
                    PartneredWith,
                    [EntityEdgeSourceTarget(source="Company", target="Company")]
                ),
                # Job edges
                "REQUIRES_ESSENTIAL": (
                    RequiresEssential,
                    [EntityEdgeSourceTarget(source="Job", target="Skill")]
                ),
                "REQUIRES_PREFERRED": (
                    RequiresPreferred,
                    [EntityEdgeSourceTarget(source="Job", target="Skill")]
                ),
                "HAS_SKILL": (
                    HasSkill,
                    [EntityEdgeSourceTarget(source="Person", target="Skill")]
                ),
                "POSTED_BY": (
                    PostedBy,
                    [EntityEdgeSourceTarget(source="Job", target="Company")]
                ),
                # Location edges
                "LOCATED_IN": (
                    LocatedIn,
                    [EntityEdgeSourceTarget(source="Job", target="Location")]
                ),
                "HEADQUARTERED_IN": (
                    HeadquarteredIn,
                    [EntityEdgeSourceTarget(source="Company", target="Location")]
                ),
                "IN_COUNTRY": (
                    InCountry,
                    [EntityEdgeSourceTarget(source="Location", target="Country")]
                ),
            }
        )

        print("\n✅ Ontology set successfully!")
        print("\nEntities configured: Company, Deal, Person, Job, Location, Country, Skill")
        print("Edge types configured: ADVISED_ON, WORKS_AT, PARTNERED_WITH, REQUIRES_ESSENTIAL,")
        print("                       REQUIRES_PREFERRED, HAS_SKILL, POSTED_BY, LOCATED_IN,")
        print("                       HEADQUARTERED_IN, IN_COUNTRY")

    except Exception as e:
        print(f"\n❌ Error setting ontology: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(setup_ontology())
