"""
App Configurations for Quest

Each app has specific:
- Keywords for news monitoring
- Exclusions (topics to avoid)
- Interests (what to prioritize)
- Geographic focus
- Target audience context

=============================================================================
ARTICLE TYPES (VideoActTemplate.name)
=============================================================================
Sonnet should select the appropriate template based on article topic:

PLACEMENT APP:
- "deal_story" - Deal/transaction story arc (default)
  Use for: Acquisitions, fundraising, exits
  Example: "Apollo Closes $25B Fund VIII"

- "market_analysis" - Industry trends, market overview
  Use for: Industry reports, market overviews
  Example: "Q3 2025 PE Fundraising Report"

- "profile" - Company/firm spotlight
  Use for: Placement agent profiles, GP spotlights
  Example: "Inside Park Hill: How They Dominate PE Placement"

- "deal_summary" - Quick transaction overview
  Use for: Transaction summaries, deal briefs
  Example: "Carlyle's Healthcare Exit: Deal Breakdown"

- "deal_of_week" - Featured transaction spotlight
  Use for: Deal of the Week, notable transactions
  Example: "Deal of the Week: KKR's Infrastructure Play"

- "investment_guide" - Educational content (REQUIRES DISCLAIMER)
  Use for: "How to invest in X", "Understanding Y"
  Example: "Understanding GP Stakes Investing"
  NOTE: Must include InvestmentDisclaimer component prominently!

RELOCATION APP:
- "transformation" - Personal journey from current life to new life
  Use for: Visa guides, moving abroad, lifestyle change articles
  Example: "Cyprus Digital Nomad Visa 2025"

- "country_guide" - Destination showcase
  Use for: Country guides, city guides, "living in X" articles
  Example: "Living in Lisbon: A Complete Guide"

- "comparison" - Side-by-side evaluation
  Use for: "X vs Y" articles, comparison guides
  Example: "Portugal vs Spain: Which is Better for Remote Workers?"

- "listicle" - Multiple highlights
  Use for: "Top X" articles, "Best Y" lists
  Example: "Top 10 Digital Nomad Destinations 2025"

=============================================================================
NEON DATABASE REQUIREMENTS
=============================================================================
For articles to render correctly on the frontend, these fields MUST be populated:

REQUIRED:
- video_playback_id: Mux playback ID for the video
- video_narrative: JSON with acts structure:
  {
    "playback_id": "xxx",
    "acts": {
      "act_1": {"start": 0, "end": 3, "title": "The Grind"},
      "act_2": {"start": 3, "end": 6, "title": "The Dream"},
      "act_3": {"start": 6, "end": 9, "title": "The Journey"},
      "act_4": {"start": 9, "end": 12, "title": "The Reality"}
    }
  }
- payload: JSON with structured content:
  {
    "four_act_content": [
      {"title": "...", "factoid": "...", "video_title": "...", "four_act_visual_hint": "..."},
      ...4 sections
    ],
    "faq": [{"q": "...", "a": "..."}],
    "callouts": [{"type": "pro_tip", "title": "...", "content": "...", "placement": "after_section_2"}],
    "comparison": {"title": "...", "items": [{"name": "Cyprus", "cost": "€800/mo", ...}]},
    "timeline": [{"date": "2022", "title": "...", "description": "..."}],
    "stat_highlight": {"headline": "...", "stats": [{"value": "3,400", "label": "Hours of sunshine"}]},
    "sources": [{"name": "...", "url": "...", "description": "..."}]
  }
- content: HTML article content
- meta_description: SEO excerpt

OPTIONAL:
- article_angle: Category label (e.g., "Relocation Guide", "Visa Guide")
- word_count: Article length

=============================================================================
MUX VIDEO TRICKS
=============================================================================
Mux provides powerful URL-based features:

THUMBNAILS:
  https://image.mux.com/{playback_id}/thumbnail.jpg?time=1.5&width=800

ANIMATED GIFS (bounded loops!):
  https://image.mux.com/{playback_id}/animated.gif?start=0&end=3&width=480&fps=12
  - Max width: 640px (larger fails with "Invalid width")
  - fps: 12-15 recommended
  - start/end: Time range in seconds
  - This is the SECRET to bounded video loops without JavaScript!

STORYBOARD:
  https://image.mux.com/{playback_id}/storyboard.vtt

HLS STREAM:
  https://stream.mux.com/{playback_id}.m3u8

=============================================================================
"""

from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel


# ============================================================================
# ARTICLE MODE - Story vs Guide
# ============================================================================

class ArticleMode(str, Enum):
    """
    Article generation mode.

    STORY: 4-act narrative structure (current default)
        - Emotional journey, cinematic
        - Setup → Opportunity → Journey → Payoff
        - 1500-4000 words
        - Timeline, comparison, FAQ components

    GUIDE: Step-by-step instructional structure (new)
        - Practical, educational
        - Introduction → Steps → Conclusion
        - 800-2000 words
        - Checklist, requirements, cost breakdown components
    """
    STORY = "story"
    GUIDE = "guide"


