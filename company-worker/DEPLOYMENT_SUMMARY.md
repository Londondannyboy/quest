# Company Worker - Fixes Applied & Deployment Steps

## ✅ Fixes Applied (Code Changes)

### 1. **AI Profile Generation - Fixed**
**File**: `src/activities/generation/profile_generation.py`
**Problem**: AI was too conservative, leaving all fields empty
**Solution**: Updated system prompt to:
- Require description and tagline
- Encourage synthesis and inference from available data
- Prioritize extracting key information over perfectionism
- Changed from "leave fields null" to "synthesize information"

### 2. **Zep Sync - Fixed**
**File**: `src/activities/storage/zep_integration.py`
**Problem**: Not returning episode_id from Zep response
**Solution**: Updated to:
- Capture response from `client.graph.add()`
- Extract and return episode_id if available
- Add logging to debug Zep responses

## ⚠️ Still Required (Manual Actions)

### 3. **Add CLOUDINARY_URL to Railway**
**Action**: Go to Railway dashboard for company-worker and add:
```
CLOUDINARY_URL=cloudinary://653994623498835:MQQ61lBHOeaZsIopjOPlWX1ITBw@dc7btom12
```

Without this, logo and featured image generation will fail.

## Deployment Steps

### Option A: Deploy via Git (Recommended)
```bash
cd /Users/dankeegan/quest/company-worker
git add .
git commit -m "Fix AI profile generation and Zep sync

- Update AI system prompt to be more directive and require key fields
- Fix Zep sync to properly capture and return episode_id
- Add comprehensive logging for debugging"
git push origin main
```

Railway will auto-deploy on push.

### Option B: Railway CLI Deploy
```bash
cd /Users/dankeegan/quest/company-worker
railway up
```

## Testing After Deployment

Test with a new company to verify all fixes:

```python
import asyncio
from temporalio.client import Client

async def test_ares():
    client = await Client.connect(
        'europe-west3.gcp.api.temporal.io:7233',
        namespace='quickstart-quest.zivkb',
        api_key='[KEY]',
        tls=True
    )

    result = await client.execute_workflow(
        'CompanyCreationWorkflow',
        args=[{
            'url': 'https://www.ares.com',
            'category': 'placement_agent',
            'jurisdiction': 'United States',
            'app': 'placement',
            'force_update': False
        }],
        id=f'test-ares-{int(time.time())}',
        task_queue='quest-company-queue'
    )

    print(f"✅ Status: {result.get('status')}")
    print(f"✅ Completeness: {result.get('data_completeness')}%")
    print(f"✅ Zep Graph ID: {result.get('zep_graph_id')}")
    print(f"✅ Name: {result.get('name')}")

asyncio.run(test_ares())
```

## Expected Results After Fixes

| Metric | Before | After (Expected) |
|--------|--------|------------------|
| Data Completeness | 29.4% | 70-85% |
| Description | null | 2-3 paragraphs |
| Tagline | null | 1 sentence |
| Headquarters | null | City, Country |
| Industry | null | Industry name |
| Services | [] | 3-10 items |
| Zep Graph ID | null | "finance-knowledge" or episode_id |
| Logo URL | null | Cloudinary URL |
| Featured Image | null | Cloudinary URL |

## Verification Checklist

After deploying and testing:
- [ ] CLOUDINARY_URL added to Railway environment
- [ ] Code changes committed and pushed
- [ ] Railway deployment successful
- [ ] Test company creation completes successfully
- [ ] Data completeness > 70%
- [ ] Description and tagline populated
- [ ] Zep Graph ID returned (not null)
- [ ] Logo and featured image URLs present

## Troubleshooting

### If completeness is still low:
1. Check Railway logs for AI generation errors
2. Verify Gemini API key is valid
3. Consider switching to Claude (see FIXES_NEEDED.md Option B)

### If Zep sync still returns null:
1. Check ZEP_API_KEY in Railway
2. Verify graph_id "finance-knowledge" exists in Zep
3. Check Railway logs for Zep errors

### If images still missing:
1. Verify CLOUDINARY_URL is set correctly
2. Check REPLICATE_API_TOKEN is valid
3. Review Railway logs for image generation errors

## Files Changed
- `src/activities/generation/profile_generation.py` - AI system prompt
- `src/activities/storage/zep_integration.py` - Zep sync return value
- `FIXES_NEEDED.md` - Comprehensive fix documentation
- `DEPLOYMENT_SUMMARY.md` - This file
