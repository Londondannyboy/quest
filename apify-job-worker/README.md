# LinkedIn Apify Job Worker

**Temporal workflow worker** for scraping LinkedIn jobs, classifying with Pydantic AI, and syncing to Neon database + ZEP knowledge graph.

## 🎯 Current Status (Dec 2025)

**✅ Working:**
- Apify scraping (10 jobs, last 24 hours)
- Pydantic AI classification via Gateway (Gemini 2.0 Flash)
- Neon database UPSERT (insert new, update existing)
- Multi-model AI strategy (fast/thinking/accurate)
- Pydantic Logfire observability

**⚠️ In Progress:**
- ZEP knowledge graph sync (SDK integrated, debugging)

## 🏗️ Architecture

**Simplified 4-Step Workflow:**

```
1. Scrape LinkedIn (Apify)
   ↓
2. Classify with Pydantic AI (via Gateway)
   ↓
3. UPSERT to Neon Database
   ↓
4. UPSERT to ZEP Knowledge Graph
```

**No complex duplicate checking** - just simple upserts everywhere!

## 🔧 Technology Stack

- **Temporal** - Workflow orchestration
- **Apify** - LinkedIn scraping
- **Pydantic AI** - Structured classification (via Gateway)
- **Gemini 2.0 Flash** - LLM (fast, cheap, good enough)
- **Neon** - PostgreSQL database
- **ZEP Cloud** - Knowledge graph (zep-cloud SDK)
- **FastAPI** - REST API service

## 📁 Project Structure

```
/Users/dankeegan/worker/apify-job-worker/
├── src/
│   ├── activities/          # Temporal activities
│   │   ├── apify_scraper.py       # Apify API integration
│   │   ├── pydantic_classification.py  # AI classification
│   │   ├── duplicate_checker.py    # (deprecated - using upserts now)
│   │   ├── database_operations.py  # Neon DB operations
│   │   └── zep_sync.py            # ZEP Cloud SDK integration
│   ├── workflows/
│   │   └── linkedin_workflow.py   # Main workflow (4 steps)
│   ├── models/
│   │   ├── job_classification.py  # Pydantic AI agent
│   │   └── apify.py              # Apify data models
│   ├── config/
│   │   └── settings.py           # Environment configuration
│   ├── api/
│   │   └── main.py               # FastAPI service
│   └── worker.py                 # Temporal worker entry point
├── scripts/
│   ├── trigger_scrape.py         # Manual workflow trigger
│   ├── test_pipeline.py          # Integration tests
│   └── terminate_workflow.py     # Terminate old workflows
├── .env                          # Configuration
├── requirements.txt              # Python dependencies
├── Procfile                      # Railway deployment
└── railway.json                  # Railway configuration
```

## 🔑 Configuration

**Required Environment Variables:**

```env
# === Temporal ===
TEMPORAL_HOST=europe-west3.gcp.api.temporal.io:7233
TEMPORAL_NAMESPACE=quickstart-quest.zivkb
TEMPORAL_TASK_QUEUE=apify-linkedin-queue
TEMPORAL_API_KEY=eyJhbGciOiJFUzI1NiIs...

# === Apify ===
APIFY_API_KEY=apify_api_...
APIFY_TASK_ID=infrastructure_quest/rapid-linkedin-jobs-scraper-free-jobs-scraper-task

# === Neon Database ===
DATABASE_URL=postgresql://neondb_owner:...@ep-green-smoke-ab3vtnw9-pooler.eu-west-2.aws.neon.tech/neondb

# === Pydantic AI Gateway & Logfire ===
PYDANTIC_GATEWAY_API_KEY=paig_...
PYDANTIC_LOGIFIRE_API_KEY=pylf_v2_us_...

# === Gemini AI ===
GOOGLE_API_KEY=AIzaSy...
GEMINI_API_KEY=AIzaSy...  # Same as GOOGLE_API_KEY
GOOGLE_MODEL=gemini-2.0-flash

# === ZEP Knowledge Graph ===
ZEP_ACCOUNT_ID=e265b35c-69d8-4880-b2b5-ec6acb237a3e
ZEP_API_KEY=z_1dWlkIjoiMm...
ZEP_BASE_URL=https://api.getzep.com
ZEP_GRAPH_ID=jobs-tech
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /Users/dankeegan/worker/apify-job-worker
pip3 install -r requirements.txt
```

### 2. Start Worker

```bash
python3 -m src.worker
```

**Expected output:**
```
✅ Configured Pydantic AI Gateway
✅ Configured Pydantic Logfire
✅ LinkedIn Apify Job Worker Started Successfully
Task Queue: apify-linkedin-queue
Registered Workflows:
  - LinkedInApifyScraperWorkflow
Registered Activities:
  - scrape_linkedin_via_apify
  - classify_jobs_with_pydantic_ai (Gemini 2.0 Flash)
  - save_jobs_to_database (Neon)
  - sync_jobs_to_zep (Knowledge Graph)
```

