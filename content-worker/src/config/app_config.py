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


class VideoConfig(BaseModel):
    """Video generation configuration."""
    model: str = "seedance-1-pro-fast"  # or "wan-2.5" for high quality
    duration: int = 12  # seconds
    resolution: str = "480p"  # or "720p"
    acts: int = 4  # number of narrative acts
    cost_per_video: float = 0.18  # estimated cost

    # Act timestamps (auto-calculated from duration/acts)
    @property
    def act_duration(self) -> float:
        return self.duration / self.acts

    def get_act_timestamps(self) -> Dict[str, Dict[str, float]]:
        """Get start/mid/end timestamps for each act."""
        act_len = self.act_duration
        return {
            f"act_{i+1}": {
                "start": i * act_len,
                "mid": i * act_len + act_len / 2,
                "end": (i + 1) * act_len
            }
            for i in range(self.acts)
        }


class ThumbnailStrategy(BaseModel):
    """Thumbnail extraction strategy for different uses."""
    # Section headers - one per act (video loops preferred)
    section_headers: List[float] = [1.5, 4.5, 7.5, 10.5]

    # FAQ/callout thumbnails - spread across acts
    supplementary: List[float] = [1.0, 4.0, 7.0, 10.0]

    # Timeline/event thumbnails
    timeline: List[float] = [1.5, 4.5, 7.5, 10.5]

    # Background/translucent images
    backgrounds: List[float] = [10.0, 5.0]


class ComponentLibrary(BaseModel):
    """Available components for article layout."""
    # Which components to include by default
    hero_video: bool = True
    chapter_scrubber: bool = True
    section_video_headers: bool = True  # Video loops vs static thumbnails
    pro_tip_callouts: bool = True
    event_timeline: bool = True
    stat_highlight: bool = True  # "The Bottom Line" section
    comparison_table: bool = True
    faq_grid: bool = True
    cta_video_section: bool = True
    sources_with_thumbnails: bool = True

    # Callout types available
    callout_types: List[str] = ["pro_tip", "warning", "insight", "did_you_know"]


