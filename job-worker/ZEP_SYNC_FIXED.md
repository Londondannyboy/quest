# ZEP Sync Fixed - Job Skill Graphs Working

## Summary of Changes

Fixed the ZEP knowledge graph sync to properly save and retrieve job data with skill relationships. The system now creates entity graphs that can power skill-based features on Fractional.quest.

## What Was Fixed

### 1. **save_jobs_to_zep Activity** (`src/activities/classification.py`)

**Before:**
```python
# Used JSON format - no entity extraction
await zep.graph.add(
    graph_id="jobs",
    type="json",  # ❌ Wrong - doesn't extract entities
    data=json.dumps(job_node)
)
```

**After:**
```python
# Uses text episodes with entity hints for proper extraction
episode_text = f"""Job Posting: {job_title} at {company_name}

The company {company_name} has posted a position for {job_title}...

Required Skills:
- Python (essential)
- FastAPI (essential)
- AWS (beneficial)
...
"""

await zep.graph.add(
    graph_id="jobs",
    type="text",  # ✅ Correct - ZEP extracts entities and relationships
    data=episode_text
)
```

**Key improvements:**
- Changed from `type="json"` to `type="text"` for entity extraction
- Structured text with clear entity hints (company names, skills, locations)
- Added skill importance levels (essential/beneficial)
- Included job descriptions and metadata
- Better deduplication by job URL

### 2. **New Retrieval Functions** (`src/activities/zep_retrieval.py`)

Created three new Temporal activities for retrieving data from the ZEP graph:

#### `get_job_skill_graph(job_id: str)`
Retrieves the skill graph for a specific job, including:
- Required skills with importance levels
- Related jobs that use similar skills
- Skill relationships

**Use case:** Display "Skills Required" and "Similar Jobs" on job detail pages

#### `get_skills_for_company(company_name: str)`
Gets aggregated skills across all jobs at a company:
- Top skills the company looks for
- Skill frequency counts
- Skills sorted by importance

**Use case:** Company profile pages showing "Skills We Value"

#### `search_jobs_by_skills(skill_names: list[str])`
Finds jobs that require specific skills:
- Search by one or multiple skills
- Returns matching jobs
- Relevance scoring

**Use case:** "Find jobs using Python and AWS" searches

## Testing

### 1. Test ZEP Sync Standalone

```bash
cd /Users/dankeegan/worker/job-worker
source .venv/bin/activate
python test_zep_complete.py
```

This tests:
- Creating a graph
- Adding 5 sample jobs with skills
- Searching for jobs and skills

### 2. Test Full Temporal Workflow

```bash
cd /Users/dankeegan/worker/job-worker
source .venv/bin/activate
python test_temporal_workflow.py
```

This tests:
- Full scraping → classification → ZEP sync pipeline
- Real jobs from a Greenhouse board
- Verifies jobs are saved to ZEP

### 3. Expected Results

After running the workflow, you should see:
```
✅ Workflow completed successfully!

📊 Results:
   Jobs found: 10
   Jobs deep scraped: 10
   Jobs classified: 10
   Jobs saved to ZEP: 10  ← This should be > 0 now!
   ZEP skipped duplicates: 0
```

## Integration with Fractional.quest

### Display Skill Graph on Job Pages

```typescript
// Example Next.js API route
import { Client } from '@temporalio/client';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const jobId = searchParams.get('jobId');

  const client = new Client({
    /* connection config */
  });

  const result = await client.workflow.execute('get_job_skill_graph', {
    args: [jobId],
    taskQueue: 'fractional-jobs-queue',
  });

  return Response.json(result);
}
```

### Example Response

```json
{
  "job_id": "12345",
  "skills": [
    {
      "name": "Python",
      "importance": "essential",
      "category": "technical"
    },
    {
      "name": "AWS",
      "importance": "beneficial",
      "category": "technical"
    }
  ],
  "related_jobs": [
    {
      "title": "Backend Engineer",
      "company": "TechCorp",
      "similarity_score": 0.85
    }
  ]
}
```

## Architecture

```
LinkedIn/Greenhouse Job Boards
         ↓
    Apify Scraper
         ↓
 Pydantic AI Classification (Gemini 2.0 Flash)
         ↓
    ┌────────────┐
    │            │
    ↓            ↓
Neon Database   ZEP Graph (NEW!)
(PostgreSQL)    (Knowledge Graph)
    │            │
    │            └─→ Entities:
    │                - Job nodes
    │                - Company nodes
    │                - Skill nodes
    │                - Location nodes
    │
    │            └─→ Relationships:
    │                - POSTED_BY (Job → Company)
    │                - REQUIRES_SKILL (Job → Skill)
    │                - LOCATED_IN (Job → Location)
    │
    ↓
Fractional.quest
(Next.js App)
    │
    └─→ Features:
        - Job skill badges
        - "Similar jobs" recommendations
        - "Find jobs by skill" search
        - Company skill profiles
```

## Deployment

The fix is ready to deploy to Railway. The worker will automatically use the new ZEP sync logic.

### Environment Variables Required

```bash
ZEP_API_KEY=z_...  # Already configured
TEMPORAL_API_KEY=...
DATABASE_URL=postgresql://...
GOOGLE_API_KEY=...  # For Gemini classification
```

### Deploy Command

```bash
cd /Users/dankeegan/worker/job-worker
git add .
git commit -m "Fix ZEP sync to use text episodes for entity extraction"
railway up
```

## Monitoring

After deployment, check Railway logs for:
```
Added job to ZEP: Senior Python Engineer at TechCorp
Retrieved skill graph: 5 skills, 3 related jobs
```

## Next Steps

1. ✅ ZEP sync fixed and tested
2. ⏳ Test with real Temporal workflow
3. ⏳ Deploy to Railway
4. ⏳ Add skill graph UI to Fractional.quest job pages
5. ⏳ Implement "Find by skills" search feature

## Technical Details

### Why Text Episodes Work Better

1. **Entity Extraction**: ZEP's NLP automatically identifies:
   - Company names: "TechCorp", "StartupCo"
   - Skills: "Python", "AWS", "React"
   - Locations: "London", "Remote"

2. **Relationship Creation**: ZEP infers relationships:
   - "TechCorp has posted a position for..." → POSTED_BY edge
   - "Required Skills: Python" → REQUIRES_SKILL edge

3. **Semantic Search**: Text allows natural language queries:
   - "Find Python jobs in London"
   - "Show me AWS engineer roles"

### Graph Structure

```
[Job: "Senior Python Engineer"]
    ├─ POSTED_BY ──→ [Company: "TechCorp"]
    ├─ REQUIRES_SKILL ──→ [Skill: "Python"]
    ├─ REQUIRES_SKILL ──→ [Skill: "FastAPI"]
    ├─ REQUIRES_SKILL ──→ [Skill: "AWS"]
    └─ LOCATED_IN ──→ [Location: "London"]
```

## Files Changed

1. `/Users/dankeegan/worker/job-worker/src/activities/classification.py`
   - Updated `save_jobs_to_zep` activity (lines 220-288)

2. `/Users/dankeegan/worker/job-worker/src/activities/zep_retrieval.py`
   - New file with 3 retrieval activities

3. `/Users/dankeegan/worker/job-worker/src/activities/__init__.py`
   - Added exports for new retrieval functions

## Testing Files Created

1. `test_zep_mcp.py` - Basic ZEP functionality test
2. `test_zep_complete.py` - Multi-job workflow test
3. `test_temporal_workflow.py` - Full Temporal integration test

---

**Status**: ✅ Ready to test and deploy
**Date**: December 9, 2025
