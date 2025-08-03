# Quest Core - AI Assistant Context

> **Context document for AI assistants working on Quest Core development**

## 🎯 **Project Overview**

Quest Core is a revolutionary professional development platform that guides users through discovering their authentic professional identity via the Trinity system: **Quest** (what drives you), **Service** (how you serve), and **Pledge** (what you commit to).

> "LinkedIn shows who you were. Quest shows who you're becoming."

### **Core Philosophy**
Built using Cole Medin's advanced context engineering methodology to create AI-powered coaching that remembers, evolves, and provides genuinely personalized guidance.

## 🏗️ **Current Architecture**

### **Technology Stack**

**📚 See [V2_TECH_STACK.md](./V2_TECH_STACK.md) for comprehensive technology documentation with URLs, versions, and setup guides.**

**Core Stack Overview:**
- **Frontend**: Next.js 15, React 18, TypeScript, Tailwind CSS
- **Design System**: Quest premium visual language with GT Walsheim typography
- **Generative UI**: thesys.dev C1 API (dynamic interface generation)
- **Authentication**: Clerk (user management)
- **Database**: PostgreSQL (Neon) - Single source of truth
- **AI & Voice**: Hume AI EVI 3 (speech-to-speech), OpenRouter.AI (AI gateway), Zep (memory management)
- **AI Models**: GPT-4, Claude-3, Gemini Pro (via OpenRouter for optimal routing)
- **AI Development**: PocketFlow (rapid prototyping and experimentation)
- **Future**: Neo4j (professional relationship graphs)
- **Deployment**: Vercel with auto-fix deployment system

### **Data Architecture Decision**
**Hybrid approach with single source of truth**:

1. **PostgreSQL (Neon)** - Master repository for all user data
2. **Zep** - Conversational memory and behavioral insights
3. **thesys.dev** - Generative UI and adaptive interface layer
4. **PocketFlow** - AI development and experimentation layer
5. **Neo4j** (future) - Professional relationship graphs
6. **Clerk** - Authentication (master user ID source)

## 🎯 **Trinity System**

### **The Three Eternal Questions**
1. **Quest** - "What drives you?" (Purpose and motivation)
2. **Service** - "How do you serve?" (Unique contribution to others)
3. **Pledge** - "What do you commit to?" (Promises and accountability)

### **AI Coaching Architecture**
Multi-coach system with specialized AI agents:
- **Master Coach**: Orchestrator and final authority
- **Career Coach**: Long-term strategy and market positioning
- **Skills Coach**: Technical development and competency building
- **Leadership Coach**: Management and interpersonal growth
- **Network Coach**: Professional relationships and networking

### **LinkedIn Mirror & Journey Visualization (V2)**
Revolutionary onboarding experience combining immediate value with visual storytelling:
- **Mirror Concept**: Show users their professional story as we see it
- **Immediate Value**: LinkedIn optimization suggestions during onboarding
- **Journey Graph**: 3D left-to-right timeline visualization
- **Quest Node**: Pulsing future node showing career destination
- **Real-time Updates**: Graph evolves during coaching conversations
- **Voice Integration**: EVI 3 voice intensity modulates based on quest proximity
- **Trust Building**: Transparency about data collection and potential errors
- See `V2_LINKEDIN_MIRROR_USE_CASE.md` for complete implementation details

## 🗂️ **4-Layer Repository System**

### **Privacy Model**
- **Surface Repo**: Public LinkedIn-style profiles
- **Working Repo**: Selective portfolio with controlled access
- **Personal Repo**: Private goals, notes, development tracking
- **Deep Repo**: AI insights, Trinity analysis, system-managed

## 🔄 **V2 Implementation Focus**

### **📋 Single Source of Truth**
**ALL V2 requirements are now consolidated in `V2_PRODUCT_REQUIREMENTS.md`**

This includes:
- Complete user journey (Story → Trinity → Quest)
- Entity Management System with synthetic organizations
- Multi-voice coaching with personality transitions
- Technical stack and integrations
- Implementation phases and success metrics

