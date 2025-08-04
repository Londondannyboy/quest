# Apify Configuration for Quest Core

## Overview
Quest Core uses Apify for LinkedIn profile and company data scraping to power the "Shock & Awe" registration experience and data intelligence features.

## Required Environment Variables

Add these to your environment configuration:

```bash
# Apify Configuration
APIFY_API_KEY=your_apify_api_key_here
APIFY_USER_ID=infrastructure_quest
```

## Apify Account Setup

**Account**: `infrastructure_quest`
- This account contains the pre-configured scrapers
- Task IDs are already configured in the codebase

## Configured Scrapers

### 1. LinkedIn Profile Scraper
- **Task ID**: `l4Rzg56H5cbFETmgx`
- **Actor**: `infrastructure_quest/quest-profile-scraper`
- **Purpose**: Scrape individual LinkedIn profiles
- **Cost**: ~$0.004 per profile

### 2. Company Employees Scraper  
- **Task ID**: `Z4hQMjDxMd5Gk4Cmj`
- **Actor**: `harvestapi/linkedin-company-employees`
- **Purpose**: Scrape employee lists from company LinkedIn pages
- **Cost**: Variable based on company size

## Testing Endpoints

Once configured, test with these endpoints:

### Basic Profile Scraping
```bash
curl -X POST https://quest-core.vercel.app/api/test-profile-simple \
  -H "Content-Type: application/json" \
  -d '{"linkedinUrl": "https://linkedin.com/in/dankeegan"}'
```

### Company Employees Scraping
```bash
curl https://quest-core.vercel.app/api/test-company-employees
```

### All Scraping Services Status
```bash
curl https://quest-core.vercel.app/api/test-scraping-all
```

## Admin Interface

Test scraping through the web interface:
- **URL**: https://quest-core.vercel.app/admin/test-scraping
- **Pre-filled test data**: Dan Keegan's LinkedIn profile
- **Real-time results display**

## Integration Points

The Apify integration powers these features:

1. **LinkedIn Registration** (`/register/linkedin`)
   - Automatic profile import
   - Trinity insights generation
   - Professional network mapping

2. **Profile Enrichment** (`/api/test-scraping`)
   - Company data enhancement
   - Skills validation
   - Network analysis

3. **Admin Tools** (`/admin/test-scraping`)
   - Manual profile testing
   - Scraping health checks
   - Data quality validation

## Configuration Files

Environment variables should be added to:

- **Development**: `.env.local`
- **Production**: Vercel Environment Variables
- **Template**: `.env.example` (for team setup)

## Troubleshooting

### Common Issues

1. **"Profile scraping failed"**
   - Check if APIFY_API_KEY is set
   - Verify API key has sufficient credits
   - Test connection with `/api/debug-apify`

2. **"No data returned"**
   - Check LinkedIn URL format
   - Verify profile is public
   - Check Apify task status

3. **Rate limiting**
   - Built-in delays between requests
   - Automatic retry logic
   - Progress logging in console

### Debug Endpoints

- `/api/debug-apify` - Test API connection
- `/api/check-apify-run?runId=xxx` - Check specific run status

## Architecture

```
User Input (LinkedIn URL)
         ↓
Quest Core API Endpoint
         ↓
Apify Client (apify-client.ts)
         ↓
infrastructure_quest Account
         ↓
Quest Profile Scraper Task
         ↓
Parsed Profile Data
         ↓
Trinity Insights Generation
         ↓
User Registration Complete
```

## Deployment

After adding the APIFY_API_KEY:

1. **Vercel**: Add to Environment Variables in dashboard
2. **Local**: Update `.env.local` file
3. **Deploy**: Push changes to trigger rebuild
4. **Test**: Use admin interface to verify functionality

The LinkedIn scraping infrastructure is fully implemented and ready to use once the API key is configured.