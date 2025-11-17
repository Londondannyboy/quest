# Company Worker Fixes Needed

## Issue Summary
The CompanyCreationWorkflow is running successfully with Temporal, but has three critical issues:

1. ❌ **AI Profile Generation**: Extracting no data despite scrapers working
2. ❌ **Zep Integration**: Not syncing to knowledge graph (returns None)
3. ❌ **Image Generation**: Logo and featured images not being created

## Test Results from Lazard
```json
{
  "scrapers_working": {
    "firecrawl": "✅ 10 pages, $0.10",
    "serper": "✅ 10 articles, $0.04",
    "exa": "✅ 1 result, $0.04",
    "crawl4ai": "❌ 0 pages (failed)"
  },
  "ai_extraction": {
    "description": null,
    "tagline": null,
    "headquarters": null,
    "industry": null,
    "services": [],
    "executives": []
  },
  "completeness": "29.4%",
  "zep_graph_id": null
}
```

## Fix #1: Add CLOUDINARY_URL to Railway

**Current State**: Railway has separate components but not the combined URL
```bash
CLOUDINARY_CLOUD_NAME="dc7btom12"
CLOUDINARY_API_KEY="653994623498835"
CLOUDINARY_API_SECRET="MQQ61lBHOeaZsIopjOPlWX1ITBw"
```

**Action Required**: Add this environment variable in Railway dashboard:
```bash
CLOUDINARY_URL=cloudinary://653994623498835:MQQ61lBHOeaZsIopjOPlWX1ITBw@dc7btom12
```

## Fix #2: Improve AI Profile Generation

**File**: `src/activities/generation/profile_generation.py`

**Problem**: Gemini 2.5 Flash is too conservative and extracting nothing

**Solution Options**:

### Option A: Make System Prompt More Directive
Change line 46-67 to be more assertive:
```python
system_prompt="""You are an expert company profiler.

Your task is to generate comprehensive company profiles from research data.

CRITICAL: You MUST extract and include information even if you need to infer it from context.

EXTRACTION RULES:
1. **description**: Write 2-3 paragraphs based on ALL available data
2. **tagline**: Create a clear 1-sentence summary
3. **headquarters**: Extract from website footer, about page, or news articles
4. **industry**: Infer from services and category
5. **services**: List what the company does based on website content
6. **executives**: Extract from about/team pages
7. **hero_stats**: Extract founded_year, employee count from any mention

QUALITY OVER PERFECTION:
- It's better to include inferred information than leave fields empty
- Use website content, news articles, and Exa research to fill gaps
- Only leave fields null if absolutely no information exists

Your output must follow the CompanyPayload schema."""
```

### Option B: Switch to Claude (More Thorough)
Change line 39 in config.py `get_ai_model()`:
```python
@classmethod
def get_ai_model(cls) -> tuple[str, str]:
    """Get preferred AI model for Pydantic AI"""
    if cls.ANTHROPIC_API_KEY:
        return ("anthropic", "claude-3-5-sonnet-20241022")  # More thorough
    elif cls.GOOGLE_API_KEY:
        return ("google", "gemini-2.5-flash")
    # ...
```

### Option C: Add Logging to Debug
Add logging to see what's being passed to the AI:
```python
# After line 71 in profile_generation.py
context = build_research_context(research)
activity.logger.info(f"Context length: {len(context)} chars")
activity.logger.info(f"Context preview: {context[:500]}")

# Generate profile
result = await company_agent.run(context)
```

## Fix #3: Fix Zep Sync Return Value

**File**: `src/activities/storage/zep_integration.py`

**Problem**: Line 147-157 doesn't return the graph_id properly

**Current Code**:
```python
await client.graph.add(
    graph_id=graph_id,
    data=graph_data
)

return {
    "graph_id": graph_id,  # This just echoes the input!
    "success": True
}
```

**Fixed Code**:
```python
# Add to Zep using app-specific organizational graph
response = await client.graph.add(
    graph_id=graph_id,
    data=graph_data
)

activity.logger.info(f"Zep response: {response}")

return {
    "graph_id": graph_id,  # Use organizational graph ID
    "episode_id": getattr(response, 'episode_id', None) if response else None,
    "success": True
}
```

## Fix #4: Fix Crawl4AI Integration

**Current State**: Crawl4AI is failing (0 pages)

**Action**: Check `src/activities/research/crawl.py` for errors:
- Ensure Playwright is installed
- Check browser configuration
- Add fallback to Firecrawl-only if Crawl4AI fails

## Deployment Steps

1. **Add CLOUDINARY_URL** to Railway (via dashboard)
2. **Update profile_generation.py** with Option A (more directive prompt)
3. **Update zep_integration.py** with proper return
4. **Add logging** to debug AI generation
5. **Redeploy** to Railway
6. **Test** with a new company

## Testing Command

After fixes are deployed, test with:
```bash
python3 -c "
import asyncio
from temporalio.client import Client

async def test():
    client = await Client.connect(
        'europe-west3.gcp.api.temporal.io:7233',
        namespace='quickstart-quest.zivkb',
        api_key='[TEMPORAL_KEY]',
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
        id='test-ares-' + str(int(time.time())),
        task_queue='quest-company-queue'
    )

    print(f'Completeness: {result.get(\"data_completeness\")}%')
    print(f'Zep Graph ID: {result.get(\"zep_graph_id\")}')

asyncio.run(test())
"
```

## Success Criteria

After fixes:
- ✅ Completeness score > 70%
- ✅ description, tagline, headquarters populated
- ✅ zep_graph_id returned (not None)
- ✅ logo_url and featured_image_url populated
- ✅ At least 3-5 services extracted
