# Quest V2 - Vercel Environment Variables Checklist

## 🎯 Quick Setup in Vercel

### Step 1: Copy from V1 Quest Core
Go to your V1 Quest Core project in Vercel and copy these:
- [ ] `DATABASE_URL` - Add `?sslmode=require` if missing
- [ ] `APIFY_TOKEN`
- [ ] Any other services you're actively using

### Step 2: Add to V2 Quest Project

In your new Quest (V2) Vercel project, add:

#### Database (2 required)
- [ ] `DATABASE_URL` = (from V1 + add ?sslmode=require)
- [ ] `DIRECT_URL` = (same value as DATABASE_URL)

#### Clerk Auth (3 required) - ALL NEW
- [ ] `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` = pk_test_...
- [ ] `CLERK_SECRET_KEY` = sk_test_...
- [ ] `CLERK_WEBHOOK_SECRET` = whsec_...

#### Apify (3 required)
- [ ] `APIFY_TOKEN` = (from V1)
- [ ] `APIFY_API_KEY` = (same as APIFY_TOKEN)
- [ ] `APIFY_USER_ID` = (from V1 or "oagG2IEtw87XfSn3x")

#### OpenRouter AI (4 required) - ALL NEW
- [ ] `OPENROUTER_API_KEY` = sk-or-v1-...
- [ ] `OPENROUTER_BASE_URL` = https://openrouter.ai/api/v1
- [ ] `OPENROUTER_PREFER_COST` = true
- [ ] `OPENROUTER_FALLBACK_ENABLED` = true

### Step 3: Post-Deploy Configuration

1. **Clerk Webhook**:
   - URL: `https://[your-app].vercel.app/api/webhooks/clerk`
   - Events: user.created, user.updated, user.deleted
   - Copy signing secret to CLERK_WEBHOOK_SECRET

2. **Database Migration**:
   ```bash
   npx prisma migrate deploy
   ```

## 🚨 Common Issues

**"Module not found @prisma/client"**
- Build command must be: `prisma generate && next build`

**"Invalid DATABASE_URL"**
- Must include `?sslmode=require` at the end

**"Clerk not authenticated"**
- All 3 Clerk variables must be set
- Publishable key must start with `pk_`

## ✅ Ready to Deploy?

Once all checkboxes above are filled:
1. Deploy to Vercel
2. Configure Clerk webhook
3. Test sign-in flow
4. Verify LinkedIn scraping

Need new accounts?
- Clerk: https://clerk.com (free tier available)
- OpenRouter: https://openrouter.ai ($5 credit to start)