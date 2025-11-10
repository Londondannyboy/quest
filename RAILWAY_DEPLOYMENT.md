# Quest - Railway Deployment Guide

Complete guide for deploying Quest to Railway with two services (worker + gateway).

---

## Prerequisites

1. **Railway account** - Sign up at https://railway.app
2. **GitHub repo** - Your quest repo (already done ✅)
3. **Environment variables** - Have your API keys ready

---

## Deployment Steps

### Step 1: Create Railway Project

```bash
# Install Railway CLI (if not already installed)
npm install -g @railway/cli

# Login to Railway
railway login

# Link to GitHub repo (in quest directory)
cd /Users/dankeegan/quest
railway init

# This will create a new Railway project and link it
```

**Or use Railway Dashboard:**
1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose `Londondannyboy/quest`

---

### Step 2: Create Two Services

Railway needs two separate services for worker and gateway.

#### Option A: Via Railway Dashboard (Recommended)

1. **Create Gateway Service:**
   - In your project, click "+ New"
   - Select "GitHub Repo"
   - Choose `Londondannyboy/quest`
   - Name it: `quest-gateway`
   - Root Directory: `/gateway`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Generate Domain: ✅ Enable (for public access)

2. **Create Worker Service:**
   - In same project, click "+ New" again
   - Select "GitHub Repo"
   - Choose `Londondannyboy/quest` again
   - Name it: `quest-worker`
   - Root Directory: `/worker`
   - Start Command: `python worker.py`
   - Generate Domain: ❌ Disable (internal only)

#### Option B: Via Railway CLI

```bash
# Create gateway service
railway service create quest-gateway

# Create worker service
railway service create quest-worker
```

---

### Step 3: Configure Environment Variables

Set these variables for **BOTH** services in Railway dashboard.

#### Both Services Need:

```bash
# Temporal Cloud (REQUIRED)
TEMPORAL_ADDRESS=europe-west3.gcp.api.temporal.io:7233
TEMPORAL_NAMESPACE=quickstart-quest.zivkb
TEMPORAL_API_KEY=your-temporal-api-key-here
TEMPORAL_TASK_QUEUE=quest-content-queue

# Database (REQUIRED)
DATABASE_URL=postgresql://neondb_owner:npg_Q9VMTIX2eHws@ep-steep-wildflower-abrkgyqu-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require

# AI Services (REQUIRED)
GOOGLE_API_KEY=your-gemini-api-key-here

# Research APIs (REQUIRED)
SERPER_API_KEY=your-serper-api-key-here
TAVILY_API_KEY=your-tavily-api-key-here

# Environment
ENVIRONMENT=production
LOG_LEVEL=info
```

#### Gateway Service Only:

```bash
# API Security (REQUIRED for production)
API_KEY=quest-production-secret-key-change-this

# CORS (Optional)
CORS_ORIGINS=https://placement.quest,https://relocation.quest
```

#### Worker Service Only:

```bash
# Image Generation (Optional - Phase 2)
REPLICATE_API_TOKEN=your-replicate-token
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-key
CLOUDINARY_API_SECRET=your-cloudinary-secret

# Memory Systems (Optional - Phase 2)
SUPERMEMORY_API_KEY=your-supermemory-key
ZEP_API_KEY=your-zep-key
```

**To set via Railway Dashboard:**
1. Select service (quest-gateway or quest-worker)
2. Go to "Variables" tab
3. Click "New Variable"
4. Add each variable (or use "Raw Editor" for bulk paste)

**To set via Railway CLI:**
```bash
# Set for gateway
railway service quest-gateway
railway variables set TEMPORAL_ADDRESS="europe-west3.gcp.api.temporal.io:7233"
railway variables set TEMPORAL_NAMESPACE="quickstart-quest.zivkb"
# ... etc

# Set for worker
railway service quest-worker
railway variables set TEMPORAL_ADDRESS="europe-west3.gcp.api.temporal.io:7233"
# ... etc
```

---

### Step 4: Configure Service Settings

#### Gateway Service Settings:

**In Railway Dashboard → quest-gateway:**

1. **Settings → Service:**
   - Service Name: `quest-gateway`
   - Root Directory: `/gateway`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. **Settings → Networking:**
   - Generate Domain: ✅ Enable
   - Copy the generated URL (e.g., `quest-gateway-production.up.railway.app`)

3. **Settings → Health Check:**
   - Health Check Path: `/health`
   - Health Check Timeout: 30 seconds

#### Worker Service Settings:

**In Railway Dashboard → quest-worker:**

1. **Settings → Service:**
   - Service Name: `quest-worker`
   - Root Directory: `/worker`
   - Start Command: `python worker.py`

2. **Settings → Networking:**
   - Generate Domain: ❌ Disable (internal only)

3. **No health check needed** (long-running worker)

---

### Step 5: Deploy

#### Auto-Deploy (Recommended):

Railway auto-deploys on git push by default.

```bash
# Just push to GitHub
git push

# Railway will automatically:
# 1. Detect the push
# 2. Build both services
# 3. Deploy them
```

#### Manual Deploy:

```bash
# Deploy gateway
railway service quest-gateway
railway up

# Deploy worker
railway service quest-worker
railway up
```

---

### Step 6: Verify Deployment

#### Check Gateway:

```bash
# Get your Railway URL (from dashboard or CLI)
GATEWAY_URL="https://quest-gateway-production.up.railway.app"

# Test health endpoint
curl $GATEWAY_URL/health

# Should return:
# {"status":"healthy","timestamp":"...","version":"1.0.0","environment":"production"}

# Test readiness (validates Temporal connection)
curl $GATEWAY_URL/ready

# View API docs
open $GATEWAY_URL/docs
```

