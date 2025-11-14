# Company Worker

Comprehensive company research and profile generation service for Quest.

## Overview

Company Worker is a Temporal-based workflow service that performs deep research on companies and generates structured profiles with 60+ data fields. It's designed to compete with Crunchbase and PitchBook by offering unlimited article visibility and comprehensive company data.

## Key Features

- **Geo-Targeted Research**: Uses Serper.dev for location-specific Google searches
- **Multi-Source Research**: Combines Serper, Crawl4AI, Firecrawl, and Exa
- **AI Profile Generation**: Pydantic AI + Gemini 2.5 for structured data extraction
- **Ambiguity Detection**: Confidence scoring and automatic re-scraping
- **Knowledge Graph Integration**: Zep Cloud for existing coverage analysis
- **Featured Images**: AI-generated images via Replicate (Flux Schnell)
- **Article Relationships**: Links companies to related articles (KEY USP!)
- **Cost Tracking**: ~$0.07-0.13 per company, <150s execution time

## Architecture

```
company-worker/
├── src/
│   ├── api/                    # FastAPI endpoints (optional)
│   ├── workflows/              # Temporal workflows
│   │   └── company_creation.py # Main workflow
│   ├── activities/             # Temporal activities
│   │   ├── research/          # Research activities
│   │   ├── media/             # Image generation
│   │   ├── generation/        # AI profile generation
│   │   ├── storage/           # Database & Zep
│   │   └── articles/          # Article relationships
│   ├── models/                # Pydantic models
│   │   ├── input.py          # CompanyInput
│   │   ├── payload.py        # CompanyPayload (60+ fields)
│   │   └── research.py       # ResearchData
│   └── utils/                 # Config & helpers
├── worker.py                  # Temporal worker entrypoint
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Tech Stack

- **Workflow**: Temporal Cloud
- **AI**: Pydantic AI + Google Gemini 2.5 / OpenAI / Anthropic
- **Search**: Serper.dev (geo-targeted Google search)
- **Web Scraping**: Crawl4AI (free) + Firecrawl (backup)
- **Research**: Exa ($0.04/query)
- **Images**: Replicate (Flux Schnell, $0.003/image)
- **Storage**: Cloudinary (images), Neon PostgreSQL (data)
- **Knowledge Graph**: Zep Cloud
- **Deployment**: Railway

## Setup

### 1. Install Dependencies

```bash
cd company-worker
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in all API keys:

```bash
cp .env.example .env
```

Required API keys:
- `TEMPORAL_API_KEY` - Temporal Cloud
- `DATABASE_URL` - Neon PostgreSQL
- `GOOGLE_API_KEY` - Gemini (or OPENAI_API_KEY / ANTHROPIC_API_KEY)
- `SERPER_API_KEY` - Serper.dev
- `EXA_API_KEY` - Exa
- `REPLICATE_API_TOKEN` - Replicate
- `CLOUDINARY_URL` - Cloudinary
- `ZEP_API_KEY` - Zep Cloud

Optional:
- `FIRECRAWL_API_KEY` - Firecrawl (backup crawler)

### 3. Run Worker Locally

```bash
python worker.py
```

You should see:
```
🏢 Company Worker - Starting...
✅ Connected to Temporal successfully
🚀 Company Worker Started Successfully!
```

## Usage

### Trigger Company Creation

The worker listens for `CompanyCreationWorkflow` on the `quest-company-queue` task queue.

**Input:**
```python
{
    "url": "https://evercore.com",
    "category": "placement_agent",  # or "relocation_provider", "recruiter"
    "jurisdiction": "US",           # UK, US, SG, etc.
    "app": "placement",             # or "relocation"
    "force_update": false
}
```

**Output:**
```python
{
    "status": "created",            # or "updated", "exists"
    "company_id": "uuid",
    "slug": "evercore",
    "name": "Evercore Inc.",
    "logo_url": "https://...",
    "featured_image_url": "https://...",
    "research_cost": 0.08,
    "research_confidence": 0.92,
    "data_completeness": 85.5,
    "related_articles_count": 15,
    "zep_graph_id": "company-uuid"
}
```

### Example: Trigger via Python

```python
from temporalio.client import Client
from src.models.input import CompanyInput

client = await Client.connect(
    "your-temporal-address",
    namespace="your-namespace",
    api_key="your-api-key",
    tls=True
)

input_data = CompanyInput(
    url="https://evercore.com",
    category="placement_agent",
    jurisdiction="US",
    app="placement"
)

handle = await client.start_workflow(
    "CompanyCreationWorkflow",
    input_data.model_dump(),
    id=f"company-evercore-{timestamp}",
    task_queue="quest-company-queue"
)

result = await handle.result()
print(f"Company created: {result['slug']}")
```

## Workflow Phases

The workflow executes in 10 phases (~90-150 seconds total):

1. **Normalize & Check** (5s)
   - Clean URL, extract domain
   - Check if company exists

2. **Parallel Research** (60s)
   - Serper: Geo-targeted news search
   - Crawl4AI/Firecrawl: Website scraping
   - Exa: Deep company research
   - Logo extraction

3. **Ambiguity Check** (10s)
   - Calculate confidence score
   - Detect missing category keywords

