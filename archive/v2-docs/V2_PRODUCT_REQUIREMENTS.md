# Quest Core V2 - Complete Product Requirements

> **Single Source of Truth for V2 Implementation**  
> **Last Updated**: January 26, 2025  
> **Status**: Ready for Implementation  
> **Philosophy**: Story → Trinity → Quest  

---

## 📋 **Table of Contents**

1. [Executive Summary](#executive-summary)
2. [Core Product Vision](#core-product-vision)
3. [User Journey Architecture](#user-journey-architecture)
4. [Data & Entity Management](#data--entity-management)
5. [AI & Voice Coaching System](#ai--voice-coaching-system)
6. [Technical Requirements](#technical-requirements)
7. [Enhanced Features from V1 Learnings](#enhanced-features-from-v1-learnings)
8. [Implementation Phases](#implementation-phases)
9. [Success Metrics](#success-metrics)

---

## 🎯 **Executive Summary**

Quest Core V2 transforms professional development from a transactional platform to a transformational journey where users must **earn their Quest through story**. 

**Key Differentiators:**
- Users don't "sign up" - they begin their "story"
- 30% must earn Quest readiness (aspirational scarcity)
- Trinity evolves through time (Past → Present → Future)
- Entity-based data (no strings, only validated objects)
- Multi-voice coaching with signature transitions

**Scoring Evolution**: Legacy (6.5/10) → Current (7.6/10) → V2 (9.6/10)

---

## 🏔️ **Core Product Vision**

### **The Sacred Journey**
```
Story Collection → Trinity Recognition → Quest Readiness → Quest Activation
     (Act 1)           (Act 2)              (Gate)           (Begin)
```

### **Philosophy**
- **Quest**: "What drives you?" (Purpose)
- **Service**: "How do you serve?" (Value)
- **Pledge**: "What do you commit to?" (Promise)

### **Core Beliefs**
- "LinkedIn shows who you were. Quest shows who you're becoming."
- Sacred threshold: Making "not yet" an invitation, not rejection
- Story as foundation: Everything builds from authentic narrative
- Continuous Trinity evolution: Not static purpose discovery
- Professional awakening: Transformation over transaction

### **Manifesto Principles**
1. Every feature must serve the Story → Trinity → Quest journey
2. Human dignity over conversion optimization
3. Earned access creates aspiration
4. Coaches guide, users discover
5. Data serves story, not surveillance

---

## 🎭 **User Journey Architecture**

### **Act 1: Professional Mirror (3-5 minutes)**

#### **Entry Point**
- LinkedIn URL or name search
- Consent: "May we discover your professional story?"

#### **Mirror Presentation**
```typescript
interface ProfessionalMirror {
  visualization: "Timeline with floating nodes",
  messaging: "This is how the world sees you",
  corrections: "Click any node to correct our understanding",
  transparency: "Here's what we found (and might have missed)"
}
```

#### **Enhanced Discovery (Shock & Awe Strategy)**
- **Phase 1**: LinkedIn via Apify + Harvest API for company intelligence
- **Phase 2**: Tavily web search (articles, talks, GitHub)
- **Phase 3**: LinkUp market intelligence + salary benchmarking
- **Real-time Progress**: Progressive UI reveals during data gathering
- **3D Organizational Charts**: Company relationships and influence mapping

#### **Voice**: Story Coach (Female, Warm)
- "Tell me about this transition..."
- "What drew you to [field]?"
- "I notice a pattern here..."

### **Act 2: Trinity Evolution (5-7 minutes)**

#### **Trinity Through Time**
```typescript
interface TrinityEvolution {
  past: {
    quest: "What drove you then?",
    visual: "Faded constellation forming"
  },
  present: {
    quest: "What drives you now?",
    visual: "Bright, active constellation"
  },
  future: {
    quest: "What will drive you?",
    visual: "Emerging, pulsing constellation"
  }
}
```

#### **Pattern Recognition**
- AI identifies themes across timeline
- Coaches highlight evolution
- User validates or corrects

#### **Voice Transition**: Quest Coach (Male, CA/UK)
- *Signature sound effect*
- "Welcome to your Quest. I see your Trinity emerging..."
- More energetic, forward-looking

### **Act 3: Quest Readiness Gate**

#### **Assessment Algorithm**
```typescript
const readinessScore = 
  (storyDepth * 0.3) +        // How much they shared
  (trinityClarity * 0.4) +    // How clear their purpose
  (futureOrientation * 0.3);  // How ready for growth

if (readinessScore >= 70) return "QUEST_READY";
if (readinessScore >= 40) return "PREPARING";
return "NOT_YET";
```

#### **Three Outcomes**
1. **Quest Ready (70%)**: Proceed to Quest activation
2. **Preparing (25%)**: Guided exercises to clarify
3. **Not Yet (5%)**: Supportive redirection

#### **Voice**: OKR/Delivery Coach (Firm, Achievement-focused)
- "I'm taking over now. Let's make this real..."
- "Your Quest requires commitment. Are you ready?"

---

## 🗄️ **Data & Entity Management**

### **Entity-First Architecture**

#### **Core Principle**
Every piece of data is an entity with relationships - NO STRINGS.

#### **Entity Types**
```typescript
interface EntitySystem {
  companies: {
    verified: boolean,
    lastScraped: Date,
    parentCompany?: Company,
    subsidiaries: Company[],
    validatedBy: User[]
  },
  skills: {
    name: string,
    cluster: SkillCluster,
    parentSkill?: Skill,
    relatedSkills: Skill[],
    marketDemand: number
  },
  education: {
    institution: Entity,
    verified: boolean,
    ranking?: number,
    specialties: string[]
  }
}
```

### **Synthetic Organizations**

#### **Concept**
When scraping reveals companies/people, create "synthetic" provisional entities that users validate.

```typescript
interface SyntheticEntity {
  type: "company" | "person" | "skill",
  confidence: number,  // AI confidence in accuracy
  status: "provisional" | "validated" | "rejected",
  validators: User[],  // Users who confirmed
  created: Date,
  source: "linkedin" | "tavily" | "user"
}
```

#### **Validation Flow**
1. Scrape creates provisional entities
2. Display with transparency: "We think this is..."
3. User validates/corrects
4. Validated entities become "real"
5. Build trust network of confirmations

### **Skill Clustering & Intelligence**

#### **AI-Powered Taxonomy**
```typescript
interface SkillCluster {
  name: "Digital Marketing",
  coreSkills: ["SEO", "SEM", "Content Marketing"],
  emergingSkills: ["AI Marketing", "Voice Search"],
  parentCluster: "Marketing",
  demandTrend: "increasing",
  salaryPremium: 15  // % above base
}
```

#### **Dynamic Grouping**
- AI groups related skills automatically
- Market data informs clustering
- User corrections improve taxonomy
- Visualizations show skill relationships

### **Caching & Deduplication**

#### **Smart Rescraping**
```typescript
const shouldRescrape = (entity: Entity): boolean => {
  const sixMonthsAgo = new Date();
  sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
  
  return entity.lastScraped < sixMonthsAgo || 
         entity.majorEventFlag || 
         entity.userRequested;
};
```

#### **Deduplication Strategy**
1. Fuzzy matching on names
2. Domain matching for companies
3. LinkedIn URL as unique identifier
4. User validation for conflicts

---

## 🤖 **AI & Voice Coaching System**

### **Multi-Coach Personalities**

#### **1. Story Coach** (Biographer)
- **Voice**: Female, warm, patient
- **Accent**: Gentle British or Midwest American
- **Tone**: Curious, non-judgmental
- **Focus**: Drawing out authentic story

#### **2. Quest Coach** (Pattern Seeker)
- **Voice**: Male, energetic
- **Accent**: California or British
- **Tone**: Insightful, connecting dots
- **Signature**: Transition sound when taking over

#### **3. OKR/Delivery Coach** (Achievement Driver)
- **Voice**: Gender-neutral, firm
- **Accent**: Clear, authoritative
- **Tone**: Direct, results-focused
- **Focus**: Turning insights into action

### **Voice Transitions**
```typescript
interface VoiceTransition {
  trigger: "Trinity clarity reached" | "Quest readiness achieved",
  effect: "Signature sound + brief silence",
  announcement: "New coach introduces themselves",
  continuity: "References previous coach's insights"
}
```

### **AI Model Strategy** (via OpenRouter)

#### **Cost-Optimized Routing**
```typescript
const modelSelection = {
  storyCoach: "anthropic/claude-3-sonnet",     // Empathetic ($3/M)
  questCoach: "openai/gpt-4-turbo",           // Insightful ($10/M)
  deliveryCoach: "moonshotai/kimi-k2",        // Direct ($0.15/M)
  skillsAnalysis: "moonshotai/kimi-k2:free",  // Zero cost
  patternRecognition: "google/gemini-pro",     // Large context ($0.5/M)
  fallback: "openai/gpt-3.5-turbo"            // Budget option ($0.5/M)
};

// Automatic fallback on errors
const routeWithFallback = async (primary: string, fallback: string) => {
  try {
    return await openRouter.chat(primary);
  } catch (error) {
    return await openRouter.chat(fallback);
  }
};
```

### **Journey-Aware Responses**
- Voice intensity increases near Quest
- Language becomes more action-oriented
- Celebration at milestones
- Adaptive to user energy

---

## 🛠️ **Technical Requirements**

### **Core Stack**
- **Frontend**: Next.js 15, React 18, TypeScript
- **Database**: PostgreSQL (Neon) + Neo4j (relationships)
- **Auth**: Clerk with proper webhook sync
- **AI Gateway**: OpenRouter for multi-model access
- **Voice**: Hume AI EVI 3 with voice cloning

### **Data Services**
- **Primary Scraping**: Apify (LinkedIn + 5000 actors) + Harvest API
- **Web Search**: Tavily AI search (professional content discovery)
- **Market Intelligence**: LinkUp API (jobs + salary benchmarking)
- **Memory Management**: Zep (conversational memory) + Graphiti (temporal graphs)
- **Workflow**: n8n for orchestration
- **Generative UI**: thesys.dev C1 API

### **Visualization**
- **Journey Graph**: React Force Graph 3D with transparent layering system
- **4-Layer Architecture**: 
  - Layer 1: Temporal gradient backgrounds
  - Layer 2: Particle effects (2000+ particles)
  - Layer 3: Interactive graph (transparent)
  - Layer 4: UI overlays
- **Quest Node**: Pulsing based on proximity + voice modulation
- **Timeline Variants**: Spiral, circular, columns, morphing geometry
- **Trinity Evolution**: Graphiti-powered temporal visualization
- **Skills Network**: D3.js clustering with market demand overlays
- **Critical Pattern**: Dynamic imports with `ssr: false`
- **See**: `V2_3D_VISUALIZATION_LEARNINGS.md` for implementation

### **Performance Requirements**
- Page load: <2 seconds
- Voice response: <500ms
- Graph rendering: 60fps @ 1000 nodes
- Cost per user: <$0.50/month

### **Security Requirements**
- Semgrep from Day 1 (5000+ rules)
- API key rotation policy
- Audit trail for all data access
- GDPR-compliant data handling

---

## 🚀 **Enhanced Features from V1 Learnings**

### **Memory & Context Management (Zep + Graphiti Integration)**
- **Temporal Knowledge Graphs**: Track Trinity evolution over time via Graphiti
- **Bi-Temporal Tracking**: Know when things happened AND when discovered
- **Cross-Session Memory**: 70% token reduction through intelligent context
- **Fact Extraction**: 13+ entity types automatically extracted
- **Multi-Coach Context Sharing**: Unified memory across all coaches
- **Session Cost Tracking**: Per-conversation analytics
- **Point-in-Time Queries**: "Show my Trinity from 6 months ago"
- **Real-Time Graph Updates**: Journey visualization updates as story unfolds

### **Advanced Multi-Coach Orchestration**
- **Debate Management**: Structured disagreements between coaches
- **Turn-Taking System**: Explicit orchestration of perspectives
- **Conflict Resolution**: Factual/Strategic/Priority handling
- **Authority Hierarchy**: Master Coach as final arbiter
- **Performance Analytics**: Track coaching effectiveness

### **Generative UI (thesys.dev Integration)**
- **Real-time UI Morphing**: Interfaces adapt during conversations
- **Trinity-Aware Design**: UI changes based on user's Trinity state
- **Streaming Updates**: Progressive interface reveals
- **Brand Compliance**: Automatic Quest design system enforcement
- **Context-Driven Components**: Generate UI based on coaching progress

### **Professional Intelligence Features**
- **3D Organizational Mapping**: Interactive company hierarchy visualization
- **Skill Network Graphs**: Market demand heat maps and clustering
- **Media Graph Visualization**: Professional content and influence
- **Influence Scoring**: Network-based professional impact metrics
- **Geographic Opportunity Maps**: Location-based career insights

### **Cost Optimization Framework**
- **Intelligent Model Routing**: Task-appropriate model selection
- **Kimi K2 Integration**: 10x cost reduction for technical coaching
- **Free Tier Utilization**: Strategic use of free models
- **Budget-Aware Selection**: Cost caps and fallback strategies
- **Performance/Cost Analytics**: ROI tracking per model

### **Innovation Lab (PocketFlow Integration)**
- **Rapid Prototyping**: Test coaching patterns before production
- **Agent Development**: Self-improving coaching capabilities
- **Pattern Analysis Services**: Trinity prediction algorithms
- **Experimental Features**: Safe testing environment
- **Innovation Pipeline**: Systematic feature development

### **Data Architecture Enhancements**
- **Unified Master ID**: Clerk ID consistent across all systems
- **Automated Sync Healing**: Self-correcting inconsistencies
- **Privacy Classification**: Public/private/encrypted data tiers
- **Performance Caching**: Intelligent query optimization
- **GDPR Compliance**: Built-in data protection workflows

### **Revolutionary 3D Visualization System**
- **4-Layer Architecture**: Background → Effects → Graph → UI
- **Transparent ForceGraph3D**: Enables layered temporal visualization
- **Temporal Backgrounds**: Gradient progressions (Past→Present→Future)
- **Particle Systems**: 2000+ particles showing data flow through time
- **Morphing Geometry**: Real-time shape transformations
- **12+ Variants Proven**: Spiral, circular, fixed columns, backgrounds
- **TypeScript Solutions**: Pragmatic approaches for Three.js integration
- **"Never Seen Before"**: Unique layered approach to temporal data

---

## 📅 **Implementation Phases**

### **Phase 1: Foundation (Weeks 1-2)**

#### **Core Journey**
- [ ] Story → Trinity → Quest flow
- [ ] Professional Mirror with LinkedIn + Harvest API
- [ ] Basic voice coaching (single voice)
- [ ] Quest Readiness Gate logic
- [ ] Temporal Trinity visualization (Past/Present/Future)

#### **Entity System**
- [ ] Company, Skill, Education entities
- [ ] Deduplication logic
- [ ] Basic validation UI
- [ ] Synthetic entity creation
- [ ] Unified Clerk ID strategy

#### **Infrastructure**
- [ ] Semgrep security scanning
- [ ] Monitoring (Checkly + HyperDX)
- [ ] Error tracking and recovery
- [ ] Basic analytics
- [ ] Zep memory integration setup

### **Phase 2: Enhancement (Weeks 3-4)**

#### **Discovery & Intelligence**
- [ ] Tavily web search integration
- [ ] Multi-platform enrichment
- [ ] 3D organizational mapping
- [ ] Skill clustering with market overlays
- [ ] Progressive reveal UI during scraping

#### **Voice Evolution**
- [ ] Multi-coach personalities with debate protocols
- [ ] Voice transitions with signature sounds
- [ ] EVI 3 migration with voice cloning
- [ ] Journey-aware responses
- [ ] Turn-taking orchestration system

#### **3D Visualization System**
- [ ] Implement transparent ForceGraph3D setup
- [ ] Create temporal gradient backgrounds
- [ ] Add particle system (2000+ particles)
- [ ] Build 4-layer rendering architecture
- [ ] Implement timeline variants (spiral, circular, columns)
- [ ] TypeScript pragmatic solutions for Three.js

#### **Memory & Context**
- [ ] Zep conversational memory setup
- [ ] Graphiti temporal knowledge graphs
- [ ] Bi-temporal Trinity tracking
- [ ] Cross-session memory sharing
- [ ] Fact extraction (13+ entity types)
- [ ] Context visualization during coaching
- [ ] Point-in-time query capability

#### **Relationships**
- [ ] Neo4j integration
- [ ] Professional network graph
- [ ] Synthetic relationship validation
- [ ] Influence scoring algorithms

### **Phase 3: Intelligence (Weeks 5-6)**

#### **Market Intelligence**
- [ ] LinkUp deep integration
- [ ] Salary benchmarking by skill cluster
- [ ] Skill demand tracking with predictions
- [ ] Geographic opportunity mapping
- [ ] Media graph visualization

#### **Advanced AI & UI**
- [ ] Kimi K2 optimization (10x cost reduction)
- [ ] Multi-model debates with conflict resolution
- [ ] Pattern recognition for Trinity prediction
- [ ] Predictive Quest paths
- [ ] thesys.dev generative UI integration
- [ ] Real-time UI morphing

#### **Scale & Innovation**
- [ ] Workflow automation (n8n)
- [ ] Bulk entity validation
- [ ] Community features
- [ ] Performance optimization
- [ ] PocketFlow innovation lab
- [ ] Self-improving agent capabilities

---

## 📊 **Success Metrics**

### **Journey Metrics**
- **Story Completion**: >80% finish Act 1
- **Trinity Clarity**: >70% achieve clear Trinity
- **Quest Readiness**: 30% earn Quest (aspirational)
- **Time to Quest**: 15-20 minutes average

### **Data Quality**
- **Entity Validation Rate**: >60% user validates
- **Deduplication Success**: <5% duplicates
- **Skill Clustering Accuracy**: >85% user agreement
- **Rescrape Efficiency**: <10% unnecessary scrapes

### **Business Metrics**
- **Cost per User**: <$0.50/month
- **Conversion to Paid**: >40% of Quest Ready
- **Monthly Retention**: >75%
- **User Satisfaction**: >4.5/5 stars

### **Technical Performance**
- **Uptime**: 99.9%
- **Response Time**: <500ms p95
- **Error Rate**: <0.1%
- **Security Incidents**: 0

---

## 🚀 **Key Differentiators**

1. **Philosophy-Driven**: Every feature serves Story → Trinity → Quest
2. **Earned Access**: Quest must be earned, creating aspiration
3. **Entity Intelligence**: No strings, only validated objects
4. **Voice Journey**: Coaches with personality transitions
5. **Temporal Trinity**: Past → Present → Future evolution

---

## 📋 **Implementation Checklist**

### **Before Starting**
- [ ] All API keys secured (Clerk, OpenRouter, Hume, Apify, Tavily)
- [ ] Database schemas migrated for entities
- [ ] Monitoring stack configured
- [ ] Security scanning enabled

### **Week 1 Deliverables**
- [ ] Professional Mirror working with real LinkedIn data
- [ ] Entity system creating companies/skills
- [ ] Basic voice coach responding
- [ ] Trinity visualization rendering

### **Definition of Done**
- [ ] User can complete Story → Trinity → Quest journey
- [ ] Entities are validated and deduplicated  
- [ ] Voice coaches transition naturally
- [ ] Performance meets all benchmarks
- [ ] Zep memory persists across sessions
- [ ] Cost per user under $0.50/month
- [ ] Security scanning passes all checks

---

## 🎯 **Final Note**

This document consolidates all V2 requirements into a single source of truth. Archive other V2 docs except:
- **V2_TECH_STACK.md** (technical reference)
- **V2_STYLE_GUIDE.md** (design reference)
- **CLAUDE.md** (AI assistant context)

Everything needed to build Quest Core V2 is here. Let the implementation begin.

---

*"You can't begin your Quest until we understand your story."*