### 3. Trigger Workflow

```bash
# In another terminal
python3 scripts/trigger_scrape.py
```

**Expected result:**
```
✅ Workflow completed!
Jobs Scraped: 10
Jobs Classified: 10
Jobs Added to Neon: 10
Jobs Synced to ZEP: 10
Duration: 20-30s
```

## 🧠 AI Classification

**Pydantic AI extracts:**
- `employment_type`: fractional, part_time, contract, full_time, etc.
- `is_fractional`: boolean
- `country`, `city`, `is_remote`, `workplace_type`
- `category`: Engineering, Finance, Marketing, Product, etc.
- `seniority_level`: c_suite, vp, director, manager, senior, mid, junior
- `role_title`: Normalized (e.g., "Chief Technology Officer")
- `required_skills`, `nice_to_have_skills`
- `salary_min`, `salary_max`, `salary_currency`
- `site_tags`: ["fractional-jobs", "remote-jobs", etc.]

**Multi-Model Strategy:**

```python
# Fast (default): gemini-2.0-flash
GOOGLE_MODEL=gemini-2.0-flash

# Reasoning: gemini-2.0-flash-thinking
GOOGLE_MODEL=gemini-2.0-flash-thinking

# Accurate: gemini-2.5-pro
GOOGLE_MODEL=gemini-2.5-pro
```

## 📊 Workflow Result

```json
{
  "source": "linkedin_apify",
  "jobs_scraped": 10,
  "jobs_classified": 10,
  "jobs_fractional": 0,
  "jobs_added_to_neon": 10,
  "jobs_updated_in_neon": 0,
  "jobs_synced_to_zep": 10,
  "errors": [],
  "duration_seconds": 22.11
}
```

## 🧪 Testing

### Integration Tests

```bash
python3 test_pipeline.py
```

Tests:
- ✅ Apify API connection
- ✅ Pydantic AI classification
- ✅ Neon duplicate check

### Manual Test

```bash
# Start worker
python3 -m src.worker

# Trigger scrape (new terminal)
python3 scripts/trigger_scrape.py

# Terminate old workflows if needed
python3 scripts/terminate_workflow.py <workflow_id> "<reason>"
```

## 🚢 Deployment (Railway)

### FastAPI Service

```bash
railway up
# Uses: Procfile → web: uvicorn src.api.main:app
```

### Worker Service

```bash
# Separate Railway service
# Procfile → worker: python -m src.worker
```

## 📡 API Endpoints (FastAPI)

### POST `/scrape/trigger`

Trigger a LinkedIn scrape.

```json
{
  "location": "United Kingdom",
  "keywords": "fractional OR part-time OR contract",
  "jobs_entries": 10,
  "job_post_time": "r86400"
}
```

### POST `/jobs/query`

Query jobs with filters.

```json
{
  "country": "United Kingdom",
  "is_fractional": true,
  "limit": 50
}
```

### GET `/workflows/{id}`

Get workflow status.

### GET `/stats`

Job statistics.

## 🐛 Debugging

### ZEP Sync Issues

```bash
# Test ZEP SDK directly
cat > /tmp/test_zep.py << 'EOF'
from zep_cloud import Zep
client = Zep(api_key="z_...")
result = client.graph.add(
    graph_id="jobs-tech",
    type="message",
    data="Test job posting"
)
print(result)
EOF
python3 /tmp/test_zep.py
```

### Worker Logs

```bash
# Watch worker logs
tail -f <worker_output>

# Look for:
# - "✅ Configured Pydantic AI Gateway"
# - "INFO: Syncing N jobs to ZEP graph: jobs-tech"
# - Any error messages
```

### Temporal UI

Check workflow execution:
- https://cloud.temporal.io
- Namespace: `quickstart-quest.zivkb`
- Look for activity failures and retry attempts

## 📈 Performance

- **Scraping**: ~15 seconds (10 jobs)
- **Classification**: ~5 seconds (10 jobs via Gateway)
- **Neon Upsert**: ~1 second
- **ZEP Sync**: ~1 second
- **Total**: ~20-30 seconds for 10 jobs

## 🔮 Next Steps

- [ ] Fix ZEP sync count reporting
- [ ] Deploy to Railway
- [ ] Add scheduled daily scrapes (Temporal cron)
- [ ] Enhanced skill extraction
- [ ] Company enrichment (industry, size, funding)
- [ ] Email alerts for new fractional jobs
- [ ] GraphQL API for job queries

## 🔗 Links

- **Temporal Cloud**: https://cloud.temporal.io
- **Apify Console**: https://console.apify.com
- **Neon Dashboard**: https://console.neon.tech
- **ZEP Dashboard**: https://www.getzep.com
- **Pydantic AI Gateway**: https://ai.pydantic.dev/gateway/

---

**Last Updated**: December 9, 2025
**Status**: ✅ Core pipeline working, ZEP integration in progress
