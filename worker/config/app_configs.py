"""
App-Specific Configuration System

Defines content generation parameters, quality thresholds, and style guidelines
for each application in the QUEST ecosystem.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


@dataclass
class AppConfig:
    """Configuration for a specific application/site"""

    # Basic Identity
    name: str
    domain: str
    display_name: str

    # Content Parameters
    tone: str
    target_audience: str
    content_focus: str
    content_angle: str

    # Article Structure
    word_count_range: Tuple[int, int]  # (min, max)
    min_sections: int
    section_style: str  # e.g., "data-driven", "practical-guide", "analytical"

    # Citation Requirements
    min_citations: int
    preferred_sources: List[str]  # Preferred publication types or domains
    citation_style: str  # e.g., "inline-links", "academic", "journalistic"

    # Image Generation
    image_style: str
    hero_image_prompt_template: str
    featured_image_prompt_template: str
    content_image_prompt_template: str

    # Quality Thresholds
    min_quality_score: float  # 0.0 - 1.0
    auto_publish_threshold: float  # 0.0 - 1.0

    # SEO & Keywords
    target_keywords_count: int
    seo_focus: str

    # Additional Guidelines
    writing_guidelines: List[str] = field(default_factory=list)
    content_requirements: List[str] = field(default_factory=list)
    brand_voice: Dict[str, str] = field(default_factory=dict)


# ============================================================================
# PLACEMENT APP CONFIGURATION
# ============================================================================

PLACEMENT_CONFIG = AppConfig(
    # Basic Identity
    name="placement",
    domain="placement.news",
    display_name="Placement",

    # Content Parameters
    tone="Professional, data-driven, authoritative with a Bloomberg/FT aesthetic",
    target_audience="Finance professionals, private equity investors, venture capitalists, M&A advisors, business executives",
    content_focus="Private equity deals, mergers & acquisitions, venture capital, market trends, financial analysis, deal structures",
    content_angle="Analytical, transaction-focused, emphasizing deal dynamics, valuation, strategic rationale, and market implications",

    # Article Structure
    word_count_range=(1200, 2000),
    min_sections=4,
    section_style="data-driven analytical",

    # Citation Requirements
    min_citations=5,
    preferred_sources=[
        "Bloomberg",
        "Financial Times",
        "Wall Street Journal",
        "Reuters",
        "PitchBook",
        "Crunchbase",
        "SEC Filings",
        "Company Press Releases",
        "Industry Reports"
    ],
    citation_style="inline-links with source attribution",

    # Image Generation
    image_style="Corporate professional, financial themes, clean modern design, Bloomberg aesthetic",
    hero_image_prompt_template="""Professional financial concept illustration, {theme}, corporate style,
clean modern design with financial motifs, Bloomberg aesthetic, high-quality business photography,
sophisticated color palette (navy, charcoal, gold accents), data visualization elements,
minimalist composition, professional boardroom or city skyline background""",

    featured_image_prompt_template="""Data visualization representing {metric}, clean modern infographic style,
professional financial design, charts and graphs, corporate color scheme,
high-contrast readable data presentation, business intelligence aesthetic""",

    content_image_prompt_template="""Professional business imagery for {topic}, corporate photography,
office environment or city business district, sophisticated lighting,
modern professional aesthetic, could include: executives in meeting,
financial district architecture, or abstract business concept visualization""",

    # Quality Thresholds
    min_quality_score=0.65,
    auto_publish_threshold=0.75,

    # SEO & Keywords
    target_keywords_count=5,
    seo_focus="Deal names, company names, transaction types, industry sectors, financial terms",

    # Additional Guidelines
    writing_guidelines=[
        "Lead with the most newsworthy aspect of the deal (size, valuation, strategic importance)",
        "Include specific financial figures when available (deal size, valuation, revenue multiples)",
        "Provide context: How does this deal compare to others in the sector?",
        "Explain the strategic rationale: Why did this transaction happen now?",
        "Include relevant market trends and industry dynamics",
        "Use precise financial terminology (EV/EBITDA, IRR, multiple, exit, etc.)",
        "Maintain objectivity - present facts and market analysis without promotional language",
        "Include forward-looking implications for the industry or market segment"
    ],

    content_requirements=[
        "Deal size or valuation (if publicly disclosed)",
        "Parties involved (buyer, seller, advisors if relevant)",
        "Strategic rationale for the transaction",
        "Industry context and market trends",
        "Timeline or deal structure details if available",
        "Expert quotes or market commentary when possible",
        "Competitive landscape analysis",
        "Potential market impact or precedent-setting aspects"
    ],

    brand_voice={
        "do": "Authoritative, precise, analytical, data-rich, objective, sophisticated",
        "dont": "Promotional, speculative without data, overly casual, hyperbolic, editorializing"
    }
)


# ============================================================================
# RELOCATION APP CONFIGURATION
# ============================================================================

RELOCATION_CONFIG = AppConfig(
    # Basic Identity
    name="relocation",
    domain="relocation.guide",  # Assuming domain
    display_name="Relocation Guide",

    # Content Parameters
    tone="Informative, practical, accessible, helpful with a friendly-expert balance",
    target_audience="Expatriates, relocating professionals, HR managers, international assignees, digital nomads, families planning international moves",
    content_focus="Visa requirements, immigration procedures, housing markets, cost of living, cultural adaptation, practical relocation logistics, country/city guides",
    content_angle="Practical, actionable guidance with step-by-step information, real-world costs, timelines, and helpful tips for successful relocation",

    # Article Structure
    word_count_range=(1000, 1800),
    min_sections=5,
    section_style="practical-guide with step-by-step structure",

    # Citation Requirements
    min_citations=4,
    preferred_sources=[
        "Government immigration websites",
        "Embassy/consulate official sites",
        "Numbeo (cost of living data)",
        "Expat forums and communities",
        "International relocation services",
        "Local housing authorities",
        "Immigration law firms",
        "World Bank / OECD data",
        "Local news sources"
    ],
    citation_style="inline-links with clear source identification",

    # Image Generation
    image_style="Travel photography, lifestyle imagery, welcoming and aspirational, authentic cultural representation",
    hero_image_prompt_template="""Vibrant travel photography of {destination}, lifestyle and cultural scene,
