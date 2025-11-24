"""
App Configurations for Quest

Each app has specific:
- Keywords for news monitoring
- Exclusions (topics to avoid)
- Interests (what to prioritize)
- Geographic focus
- Target audience context
"""

from typing import Dict, List
from pydantic import BaseModel


class AppConfig(BaseModel):
    """Configuration for a Quest app."""
    name: str
    display_name: str
    description: str

    # News monitoring
    keywords: List[str]
    exclusions: List[str]
    priority_sources: List[str]

    # Content focus
    interests: List[str]
    target_audience: str
    content_tone: str

    # Geographic focus
    geographic_focus: List[str]


# ============================================================================
# APP CONFIGURATIONS
# ============================================================================

PLACEMENT_CONFIG = AppConfig(
    name="placement",
    display_name="Placement Agent Directory",
    description="Directory of placement agents for private equity fund managers",

    keywords=[
        "private equity placement",
        "placement agent",
        "fund placement",
        "capital raising",
        "private equity fundraising",
        "LP commitment",
        "fund distribution",
        "GP stakes",
        "fund formation",
        "institutional investors",
        "limited partner"
    ],

    exclusions=[
        "job placement",
        "staffing agency",
        "recruitment",
        "employment agency",
        "real estate placement",
        "product placement",
        "advertising placement",
        "cryptocurrency",
        "crypto fund",
        "bitcoin",
        "blockchain fund",
        "pornography",
        "adult entertainment",
        "gambling",
        "casino",
        "sports betting"
    ],

    priority_sources=[
        "Private Equity International",
        "PE Hub",
        "PitchBook",
        "Preqin",
        "Buyouts Insider",
        "Private Equity Wire",
        "Institutional Investor",
        "Bloomberg",
        "Reuters"
    ],

    interests=[
        "New fund launches",
        "Placement agent mandates",
        "LP commitments",
        "Fundraising milestones",
        "Team hires at placement agents",
        "New placement agent launches",
        "GP-LP relationships",
        "Fund performance",
        "Market trends in PE fundraising"
    ],

    target_audience="Private equity fund managers, GPs, institutional LPs, placement professionals",
    content_tone="Professional, data-driven, industry insider",

    geographic_focus=["UK", "US", "EU", "Asia"]
)


RELOCATION_CONFIG = AppConfig(
    name="relocation",
    display_name="Global Relocation Directory",
    description="Directory of corporate relocation and global mobility providers",

    keywords=[
        "corporate relocation",
        "employee mobility",
        "global mobility",
        "expat relocation",
        "talent mobility",
        "international assignment",
        "relocation management",
        "destination services",
        "immigration services",
        "assignment management"
    ],

    exclusions=[
        "moving company reviews",
        "DIY moving tips",
        "furniture moving",
        "residential moving",
        "local moving",
        "storage units",
        "packing tips",
        "cryptocurrency",
        "pornography",
        "gambling"
    ],

    priority_sources=[
        "Mobility Magazine",
        "Forum for Expatriate Management",
        "Relocate Global",
        "Re:locate Magazine",
        "Global Mobility News",
        "HR Executive",
        "SHRM",
        "Bloomberg",
        "Reuters"
    ],

    interests=[
        "RMC acquisitions and mergers",
        "New mobility programs",
        "Immigration policy changes",
        "Remote work policies",
        "Hybrid work impact on mobility",
        "Tax and compliance changes",
        "Technology in mobility",
        "Sustainability in relocation",
        "DE&I in global mobility"
    ],

    target_audience="HR leaders, global mobility managers, talent acquisition, relocation professionals",
    content_tone="Practical, compliance-aware, HR-focused",

    geographic_focus=["US", "UK", "EU", "Asia", "Global"]
)


PE_NEWS_CONFIG = AppConfig(
    name="pe_news",
    display_name="PE News Monitor",
    description="Private equity industry news and deal coverage",

    keywords=[
        "private equity",
        "private equity Asia",
        "buyout fund",
        "LBO",
        "private equity exit",
        "PE fundraising",
        "portfolio company acquisition",
        "private equity investment",
        "GP stakes",
        "secondary PE"
    ],

    exclusions=[
        "private equity jobs",
        "private equity career",
        "PE interview tips",
        "how to get into PE",
        "private equity salary",
        "consulting commentary",
        "market outlook predictions",
        "cryptocurrency",
        "crypto fund",
        "bitcoin",
        "pornography",
        "gambling"
    ],

    priority_sources=[
        "Private Equity International",
        "PE Hub",
        "PitchBook",
        "Preqin",
        "Buyouts Insider",
        "Private Equity Wire",
        "Bloomberg",
        "Reuters",
        "Financial Times",
        "Wall Street Journal"
    ],

    interests=[
        "PE deal announcements",
        "Fund closes and launches",
        "Exit transactions",
        "LP commitments",
        "Firm hirings and departures",
        "Regulatory changes",
        "Market trends",
        "Cross-border deals",
        "Sector-specific PE activity"
    ],

    target_audience="Private equity professionals, institutional investors, fund managers, LPs",
    content_tone="News-focused, deal-centric, market intelligence",

    geographic_focus=["UK", "US", "SG"]
)


# ============================================================================
# APP REGISTRY
# ============================================================================

APP_CONFIGS: Dict[str, AppConfig] = {
    "placement": PLACEMENT_CONFIG,
    "relocation": RELOCATION_CONFIG,
    "pe_news": PE_NEWS_CONFIG,
}


def get_app_config(app_name: str) -> AppConfig:
    """Get configuration for an app."""
    if app_name not in APP_CONFIGS:
        raise ValueError(f"Unknown app: {app_name}. Available: {list(APP_CONFIGS.keys())}")
    return APP_CONFIGS[app_name]


def get_all_apps() -> List[str]:
    """Get list of all configured apps."""
    return list(APP_CONFIGS.keys())