class CharacterStyle(str, Enum):
    """
    Character demographic options for video generation.

    Organized by region, then gender/group type.
    Dashboard should present as 2-level selector:
    1. Region: None / North European / South European / East Asian / Southeast Asian / South Asian / Middle Eastern / Black / Diverse
    2. Type: Male / Female / Group (if applicable)
    """
    # No people
    NONE = "none"

    # North European (Nordic, British, German, Dutch)
    NORTH_EUROPEAN_MALE = "north_european_male"
    NORTH_EUROPEAN_FEMALE = "north_european_female"
    NORTH_EUROPEAN_GROUP = "north_european_group"

    # South European (Mediterranean - Spanish, Italian, Greek, Portuguese)
    SOUTH_EUROPEAN_MALE = "south_european_male"
    SOUTH_EUROPEAN_FEMALE = "south_european_female"
    SOUTH_EUROPEAN_GROUP = "south_european_group"

    # East Asian (Chinese, Japanese, Korean)
    EAST_ASIAN_MALE = "east_asian_male"
    EAST_ASIAN_FEMALE = "east_asian_female"
    EAST_ASIAN_GROUP = "east_asian_group"

    # Southeast Asian (Singaporean, Thai, Vietnamese, Filipino, Indonesian, Malaysian)
    SOUTHEAST_ASIAN_MALE = "southeast_asian_male"
    SOUTHEAST_ASIAN_FEMALE = "southeast_asian_female"
    SOUTHEAST_ASIAN_GROUP = "southeast_asian_group"

    # South Asian (Indian, Pakistani, Bangladeshi, Sri Lankan)
    SOUTH_ASIAN_MALE = "south_asian_male"
    SOUTH_ASIAN_FEMALE = "south_asian_female"
    SOUTH_ASIAN_GROUP = "south_asian_group"

    # Middle Eastern / Arab (UAE, Saudi, Qatari, etc.)
    MIDDLE_EASTERN_MALE = "middle_eastern_male"
    MIDDLE_EASTERN_FEMALE = "middle_eastern_female"
    MIDDLE_EASTERN_GROUP = "middle_eastern_group"

    # Black (African, Caribbean, African-American)
    BLACK_MALE = "black_male"
    BLACK_FEMALE = "black_female"
    BLACK_GROUP = "black_group"

    # Diverse (mixed ethnicity and gender)
    DIVERSE = "diverse"


# Prompt text for each character style (injected into video prompts)
# Keep prompts concise to stay within 2000 char limit
CHARACTER_STYLE_PROMPTS: Dict[CharacterStyle, str] = {
    # No people
    CharacterStyle.NONE: "No people. Abstract visuals, architecture, cityscapes only.",

    # North European
    CharacterStyle.NORTH_EUROPEAN_MALE: "Main character: North European man.",
    CharacterStyle.NORTH_EUROPEAN_FEMALE: "Main character: North European woman.",
    CharacterStyle.NORTH_EUROPEAN_GROUP: "Cast: North European professionals, mixed gender.",

    # South European
    CharacterStyle.SOUTH_EUROPEAN_MALE: "Main character: Southern European man (Mediterranean).",
    CharacterStyle.SOUTH_EUROPEAN_FEMALE: "Main character: Southern European woman (Mediterranean).",
    CharacterStyle.SOUTH_EUROPEAN_GROUP: "Cast: Southern European professionals, mixed gender.",

    # East Asian
    CharacterStyle.EAST_ASIAN_MALE: "Main character: East Asian man.",
    CharacterStyle.EAST_ASIAN_FEMALE: "Main character: East Asian woman.",
    CharacterStyle.EAST_ASIAN_GROUP: "Cast: East Asian professionals, mixed gender.",

    # Southeast Asian
    CharacterStyle.SOUTHEAST_ASIAN_MALE: "Main character: Southeast Asian man.",
    CharacterStyle.SOUTHEAST_ASIAN_FEMALE: "Main character: Southeast Asian woman.",
    CharacterStyle.SOUTHEAST_ASIAN_GROUP: "Cast: Southeast Asian professionals, mixed gender.",

    # South Asian
    CharacterStyle.SOUTH_ASIAN_MALE: "Main character: South Asian man.",
    CharacterStyle.SOUTH_ASIAN_FEMALE: "Main character: South Asian woman.",
    CharacterStyle.SOUTH_ASIAN_GROUP: "Cast: South Asian professionals, mixed gender.",

    # Middle Eastern
    CharacterStyle.MIDDLE_EASTERN_MALE: "Main character: Middle Eastern/Arab man.",
    CharacterStyle.MIDDLE_EASTERN_FEMALE: "Main character: Middle Eastern/Arab woman.",
    CharacterStyle.MIDDLE_EASTERN_GROUP: "Cast: Middle Eastern/Arab professionals, mixed gender.",

    # Black
    CharacterStyle.BLACK_MALE: "Main character: Black man.",
    CharacterStyle.BLACK_FEMALE: "Main character: Black woman.",
    CharacterStyle.BLACK_GROUP: "Cast: Black professionals, mixed gender.",

    # Diverse
    CharacterStyle.DIVERSE: "Cast: diverse international professionals, mixed ethnicity and gender.",
}


