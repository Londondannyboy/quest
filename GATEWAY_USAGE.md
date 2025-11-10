# Quest Gateway - API Usage Guide

## Quick Start

### 1. Set Environment Variables

```bash
# Required
export TEMPORAL_ADDRESS="europe-west3.gcp.api.temporal.io:7233"
export TEMPORAL_NAMESPACE="quickstart-quest.zivkb"
export TEMPORAL_API_KEY="your-temporal-api-key"
export TEMPORAL_TASK_QUEUE="quest-content-queue"

# Optional (for authentication)
export API_KEY="quest-secret-key"

# Optional (for CORS)
export CORS_ORIGINS="*"  # or specific origins
```

### 2. Start Gateway

```bash
cd gateway
python3 main.py
```

Gateway will start on http://localhost:8000

### 3. Test Endpoints

**Health Check:**
```bash
curl http://localhost:8000/health
```

**API Documentation:**
Open http://localhost:8000/docs in your browser

---

## API Endpoints

### Health & Status

#### GET /health
Basic health check (no auth required)

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T12:00:00.000Z",
  "version": "1.0.0",
  "environment": "development"
}
```

#### GET /ready
Readiness check (validates Temporal connection)

```bash
curl http://localhost:8000/ready
```

#### GET /
API information

```bash
curl http://localhost:8000/
```

---

### Workflow Triggers

#### POST /v1/workflows/article
Trigger article generation workflow

**Request:**
```bash
curl -X POST http://localhost:8000/v1/workflows/article \
  -H "X-API-Key: quest-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Private Equity UK Q4 2025",
    "app": "placement",
    "target_word_count": 1500,
    "auto_approve": true
  }'
```

**Response:**
```json
{
  "workflow_id": "article-placement-123e4567-e89b-12d3-a456-426614174000",
  "status": "started",
  "started_at": "2025-11-10T12:00:00.000Z",
  "topic": "Private Equity UK Q4 2025",
  "app": "placement",
  "message": "Article generation workflow started. Use workflow_id to check status."
}
```

**Parameters:**
- `topic` (required): Topic to generate article about
- `app` (optional): App/site identifier (default: "placement")
  - Options: placement, relocation, rainmaker, gtm
- `target_word_count` (optional): Target word count (default: 1500, range: 300-5000)
- `auto_approve` (optional): Skip manual approval (default: true)

#### GET /v1/workflows/{workflow_id}/status
Check workflow status (non-blocking)

```bash
curl -X GET http://localhost:8000/v1/workflows/article-placement-123/status \
  -H "X-API-Key: quest-secret-key"
```

**Response (Running):**
```json
{
  "workflow_id": "article-placement-123",
  "status": "running",
  "result": null,
  "error": null
}
```

**Response (Completed):**
```json
{
  "workflow_id": "article-placement-123",
  "status": "completed",
  "result": {
    "id": "01HKJX...",
    "title": "Private Equity UK Sees Record Fundraising in Q4 2025",
    "slug": "private-equity-uk-record-fundraising-q4-2025",
    "word_count": 1523,
    "app": "placement",
    "status": "published"
  },
  "error": null
}
```

**Response (Failed):**
```json
{
  "workflow_id": "article-placement-123",
  "status": "failed",
  "result": null,
  "error": "Workflow execution failed: ..."
}
```

#### GET /v1/workflows/{workflow_id}/result
Get workflow result (blocks until complete)

```bash
curl -X GET http://localhost:8000/v1/workflows/article-placement-123/result \
  -H "X-API-Key: quest-secret-key"
```

**Note:** This endpoint will wait for the workflow to complete. Use `/status` for non-blocking checks.

---

## Examples

### Generate Placement Article

```bash
curl -X POST http://localhost:8000/v1/workflows/article \
  -H "X-API-Key: quest-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Top PE Placement Agents 2025",
    "app": "placement",
    "target_word_count": 2000
  }'
```

### Generate Relocation Article

```bash
curl -X POST http://localhost:8000/v1/workflows/article \
  -H "X-API-Key: quest-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Best Cities for Relocating to UK",
    "app": "relocation",
    "target_word_count": 1500
  }'
```

### Check Status

```bash
# Save workflow ID from trigger response
WORKFLOW_ID="article-placement-123e4567-e89b-12d3-a456-426614174000"

# Check status
curl -X GET "http://localhost:8000/v1/workflows/${WORKFLOW_ID}/status" \
  -H "X-API-Key: quest-secret-key"
```

### Wait for Result

```bash
# This will block until workflow completes
curl -X GET "http://localhost:8000/v1/workflows/${WORKFLOW_ID}/result" \
  -H "X-API-Key: quest-secret-key"
```

---

## Authentication

The gateway uses API key authentication via the `X-API-Key` header.

**Set your API key:**
```bash
export API_KEY="your-secret-key-here"
```

**Include in requests:**
```bash
curl -H "X-API-Key: your-secret-key-here" ...
```

**Development Mode (No Auth):**
If `API_KEY` is not set, the gateway runs in development mode with no authentication.
⚠️ **Do not use this in production!**

---

## Error Responses

### 401 Unauthorized
Missing or invalid API key

```json
{
  "detail": "API key is missing. Include X-API-Key header."
}
```

### 404 Not Found
Workflow ID not found

```json
{
  "detail": "Workflow article-123 not found"
}
```

### 500 Internal Server Error
Workflow execution failed

```json
{
  "error": "Internal server error",
  "detail": "Failed to start workflow: ...",
  "type": "Exception"
}
```

### 503 Service Unavailable
Temporal connection failed

```json
{
  "detail": "Service not ready - Temporal connection failed"
}
```

---

## Production Deployment

### Railway

1. **Set environment variables** in Railway dashboard:
   - `TEMPORAL_ADDRESS`
   - `TEMPORAL_NAMESPACE`
   - `TEMPORAL_API_KEY`
   - `TEMPORAL_TASK_QUEUE`
   - `API_KEY`
   - `ENVIRONMENT=production`

2. **Deploy command:**
   ```
   uvicorn gateway.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Health check endpoint:**
   ```
   /health
   ```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY gateway/requirements.txt .
RUN pip install -r requirements.txt

COPY gateway/ gateway/
COPY shared/ shared/

CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Monitoring

### Temporal Cloud Dashboard
Monitor workflow executions:
https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows

### Gateway Logs
- Structured logging to stdout
- All requests logged with status
- Errors logged with full traceback

### Railway Logs
```bash
railway logs --service quest-gateway
```

---

## Next Steps

1. Start gateway: `python3 gateway/main.py`
2. Start worker: `python3 worker/worker.py`
3. Trigger workflow via HTTP
4. Check Temporal Cloud dashboard
5. Query article from database

---

**API Documentation:** http://localhost:8000/docs
**Gateway Version:** 1.0.0
**Last Updated:** November 10, 2025
