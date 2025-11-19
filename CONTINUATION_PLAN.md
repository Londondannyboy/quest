# Quest Platform - Continuation Plan

**Created**: 2025-11-19
**Status**: Article Creation Infrastructure Complete, Ready for Testing

---

## Current System State

### ✅ DEPLOYED AND WORKING

**Company Worker** (Railway: `company-worker`)
- CompanyCreationWorkflow - Full company profiling
- ArticleCreationWorkflow - NEW article generation
- All research activities (Serper, Exa, Crawl4AI, Firecrawl)
- Sequential images (Kontext Pro/Max)
- Zep hybrid integration (query before, sync after with ontology)
- Task Queue: `quest-company-queue`

**Gateway** (Railway: `gateway`)
- Company creation endpoint working
- Article creation endpoint needs testing

**Streamlit Dashboard** (Local)
- Company creation UI working
- Article creation UI NOT YET ADDED

---

## What Was Completed This Session

### 1. Fixed Deployment Issues
- Fixed Temporal activity name mismatches (aliases)
- Removed abandoned article-worker (deleted from Railway)
- Added Procfile for company-worker deployment

### 2. Article Creation Infrastructure
**NEW FILES**:
- `company-worker/src/models/article.py` - ArticlePayload model
- `company-worker/src/activities/generation/article_generation.py` - AI content generation
- `company-worker/src/workflows/article_creation.py` - Complete workflow
- `company-worker/ARTICLE_CREATION_PLAN.md` - Implementation details

**UPDATED FILES**:
- `company-worker/worker.py` - Registered ArticleCreationWorkflow + generate_article_content

### 3. Confirmed Zep Hybrid Integration
- Query BEFORE generation (episodes + nodes)
- Flexible narrative payload DURING generation
- Extract entities + sync to graph AFTER generation
- Project-level ontology (Company, Deal, Person)
- ONE episode with both narrative and structured data

---

## Article Creation Architecture

### Workflow: Research → Deep Crawl → Generate → Images

```
ArticleCreationWorkflow (8 phases, 5-10 minutes)
│
├─ Phase 1: Research Topic
│  ├─ Serper: News search
│  └─ Exa: Deep research
│
├─ Phase 2: Crawl Discovered URLs
│  └─ Crawl4AI: ALL URLs (avoid paywalls)
│
├─ Phase 3: Query Zep Context
│
├─ Phase 4: Generate Article
│  └─ Gemini 2.5 Flash with rich context
│
├─ Phase 5: Analyze Sections
│  └─ Sentiment + visual moments
│
├─ Phase 6: Generate Sequential Images
│  └─ Kontext Pro: 3-5 contextual images
│
├─ Phase 7: Save to Database (TODO)
│
└─ Phase 8: Sync to Zep (TODO)
```

### Article Types Supported
- **News**: "Goldman Sachs acquiring startup X"
- **Guides**: "Digital Nomad Visa in Greece"
- **Comparisons**: "Top 10 Placement Agents in UK"

### Cost Per Article: ~$0.20
- Serper: $0.04
- Exa: $0.04
- Gemini: $0.015
- Images (5): $0.10

---

## TODO: Remaining Implementation

### Priority 1: Test Article Workflow (30 min)

- [ ] Test ArticleCreationWorkflow via Temporal UI
- [ ] Test input:
```json
{
  "topic": "Goldman Sachs acquires AI startup",
  "article_type": "news",
  "app": "placement",
  "target_word_count": 1500,
  "jurisdiction": "UK",
  "generate_images": true,
  "num_research_sources": 10
}
```
- [ ] Verify research phase works
- [ ] Verify article generation works
- [ ] Verify image generation works
- [ ] Check Temporal logs for any errors

### Priority 2: Streamlit Article UI (2-3 hours)

Add to `company-worker/dashboard.py`:

- [ ] Article creation form:
  - Topic input
  - Article type dropdown (news, guide, comparison)
  - App dropdown (placement, relocation)
  - Word count slider (500-3000)
  - Generate button

- [ ] Article list view:
  - Table with title, type, word count, date
  - Thumbnail images

- [ ] Article detail view:
  - Rendered markdown
  - Inline images
  - Company mentions

### Priority 3: Database Integration (2 hours)

- [ ] Create `save_article_to_neon` activity
- [ ] Create articles table if not exists
- [ ] Create article_companies junction table
- [ ] Update workflow to save article

### Priority 4: Gateway Endpoint (1 hour)

- [ ] Add/update `/v1/workflows/article-creation` route
- [ ] Test from curl/Postman
- [ ] Connect Streamlit to gateway

