# Company Creation API

HTTP API for creating company profiles via Gateway with **AI Auto-Detection**.

## Quick Start

### Create Any Company (Auto-Detected Type)

Just provide the URL - AI automatically detects if it's a recruiter, placement agent, or relocation company:

```bash
curl -X POST https://your-gateway.railway.app/v1/workflows/company \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Bain & Gray",
    "company_website": "https://www.bainandgray.com"
  }'
```

Response:
```json
{
  "workflow_id": "company-smart-123e4567-e89b-12d3-a456-426614174000",
  "status": "started",
  "started_at": "2025-11-11T12:00:00.000Z",
  "company_name": "Bain & Gray",
  "message": "Smart company profile workflow started. AI will auto-detect company type. Use workflow_id to check status."
}
```

---

## Endpoint Details

### POST /v1/workflows/company

Creates a complete company profile with **AI-powered type detection**.

**Headers:**
- `X-API-Key`: Your API key (required)
- `Content-Type`: `application/json`

**Request Body:**
```json
{
  "company_name": "Company Name",
  "company_website": "https://example.com",
  "auto_approve": true
}
```

**Parameters:**
- `company_name` (required): Company name
- `company_website` (required): Company website URL
- `auto_approve` (optional): Skip manual approval (default: true)

**How It Works:**
AI analyzes the website content and automatically classifies the company as:
- **Recruiter** - Executive Assistant / Chief of Staff recruiters → `executive_assistant_recruiters`
- **Placement** - PE/VC placement agents → `placement_agent`
- **Relocation** - Relocation service providers → `relocation_company`

**Response:**
```json
{
  "workflow_id": "company-smart-abc123...",
  "status": "started",
  "started_at": "2025-11-11T12:00:00.000Z",
  "company_name": "Bain & Gray",
  "message": "Smart company profile workflow started. AI will auto-detect company type..."
}
```

---

## What It Creates

The workflow automatically:

1. **Scrapes website** - Extracts content from company website
2. **AI Classification** - Analyzes website to detect company type (recruiter/placement/relocation)
3. **Searches news** - Finds recent company news articles
4. **Extracts information** (type-aware prompts):
   - Company description
   - Headquarters location
   - Phone number
   - Founded year
   - Specializations array
   - Services offered
   - Key facts (JSONB)
5. **Processes logo** - Downloads, uploads to Cloudinary
6. **Validates data** - Checks completeness (must meet 70% threshold)
7. **Saves to database** - Inserts into `companies` table with auto-detected `company_type`

### Database Fields Created

```sql
-- Automatically populated by workflow
name                -- Company name
slug                -- URL-friendly slug
company_type        -- 'executive_assistant_recruiters', 'placement_agent', etc.
description         -- Company description
headquarters        -- Location
website             -- Website URL
phone               -- Contact phone
specializations     -- Array of services
founded_year        -- Year founded
logo_url            -- Cloudinary URL
overview            -- Detailed overview
key_facts           -- JSONB with services, achievements, people
status              -- 'published' (auto-published)
```

---

## Check Workflow Status

### Non-blocking Status Check

```bash
curl -X GET https://your-gateway.railway.app/v1/workflows/{workflow_id}/status \
  -H "X-API-Key: your-api-key"
```

**Response (Running):**
```json
{
  "workflow_id": "company-recruiter-abc123...",
  "status": "running",
  "result": null,
  "error": null
}
```

**Response (Completed):**
```json
{
  "workflow_id": "company-smart-abc123...",
  "status": "completed",
  "result": {
    "id": "xyz789",
    "company_name": "Bain & Gray",
    "slug": "bain-and-gray",
    "company_type": "executive_assistant_recruiters",
    "detected_type": "recruiter",
    "detection_confidence": 0.95,
    "headquarters": "London, UK",
    "phone": "020 7036 2030",
    "website": "https://www.bainandgray.com/",
    "specializations": [
      "Executive Assistant Recruitment",
      "Chief of Staff Recruitment",
      "Personal Assistant Recruitment"
    ],
    "saved": true
  }
}
```

### Wait for Result (Blocking)

```bash
curl -X GET https://your-gateway.railway.app/v1/workflows/{workflow_id}/result \
  -H "X-API-Key: your-api-key"
```

This endpoint will wait for the workflow to complete before returning.

---

## Company Types (Auto-Detected)

