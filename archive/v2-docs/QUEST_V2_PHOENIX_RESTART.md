# Quest Core V2 Phoenix Restart Plan

*Last Updated: December 2024*

## Overview

The "Phoenix Restart" represents a complete rebuild of Quest Core V2 using proven methodologies and enhanced workflows. Like a phoenix rising from ashes, we'll rebuild stronger, faster, and more focused.

## Why Phoenix?

Current state analysis:
- **Lines of Code**: 17,452 (target: ~3,000)
- **Complexity**: Over-engineered features
- **Focus**: Lost in feature creep
- **Performance**: Degraded over iterations

Phoenix goals:
- **Radical Simplification**: 10% of current code
- **Laser Focus**: Trinity + Voice + Jobs only
- **Enhanced Stack**: Add PG Vector, 21st.dev
- **Agent Workflow**: BMAD-inspired with specialists

## The Phoenix Stack

### Core (Unchanged)
- Next.js 15
- TypeScript
- Prisma + Neon DB
- Clerk Authentication
- Tailwind CSS v4

### Phoenix Enhancements
- **PG Vector**: Semantic Trinity matching
- **21st.dev Magic MCP**: Delightful animations
- **Firecrawl**: Job scraping intelligence
- **Hume AI EVI 3**: Voice coach (existing)
- **Agent Workflow**: Specialized AI agents

## Phoenix Methodology: BMAD + Specialist Agents

### Phase 1: Planning (Days 1-2)
**Agents:**
- UX Researcher
- Trinity Architect
- Sprint Prioritizer

**Outputs:**
- Complete UX research
- Trinity flow documentation
- 6-day implementation plan

### Phase 2: Design (Day 3)
**Agents:**
- UI Designer
- Whimsy Injector
- Voice Coach Specialist

**Outputs:**
- Complete UI designs
- Micro-interaction plans
- Voice conversation flows

### Phase 3: Implementation (Days 4-5)
**Agents:**
- Rapid Prototyper
- Frontend Developer
- Backend Architect

**Outputs:**
- Working Trinity creation
- Voice coach integration
- Job matching system

### Phase 4: Polish & Ship (Day 6)
**Agents:**
- Test Writer/Fixer
- Performance Benchmarker
- Project Shipper

**Outputs:**
- Tested application
- Optimized performance
- Deployed to production

## Phoenix Feature Set (MVP Only)

### 1. Trinity Creation (Core)
- Voice-first discovery with Hume AI
- Three eternal questions flow
- Beautiful visualization
- Semantic embeddings via PG Vector

### 2. Professional Mirror
- LinkedIn data transformation
- "Shock and awe" visualization
- Shareable moments
- Whimsy animations

### 3. Quest Job Matching
- Semantic matching via PG Vector
- Trinity-aligned opportunities
- Firecrawl for job data
- Simple, powerful UI

### What We're NOT Building (Yet)
- ❌ Complex networking features
- ❌ Multiple coach personalities
- ❌ Advanced analytics
- ❌ Social features
- ❌ Payment processing

## Technical Architecture

### Database Schema (Simplified)
```prisma
model User {
  id        String   @id @default(cuid())
  email     String   @unique
  trinity   Trinity?
  profile   Profile?
  matches   Match[]
}

model Trinity {
  id        String   @id @default(cuid())
  userId    String   @unique
  quest     String   @db.Text
  service   String   @db.Text
  pledge    String   @db.Text
  embedding Json     // PG Vector embeddings
  user      User     @relation(fields: [userId], references: [id])
}

model Job {
  id          String   @id @default(cuid())
  title       String
  company     String
  description String   @db.Text
  embedding   Json     // PG Vector embedding
  matches     Match[]
}

model Match {
  id         String   @id @default(cuid())
  userId     String
  jobId      String
  similarity Float
  user       User     @relation(fields: [userId], references: [id])
  job        Job      @relation(fields: [jobId], references: [id])
}
```

### Agent Workflow Structure
```
/quest-core-v2-phoenix
  /.claude
    /agents
      /trinity-architect.md
      /voice-coach-specialist.md
      /quest-matcher.md
      /whimsy-injector.md
    /commands
      /trinity-mode.md
      /voice-mode.md
      /phoenix-mode.md
  /docs
    /agent-context
      /ux-research.md
      /design-system.md
      /implementation-plan.md
```

## Implementation Timeline

### Day 1: Foundation & Planning
- [ ] Set up fresh Next.js project
- [ ] Configure Prisma + Neon + PG Vector
- [ ] Run UX Researcher agent
- [ ] Create Trinity Architect plans

### Day 2: Core Infrastructure
- [ ] Implement Clerk auth
- [ ] Set up base layouts
- [ ] Create Trinity schema
- [ ] Design component system

### Day 3: Trinity Creation
- [ ] Build Trinity flow UI
- [ ] Integrate Hume AI
- [ ] Add whimsy animations
- [ ] Create embeddings system

### Day 4: Professional Mirror
- [ ] LinkedIn data integration
- [ ] Visualization components
- [ ] Shareable moments
- [ ] Polish interactions

### Day 5: Job Matching
- [ ] Implement Firecrawl scraping
- [ ] Build matching algorithm
- [ ] Create job UI
- [ ] Test end-to-end

### Day 6: Ship It
- [ ] Performance optimization
- [ ] Final testing
- [ ] Deploy to Vercel
- [ ] Monitor and celebrate

## Success Metrics

### Code Quality
- Total lines: <3,000
- Test coverage: >80%
- Performance score: >95
- No TypeScript errors

### User Experience
- Trinity creation: <3 minutes
- Time to first match: <30 seconds
- Voice interaction success: >90%
- Delight moments: >5 per session

### Business Impact
- User activation: >60%
- Trinity completion: >80%
- Job match satisfaction: >70%
- Viral shares: >10%

## Lessons from Previous Attempts

### What Failed
- Over-abstraction killed clarity
- Too many features diluted focus
- Perfection prevented shipping
- Complex state management

### What We Learned
- Skeleton first, features second
- Ship weekly, iterate constantly
- Let agents do heavy lifting
- Delight differentiates

## The Phoenix Promise

In 6 days, we will have:
1. A working Trinity creation system with voice
2. A Professional Mirror that creates "shock and awe"
3. A job matching system that actually works
4. Under 3,000 lines of maintainable code
5. A foundation for sustainable growth

## Next Steps

1. **Today**: Delete everything except docs
2. **Tomorrow**: Start Day 1 with fresh energy
3. **This Week**: Ship Phoenix V1
4. **Next Week**: Iterate based on user feedback

---

*"From the ashes of complexity, simplicity rises. From the ruins of features, focus emerges. This is the Phoenix way."*

## Remember

- **Trust the agents**: Let specialized AI do the work
- **Embrace constraints**: 3,000 lines is enough
- **Ship daily**: Progress over perfection
- **Add whimsy**: Delight differentiates
- **Stay focused**: Trinity + Voice + Jobs only

The Phoenix rises. Let's build.