class ArticleTheme(BaseModel):
    """Complete article theme configuration."""
    video: VideoConfig = VideoConfig()
    thumbnails: ThumbnailStrategy = ThumbnailStrategy()
    components: ComponentLibrary = ComponentLibrary()

    # Branding
    brand_name: str = "Relocation Quest"
    brand_position: str = "top-right"  # Where to show brand on thumbnails
    accent_color: str = "amber"  # Tailwind color name

    # Typography
    factoid_style: str = "overlay"  # "overlay" on thumbnail or "below" as separate element


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

    # Media style for images and videos
    media_style: str = "Cinematic, professional, high production value"
    media_style_details: str = ""

    # Article theme and component library
    article_theme: ArticleTheme = ArticleTheme()


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

    geographic_focus=["UK", "US", "EU", "Asia"],

    media_style="Professional corporate cinema",
    media_style_details="""TONE: Confident, sophisticated, deal-making energy.
QUALITY: Cinematic, high production value, premium feel.
LIGHTING: Clean, modern - daylight through glass or warm evening city lights.
PEOPLE: Confident professionals, authentic moments of success and collaboration.
FEEL: Dynamic and forward-looking, not stuffy or stock-photo generic.

Base visuals on the SPECIFIC deal/story - golf deal = golf imagery, tech acquisition = tech setting.
Let the article content drive specifics - this sets the professional MOOD only.""",

    article_theme=ArticleTheme(
        video=VideoConfig(model="seedance-1-pro-fast", duration=12, resolution="480p", acts=4),
        thumbnails=ThumbnailStrategy(
            section_headers=[1.5, 4.5, 7.5, 10.5],
            supplementary=[1.0, 4.0, 7.0, 10.0],
        ),
        components=ComponentLibrary(
            hero_video=True,
            chapter_scrubber=True,
            section_video_headers=True,
            pro_tip_callouts=True,
            event_timeline=True,  # Deal timelines
            stat_highlight=True,
            comparison_table=True,
            faq_grid=True,
            callout_types=["pro_tip", "deal_insight", "market_context", "expert_view"]
        ),
        brand_name="Placement Quest",
        accent_color="blue",
        factoid_style="overlay"
    )
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

    geographic_focus=["US", "UK", "EU", "Asia", "Global"],

    media_style="Aspirational travel and lifestyle photography",
    media_style_details="""TONE: Cinematic, aspirational, emotionally compelling. SELL THE DREAM.
QUALITY: Photorealistic, travel magazine quality, Conde Nast Traveller aesthetic.
LIGHTING: Golden hour warmth, natural light, inviting atmosphere.
PEOPLE: Happy, genuine, relatable - living their best life. Real moments of joy.
FEEL: Make viewers want to experience this place/lifestyle immediately.

IMPORTANT: Base imagery on the SPECIFIC location/topic in the article.
Cyprus article = Cyprus landscapes, Limassol marina, Paphos old town.
Portugal article = Lisbon trams, Porto riverfront, Algarve coast.
Dubai article = Dubai skyline, desert luxury, modern architecture.
Let the article topic drive the specific visuals - this guide sets the MOOD only.""",

    article_theme=ArticleTheme(
        video=VideoConfig(model="seedance-1-pro-fast", duration=12, resolution="480p", acts=4),
        thumbnails=ThumbnailStrategy(
            section_headers=[1.5, 4.5, 7.5, 10.5],
            supplementary=[1.0, 4.0, 7.0, 10.0],
            timeline=[1.5, 4.5, 7.5, 10.5],
            backgrounds=[10.0, 5.0]
        ),
        components=ComponentLibrary(
            hero_video=True,
            chapter_scrubber=True,
            section_video_headers=True,
            pro_tip_callouts=True,
            event_timeline=True,  # Visa program timelines
            stat_highlight=True,  # "The Bottom Line" savings
            comparison_table=True,  # Country comparisons
            faq_grid=True,
            cta_video_section=True,
            sources_with_thumbnails=True,
            callout_types=["pro_tip", "warning", "tax_insight", "lifestyle_tip", "cost_saving"]
        ),
        brand_name="Relocation Quest",
        accent_color="amber",
        factoid_style="overlay"
    )
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

    geographic_focus=["UK", "US", "SG"],

    media_style="Dynamic financial news cinema",
    media_style_details="""TONE: Authoritative, high-energy for deals, analytical for commentary.
QUALITY: Bloomberg/CNBC meets premium documentary - visually striking.
LIGHTING: Modern office daylight or dramatic city night scenes.
PEOPLE: Power players, confident executives, strategic energy.
FEEL: Fast-paced news urgency combined with cinematic polish.

Match imagery to the SPECIFIC story - fund launch = celebration, market downturn = thoughtful.
Can use stylized elements for abstract concepts. Article topic drives specifics.""",

    article_theme=ArticleTheme(
        video=VideoConfig(model="seedance-1-pro-fast", duration=12, resolution="480p", acts=4),
        thumbnails=ThumbnailStrategy(
            section_headers=[1.5, 4.5, 7.5, 10.5],
            supplementary=[1.0, 4.0, 7.0, 10.0],
        ),
        components=ComponentLibrary(
            hero_video=True,
            chapter_scrubber=True,
            section_video_headers=False,  # Static thumbnails for news - faster load
            pro_tip_callouts=True,
            event_timeline=True,  # Deal/market timelines
            stat_highlight=True,
            comparison_table=True,
            faq_grid=False,  # Less relevant for news
            cta_video_section=False,  # News doesn't need CTA
            sources_with_thumbnails=True,
            callout_types=["breaking", "analysis", "market_impact", "expert_quote"]
        ),
        brand_name="PE News",
        accent_color="slate",
        factoid_style="overlay"
    )
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