class VideoConfig(BaseModel):
    """Video generation configuration."""
    model: str = "seedance-1-pro-fast"  # or "wan-2.5" for high quality
    duration: int = 12  # seconds
    resolution: str = "720p"  # upgraded from 480p
    acts: int = 4  # number of narrative acts
    cost_per_video: float = 0.30  # estimated cost (720p is ~$0.025/sec)

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


class VideoActTemplate(BaseModel):
    """Single 4-act video template - one story type."""
    name: str  # e.g., "transformation", "deal_story", "comparison"
    description: str = ""  # When to use this template

    act_1_role: str
    act_1_mood: str
    act_1_example: str = ""

    act_2_role: str
    act_2_mood: str
    act_2_example: str = ""

    act_3_role: str
    act_3_mood: str
    act_3_example: str = ""

    act_4_role: str
    act_4_mood: str
    act_4_example: str = ""


# ============================================================================
# GUIDE MODE TEMPLATES
# ============================================================================

class GuideStep(BaseModel):
    """Single step in a guide template."""
    name: str  # e.g., "Requirements", "Application Process", "Timeline"
    description: str = ""  # What this step covers
    visual_hint: str = ""  # Visual style for this step's thumbnail


class GuideTemplate(BaseModel):
    """
    Guide article template - step-by-step instructional structure.

    Unlike story mode (4-act narrative), guide mode uses:
    - Introduction (what you'll learn)
    - Numbered steps (practical how-to)
    - Conclusion (next steps / summary)

    Components: checklist, requirements box, cost breakdown, timeline, FAQ
    """
    name: str  # e.g., "visa_guide", "process_guide"
    description: str = ""  # When to use this template

    # Section structure
    intro_role: str = "What you'll learn and who this is for"
    steps: List[GuideStep] = []  # The actual steps (3-6 typical)
    conclusion_role: str = "Next steps and key takeaways"

    # Tone and voice
    voice: str = "Direct, practical, authoritative"

    # Components to include (frontend renders these)
    include_checklist: bool = True
    include_requirements_box: bool = True
    include_cost_breakdown: bool = True
    include_timeline: bool = True
    include_faq: bool = True

    # Video style (guides use process demonstration style)
    video_style: str = "Educational, step-by-step demonstration"


class GuideConfig(BaseModel):
    """
    Collection of guide templates for an app.

    Similar to VideoPromptTemplate but for guide-mode articles.
    """
    templates: List[GuideTemplate] = []
    default_template: str = ""

    # Global guide style
    no_text_rule: str = "CRITICAL: NO text, words, letters, numbers on screens, documents, or anywhere."
    technical_notes: str = "Clean, professional aesthetic. Educational documentary style."

    def get_template(self, name: str = None) -> Optional[GuideTemplate]:
        """Get a template by name, or default."""
        target = name or self.default_template
        for t in self.templates:
            if t.name == target:
                return t
        return self.templates[0] if self.templates else None

    def get_template_names(self) -> List[str]:
        """Get all available template names."""
        return [t.name for t in self.templates]


class VideoPromptTemplate(BaseModel):
    """
    Collection of 4-act video templates for an app.

    Sonnet picks the best template OR creates its own if none fit.
    The ONLY requirement is 4 acts - themes are flexible.
    """
    # Multiple templates - add more over time
    templates: List[VideoActTemplate] = []

    # Default template used when no specific match
    default_template: str = "transformation"  # Name of template to use as fallback

    # Global constraints (apply to ALL templates)
    no_text_rule: str = "CRITICAL: NO text, words, letters, numbers, signs, logos anywhere. Screens show abstract colors only."
    technical_notes: str = "Smooth transitions, cinematic color grading, natural motion."

    def get_template(self, name: str = None) -> Optional[VideoActTemplate]:
        """Get a template by name, or default."""
        target = name or self.default_template
        for t in self.templates:
            if t.name == target:
                return t
        return self.templates[0] if self.templates else None

    def get_template_names(self) -> List[str]:
        """Get all available template names."""
        return [t.name for t in self.templates]


# Legacy support - single template format
class VideoPromptTemplateLegacy(BaseModel):
    """4-act video prompt template for an app (legacy single-template format)."""
    act_1_role: str = "THE SETUP - Problem/current situation/pain point"
    act_1_mood: str = "Tension, confinement, challenge"
    act_1_example: str = ""

    act_2_role: str = "THE OPPORTUNITY - Discovery/revelation/hope"
    act_2_mood: str = "Hope, possibility, curiosity"
    act_2_example: str = ""

    act_3_role: str = "THE JOURNEY - Process/action/transition"
    act_3_mood: str = "Movement, progress, anticipation"
    act_3_example: str = ""

    act_4_role: str = "THE PAYOFF - Resolution/success/new reality"
    act_4_mood: str = "Joy, freedom, satisfaction"
    act_4_example: str = ""

    no_text_rule: str = "CRITICAL: NO text, words, letters, numbers, signs, logos anywhere. Screens show abstract colors only."
    technical_notes: str = "Smooth transitions, cinematic color grading, natural motion."


