# LinkedIn Apify Scraper Worker

Standalone Temporal worker for scraping UK fractional jobs from LinkedIn using Apify.

## Overview

This worker scrapes LinkedIn job listings for fractional/part-time/contract roles in the UK using the [Apify LinkedIn Jobs Scraper](https://apify.com/bebity/linkedin-jobs-scraper). Jobs are classified using Gemini Flash, enriched with skills extraction, and stored in the shared Neon database.

## Features

- 🔍 **LinkedIn Scraping**: Uses Apify's official LinkedIn Jobs Scraper actor
- 🇬🇧 **UK-Focused**: Filters to United Kingdom location
- 💼 **Fractional Filtering**: Searches for fractional/part-time/contract keywords
- 🤖 **AI Classification**: Uses Gemini Flash for employment type and seniority
- 📊 **Skill Extraction**: OpenAI-powered skill identification
- 🗄️ **Shared Database**: Reuses job-worker's job_boards/jobs schema
- ⏰ **Scheduled**: Runs daily at 2 AM UTC via Temporal

## Prerequisites

- Python 3.9+
- Apify account with API key
- Temporal Cloud account (credentials)
- Neon database (shared with job-worker)
- Google API key (Gemini Flash)
- OpenAI API key (skills extraction)

## Quick Start

### 1. Setup Environment

```bash
cd /Users/dankeegan/worker/fractional-worker

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### 2. Test Apify Connection

```bash
python scripts/test_apify.py
```

Expected output:
```
✅ Actor found: LinkedIn Jobs Scraper
✅ Run started: <run-id>
✅ Apify API integration working!
```

### 3. Start Worker

In one terminal:
```bash
python -m src.worker
```

You should see:
```
✅ Connected to Temporal
✅ Worker started successfully
Listening on task queue: apify-linkedin-queue
Waiting for workflows to execute...
```

### 4. Trigger Manual Test

In another terminal:
```bash
python scripts/trigger_scrape.py
```

Monitor the workflow:
1. Worker terminal shows activity logs
2. Check Temporal UI: https://cloud.temporal.io
3. Query database for new jobs:
   ```sql
   SELECT * FROM job_boards WHERE board_type = 'apify';
   SELECT * FROM jobs WHERE board_id = (SELECT id FROM job_boards WHERE board_type = 'apify') LIMIT 10;
   ```

## Configuration

Edit environment variables in `.env`:

```env
# Temporal
TEMPORAL_HOST=europe-west3.gcp.api.temporal.io:7233
TEMPORAL_NAMESPACE=quickstart-quest.zivkb
TEMPORAL_TASK_QUEUE=apify-linkedin-queue
TEMPORAL_API_KEY=your_key

# Apify
APIFY_API_KEY=your_apify_key
APIFY_ACTOR_ID=BHzefUZlZRKWxkTck

# Database (from job-worker)
DATABASE_URL=postgresql://...

# AI APIs
GOOGLE_API_KEY=your_google_key
OPENAI_API_KEY=your_openai_key
```

### Workflow Parameters

You can customize workflow behavior via config:

```python
config = {
    "location": "United Kingdom",  # Default
    "keywords": "fractional OR part-time OR contract OR interim",  # Default
    "max_results": 500,  # Default
}
```

## Architecture

### Data Flow

```
LinkedIn → Apify API → scrape_linkedin_via_apify (15 min)
                              ↓
                    classify_jobs_with_gemini (5 min)
                              ↓
                       extract_job_skills (3 min)
                              ↓
                    save_jobs_to_database (2 min)
```

### Database Schema

Jobs are stored in shared database:

- **job_boards**: `"LinkedIn UK (Apify)"` with `board_type = "apify"`
- **jobs**: Same schema as job-worker

Key fields:
- `is_fractional`: Boolean flag for fractional roles
- `employment_type`: fractional/part_time/contract/full_time
- `seniority_level`: c_suite/vp/director/manager/etc
- `classification_confidence`: 0.0-1.0 confidence score
- `skills`: Array of extracted skills with importance levels

## File Structure

```
fractional-worker/
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── src/
│   ├── __main__.py          # Module entry point
│   ├── worker.py            # Main worker
│   ├── config/
│   │   └── settings.py      # Configuration
│   ├── models/
│   │   └── apify.py         # Data models
│   ├── activities/
│   │   ├── __init__.py      # Activity imports (shared + local)
│   │   └── apify_scraper.py # Apify API activity
│   └── workflows/
│       ├── __init__.py
│       └── linkedin_workflow.py # Main workflow
└── scripts/
    ├── test_apify.py        # Test Apify API
    ├── trigger_scrape.py    # Manual workflow trigger
    └── setup_daily_scrape.py # Schedule setup (TODO)
```

## Troubleshooting

### Issue: "APIFY_API_KEY not set"

**Solution:** Add `APIFY_API_KEY=<your_key>` to `.env` file

### Issue: "Failed to import from job-worker"

**Solution:** Ensure job-worker exists at `/Users/dankeegan/worker/job-worker/`

**Workaround:** Copy activities from job-worker manually:
```bash
cp /Users/dankeegan/worker/job-worker/src/activities/classification.py src/activities/
cp /Users/dankeegan/worker/job-worker/src/activities/enrichment.py src/activities/
cp /Users/dankeegan/worker/job-worker/src/activities/database.py src/activities/
```

### Issue: Workflow times out or fails

Check logs:
1. Worker terminal for activity errors
2. Temporal UI for workflow execution details
3. Apify console for scraping failures

### Issue: No jobs found

1. Verify Apify actor is working: `python scripts/test_apify.py`
2. Check search keywords are finding results
3. Verify Gemini classification is working (requires GOOGLE_API_KEY)

## Monitoring

### Real-time

- **Worker logs**: Check terminal running `python -m src.worker`
- **Temporal UI**: https://cloud.temporal.io
- **Apify Console**: https://console.apify.com

### Database

```sql
-- Check scraped jobs
SELECT COUNT(*) FROM jobs
WHERE board_id = (SELECT id FROM job_boards WHERE board_type = 'apify');

-- Check recent additions
SELECT title, employment_type, is_fractional, created_at
FROM jobs
WHERE board_id = (SELECT id FROM job_boards WHERE board_type = 'apify')
ORDER BY created_at DESC LIMIT 10;

-- Check classification stats
SELECT employment_type, COUNT(*) as count
FROM jobs
WHERE board_id = (SELECT id FROM job_boards WHERE board_type = 'apify')
GROUP BY employment_type;
```

## Cost Estimates

- **Apify**: ~$0.50-2.00 per scrape (500 results)
- **Gemini Flash**: ~$0.01 per scrape (classification)
- **OpenAI**: ~$0.05 per scrape (skills extraction)

**Daily cost**: ~$1-3

## Next Steps

### For Daily Scheduling

```bash
python scripts/setup_daily_scrape.py
```

This creates a Temporal schedule that runs the workflow daily at 2 AM UTC.

### For Railway Deployment

1. Create `Procfile`:
   ```
   worker: python -m src.worker
   ```

2. Create `railway.json`:
   ```json
   {
     "build": {
       "builder": "nixpacks"
     },
     "deploy": {
       "startCommand": "python -m src.worker"
     }
   }
   ```

3. Deploy: `railway up`

### For Alerts

Add Slack/email notifications on workflow failures (future enhancement)

## Related Files

- **Job Worker**: `/Users/dankeegan/worker/job-worker/` - Shared database schema
- **Content Worker**: `/Users/dankeegan/worker/content-worker/` - Temporal schedule patterns
- **Apify Scraper**: https://apify.com/bebity/linkedin-jobs-scraper

## License

Part of the Quest platform infrastructure.
