# Restart Prompt: Article-First 4-Act Video Integration

## Context Summary
Built complete **Article-First Video Workflow** with Seedance 4-act videos ($0.18 vs $1.00). Article is written FIRST, then video prompt generated from actual section angles. No more generic video prompts.

## Architecture Decision: ADAPT existing workflow

**Recommendation**: Adapt `ArticleCreationWorkflow` rather than create new workflow.
- Remove image prompt generation (no longer needed)
- Add new activity: `generate_video_prompt_from_article()` AFTER article generation
- Keep existing research, article gen, Mux upload activities

```
WORKFLOW ORDER:
1. Research (Exa/Serper) → curated sources
2. Article Generation → 4 sections with factoids, external links
3. NEW: Generate Video Prompt → extract visual descriptions from sections
4. Video Generation → Seedance 4-act (12s, 480p)
5. Mux Upload → get playback_id
6. Save to Neon → article + video_narrative JSON
```

## Critical Fix: External Links Regression

**Priority**: Fix before resuming schedules

Investigate commits around Nov 25:
- `8e48927 fix: enforce source links in article generation`
- `c24e5eb feat: consolidated URL list for article citations`
- `1f9f0cd fix: graceful fail for Phase 5b link validation`

Articles before Nov 25 had links, after Nov 25 mostly don't.

---

## What Was Built

### 1. Seedance Video Generation
- **Model**: `bytedance/seedance-1-pro-fast` via Replicate
- **Duration**: 12 seconds (4 acts × 3 seconds)
- **Resolution**: 480p
- **Cost**: $0.18 per video (82% savings)
- **NO TEXT**: Enforced in prompt

### 2. Component Library (`src/config/app_config.py`)
```python
ArticleTheme
├── VideoConfig (model="seedance-1-pro-fast", duration=12, acts=4)
├── ThumbnailStrategy (section_headers, supplementary, timeline, backgrounds)
├── ComponentLibrary (hero_video, chapter_scrubber, section_video_headers, etc.)
├── brand_name, accent_color, factoid_style
```

### 3. Per-App Customization
| App | Brand | Accent | Style |
|-----|-------|--------|-------|
| relocation | Relocation Quest | amber | Aspirational travel, golden hour |
| placement | Placement Quest | blue | Corporate cinema, deal energy |
| pe_news | PE News | slate | Bloomberg meets documentary |

---

## Video Prompt Strategy

### Hybrid Approach (Config + Article Content)

**From Config** (`media_style_details`):
- Overall tone and mood
- Lighting style
- People/aesthetic feel

**From Article** (extracted after generation):
- Section 1 title → Act 1 visual
- Section 2 title → Act 2 visual
- Section 3 title → Act 3 visual
- Section 4 title → Act 4 visual
- Factoids → visual hints

### Example Video Prompt Generation
```python
def generate_video_prompt_from_article(article, app_config):
    """Generate 4-act video prompt from article sections."""

    style = app_config.media_style_details  # From config
    sections = article['sections']  # From article

    prompt = f"""CRITICAL: NO TEXT, NO WORDS, NO LETTERS anywhere.

STYLE: {style}

ACT 1 (0-3s): {sections[0]['title']}
Visual: {sections[0].get('visual_hint', 'Opening scene')}

ACT 2 (3-6s): {sections[1]['title']}
Visual: {sections[1].get('visual_hint', 'Development')}

ACT 3 (6-9s): {sections[2]['title']}
Visual: {sections[2].get('visual_hint', 'Journey/Process')}

ACT 4 (9-12s): {sections[3]['title']}
Visual: {sections[3].get('visual_hint', 'Resolution/Outcome')}

REMINDER: ZERO TEXT IN ANY FRAME."""

    return prompt
```

---

## Integration Tasks

### Phase 0: Fix External Links (PRIORITY)
- [ ] Investigate commits `8e48927`, `c24e5eb`, `1f9f0cd`
- [ ] Restore link insertion in article generation
- [ ] Test with new article

### Phase 1: Remove Image Generation
File: `src/activities/media/` + workflows
- [ ] Remove `generate_image_prompts()` activity
- [ ] Remove image generation from workflow
- [ ] Remove Flux/image model calls
- [ ] Keep ONLY video generation

### Phase 2: Add Video Prompt Activity
File: `src/activities/generation/video_prompt.py` (NEW)
- [ ] Create `generate_video_prompt_from_article()` activity
- [ ] Extract section titles/angles from article
- [ ] Combine with app config media style
- [ ] Output 4-act prompt with NO TEXT rule

