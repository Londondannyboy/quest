# Monorepo Deployment Guide

## Overview

The `company-worker` is part of the Quest monorepo. This guide explains how to deploy it as a separate Railway service while keeping it in the monorepo.

## Architecture

```
quest/ (GitHub repo)
├── gateway/              # FastAPI gateway service
├── worker/               # Original Quest worker
├── company-worker/       # New company profiling service (THIS ONE!)
└── shared/              # Shared models/utilities
```

## Railway Configuration

The company-worker has been configured for monorepo deployment:

1. **railway.json** - Contains `watchPatterns: ["company-worker/**"]`
2. **railway.toml** - Contains `watchPatterns = ["company-worker/**"]`
3. **Root Directory** - Must be set to `company-worker` in Railway dashboard

This ensures:
- Only rebuilds when `company-worker/**` files change
- Doesn't rebuild when other Quest services change
- Correct working directory for Python imports

## Deployment Options

### Option 1: Railway Dashboard (Easiest)

1. **Go to Railway Dashboard**
   - https://railway.app/dashboard

2. **Create New Service**
   - Click "New" → "GitHub Repo"
   - Select `Londondannyboy/quest`

3. **Configure Root Directory**
   - In service settings, find "Root Directory"
   - Set to: `company-worker`
   - This is CRITICAL - without it, Railway will try to build from repo root

4. **Set Environment Variables**
   - Add all variables from `.env.example`
   - See DEPLOYMENT.md for full list

5. **Deploy**
   - Railway will automatically:
     - Detect Python via `requirements.txt`
     - Use Railpack (Railway's preferred builder)
     - Run `python worker.py` via Procfile

### Option 2: Railway CLI

```bash
# From Quest root directory
cd ~/quest

# Login
railway login

# Link to your project (or create new)
railway link

# Option A: Deploy via service flag
railway up --service company-worker

# Option B: Deploy from within the directory
cd company-worker
railway up
```

**Important**: When using CLI, Railway will respect the `watchPatterns` in `railway.json`.

### Option 3: GitHub Actions (CI/CD)

Create `.github/workflows/deploy-company-worker.yml`:

```yaml
name: Deploy Company Worker

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

      - name: Install Railway CLI
        run: npm install -g @railway/cli

      - name: Deploy to Railway
        run: |
          cd company-worker
          railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

## Verify Deployment

After deployment, check:

1. **Service Logs**
   ```bash
   railway logs --service company-worker
   ```

   Should see:
   ```
   🏢 Company Worker - Starting...
   ✅ Connected to Temporal successfully
   🚀 Company Worker Started Successfully!
   ```

2. **Environment Variables**
   - Check all required vars are set
   - Use Railway dashboard or: `railway variables --service company-worker`

3. **Build Logs**
   - Verify Python 3.11 detected
   - Check all dependencies installed
   - Confirm worker.py executed

## Multiple Services in Quest Monorepo

Your Quest project can have multiple Railway services:

| Service | Root Directory | Port | Purpose |
|---------|---------------|------|---------|
| quest-gateway | `gateway` | 8000 | FastAPI HTTP API |
| quest-worker | `worker` | - | Original content worker |
| quest-company-worker | `company-worker` | - | Company profiling |

Each service:
- Has its own Railway service in the dashboard
- Builds independently
- Watches only its own directory
- Can have different environment variables

## Troubleshooting

### Issue: Builds entire Quest repo

**Solution**: Set Root Directory to `company-worker` in Railway dashboard

### Issue: Can't find modules (ImportError)

**Solution**: Check Root Directory is set correctly. Python imports should work from `company-worker/` as root.

### Issue: Changes not triggering rebuild

**Solution**: Verify `watchPatterns` in `railway.json`:
```json
{
  "build": {
    "watchPatterns": ["company-worker/**"]
  }
}
```

### Issue: Wrong start command

**Solution**: Should be `python worker.py` (not `python company-worker/worker.py`)

## Local Development

When developing locally, always work from the `company-worker` directory:

```bash
cd ~/quest/company-worker

# Create venv
python -m venv venv
source venv/bin/activate

# Install deps
pip install -r requirements.txt

# Run worker
python worker.py
```

## Environment Variables

Each Railway service maintains its own environment variables:

- **company-worker** needs: Temporal, Database, AI services, etc.
- **gateway** needs: API keys, Temporal connection
- **worker** needs: Different set based on its requirements

No need to duplicate variables between services unless they're shared.

## Cost Considerations

Having separate Railway services:
- ✅ Better isolation
- ✅ Independent scaling
- ✅ Clearer logs and metrics
- ⚠️ Each service counts toward Railway pricing

Estimated costs:
- company-worker: $5-10/month (low CPU, always running)
- Total Quest project: $15-25/month (all services)

## Best Practices

1. **Always set Root Directory** when creating Railway service
2. **Use watchPatterns** to limit rebuilds
3. **Test locally first** before deploying
4. **Monitor logs** after deployment
5. **Use Railway CLI** for quick deployments
6. **Document env vars** in each service's README

## Deployment Checklist

- [ ] Root Directory set to `company-worker` in Railway
- [ ] All environment variables configured
- [ ] watchPatterns configured in railway.json
- [ ] Service builds successfully
- [ ] Worker connects to Temporal
- [ ] Test workflow executes successfully
- [ ] Logs show no errors

## Support

If deployment issues persist:
- Check Railway dashboard service logs
- Verify Root Directory setting
- Review railway.json configuration
- Test locally first
- Check Quest main repository issues
