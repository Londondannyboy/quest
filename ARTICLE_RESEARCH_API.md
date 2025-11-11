# ArticleWorkflow Research API

## Overview

The **ArticleWorkflow** is now accessible via Gateway at `/v1/workflows/article-research`. This endpoint uses **Exa-based research** for comprehensive, evergreen article creation, distinct from the news-based `/v1/workflows/article` endpoint.

## Key Differences

| Feature | `/v1/workflows/article` | `/v1/workflows/article-research` |
|---------|------------------------|----------------------------------|
| **Research Source** | Serper news search | Exa comprehensive research |
| **Content Type** | Breaking news, time-sensitive | Evergreen, guides, analysis |
| **Workflow** | PlacementWorkflow/RelocationWorkflow/ChiefOfStaffWorkflow (news-based) | ArticleWorkflow (Exa-based) |
| **Assessment** | Entity extraction from news | Research insights extraction |
| **Best For** | Current events, financial news, breaking stories | Topic guides, how-tos, company analysis, visa guides |

## API Endpoint

```
POST https://your-gateway.com/v1/workflows/article-research
```

### Authentication

Requires `X-API-Key` header.

### Request Body

```json
{
  "topic": "Digital Nomad Visa Portugal",
  "app": "relocation",
  "target_word_count": 2000,
  "num_research_sources": 7,
  "deep_crawl_enabled": true,
  "skip_zep_sync": false
}
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `topic` | string | ✅ Yes | - | Topic to research (min 3 chars) |
| `app` | string | No | `"placement"` | App context: placement, relocation, chief-of-staff |
| `target_word_count` | integer | No | `1500` | Target article length (300-5000) |
| `num_research_sources` | integer | No | `5` | Number of Exa sources (3-10) |
| `deep_crawl_enabled` | boolean | No | `false` | Enable FireCrawl deep scraping |
| `skip_zep_sync` | boolean | No | `false` | Skip knowledge base sync |

### Response

```json
{
  "workflow_id": "article-research-relocation-a1b2c3d4",
  "status": "started",
  "started_at": "2025-11-11T14:30:00Z",
  "topic": "Digital Nomad Visa Portugal",
  "app": "relocation",
  "message": "Article research workflow started with Exa. Use workflow_id to check status."
}
```

## Example Requests

### 1. Placement - Industry Guide

```bash
curl -X POST "https://your-gateway.com/v1/workflows/article-research" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Venture Capital Fund Structure and Economics",
    "app": "placement",
    "target_word_count": 2500,
    "num_research_sources": 8
  }'
```

### 2. Relocation - Visa Guide (with Deep Crawl)

```bash
curl -X POST "https://your-gateway.com/v1/workflows/article-research" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Digital Nomad Visa Portugal",
    "app": "relocation",
    "target_word_count": 1800,
    "num_research_sources": 6,
    "deep_crawl_enabled": true
  }'
```

### 3. Chief of Staff - Executive Strategy

```bash
curl -X POST "https://your-gateway.com/v1/workflows/article-research" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Executive leadership frameworks for chiefs of staff in 2025",
    "app": "chief-of-staff",
    "target_word_count": 1500,
    "num_research_sources": 5
  }'
```

### 4. Python Client

```python
import httpx

async def create_research_article():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://your-gateway.com/v1/workflows/article-research",
            headers={"X-API-Key": "your-api-key"},
            json={
                "topic": "Private Equity Dry Powder 2025",
                "app": "placement",
                "target_word_count": 1800,
                "num_research_sources": 6
            }
        )
        return response.json()

# Returns:
# {
#   "workflow_id": "article-research-placement-xyz123",
#   "status": "started",
#   ...
# }
```

## Checking Status

Use the workflow_id to check progress:

```bash
curl -X GET "https://your-gateway.com/v1/workflows/{workflow_id}/status" \
  -H "X-API-Key: your-api-key"
```

## When to Use Article Research vs Article

### Use `/article-research` (Exa-based) for:
- ✅ Evergreen content guides
- ✅ How-to articles and tutorials
- ✅ Company/product deep dives
- ✅ Visa and immigration guides
- ✅ Industry analysis and frameworks
- ✅ Topic-based research articles
- ✅ Reference materials

### Use `/article` (News-based) for:
- ✅ Breaking news coverage
- ✅ Recent financial deals
- ✅ Market updates
- ✅ Time-sensitive content
- ✅ Real-time event coverage

## App-Specific Behavior

The workflow adapts based on the `app` parameter:

### Placement
- **Focus**: Financial news, PE firms, M&A
- **Tone**: Professional, Bloomberg-style
- **Citations**: Financial sources preferred
- **Images**: Corporate, data visualization

### Relocation
- **Focus**: Expat guides, visa info, relocation
- **Tone**: Practical, helpful
- **Citations**: Government sources, expat resources
- **Images**: Lifestyle, destination imagery

### Chief of Staff
- **Focus**: Executive management, C-suite operations
- **Tone**: Strategic, authoritative
- **Citations**: HBR, McKinsey, Gartner
- **Images**: Executive, professional aesthetic

## Features

✅ **Exa Research**: High-quality sources with full content
✅ **Autoprompt**: Automatically optimizes search queries
✅ **Deep Crawl**: Optional FireCrawl for enhanced content
✅ **App-Aware**: Adapts tone, style, citations per app
✅ **Quality Scoring**: Automatic assessment
✅ **Image Generation**: App-specific imagery
✅ **Zep Integration**: Optional knowledge base sync

## Deployment

**Committed & Ready**:
- ✅ ArticleWorkflow in worker
- ✅ Gateway endpoint `/article-research`
- ✅ Exa research activities
- ✅ All dependencies configured

**Deploy both services**:
```bash
# Worker
railway up --service worker

# Gateway
railway up --service gateway
```

## Troubleshooting

### "Workflow not found: ArticleWorkflow"
- Ensure worker is deployed with latest changes
- Check worker logs for registration confirmation

### "EXA_API_KEY not set"
- Worker requires EXA_API_KEY environment variable
- Already configured in your production environment

### Low quality articles
- Increase `num_research_sources` for more citations
- Enable `deep_crawl_enabled` for deeper research
- Check topic is broad enough for research
