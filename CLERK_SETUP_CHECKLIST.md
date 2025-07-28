# Clerk Setup Checklist

## 🧹 Cleanup Phase

### In Clerk Dashboard:

- [ ] Choose ONE development app to keep (note the domain: ******\_\_\_\_******)
- [ ] Delete all duplicate "quest" apps except the chosen one
- [ ] Delete all "V2" apps

## 🔨 Development Setup

### From your chosen development app:

- [ ] Copy `Publishable Key` → Update in `.env.local`
- [ ] Copy `Secret Key` → Update in `.env.local`
- [ ] Configure webhook:
  - [ ] Go to Webhooks → Create Endpoint
  - [ ] URL: `https://your-vercel-preview-url.vercel.app/api/webhooks/clerk`
  - [ ] Events: Select `user.created` and `user.updated`
  - [ ] Copy `Signing Secret` → Update `CLERK_WEBHOOK_SECRET` in `.env.local`

## 🚀 Production Setup

### Create Production Instance:

- [ ] Click "Create application" in Clerk Dashboard
- [ ] Name: "quest-production"
- [ ] Environment: Production
- [ ] Domain: Your production domain (e.g., questcore.ai)

### From your production app:

- [ ] Copy `Publishable Key` (pk*live*...)
- [ ] Copy `Secret Key` (sk*live*...)
- [ ] Configure webhook:
  - [ ] URL: `https://your-production-domain.com/api/webhooks/clerk`
  - [ ] Events: Select `user.created` and `user.updated`
  - [ ] Copy `Signing Secret`

## 📝 Vercel Environment Variables

### Add to Vercel Dashboard:

```
# Production Environment
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
CLERK_WEBHOOK_SECRET=whsec_...

# These stay the same for all environments
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/
```

### Preview Environment (optional):

```
# Use dev keys for preview deployments
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
CLERK_WEBHOOK_SECRET=whsec_...
```

## ✅ Verification Steps

1. **Local Development:**

   ```bash
   npm run dev
   # Test /api/health endpoint
   # Test authentication flow
   ```

2. **Production:**
   - Deploy to Vercel
   - Test authentication on production domain
   - Verify webhook is receiving events

## 🔍 Troubleshooting

- **"Publishable key not valid"**: Check that keys don't have quotes in `.env.local`
- **Webhook not working**: Ensure the webhook URL matches your deployment URL
- **Authentication not working in production**: Verify production keys are in Vercel

## 📌 Important Notes

1. Never commit production keys to git
2. Development keys only work on localhost and staging domains
3. Production keys only work on your configured production domain
4. Each environment needs its own webhook endpoint
