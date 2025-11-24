# Quick Start Guide

Get the company worker running in 5 minutes!

## Prerequisites

- Python 3.11+
- All API keys ready (see below)
- Temporal Cloud account
- Neon PostgreSQL database

## Step 1: Get API Keys

You need these API keys:

1. **Temporal Cloud** - https://cloud.temporal.io
   - Create namespace
   - Get API key

2. **Google Gemini** - https://aistudio.google.com
   - Create API key
   - Enable Gemini API

3. **Serper.dev** - https://serper.dev
   - Sign up
   - Get API key
   - $50 free credit

4. **Exa** - https://exa.ai
   - Sign up
   - Get API key

5. **Replicate** - https://replicate.com
   - Sign up
   - Get API token
   - Add payment method

6. **Cloudinary** - https://cloudinary.com
   - Sign up (free tier)
   - Get cloudinary URL

7. **Zep Cloud** - https://www.getzep.com
   - Sign up
   - Get API key

## Step 2: Configure Environment

```bash
cd ~/quest/company-worker

# Copy example env file
cp .env.example .env

# Edit .env and add all your API keys
nano .env
```

Fill in these required variables:
```env
TEMPORAL_API_KEY=your-temporal-api-key
DATABASE_URL=postgresql://...
GOOGLE_API_KEY=your-gemini-key
SERPER_API_KEY=your-serper-key
EXA_API_KEY=your-exa-key
REPLICATE_API_TOKEN=your-replicate-token
CLOUDINARY_URL=cloudinary://...
ZEP_API_KEY=your-zep-key
```

## Step 3: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Run Worker

```bash
python worker.py
```

You should see:
```
🏢 Company Worker - Starting...
✅ All required environment variables present
✅ Connected to Temporal successfully
🚀 Company Worker Started Successfully!
✅ Worker is ready to process company creation workflows
```

## Step 5: Test It!

Create a test script `test_company.py`:

```python
import asyncio
from temporalio.client import Client

async def test_company():
    # Connect to Temporal
    client = await Client.connect(
        "europe-west3.gcp.api.temporal.io:7233",  # Your Temporal address
        namespace="your-namespace",
        api_key="your-api-key",
        tls=True
    )

    # Start workflow
    handle = await client.start_workflow(
        "CompanyCreationWorkflow",
        {
            "url": "https://evercore.com",
            "category": "placement_agent",
            "jurisdiction": "US",
            "app": "placement"
        },
        id=f"test-evercore-{int(asyncio.get_event_loop().time())}",
        task_queue="quest-company-queue"
    )

    print(f"Workflow started: {handle.id}")
    print("Waiting for result...")

    # Wait for result
    result = await handle.result()

    print("\n✅ Success!")
    print(f"Company: {result['name']}")
    print(f"Slug: {result['slug']}")
    print(f"Completeness: {result['data_completeness']}%")
    print(f"Cost: ${result['research_cost']:.4f}")
    print(f"Articles: {result['related_articles_count']}")

asyncio.run(test_company())
```

Run it:
```bash
python test_company.py
```

## Expected Output

The workflow will:
1. ✅ Normalize URL (5s)
2. ✅ Research in parallel (60s)
3. ✅ Check ambiguity (10s)
4. ✅ Generate profile (15s)
5. ✅ Create images (15s)
6. ✅ Save to database (5s)
7. ✅ Fetch articles (5s)
8. ✅ Sync to Zep (5s)

Total: ~90-120 seconds

Result:
```json
{
  "status": "created",
  "company_id": "uuid",
  "slug": "evercore",
  "name": "Evercore Inc.",
  "logo_url": "https://...",
  "featured_image_url": "https://...",
  "research_cost": 0.08,
  "research_confidence": 0.92,
  "data_completeness": 85.5,
  "related_articles_count": 0,
  "zep_graph_id": "company-uuid"
}
```

## Troubleshooting

### "Missing required environment variables"
- Check `.env` file exists
- Verify all API keys are set
- Check for typos in variable names

### "Failed to connect to Temporal"
- Verify Temporal API key
- Check namespace name
- Ensure network connectivity

### "Activity failed"
- Check API key for specific service
- Verify service has quota/credits
- Review activity logs

### "Low completeness scores"
- Normal for some companies
- Check ambiguity signals
- May need manual review

## Next Steps

1. **Deploy to Railway** - See `DEPLOYMENT.md`
2. **Add more companies** - Test with different categories
3. **Monitor costs** - Track per-company costs
4. **Integrate with frontend** - Display company profiles

## Common Commands

```bash
# Start worker
python worker.py

# Install new dependency
pip install package-name
pip freeze > requirements.txt

# Check logs
# (Worker logs to stdout)

# Stop worker
# Press Ctrl+C
```

## Quick Reference

| Service | Cost | Purpose |
|---------|------|---------|
| Serper | $0.02 | News search |
| Exa | $0.04 | Deep research |
| Gemini | $0.01 | AI profile |
| Replicate | $0.003 | Images |
| Crawl4AI | Free | Web scraping |
| Cloudinary | Free | Image hosting |

**Total per company: $0.07-0.13**

## Support

- Documentation: `README.md`
- Deployment: `DEPLOYMENT.md`
- Implementation: `IMPLEMENTATION_SUMMARY.md`

---

**You're all set!** 🚀

Now you can create comprehensive company profiles in 90-150 seconds!