### Phase 3: Update Video Generation
File: `src/activities/media/video_generation.py`
- [ ] Switch to Seedance as default
- [ ] Update duration to 12 seconds
- [ ] Use app config for model/resolution
- [ ] Accept prompt from new activity

### Phase 4: Update Article Generation
File: `src/activities/generation/article_generation.py`
- [ ] Generate 4 H2 sections (act-aligned)
- [ ] Include factoid for each section
- [ ] Include visual_hint for each section (for video prompt)
- [ ] Ensure external links are inserted
- [ ] Generate callouts based on app config callout_types
- [ ] Generate FAQ items (4 questions)
- [ ] Generate comparison data if applicable
- [ ] Generate timeline events if dates are present

#### Sonnet Article Output Structure (FULL DETAIL)
```python
{
    "title": "Cyprus Digital Nomad Visa 2025: Your Complete Escape Plan",
    "slug": "cyprus-digital-nomad-visa-2025-escape-plan",
    "excerpt": "Discover how Cyprus's new digital nomad visa...",

    # 4 ACT-ALIGNED SECTIONS (for video and section headers)
    "sections": [
        {
            "act": 1,
            "title": "The London Grind: Why Remote Workers Are Burning Out",
            "factoid": "73% of UK remote workers report feeling trapped despite location flexibility",
            "visual_hint": "Dark grey London office, rain on windows, exhausted worker at desk, blue monitor glow",
            "content": "<p>...</p>"  # Full HTML content with external links
        },
        {
            "act": 2,
            "title": "The Cyprus Opportunity: Tax Benefits That Actually Make Sense",
            "factoid": "Cyprus has 3,400 hours of sunshine annually vs UK's 1,500 hours",
            "visual_hint": "Woman at home looking hopeful at laptop, warm evening light, Mediterranean imagery on screen",
            "content": "<p>...</p>"
        },
        {
            "act": 3,
            "title": "Making the Move: From Application to Arrival",
            "factoid": "Average processing time: 4-6 weeks • Application fee: ~€70",
            "visual_hint": "Travel montage: suitcase, passport, airplane window, Cyprus coastline from above",
            "content": "<p>...</p>"
        },
        {
            "act": 4,
            "title": "Life After the Move: What Six Months Actually Looks Like",
            "factoid": "Most digital nomads save €1,000-2,000 more per month than in the UK",
            "visual_hint": "Golden sunset terrace, wine with friends, Mediterranean view, genuine happiness",
            "content": "<p>...</p>"
        }
    ],

    # CALLOUTS (types from app_config.callout_types)
    # For relocation: pro_tip, warning, tax_insight, lifestyle_tip, cost_saving
    "callouts": [
        {
            "type": "pro_tip",
            "title": "The Tax Advantage",
            "content": "Cyprus operates a non-domicile tax regime...",
            "placement": "after_section_2"  # or "after_section_3"
        },
        {
            "type": "warning",
            "title": "Visa Quota Alert",
            "content": "Cyprus limits digital nomad visas to 500 per year...",
            "placement": "after_section_3"
        }
    ],

    # FAQ (4 items, each gets unique thumbnail)
    "faq": [
        {"q": "Can I bring my family on the Cyprus Digital Nomad Visa?", "a": "Yes, the visa allows for family reunification..."},
        {"q": "Do I need to pay Cyprus taxes on my foreign income?", "a": "Tax treatment depends on your specific situation..."},
        {"q": "What's the internet speed like in Cyprus?", "a": "Excellent. Major cities have fiber up to 1Gbps..."},
        {"q": "Can I travel within the EU on this visa?", "a": "Cyprus is an EU member, but the Digital Nomad Visa doesn't automatically grant Schengen access..."}
    ],

    # COMPARISON TABLE (if applicable)
    "comparison": {
        "title": "Cyprus vs Other Digital Nomad Visas",
        "items": [
            {"country": "Cyprus", "income_req": "€3,500/mo", "tax": "Favorable", "duration": "1yr + 2 renewals", "processing": "4-6 weeks"},
            {"country": "Portugal", "income_req": "€3,040/mo", "tax": "NHR regime", "duration": "2 years", "processing": "2-3 months"},
            {"country": "Spain", "income_req": "€2,520/mo", "tax": "Beckham Law", "duration": "1 year", "processing": "1-3 months"}
        ]
    },

    # TIMELINE (if dates are present in research)
    "timeline": [
        {"date": "January 2022", "title": "Program Launched", "description": "Cyprus introduces Digital Nomad Visa scheme"},
        {"date": "June 2022", "title": "Income Threshold Set", "description": "€3,500 monthly requirement established"},
        {"date": "March 2023", "title": "First Renewals", "description": "Initial holders begin renewing for 2-year terms"},
        {"date": "2025", "title": "Program Matures", "description": "Established expat community, streamlined processing"}
    ],

    # STAT HIGHLIGHT (for "The Bottom Line" section)
    "stat_highlight": {
        "headline": "Save €12,000-24,000 per year while upgrading your lifestyle",
        "description": "Between tax optimization, lower cost of living, and reduced commuting stress...",
        "stats": [
            {"value": "3,400", "label": "Hours of sunshine/year"},
            {"value": "30-40%", "label": "Lower cost of living"},
            {"value": "4-6", "label": "Weeks to approval"}
        ]
    },

    # SOURCES (for sources section with thumbnails)
    "sources": [
        {"name": "Cyprus Ministry of Interior", "description": "Digital Nomad Visa Program", "url": "..."},
        {"name": "Nomad Capitalist", "description": "Cyprus Tax Guide 2025", "url": "..."},
        {"name": "GetGoldenVisa", "description": "European DN Visa Comparison", "url": "..."}
    ]
}
```

