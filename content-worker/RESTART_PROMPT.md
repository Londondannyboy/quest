# Quest Content Worker - Comprehensive Restart Prompt

**Last Updated:** 2025-12-04
**Last Commits:** `b0c4ae9`, `563bf83`

Use this document to quickly restore context when starting a new Claude Code session.

---

## CRITICAL: Recent Session (2025-12-04)

### Problem Solved
Country Guide workflow was broken due to:
1. **Deprecated Google model names:** `gemini-3-pro-preview`, `gemini-2.0-flash-exp`, `gemini-2.5-pro-preview-06-05`
2. **Expired `GOOGLE_API_KEY`** on Railway worker

### Solution: Pydantic AI Gateway
Created unified AI access via Gateway proxy. **Priority order: Gateway → Anthropic → Gemini**

### New Files Created
| File | Purpose |
|------|---------|
| `src/utils/ai_gateway.py` | Gateway utility: `get_completion_async()`, `is_gateway_available()` |
| `test_pydantic_ai.py` | Integration test for AI providers |

### Key Pattern - AI Gateway Usage
```python
from src.utils.ai_gateway import get_completion_async

response = await get_completion_async(
    prompt,
    model="fast",     # gpt-4o-mini (news, sections)
    # model="quality",  # gpt-4o (curation, articles)
    temperature=0.7,
    max_tokens=4096
)
```

### Gateway works via OpenAI proxy
```python
import openai
client = openai.Client(
    base_url='https://gateway.pydantic.dev/proxy/chat/',
    api_key='paig_7fYwHe34BlYcQgYf4OJpEd7qnzScyWFs',
)
```

### Environment Variable Required
```bash
PYDANTIC_AI_GATEWAY_API_KEY=paig_7fYwHe34BlYcQgYf4OJpEd7qnzScyWFs
```
**Must be set on Railway** (where Temporal worker runs), not just Vercel.

### Files Updated for Gateway
- `src/activities/research/news_assessment.py`
- `src/activities/articles/analyze_sections.py`
- `src/utils/inject_section_images.py`
- `src/activities/generation/research_curation.py`
- `src/activities/generation/article_generation.py`
- `src/activities/generation/country_guide_generation.py`
- `src/utils/config.py`
- `requirements.txt` → `pydantic-ai-slim>=0.8.0`

### Current Status
- ✅ Gateway tested and working locally
- ✅ Code committed and pushed
- ⏳ Railway needs `PYDANTIC_AI_GATEWAY_API_KEY` env var
- ❌ Google API key expired (but Gateway bypasses this)

### To Test After Railway Redeploy
```bash
python scripts/test_country_guide.py Switzerland CH
```

### Quick Test Gateway Locally
```bash
# Test gateway is working
PYDANTIC_AI_GATEWAY_API_KEY="paig_7fYwHe34BlYcQgYf4OJpEd7qnzScyWFs" python3 -c "
import asyncio
from src.utils.ai_gateway import get_completion_async, is_gateway_available
print('Gateway available:', is_gateway_available())
print(asyncio.run(get_completion_async('Say hello', model='fast')))
"
```

### Error Pattern That Triggered This Session
```json
{
  "type": "activity_failed",
  "workflow_run_id": "...",
  "error": {
    "type": "ApplicationError",
    "message": "API Key not found. Please pass a valid API key.",
    "cause": "got unexpected status code 400"
  }
}
```
**Cause:** Expired `GOOGLE_API_KEY` in Railway env vars.
**Solution:** Use Gateway as primary, not Google.

---

## PENDING TASKS (2025-12-04)

| Priority | Task | Status |
|----------|------|--------|
| 🔴 HIGH | Set `PYDANTIC_AI_GATEWAY_API_KEY` on Railway | ⏳ Pending |
| 🟡 MED | Re-test Switzerland Country Guide after Railway redeploys | ⏳ Pending |
| 🟢 LOW | Update Google API key if needed (backup only) | Optional |

---

## Project Overview

Quest is an AI-powered content generation platform that creates company profiles and articles. It uses:
- **Temporal** for workflow orchestration (cloud hosted at `quickstart-quest.zivkb`)
- **Railway** for deployment (multiple services)
- **Neon** for PostgreSQL database
- **Zep** for knowledge graph/memory