4. **Optional Re-scrape** (30s)
   - Triggered if confidence < 70%
   - Refined queries for better results

5. **Zep Context** (5s)
   - Query for existing coverage
   - Find related articles and deals

6. **Generate Profile** (15s)
   - Pydantic AI synthesis
   - 60+ structured fields

7. **Generate Images** (15s)
   - Featured image via Replicate
   - Upload to Cloudinary

8. **Save to Database** (5s)
   - Store in Neon PostgreSQL
   - JSONB payload

9. **Fetch Articles** (5s)
   - Query article_companies junction table
   - Return related coverage (KEY USP!)

10. **Sync to Zep** (5s)
    - Add company to knowledge graph
    - Enable future enrichment

## Data Model

### CompanyPayload (60+ Fields)

```python
{
    # Hero Stats
    "hero_stats": {
        "employees": "1,800",
        "founded_year": 1995,
        "serviced_deals": 450,
        "countries_served": 15
    },

    # Basic Info
    "legal_name": "Evercore Inc.",
    "tagline": "Premier global investment banking advisory",
    "description": "...",
    "short_description": "...",

    # Classification
    "industry": "Investment Banking",
    "company_type": "placement_agent",
    "operating_status": "Active",

    # Location
    "headquarters": "55 East 52nd Street, New York, NY",
    "headquarters_city": "New York",
    "headquarters_country": "United States",
    "office_locations": [...],

    # Contact
    "website": "https://evercore.com",
    "phone": "+1-212-555-1234",
    "linkedin_url": "...",

    # People
    "executives": [...],
    "founders": [...],

    # Services & Clients
    "services": [...],
    "key_clients": [...],
    "notable_deals": [...],

    # Research Metadata
    "data_completeness_score": 85.5,
    "confidence_score": 0.92,
    "research_cost": 0.08,
    "ambiguity_signals": []
}
```

## Cost Breakdown

Per company (normal research):
- Serper (news): $0.02
- Exa (research): $0.04
- Crawl4AI: $0.00 (free)
- Gemini 2.5: $0.01
- Replicate (image): $0.003
- Cloudinary: $0.00 (free tier)
- **Total: ~$0.07**

With re-scrape (low confidence):
- Additional Serper: $0.02
- Additional Exa: $0.04
- **Total: ~$0.13**

**50 companies/month: $3.50-6.50**

## Article Display USP

This is what differentiates us from Crunchbase/PitchBook:

### Crunchbase
- Paywalled articles
- Minimal display

### PitchBook
- Shows 2 recent articles
- Basic list view

### Quest (Us!)
- ✅ Unlimited article visibility (no paywall)
- ✅ Rich timeline view
- ✅ Network graph visualization
- ✅ Article-company-deal relationships
- ✅ "Previously reported" connections
- ✅ Beautiful modern UI

### Implementation

Companies page queries:
```sql
SELECT a.*, ac.relevance_score
FROM articles a
JOIN article_companies ac ON a.id = ac.article_id
WHERE ac.company_id = $1
AND a.status = 'published'
ORDER BY a.published_at DESC
```

Display as timeline with relationship indicators!

## Deployment

### Railway

1. **Create Service**
   ```bash
   railway up
   ```

2. **Set Environment Variables**
   All variables from `.env.example` must be set in Railway

3. **Deploy**
   Railway will automatically:
   - Detect Python
   - Install dependencies
   - Run `python worker.py`

### Monitoring

Check worker logs:
```bash
railway logs
```

Worker prints detailed phase information:
```
Phase 1: Normalizing URL
Phase 2: Parallel research
Phase 3: Checking research ambiguity
...
✅ Company creation complete: evercore (cost: $0.08)
```

## Development

### Run Tests

```bash
pytest tests/
```

### Local Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run worker
python worker.py
```

### Add New Activity

1. Create activity file in `src/activities/`
2. Import in `worker.py`
3. Add to activities list
4. Use in workflow with `workflow.execute_activity()`

## API Keys Setup

### Serper.dev
1. Sign up at https://serper.dev
2. Get API key from dashboard
3. Add to `.env` as `SERPER_API_KEY`

### Exa
1. Sign up at https://exa.ai
2. Get API key
3. Add as `EXA_API_KEY`

### Replicate
1. Sign up at https://replicate.com
2. Get API token
3. Add as `REPLICATE_API_TOKEN`

### Cloudinary
1. Sign up at https://cloudinary.com
2. Get cloudinary URL (format: `cloudinary://key:secret@cloud`)
3. Add as `CLOUDINARY_URL`

### Zep Cloud
1. Sign up at https://www.getzep.com
2. Get API key
3. Add as `ZEP_API_KEY`

## Troubleshooting

### Worker won't start
- Check all required env vars are set
- Verify Temporal Cloud connectivity
- Check database connection

### Research failing
- Verify API keys are valid
- Check rate limits
- Review ambiguity signals in output

### Low completeness scores
- Check source data quality
- Review AI prompts in `profile_generation.py`
- Adjust field weights in `completeness.py`

## Contributing

When adding new features:
1. Create activity in appropriate subdirectory
2. Add to worker registration
3. Update workflow if needed
4. Update this README

## License

MIT

## Support

For issues or questions, see the main Quest repository.
