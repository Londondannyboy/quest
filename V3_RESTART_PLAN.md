# V3 Restart Plan - Quest Unified Platform

*Last Updated: December 2024*

## Executive Summary

Quest V3 is a complete restart focusing on serving small dynamic startups (10-50 employees) with a unified platform for funding, talent, and visibility. Using a Sanity-first architecture with MCP integrations, we can launch in 2-3 weeks with minimal code.

**Key Innovation**: Trinity-based matching for everything - investors, talent, journalists.

## Vision

**"From finding your purpose to funding your vision"**

A single platform where:
- Founders discover funding through Trinity-aligned investors
- Professionals find purpose-driven startups
- Investors discover mission-aligned deals
- Journalists find authentic founder stories

## Architecture Principles

### 1. Sanity-First
- ALL data in Sanity CMS (investors, jobs, journalists, content)
- Built-in human review via Sanity Studio
- Version control and collaboration included
- No need for separate admin tools

### 2. Minimal Code via MCP
- Apify MCP for scraping
- Sanity MCP for data management
- Arcade.dev for user actions
- 80% less code than traditional approach

### 3. Unified Platform
- One codebase (Next.js)
- One database (Sanity + PG Vector)
- One auth system (Clerk)
- Multiple perspectives based on user type

## Technical Stack

```typescript
const v3Stack = {
  // Core
  framework: 'Next.js 15',
  language: 'TypeScript',
  styling: 'Tailwind CSS',
  
  // Data
  cms: 'Sanity (primary database)',
  vector: 'PG Vector (search only)',
  auth: 'Clerk',
  
  // AI & Voice
  llm: 'OpenRouter (Claude/GPT-4)',
  voice: 'Hume AI EVI 3',
  actions: 'Arcade.dev',
  
  // Integrations
  scraping: 'Apify MCP',
  content: 'Sanity MCP',
  search: 'Firecrawl'
}
```

## Data Architecture

### Everything in Sanity

```javascript
// Core document types
const sanitySchemas = [
  'investor',      // VCs, angels, funds
  'journalist',    // Media contacts
  'job',          // Open positions
  'organization', // Startups, companies
  'user',         // Platform users
  'article'       // SEO content
]

// Data flow
DataSource → MCP → Sanity (draft) → Human Review → Sanity (published) → PG Vector
```

### Why Sanity for Everything?
1. Beautiful built-in UI (Sanity Studio)
2. Real-time collaboration
3. Version history on all changes
4. No need for Retool or custom admin
5. Powerful GROQ queries
6. Webhooks for vector sync

## Implementation Timeline

### Week 1: Foundation
**Day 1-2: Project Setup**
- Create new Next.js 15 app
- Set up Sanity project
- Configure Clerk auth
- Basic routing structure

**Day 3-4: Sanity Schemas**
- Define all document types
- Set up Sanity Studio
- Configure review workflows
- Create custom desk structure

**Day 5-7: Core Features**
- Trinity discovery flow
- Voice integration (Hume AI)
- Basic matching logic
- User onboarding

### Week 2: Data & Matching
**Day 8-9: Data Pipeline**
- Apify MCP integration
- Investor/journalist ingestion
- Job scraping setup
- Sanity webhook → PG Vector

**Day 10-11: Search & Match**
- PG Vector semantic search
- Trinity-based matching
- Voice query interface
- Results presentation

**Day 12-14: Polish & Launch**
- Arcade.dev integration
- Email introductions
- Basic analytics
- Deployment to Vercel

## User Journeys

### Founder Journey
```
1. Voice onboarding → Discover Trinity
2. "I need funding" → Match with investors
3. Review matches → Request intros (Arcade)
4. Get funded → Post jobs on platform
5. Need PR → Match with journalists
```

### Investor Journey
```
1. Voice onboarding → Define thesis
2. Browse Trinity-aligned founders
3. See warm intro paths
4. Schedule meetings (Arcade)
5. Track deal flow
```