### Repository Structure

```
/Users/dankeegan/quest/
├── content-worker/          # Main worker service (THIS FOLDER)
│   ├── src/
│   │   ├── workflows/       # Temporal workflows
│   │   │   ├── article_creation.py    # Main article workflow
│   │   │   ├── company_creation.py    # Company profile workflow
│   │   │   └── news_creation.py       # Scheduled news workflow
│   │   ├── activities/      # Temporal activities
│   │   │   ├── generation/  # AI generation (article, curation, prompts)
│   │   │   ├── media/       # Video, images, logo extraction
│   │   │   ├── research/    # Serper, Exa, Crawl4AI, DataForSEO
│   │   │   ├── storage/     # Neon, Zep integration
│   │   │   └── validation/  # Link validation
│   │   ├── utils/           # Config, helpers
│   │   └── config/          # App-specific configs
│   ├── worker.py            # Temporal worker entry point
│   ├── app.py               # Streamlit dashboard (DO NOT RENAME - Railway expects this)
│   └── requirements.txt
├── gateway/                 # FastAPI gateway service
│   └── routers/
│       └── workflows.py     # API endpoints for triggering workflows
└── [other apps - gtm, placement, relocation, etc.]
```

---

## Key Workflows

### ArticleCreationWorkflow (`src/workflows/article_creation.py`)

**Current Phase Order (as of 2025-11-25):**

```
Phase 1: Research Topic (60s)
  - DataForSEO news search
  - Serper article search
  - Exa topic research
  All run in PARALLEL

Phase 2: Crawl Discovered URLs (90s)
  - Crawl4AI batch crawl for full content

Phase 3: Curate Research Sources (30s)
  - Gemini 2.5 Pro extracts facts, opinions, angles
  - Filters off-topic sources
  - Generates article outline

Phase 4: Query Zep Context (5s)
  - Get related entities from knowledge graph

Phase 5: Generate Article (180s)
  - Claude Sonnet writes article from curated research
  - Extracts media prompts embedded in content

Phase 5b: Validate Links (30s)
  - Playwright checks all external URLs
  - Removes broken links

Phase 6: SAVE TO DATABASE (5s)
  - Article saved to Neon BEFORE media generation
  - If video/images fail, article content is safe

Phase 7: SYNC TO ZEP (5s)
  - Knowledge graph updated early (doesn't need media)

Phase 8: Generate VIDEO Prompt (10s) - NEW SEPARATED STEP
  - Calls generate_video_prompt activity
  - Model-aware (Seedance vs WAN-2.5 specific tips)
  - Returns focused 60-100 word cinematic prompt

Phase 9: Generate Video (5-15min)
  - Replicate API (Seedance or WAN-2.5)
  - Upload to Mux for streaming
  - Get GIF thumbnail for featured_asset_url

Phase 10: Generate IMAGE Prompts (10s) - NEW SEPARATED STEP
  - Calls generate_image_prompts activity
  - Style-matched to video (uses video prompt as reference)
  - Can reference video GIF URL

Phase 10b: Generate Content Videos (if video_count > 1)
  - Sequential videos using hero GIF as style context

Phase 10c: Generate Content Images (Flux Kontext Pro)
  - Sequential images matching video style

Phase 11: Final Update (5s)
  - Embed media in article content
  - Update Neon with final payload
```

### CountryGuideCreationWorkflow (`src/workflows/country_guide_creation.py`)

**Used for:** Comprehensive relocation guides (e.g., "Switzerland", "Portugal")

**AI Provider Order:** Gateway (GPT-4o) → Anthropic (Claude) → Gemini

```
Phase 1: Research Country Topics
  - Multiple parallel Serper searches per topic
  - Crawl4AI for full content

Phase 2: Curate Research (Gateway/GPT-4o)
  - Extract facts, costs, requirements
  - Generate section outlines

Phase 3: Generate Guide Content (Gateway/GPT-4o)
  - Comprehensive country guide
  - 10-15 sections typical

Phase 4: Save to Database
  - Neon PostgreSQL

Phase 5: Sync to Zep
  - Knowledge graph update
```