class ArticleTheme(BaseModel):
    """Complete article theme configuration."""
    video: VideoConfig = VideoConfig()
    thumbnails: ThumbnailStrategy = ThumbnailStrategy()
    components: ComponentLibrary = ComponentLibrary()
    video_prompt_template: VideoPromptTemplate = VideoPromptTemplate()

    # Guide mode configuration (optional - for guide-mode articles)
    guide_config: Optional[GuideConfig] = None

    # Default article mode for this app
    default_article_mode: ArticleMode = ArticleMode.STORY

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

    # Character style for video generation (default demographic)
    # Can be overridden per-article via payload
    character_style: CharacterStyle = CharacterStyle.DIVERSE

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

    # Financial/deal stories: no people by default (abstract visuals)
    character_style=CharacterStyle.NONE,

    article_theme=ArticleTheme(
        video=VideoConfig(model="seedance-1-pro-fast", duration=12, resolution="720p", acts=4),
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
        video_prompt_template=VideoPromptTemplate(
            default_template="deal_story",
            no_text_rule="CRITICAL: NO text, words, letters, numbers on screens, documents, or anywhere. All screens show abstract data visuals only.",
            technical_notes="Clean corporate aesthetic. Teal-and-orange color grade. Dynamic camera movement.",
            templates=[
                # DEAL STORY - Classic PE deal narrative
                VideoActTemplate(
                    name="deal_story",
                    description="Deal/transaction story arc. Use for acquisitions, fundraising, exits.",
                    act_1_role="THE CHALLENGE - Market pressure/fundraising need/competitive landscape",
                    act_1_mood="Stakes, tension, boardroom energy",
                    act_1_example="Executive reviewing documents, city skyline at dusk, serious expressions, glass offices",
                    act_2_role="THE STRATEGY - Solution/approach/partnership forming",
                    act_2_mood="Strategic thinking, collaboration, confidence building",
                    act_2_example="Meeting room handshake, charts on screen (abstract, no text), deal team discussion",
                    act_3_role="THE EXECUTION - Deal in motion/roadshow/negotiations",
                    act_3_mood="Action, momentum, progress",
                    act_3_example="Fast-paced office scenes, travel montage, signing moments, champagne being poured",
                    act_4_role="THE CLOSE - Success/celebration/new chapter",
                    act_4_mood="Achievement, celebration, forward-looking",
                    act_4_example="Team celebration, city lights at night, confident executives, success atmosphere"
                ),
                # MARKET ANALYSIS - Industry trends, market overview
                VideoActTemplate(
                    name="market_analysis",
                    description="Market trends and analysis. Use for industry reports, market overviews.",
                    act_1_role="THE LANDSCAPE - Current market state",
                    act_1_mood="Analytical, establishing context",
                    act_1_example="Financial district establishing shots, market activity, trading floor energy",
                    act_2_role="THE TRENDS - Key movements/patterns",
                    act_2_mood="Discovery, insight",
                    act_2_example="Abstract data visualizations, movement patterns, growth indicators",
                    act_3_role="THE PLAYERS - Who's winning/losing",
                    act_3_mood="Competition, positioning",
                    act_3_example="Different firms/approaches, contrasting styles, market dynamics",
                    act_4_role="THE OUTLOOK - Where it's heading",
                    act_4_mood="Forward-looking, opportunity",
                    act_4_example="Dawn over financial district, new opportunities, future focus"
                ),
                # PROFILE - Company/firm spotlight
                VideoActTemplate(
                    name="profile",
                    description="Company or firm profile. Use for placement agent profiles, GP spotlights.",
                    act_1_role="THE INTRODUCTION - Who they are",
                    act_1_mood="Authority, establishment",
                    act_1_example="Headquarters exterior, confident team, professional setting",
                    act_2_role="THE TRACK RECORD - What they've done",
                    act_2_mood="Credibility, achievement",
                    act_2_example="Deal celebration moments, successful outcomes, growth story",
                    act_3_role="THE APPROACH - How they work",
                    act_3_mood="Methodology, differentiation",
                    act_3_example="Team collaboration, client meetings, strategic discussions",
                    act_4_role="THE FUTURE - Where they're going",
                    act_4_mood="Ambition, forward momentum",
                    act_4_example="Expansion hints, new opportunities, confident outlook"
                ),
                # DEAL SUMMARY - Quick transaction overview
                VideoActTemplate(
                    name="deal_summary",
                    description="Quick deal overview. Use for transaction summaries, deal briefs.",
                    act_1_role="THE HEADLINE - Key transaction facts",
                    act_1_mood="Immediate impact, news flash",
                    act_1_example="Deal signing moment, boardroom celebration, handshake",
                    act_2_role="THE PLAYERS - Who's involved",
                    act_2_mood="Credibility, relationships",
                    act_2_example="Firm logos (abstract), team profiles, partnership energy",
                    act_3_role="THE TERMS - Structure highlights",
                    act_3_mood="Analytical, substantial",
                    act_3_example="Abstract deal visualization, value flow, strategic positioning",
                    act_4_role="THE SIGNIFICANCE - Why it matters",
                    act_4_mood="Market impact, forward-looking",
                    act_4_example="Wider market context, ripple effects, industry implications"
                ),
                # DEAL OF THE WEEK - Featured transaction spotlight
                VideoActTemplate(
                    name="deal_of_week",
                    description="Featured transaction spotlight. Use for Deal of the Week, notable transactions.",
                    act_1_role="THE SPOTLIGHT - Why this deal stands out",
                    act_1_mood="Premium, notable, exceptional",
                    act_1_example="Dramatic reveal, spotlight effect, prestigious setting",
                    act_2_role="THE BACKSTORY - How it came together",
                    act_2_mood="Narrative, journey, buildup",
                    act_2_example="Timeline montage, relationship building, strategic moments",
                    act_3_role="THE EXECUTION - How it got done",
                    act_3_mood="Precision, expertise, deal-making",
                    act_3_example="Negotiation energy, late nights, champagne preparation",
                    act_4_role="THE IMPACT - What it means for the market?",
                    act_4_mood="Significance, trendsetting, question mark",
                    act_4_example="Market reaction, industry watching, future implications"
                ),
                # INVESTMENT GUIDE - Educational content (REQUIRES DISCLAIMER)
                VideoActTemplate(
                    name="investment_guide",
                    description="Educational investment content. REQUIRES prominent disclaimer. Use for 'How to invest in X', 'Understanding Y investment'.",
                    act_1_role="THE LANDSCAPE - Market overview/opportunity",
                    act_1_mood="Educational, context-setting",
                    act_1_example="Market overview shots, financial district, analytical setting",
                    act_2_role="THE MECHANICS - How it works",
                    act_2_mood="Explanatory, clear, trustworthy",
                    act_2_example="Process visualization, abstract flow diagrams, step demonstration",
                    act_3_role="THE CONSIDERATIONS - Risks and factors",
                    act_3_mood="Balanced, thoughtful, risk-aware",
                    act_3_example="Scales balancing, thoughtful analysis, careful evaluation",
                    act_4_role="THE PERSPECTIVE - Market outlook?",
                    act_4_mood="Forward-looking with uncertainty acknowledged",
                    act_4_example="Horizon view, question marks, multiple paths forward"
                )
            ]
        ),
        # GUIDE MODE TEMPLATES (educational/process content)
        guide_config=GuideConfig(
            default_template="process_guide",
            no_text_rule="CRITICAL: NO text, numbers on screens. Abstract corporate visuals only.",
            technical_notes="Clean corporate aesthetic. Professional, authoritative tone.",
            templates=[
                # PROCESS GUIDE - How placement agents work
                GuideTemplate(
                    name="process_guide",
                    description="How placement agents work. Use for 'How to work with a placement agent' articles.",
                    intro_role="What placement agents do and why you need one",
                    steps=[
                        GuideStep(
                            name="Selecting an Agent",
                            description="What to look for and how to evaluate",
                            visual_hint="Conference table meeting, portfolio review, handshake"
                        ),
                        GuideStep(
                            name="The Engagement",
                            description="Terms, fees, and what to expect",
                            visual_hint="Document signing, strategy discussion, whiteboard planning"
                        ),
                        GuideStep(
                            name="The Roadshow",
                            description="LP meetings, pitches, and timeline",
                            visual_hint="Travel montage, presentation room, investor meetings"
                        ),
                        GuideStep(
                            name="Closing & Beyond",
                            description="Deal completion and ongoing relationship",
                            visual_hint="Celebration, champagne, successful outcomes"
                        )
                    ],
                    conclusion_role="Key success factors and next steps",
                    voice="Professional, strategic, insider",
                    include_checklist=True,
                    include_requirements_box=False,
                    include_cost_breakdown=False,
                    include_timeline=True,
                    include_faq=True,
                    video_style="Corporate documentary, professional aesthetic"
                ),
                # DUE DILIGENCE GUIDE - LP evaluation framework
                GuideTemplate(
                    name="due_diligence_guide",
                    description="LP due diligence framework. Use for 'How to evaluate X' articles.",
                    intro_role="Why due diligence matters and what to assess",
                    steps=[
                        GuideStep(
                            name="Track Record Analysis",
                            description="Evaluating historical performance",
                            visual_hint="Data analysis, charts on screens (abstract), research"
                        ),
                        GuideStep(
                            name="Team Assessment",
                            description="Key person risk and team dynamics",
                            visual_hint="Team introductions, meeting room, professional profiles"
                        ),
                        GuideStep(
                            name="Strategy Review",
                            description="Investment thesis and market positioning",
                            visual_hint="Strategy presentation, market analysis, competitive view"
                        ),
                        GuideStep(
                            name="Terms & Documentation",
                            description="LPA review and fee analysis",
                            visual_hint="Document review, legal consultation, negotiation"
                        )
                    ],
                    conclusion_role="Red flags to watch and decision framework",
                    voice="Analytical, thorough, risk-aware",
                    include_checklist=True,
                    include_requirements_box=True,
                    include_cost_breakdown=False,
                    include_timeline=False,
                    include_faq=True,
                    video_style="Professional documentary, analytical tone"
                )
            ]
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

    # Relocation/lifestyle: diverse by default (Sonnet infers from article context)
    character_style=CharacterStyle.DIVERSE,

    article_theme=ArticleTheme(
        video=VideoConfig(model="seedance-1-pro-fast", duration=12, resolution="720p", acts=4),
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
        video_prompt_template=VideoPromptTemplate(
            default_template="transformation",
            no_text_rule="CRITICAL: NO text, words, letters, signs, logos anywhere. Screens show abstract colors. No airport signs. No country names written.",
            technical_notes="High contrast grey-to-golden transition. Cinematic travel documentary style. Natural motion.",
            templates=[
                # TRANSFORMATION - Personal journey stories (visa guides, moving abroad)
                VideoActTemplate(
                    name="transformation",
                    description="Personal journey from current situation to new life. Use for visa guides, moving abroad, lifestyle change articles.",
                    act_1_role="THE GRIND - Current life frustration/limitation",
                    act_1_mood="Exhaustion, confinement, grey tones",
                    act_1_example="Dark office, rain on windows, tired professional at desk, cold lighting, urban grey",
                    act_2_role="THE DREAM - Discovery of opportunity/possibility",
                    act_2_mood="Hope, warm light emerging, expression change",
                    act_2_example="Same person at home, warm lamplight, looking at screen with hope, smile emerging",
                    act_3_role="THE JOURNEY - Travel/transition/process",
                    act_3_mood="Movement, anticipation, colors shifting warm",
                    act_3_example="Packing, airport glimpses (no text), airplane window, destination coastline",
                    act_4_role="THE NEW LIFE - Settled happiness/success",
                    act_4_mood="Golden hour, joy, belonging, freedom",
                    act_4_example="Sunset terrace, local lifestyle, friends, genuine happiness, laptop closed"
                ),
                # COMPARISON - Side-by-side evaluation (country vs country, visa vs visa)
                VideoActTemplate(
                    name="comparison",
                    description="Comparing options side by side. Use for 'X vs Y' articles, comparison guides.",
                    act_1_role="THE QUESTION - Presenting the choice/dilemma",
                    act_1_mood="Curiosity, weighing options",
                    act_1_example="Person looking at map, globe spinning, two paths visible",
                    act_2_role="OPTION A - First choice highlights",
                    act_2_mood="Showcasing strengths, distinctive features",
                    act_2_example="First destination montage - iconic landmarks, lifestyle moments",
                    act_3_role="OPTION B - Second choice highlights",
                    act_3_mood="Contrasting qualities, different appeal",
                    act_3_example="Second destination montage - different aesthetic, unique character",
                    act_4_role="THE CLARITY - Decision made/path forward",
                    act_4_mood="Resolution, confidence, chosen path",
                    act_4_example="Person confidently moving forward, happy in chosen setting"
                ),
                # COUNTRY GUIDE - Destination showcase
                VideoActTemplate(
                    name="country_guide",
                    description="Showcasing a destination. Use for country guides, city guides, 'living in X' articles.",
                    act_1_role="THE ARRIVAL - First impressions/iconic entry",
                    act_1_mood="Wonder, discovery, excitement",
                    act_1_example="Airplane window view, first glimpse of coastline/skyline, stepping into new world",
                    act_2_role="THE CULTURE - Local life/people/traditions",
                    act_2_mood="Warmth, authenticity, connection",
                    act_2_example="Local markets, cafes, friendly faces, cultural moments",
                    act_3_role="THE LIFESTYLE - Daily experience/practical beauty",
                    act_3_mood="Livability, comfort, quality of life",
                    act_3_example="Coworking spaces, beaches, neighborhoods, daily routines",
                    act_4_role="THE BELONGING - Settled/home feeling",
                    act_4_mood="Contentment, this is home now",
                    act_4_example="Sunset with friends, rooftop views, genuine belonging"
                ),
                # LISTICLE - Multiple highlights (Top 10 X, Best Y)
                VideoActTemplate(
                    name="listicle",
                    description="Showcasing multiple items/options. Use for 'Top X' articles, 'Best Y' lists.",
                    act_1_role="THE OVERVIEW - Setting up the list premise",
                    act_1_mood="Anticipation, variety promised",
                    act_1_example="Wide establishing shot, multiple options hinted",
                    act_2_role="HIGHLIGHTS A - First batch of standouts",
                    act_2_mood="Excitement, quality showcased",
                    act_2_example="Quick cuts of first few highlights, distinctive features",
                    act_3_role="HIGHLIGHTS B - More discoveries",
                    act_3_mood="Continued discovery, variety",
                    act_3_example="More highlights, different styles, broader appeal",
                    act_4_role="THE BEST - Culmination/top picks",
                    act_4_mood="Pinnacle, best of the best",
                    act_4_example="Most impressive moments, final flourish"
                )
            ]
        ),
        # GUIDE MODE TEMPLATES (step-by-step instructional content)
        guide_config=GuideConfig(
            default_template="visa_guide",
            no_text_rule="CRITICAL: NO text, words, letters on screens. Abstract visuals only.",
            technical_notes="Clean, educational style. Documentary aesthetic with warm golden tones.",
            templates=[
                # VISA GUIDE - Step-by-step visa application process
                GuideTemplate(
                    name="visa_guide",
                    description="Step-by-step visa application guide. Use for 'How to get X visa' articles.",
                    intro_role="Who this visa is for and what you'll learn",
                    steps=[
                        GuideStep(
                            name="Eligibility & Requirements",
                            description="Who qualifies and what documents you need",
                            visual_hint="Clean desk with documents, laptop showing forms (no text), organized preparation"
                        ),
                        GuideStep(
                            name="Application Process",
                            description="Step-by-step submission walkthrough",
                            visual_hint="Hand completing forms (no visible text), embassy building exterior, waiting room"
                        ),
                        GuideStep(
                            name="Timeline & Costs",
                            description="Processing times, fees, and what to expect",
                            visual_hint="Calendar pages flipping, coins stacking, clock hands moving slowly"
                        ),
                        GuideStep(
                            name="After Approval",
                            description="What happens next and settling in",
                            visual_hint="Passport stamp close-up (blurred), airplane window, arrival at destination"
                        )
                    ],
                    conclusion_role="Key takeaways and next steps for your move",
                    voice="Practical, reassuring, authoritative",
                    include_checklist=True,
                    include_requirements_box=True,
                    include_cost_breakdown=True,
                    include_timeline=True,
                    include_faq=True,
                    video_style="Educational documentary, warm tones, process demonstration"
                ),
                # COST GUIDE - Breakdown of living costs
                GuideTemplate(
                    name="cost_guide",
                    description="Cost of living breakdown. Use for 'Cost of living in X' articles.",
                    intro_role="Overview of expenses and who this guide is for",
                    steps=[
                        GuideStep(
                            name="Housing Costs",
                            description="Rent, utilities, neighborhoods",
                            visual_hint="Apartment exterior, living room interior, neighborhood streets"
                        ),
                        GuideStep(
                            name="Daily Living",
                            description="Food, transport, entertainment",
                            visual_hint="Local market produce, cafe scenes, public transport"
                        ),
                        GuideStep(
                            name="Healthcare & Insurance",
                            description="Medical costs and coverage options",
                            visual_hint="Modern hospital exterior, pharmacy, doctor consultation"
                        ),
                        GuideStep(
                            name="Budget Comparison",
                            description="How it compares to your current location",
                            visual_hint="Split screen city comparison, lifestyle montage, savings jar filling"
                        )
                    ],
                    conclusion_role="Monthly budget summary and money-saving tips",
                    voice="Honest, practical, data-driven",
                    include_checklist=False,
                    include_requirements_box=False,
                    include_cost_breakdown=True,
                    include_timeline=False,
                    include_faq=True,
                    video_style="Lifestyle documentary, warm Mediterranean/destination tones"
                ),
                # MOVING GUIDE - Practical relocation steps
                GuideTemplate(
                    name="moving_guide",
                    description="Complete moving checklist. Use for 'How to move to X' articles.",
                    intro_role="Your roadmap from decision to arrival",
                    steps=[
                        GuideStep(
                            name="Planning Your Move",
                            description="Timeline, visa selection, financial prep",
                            visual_hint="Person at desk with laptop, calendar view, planning materials"
                        ),
                        GuideStep(
                            name="Before You Go",
                            description="Documents, banking, housing search",
                            visual_hint="Packing boxes, document folder, video call with realtor"
                        ),
                        GuideStep(
                            name="The Move",
                            description="Shipping belongings, travel, first days",
                            visual_hint="Moving truck, airport departure, taxi through new city"
                        ),
                        GuideStep(
                            name="Settling In",
                            description="Registration, bank account, building routines",
                            visual_hint="Unpacking in new apartment, exploring neighborhood, cafe with laptop"
                        )
                    ],
                    conclusion_role="Your first month checklist and resources",
                    voice="Supportive, organized, reassuring",
                    include_checklist=True,
                    include_requirements_box=True,
                    include_cost_breakdown=True,
                    include_timeline=True,
                    include_faq=True,
                    video_style="Journey documentary, grey-to-golden transition"
                )
            ]
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

    # PE News: no people by default (abstract financial visuals)
    character_style=CharacterStyle.NONE,

    article_theme=ArticleTheme(
        video=VideoConfig(model="seedance-1-pro-fast", duration=12, resolution="720p", acts=4),
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
        video_prompt_template=VideoPromptTemplate(
            default_template="news_story",
            no_text_rule="CRITICAL: NO text, tickers, headlines, numbers. News aesthetic without actual readable content. Abstract data visuals only.",
            technical_notes="Bloomberg/CNBC documentary feel. Fast cuts for urgency. Cool blue tones with warm accents.",
            templates=[
                # NEWS STORY - Breaking news/announcements (default)
                VideoActTemplate(
                    name="news_story",
                    description="Breaking news or announcements. Use for deal announcements, fund launches, exits.",
                    act_1_role="THE NEWS - Breaking development/announcement",
                    act_1_mood="Urgency, importance, high stakes",
                    act_1_example="News ticker aesthetic (no text), city financial district, busy trading floor energy",
                    act_2_role="THE CONTEXT - Background/what led to this",
                    act_2_mood="Analytical, historical perspective",
                    act_2_example="Archive footage feel, previous deal montage, market chart movements (abstract)",
                    act_3_role="THE IMPACT - Market reaction/implications",
                    act_3_mood="Ripple effects, analysis, assessment",
                    act_3_example="Multiple screens showing abstract data, analysts in discussion, market activity",
                    act_4_role="THE OUTLOOK - What's next/future implications",
                    act_4_mood="Forward-looking, strategic, opportunity",
                    act_4_example="Dawn over financial district, new day metaphor, forward momentum"
                ),
                # DEAL COVERAGE - Specific transaction deep dive
                VideoActTemplate(
                    name="deal_coverage",
                    description="Detailed deal/transaction coverage. Use for acquisition analysis, LBO breakdowns.",
                    act_1_role="THE DEAL - Transaction announcement/structure",
                    act_1_mood="Big moment, significance",
                    act_1_example="Boardroom signing, handshake, celebratory atmosphere",
                    act_2_role="THE PARTIES - Players involved/backgrounds",
                    act_2_mood="Profile, credibility",
                    act_2_example="Firm headquarters, team shots, track record hints",
                    act_3_role="THE STRATEGY - Why this deal/rationale",
                    act_3_mood="Analytical, strategic logic",
                    act_3_example="Strategy discussions, market positioning visuals",
                    act_4_role="THE IMPLICATIONS - Market impact/what it means",
                    act_4_mood="Ripple effects, industry context",
                    act_4_example="Wider market scenes, future growth hints"
                ),
                # ANALYSIS - Market commentary/trends
                VideoActTemplate(
                    name="analysis",
                    description="Market analysis or commentary. Use for trend pieces, quarterly reviews.",
                    act_1_role="THE THESIS - Key insight/argument",
                    act_1_mood="Authority, clarity",
                    act_1_example="Expert at desk, confident posture, analytical setting",
                    act_2_role="THE EVIDENCE - Supporting data/trends",
                    act_2_mood="Data-driven, proof",
                    act_2_example="Abstract data visualizations, charts (no text), pattern reveals",
                    act_3_role="THE COUNTERPOINT - Challenges/risks/alternative views",
                    act_3_mood="Balance, nuance",
                    act_3_example="Different perspectives, contrasting scenes, tension",
                    act_4_role="THE CONCLUSION - Takeaway/recommendation",
                    act_4_mood="Clarity, actionable insight",
                    act_4_example="Resolution, clear path forward, confident outlook"
                )
            ]
        ),
        # GUIDE MODE TEMPLATES (educational/explainer content)
        guide_config=GuideConfig(
            default_template="deal_explainer",
            no_text_rule="CRITICAL: NO text, numbers, tickers. Abstract financial visuals only.",
            technical_notes="Bloomberg documentary style. Clean, professional, analytical aesthetic.",
            templates=[
                # DEAL EXPLAINER - Breaking down a transaction
                GuideTemplate(
                    name="deal_explainer",
                    description="Deal breakdown and analysis. Use for 'How X deal works' articles.",
                    intro_role="Deal overview and why it matters",
                    steps=[
                        GuideStep(
                            name="The Transaction",
                            description="Deal structure, size, and parties involved",
                            visual_hint="Boardroom view, handshake, deal celebration"
                        ),
                        GuideStep(
                            name="The Rationale",
                            description="Strategic logic and investment thesis",
                            visual_hint="Strategy meeting, analysts at screens, market data"
                        ),
                        GuideStep(
                            name="The Structure",
                            description="Financing, terms, and mechanics",
                            visual_hint="Abstract flow diagrams, building blocks, arrows"
                        ),
                        GuideStep(
                            name="The Implications",
                            description="Market impact and what to watch",
                            visual_hint="Wider market view, ripple effect visuals, forward momentum"
                        )
                    ],
                    conclusion_role="Key takeaways for market participants",
                    voice="Analytical, authoritative, market-savvy",
                    include_checklist=False,
                    include_requirements_box=False,
                    include_cost_breakdown=False,
                    include_timeline=True,
                    include_faq=True,
                    video_style="Financial documentary, Bloomberg aesthetic"
                ),
                # MARKET GUIDE - Understanding a sector/trend
                GuideTemplate(
                    name="market_guide",
                    description="Sector or market analysis framework. Use for 'Understanding X market' articles.",
                    intro_role="Market landscape and key dynamics",
                    steps=[
                        GuideStep(
                            name="Market Overview",
                            description="Size, growth, and key players",
                            visual_hint="Market montage, industry leaders, growth indicators"
                        ),
                        GuideStep(
                            name="Key Drivers",
                            description="What's moving the market",
                            visual_hint="Trend arrows, catalyst moments, momentum"
                        ),
                        GuideStep(
                            name="Competitive Landscape",
                            description="Major players and positioning",
                            visual_hint="Chess pieces, strategic positioning, competition"
                        ),
                        GuideStep(
                            name="Outlook",
                            description="Opportunities and risks ahead",
                            visual_hint="Dawn over city, forward view, opportunity signals"
                        )
                    ],
                    conclusion_role="Investment implications and key metrics to watch",
                    voice="Strategic, data-informed, forward-looking",
                    include_checklist=False,
                    include_requirements_box=False,
                    include_cost_breakdown=False,
                    include_timeline=False,
                    include_faq=True,
                    video_style="Market documentary, analytical tone"
                )
            ]
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
