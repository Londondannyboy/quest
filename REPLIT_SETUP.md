# Quest Core V2 - Replit Setup Guide

## 🚀 Quick Start

1. **Import to Replit**
   - Go to Replit and import from GitHub: `https://github.com/Londondannyboy/quest`
   - Select "Import from GitHub"

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Set Up Environment Variables**
   In Replit's Secrets tab, add these environment variables:

   ### Required for Phase 1:
   ```
   DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
   DIRECT_URL=postgresql://user:pass@host/db?sslmode=require
   
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
   CLERK_SECRET_KEY=sk_test_...
   CLERK_WEBHOOK_SECRET=whsec_...
   
   APIFY_TOKEN=apify_api_...
   APIFY_API_KEY=apify_api_...
   APIFY_USER_ID=oagG2IEtw87XfSn3x
   
   OPENROUTER_API_KEY=sk-or-v1-...
   ```

4. **Database Setup**
   ```bash
   npx prisma generate
   npx prisma db push
   ```

5. **Run Development Server**
   ```bash
   npm run dev
   ```

## 🔧 Replit-Specific Configuration

### Database Connection
If using Replit's PostgreSQL:
1. Create a PostgreSQL database in Replit
2. Copy the connection string to both DATABASE_URL and DIRECT_URL
3. Ensure `?sslmode=require` is added

### Public URL for Webhooks
Your Clerk webhook URL will be:
`https://[your-repl-name].[your-username].repl.co/api/webhooks/clerk`

### Port Configuration
The app runs on port 3000, which Replit automatically proxies to port 80.

## 📝 Environment Variables from V1

If you have Quest V1 running on Replit, you can reuse:
- Clerk keys (but add the webhook secret)
- Apify token (but add the redundant keys)
- Update database URLs with SSL mode

## 🆕 New for V2

You'll need to obtain:
- OpenRouter API key (https://openrouter.ai)
- Clerk webhook secret (from Clerk dashboard)

## 🐛 Troubleshooting

### "Module not found" errors
```bash
npm install
npx prisma generate
```

### Database connection issues
- Ensure both DATABASE_URL and DIRECT_URL are set
- Check that `?sslmode=require` is included
- Verify PostgreSQL is running

### Clerk authentication issues
- Verify all three Clerk env vars are set
- Check webhook is configured in Clerk dashboard
- Ensure public key starts with `pk_` and secret with `sk_`