**Key Files:**
- `src/workflows/country_guide_creation.py` - Main workflow
- `src/activities/generation/country_guide_generation.py` - Content generation (uses Gateway)

---

### Input Parameters (from Gateway)

```python
{
    "topic": str,                    # Required - article subject
    "article_type": str,             # "news", "guide", "comparison"
    "app": str,                      # "placement", "relocation", "chief-of-staff", "gtm", "newsroom"
    "target_word_count": int,        # 500-3000, default 1500
    "jurisdiction": str,             # "UK", "US", "EU", "SG", etc.
    "num_research_sources": int,     # 3-15, default 10
    "generate_images": bool,         # default True
    "video_quality": str | None,     # None, "low", "medium", "high"
    "video_model": str,              # "seedance", "wan-2.5"
    "video_prompt": str | None,      # Custom prompt (optional)
    "video_count": int,              # 1-3 (1=hero only, 2-3=hero+content)
    "content_images_count": int,     # 0-5, default 2
    "slug": str | None,              # Custom URL slug for SEO
}
```

---

## Key Activities

### Research Activities

| Activity | File | Purpose |
|----------|------|---------|
| `serper_article_search` | `research/serper.py` | Google search for articles |
| `dataforseo_news_search` | `research/dataforseo.py` | News search API |
| `exa_research_topic` | `research/exa.py` | Semantic search for research |
| `crawl4ai_batch_crawl` | `research/crawl4ai_service.py` | Full page content extraction |

### Generation Activities

| Activity | File | Purpose |
|----------|------|---------|
| `curate_research_sources` | `generation/research_curation.py` | Gemini 2.5 Pro fact extraction |
| `generate_article_content` | `generation/article_generation.py` | Claude Sonnet article writing |
| `generate_video_prompt` | `generation/media_prompts.py` | **NEW** Model-aware video prompt |
| `generate_image_prompts` | `generation/media_prompts.py` | **NEW** Style-matched image prompts |
| `generate_media_prompts` | `generation/media_prompts.py` | DEPRECATED - kept for compatibility |

### Media Activities

| Activity | File | Purpose |
|----------|------|---------|
| `generate_article_video` | `media/video_generation.py` | Replicate video generation |
| `upload_video_to_mux` | `media/mux_client.py` | Upload to Mux, get stream URL + GIF |
| `generate_sequential_article_images` | `media/sequential_images.py` | Flux Kontext Pro images |
| `generate_flux_image` | `media/flux_api_client.py` | Single image generation |

### Storage Activities

| Activity | File | Purpose |
|----------|------|---------|
| `save_article_to_neon` | `storage/neon_database.py` | Insert/update article in DB |
| `sync_article_to_zep` | `storage/zep_integration.py` | Knowledge graph sync |

---

## Recent Changes (2025-11-25)

### 1. Separated Video & Image Prompt Generation
**Commit:** `94ee347`

Split `generate_media_prompts` into two dedicated activities:

**`generate_video_prompt`** - Model-aware video prompts:
```python
VIDEO_MODEL_GUIDANCE = {
    "seedance": {
        "strengths": "Fast, good motion, cinematic quality",
        "weaknesses": "Cannot render text at all",
        "optimal_length": "60-100 words",
        "tips": ["Use degree adverbs", "Sequential actions", "No text/typography"]
    },
    "wan-2.5": {
        "strengths": "Better text rendering (single words), excellent depth/parallax",
        "weaknesses": "Slower, struggles with multiple words",
        "optimal_length": "80-120 words",
        "tips": ["Single-word text OK", "Emphasize depth", "Film terminology"]
    }
}
```

**`generate_image_prompts`** - Style-matched to video:
- Takes `video_gif_url` for visual reference
- Takes `video_style_description` from video prompt
- Generates prompts that complement video's visual style

### 2. Workflow Reordering for Resilience
**Commit:** `ba15de7`

