# Quest Core V1 → V2 Migration Guide

## 🔄 Environment Variable Migration

### ✅ Variables You Can Copy from V1

These can be copied directly from your existing Quest Core V1:

```bash
# Database (if using Neon PostgreSQL)
DATABASE_URL=<copy from V1>
DIRECT_URL=<copy from V1>  # If not present, use same as DATABASE_URL

# Scraping (Apify)
APIFY_TOKEN=<copy from V1>
APIFY_API_KEY=<copy from V1>  # If not present, use same as APIFY_TOKEN
APIFY_USER_ID=<copy from V1>
```

### 🔄 Variables That Need Updates

#### Authentication System Change
V2 uses Clerk instead of V1's auth system. You'll need NEW keys:

```bash
# Get these from clerk.com dashboard
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
CLERK_WEBHOOK_SECRET=whsec_...  # From webhook setup
```

### 🆕 New Required Variables

#### AI System (Replace OpenAI with OpenRouter)
```bash
# Remove: OPENAI_API_KEY
# Add these instead:
OPENROUTER_API_KEY=sk-or-v1-...  # Get from openrouter.ai
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_PREFER_COST=true
OPENROUTER_FALLBACK_ENABLED=true
```

### 📊 Cost Comparison

**V1 with OpenAI:**
- All requests use GPT-4: ~$10/million tokens
- No cost optimization

**V2 with OpenRouter:**
- Story Coach (Claude): $3/million tokens
- Quest Coach (GPT-4): $10/million tokens  
- Delivery Coach (Kimi): $0.15/million tokens
- Skills Analysis: FREE
- Average: <$2/million tokens (80% cost reduction!)

### 🚀 Migration Steps

1. **In Vercel Dashboard for V1:**
   - Copy DATABASE_URL
   - Copy APIFY_TOKEN
   - Note any other services you're using

2. **Sign up for New Services:**
   - [Clerk](https://clerk.com) - Authentication
   - [OpenRouter](https://openrouter.ai) - AI Gateway

3. **In Vercel for V2 (Quest repo):**
   - Add all variables from `.env.example`
   - Use copied values where applicable
   - Add new service credentials

### ⚠️ Critical Changes

1. **Database URLs**: Must add `?sslmode=require` if not present
2. **Build Command**: Must be `prisma generate && next build`
3. **User Sync**: Configure Clerk webhook after deploy

### 🔍 Quick Verification

After migration, check:
- [ ] Both DATABASE_URL and DIRECT_URL are set
- [ ] All 3 Clerk variables are present
- [ ] OpenRouter (not OpenAI) keys are configured
- [ ] Apify has all 3 required variables

### 💡 Pro Tips

1. **Use V1 Data**: Your PostgreSQL data can be migrated
2. **Test Locally First**: Use `.env.local` to verify
3. **Monitor Costs**: OpenRouter dashboard shows per-model usage
4. **Gradual Migration**: Can run V1 and V2 in parallel

## 🎯 Why These Changes?

- **Clerk**: Better user management and webhooks
- **OpenRouter**: 80% cost reduction through multi-model routing
- **Entity System**: Better data quality and deduplication
- **Voice Coaches**: Different personalities need different models

Ready to migrate? The new architecture will significantly reduce costs while improving the user experience!