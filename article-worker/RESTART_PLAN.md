# Article Worker - Restart Plan & Status

**Last Updated**: 2025-11-18
**Context**: ArticleCreationWorkflow implementation complete, deployment in progress

---

## 📊 Current Status

### ✅ COMPLETED

1. **Article Worker Service Created**
   - Location: `/Users/dankeegan/quest/article-worker/`
   - Structure: Complete with 40 files
   - Committed: Yes (commits: ff3b8af, e5fb54e, 2b6db34)
   - Pushed: Yes ✅

2. **Code Complete**
   - ✅ ArticleCreationWorkflow (11 phases, 5-12 min execution)
   - ✅ ArticleInput model (14 fields)
   - ✅ ArticlePayload model (100+ fields, 7 images)
   - ✅ 19 Activities (8 implemented, 11 stubbed)
   - ✅ Worker.py configured
   - ✅ All __init__.py files
   - ✅ Config files (requirements.txt, Procfile, railway.json, etc.)

3. **Gateway Endpoint Added**
   - ✅ Route: `/v1/workflows/article-creation`
   - ✅ File: `gateway/routers/workflows.py` (line 536+)
   - ✅ Committed: Yes (commit d3bd691, updated 2b6db34)
   - ✅ Pushed: Yes

4. **Configuration**
   - ✅ Single task queue: `quest-content-queue`
   - ✅ Both workers use same queue (simplified)
   - ✅ Syntax error fixed (line 408)

### 🚧 IN PROGRESS

1. **Railway Deployments**
   - ⚠️ article-worker: DEPLOYED with env vars set
   - ⚠️ gateway: NEEDS REDEPLOY to pick up new endpoint

### ❌ NOT STARTED

1. **Activities Need Implementation**
   - Content generation (AI with Gemini + Claude)
   - Image generation (Flux Kontext Max)
   - Section sentiment analysis (AI)
   - Company NER extraction
   - Playwright URL validation
   - Zep integration
   - Authoritative site crawling

---

## 🎯 IMMEDIATE TODO LIST

### Priority 1: Get Workflow Running (Today)

- [ ] **Redeploy Gateway on Railway**
  - Go to Railway dashboard
  - Find `gateway` service
  - Click "Redeploy" button
  - Wait 2-3 minutes

- [ ] **Test Via Gateway**
  ```bash
  curl -X POST "https://gateway-production-5e6f.up.railway.app/v1/workflows/article-creation" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: YOUR_KEY" \
    -d '{
      "topic": "Digital Nomad Visa Greece",
      "app": "relocation",
      "target_word_count": 500,
      "generate_images": false,
      "skip_zep_sync": true,
      "deep_crawl_enabled": false
    }'
  ```

- [ ] **Verify in Temporal UI**
  - Go to: https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows
  - Check workflow appears and starts
  - Watch which activities execute
  - Note which activities fail

### Priority 2: Implement Core Activities (This Week)

- [ ] **generate_article_content** (HIGH PRIORITY)
  - Copy pattern from company-worker `generate_company_profile_v2.py`
  - Use Gemini 2.5 Flash + Claude Sonnet 4.5
  - Generate: title, subtitle, markdown content, sections
  - Location: `article-worker/src/activities/generation/content_generation.py`

- [ ] **analyze_article_sections** (HIGH PRIORITY)
  - Copy from company-worker `analyze_sections.py`
  - Already exists but may need tweaking
  - Sentiment analysis per H2 section
  - Location: `article-worker/src/activities/articles/analyze_sections.py`

- [ ] **generate_article_contextual_images** (HIGH PRIORITY)
  - Copy from company-worker `sequential_images.py`
  - Adapt for articles (7 images vs 2)
  - Use section sentiment for context
  - Location: `article-worker/src/activities/generation/image_generation.py`

- [ ] **extract_company_mentions** (MEDIUM)
  - NER-based company extraction
  - Match to database
  - Calculate relevance scores
  - Location: `article-worker/src/activities/articles/company_extraction.py`

- [ ] **Playwright Activities** (MEDIUM)
  - `playwright_url_cleanse`
  - `playwright_clean_article_links`
  - Location: `article-worker/src/activities/validation/link_validator.py`