The SmartCompanyWorkflow uses AI to automatically classify companies into these types:

### Recruiter (Auto-Detected)

- **AI Detection**: Analyzes for keywords like "executive assistant", "EA recruitment", "Chief of Staff"
- **Database value**: `executive_assistant_recruiters`
- **Site**: chiefofstaff.quest
- **Examples**: Bain & Gray, Tiger Recruitment, Pertemps

```bash
# No company_type needed - AI auto-detects!
curl -X POST .../v1/workflows/company \
  -H "X-API-Key: ..." \
  -d '{
    "company_name": "Bain & Gray",
    "company_website": "https://www.bainandgray.com"
  }'
```

### Placement (Auto-Detected)

- **AI Detection**: Analyzes for keywords like "placement agent", "private equity", "fund placement"
- **Database value**: `placement_agent`
- **Site**: placement.quest
- **Examples**: Campbell Lutyens, Evercore, Lazard

```bash
# No company_type needed - AI auto-detects!
curl -X POST .../v1/workflows/company \
  -H "X-API-Key: ..." \
  -d '{
    "company_name": "Campbell Lutyens",
    "company_website": "https://www.campbelllutyens.com"
  }'
```

### Relocation (Auto-Detected)

- **AI Detection**: Analyzes for keywords like "relocation", "immigration", "visa"
- **Database value**: `relocation_company`
- **Site**: relocation.quest

---

## Examples

### Create Multiple Companies (Simplified - No Type Required!)

```bash
# Bain & Gray - AI detects it's a recruiter
curl -X POST https://gateway.railway.app/v1/workflows/company \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Bain & Gray",
    "company_website": "https://www.bainandgray.com"
  }'

# Tiger Recruitment - AI detects it's a recruiter
curl -X POST https://gateway.railway.app/v1/workflows/company \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Tiger Recruitment",
    "company_website": "https://www.tigerrecruitment.com"
  }'

# Campbell Lutyens - AI detects it's a placement agent
curl -X POST https://gateway.railway.app/v1/workflows/company \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Campbell Lutyens",
    "company_website": "https://www.campbelllutyens.com"
  }'
```

### Check Status

```bash
# Save workflow ID from response
WORKFLOW_ID="company-smart-123e4567-e89b-12d3-a456-426614174000"

# Check status (non-blocking)
curl -X GET https://gateway.railway.app/v1/workflows/${WORKFLOW_ID}/status \
  -H "X-API-Key: $API_KEY"

# Wait for result (blocking) - shows detected_type and confidence
curl -X GET https://gateway.railway.app/v1/workflows/${WORKFLOW_ID}/result \
  -H "X-API-Key: $API_KEY"
```

---

## Output

Once workflow completes, company will be available at:

- **Homepage**: https://chiefofstaff.quest/ (if `company_type="recruiter"`)
- **Directory**: https://chiefofstaff.quest/companies
- **Profile**: https://chiefofstaff.quest/companies/{slug}

---

## Error Handling

### 401 Unauthorized
Missing or invalid API key

```json
{
  "detail": "API key is missing. Include X-API-Key header."
}
```

### 500 Internal Server Error
Workflow execution failed

```json
{
  "detail": "Failed to start workflow: ..."
}
```

### 503 Service Unavailable
Temporal connection failed

```json
{
  "detail": "Failed to connect to Temporal: ..."
}
```

---

## Gateway Setup

### Start Gateway Locally

```bash
cd /Users/dankeegan/quest/gateway
export API_KEY="your-secret-key"
export TEMPORAL_ADDRESS="..."
export TEMPORAL_NAMESPACE="..."
export TEMPORAL_API_KEY="..."
python3 main.py
```

Gateway runs on http://localhost:8000

### View API Documentation

http://localhost:8000/docs

Interactive Swagger UI with all endpoints documented.

---

## Production Deployment

The gateway should already be deployed on Railway. Use the Railway URL:

```bash
curl -X POST https://your-gateway-production.up.railway.app/v1/workflows/company \
  -H "X-API-Key: $API_KEY" \
  -d '{...}'
```

---

**Next Companies to Add:**

UK Executive Assistant / Chief of Staff Recruiters:
- Bain & Gray ✅ (ready to add)
- Tiger Recruitment
- Pertemps
- Office Angels
- Bespoke Bureau
- The Consultancy Group
- Mayfair Executive
