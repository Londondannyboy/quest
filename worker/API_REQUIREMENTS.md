# API Requirements for Quest Worker

## Required (Worker won't start without these)

| API | Purpose | Used By |
|-----|---------|---------|
| `DATABASE_URL` | Neon PostgreSQL connection | All workflows (saving articles) |
| `GOOGLE_API_KEY` | Gemini AI for content generation | All workflows (article writing, extraction) |
| `SERPER_API_KEY` | Google News search | NewsroomWorkflow, PlacementWorkflow, RelocationWorkflow |
| `EXA_API_KEY` | Exa research API | **ArticleWorkflow** (direct research) |

## Optional (Enhanced features)

| API | Purpose | Used By | Behavior if Missing |
|-----|---------|---------|-------------------|
| `FIRECRAWL_API_KEY` | Deep web scraping | ArticleWorkflow (deep_crawl), Company workflows | Falls back to Serper or skips |
| `TAVILY_API_KEY` | Web content extraction | NewsroomWorkflow (scraping) | Returns sources without content |
| `REPLICATE_API_TOKEN` | Image generation (Flux) | All workflows | Skips image generation |
| `CLOUDINARY_CLOUD_NAME` | Image storage | All workflows | Skips image upload |
| `CLOUDINARY_API_KEY` | Image storage | All workflows | Skips image upload |
| `CLOUDINARY_API_SECRET` | Image storage | All workflows | Skips image upload |
| `ZEP_API_KEY` | Knowledge base sync | All workflows (optional stage) | Skips Zep sync |

## Temporal Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `TEMPORAL_ADDRESS` | `localhost:7233` | Temporal server address |
| `TEMPORAL_NAMESPACE` | `default` | Temporal namespace |
| `TEMPORAL_API_KEY` | (none) | Required for Temporal Cloud |
| `TEMPORAL_TASK_QUEUE` | `quest-content-queue` | Task queue name |

## Workflow-Specific Requirements

### NewsroomWorkflow (News-based articles)
**Required:**
- GOOGLE_API_KEY
- SERPER_API_KEY
- DATABASE_URL

**Optional:**
- TAVILY_API_KEY (for scraping)
- ZEP_API_KEY (for knowledge base)
- REPLICATE_API_TOKEN + CLOUDINARY_* (for images)

### ArticleWorkflow (Direct research)
**Required:**
- GOOGLE_API_KEY
- EXA_API_KEY
- DATABASE_URL

**Optional:**
- FIRECRAWL_API_KEY (for deep crawling)
- ZEP_API_KEY (for knowledge base)
- REPLICATE_API_TOKEN + CLOUDINARY_* (for images)

### Company Workflows
**Required:**
- GOOGLE_API_KEY
- DATABASE_URL

**Optional:**
- FIRECRAWL_API_KEY (primary scraping method)
- SERPER_API_KEY (fallback scraping)
- CLOUDINARY_* (for logo processing)

## Setting Variables in Railway

```bash
# Set a variable
railway variables set EXA_API_KEY=your_key_here

# Set multiple variables
railway variables set \
  EXA_API_KEY=your_exa_key \
  FIRECRAWL_API_KEY=your_firecrawl_key

# View all variables
railway variables
```

## Example: Minimal ArticleWorkflow Setup

For a basic ArticleWorkflow deployment, you need:

```bash
DATABASE_URL=postgresql://...
GOOGLE_API_KEY=AIza...
EXA_API_KEY=exa_...
TEMPORAL_ADDRESS=europe-west3.gcp.api.temporal.io:7233
TEMPORAL_NAMESPACE=your-namespace
TEMPORAL_API_KEY=your_temporal_key
```

This will:
✅ Create articles with Exa research
✅ Generate content with Gemini
✅ Save to Neon database
❌ Skip image generation (no Replicate/Cloudinary)
❌ Skip knowledge base sync (no Zep)

## Getting API Keys

- **Exa**: https://exa.ai - Research API
- **Serper**: https://serper.dev - Google Search API
- **Tavily**: https://tavily.com - Web scraping
- **FireCrawl**: https://firecrawl.dev - Advanced scraping
- **Google AI**: https://ai.google.dev - Gemini API
- **Replicate**: https://replicate.com - Image generation
- **Cloudinary**: https://cloudinary.com - Image storage
- **Zep**: https://www.getzep.com - Knowledge graphs
- **Neon**: https://neon.tech - PostgreSQL database
