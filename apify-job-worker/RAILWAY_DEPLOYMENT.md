# Railway Deployment Guide - Apify LinkedIn Job Worker

## ✅ Code Ready for Deployment

**Git Status**: Committed and pushed to main
**Commit**: `f75a545` - Fix ZEP sync for Apify LinkedIn job scraper

## 🚂 Railway Setup Required

### 1. Create New Service in Railway

Go to Railway Dashboard → `quest` project → **New Service**

**Service Name**: `apify-job-worker`
**Source**: GitHub repo `Londondannyboy/worker`
**Root Directory**: `/apify-job-worker`

### 2. Configure Start Command

**For Worker Service**:
```
python -m src.worker
```

**OR for API Service** (if you want the FastAPI endpoint):
```
uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

**Recommended**: Create TWO services:
1. `apify-worker` → Start: `python -m src.worker`
2. `apify-api` → Start: `uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT}`

### 3. Environment Variables

Copy these from `/Users/dankeegan/worker/apify-job-worker/.env`:

```bash
# === Temporal ===
TEMPORAL_HOST=europe-west3.gcp.api.temporal.io:7233
TEMPORAL_NAMESPACE=quickstart-quest.zivkb
TEMPORAL_TASK_QUEUE=apify-linkedin-queue
TEMPORAL_API_KEY=[get from .env]

# === Apify ===
APIFY_API_KEY=[get from .env]
APIFY_TASK_ID=infrastructure_quest/rapid-linkedin-jobs-scraper-free-jobs-scraper-task

# === Neon Database ===
DATABASE_URL=[get from .env]

# === Pydantic AI ===
PYDANTIC_GATEWAY_API_KEY=[get from .env]
PYDANTIC_LOGIFIRE_API_KEY=[get from .env]

# === Gemini AI ===
GOOGLE_API_KEY=[get from .env]
GEMINI_API_KEY=[same as GOOGLE_API_KEY]
GOOGLE_MODEL=gemini-2.0-flash

# === ZEP Knowledge Graph ===
ZEP_ACCOUNT_ID=[get from .env]
ZEP_API_KEY=[get from .env]
ZEP_BASE_URL=https://api.getzep.com
ZEP_GRAPH_ID=jobs-tech
```

### 4. Deployment Commands (if using Railway CLI)

```bash
cd /Users/dankeegan/worker/apify-job-worker

# Link to Railway project and service
railway link

# Deploy
railway up

# Check logs
railway logs
```

## 📅 Scheduled Workflow

**Already configured in Temporal**:
- Schedule ID: `daily-linkedin-apify-10am-uk`
- Frequency: Daily at 10:00 UTC (10am UK time)
- Next run: Tomorrow (Dec 10) at 10:00 UTC
- Workflow: `LinkedInApifyScraperWorkflow`

## ✅ What's Fixed

**ZEP Sync Now Working**:
- ✅ Changed `type="message"` → `type="text"`
- ✅ Rich text format with entity hints
- ✅ Skills structured as essential/beneficial
- ✅ **Result**: 10/10 jobs sync to ZEP (was 0/10 before)

## 🧪 Test Before Tomorrow's Auto-Run

Once deployed, trigger manually to verify:

```bash
cd /Users/dankeegan/worker/apify-job-worker
python3 scripts/trigger_scrape.py
```

**Expected Output**:
```
✅ Workflow completed!
Jobs Scraped: 10
Jobs Classified: 10
Jobs Synced to ZEP: 10  ← KEY METRIC
Duration: ~45-60s
```

## 📊 Monitor Deployment

After deployment, check:

1. **Railway Logs**:
   ```bash
   railway logs
   ```
   Look for: `✅ LinkedIn Apify Job Worker Started Successfully`

2. **Temporal UI**:
   - https://cloud.temporal.io
   - Namespace: `quickstart-quest.zivkb`
   - Check for worker heartbeats

3. **Tomorrow at 10am**:
   - Schedule will auto-trigger
   - Monitor results in Temporal UI

## 🎯 Post-Deployment Checklist

- [ ] Service created in Railway
- [ ] Environment variables configured
- [ ] Worker starts successfully (check logs)
- [ ] Manual test scrape works
- [ ] ZEP sync shows 10/10 jobs
- [ ] Schedule ready for tomorrow 10am

---

**Status**: ✅ Code deployed to git, ready for Railway service creation
**Date**: December 9, 2025
