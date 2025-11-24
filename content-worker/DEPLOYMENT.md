# Deployment Guide

## Railway Deployment

### Prerequisites

1. Railway account: https://railway.app
2. Railway CLI installed: `npm install -g @railway/cli`
3. All API keys ready (see `.env.example`)

### Step 1: Create Railway Service (Monorepo Setup)

Since company-worker is part of the Quest monorepo, you need to create a separate Railway service for it:

**Option A: Using Railway Dashboard (Recommended)**

1. Go to Railway dashboard
2. Create new service from GitHub repo
3. Select your Quest repository
4. **Important**: Set "Root Directory" to `company-worker`
5. Railway will automatically detect Python and use Railpack (Railway's preferred builder)

**Option B: Using Railway CLI**

```bash
# From the Quest root directory
cd ~/quest

# Login to Railway
railway login

# Create/link to project
railway link

# Deploy company-worker service
# Railway will use the watchPatterns in railway.json to only watch company-worker/**
railway up --service company-worker
```

**Note**: The `railway.json` in `company-worker/` has `watchPatterns` configured to only trigger rebuilds when files in `company-worker/**` change.

### Step 2: Set Environment Variables

Set all required environment variables in Railway dashboard:

**Critical Variables:**
```bash
TEMPORAL_ADDRESS=europe-west3.gcp.api.temporal.io:7233
TEMPORAL_NAMESPACE=your-namespace
TEMPORAL_API_KEY=your-temporal-api-key
TEMPORAL_TASK_QUEUE=quest-company-queue

DATABASE_URL=postgresql://...

GOOGLE_API_KEY=your-gemini-key
SERPER_API_KEY=your-serper-key
EXA_API_KEY=your-exa-key
REPLICATE_API_TOKEN=your-replicate-token
CLOUDINARY_URL=cloudinary://...
ZEP_API_KEY=your-zep-key
```

**Optional:**
```bash
FIRECRAWL_API_KEY=your-firecrawl-key
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

Or use CLI:
```bash
railway variables set TEMPORAL_API_KEY=your-key
railway variables set DATABASE_URL=postgresql://...
# ... etc
```

### Step 3: Deploy

```bash
# Deploy from current directory
railway up

# Or push to Railway git
git push railway main
```

Railway will automatically:
1. Detect Python project
2. Install dependencies from `requirements.txt`
3. Run `python worker.py`

### Step 4: Verify Deployment

Check logs:
```bash
railway logs
```

You should see:
```
🏢 Company Worker - Starting...
✅ Connected to Temporal successfully
🚀 Company Worker Started Successfully!
✅ Worker is ready to process company creation workflows
```

### Step 5: Monitor

View service:
```bash
railway open
```

Check status:
```bash
railway status
```

View logs in real-time:
```bash
railway logs --follow
```

## Deployment Checklist

- [ ] All environment variables set
- [ ] Temporal Cloud accessible
- [ ] Database accessible (Neon)
- [ ] All API keys valid and have quota
- [ ] Worker starts without errors
- [ ] Can execute test workflow

## Test Deployment

Create a test workflow to verify everything works:

```python
from temporalio.client import Client

client = await Client.connect(
    "europe-west3.gcp.api.temporal.io:7233",
    namespace="your-namespace",
    api_key="your-api-key",
    tls=True
)

# Simple test
handle = await client.start_workflow(
    "CompanyCreationWorkflow",
    {
        "url": "https://evercore.com",
        "category": "placement_agent",
        "jurisdiction": "US",
        "app": "placement"
    },
    id=f"test-company-{int(time.time())}",
    task_queue="quest-company-queue"
)

result = await handle.result()
print(f"Success! Company created: {result['slug']}")
```

## Troubleshooting

### Worker won't start
```bash
railway logs
```

Check for:
- Missing environment variables
- Invalid API keys
- Database connection errors

### Can't connect to Temporal
- Verify TEMPORAL_API_KEY is correct
- Check namespace matches
- Ensure TLS is enabled

### Activities failing
- Check individual API keys
- Verify rate limits
- Review activity logs

### Out of memory
Railway default: 512MB RAM

If needed, upgrade plan or optimize:
- Reduce parallel activities
- Limit image generation
- Optimize data structures

## Environment-Specific Config

### Development (Local)
```bash
TEMPORAL_ADDRESS=localhost:7233
# No API key needed
# No TLS
```

### Staging
```bash
ENVIRONMENT=staging
LOG_LEVEL=debug
```

### Production
```bash
ENVIRONMENT=production
LOG_LEVEL=info
ENABLE_COST_ALERTS=true
```

## Scaling

Railway auto-scales based on CPU/memory.

For high volume:
1. Increase Railway plan
2. Consider multiple workers
3. Monitor costs per company

## Monitoring

### Key Metrics

- Workflow success rate
- Average execution time (target: <150s)
- Average cost per company (target: <$0.15)
- Data completeness scores (target: >70%)

### Logs to Watch

```
✅ Company creation complete: <slug> (cost: $X.XX, confidence: 0.XX)
```

### Alerts

Set up alerts for:
- Worker crashes
- High failure rates
- Cost spikes

## Rollback

If deployment fails:

```bash
# Rollback to previous deployment
railway rollback
```

## Multiple Environments

Create separate Railway services:
- `company-worker-dev`
- `company-worker-staging`
- `company-worker-prod`

Each with own environment variables.

## CI/CD

### GitHub Actions

```yaml
name: Deploy to Railway

on:
  push:
    branches: [main]
    paths:
      - 'company-worker/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm install -g @railway/cli
      - run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

## Cost Optimization

1. **Use Crawl4AI over Firecrawl** (free vs paid)
2. **Cache research results** (implement in future)
3. **Batch operations** where possible
4. **Monitor API usage** per service

Target: $3.50-6.50 per 50 companies/month

## Security

- Never commit `.env` file
- Rotate API keys regularly
- Use Railway secrets for sensitive data
- Monitor for unusual activity

## Support

If issues persist:
- Check Railway status: https://railway.statuspage.io
- Review logs: `railway logs`
- Contact Railway support
- Check Quest main repo issues