- [ ] **Zep Integration** (LOW - can skip initially)
  - `query_zep_for_article_context`
  - `sync_article_to_zep`
  - Location: `article-worker/src/activities/storage/zep_integration.py`

---

## 🔧 CONFIGURATION

### Railway Services

**article-worker**
- Service: `article-worker`
- Status: DEPLOYED ✅
- Root Directory: `article-worker`
- Start Command: `python worker.py`

**gateway**
- Service: `gateway`
- Status: NEEDS REDEPLOY ⚠️
- Root Directory: `gateway`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Environment Variables (article-worker)

**ALL VARIABLES SET ✅** (copied from company-worker):

```bash
# Temporal (CRITICAL - VERIFIED)
TEMPORAL_ADDRESS=europe-west3.gcp.api.temporal.io:7233
TEMPORAL_NAMESPACE=quickstart-quest.zivkb
TEMPORAL_API_KEY=<set>
TEMPORAL_TASK_QUEUE=quest-content-queue  # ← IMPORTANT!

# Database
DATABASE_URL=<set>

# AI Services
GOOGLE_API_KEY=<set>
ANTHROPIC_API_KEY=<set>

# Research APIs
SERPER_API_KEY=<set>
EXA_API_KEY=<set>
FIRECRAWL_API_KEY=<set>

# Image Services
REPLICATE_API_TOKEN=<set>
CLOUDINARY_URL=<set>

# Knowledge Graph
ZEP_API_KEY=<set>

# App Settings
ENVIRONMENT=production
```

---

## 🧪 TESTING WORKFLOW

### Method 1: Via Gateway (RECOMMENDED)

```bash
curl -X POST "https://gateway-production-5e6f.up.railway.app/v1/workflows/article-creation" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "topic": "Digital Nomad Visa Greece",
    "app": "relocation",
    "target_word_count": 500,
    "article_format": "article",
    "generate_images": false,
    "skip_zep_sync": true,
    "deep_crawl_enabled": false,
    "num_research_sources": 3,
    "auto_publish": false
  }'
```

**Expected Response:**
```json
{
  "workflow_id": "article-creation-relocation-...",
  "status": "started",
  "started_at": "2025-11-18T...",
  "topic": "Digital Nomad Visa Greece",
  "app": "relocation",
  "message": "Article creation workflow started on quest-content-queue..."
}
```

### Method 2: Via Temporal Cloud UI

1. Go to: https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows
2. Click "Start Workflow"
3. Settings:
   - Workflow Type: `ArticleCreationWorkflow`
   - Task Queue: `quest-content-queue`
4. Input: (same JSON as above)
5. Click "Start Workflow"

### Method 3: Via Local Script

```bash
cd /Users/dankeegan/quest/article-worker
python3 trigger_article.py  # Needs env vars set locally
```

---

## 📁 FILE STRUCTURE

```
quest/
├── article-worker/              ← NEW SERVICE
│   ├── src/
│   │   ├── workflows/
│   │   │   └── article_creation.py      ← 11-phase workflow ✅
│   │   ├── activities/
│   │   │   ├── normalize.py             ← ✅ Implemented
│   │   │   ├── research/
│   │   │   │   ├── serper.py           ← ✅ Implemented
│   │   │   │   ├── exa.py              ← ✅ Implemented
│   │   │   │   ├── crawl_news.py       ← ✅ Implemented
│   │   │   │   └── crawl_auth.py       ← 🚧 Stub
│   │   │   ├── generation/
│   │   │   │   ├── content_generation.py  ← 🚧 Stub - NEEDS IMPL
│   │   │   │   └── image_generation.py    ← 🚧 Stub - NEEDS IMPL
│   │   │   ├── articles/
│   │   │   │   ├── analyze_sections.py    ← 🚧 Stub - NEEDS IMPL
│   │   │   │   └── company_extraction.py  ← 🚧 Stub
│   │   │   ├── storage/
│   │   │   │   ├── neon_database.py       ← ✅ Implemented
│   │   │   │   └── zep_integration.py     ← 🚧 Stub
│   │   │   └── validation/
│   │   │       └── link_validator.py      ← 🚧 Stub
│   │   ├── models/
│   │   │   ├── article_input.py          ← ✅ Complete
│   │   │   └── article_payload.py        ← ✅ Complete
│   │   └── utils/
│   │       ├── config.py                 ← ✅ Complete
│   │       └── helpers.py                ← ✅ Complete
│   ├── worker.py                         ← ✅ Complete
│   ├── trigger_article.py                ← ✅ Test script
│   ├── requirements.txt                  ← ✅ Complete
│   ├── Procfile                          ← ✅ Complete
│   ├── railway.json                      ← ✅ Complete
│   ├── README.md                         ← ✅ Documentation
│   └── IMPLEMENTATION_SUMMARY.md         ← ✅ Details
│
├── gateway/
│   └── routers/
│       └── workflows.py          ← ✅ Updated (line 536+)
│
└── company-worker/               ← Reference implementation
    └── src/
        ├── activities/
        │   ├── generation/
        │   │   └── profile_generation_v2.py  ← Copy for content gen
        │   └── media/
        │       └── sequential_images.py      ← Copy for images
        └── ...
```