### Professional Journey
```
1. Discover Trinity purpose
2. Find aligned startups
3. Apply with Trinity context (Arcade)
4. Join purpose-driven team
```

## Minimal Code Examples

### Data Ingestion (10 lines vs 100)
```typescript
// Old way: 100+ lines of code
// New way with MCP:
async function ingestInvestor(linkedinUrl: string) {
  const data = await apifyMCP.scrape({
    actor: 'linkedin-scraper',
    url: linkedinUrl
  })
  
  await sanityMCP.create_document({
    type: 'investor',
    data: { ...data, verified: false }
  })
}
```

### Human Review (0 lines)
```typescript
// No code needed! 
// Reviewers use Sanity Studio's built-in UI
// Custom desk structure shows review queues
```

### Trinity Matching
```typescript
async function findInvestors(userTrinity: Trinity) {
  // Query PG Vector with Trinity embedding
  const matches = await pgVector.search({
    embedding: await embed(userTrinity),
    type: 'investor',
    threshold: 0.75
  })
  
  // Enrich with Sanity data
  return sanityClient.fetch(
    `*[_type == "investor" && _id in $ids]`,
    { ids: matches.map(m => m.id) }
  )
}
```

## Revenue Model

### Phase 1: Freemium
- **Free**: Trinity discovery + 5 introductions/month
- **Pro ($99/mo)**: Unlimited intros + priority support
- **Team ($299/mo)**: Multiple users + analytics

### Phase 2: Success Fees
- 0.5% on successful funding (optional)
- $500 placement bonus for hires
- $100 per media placement

### Phase 3: Premium Tiers
- **Investors ($999/mo)**: Verified deal flow
- **Placement Agents ($299/mo)**: Enhanced profiles
- **PR Agencies ($499/mo)**: Journalist database

## Launch Strategy

### MVP Focus (Week 2)
1. **One use case**: Founder-investor matching
2. **One city**: Start with SF/NYC
3. **100 investors**: Hand-curated quality
4. **Voice-first**: Differentiate immediately

### Growth (Month 1)
1. Add job postings
2. Expand to 10 cities
3. 1,000 investors
4. First paying customers

### Scale (Month 3)
1. Add journalist matching
2. Full Arcade.dev workflows
3. 10,000 users
4. $50K MRR

## Key Differentiators

1. **Trinity Matching**: Nobody else does purpose-based matching
2. **Voice-First**: Natural conversation vs forms
3. **Unified Platform**: Funding + talent + PR in one place
4. **Action-Oriented**: Arcade.dev enables real outcomes
5. **Minimal Complexity**: Sanity-first means faster development

## Risk Mitigation

### Technical Risks
- Start simple (one use case)
- Use proven tools (Sanity, Next.js)
- MCP reduces custom code
- Progressive enhancement

### Market Risks
- Focus on underserved placement agents first
- Clear value prop (Trinity matching)
- Quick iteration based on feedback
- Multiple revenue streams

## Success Metrics

### Week 2 Launch
- 100 investors profiled
- 10 successful intros
- 5 beta users active

### Month 1
- 1,000 users
- 100 paid subscriptions
- 50 successful connections

### Month 3
- 10,000 users
- $50K MRR
- 500 funded connections
- Expand to jobs + PR

## Why This Will Work

1. **Proven Market**: Placement agents charge $50K+, we charge $99/mo
2. **Clear Problem**: Founders can't find aligned investors
3. **Unique Solution**: Trinity matching + voice + actions
4. **Simple Tech**: Sanity + MCP = minimal code
5. **Fast Execution**: 2 weeks to MVP

## Next Steps

1. Create new V3 repository
2. Set up Sanity project
3. Define schemas (see V3_SANITY_SCHEMA.md)
4. Build Trinity discovery
5. Add investor matching
6. Launch to 10 beta users

---

*"Delete everything. Start fresh. Ship in 2 weeks. Change how startups find funding forever."*