### **🏗️ V2 Key Innovations**
1. **Entity-First Data**: No strings, only validated objects
2. **Synthetic Organizations**: Provisional entities users validate
3. **Skill Clustering**: AI-powered taxonomy and relationships
4. **Voice Journey**: Story Coach → Quest Coach → Delivery Coach
5. **Smart Caching**: 6-month rescrape policy with deduplication

### **📊 Current V1 Status**
- ✅ Authentication, profiles, and basic repo system working
- ✅ Voice coaching with Hume AI integrated
- ✅ 3D visualizations functional
- 🚧 Multi-coach system partially implemented
- 📋 See `CURRENT_STATUS.md` for V1 progress

### **🎯 V2 Next Steps**
1. Review `V2_PRODUCT_REQUIREMENTS.md` for complete implementation guide
2. Create clean V2 repository with entity-first architecture
3. Implement Phase 1: Core journey + Entity system
4. Security scanning from Day 1 (Semgrep MCP)

## 🛠️ **Development Guidelines**

### **Code Style**
- TypeScript with strict typing
- Component-based React architecture
- Tailwind CSS for styling
- Prisma ORM for database operations

### **Key Commands**
```bash
npm run dev              # Development server
npm run build            # Production build (includes Prisma generation)
npm run lint             # ESLint checking
npm run type-check       # TypeScript validation
```

### **Database Operations**
```bash
npx prisma generate      # Generate Prisma client
npx prisma db push       # Push schema changes
npx prisma studio        # Database GUI
```

## 🏗️ **Architecture Recommendations**

### **State Management Strategy: Zustand**

Quest Core uses Zustand for complex state management, particularly for AI features and multi-coach conversations.

#### **Why Zustand for Quest Core**
- **Lightweight**: ~2KB vs Redux's ~15KB bundle size
- **TypeScript-first**: Excellent TypeScript support out of the box
- **No boilerplate**: Direct state updates without actions/reducers
- **React 18 compatible**: Works seamlessly with Suspense and concurrent features
- **Perfect for AI features**: Ideal for coaching state, conversation management, and generative UI

#### **Implementation Pattern**
```typescript
// stores/coaching-store.ts
import { create } from 'zustand'

interface CoachingState {
  currentCoach: 'master' | 'career' | 'skills' | 'leadership' | 'network'
  conversationHistory: Message[]
  zepContext: ZepContext | null
  generativeUI: GenerativeUIState | null
  
  // Actions
  switchCoach: (coach: CoachType) => void
  addMessage: (message: Message) => void
  updateContext: (context: ZepContext) => void
  updateGenerativeUI: (ui: GenerativeUIState) => void
}

export const useCoachingStore = create<CoachingState>((set) => ({
  currentCoach: 'master',
  conversationHistory: [],
  zepContext: null,
  generativeUI: null,
  
  switchCoach: (coach) => set({ currentCoach: coach }),
  addMessage: (message) => set((state) => ({ 
    conversationHistory: [...state.conversationHistory, message] 
  })),
  updateContext: (context) => set({ zepContext: context }),
  updateGenerativeUI: (ui) => set({ generativeUI: ui })
}))
```

#### **Usage in Components**
```typescript
// components/voice/CoachingInterface.tsx
import { useCoachingStore } from '@/stores/coaching-store'

export function CoachingInterface() {
  const { currentCoach, switchCoach, conversationHistory } = useCoachingStore()
  
  return (
    <div>
      <CoachSelector current={currentCoach} onSwitch={switchCoach} />
      <ConversationView messages={conversationHistory} />
    </div>
  )
}
```

### **API-First Design Pattern**

Quest Core follows an API-first architecture that separates concerns cleanly while enabling external service integration.