#### App-Specific Callout Types
```python
# From app_config.py - Sonnet uses these to decide callout types
RELOCATION_CALLOUTS = ["pro_tip", "warning", "tax_insight", "lifestyle_tip", "cost_saving"]
PLACEMENT_CALLOUTS = ["pro_tip", "deal_insight", "market_context", "expert_view"]
PE_NEWS_CALLOUTS = ["breaking", "analysis", "market_impact", "expert_quote"]
```

### Phase 5: Update Workflow
File: `src/workflows/article_creation.py`
- [ ] Remove image generation step
- [ ] Add video prompt generation step (after article)
- [ ] Update video generation call
- [ ] Generate thumbnail URLs from playback_id

### Phase 6: Database Output
- [ ] Store `video_narrative` JSON:
```json
{
  "playback_id": "xxx",
  "duration": 12,
  "acts": 4,
  "thumbnails": {
    "hero": "https://image.mux.com/{id}/thumbnail.jpg?time=10.5",
    "sections": [
      {"time": 1.5, "title": "...", "factoid": "..."},
      {"time": 4.5, "title": "...", "factoid": "..."},
      {"time": 7.5, "title": "...", "factoid": "..."},
      {"time": 10.5, "title": "...", "factoid": "..."}
    ]
  }
}
```

---

## Key Files

```
src/config/app_config.py                    # App + theme configs (UPDATED)
src/activities/generation/article_generation.py  # Article with 4 sections
src/activities/generation/video_prompt.py   # NEW: Video prompt from article
src/activities/media/video_generation.py    # Seedance generation
src/workflows/article_creation.py           # Main workflow
```

## Test Files
```
test_seedance_4act.py                       # Seedance video test
test_full_article_workflow.py --use-existing # Full demo
analyze_thumbnails.py                       # Thumbnail analysis
thumbnail_comparison.html                   # Grid of all 0.5s timestamps
```

## Thumbnail Visual Distinctness Tool

To ensure thumbnails used for different components are visually distinct:

```bash
python3 analyze_thumbnails.py <playback_id>
# Generates: thumbnail_analysis.html
```

**What it shows:**
- Full timeline grid (0.5s intervals)
- Act-by-act breakdown (color-coded)
- Click-to-select for visual comparison
- Recommended timestamps for 4 vs 8 sections

**Smart Timestamp Selection:**
```python
# Avoid adjacent timestamps that look similar
# Spread across all 4 acts for visual variety

SECTION_THUMBNAILS = [1.5, 4.5, 7.5, 10.5]      # Section headers (1 per act)
FAQ_THUMBNAILS = [1.0, 4.0, 7.0, 10.0]          # FAQ cards (spread across acts)
TIMELINE_THUMBNAILS = [1.5, 4.5, 7.5, 10.5]     # Timeline events
BACKGROUND_THUMBNAILS = [10.0, 5.0]              # Translucent backgrounds
```

**Rule**: Never use timestamps from same act for adjacent components (e.g., FAQ 1 and FAQ 2 should be from different acts)

## Demo
```bash
python3 test_full_article_workflow.py --use-existing
open file:///Users/dankeegan/quest/content-worker/test_full_article_demo.html
```

## Existing Test Playback ID
`a2WovgYswGqojcLdc6Mv8YabXbHsU02MTPHoDbcE700Yc`

---

## Summary

1. **Fix links first** (Nov 25 regression)
2. **Remove images** (no longer needed, Mux thumbnails replace)
3. **Article-First**: Write article → extract sections → generate video prompt
4. **Hybrid prompts**: Config style + Article content = Tailored video
5. **Adapt workflow**: Don't create new, modify `ArticleCreationWorkflow`
