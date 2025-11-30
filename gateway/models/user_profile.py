"""
User Profile Models

Pydantic models for user profile facts and voice sessions.
Works with existing user_profiles table (UUID primary key) and new
user_profile_facts + voice_sessions tables.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class FactType(str, Enum):
    """Categories of user profile facts extracted from conversations."""
    DESTINATION = "destination"
    ORIGIN = "origin"
    FAMILY = "family"
    PROFESSION = "profession"
    EMPLOYER = "employer"
    WORK_TYPE = "work_type"
    BUDGET = "budget"
    TIMELINE = "timeline"
    VISA_INTEREST = "visa_interest"
    LIFESTYLE = "lifestyle"
    LANGUAGE = "language"
    NET_WORTH = "net_worth"
    CHILDREN = "children"
    NATIONALITY = "nationality"


class FactSource(str, Enum):
    """How a fact was captured."""
    VOICE = "voice"  # Quick regex extraction during conversation
    LLM_REFINED = "llm_refined"  # End-of-session LLM analysis
    USER_EDIT = "user_edit"  # Manual user correction


class SessionStatus(str, Enum):
    """Voice session status."""
    ACTIVE = "active"
    ENDED = "ended"
    ABANDONED = "abandoned"


# ============================================================================
# Fact Value Schemas (for fact_value JSONB)
# ============================================================================

class DestinationValue(BaseModel):
    """Value schema for destination facts."""
    country: str
    city: Optional[str] = None
    region: Optional[str] = None
    interest_level: Optional[str] = None  # primary, exploring, backup


class OriginValue(BaseModel):
    """Value schema for origin facts."""
    country: str
    city: Optional[str] = None


class FamilyValue(BaseModel):
    """Value schema for family facts."""
    status: str  # single, married, partner
    spouse_nationality: Optional[str] = None


class ChildrenValue(BaseModel):
    """Value schema for children facts."""
    count: int
    ages: Optional[List[int]] = None


class ProfessionValue(BaseModel):
    """Value schema for profession facts."""
    title: str
    industry: Optional[str] = None


class EmployerValue(BaseModel):
    """Value schema for employer facts."""
    name: str
    industry: Optional[str] = None


class WorkTypeValue(BaseModel):
    """Value schema for work type facts."""
    type: str  # remote, hybrid, onsite, freelance, retired
    flexibility: Optional[str] = None


class BudgetValue(BaseModel):
    """Value schema for budget facts."""
    monthly: Optional[int] = None
    currency: str = "USD"
    range: Optional[str] = None  # "2000-4000"


class TimelineValue(BaseModel):
    """Value schema for timeline facts."""
    target: str  # "6 months", "1 year", "ASAP"
    specific_date: Optional[str] = None


class NetWorthValue(BaseModel):
    """Value schema for net worth facts."""
    range: Optional[str] = None
    currency: str = "USD"


class GenericFactValue(BaseModel):
    """Generic value for any fact type."""
    value: str
    details: Optional[Dict[str, Any]] = None


# ============================================================================
# Database Models
# ============================================================================

class UserProfileFact(BaseModel):
    """A single extracted fact about a user."""
    id: int
    user_profile_id: UUID
    fact_type: FactType
    fact_value: Dict[str, Any]
    source: FactSource = FactSource.VOICE
    confidence: float = Field(ge=0, le=1, default=0.5)
    session_id: Optional[str] = None
    extracted_from_message: Optional[str] = None
    is_user_verified: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfileFactCreate(BaseModel):
    """Schema for creating a new fact."""
    fact_type: FactType
    fact_value: Dict[str, Any]
    source: FactSource = FactSource.VOICE
    confidence: float = Field(ge=0, le=1, default=0.5)
    session_id: Optional[str] = None
    extracted_from_message: Optional[str] = None


class UserProfileFactUpdate(BaseModel):
    """Schema for updating a fact (user edit)."""
    fact_value: Optional[Dict[str, Any]] = None
    is_user_verified: Optional[bool] = None
    is_active: Optional[bool] = None


class VoiceSessionMessage(BaseModel):
    """A single message in a voice session."""
    role: str  # user, assistant
    content: str
    timestamp: datetime
    extracted_facts: Optional[List[Dict[str, Any]]] = None


class VoiceSession(BaseModel):
    """A voice conversation session."""
    id: int
    session_id: str
    user_profile_id: Optional[UUID] = None
    stack_user_id: Optional[str] = None
    status: SessionStatus = SessionStatus.ACTIVE
    messages: List[VoiceSessionMessage] = []
    quick_extraction: Dict[str, Any] = {}
    llm_refined_facts: Dict[str, Any] = {}
    message_count: int = 0
    duration_seconds: Optional[int] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VoiceSessionCreate(BaseModel):
    """Schema for creating a voice session."""
    session_id: str
    stack_user_id: Optional[str] = None


# ============================================================================
# API Response Models
# ============================================================================

class UserProfileSnapshot(BaseModel):
    """Aggregated user profile for quick access."""
    user_id: str
    destinations: List[str] = []
    origin: Optional[str] = None
    family_status: Optional[str] = None
    children_count: Optional[int] = None
    profession: Optional[str] = None
    employer: Optional[str] = None
    work_type: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    total_facts: int = 0
    last_session: Optional[datetime] = None


class UserFactsResponse(BaseModel):
    """Response containing user facts grouped by type."""
    user_id: str
    facts_by_type: Dict[str, List[UserProfileFact]] = {}
    total_facts: int = 0
    verified_facts: int = 0


class FactExtractionResult(BaseModel):
    """Result of extracting facts from a message."""
    facts: List[UserProfileFactCreate] = []
    raw_extraction: Dict[str, Any] = {}
    extraction_method: str = "regex"  # regex, llm


class SessionSummary(BaseModel):
    """Summary of a voice session."""
    session_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    message_count: int
    facts_extracted: int
    duration_seconds: Optional[int] = None


# ============================================================================
# Extraction Patterns (for quick regex extraction)
# ============================================================================

EXTRACTION_PATTERNS = {
    FactType.DESTINATION: [
        r"(?:moving|relocating|going|move)\s+to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"interested\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"considering\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    ],
    FactType.ORIGIN: [
        r"(?:from|live\s+in|based\s+in|currently\s+in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"I'm\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    ],
    FactType.CHILDREN: [
        r"(\d+)\s+(?:kids?|children)",
        r"(?:have|got)\s+(\d+)\s+(?:kids?|children)",
    ],
    FactType.PROFESSION: [
        r"(?:I'm\s+a|work\s+as\s+a?|I\s+am\s+a)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
    ],
    FactType.EMPLOYER: [
        r"(?:work\s+(?:for|at)|employed\s+(?:by|at))\s+([A-Z][a-zA-Z]+(?:\s+[A-Z]?[a-zA-Z]+)?)",
    ],
    FactType.WORK_TYPE: [
        r"(?:work|working)\s+(remote(?:ly)?|hybrid|from\s+home)",
        r"(freelance|self-employed|contractor)",
    ],
    FactType.BUDGET: [
        r"budget\s+(?:of\s+)?(?:around\s+)?[\$€£]?(\d+(?:,\d{3})*(?:k)?)",
        r"(\d+(?:,\d{3})*(?:k)?)\s+(?:per\s+month|monthly|a\s+month)",
    ],
    FactType.TIMELINE: [
        r"(?:within|in)\s+(\d+\s+(?:months?|years?))",
        r"(ASAP|as\s+soon\s+as\s+possible|this\s+year|next\s+year)",
    ],
}
