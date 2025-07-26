# Quest Core V2 - Vercel Deployment Guide

## 🚀 Quick Deploy to Vercel

### Option 1: Deploy with Vercel Button
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Londondannyboy/quest)

### Option 2: Manual Setup

1. **Import Project**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import from GitHub: `Londondannyboy/quest`
   - Select your account and continue

2. **Configure Build Settings**
   - Framework Preset: `Next.js`
   - Build Command: `prisma generate && next build` (CRITICAL!)
   - Output Directory: `.next`
   - Install Command: `npm install`

3. **Environment Variables** (Add ALL of these!)

## 🔑 Required Environment Variables

Copy these to Vercel's Environment Variables section:

### Database (Neon) - BOTH Required!
```
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
DIRECT_URL=postgresql://user:pass@host/db?sslmode=require
```
⚠️ **CRITICAL**: Must include `?sslmode=require` on both!

### Authentication (Clerk) - ALL Three Required!
```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
CLERK_WEBHOOK_SECRET=whsec_...
```

### Scraping (Apify) - ALL Three Required!
```
APIFY_TOKEN=apify_api_...
APIFY_API_KEY=apify_api_...
APIFY_USER_ID=oagG2IEtw87XfSn3x
```
Note: APIFY_API_KEY should be the same value as APIFY_TOKEN

### AI Gateway (OpenRouter) - NEW for V2!
```
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_PREFER_COST=true
OPENROUTER_FALLBACK_ENABLED=true
```

### Voice AI (Hume) - For Phase 2
```
HUME_API_KEY=...
HUME_CLIENT_SECRET=...
HUME_CONFIG_ID=...
EVI_VERSION=3
```

## 🔧 Post-Deployment Setup

### 1. Database Migration
After first deploy, run in Vercel CLI or locally:
```bash
npx prisma migrate deploy
```

### 2. Clerk Webhook Configuration
1. Go to Clerk Dashboard → Webhooks
2. Add endpoint: `https://your-domain.vercel.app/api/webhooks/clerk`
3. Select events: `user.created`, `user.updated`, `user.deleted`
4. Copy the signing secret to `CLERK_WEBHOOK_SECRET`

### 3. Domain Configuration (Optional)
1. In Vercel project settings → Domains
2. Add your custom domain
3. Update Clerk settings with new domain

## ⚠️ Common Deployment Issues

### "Missing Environment Variable" Error
- Ensure ALL variables are added in Vercel dashboard
- Check for typos in variable names
- Verify no quotes around values in Vercel

### "Database Connection Failed"
- Confirm `?sslmode=require` is included
- Check both DATABASE_URL and DIRECT_URL are set
- Verify Neon database is active

### "Prisma Generate Failed"
- Build command MUST be: `prisma generate && next build`
- Not just `next build`

### "Clerk Authentication Failed"
- All three Clerk variables must be set
- Webhook secret must match dashboard
- Publishable key must start with `pk_`

## 📊 Environment Variable Checklist

Before deploying, verify in Vercel dashboard:

- [ ] DATABASE_URL (with ?sslmode=require)
- [ ] DIRECT_URL (with ?sslmode=require)
- [ ] NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
- [ ] CLERK_SECRET_KEY
- [ ] CLERK_WEBHOOK_SECRET
- [ ] APIFY_TOKEN
- [ ] APIFY_API_KEY (same as token)
- [ ] APIFY_USER_ID
- [ ] OPENROUTER_API_KEY
- [ ] OPENROUTER_BASE_URL
- [ ] OPENROUTER_PREFER_COST
- [ ] OPENROUTER_FALLBACK_ENABLED

## 🎯 Verification Steps

1. **Check Build Logs**
   - Look for "Prisma Client generated successfully"
   - Ensure no missing env var warnings

2. **Test Authentication**
   - Visit homepage
   - Click "Begin Your Journey"
   - Should show Clerk sign-in modal

3. **Test Database Connection**
   - Sign in creates user record
   - Check Neon dashboard for new user

4. **Test Scraping** (needs valid Apify token)
   - Enter LinkedIn URL
   - Should start scraping process

## 🆘 Need Help?

- Build failing? Check build command includes `prisma generate`
- Auth not working? Verify all 3 Clerk env vars
- Database errors? Ensure SSL mode on both URLs
- Scraping fails? Check Apify token and user ID

Remember: V2 requires MORE environment variables than V1!