#### **Service Layer Pattern**
```typescript
// lib/services/ai-orchestrator.ts
export class AIOrchestrator {
  constructor(
    private openRouter: OpenRouterClient,
    private zepClient: ZepClient,
    private pocketFlow?: PocketFlowService
  ) {}

  async processCoachingSession(userId: string, message: string, coach: CoachType) {
    // 1. Get contextual memory
    const context = await this.zepClient.getContext(userId)
    
    // 2. Route to appropriate model via OpenRouter
    const modelConfig = this.getModelForCoach(coach)
    const response = await this.openRouter.chat(message, context, modelConfig)
    
    // 3. Optional: Enhance with PocketFlow experimental features
    const enhanced = this.pocketFlow 
      ? await this.pocketFlow.enhance(response)
      : response
    
    // 4. Update memory
    await this.zepClient.updateMemory(userId, enhanced)
    
    return enhanced
  }
  
  private getModelForCoach(coach: CoachType): ModelConfig {
    const modelMap = {
      master: { model: 'openai/gpt-4-turbo', temperature: 0.7 },
      career: { model: 'anthropic/claude-3-sonnet', temperature: 0.6 },
      skills: { model: 'openai/gpt-4', temperature: 0.5 },
      leadership: { model: 'google/gemini-pro', temperature: 0.7 },
      network: { model: 'anthropic/claude-3-sonnet', temperature: 0.6 }
    }
    return modelMap[coach]
  }
}
```

#### **Integration in API Routes**
```typescript
// app/api/coaching/session/route.ts
import { AIOrchestrator } from '@/lib/services/ai-orchestrator'

const orchestrator = new AIOrchestrator(
  openRouterClient,
  zepClient,
  pocketFlowService
)

export async function POST(request: NextRequest) {
  const { userId, message, coach } = await request.json()
  
  const response = await orchestrator.processCoachingSession(userId, message, coach)
  
  return NextResponse.json({ response })
}
```

### **Microservices Strategy: When NOT to Use Them**

Quest Core deliberately avoids microservices architecture at current scale.

#### **Current Architecture (Recommended)**
```
Quest Core Monolith (Next.js)
├── Frontend (React/TypeScript)
├── API Routes (Next.js serverless)
├── Database (PostgreSQL)
└── External Services
    ├── OpenRouter (AI Gateway)
    ├── Zep (Memory Management)
    ├── Hume AI (Voice Processing)
    └── PocketFlow (AI Experimentation)
```

#### **Why Monolith + External Services**
1. **Team Size**: Small teams benefit from monolithic simplicity
2. **Development Speed**: Faster iteration and debugging
3. **Deployment Simplicity**: Single deployment pipeline
4. **Current Scale**: Microservices complexity not justified
5. **Language Flexibility**: Can still use Python for specialized AI services

#### **External Service Integration Pattern**
```typescript
// lib/integrations/pocketflow-service.ts
export class PocketFlowService {
  async enhanceCoachingResponse(response: string, userContext: any) {
    // Call external Python service for AI enhancement
    const enhanced = await fetch('/api/pocketflow/enhance', {
      method: 'POST',
      body: JSON.stringify({ response, context: userContext })
    })
    return enhanced.json()
  }
}
```

### **Technology Integration Philosophy**

#### **React + Node.js + External Services**
- **Frontend**: React/TypeScript for sophisticated user interfaces
- **Backend**: Node.js/Next.js for web APIs and business logic
- **AI Services**: External Python services (PocketFlow) for specialized processing
- **Data Layer**: PostgreSQL as single source of truth with specialized systems (Zep for memory)

#### **Integration Benefits**
- Best tool for each layer
- Maintain development velocity
- Enable specialized AI capabilities
- Avoid premature architecture complexity

## 🔑 **Environment Variables**

### **Required Services**
- **Database**: Neon PostgreSQL connection ✅
- **Authentication**: Clerk keys (public/secret) ✅
- **AI Gateway**: OpenRouter API key for multi-model access ✅ **OPEN_ROUTER_API_KEY**
- **Voice AI**: Hume AI credentials for empathic voice processing ✅
- **Memory**: Zep API key and configuration (pending setup)
- **Generative UI**: thesys.dev C1 API credentials (future)
- **Deployment**: Vercel integration ✅

