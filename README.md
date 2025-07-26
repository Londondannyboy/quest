# Quest Core V2

A revolutionary professional development platform where users must earn their Quest through story.

## Philosophy

**Story → Trinity → Quest**

"You can't begin your Quest until we understand your story."

## Project Status

### ✅ Completed (Phase 1 Foundation)
- [x] Next.js 15 with TypeScript setup
- [x] Entity-first Prisma schema (no strings!)
- [x] Clerk authentication with webhook sync
- [x] Professional Mirror page with timeline visualization
- [x] Apify scraping service integration
- [x] AI coaching service with OpenRouter
- [x] Landing page with journey entry

### 🚧 In Progress
- [ ] Trinity discovery flow
- [ ] Quest readiness gate
- [ ] Voice coaching integration

### 📋 Next Steps
1. Complete Trinity discovery page
2. Implement Quest readiness assessment
3. Add voice coaching with Hume AI
4. Set up monitoring and error tracking

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