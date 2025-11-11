# Company Creation API

HTTP API for creating company profiles via Gateway.

## Quick Start

### Create a Chief of Staff Recruiter

```bash
curl -X POST https://your-gateway.railway.app/v1/workflows/company \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Bain & Gray",
    "company_website": "https://www.bainandgray.com",
    "company_type": "recruiter"
  }'
```

Response:
```json
{
  "workflow_id": "company-recruiter-123e4567-e89b-12d3-a456-426614174000",
  "status": "started",
  "started_at": "2025-11-11T12:00:00.000Z",
  "company_name": "Bain & Gray",
  "company_type": "recruiter",
  "message": "Company profile creation workflow started. Use workflow_id to check status."
}
```

---

## Endpoint Details

### POST /v1/workflows/company

Creates a complete company profile automatically.

**Headers:**
- `X-API-Key`: Your API key (required)
- `Content-Type`: `application/json`

**Request Body:**
```json
{
  "company_name": "Company Name",
  "company_website": "https://example.com",
  "company_type": "recruiter",
  "auto_approve": true
}
```

**Parameters:**
- `company_name` (required): Company name
- `company_website` (required): Company website URL
- `company_type` (required): One of:
  - `"recruiter"` - Executive Assistant / Chief of Staff recruiters
  - `"placement"` - PE/VC placement agents
  - `"relocation"` - Relocation service providers
- `auto_approve` (optional): Skip manual approval (default: true)

**Response:**
```json
{
  "workflow_id": "company-recruiter-abc123...",
  "status": "started",
  "started_at": "2025-11-11T12:00:00.000Z",
  "company_name": "Bain & Gray",
  "company_type": "recruiter",
  "message": "Company profile creation workflow started..."
}
```

---

## What It Creates

The workflow automatically:

1. **Scrapes website** - Extracts content from company website
2. **Searches news** - Finds recent company news articles
3. **Extracts information**:
   - Company description
   - Headquarters location
   - Phone number
   - Founded year
   - Specializations array
   - Services offered
   - Key facts (JSONB)
4. **Processes logo** - Downloads, uploads to Cloudinary
5. **Validates data** - Checks completeness (must meet 70% threshold)
6. **Saves to database** - Inserts into `companies` table with proper `company_type`

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
  "workflow_id": "company-recruiter-abc123...",
  "status": "completed",
  "result": {
    "id": "xyz789",
    "company_name": "Bain & Gray",
    "slug": "bain-and-gray",
    "company_type": "executive_assistant_recruiters",
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

## Company Types

### Recruiter (`company_type: "recruiter"`)

- **Database value**: `executive_assistant_recruiters`
- **Site**: chiefofstaff.quest
- **Workflow**: `RecruiterCompanyWorkflow`
- **Examples**: Bain & Gray, Tiger Recruitment, Pertemps

```bash
curl -X POST .../v1/workflows/company \
  -H "X-API-Key: ..." \
  -d '{
    "company_name": "Bain & Gray",
    "company_website": "https://www.bainandgray.com",
    "company_type": "recruiter"
  }'
```

### Placement (`company_type: "placement"`)

- **Database value**: `placement_agent`
- **Site**: placement.quest
- **Workflow**: `PlacementCompanyWorkflow`
- **Examples**: Campbell Lutyens, Evercore, Lazard

```bash
curl -X POST .../v1/workflows/company \
  -H "X-API-Key: ..." \
  -d '{
    "company_name": "Campbell Lutyens",
    "company_website": "https://www.campbelllutyens.com",
    "company_type": "placement"
  }'
```

### Relocation (`company_type: "relocation"`)

- **Database value**: TBD
- **Site**: relocation.quest
- **Workflow**: `RelocationCompanyWorkflow`

---

## Examples

### Create Multiple Companies

```bash
# Bain & Gray
curl -X POST https://gateway.railway.app/v1/workflows/company \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Bain & Gray",
    "company_website": "https://www.bainandgray.com",
    "company_type": "recruiter"
  }'

# Tiger Recruitment
curl -X POST https://gateway.railway.app/v1/workflows/company \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Tiger Recruitment",
    "company_website": "https://www.tigerrecruitment.com",
    "company_type": "recruiter"
  }'

# Office Angels
curl -X POST https://gateway.railway.app/v1/workflows/company \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Office Angels",
    "company_website": "https://www.office-angels.com",
    "company_type": "recruiter"
  }'
```

### Check Status

```bash
# Save workflow ID from response
WORKFLOW_ID="company-recruiter-123e4567-e89b-12d3-a456-426614174000"

# Check status (non-blocking)
curl -X GET https://gateway.railway.app/v1/workflows/${WORKFLOW_ID}/status \
  -H "X-API-Key: $API_KEY"

# Wait for result (blocking)
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

### 400 Bad Request
Invalid company_type

```json
{
  "detail": "Invalid company_type: foo. Must be: recruiter, placement, or relocation"
}
```

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