### **AI Gateway Configuration**
```env
# OpenRouter for multi-model routing
OPEN_ROUTER_API_KEY=your_openrouter_key  # ✅ Configured
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Model selection for different coaches
COACH_MODEL_MASTER=openai/gpt-4-turbo
COACH_MODEL_CAREER=anthropic/claude-3-sonnet
COACH_MODEL_SKILLS=moonshotai/kimi-k2         # Updated: Superior coding performance
COACH_MODEL_LEADERSHIP=google/gemini-pro
COACH_MODEL_NETWORK=anthropic/claude-3-sonnet
COACH_MODEL_TECHNICAL=moonshotai/kimi-k2:free # NEW: Free tier for technical tasks

# Cost optimization settings
OPENROUTER_PREFER_COST=true
OPENROUTER_FALLBACK_ENABLED=true

# thesys.dev C1 API for generative UI
THESYS_API_KEY=your_thesys_api_key
THESYS_BASE_URL=https://api.thesys.dev/c1
THESYS_MODEL=claude-3-sonnet  # Model for UI generation
THESYS_STREAMING=true         # Enable real-time UI updates
```

### **Configuration Files**
- `.env.local` - Local development environment
- `.env.example` - Template with required variables
- `prisma/schema.prisma` - Database schema definition

## 🎤 **Voice Coaching Integration**

### **Hume AI EVI 3 Setup (V2)**
- **Speech-to-Speech**: Direct voice processing without text pipeline
- **Voice Cloning**: Unique personality for each coach (30 second samples)
- **Multi-LLM Integration**: Seamless switching between Claude 4, Kimi K2, GPT-4
- **Emotional Intelligence**: Superior empathy and naturalness vs GPT-4o
- **Mandatory Migration**: EVI 2 sunsets August 30, 2025

### **Coach Voice Personas**
- **Biographer**: Warm, patient narrator (think David Attenborough)
- **Pattern Seeker**: Insightful analyst (think Malcolm Gladwell)
- **Career Coach**: Professional mentor voice
- **Skills Coach**: Technical but encouraging (powered by Kimi K2)
- **Leadership Coach**: Authoritative yet supportive
- **Network Coach**: Socially savvy connector

### **Voice Session Flow**
1. User initiates voice session via interface
2. EVI 3 processes speech directly (no text conversion)
3. System routes to appropriate LLM based on coach type
4. Voice cloned coach responds with emotional understanding
5. Session insights stored in both Zep and PostgreSQL

### **Migration Documentation**
- See `V2_EVI3_MIGRATION.md` for complete implementation guide

## 🎨 **Generative UI Integration**

### **thesys.dev C1 API Pattern**
Quest Core leverages thesys.dev for cutting-edge generative UI experiences that adapt to each user's professional development journey. Interfaces evolve in real-time based on user progress, Trinity insights, and coaching context.

```typescript
// Dynamic interface generation
const generateAdaptiveInterface = async (userContext: UserContext) => {
  const thesysClient = new ThesysClient({
    apiKey: process.env.THESYS_API_KEY,
    model: process.env.THESYS_MODEL
  });
  
  const interfaceSpec = await thesysClient.generateInterface({
    userState: userContext.currentState,
    trinityData: userContext.trinity,
    coachingProgress: userContext.progress,
    adaptationRules: getQuestCoreAdaptationRules()
  });
  
  return interfaceSpec;
};
```

### **Quest Core Use Cases**
- **Adaptive Trinity Discovery**: Interface elements that evolve based on user responses
- **Dynamic Coaching Dashboards**: Real-time layout changes based on session progress
- **Personalized Skill Development**: Custom interface flows per user's learning style
- **Context-Aware Profile Builder**: Adaptive forms that respond to user's professional context
- **Real-Time Coaching Sessions**: Voice coaching interfaces that update during conversation

