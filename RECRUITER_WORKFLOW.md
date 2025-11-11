# Recruiter Company Workflow

Automated workflow for creating Chief of Staff / Executive Assistant recruiter profiles.

## Overview

The `RecruiterCompanyWorkflow` automatically:
- Scrapes company website
- Searches for recent news
- Extracts company information (description, headquarters, phone, specializations)
- Processes company logo
- Validates data quality
- Saves to database with `company_type = 'executive_assistant_recruiters'`

## Quick Usage

### Add a Single Company

```bash
cd /Users/dankeegan/quest

# Using default (Bain & Gray)
python test_recruiter_company.py

# Custom company
python test_recruiter_company.py --company "ABC Recruiters" --website "https://example.com"
```

### Requirements

1. **Temporal Worker Running**
   - Make sure the worker is running: `cd /Users/dankeegan/quest && python -m worker.worker`

2. **Environment Variables** (in `.env`)
   - `TEMPORAL_ADDRESS`
   - `TEMPORAL_NAMESPACE`
   - `TEMPORAL_API_KEY`
   - `DATABASE_URL` (Neon)
   - `GOOGLE_API_KEY`
   - `SERPER_API_KEY`
   - `CLOUDINARY_URL` (for logo processing)

## What It Creates

The workflow creates a complete company profile with:

### Required Fields
- `name` - Company name
- `slug` - URL-friendly slug
- `company_type` - Set to `'executive_assistant_recruiters'`
- `status` - Set to `'published'`

### Extracted Fields
- `description` - Company description
- `headquarters` - Location
- `website` - Company website URL
- `phone` - Contact phone number
- `specializations` - Array of service specializations (e.g., ["Executive Assistant Recruitment", "Chief of Staff Recruitment"])
- `founded_year` - Year founded (if available)
- `logo_url` - Processed company logo
- `overview` - Detailed company overview
- `key_facts` - JSONB with services, achievements, leadership

## Output

Once complete, the company will be available at:
- **Homepage**: https://chiefofstaff.quest/ (first 6 companies)
- **Directory**: https://chiefofstaff.quest/companies
- **Profile**: https://chiefofstaff.quest/companies/[slug]

## Example Output

```
✅ WORKFLOW COMPLETED

Company ID: abc12345
Company Name: Bain & Gray
Company Type: executive_assistant_recruiters
Industry: Executive Recruitment
Website: https://www.bainandgray.com
Phone: 020 7036 2030
Headquarters: London, UK
Description: Boutique business support and PA recruitment agency...

Validation:
  Completeness: 87.5%
  Meets Threshold: True

Logo:
  Source: extracted

Specializations:
  - Executive Assistant Recruitment
  - Chief of Staff Recruitment
  - Personal Assistant Recruitment

Saved to Database: True

🎉 Company available at:
   https://chiefofstaff.quest/companies/bain-and-gray
```

## Workflow Architecture

```
RecruiterCompanyWorkflow
  ├─ Stage 1: Scrape Website
  ├─ Stage 2: Search News
  ├─ Stage 3: Extract Info
  ├─ Stage 4: Validate Data
  ├─ Stage 5: Process Logo
  ├─ Stage 6: Format Profile
  └─ Stage 7: Save to Database
```

## Manual SQL (Fallback)

If the workflow is unavailable, you can add companies manually:

```sql
INSERT INTO companies (
  name, slug, description, headquarters,
  website, phone, specializations, status,
  company_type, founded_year
) VALUES (
  'Company Name',
  'company-name',
  'Company description...',
  'London, UK',
  'https://example.com',
  '020 1234 5678',
  ARRAY['Executive Assistant Recruitment', 'Chief of Staff Recruitment'],
  'published',
  'executive_assistant_recruiters',
  2009
);
```

## Troubleshooting

### Workflow not found
- Ensure worker is running: `python -m worker.worker`
- Check workflow is registered in `worker/worker.py`

### Database errors
- Verify `DATABASE_URL` in `.env`
- Check database schema matches

### Logo processing fails
- Verify `CLOUDINARY_URL` is set
- Logo will fallback to text-based logo if extraction fails

## Next Companies to Add

Some top Executive Assistant / Chief of Staff recruiters:
- Bain & Gray (London) ✅
- Tiger Recruitment (London)
- Pertemps (UK nationwide)
- Office Angels (UK nationwide)
- Bespoke Bureau (London)
- The Consultancy Group (London)