#### Check Worker Logs:

```bash
# Via CLI
railway service quest-worker
railway logs

# Should see:
# 🚀 Quest Worker Started Successfully!
# ✅ Connected to Temporal
# ✅ Worker is ready to process workflows...
```

#### Check Gateway Logs:

```bash
railway service quest-gateway
railway logs

# Should see:
# 🚀 Quest Gateway starting...
# ✅ Gateway ready to accept requests
```

---

### Step 7: Test End-to-End

Trigger a workflow via HTTP:

```bash
# Get your gateway URL
GATEWAY_URL="https://quest-gateway-production.up.railway.app"

# Get your API key (from Railway variables)
API_KEY="your-api-key-here"

# Trigger article generation
curl -X POST $GATEWAY_URL/v1/workflows/article \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Private Equity UK Q4 2025",
    "app": "placement",
    "target_word_count": 1500
  }'

# Save the workflow_id from response

# Check status
curl -X GET "$GATEWAY_URL/v1/workflows/{workflow-id}/status" \
  -H "X-API-Key: $API_KEY"

# Monitor in Temporal Cloud
open "https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows"
```

---

## Troubleshooting

### Gateway Returns 503 Service Unavailable

**Problem:** Gateway can't connect to Temporal

**Solutions:**
1. Check `TEMPORAL_ADDRESS`, `TEMPORAL_NAMESPACE`, `TEMPORAL_API_KEY` are set correctly
2. Check Railway logs: `railway service quest-gateway && railway logs`
3. Verify Temporal Cloud credentials are valid

### Worker Not Processing Workflows

**Problem:** Worker not connected to Temporal

**Solutions:**
1. Check worker logs: `railway service quest-worker && railway logs`
2. Look for "Connected to Temporal" message
3. Verify `TEMPORAL_TASK_QUEUE` matches gateway (default: `quest-content-queue`)
4. Check all required env vars are set

### Database Connection Failed

**Problem:** Worker can't connect to Neon

**Solutions:**
1. Verify `DATABASE_URL` is correct (check Neon dashboard)
2. Ensure URL includes `?sslmode=require`
3. Test connection: `psql $DATABASE_URL`

### 401 Unauthorized on API Calls

**Problem:** API key not matching

**Solutions:**
1. Check `API_KEY` is set in gateway service
2. Verify you're including correct `X-API-Key` header
3. Check for typos or extra spaces

### Workflow Execution Failed

**Problem:** Activity errors during execution

**Solutions:**
1. Check worker logs for specific error
2. Common causes:
   - Missing `GOOGLE_API_KEY` → Can't generate article
   - Missing `SERPER_API_KEY` → Can't search news
   - Missing `TAVILY_API_KEY` → Can't scrape sources
3. View full workflow history in Temporal Cloud dashboard

---

## Monitoring

### Railway Dashboard

View real-time logs and metrics:
1. Go to Railway dashboard
2. Select service
3. View "Deployments" or "Metrics" tab

### Temporal Cloud Dashboard

Monitor workflow executions:
https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows

### Database Queries

Check published articles:

```bash
psql $DATABASE_URL -c "
SELECT
  title,
  app,
  word_count,
  published_at
FROM articles
WHERE status = 'published'
ORDER BY published_at DESC
LIMIT 10;
"
```

---

## Updating Deployment

### Push New Code:

```bash
# Make changes locally
git add .
git commit -m "Your changes"
git push

# Railway auto-deploys both services
```

### Update Environment Variables:

**Via Dashboard:**
1. Go to service
2. Variables tab
3. Edit or add variables
4. Service auto-restarts

**Via CLI:**
```bash
railway service quest-gateway
railway variables set NEW_VAR="value"
```

### Manual Restart:

**Via Dashboard:**
1. Go to service
2. Click "⋯" menu
3. Select "Restart"

**Via CLI:**
```bash
railway service quest-gateway
railway restart
```

---

## Cost Estimates

### Railway Costs

**Hobby Plan (Free):**
- $5 credit/month
- Good for testing

**Pro Plan ($20/month):**
- $20 credit included
- Additional usage billed
- Recommended for production

**Typical Usage:**
- Gateway: ~$5-10/month (public HTTP service)
- Worker: ~$5-10/month (background worker)
- **Total: ~$10-20/month**

### API Costs

**Per Article Generated (~$0.15-0.20):**
- Serper.dev: $0.003 (news search)
- Tavily: $0 (free tier)
- Gemini Flash: $0.01 (entity extraction)
- Gemini Pro: $0.10 (article generation)
- Temporal: Free (included)
- Neon: Free (included in plan)

**Monthly (100 articles):**
- API costs: ~$15-20
- Railway: ~$10-20
- **Total: ~$25-40/month**

---

## Next Steps After Deployment

1. ✅ Test workflow execution
2. ✅ Verify articles save to database
3. ✅ Check multi-app routing (placement vs relocation)
4. ✅ Generate test content for both apps
5. ✅ Monitor costs and performance
6. ⏳ Add SuperMemory (Phase 2)
7. ⏳ Add image generation (Phase 2)

---

## Quick Reference

### Railway URLs

- **Dashboard:** https://railway.app/dashboard
- **Gateway URL:** `https://quest-gateway-production.up.railway.app`
- **API Docs:** `https://quest-gateway-production.up.railway.app/docs`

### Important Commands

```bash
# View logs
railway logs --service quest-gateway
railway logs --service quest-worker

# Restart services
railway restart --service quest-gateway

# View variables
railway variables

# Deploy manually
railway up
```

---

**Status:** Ready to deploy!
**Time Required:** 15-30 minutes
**Difficulty:** Easy (mostly copy-paste)

Let me know when you're ready to start! 🚀