Moved SAVE TO NEON before video/image generation:
- Article content is safe even if video generation fails
- Zep sync happens early (doesn't need media)
- Video/images update existing article record

### 3. Dashboard Sliders
**Commit:** `6fcb8a5`

Added to `app.py`:
- Video count slider (1-3)
- Content images count slider (0-5)
- Video controls only show when video quality selected

### 4. Dashboard Fix
**Commit:** `947dc28`

Renamed `dashboard.py` back to `app.py` - Railway expects this filename.

---

## Video Generation Details

### Seedance Model
- **Provider:** Replicate (`fofr/seedance`)
- **Duration:** 3 seconds
- **Cannot render text** - prompt suffix added automatically:
  `"CRITICAL: Absolutely NO text, NO words, NO letters, NO typography - purely visual only."`
- **Cost:** ~$0.045 (low), ~$0.075 (medium)

### WAN-2.5 Model
- **Provider:** Replicate (`wan-video/wan-2.5-t2v`)
- **Duration:** 5 seconds
- **Can render single words** (like "Quest" branding)
- **Cost:** ~$0.10 per video

### Polling/Heartbeats
Video generation uses polling with Temporal heartbeats:
```python
while elapsed < max_wait:  # 10 minutes
    prediction.reload()
    activity.heartbeat(f"Status: {prediction.status}, elapsed: {elapsed}s")
    if prediction.status == "succeeded":
        break
    time.sleep(5)  # Poll every 5 seconds
```

---

## Curation (Gateway/GPT-4o)

**File:** `src/activities/generation/research_curation.py`

Uses **GPT-4o via Pydantic AI Gateway** (or Anthropic fallback) for fact extraction.

**Pre-filter:** `is_relevant_to_topic()` requires ≥2 keyword matches

**Extracts:**
- 40-60 key facts with exact numbers/dates/costs
- Opinions and sentiment from different stakeholders
- Unique angles others might miss
- Direct quotes with attribution
- Comparisons to alternatives
- Recent changes (2024-2025)
- Warnings and gotchas
- Article outline with 5-7 sections
- High-authority sources
- Timeline of events

**Model Priority:** Gateway (`gpt-4o`) → Anthropic (`claude-sonnet-4`) → Gemini (`gemini-2.5-pro`)

---

## Database Schema (Neon)

### Articles Table Key Fields
```sql
id, slug, title, app, article_type, content (JSONB),
featured_asset_url, hero_asset_url,
video_url, video_playback_id, video_asset_id,
content_image_1_url, content_image_2_url, ... content_image_5_url,
status ('draft', 'published'),
raw_research (JSONB),
created_at, updated_at
```

### `save_article_to_neon` Behavior
- If `article_id` is None → INSERT new article
- If `article_id` is provided → UPDATE existing article
- Works regardless of status (draft or published)

---

## Environment Variables

```bash
# Temporal
TEMPORAL_ADDRESS=quickstart-quest.zivkb.tmprl.cloud:7233
TEMPORAL_NAMESPACE=quickstart-quest.zivkb
TEMPORAL_API_KEY=xxx
TEMPORAL_TASK_QUEUE=company-worker

# AI Models (PRIORITY ORDER)
PYDANTIC_AI_GATEWAY_API_KEY=paig_...  # PRIMARY - unified access to GPT-4o
ANTHROPIC_API_KEY=xxx                  # SECONDARY - Claude fallback
GOOGLE_API_KEY=xxx                     # LAST RESORT - Gemini (currently expired)
REPLICATE_API_TOKEN=xxx                # Video generation

# Research
SERPER_API_KEY=xxx
EXA_API_KEY=xxx
DATAFORSEO_LOGIN=xxx
DATAFORSEO_PASSWORD=xxx

# Storage
DATABASE_URL=postgresql://...  # Neon
ZEP_API_KEY=xxx

# Media
MUX_TOKEN_ID=xxx
MUX_TOKEN_SECRET=xxx
FLUX_API_KEY=xxx

# Dashboard
DASHBOARD_PASSWORD=xxx
API_KEY=xxx
GATEWAY_URL=https://quest-gateway-production.up.railway.app
```

**IMPORTANT:** The `PYDANTIC_AI_GATEWAY_API_KEY` must be set on **Railway** (where the Temporal worker runs).

---

## Railway Services

| Service | Purpose | Entry Point |
|---------|---------|-------------|
| `content-worker` | Temporal worker | `python worker.py` |
| `dashboard` | Streamlit UI | `streamlit run app.py` |
| `gateway` | FastAPI API | `uvicorn main:app` |
| `crawl4ai` | Browser automation | External microservice |

---

## Known Issues & Gotchas

### 1. Video Prompt Was Just Topic (FIXED)
**Symptom:** Replicate received "Digital Nomad Visa Cyprus CRITICAL..." instead of full prompt
**Root Cause:** Unknown - possibly old code on Railway or state issue
**Fix:** New separated `generate_video_prompt` activity with explicit logging

### 2. Dashboard Filename
**NEVER rename `app.py`** - Railway dashboard service is configured to run `streamlit run app.py`

### 3. Temporal SDK Doesn't Support kwargs
```python
# WRONG - will fail
await workflow.execute_activity("foo", args=[a, b], kwargs={"c": c})

# CORRECT - positional args only
await workflow.execute_activity("foo", args=[a, b, c])
```

### 4. Seedance Cannot Render Text
Always append: `"CRITICAL: Absolutely NO text, NO words, NO letters, NO typography - purely visual only."`
This is done in `transform_prompt_for_seedance()` in video_generation.py

### 5. Content Images Variable Name
Old code used `content_images` (string: "with_content", "without"), new code uses `content_images_count` (int: 0-5)

---

## Testing

### Local Test Script
```bash
cd /Users/dankeegan/quest/content-worker
python test_full_pipeline.py article   # Curation + article generation
python test_full_pipeline.py video     # Video generation only
python test_full_pipeline.py images    # Image generation only
```

### Check Imports Work
```bash
python -c "from worker import *; print('OK')"
```

### Syntax Check
```bash
python -m py_compile src/workflows/article_creation.py
python -m py_compile src/activities/generation/media_prompts.py
```

---

## Git Commands

```bash
# Check status
git status

# Recent commits
git log --oneline -10

# Push changes
git add -A && git commit -m "message" && git push

# Check what's deployed
git log --oneline origin/main -5
```

---

## Useful Temporal Commands

View workflows in Temporal Cloud UI:
https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows

---

## Common Tasks

### Add New Activity
1. Create function in appropriate `src/activities/` file
2. Decorate with `@activity.defn`
3. Import in `worker.py`
4. Add to worker's `activities=[]` list
5. Call from workflow with `workflow.execute_activity("name", args=[...])`

### Update Workflow
1. Edit `src/workflows/article_creation.py`
2. Test locally with `python -m py_compile`
3. Commit and push
4. Railway auto-deploys

### Debug Video Issues
1. Check Replicate dashboard for prediction status
2. Look at Temporal Cloud UI for activity logs
3. Check what prompt was passed (should see in logs)

---

## Architecture Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Dashboard  │────▶│   Gateway   │────▶│   Temporal  │
│  (app.py)   │     │  (FastAPI)  │     │   Cloud     │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
┌──────────────────────────────────────────────────────┐
│              Content Worker (Railway)                 │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Research   │  │  Generation │  │    Media    │  │
│  │  Serper     │  │  Gateway*   │  │  Replicate  │  │
│  │  Exa        │  │  (GPT-4o)   │  │  Mux        │  │
│  │  DataForSEO │  │  Anthropic  │  │  Flux       │  │
│  │  Crawl4AI   │  │  (fallback) │  │             │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐                    │
│  │   Storage   │  │  Validation │                    │
│  │  Neon (DB)  │  │  Playwright │                    │
│  │  Zep (KG)   │  │             │                    │
│  └─────────────┘  └─────────────┘                    │
└──────────────────────────────────────────────────────┘
```

---

## Quick Reference

**Start new session with:**
```
Read /Users/dankeegan/quest/content-worker/RESTART_PROMPT.md for full context on the Quest content worker project.
```

**Key files to read if needed:**
- `src/workflows/article_creation.py` - Main workflow
- `src/activities/generation/media_prompts.py` - Video/image prompt generation
- `src/activities/generation/research_curation.py` - Gemini curation
- `src/activities/media/video_generation.py` - Replicate video
- `worker.py` - Activity registration
- `app.py` - Streamlit dashboard

