# Flux Kontext Sequential Images - Deployment Guide

## 🎉 Implementation Status: READY TO DEPLOY

All code is implemented and ready for testing. Follow these steps to deploy.

---

## What's Been Built

### ✅ Completed:
1. **Smart sentiment analysis** with business context awareness (layoffs, acquisitions, deals)
2. **3-stage sentiment tracking** (overall + opening/middle/climax)
3. **Tone-matched image generation** (no smiling execs for layoffs!)
4. **Kontext Max for companies** (featured/hero only)
5. **Kontext Pro for articles** (all images)
6. **Company workflow integrated**
7. **Worker activities registered**
8. **Environment configured**

### 📋 Remaining (Manual Steps):
1. Run database migration
2. Test with real company
3. Monitor costs and quality

---

## Deployment Steps

### Step 1: Run Database Migration

Connect to your Neon database and run:

```bash
# Option A: Using psql
psql "$DATABASE_URL" < /Users/dankeegan/quest/company-worker/migrations/add_sequential_images.sql

# Option B: Using Neon CLI (if you have it)
neon sql --file /Users/dankeegan/quest/company-worker/migrations/add_sequential_images.sql

# Option C: Copy and paste SQL
# Open the migration file and run it in Neon SQL Editor:
# https://console.neon.tech/
```

**What this does:**
- Adds 28 image columns to `articles` table
- Adds 28 image columns to `companies` table
- Creates indexes for performance
- Adds comments for documentation

**Verify migration:**
```sql
-- Check articles table
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'articles'
AND column_name LIKE '%image%';

-- Should return: featured_image_url, featured_image_alt, hero_image_url, etc.
```

### Step 2: Verify Environment Variables

Check that Flux API key is set:

```bash
cd /Users/dankeegan/quest/company-worker
cat .env | grep FLUX
```

Should show:
```
FLUX_API_KEY=add1e152-4975-49ef-a89f-00c7ce812969
FLUX_MODEL=kontext-pro
GENERATE_SEQUENTIAL_IMAGES=true
```

### Step 3: Restart Worker

If you have a running worker, restart it to pick up new activities:

```bash
# Stop current worker (Ctrl+C if running in terminal)
# Or:
pkill -f "python.*worker.py"

# Start worker
cd /Users/dankeegan/quest/company-worker
python worker.py
```

**You should see the new activities registered:**
- `generate_flux_image`
- `generate_sequential_article_images`
- `generate_company_contextual_images`
- `analyze_article_sections`

### Step 4: Test with Real Company

Create a test company to verify image generation:

```bash
# Using Gateway API (if running)
curl -X POST http://localhost:8000/v1/workflows/company \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.example-company.com",
    "category": "placement",
    "app": "placement"
  }'

# Or use Temporal UI to start workflow manually
```

**Expected output:**
- ✅ Company created successfully
- ✅ Two images generated (featured + hero)
- ✅ Both using Kontext Max
- ✅ Logo consistency maintained
- ✅ Total cost: ~$0.20 (2 images × $0.10 each for Max)

**Check in database:**
```sql
SELECT
  name,
  featured_image_url,
  hero_image_url,
  logo_url
FROM companies
ORDER BY created_at DESC
LIMIT 1;
```

### Step 5: Monitor First Run

Watch the Temporal workflow logs for:

```
Phase 7: Generating contextual brand images (Flux Kontext Max)
Generating company featured image with kontext-max
Flux image generated, uploading to Cloudinary...
Uploaded to Cloudinary: https://res.cloudinary.com/...
Generating company hero image with kontext-max
✅ Company creation complete (cost: $0.20)
```

### Step 6: Verify Image Quality

1. **Open featured image URL** - Should show professional business card design
2. **Open hero image URL** - Should show office/workspace maintaining same brand aesthetic
3. **Check visual consistency** - Hero should reference featured image's style

**What to look for:**
- ✅ Same brand aesthetic across both images
- ✅ Professional quality (Kontext Max is high-quality)
- ✅ Appropriate for social sharing (featured) and header (hero)
- ❌ No weird artifacts or style inconsistencies

---

## Cost Monitoring

### Per Company (Current):
```
Featured Image (Kontext Max):  $0.10
Hero Image (Kontext Max):      $0.10
─────────────────────────────────────
TOTAL:                         $0.20
```

### Monthly Estimates:
```
50 companies/month:   $10.00
100 companies/month:  $20.00
200 companies/month:  $40.00
```

**Compare to old setup (Flux Schnell):**
- Old: 1 image × $0.003 = $0.003/company
- New: 2 images × $0.10 = $0.20/company
- **Increase: ~$0.197 per company**

**But you get:**
- ✅ 2 images instead of 1
- ✅ Much higher quality (Kontext Max)
- ✅ Visual consistency via context chaining
- ✅ Better branding

---

## How It Works Now

### Company Workflow (Updated)

```
1-6. [Previous phases unchanged]

7. Generate Images (NEW - Kontext Max)
   ├─ analyze_article_sections (optional, for company context)
   ├─ generate_company_contextual_images
   │  ├─ Featured image (use logo as context) [KONTEXT MAX]
   │  └─ Hero image (use featured as context) [KONTEXT MAX]
   └─ Upload both to Cloudinary

8-10. [Save to DB, fetch articles, sync to Zep - unchanged]
```

### Key Changes:

**Old (Flux Schnell):**
```python
featured_image = await workflow.execute_activity(
    "generate_company_featured_image",  # Old activity
    args=[company_name, logo_url, country, founded_year],
    timeout=timedelta(minutes=2)
)
# Returns: {"url": "cloudinary_url", "cost": 0.003}
```

