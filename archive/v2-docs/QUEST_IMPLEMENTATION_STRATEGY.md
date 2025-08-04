# Quest Core V2 Implementation Strategy

*Last Updated: December 2024*

## Overview

This document outlines the implementation strategy for Quest Core V2 and the Placement Agents Platform, leveraging specialized AI agents and the Hume EVI Next.js starter for rapid development.

## Core Technology Decisions

### 1. Voice Integration: Hume EVI Next.js Starter

**Repository**: https://github.com/HumeAI/hume-evi-next-js-starter

**Why this starter:**
- **Perfect Stack Match**: Next.js 14 App Router + TypeScript
- **Production Ready**: Handles auth, WebSocket, audio permissions
- **Quick Integration**: Copy-paste components into existing project
- **EVI 3 Support**: Latest speech-to-speech architecture

**Implementation Timeline:**
- Day 1: Clone starter, set up environment
- Day 2: Integrate with Quest UI components
- Day 3: Customize for Trinity discovery

### 2. Agent Workflow Architecture

Based on Contains Studio agents and our learnings, we'll use:

#### Selected Agents from Contains Studio

**Whimsy Injector** (Priority 1)
- Repository: https://github.com/contains-studio/agents/tree/main/whimsy-injector
- Purpose: Add delightful micro-interactions
- Quest Use Cases:
  - Trinity creation ceremony animations
  - Professional Mirror "shock and awe" reveals
  - Achievement celebrations
  - Shareable moment creation

#### Custom Quest Agents

**Voice Coach Specialist**
- Purpose: Hume AI prompt engineering and conversation flow
- Responsibilities:
  - Trinity discovery conversation design
  - Coach personality management
  - Emotional state tracking
  - Conversation branch handling

**Trinity Architect**
- Purpose: Ensure philosophical coherence
- Responsibilities:
  - Quest/Service/Pledge alignment
  - Journey mapping
  - Pattern recognition
  - Evolution tracking

**Quest Matcher**
- Purpose: Semantic matching with PG Vector
- Responsibilities:
  - Trinity-to-job matching algorithms
  - Similarity scoring
  - Recommendation ranking

### 3. Development Workflow

#### 6-Day Sprint Plan

**Days 1-2: Foundation**
- Set up Hume EVI starter
- Configure agent workspace
- Design Trinity flow with Trinity Architect

**Days 3-4: Core Features**
- Implement voice coaching with Voice Coach Specialist
- Build Trinity creation UI
- Add PG Vector for matching

**Day 5: Polish**
- Run Whimsy Injector for micro-interactions
- Test end-to-end flows
- Performance optimization

**Day 6: Ship**
- Final testing
- Deploy to Vercel
- Monitor initial usage

## Quest Core V2 Specific Implementation

### Voice-First Trinity Discovery

```typescript
// Adapt Hume starter for Trinity
const trinitySystemPrompt = `
You are the Trinity Discovery Coach. Your role is to help users discover:
1. Quest - What drives them (their purpose)
2. Service - How they serve others (their unique value)
3. Pledge - What they commit to (their standards)

Start by asking about their professional story. Listen for patterns.
Guide them through self-discovery, don't prescribe answers.
`;

// Trinity state management
interface TrinityState {
  quest: string | null;
  service: string | null;
  pledge: string | null;
  currentPhase: 'story' | 'quest' | 'service' | 'pledge' | 'complete';
  confidence: {
    quest: number;
    service: number;
    pledge: number;
  };
}
```

### Professional Mirror with Whimsy

```typescript
// After LinkedIn data processing
const revealProfessionalMirror = async (profileData: LinkedInProfile) => {
  // Process with AI
  const mirror = await generateProfessionalMirror(profileData);
  
  // Add whimsy animations
  const animatedMirror = await whimsyInjector.enhance({
    component: 'ProfessionalMirror',
    data: mirror,
    goals: ['create_shareable_moment', 'inspire_awe']
  });
  
  return animatedMirror;
};
```

### Agent Directory Structure

```
/quest-core-v2
  /.claude
    /agents
      /trinity-architect
        - instructions.md
        - context-rules.md
      /voice-coach-specialist
        - hume-prompts.md
        - conversation-flows.md
      /whimsy-injector
        - animation-library.md
        - interaction-patterns.md
    /commands
      /trinity-mode.md
      /voice-mode.md
      /mirror-mode.md
```

## Placement Agents Platform Implementation

### Adapting Quest Stack

The placement agents platform uses 90% of Quest's stack:

1. **Same Voice Foundation**: Hume EVI starter
2. **Different Purpose**: Match GPs to placement agents
3. **SEO Focus**: Contentlayer for content management
4. **Scraping Stack**: Firecrawl + Apify + Lobstr.io

### Conversational Discovery

```typescript
// Placement agent discovery prompt
const placementAgentPrompt = `
You are an AI advisor helping fund managers find the right placement agent.
Ask about:
1. Fund size and target raise
2. Sector focus and geography
3. LP preferences
4. Timeline and urgency

Match them with placement agents based on expertise and track record.
`;
```

### Content Structure with Contentlayer

```typescript
// contentlayer.config.ts
export const PlacementAgent = defineDocumentType(() => ({
  name: 'PlacementAgent',
  filePathPattern: 'agents/**/*.mdx',
  fields: {
    name: { type: 'string', required: true },
    location: { type: 'string', required: true },
    sectors: { type: 'list', of: { type: 'string' } },
    aum: { type: 'string' },
    notableRaises: { type: 'list', of: { type: 'string' } },
    minimumFundSize: { type: 'string' },
    seoTitle: { type: 'string' },
    metaDescription: { type: 'string' }
  },
  computedFields: {
    slug: {
      type: 'string',
      resolve: (agent) => `/placement-agents/${agent.location.toLowerCase()}/${agent._raw.flattenedPath}`
    }
  }
}));
```

## Implementation Priorities

### Phase 1: MVP (Week 1)
1. ✅ Clone Hume EVI starter
2. ✅ Set up agent workspace
3. ✅ Basic Trinity discovery flow
4. ✅ Simple job matching

### Phase 2: Enhancement (Week 2)
1. 🔄 Add Whimsy Injector
2. 🔄 Professional Mirror visualization
3. 🔄 PG Vector semantic search
4. 🔄 Voice coach personalities

### Phase 3: Scale (Week 3+)
1. 📋 Multi-coach orchestration
2. 📋 Advanced matching algorithms
3. 📋 Analytics and insights
4. 📋 API for external integrations

## Success Metrics

### Technical Metrics
- Voice connection success rate > 95%
- Trinity completion rate > 80%
- Page load speed < 1 second
- SEO visibility increase 10x (placement agents)

### User Metrics
- Time to Trinity: < 5 minutes
- User delight score: > 4.5/5
- Viral shares: > 10% of users
- Return rate: > 60% within 7 days

## Risk Mitigation

### Technical Risks
- **Hume API changes**: Use starter's abstraction layer
- **WebSocket stability**: Implement reconnection logic
- **Audio permissions**: Clear user onboarding

### Business Risks
- **Placement agent data**: Start with public information
- **SEO competition**: Focus on long-tail keywords first
- **Voice adoption**: Offer text alternative

## Next Steps

1. **Today**: Clone Hume starter and test locally
2. **Tomorrow**: Create agent workspace structure
3. **This Week**: Ship Trinity discovery MVP
4. **Next Week**: Add placement agents prototype

---

*"Start with the Hume starter, enhance with agents, ship with confidence."*