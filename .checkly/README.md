# Checkly Monitoring

This directory contains synthetic monitoring checks for Quest Core V2.

## Setup

1. **Login to Checkly CLI**:

   ```bash
   npx checkly login
   ```

2. **Set environment variables** in `.env.local`:
   ```
   CHECKLY_API_KEY="your-api-key"
   CHECKLY_ACCOUNT_ID="your-account-id"
   ```

## Running Checks Locally

Test your checks before deploying:

```bash
# Run all checks locally
npm run checkly:test

# Run with recording (saves results to Checkly)
npx checkly test --record

# Run specific check
npx checkly test homepage-check
```

## Deploying to Checkly

Deploy your checks to production:

```bash
# Deploy all checks
npm run checkly:deploy

# Preview what will be deployed
npx checkly deploy --preview

# Force deploy (skip confirmation)
npx checkly deploy --force
```

## Available Checks

1. **API Health Check** (`api-health.check.ts`)
   - Monitors `/api/health` endpoint
   - Runs every 5 minutes
   - Checks response time < 1s

2. **Homepage Browser Check** (`homepage.spec.ts`)
   - Full browser test of homepage
   - Captures screenshots
   - Runs every 10 minutes
   - Works with Vercel preview deployments

## Adding New Checks

1. Create a new file in `__checks__/`:
   - API checks: `*.check.ts`
   - Browser checks: `*.spec.ts`

2. Test locally:

   ```bash
   npx checkly test your-new-check
   ```

3. Deploy:
   ```bash
   npm run checkly:deploy
   ```

## Vercel Integration

The Checkly Vercel integration automatically:

- Tests preview deployments
- Uses `ENVIRONMENT_URL` for preview URLs
- Falls back to production URL

## Alerts

Configure alerts in the Checkly dashboard:

- Email notifications
- Slack webhooks
- PagerDuty integration

## Resources

- [Checkly CLI Docs](https://www.checklyhq.com/docs/cli/)
- [Playwright Test Docs](https://playwright.dev/docs/test-intro)
- [Checkly Community Slack](https://www.checklyhq.com/slack)
