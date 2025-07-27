# Quest Core V2

A revolutionary professional development platform where users must earn their Quest through story.

## Philosophy

**Story → Trinity → Quest**

"You can't begin your Quest until we understand your story."

## Project Status

### ✅ Completed (Phase 1 Foundation)
- [x] Next.js 15 with TypeScript setup
- [x] Entity-first Prisma schema (no strings!)
- [x] Clerk authentication (with workaround for middleware issues)
- [x] Database initialization and user sync
- [x] Professional Mirror page
- [x] LinkedIn scraping with HarvestAPI/Apify
- [x] Trinity discovery page UI
- [x] Code cleanup and modularization
- [x] GitHub Actions for automated fixes

### 🎯 Phase 1 Complete! Key Achievements:
- **Authentication**: Working with Clerk (using currentUser() approach)
- **Database**: PostgreSQL with Prisma, entity-first design
- **Scraping**: LinkedIn profiles via HarvestAPI
- **User Journey**: Professional Mirror → Trinity pages built
- **Clean Code**: Removed 670 lines of test/debug code

### 🚧 Phase 2: Trinity & Quest (Next)
- [ ] Trinity save functionality (API endpoint)
- [ ] Quest readiness assessment (30% gate)
- [ ] AI coaching integration (OpenRouter)
- [ ] Quest page implementation
- [ ] Story session tracking
- [ ] Voice coaching with Hume AI

### 📋 Phase 3: Intelligence Layer
- [ ] Skill entity extraction from LinkedIn
- [ ] Company entity validation
- [ ] Trinity pattern recognition
- [ ] Quest recommendation engine

## Setup Instructions

1. **Clone and install:**
```bash
npm install
```

2. **Set up environment variables:**
Copy `.env.local` and fill in your actual API keys:
- Clerk keys from dashboard
- Database URLs from Neon
- Apify token
- OpenRouter API key

3. **Set up database:**
```bash
npx prisma generate
npx prisma db push
```

4. **Configure Clerk webhook:**
Add webhook endpoint in Clerk dashboard:
`https://your-domain.com/api/webhooks/clerk`

5. **Run development server:**
```bash
npm run dev
```

## Key Implementation Notes

### Entity System
- Everything is an entity (Company, Skill, Institution)
- No raw strings stored
- Provisional → Validated workflow
- 6-month cache strategy

### Scraping Gotcha
LinkedIn data is nested: `items[0].element` not `items[0]`

### User Journey
1. **Professional Mirror**: LinkedIn scraping & visualization
2. **Trinity Discovery**: Past → Present → Future evolution
3. **Quest Gate**: Only 30% earn Quest readiness

### Cost Optimization
- Model routing based on coach type
- Fallback strategies
- Target: <$0.50/user/month

## Architecture

```
src/
├── app/              # Next.js app router pages
├── components/       # React components
├── lib/             # Core utilities (prisma client)
├── services/        # Business logic (scraping, AI)
├── types/           # TypeScript types
└── utils/           # Helper functions
```

## Security

- Semgrep configured (add MCP from Day 1)
- Environment variables never in code
- Clerk webhook verification
- API key rotation strategy

## References

- Product Requirements: `V2_PRODUCT_REQUIREMENTS.md`
- Launch Checklist: `V2_LAUNCH_CHECKLIST.md`
- Original Repository: https://github.com/Londondannyboy/quest-core