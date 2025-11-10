# Quest - Development Guide

## Quick Start

### Prerequisites

- Python 3.11+
- Temporal Cloud account
- Neon PostgreSQL database
- Google Gemini API key
- Serper API key (for news search)

### Environment Setup

1. **Copy environment template:**
```bash
cp .env.example .env
```

2. **Fill in your API keys:**
```bash
# Temporal Cloud
TEMPORAL_ADDRESS=europe-west3.gcp.api.temporal.io:7233
TEMPORAL_NAMESPACE=quickstart-quest.zivkb
TEMPORAL_API_KEY=your-temporal-api-key
TEMPORAL_TASK_QUEUE=quest-content-queue

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# AI Services
GOOGLE_API_KEY=your-gemini-api-key
REPLICATE_API_TOKEN=your-replicate-token

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Memory
SUPERMEMORY_API_KEY=your-supermemory-key
ZEP_API_KEY=your-zep-key

# External APIs
SERPER_API_KEY=your-serper-key
```

### Local Development

#### Worker (Temporal)

```bash
# Install dependencies
cd worker
pip install -r requirements.txt

# Run worker
python worker.py
```

#### Gateway (FastAPI)

```bash
# Install dependencies
cd gateway
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload --port 8000
```

### Project Structure

```
quest/
├── gateway/                  # FastAPI HTTP API
│   ├── main.py              # App entry point
│   ├── routers/
│   │   ├── workflows.py     # Workflow triggers
│   │   ├── status.py        # Status queries
│   │   └── health.py        # Health check
│   ├── auth.py              # API key validation
│   ├── temporal_client.py   # Temporal singleton
│   └── requirements.txt
│
├── worker/                   # Temporal Python worker
│   ├── worker.py            # Entry point
│   ├── workflows/
│   │   └── newsroom.py      # Article generation
│   ├── agents/
│   │   ├── editorial.py     # Brief generation
│   │   └── writer.py        # Article writing
│   ├── activities/
│   │   ├── research.py      # News search + scraping
│   │   ├── database.py      # Neon operations
│   │   └── memory.py        # SuperMemory + Zep
│   ├── models.py            # Pydantic models
│   └── requirements.txt
│
└── shared/                   # Shared types (optional)
    ├── article.py
    └── models.py
```

## Testing

### Test Worker Locally

```bash
# Start worker
cd worker
python worker.py
```

### Test Gateway Locally

```bash
# Start gateway
cd gateway
uvicorn main:app --reload

# Test health endpoint
curl http://localhost:8000/health

# Trigger workflow
curl -X POST http://localhost:8000/v1/workflows/article \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"app": "placement", "topic": "Private Equity UK Q4 2025"}'
```

## Deployment

### Railway Setup

1. **Create Railway project:**
```bash
railway login
railway init
```

2. **Configure services:**
   - `quest-gateway` (root: gateway/)
   - `quest-worker` (root: worker/)

3. **Set environment variables** in Railway dashboard

4. **Deploy:**
```bash
railway up
```

### Monitoring

- **Temporal Cloud:** https://cloud.temporal.io
- **Railway Logs:** `railway logs --service worker`
- **Database:** Neon dashboard

## Common Tasks

### Generate Article Manually

```python
from temporalio.client import Client

async def trigger_article():
    client = await Client.connect("temporal-cloud-address")

    result = await client.execute_workflow(
        "NewsroomWorkflow",
        args=["Private Equity News UK"],
        id=f"article-{datetime.now().isoformat()}",
        task_queue="quest-content-queue"
    )

    print(f"Article generated: {result}")
```

### Check Database

```bash
# Connect to Neon
psql $DATABASE_URL

# List recent articles
SELECT id, title, app, published_at FROM articles ORDER BY published_at DESC LIMIT 10;
```

### View Workflow in Temporal

1. Open Temporal Cloud dashboard
2. Navigate to your namespace
3. Find workflow by ID
4. View execution history and logs

## Troubleshooting

### Worker not connecting to Temporal

- Check `TEMPORAL_ADDRESS`, `TEMPORAL_NAMESPACE`, `TEMPORAL_API_KEY`
- Verify network connectivity
- Check Temporal Cloud service status

### Database connection failed

- Verify `DATABASE_URL` format
- Check Neon dashboard for connection limits
- Test with `psql $DATABASE_URL`

### Image generation failing

- Check `REPLICATE_API_TOKEN`
- Verify Cloudinary credentials
- Check Replicate service status

### Gateway 401 errors

- Verify `API_KEY` in `.env`
- Check `X-API-Key` header in request
- Ensure key matches between gateway and client

## Development Workflow

1. **Create feature branch:**
```bash
git checkout -b feature/your-feature
```

2. **Make changes and test locally**

3. **Commit with descriptive message:**
```bash
git add .
git commit -m "feat: add multi-app support to workflow"
```

4. **Push and deploy:**
```bash
git push origin feature/your-feature
railway deploy
```

## Next Steps

See [README.md](./README.md) for architecture overview
See [MIGRATION.md](./MIGRATION.md) for extraction details

---

**Last Updated:** November 10, 2025
**Status:** Phase 1 - Setup Complete
