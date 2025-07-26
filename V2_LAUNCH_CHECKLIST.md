# Quest Core V2 - Pre-Launch Checklist

> **CRITICAL**: Complete this checklist before starting V2 implementation  
> **Purpose**: Ensure all learnings, credentials, and gotchas are captured  

---

## 🔑 **Environment Variables Checklist**

### **Core Services (.env.local)**
```env
# Database (Neon) - EXACT format matters!
DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"
DIRECT_URL="postgresql://user:pass@host/db?sslmode=require"  # Direct for migrations

# Authentication (Clerk) - BOTH needed!
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="pk_test_..."
CLERK_SECRET_KEY="sk_test_..."
CLERK_WEBHOOK_SECRET="whsec_..."  # For user sync

# Scraping (Apify) - All three for compatibility
APIFY_TOKEN="apify_api_..."
APIFY_API_KEY="apify_api_..."  # Same as token
APIFY_USER_ID="oagG2IEtw87XfSn3x"  # Your specific user ID

# AI Gateway (OpenRouter)
OPENROUTER_API_KEY="sk-or-v1-..."
OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
OPENROUTER_PREFER_COST="true"
OPENROUTER_FALLBACK_ENABLED="true"

# Voice AI (Hume) - Upgrading to EVI 3
HUME_API_KEY="..."
HUME_CLIENT_SECRET="..."
HUME_CONFIG_ID="..."  # EVI 3 config
EVI_VERSION="3"

# Memory (Zep) - Phase 2
ZEP_API_KEY="..."
ZEP_BASE_URL="https://api.getzep.com"

# Graph Database (Neo4j) - Phase 2
NEO4J_URI="neo4j+s://..."
NEO4J_USER="neo4j"
NEO4J_PASSWORD="..."

# Web Search (Phase 2)
TAVILY_API_KEY="tvly_..."
LINKUP_API_KEY="lkup_..."

# Generative UI (Future)
THESYS_API_KEY="..."
THESYS_BASE_URL="https://api.thesys.dev/c1"
```

### **Vercel Production Settings**
- ⚠️ **CRITICAL**: Must add EACH env var in Vercel dashboard
- ⚠️ **Build Command**: `prisma generate && next build`
- ⚠️ **Node Version**: 18.x or higher

---

## ✅ **Critical Implementation Patterns**

### **1. Clerk User Sync (MUST HAVE)**
```typescript
// Without this, users can't access their data!
// app/api/webhooks/clerk/route.ts OR manual sync

export async function POST(req: Request) {
  const { type, data } = await req.json();
  
  if (type === 'user.created') {
    await prisma.user.create({
      data: {
        clerkId: data.id,
        email: data.email_addresses[0].email_address
      }
    });
  }
  return new Response('OK', { status: 200 });
}
```

### **2. Apify Data Structure (THE GOTCHA)**
```typescript
// WRONG - This will fail
const profile = items[0];

// CORRECT - Data is nested!
const profile = items[0]?.element;
```

### **3. Entity Management (NEW IN V2)**
```typescript
// NEVER store strings for companies/skills
// ALWAYS create or find existing entity
const company = await prisma.company.upsert({
  where: { domain: extractDomain(companyWebsite) },
  update: { lastScraped: new Date() },
  create: { name, domain, website }
});
```

### **4. Prisma Commands**
```bash
# After EVERY schema change
npx prisma generate

# Development
npx prisma db push

# Production (use migrations)
npx prisma migrate deploy
```

---

## 📋 **Pre-Launch Verification**

### **Database Schema**
- [ ] Entity models (Company, Skill, Education) with `verified` field
- [ ] Synthetic organization support (`provisional` status)
- [ ] Skill clustering relationships
- [ ] 6-month cache tracking (`lastScraped` field)
- [ ] User → Entity relationships properly mapped

### **Security**
- [ ] Semgrep MCP configured from Day 1
- [ ] API key rotation strategy documented
- [ ] Clerk webhook secured
- [ ] Environment variables never in code

### **Critical Files to Migrate**
- [ ] Apify scraping patterns (proven working)
- [ ] Clerk user sync logic
- [ ] Entity search/autocomplete endpoints
- [ ] 3D visualization components (if needed)

### **Documentation**
- [ ] PRODUCT_REQUIREMENTS_V2.md is authoritative
- [ ] CLAUDE.md updated for V2 context
- [ ] Archive old V2 docs (keep only Tech Stack & Style)

---

## 🚨 **Common V1 Mistakes to Avoid**

1. **No User Sync**: Forgetting Clerk → Database sync
2. **Wrong Apify Path**: Not accessing `items[0].element`
3. **Missing Env Vars**: Forgetting one in production
4. **String Storage**: Not using entity system
5. **No Deduplication**: Creating duplicate companies/skills
6. **Skipping Prisma Generate**: After schema changes
7. **No Error Boundaries**: Crashes on scraping failures

---

## 🎯 **V2 Launch Sequence**

### **Week 1 - Day 1**
1. [ ] Create fresh repo with Next.js 15
2. [ ] Configure ALL environment variables
3. [ ] Set up Clerk with webhook sync
4. [ ] Create entity-first database schema
5. [ ] Implement basic LinkedIn scraping
6. [ ] Test entity creation/deduplication

### **Week 1 - Day 2-3**
1. [ ] Professional Mirror visualization
2. [ ] Story Coach voice setup
3. [ ] Trinity discovery flow
4. [ ] Quest Readiness Gate

### **Definition of "Working"**
- User can complete Story → Trinity journey
- Entities are created, not strings
- No duplicate companies/skills
- Voice coaching responds
- Data persists correctly

---

## 💡 **Final Reminders**

1. **Entity System is Core**: Every string should be an entity
2. **Synthetic First**: Create provisional, validate later
3. **Cache Smart**: 6-month rescrape, not every time
4. **Voice Transitions**: Signature sounds matter
5. **Security Day 1**: Not "we'll add it later"

---

## 🚀 **Ready for V2?**

If all items above are checked and understood:
1. Create new repository: `quest-core-v2`
2. Use PRODUCT_REQUIREMENTS_V2.md as bible
3. Start with Phase 1 implementation
4. Measure against success metrics

**Remember**: "You can't begin your Quest until we understand your story."

---

*This checklist captures all critical learnings from 42,000+ lines of V1 code.*