**New (Flux Kontext Max):**
```python
company_images = await workflow.execute_activity(
    "generate_company_contextual_images",  # New activity
    args=[
        company_id, company_name, logo_url,
        description, country, app,
        True  # use_max_for_featured
    ],
    timeout=timedelta(minutes=3)
)
# Returns: {
#   "featured_image_url": "url1",
#   "hero_image_url": "url2",
#   "total_cost": 0.20
# }
```

---

## Troubleshooting

### Issue: Worker won't start

**Error:** `ModuleNotFoundError: No module named 'pydantic_ai'`

**Fix:**
```bash
cd /Users/dankeegan/quest/company-worker
pip install pydantic-ai
```

**Error:** `ModuleNotFoundError: No module named 'httpx'`

**Fix:**
```bash
pip install httpx
```

### Issue: Migration fails

**Error:** `psql: command not found`

**Fix:** Use Neon SQL Editor instead:
1. Go to https://console.neon.tech/
2. Select your project
3. Go to SQL Editor
4. Copy contents of `/Users/dankeegan/quest/company-worker/migrations/add_sequential_images.sql`
5. Run it

### Issue: "FLUX_API_KEY not configured"

**Check:**
```bash
cat /Users/dankeegan/quest/company-worker/.env | grep FLUX_API_KEY
```

**Fix if missing:**
```bash
echo "FLUX_API_KEY=add1e152-4975-49ef-a89f-00c7ce812969" >> /Users/dankeegan/quest/company-worker/.env
```

### Issue: Images not generating

**Check logs for:**
```
ERROR: generate_company_contextual_images not found
```

**Fix:** Worker needs restart to pick up new activities:
```bash
pkill -f "python.*worker.py"
cd /Users/dankeegan/quest/company-worker
python worker.py
```

### Issue: "Input image not found" (Kontext context chaining)

**Cause:** Featured image failed, so hero image has no context

**Check:** Look for featured image generation errors in logs

**Common causes:**
- Cloudinary upload failed
- Flux API timeout
- Invalid logo URL

**Fix:** Ensure Cloudinary is configured:
```bash
cat /Users/dankeegan/quest/company-worker/.env | grep CLOUDINARY_URL
```

### Issue: Images look inconsistent

**Possible causes:**
1. **Context not being passed** - Check logs for "context_image_url"
2. **Different models used** - Both should be "kontext-max" for companies
3. **Prompt too long** - Shortened automatically, but might lose detail

**Debug:**
```python
# Check activity logs
workflow.logger.info(f"Using model: {model}")
workflow.logger.info(f"Context image: {context_image_url}")
```

---

## Rollback Plan

If something goes wrong, you can rollback:

### 1. Revert Workflow Changes

```bash
cd /Users/dankeegan/quest/company-worker
git diff src/workflows/company_creation.py

# If you need to rollback:
git checkout HEAD -- src/workflows/company_creation.py
```

### 2. Use Old Image Generation

Edit workflow to use old activity:

```python
# Change:
company_images = await workflow.execute_activity(
    "generate_company_contextual_images",
    ...
)

# Back to:
featured_image = await workflow.execute_activity(
    "generate_company_featured_image",
    ...
)
```

### 3. Database Columns Stay

Migration adds columns but they're nullable - old code will ignore them.

---

## Next: Article Integration (Optional)

Articles are **not yet integrated** - that requires:
1. Finding article generation workflow
2. Adding `generate_sequential_article_images` activity
3. Using Kontext Pro (not Max) for articles
4. Testing with real articles

**Cost estimate for articles:**
- 5 images × $0.04 (Kontext Pro) = $0.20 per article

Do you want me to integrate articles too, or test companies first?

---

## Success Criteria

### ✅ Deployment Successful If:
1. Database migration applied (28 new columns per table)
2. Worker starts with new activities registered
3. Company workflow completes successfully
4. Two images generated (featured + hero)
5. Both images uploaded to Cloudinary
6. Images show visual consistency
7. Total cost ~$0.20 per company

### ⚠️ Known Limitations:
- Articles not yet integrated (manual step)
- First run may be slower (cold start)
- Kontext Max takes 30-60s per image

---

## Files Modified

✅ **New Files (6):**
1. `company-worker/migrations/add_sequential_images.sql`
2. `company-worker/src/activities/articles/analyze_sections.py`
3. `company-worker/src/activities/media/flux_api_client.py`
4. `company-worker/src/activities/media/sequential_images.py`
5. `test_flux_kontext.py`
6. `DEPLOYMENT_GUIDE.md` (this file)

✅ **Modified Files (6):**
1. `company-worker/src/workflows/company_creation.py` - Integrated new image generation
2. `company-worker/worker.py` - Registered new activities
3. `company-worker/src/utils/config.py` - Added Flux settings
4. `company-worker/.env` - Added Flux API key
5. `shared/models.py` - Extended Article model
6. `company-worker/src/models/payload_v2.py` - Extended CompanyPayload

---

## Support

**Test Command:**
```bash
cd /Users/dankeegan/quest
python test_flux_kontext.py
```

**Check Logs:**
- Temporal UI: https://cloud.temporal.io/
- Worker logs: Check terminal where worker is running
- Database: Neon Console

**Questions?**
- Check `FLUX_KONTEXT_IMPLEMENTATION.md` for detailed docs
- Review test results from `test_flux_kontext.py`
- Check Temporal workflow execution logs

---

🚀 **Ready to deploy!** Run the migration, restart the worker, and create a test company to see the magic happen!
