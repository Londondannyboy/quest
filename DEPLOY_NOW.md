# Deploy Quest to Railway - Quick Start

Follow these steps to deploy Quest in the next 15 minutes.

---

## Step 1: Create Railway Project (2 minutes)

1. **Open Railway Dashboard:**
   - Go to: https://railway.app/dashboard
   - You're already logged in as Dan Keegan ✅

2. **Create New Project:**
   - Click "New Project"
   - Select "Empty Project"
   - Name it: `quest`

---

## Step 2: Create Gateway Service (3 minutes)

1. **Add Gateway Service:**
   - In your `quest` project, click "+ New"
   - Select "GitHub Repo"
   - Choose: `Londondannyboy/quest`
   - Click "Add Variables" (we'll add them in Step 4)
   - Click "Deploy"

2. **Configure Gateway:**
   - Click the service after it's created
   - Go to "Settings" tab
   - Set **Service Name**: `quest-gateway`
   - Set **Root Directory**: `gateway`
   - Set **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Click "Networking" → Generate Domain → ✅ Enable
   - Save your domain URL (e.g., `quest-gateway-production-xxx.up.railway.app`)

---

## Step 3: Create Worker Service (3 minutes)

1. **Add Worker Service:**
   - In same `quest` project, click "+ New" again
   - Select "GitHub Repo"
   - Choose: `Londondannyboy/quest` (yes, same repo)
   - Click "Deploy"

2. **Configure Worker:**
   - Click the new service
   - Go to "Settings" tab
   - Set **Service Name**: `quest-worker`
   - Set **Root Directory**: `worker`
   - Set **Start Command**: `python worker.py`
   - Keep domain generation OFF (internal service)

---

## Step 4: Set Environment Variables (5 minutes)

### For BOTH Services (Gateway + Worker):

Click on each service → "Variables" tab → "Raw Editor" → Paste this:

```bash
# Temporal Cloud
TEMPORAL_ADDRESS=europe-west3.gcp.api.temporal.io:7233
TEMPORAL_NAMESPACE=quickstart-quest.zivkb
TEMPORAL_API_KEY=your-temporal-api-key-here
TEMPORAL_TASK_QUEUE=quest-content-queue

# Database
DATABASE_URL=postgresql://neondb_owner:npg_Q9VMTIX2eHws@ep-steep-wildflower-abrkgyqu-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require

# AI Services
GOOGLE_API_KEY=your-gemini-api-key-here

# Research APIs
SERPER_API_KEY=your-serper-api-key-here
TAVILY_API_KEY=your-tavily-api-key-here

# Environment
ENVIRONMENT=production
LOG_LEVEL=info
```

### Additional for Gateway Only:

```bash
# API Security
API_KEY=quest-production-secret-key-change-this-to-something-secure

# CORS (optional)
CORS_ORIGINS=*
```

**Click "Save" after pasting**

---

## Step 5: Deploy & Test (2 minutes)

Both services should auto-deploy after setting variables.

### Check Logs:

**Gateway:**
- Click `quest-gateway` service
- Go to "Deployments" tab
- Watch for: `✅ Gateway ready to accept requests`

**Worker:**
- Click `quest-worker` service
- Go to "Deployments" tab
- Watch for: `🚀 Quest Worker Started Successfully!`

---

## Step 6: Test Your Deployment

### Get Your Gateway URL:

Go to `quest-gateway` → "Settings" → "Networking" → Copy your domain

### Test Health Check:

```bash
curl https://your-gateway-url.up.railway.app/health
```

Should return:
```json
{"status":"healthy","timestamp":"..."}
```

### Trigger Your First Article:

```bash
curl -X POST https://your-gateway-url.up.railway.app/v1/workflows/article \
  -H "X-API-Key: quest-production-secret-key-change-this-to-something-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Private Equity UK Q4 2025 Test",
    "app": "placement",
    "target_word_count": 1500
  }'
```

Save the `workflow_id` from the response.

### Check Status:

```bash
curl https://your-gateway-url.up.railway.app/v1/workflows/YOUR_WORKFLOW_ID/status \
  -H "X-API-Key: your-api-key-here"
```

### Monitor in Temporal:

https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows

---

## Troubleshooting

### Gateway Returns 503:
- Check Variables tab → Verify `TEMPORAL_ADDRESS`, `TEMPORAL_NAMESPACE`, `TEMPORAL_API_KEY`
- Check Deployments tab → Look for connection errors

### Worker Not Starting:
- Check Variables tab → Verify all required vars are set
- Check Deployments tab → Look for import errors or missing dependencies

### Database Connection Failed:
- Verify `DATABASE_URL` includes `?sslmode=require`
- Test locally: `psql $DATABASE_URL`

---

## You're Done! 🎉

Your Quest system is now live on Railway with:
- ✅ Public HTTP API (gateway)
- ✅ Background worker (worker)
- ✅ Connected to Temporal Cloud
- ✅ Connected to Neon database
- ✅ Ready to generate content

**Next Steps:**
1. Test generating an article for placement
2. Test generating an article for relocation
3. Monitor costs and performance
4. Check articles in database

---

## Quick Reference

**Railway Dashboard:** https://railway.app/dashboard
**Temporal Cloud:** https://cloud.temporal.io
**Your Gateway:** https://your-gateway-url.up.railway.app/docs

**Need Help?** See `RAILWAY_DEPLOYMENT.md` for detailed troubleshooting.
