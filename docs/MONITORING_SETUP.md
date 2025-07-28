# Monitoring Setup Guide

## Required Accounts & Environment Variables

### 1. **Checkly** (Synthetic Monitoring)

**Account Setup:**

1. Sign up at https://app.checklyhq.com/signup
2. Get your API key from Account Settings → API Keys
3. Get your Account ID from Account Settings

**Environment Variables:**

```bash
# .env.local
CHECKLY_API_KEY="your-checkly-api-key"
CHECKLY_ACCOUNT_ID="your-account-id"
```

**Vercel Environment Variables:**

- Add the same keys to your Vercel project settings

### 2. **HyperDX** (Application Monitoring)

**Account Setup:**

1. Sign up at https://app.hyperdx.io/register
2. Create a new project
3. Get your API key from Settings → API Keys

**Environment Variables:**

```bash
# .env.local
NEXT_PUBLIC_HYPERDX_API_KEY="your-hyperdx-api-key"
HYPERDX_API_KEY="your-hyperdx-api-key"
```

**Note:** The `NEXT_PUBLIC_` prefix is needed for client-side monitoring.

### 3. **Semgrep** (Security Scanning)

**Account Setup:**

1. Sign up at https://semgrep.dev/login
2. Connect your GitHub repository
3. Get your API token from Settings → Tokens

**Environment Variables:**

```bash
# For GitHub Actions (add as repository secret)
SEMGREP_APP_TOKEN="your-semgrep-token"
```

## Implementation Steps

### Step 1: Set up HyperDX Client-Side Monitoring

Add to your root layout or \_app.tsx:

```typescript
// src/app/layout.tsx
import { initHyperDX } from '@/lib/monitoring/hyperdx'

// Initialize monitoring
if (typeof window !== 'undefined') {
  initHyperDX()
}
```

### Step 2: Set up HyperDX Server-Side Monitoring

Create initialization file:

```typescript
// src/lib/monitoring/hyperdx-server.ts
import { HyperDX } from '@hyperdx/node-opentelemetry'

if (process.env.HYPERDX_API_KEY) {
  HyperDX.init({
    apiKey: process.env.HYPERDX_API_KEY,
    service: 'quest-core-v2-api',
    // Additional configuration
  })
}
```

### Step 3: Deploy Checkly Checks

```bash
# Login to Checkly
npx checkly login

# Deploy your checks
npx checkly deploy
```

### Step 4: Add Semgrep GitHub Action

Create `.github/workflows/semgrep.yml`:

```yaml
name: Semgrep
on:
  pull_request: {}
  push:
    branches: ['main']
  schedule:
    - cron: '0 0 * * 0'

jobs:
  semgrep:
    name: Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: returntocorp/semgrep-action@v1
        with:
          publishToken: ${{ secrets.SEMGREP_APP_TOKEN }}
```

## Verification Steps

1. **HyperDX**: Check https://app.hyperdx.io for incoming events
2. **Checkly**: View dashboard at https://app.checklyhq.com
3. **Semgrep**: Check security findings at https://semgrep.dev

## Cost Considerations

- **HyperDX**: Free tier includes 1M events/month
- **Checkly**: Free tier includes 10k check runs/month
- **Semgrep**: Free for open source, paid for private repos

## Alternative: OpenTelemetry (Future)

As mentioned in V2_TECH_STACK.md, OpenTelemetry is planned for distributed tracing of AI calls.