---

## 🐛 KNOWN ISSUES

### Issue 1: Gateway Not Deployed
- **Status**: Needs manual redeploy
- **Fix**: Redeploy gateway service on Railway
- **ETA**: 2-3 minutes

### Issue 2: Stubbed Activities
- **Status**: 11 activities return placeholder data
- **Impact**: Workflow will run but won't generate real content
- **Fix**: Implement activities (see Priority 2 todo list)
- **ETA**: 1-2 weeks for full implementation

### Issue 3: No Local Testing Environment
- **Status**: Can't test locally without env vars
- **Impact**: Must test via Railway/Temporal Cloud
- **Fix**: Create .env file locally (optional)

---

## 📈 SUCCESS METRICS

### Phase 1: Workflow Executes (Today)
- [x] Worker deploys successfully
- [x] Worker registers on quest-content-queue
- [ ] Workflow starts via gateway
- [ ] Activities execute (even if stubbed)
- [ ] Workflow completes without errors

### Phase 2: Content Generation (This Week)
- [ ] Real article content generated
- [ ] Sections with sentiment analysis
- [ ] Database entry created
- [ ] Basic completeness >60%

### Phase 3: Images & Polish (Next Week)
- [ ] 7 contextual images generated
- [ ] Company mentions extracted
- [ ] Zep sync working
- [ ] Completeness >90%

---

## 🚀 QUICK START COMMANDS

```bash
# Check git status
cd /Users/dankeegan/quest
git status
git log --oneline -5

# Test gateway endpoint (after redeploy)
curl -X POST "https://gateway-production-5e6f.up.railway.app/v1/workflows/article-creation" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: quest_2024_dev_key" \
  -d '{"topic":"Test Article","app":"relocation","target_word_count":500,"generate_images":false,"skip_zep_sync":true}'

# Check article-worker logs (need Railway login)
cd /Users/dankeegan/quest/article-worker
railway logs --service article-worker

# View Temporal workflows
open https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows
```

---

## 📞 NEXT SESSION CHECKLIST

When you restart, check:

1. **Is gateway redeployed?**
   - Check Railway dashboard
   - Test endpoint with curl

2. **Did the test workflow work?**
   - Check Temporal UI
   - Note which activities succeeded/failed

3. **What needs to be implemented?**
   - Start with `generate_article_content`
   - Copy from `company-worker/src/activities/generation/profile_generation_v2.py`
   - Adapt for articles

4. **Any errors?**
   - Check Railway logs
   - Check Temporal workflow history

---

## 💡 KEY INSIGHTS

1. **Single Queue Simplification**
   - Both workers use `quest-content-queue`
   - Simpler than separate queues
   - Working for company-worker already

2. **Copy-Paste Strategy**
   - Don't reinvent the wheel
   - Copy working code from company-worker
   - Adapt for articles (topic vs URL, 7 images vs 2, etc.)

3. **Incremental Testing**
   - Start with minimal input
   - Disable images, Zep, deep crawling
   - Get basic flow working first
   - Add features incrementally

4. **Railway Auto-Deploy**
   - Pushes to main trigger auto-deploy
   - But sometimes needs manual redeploy
   - Check deployment status in dashboard

---

**END OF RESTART PLAN**

✅ Ready to resume! Start with: Redeploy gateway → Test endpoint → Implement content generation