### **Integration with Existing Systems**
```typescript
// Combine Zep context with generative UI
const contextualInterface = async (userId: string, sessionType: string) => {
  const zepContext = await getCoachingContext(userId);
  const uiGeneration = await thesysClient.generateCoachingInterface({
    userHistory: zepContext.relevantFacts,
    currentFocus: sessionType,
    trinityState: zepContext.trinity,
    adaptiveElements: getQuestCoreUIElements()
  });
  
  return uiGeneration;
};
```

## 🎨 **Design System & Brand Standards**

### **Quest Premium Visual Language**
Quest Core employs a sophisticated design system that positions the platform as a premium, cutting-edge professional development solution.

#### **Core Design Principles**
1. **Premium & Professional**: Sophisticated visual language building enterprise trust
2. **Innovation Leadership**: Cutting-edge design positioning Quest ahead of competitors  
3. **Data-Driven Beauty**: Complex professional data presented elegantly
4. **Adaptive Excellence**: Seamless integration with thesys.dev generative UI
5. **Journey Metaphor**: Visual elements reinforcing professional growth narrative

#### **Color System**
```css
/* Primary Brand Colors */
--quest-primary: #00D4B8;        /* Aurora Fade (Teal) */
--quest-secondary: #4F46E5;      /* Electric Violet (Blue) */
--quest-accent: #8B5CF6;         /* Purple */

/* Gradients */
--quest-gradient-primary: linear-gradient(135deg, #00D4B8 0%, #4F46E5 100%);
--quest-sphere-gradient: radial-gradient(circle at 30% 30%, #00D4B8, #4F46E5, #8B5CF6);
```

#### **Typography System**
- **Primary Font**: GT Walsheim (premium, professional)
- **Hierarchy**: H1 48px, H2 36px, Body 16px, Caption 12px
- **Usage**: Clean, modern typography with sophisticated weight variations

#### **Quest-Specific UI Patterns**
- **Trinity Visualization**: Interconnected cards with gradient treatments
- **Professional Network Graphs**: Profile photos with gradient borders
- **AI Coaching Interface**: Specialist coach cards with visual hierarchy
- **3D Spherical Elements**: Distinctive gradient spheres reinforcing journey metaphor

### **thesys.dev Brand Compliance**
When generating adaptive interfaces, ensure:
```typescript
// Brand compliance rules for generative UI
const questUIRules = {
  colorPalette: ['#00D4B8', '#4F46E5', '#8B5CF6', '#1A1D29'],
  typography: 'GT Walsheim',
  componentStyle: 'premium-dark',
  gradientUsage: 'selective-emphasis',
  animations: 'subtle-professional'
};
```