---

## Key File Locations

### Article Creation
```
company-worker/
├── src/
│   ├── models/
│   │   └── article.py              ← ArticlePayload model
│   ├── activities/
│   │   └── generation/
│   │       └── article_generation.py   ← AI content generation
│   └── workflows/
│       └── article_creation.py     ← ArticleCreationWorkflow
├── worker.py                       ← Both workflows registered
└── ARTICLE_CREATION_PLAN.md        ← Detailed implementation plan
```

### Company Creation (Reference)
```
company-worker/
├── src/
│   ├── models/
│   │   ├── payload_v2.py           ← CompanyPayload
│   │   └── research.py             ← ResearchData
│   ├── activities/
│   │   ├── generation/
│   │   │   └── profile_generation_v2.py
│   │   ├── research/
│   │   │   ├── serper.py
│   │   │   ├── exa.py
│   │   │   ├── crawl.py
│   │   │   └── crawl4ai_service.py
│   │   └── media/
│   │       └── sequential_images.py ← Already works for articles!
│   └── workflows/
│       └── company_creation.py
└── dashboard.py                    ← Streamlit UI
```

### Zep Integration
```
company-worker/src/
├── models/
│   └── zep_ontology.py             ← Entity types (Company, Deal, Person)
└── activities/storage/
    ├── zep_integration.py          ← Query + sync activities
    └── zep_entity_extraction.py    ← Extract entities from narrative
```

---

## Testing Commands

### Test Article Workflow via Temporal UI

1. Go to: https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows
2. Click "Start Workflow"
3. Workflow Type: `ArticleCreationWorkflow`
4. Task Queue: `quest-company-queue`
5. Input:
```json
{
  "topic": "Goldman Sachs acquires AI startup for $500M",
  "article_type": "news",
  "app": "placement",
  "target_word_count": 1500,
  "jurisdiction": "UK",
  "generate_images": false,
  "num_research_sources": 5
}
```

**Start with `generate_images: false` to test faster!**

### Test Company Workflow

Use Streamlit dashboard: http://localhost:8501

Or via Temporal UI with:
```json
{
  "url": "https://evercore.com",
  "category": "placement_agent",
  "jurisdiction": "US",
  "app": "placement"
}
```

---

## Configuration Reference

### Environment Variables (company-worker/.env)
```
TEMPORAL_ADDRESS=europe-west3.gcp.api.temporal.io:7233
TEMPORAL_NAMESPACE=quickstart-quest.zivkb
TEMPORAL_API_KEY=<set>
TEMPORAL_TASK_QUEUE=quest-company-queue

DATABASE_URL=<set>

GOOGLE_API_KEY=<set>
ANTHROPIC_API_KEY=<set>

SERPER_API_KEY=<set>
EXA_API_KEY=<set>
FIRECRAWL_API_KEY=<set>

REPLICATE_API_TOKEN=<set>
CLOUDINARY_URL=<set>

ZEP_API_KEY=<set>

CRAWL4AI_SERVICE_URL=<set>
```

### Railway Services
- `company-worker`: Root directory = `company-worker`
- `gateway`: Root directory = `gateway`

---

## Potential Issues & Solutions

### 1. Activity Not Registered Error
**Symptom**: "Activity function X is not registered"
**Solution**: Check worker.py imports and activities list

### 2. Temporal Nondeterminism
**Symptom**: "Activity type mismatch" error
**Solution**: Use activity aliases or cancel old workflows

### 3. Railway "No start command"
**Symptom**: Deployment fails
**Solution**: Ensure Procfile exists with `worker: python worker.py`

### 4. Image Generation Fails
**Symptom**: Images not generating
**Solution**: Check REPLICATE_API_TOKEN and CLOUDINARY_URL

---

## Next Session Quick Start

1. **Check Railway deployments** are healthy
2. **Run Streamlit**: `cd company-worker && streamlit run dashboard.py`
3. **Test article workflow** via Temporal UI (without images first)
4. **Add Streamlit article UI** if workflow works
5. **Implement database save** for articles

---

## Summary

**COMPLETED**:
- ✅ Article creation infrastructure (model, activity, workflow)
- ✅ Registered in worker
- ✅ Deployed to Railway
- ✅ Zep hybrid integration confirmed

**NEXT**:
- 🔲 Test article workflow
- 🔲 Add Streamlit article UI
- 🔲 Database integration
- 🔲 Gateway endpoint

**ESTIMATED TIME**: 4-6 hours to complete

---

**Ready to test!** Start with the article workflow in Temporal UI without images to verify it works.