welcoming and aspirational feel, authentic representation, professional travel photography,
showing city life or landmarks, warm natural lighting, diverse people if included,
modern urban environment or scenic cultural location, high-quality photojournalistic style""",

    featured_image_prompt_template="""{city} skyline or iconic landmark, aspirational travel photography,
golden hour lighting, modern city life, cultural authenticity,
professional destination marketing aesthetic, welcoming atmosphere""",

    content_image_prompt_template="""Practical scene related to {topic}, authentic lifestyle photography,
real-world relocation scenarios (could include: apartment hunting, visa office,
cultural activities, daily life scenes, transportation), natural lighting,
diverse representation, helpful and realistic depiction""",

    # Quality Thresholds
    min_quality_score=0.60,
    auto_publish_threshold=0.70,

    # SEO & Keywords
    target_keywords_count=6,
    seo_focus="Destination names, visa types, relocation terms, cost-of-living keywords, practical queries",

    # Additional Guidelines
    writing_guidelines=[
        "Start with the most critical practical information (visa requirements, major costs)",
        "Use clear section headers that answer specific questions (e.g., 'How Much Does Housing Cost?')",
        "Include specific timelines (visa processing times, how long to find housing, etc.)",
        "Provide concrete cost ranges with currency conversions",
        "Offer step-by-step processes for complex procedures (visa applications, finding housing)",
        "Include insider tips and common pitfalls to avoid",
        "Balance official information with practical real-world advice",
        "Use accessible language - avoid excessive jargon, explain necessary technical terms",
        "Include cultural context that helps readers adapt successfully"
    ],

    content_requirements=[
        "Current visa/immigration requirements with official source links",
        "Cost of living data with specific ranges (housing, food, transport, etc.)",
        "Timelines and processing times for key procedures",
        "Practical step-by-step guidance for major processes",
        "Contact information or links to relevant authorities/services",
        "Common challenges or frequently asked questions addressed",
        "Cultural tips or local customs relevant to the topic",
        "Up-to-date information with date-sensitive disclaimers when appropriate"
    ],

    brand_voice={
        "do": "Helpful, clear, practical, friendly yet professional, empowering, realistic",
        "dont": "Overly complex, intimidating, vague, overly promotional, ignoring challenges"
    }
)


# ============================================================================
# CONFIG REGISTRY
# ============================================================================

_APP_CONFIGS: Dict[str, AppConfig] = {
    "placement": PLACEMENT_CONFIG,
    "relocation": RELOCATION_CONFIG,
}

AVAILABLE_APPS = list(_APP_CONFIGS.keys())


def get_app_config(app_name: str) -> AppConfig:
    """
    Retrieve configuration for a specific application.

    Args:
        app_name: Application identifier (e.g., "placement", "relocation")

    Returns:
        AppConfig instance for the specified app

    Raises:
        ValueError: If app_name is not recognized
    """
    app_name = app_name.lower().strip()

    if app_name not in _APP_CONFIGS:
        raise ValueError(
            f"Unknown app: '{app_name}'. Available apps: {', '.join(AVAILABLE_APPS)}"
        )

    return _APP_CONFIGS[app_name]


def validate_app_config(config: AppConfig) -> List[str]:
    """
    Validate an AppConfig instance for completeness and consistency.

    Args:
        config: AppConfig instance to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Check word count range
    if config.word_count_range[0] >= config.word_count_range[1]:
        errors.append(f"Invalid word_count_range: min ({config.word_count_range[0]}) must be < max ({config.word_count_range[1]})")

    # Check quality thresholds
    if not 0 <= config.min_quality_score <= 1:
        errors.append(f"min_quality_score must be between 0 and 1, got {config.min_quality_score}")

    if not 0 <= config.auto_publish_threshold <= 1:
        errors.append(f"auto_publish_threshold must be between 0 and 1, got {config.auto_publish_threshold}")

    if config.min_quality_score > config.auto_publish_threshold:
        errors.append("auto_publish_threshold must be >= min_quality_score")

    # Check required string fields are not empty
    required_fields = ['name', 'domain', 'tone', 'target_audience', 'content_focus']
    for field_name in required_fields:
        value = getattr(config, field_name)
        if not value or not value.strip():
            errors.append(f"{field_name} cannot be empty")

    return errors


# Validate configs on import
for app_name, config in _APP_CONFIGS.items():
    validation_errors = validate_app_config(config)
    if validation_errors:
        raise ValueError(f"Invalid config for '{app_name}':\n" + "\n".join(validation_errors))
