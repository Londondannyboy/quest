# ArticleWorkflow - Direct Article Creation

## Overview

The `ArticleWorkflow` is a new workflow that creates articles directly from any topic using Exa research, bypassing the news assessment pipeline entirely. Perfect for evergreen content, guides, and in-depth research articles.

## Key Differences from NewsroomWorkflow

| Feature | NewsroomWorkflow | ArticleWorkflow |
|---------|-----------------|-----------------|
| **Research Source** | Serper news search | Exa comprehensive research |
| **Content Type** | Breaking news, time-sensitive | Evergreen, guides, analysis |
| **Assessment** | Yes - relevance check | No - direct creation |
| **Crawling** | Tavily (required) | Exa + optional FireCrawl |
| **Speed** | Slower (9 stages) | Faster (7-9 stages) |

## Workflow Stages

1. **Exa Research** - Search high-quality sources with full content
2. **Deep Crawl** (optional) - Enhance with FireCrawl
3. **Extract Insights** - Entities, citations, findings (app-aware)
4. **Create Brief** - Article structure and angle
5. **Generate Article** - App-specific content generation
6. **Calculate Quality** - Quality score
7. **Generate Images** - App-aware image generation
8. **Save to Neon** - Database storage
9. **Zep Sync** (optional) - Knowledge base integration

## Usage

### API Endpoint

```bash
POST http://your-worker-api/workflows/article
```

### Request Body

```json
{
  "topic": "Digital Nomad Visa Portugal",
  "app": "placement",
  "target_word_count": 1500,
  "num_research_sources": 5,
  "deep_crawl_enabled": false,
  "skip_zep_sync": false
}
```

### Parameters

- **topic** (required): The topic to research and write about
- **app** (optional): App context - "placement", "relocation", etc. (default: "placement")
- **target_word_count** (optional): Target article length (default: 1500)
- **num_research_sources** (optional): Number of Exa sources (default: 5)
- **deep_crawl_enabled** (optional): Enable FireCrawl deep scraping (default: false)
- **skip_zep_sync** (optional): Skip knowledge base sync (default: false)

### cURL Example

```bash
curl -X POST "http://localhost:8000/workflows/article" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Digital Nomad Visa Portugal",
    "app": "relocation",
    "target_word_count": 2000,
    "num_research_sources": 7,
    "deep_crawl_enabled": true
  }'
```

### Python Example

```python
import httpx

async def create_article():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/workflows/article",
            json={
                "topic": "Private Equity Dry Powder 2025",
                "app": "placement",
                "target_word_count": 1800,
                "num_research_sources": 6
            }
        )
        return response.json()
```

## App-Aware Features

The workflow automatically adapts based on the `app` parameter:

### Placement App
- **Focus**: Financial news, PE firms, M&A
- **Tone**: Professional, Bloomberg-style
- **Citations**: Financial sources preferred
- **Images**: Corporate, data visualization aesthetic

### Relocation App
- **Focus**: Expat guides, visa information, relocation services
- **Tone**: Practical, helpful
- **Citations**: Government sources, expat resources
- **Images**: Lifestyle, destination imagery

## Environment Variables Required

```bash
# Required
EXA_API_KEY=your_exa_api_key
GOOGLE_API_KEY=your_gemini_api_key
DATABASE_URL=your_neon_postgres_url

# Optional (for enhanced features)
FIRECRAWL_API_KEY=your_firecrawl_key  # For deep crawling
REPLICATE_API_TOKEN=your_replicate_token  # For images
CLOUDINARY_CLOUD_NAME=your_cloudinary_name  # For image storage
CLOUDINARY_API_KEY=your_cloudinary_key
CLOUDINARY_API_SECRET=your_cloudinary_secret
ZEP_API_KEY=your_zep_key  # For knowledge base sync
```

## Example Use Cases

### 1. Placement - Industry Guide
```json
{
  "topic": "Venture Capital Fund Structure and Economics",
  "app": "placement",
  "target_word_count": 2500,
  "num_research_sources": 8
}
```

### 2. Relocation - Visa Guide
```json
{
  "topic": "Digital Nomad Visa Portugal",
  "app": "relocation",
  "target_word_count": 1800,
  "num_research_sources": 6,
  "deep_crawl_enabled": true
}
```

### 3. Placement - Company Analysis
```json
{
  "topic": "Goldman Sachs Asset Management Strategy",
  "app": "placement",
  "target_word_count": 1500,
  "num_research_sources": 5
}
```

## Exa Research Features

The workflow uses Exa's advanced features:

- **Autoprompt**: Automatically optimizes search queries
- **Full Content**: Retrieves complete article text
- **Summaries**: AI-generated summaries for context
- **Highlights**: Key passages extracted
- **Quality Filtering**: Only high-quality, authoritative sources

## Deep Crawl (Optional)

When `deep_crawl_enabled: true`:
- Takes top Exa result URLs
- Re-scrapes with FireCrawl for enhanced content
- Merges with Exa content for comprehensive research
- Best for: Complex topics requiring maximum depth

## Quality Scoring

Articles are automatically scored based on:
- Word count (target achievement)
- Citation count (minimum per app config)
- Content structure
- Research depth

Scores above the app's `auto_publish_threshold` can be auto-published.

## Monitoring

Check workflow status via Temporal UI:
- Workflow ID: `article-{app}-{topic-slug}-{random}`
- Task Queue: `quest-content-queue`
- Activities: Track Exa research, generation, image creation

## Troubleshooting

### "EXA_API_KEY not set"
- Add `EXA_API_KEY` to your environment variables
- Get an API key from https://exa.ai

### "No research results found"
- Topic may be too specific or obscure
- Try broader search terms
- Increase `num_research_sources`

### Image generation skipped
- Check `REPLICATE_API_TOKEN` is set
- Verify `CLOUDINARY_*` credentials
- Images are optional, article will still be created

### Low quality score
- Increase `num_research_sources` for more citations
- Enable `deep_crawl_enabled` for deeper research
- Check target word count is achievable for topic

## Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Set environment variables**: Add `EXA_API_KEY` and others
3. **Start worker**: `python worker.py`
4. **Start API**: `python api.py`
5. **Trigger workflow**: Use API endpoint or Temporal directly