### **Component Standards**
- **Cards**: Dark backgrounds (#1A1D29) with subtle borders
- **Buttons**: Gradient treatments for primary actions
- **Forms**: Clean inputs with Quest color focus states
- **Data Visualization**: Professional graph styling with brand colors

## ⚡ **AI Development & Experimentation**

### **PocketFlow Integration Pattern**
Quest Core leverages PocketFlow as a rapid development and experimentation tool for AI innovation, enabling 10x faster prototyping of advanced coaching patterns.

```python
# Rapid prototyping with PocketFlow
trinity_debate = PocketFlow()
  .add_agent("quest_challenger", model="claude-3-sonnet")
  .add_agent("service_advocate", model="gpt-4") 
  .add_agent("pledge_validator", model="gemini-pro")
  .debate("trinity_coherence", rounds=3)
  .synthesize("trinity_insights")
```

### **Development Workflow**
```
Idea → PocketFlow Prototype → Validation → Quest Core Implementation
```

### **Use Cases**
- **Rapid Prototyping**: Test new coaching patterns before production implementation
- **AI Microservices**: Build specialized backend services for complex coaching workflows
- **Agent Development**: Leverage "agentic coding" for rapid coaching specialization development
- **Innovation Pipeline**: Continuous experimentation with cutting-edge AI coaching techniques

### **Integration Architecture**
```typescript
// Quest Core (TypeScript) ↔ PocketFlow Services (Python)
const pocketflowService = await fetch('/api/pocketflow/coaching-analysis', {
  method: 'POST',
  body: JSON.stringify({
    conversationData: zepContext,
    analysisType: 'trinity-evolution-prediction'
  })
});
```

## 🧠 **AI Context Engineering**

### **Zep Integration Pattern**
```typescript
// User session management
const sessionId = await zep.memory.add_session({
  session_id: generateSessionId(),
  user_id: clerkUserId,  // Consistent ID across systems
  metadata: { sessionType, coach }
});

// Context retrieval
const relevantFacts = await zep.graph.search({
  user_id: userId,
  query: userMessage,
  limit: 3,
  min_score: 0.7
});
```

### **Multi-Coach Orchestration with AI Gateway**
- OpenRouter.AI for intelligent model routing per coach type
- Master Coach (GPT-4): Complex orchestration and final authority
- Career Coach (Claude-3): Strategic analysis and market insights  
- **Skills Coach (Kimi K2)**: Technical assessment with 65.8% SWE-bench accuracy
- Leadership Coach (Gemini Pro): Interpersonal and management growth
- Network Coach (Claude-3): Relationship and networking strategy
- **Technical Coach (Kimi K2 Free)**: Cost-free code generation and testing
- Cost optimization through automatic model selection

### **Kimi K2 Cost Optimization Strategy**
- **10x Cost Reduction**: $0.15/M tokens vs Claude's $3/M for technical tasks
- **Free Tier Usage**: Zero-cost test generation, documentation, and scaffolding
- **Performance**: Outperforms GPT-4 on coding benchmarks (65.8% vs 54.6% SWE-bench)
- **Use Cases**:
  - Skills assessment and technical interviews
  - Automated test suite generation
  - Code review and refactoring suggestions
  - Trinity pattern analysis algorithms
  - Documentation updates and API specs

### **AI Client Abstraction Pattern**
```typescript
// AI routing with OpenRouter
const aiClient = new AIClient({
  baseURL: process.env.OPENROUTER_BASE_URL,
  apiKey: process.env.OPENROUTER_API_KEY
});

// Model selection by coach type
const getCoachResponse = async (coach: CoachType, context: ZepContext) => {
  const model = selectModelForCoach(coach);
  return await aiClient.chat.completions.create({
    model,
    messages: buildCoachPrompt(coach, context),
    temperature: getTemperatureForCoach(coach)
  });
};
```

## 📊 **Data Flow Architecture**

### **User ID Strategy**
- **Master ID**: Clerk user ID used across all systems
- **PostgreSQL**: Stores user with Clerk ID as primary key
- **Zep**: Uses same Clerk ID for consistency
- **Neo4j** (future): Will use Clerk ID for user nodes

### **Sync Strategy**
```typescript
// After each coaching session
const insights = await zep.memory.get_session_summary(sessionId);
await prisma.userInsight.create({
  data: {
    userId: clerkUserId,
    insights: insights.key_points,
    trinityUpdates: insights.extracted_trinity,
    sourceSystem: 'zep'
  }
});
```

## 🚀 **Deployment & Operations**

### **Auto-Fix System**
- GitHub Actions workflow for deployment monitoring
- Automatic error detection and correction
- 5-attempt retry logic with manual fallback
- Zero-approval development operations

### **MCP-Vercel Integration**
- Real-time deployment status monitoring
- Automatic failure detection
- Integration with Claude Code for hands-free fixes

## 🔒 **Security & Privacy**

### **User Data Protection**
- Four-layer privacy model with granular control
- Clerk authentication with secure session management
- Encrypted context storage in Zep
- GDPR-compliant data handling

### **API Security**
- Environment-based configuration
- Secure API key management
- User isolation in all data systems

## 📚 **Key Documentation Files**

### **Architecture Documents**
- `DATA_ARCHITECTURE.md` - Complete data strategy
- `ZEP_INTEGRATION.md` - Zep implementation details
- `OPENROUTER_INTEGRATION.md` - AI gateway implementation guide
- `GENERATIVE_UI.md` - thesys.dev integration and adaptive interfaces
- `DESIGN_SYSTEM.md` - Premium visual language and brand standards
- `POCKETFLOW_EVALUATION.md` - AI development acceleration strategy
- `MULTI_COACH_AI_ARCHITECTURE.md` - AI coaching system design
- `V2_LINKEDIN_MIRROR_USE_CASE.md` - Journey visualization and mirror concept
- `V2_JOURNEY_GRAPH_VISUAL_DESIGN.md` - Detailed visual specifications

### **Status Documents**
- `CURRENT_STATUS.md` - Development progress
- `NEXT_SESSION_TODO.md` - Immediate priorities
- `PRODUCT_REQUIREMENTS.md` - V1 feature specifications
- **`V2_PRODUCT_REQUIREMENTS.md`** - 🎯 **SINGLE SOURCE OF TRUTH FOR V2**
- `V2_PROJECT_EVOLUTION_COMPARISON.md` - Comprehensive comparison of all project phases

### **Process Documents**
- `DEVELOPMENT.md` - Development workflows
- `AUTO_FIX_SYSTEM.md` - Deployment automation
- `VOICE_INTEGRATION_SUCCESS.md` - Voice setup guide

## 🎯 **Success Metrics**

### **User Experience**
- Trinity completion and evolution tracking
- Voice coaching engagement and satisfaction
- Goal achievement and progress monitoring
- Professional development outcomes

### **Technical Performance**
- Zep context retrieval latency (target: <300ms)
- Voice coaching response quality
- Multi-coach conversation coherence
- Deployment reliability (99%+ uptime)

## 🤝 **Contributing Guidelines**

### **Development Workflow**
1. Read relevant documentation files
2. Update `CURRENT_STATUS.md` with progress
3. Use auto-fix system for deployment errors
4. Maintain consistent user ID strategy
5. Test both voice and web interfaces

### **Code Review Focus**
- TypeScript type safety
- Zep integration patterns
- User data privacy compliance
- Voice coaching UX quality

## 🎭 **V2 Journey Visualization Implementation Notes**

### **LinkedIn Mirror Technical Flow**
```typescript
// 1. Scrape LinkedIn with user consent
const profile = await apifyClient.scrapeLinkedInProfile(url);

// 2. Analyze with Kimi K2 (cost-effective)
const mirror = await kimiK2.analyzeProfessionalMirror(profile);

// 3. Create journey nodes from experience
const nodes = createJourneyNodes(profile.experience, profile.education);

// 4. Add pulsing quest node based on conversation
const questNode = detectQuestFromConversation(zepContext);

// 5. Update voice coaching based on proximity
const voiceConfig = modulateVoiceByQuestProximity(questNode.distance);
```

### **Key V2 Features**
- **Immediate Value**: Users get LinkedIn improvements in <3 minutes
- **Visual Memory**: Journey graph becomes persistent visual anchor
- **Conversational Evolution**: Graph updates as coaches discover more
- **Trust Through Transparency**: "Here's what we see (and might miss)"

## 📊 **Project Evolution Insights**

### **Key Learnings from Legacy → Current → V2**
Based on comprehensive comparison analysis:
- **Legacy Platform Score**: 6.5/10 - Good vision but overengineered
- **Current Quest Core**: 7.6/10 - Revolutionary Trinity but incomplete
- **V2 Documentation**: 9.1/10 - Philosophy + technology fusion

### **Critical V2 Success Factors**
1. **Document Missing Services**: Tavily, LinkUp web search
2. **Position Neo4j Correctly**: Phase 2 for relationships, not "future"
3. **Security Hardening**: Learn from past API key incidents
4. **Preserve Innovations**: Multi-agent patterns, web intelligence
5. **Maintain Philosophy**: Resist feature creep with manifesto discipline

See `V2_PROJECT_EVOLUTION_COMPARISON.md` for complete analysis.

## 📚 **Recent Learnings & Documentation Updates** (December 2024)

### **Agent-Based Development Insights**
- **Rob Shocks Stack Validation**: Nearly identical to Quest (Next.js, Prisma, Neon, Clerk, Tailwind)
- **Agent Workflows**: Specialized agents with 200k token windows each
- **PG Vector**: Use with Neon for semantic Trinity matching
- **21st.dev Magic MCP**: Add delightful micro-interactions
- **Whimsy Injector**: Proactive agent for adding delight after UI changes
- **Arcade.dev Revolution**: Cole Medin's solution for scaling AI agents from demos to production
  - Solves the "authentication wall" preventing AI agents from taking real actions
  - Enables just-in-time OAuth flows for user services (Gmail, LinkedIn, etc.)
  - Transforms Quest from passive recommendations to active career acceleration

### **New Documentation**
- `QUEST_AGENT_WORKFLOW_LEARNINGS.md` - AI Labs HIVE methodology
- `QUEST_ROB_SHOCKS_STACK_ANALYSIS.md` - Stack validation and enhancements
- `QUEST_V2_PHOENIX_RESTART.md` - Turn and burn restart plan with BMAD + agents
- `QUEST_IMPLEMENTATION_STRATEGY.md` - V2 implementation roadmap
- `PLACEMENT_AGENTS_PLATFORM.md` - Placement agents platform proposal
- `QUEST_ECOSYSTEM_IDEAS.md` - Complete Quest product ecosystem vision
- `PLACEMENT_AGENTS_CONTENT_STRATEGY.md` - Sanity MCP content strategy
- `QUEST_PR_PLATFORM.md` - AI-powered PR platform architecture
- `CONTENT_IDEATION_ENGINE.md` - Automated content ideation workflows
- `ARCADE_INTEGRATION_ANALYSIS.md` - Comprehensive Arcade.dev evaluation
- `ARCADE_IMPLEMENTATION_GUIDE.md` - Step-by-step integration guide
- `QUEST_CORE_ARCADE_WORKFLOWS.md` - AI-powered career automation workflows

### **Key Takeaways**
1. **Validation**: Our tech choices are industry best practices
2. **Agent Workflows**: Specialized agents dramatically improve quality
3. **Whimsy Matters**: Micro-interactions differentiate great apps
4. **PG Vector**: Perfect for Trinity-to-job semantic matching
5. **Ecosystem Strategy**: Three products sharing infrastructure
6. **Content at Scale**: AI-powered ideation and generation
7. **Voice-First**: Conversational interfaces across all products
8. **Action-First**: Arcade.dev enables AI to take authenticated actions (apply to jobs, send emails, etc.)
9. **Scale Ready**: Move from single-user demos to millions with user-specific auth

## 🚀 **Claude Code Enhancement Opportunities**

### **Sub-Agents for Quest Core V2**

Consider upgrading Claude Code to latest version (1.0.60+) to leverage sub-agents feature for:

#### **Proposed Sub-Agents**
1. **Style Guide Compliance Agent**
   - Validates UI components against V2_STYLE_GUIDE.md
   - Checks design tokens, accessibility standards
   - Ensures consistent Quest visual language

2. **Security Scanner Agent**
   - Runs Semgrep patterns on code changes
   - Validates data privacy compliance
   - Checks for exposed secrets/keys

3. **Trinity Alignment Agent**
   - Validates features against manifesto principles
   - Ensures every change serves Story → Trinity → Quest journey
   - Maintains philosophical integrity

4. **Database Migration Agent**
   - Handles Prisma schema changes safely
   - Validates migrations before applying
   - Manages rollback strategies

5. **API Integration Agent**
   - Specializes in OpenRouter/Zep/Apify patterns
   - Knows common gotchas and best practices
   - Maintains consistent error handling

#### **Benefits**
- Preserve main conversation context
- Delegate specialized tasks efficiently
- Create reusable expertise domains
- Reduce cognitive load on main Claude instance

---

**Quest Core** - Discover your authentic professional identity through AI-powered coaching and intelligent skill development.

*Built with ❤️ using Cole Medin's context engineering patterns and Zep's temporal knowledge graphs*