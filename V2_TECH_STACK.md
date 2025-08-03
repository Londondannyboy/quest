# Quest Core V2 - Complete Technology Stack

> **Comprehensive reference of all technologies, services, and tools used in Quest Core V2**

Last Updated: 2025-07-26

---

## 📋 Table of Contents

1. [Core Technologies](#core-technologies)
2. [AI & Voice Services](#ai--voice-services)
3. [Data & Storage](#data--storage)
4. [Scraping & Automation](#scraping--automation)
5. [Authentication & Security](#authentication--security)
6. [Monitoring & Analytics](#monitoring--analytics)
7. [Testing Frameworks](#testing-frameworks)
8. [Development Tools](#development-tools)
9. [MCP Servers](#mcp-servers)
10. [Design & UI](#design--ui)
11. [Deployment & Infrastructure](#deployment--infrastructure)
12. [Future/Planned Technologies](#futureplanned-technologies)

---

## 🎯 Core Technologies

### Next.js 15
- **Purpose**: Full-stack React framework for production
- **Version**: 15.x (App Router, Server Components)
- **Website**: https://nextjs.org/
- **Documentation**: https://nextjs.org/docs
- **Key Features Used**:
  - App Router with nested layouts
  - Server Components for performance
  - API Routes for backend logic
  - Middleware for auth protection
- **Related Files**: `next.config.js`, `app/` directory

### React 18
- **Purpose**: UI component library
- **Version**: 18.x (with Concurrent Features)
- **Website**: https://react.dev/
- **Documentation**: https://react.dev/learn
- **Key Features Used**:
  - Server Components
  - Suspense boundaries
  - Concurrent rendering
- **Related Files**: All `.tsx` components

### TypeScript
- **Purpose**: Type-safe JavaScript
- **Version**: 5.x
- **Website**: https://www.typescriptlang.org/
- **Documentation**: https://www.typescriptlang.org/docs/
- **Configuration**: Strict mode enabled
- **Related Files**: `tsconfig.json`

### Tailwind CSS
- **Purpose**: Utility-first CSS framework
- **Version**: 3.x
- **Website**: https://tailwindcss.com/
- **Documentation**: https://tailwindcss.com/docs
- **Custom Config**: Quest design system tokens
- **Related Files**: `tailwind.config.js`, `globals.css`

---

## 🤖 AI & Voice Services

### OpenRouter
- **Purpose**: AI gateway for multi-model routing and cost optimization
- **Website**: https://openrouter.ai/
- **Documentation**: https://openrouter.ai/docs
- **Models Used**:
  - GPT-4 Turbo (Master Coach)
  - Claude-3 Sonnet (Career/Network Coach)
  - Gemini Pro (Leadership Coach)
  - **NEW**: Kimi K2 (Skills Coach & Technical Tasks)
- **Cost Savings**: 40-60% vs direct API calls
- **Related Files**: `OPENROUTER_INTEGRATION.md`

### Kimi K2 (Moonshot AI)
- **Purpose**: Cost-effective AI model for coding and technical tasks
- **Website**: https://moonshotai.github.io/Kimi-K2/
- **Documentation**: https://platform.moonshot.ai/docs
- **Model Variants**:
  - `moonshotai/kimi-k2`: Paid version ($0.15/$2.50 per million tokens)
  - `moonshotai/kimi-k2:free`: Free tier on OpenRouter
- **Key Strengths**:
  - 65.8% SWE-bench accuracy (vs Claude's 50.2%)
  - 10x cheaper than Claude Sonnet 4
  - Excellent at coding, math, and tool use
  - 1 trillion parameters (32B active)
- **Quest Core Use Cases**:
  - Test generation and code scaffolding
  - Trinity pattern analysis algorithms
  - Technical documentation updates
  - Skills assessment automation
- **Limitations**: Slower output (34 tokens/sec vs Claude's 91)

### Hume AI EVI 3 (V2)
- **Purpose**: Empathic voice conversations with emotional intelligence
- **Version**: EVI 3 (mandatory for V2 - EVI 2 sunsets Aug 2025)
- **Website**: https://www.hume.ai/
- **Documentation**: https://dev.hume.ai/docs
- **Key Features**:
  - **NEW**: Speech-to-speech architecture (no text pipeline)
  - **NEW**: Voice cloning (30 seconds = unique coach voice)
  - **NEW**: Multi-LLM integration (Claude 4 + Kimi K2 + GPT-4)
  - Real-time voice processing
  - Emotional context understanding
  - Superior to GPT-4o in empathy & naturalness
- **Quest Core Use**:
  - Unique voice for each coach persona
  - Direct emotional understanding
  - Seamless model switching mid-conversation
- **Related Files**: `V2_EVI3_MIGRATION.md`, `VOICE_INTEGRATION_SUCCESS.md`

### Zep
- **Purpose**: Long-term memory management for AI conversations
- **Website**: https://www.getzep.com/
- **Documentation**: https://docs.getzep.com/
- **Key Features**:
  - Temporal knowledge graphs
  - Fact extraction
  - Session management
- **Related Files**: `ZEP_INTEGRATION.md`

### Graphiti
- **Purpose**: Temporal knowledge graph framework for Trinity evolution tracking
- **Website**: https://github.com/getzep/graphiti
- **Documentation**: https://docs.getzep.com/graphiti
- **Key Features**:
  - **Bi-temporal data model**: Tracks event time AND ingestion time
  - **Real-time incremental updates**: No batch processing delays
  - **Hybrid retrieval**: Semantic + keyword + graph traversal
  - **Point-in-time queries**: "What was your Trinity 6 months ago?"
- **Quest Core Use Cases**:
  - Trinity evolution visualization over time
  - Professional journey timeline with temporal context
  - Story → Trinity → Quest progression tracking
  - Dynamic relationship mapping as story unfolds
- **Integration**: Works alongside Zep for enhanced temporal intelligence
- **Status**: Phase 2 priority for journey visualization

### PocketFlow
- **Purpose**: Rapid AI prototyping and experimentation
- **Website**: https://github.com/pocketflow/pocketflow
- **Documentation**: https://pocketflow.dev/docs
- **Use Cases**:
  - Multi-agent debates
  - Rapid coaching pattern testing
  - Python microservices
- **Related Files**: `POCKETFLOW_EVALUATION.md`

---

## 💾 Data & Storage

### PostgreSQL (Neon)
- **Purpose**: Primary relational database
- **Website**: https://neon.tech/
- **Documentation**: https://neon.tech/docs
- **Features**:
  - Serverless Postgres
  - Branching for development
  - Auto-scaling
- **Related Files**: `prisma/schema.prisma`

### Prisma
- **Purpose**: Type-safe database ORM
- **Version**: 5.x
- **Website**: https://www.prisma.io/
- **Documentation**: https://www.prisma.io/docs
- **Features**:
  - Schema-first development
  - Migrations
  - Type generation
- **Related Files**: `prisma/`, `lib/prisma.ts`

### Neo4j
- **Purpose**: Graph database for professional relationships and Trinity intelligence
- **Website**: https://neo4j.com/
- **Documentation**: https://neo4j.com/docs/
- **Use Cases**:
  - Professional relationship mapping and analysis
  - Trinity pattern recognition across users
  - Career path intelligence and recommendations
  - Network effect insights and connections
  - Quest similarity and clustering
- **Integration**: Works alongside PostgreSQL - relational data in Postgres, graph intelligence in Neo4j
- **Status**: Phase 2 priority for relationship features

---

## 🕷️ Scraping & Automation

### Tavily
- **Purpose**: AI-powered web search for professional content discovery
- **Website**: https://tavily.com/
- **Documentation**: https://docs.tavily.com/
- **Use Cases**:
  - Discover user's articles, talks, and thought leadership
  - Find GitHub contributions and open source work
  - Research industry trends and insights
  - Enhance "shock & awe" registration beyond LinkedIn
- **Pricing**: Free tier (1K/month), Starter $50/month (25K searches)
- **Status**: Phase 2 enhancement
- **Related Files**: `V2_WEB_SEARCH_INTEGRATION.md`

### LinkUp
- **Purpose**: Real-time job market intelligence and skills analysis
- **Website**: https://www.linkup.com/
- **Documentation**: https://www.linkup.com/developers/
- **Use Cases**:
  - Current market demand for user's skills
  - Salary benchmarking for Trinity-aligned roles
  - Emerging skills identification
  - Geographic opportunity analysis
- **Pricing**: Custom API pricing (~$500/month)
- **Status**: Phase 3 after product-market fit
- **Related Files**: `V2_WEB_SEARCH_INTEGRATION.md`

### Arcade.dev
- **Purpose**: AI agent authentication and tool-calling platform for user actions
- **Website**: https://arcade.dev/
- **Documentation**: https://docs.arcade.dev/home
- **Key Features**:
  - OAuth 2.0 authentication for user services
  - Pre-built integrations (Gmail, LinkedIn, GitHub, Calendar, etc.)
  - Just-in-time authorization flows
  - User-specific token management
  - LangGraph integration for workflows
- **Use Cases**:
  - Automated job applications via Gmail
  - LinkedIn networking and outreach
  - Calendar scheduling for interviews
  - GitHub project creation for portfolios
  - Cross-platform workflow orchestration
- **Pricing**: 
  - Free tier: 10 MAU, 1,000 calls/month
  - Starter: $50/month (200 MAU, 20K calls)
  - Growth: $200/month (800 MAU, 100K calls)
- **Status**: Priority integration for V2
- **Related Files**: `ARCADE_INTEGRATION_ANALYSIS.md`, `ARCADE_IMPLEMENTATION_GUIDE.md`, `QUEST_CORE_ARCADE_WORKFLOWS.md`

---

## 🕷️ Primary Scraping

### Apify
- **Purpose**: Web scraping platform for professional data
- **Website**: https://apify.com/
- **Documentation**: https://docs.apify.com/
- **Actors Used**:
  - LinkedIn Profile Scraper
  - Twitter/X Scraper
  - GitHub Profile Scraper
  - Reddit Scraper
- **Related Files**: `APIFY_INTEGRATION_FIX.md`, `APIFY_SOLUTIONS.md`

### n8n (Planned)
- **Purpose**: Workflow automation for data orchestration
- **Website**: https://n8n.io/
- **Documentation**: https://docs.n8n.io/
- **Use Cases**:
  - Multi-platform scraping orchestration
  - Rate limit handling
  - Visual workflow debugging
- **Status**: Planned MCP integration

---

## 🔐 Authentication & Security

### Clerk
- **Purpose**: User authentication and management
- **Website**: https://clerk.com/
- **Documentation**: https://clerk.com/docs
- **Features**:
  - Social login (Google, GitHub)
  - User profiles
  - Session management
  - Webhooks for user sync
- **Related Files**: `middleware.ts`, `app/api/clerk-webhook/`

### Semgrep (Planned)
- **Purpose**: Static analysis security scanning
- **Website**: https://semgrep.dev/
- **Documentation**: https://semgrep.dev/docs/
- **Rules**: 5,000+ vulnerability patterns
- **Status**: Planned MCP integration

---

## 📊 Monitoring & Analytics

### Checkly
- **Purpose**: Synthetic monitoring and testing
- **Website**: https://www.checklyhq.com/
- **Documentation**: https://www.checklyhq.com/docs/
- **Features**:
  - API monitoring
  - Browser checks
  - Vercel integration
- **Related Files**: `.checkly/`

### HyperDX
- **Purpose**: Unified observability platform
- **Website**: https://www.hyperdx.io/
- **Documentation**: https://docs.hyperdx.io/
- **Features**:
  - Logs, metrics, traces
  - Session replay
  - Error tracking
- **Status**: Backup monitoring solution

### OpenTelemetry (Future)
- **Purpose**: Observability framework
- **Website**: https://opentelemetry.io/
- **Documentation**: https://opentelemetry.io/docs/
- **Use Case**: Distributed tracing for AI calls
- **Status**: Future implementation

---

## 🧪 Testing Frameworks

### Vitest
- **Purpose**: Unit testing framework (4x faster than Jest)
- **Website**: https://vitest.dev/
- **Documentation**: https://vitest.dev/guide/
- **Features**:
  - ESM first
  - TypeScript support
  - React Testing Library integration
- **Related Files**: `vitest.config.ts`

### Playwright
- **Purpose**: E2E testing and browser automation
- **Website**: https://playwright.dev/
- **Documentation**: https://playwright.dev/docs/intro
- **Features**:
  - Cross-browser testing
  - Visual regression
  - Accessibility testing
- **Related Files**: `playwright.config.ts`, `e2e/`

### Testing Library
- **Purpose**: React component testing utilities
- **Website**: https://testing-library.com/
- **Documentation**: https://testing-library.com/docs/react-testing-library/intro/
- **Packages**:
  - @testing-library/react
  - @testing-library/jest-dom
  - @testing-library/user-event

---

## 🛠️ Development Tools

### Zustand
- **Purpose**: Lightweight state management
- **Website**: https://zustand-demo.pmnd.rs/
- **Documentation**: https://github.com/pmndrs/zustand
- **Use Cases**:
  - Coach conversation state
  - UI preferences
  - Complex form state
- **Related Files**: `stores/`

### React Query (TanStack Query)
- **Purpose**: Server state management
- **Website**: https://tanstack.com/query/latest
- **Documentation**: https://tanstack.com/query/latest/docs/react/overview
- **Features**:
  - Data caching
  - Background refetching
  - Optimistic updates

### React Force Graph 3D
- **Purpose**: 3D network visualizations with revolutionary layered system
- **Website**: https://github.com/vasturiano/react-force-graph
- **Documentation**: https://github.com/vasturiano/react-force-graph#readme
- **Version**: Latest (with ForceGraph3D component)
- **Critical Implementation Pattern**:
  ```typescript
  // MUST use dynamic import with SSR disabled
  const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), {
    ssr: false,
    loading: () => <div>Loading 3D Timeline...</div>
  });
  ```
- **Revolutionary Features**:
  - **Transparent Background**: `backgroundColor="transparent"` enables layering
  - **Scene Access**: `graphRef.current.scene()` for custom Three.js objects
  - **Camera Control**: `graphRef.current.cameraPosition()` for positioning
  - **4-Layer Architecture**: Background → Effects → Graph → UI
- **Use Cases**:
  - Trinity evolution visualization
  - Professional journey timeline
  - LinkedIn Mirror with temporal context
  - Quest node pulsing with proximity detection
  - Real-time updates during coaching conversations
- **V1 Achievements**:
  - 12+ working visualization variants
  - "Never seen anything like it" - User feedback
  - Temporal gradients (Past→Present→Future)
  - 2000+ particle systems
  - Morphing geometry animations
- **Key Learnings**: See `V2_3D_VISUALIZATION_LEARNINGS.md`
- **Related Files**: `components/visualization/`, `src/app/test-*/`

### Three.js
- **Purpose**: 3D graphics library for advanced temporal visualizations
- **Website**: https://threejs.org/
- **Documentation**: https://threejs.org/docs/
- **Version**: Latest (with TypeScript support)
- **Critical Import Pattern**:
  ```typescript
  // MUST use direct import for reliability
  import * as THREE from 'three';
  ```
- **Integration with ForceGraph3D**:
  ```typescript
  // Access Three.js scene from ForceGraph
  const scene = graphRef.current.scene();
  
  // Add custom objects
  const bgGroup = new THREE.Group();
  bgGroup.name = 'timeBackground';
  scene.add(bgGroup);
  ```
- **Proven Implementations**:
  - **Temporal Gradients**: Canvas-based gradient textures
  - **Particle Systems**: 2000+ particles with time-based colors
  - **Morphing Geometry**: Real-time deformation animations
  - **Custom Shaders**: GLSL for temporal wave effects
  - **WebGL Renderer**: `{ alpha: true }` for transparency
- **TypeScript Solutions**:
  ```typescript
  // Handle namespace issues pragmatically
  const materials: any[] = [];
  scene.traverse((child: any) => { });
  ```
- **Related Files**: `V2_3D_VISUALIZATION_LEARNINGS.md`

### Framer Motion
- **Purpose**: Animation library
- **Website**: https://www.framer.com/motion/
- **Documentation**: https://www.framer.com/docs/
- **Use Cases**:
  - Page transitions
  - Component animations
  - Gesture handling

---

## 🔌 MCP Servers

### REF MCP
- **Purpose**: Smart documentation with 85% token reduction
- **Status**: Phase 1 - Immediate implementation
- **Repository**: https://github.com/ref-tools/ref-tools-mcp
- **Benefits**:
  - Session-aware search
  - Smart chunking
  - Cost optimization

### Playwright MCP
- **Purpose**: AI-graded UI testing & browser automation
- **Status**: Phase 1 - Immediate implementation
- **Repository**: https://github.com/microsoft/playwright-mcp
- **Use Cases**:
  - Style guide compliance
  - Accessibility validation
  - Visual regression
  - **NEW**: End-to-end user journey testing
  - **NEW**: Browser automation for complex flows
  - **NEW**: Cross-browser compatibility testing

### Semgrep MCP
- **Purpose**: Security vulnerability scanning
- **Status**: Phase 2 - Before user data
- **Repository**: https://github.com/semgrep/semgrep-mcp
- **Rules**: 5,000+ security patterns

### Apify MCP
- **Purpose**: Enhanced web scraping
- **Status**: Phase 2 - High priority
- **Integration**: Access to 5,000+ scrapers

### n8n MCP
- **Purpose**: Workflow automation
- **Status**: Phase 2 - High priority
- **Use Cases**: Scraping orchestration

### Zen MCP
- **Purpose**: Multi-model AI collaboration
- **Status**: Phase 3 - Scale phase
- **Use Cases**: Trinity analysis with different models

### Pieces MCP
- **Purpose**: Developer memory and context
- **Status**: Phase 3 - Team scaling
- **Repository**: https://github.com/pieces-app/pieces-mcp
- **Token overhead**: ~500-1000 per interaction

### Sequential Thinking MCP
- **Purpose**: Structured problem-solving for Trinity analysis
- **Status**: Phase 3 - High priority
- **Repository**: https://github.com/modelcontextprotocol/server-sequential-thinking
- **Use Cases**:
  - Dynamic Trinity pattern recognition
  - Multi-step coaching logic
  - Quest readiness assessment
  - Branching user journey analysis
- **Key Features**:
  - Step-by-step problem breakdown
  - Alternative reasoning paths
  - Context preservation
  - Hypothesis testing

---

## 🎨 Design & UI

### GT Walsheim Font
- **Purpose**: Primary typography
- **License**: Commercial license required
- **Fallback**: System UI fonts
- **Usage**: Headers and body text

### thesys.dev C1 API
- **Purpose**: Generative UI and adaptive interfaces
- **Website**: https://thesys.dev/
- **Documentation**: https://docs.thesys.dev/c1
- **Features**:
  - Real-time UI generation
  - Context-aware layouts
  - Claude-3 Sonnet powered
- **Related Files**: `GENERATIVE_UI.md`

### Design Tokens
- **Purpose**: Consistent design system
- **Colors**:
  - Primary: #00D4B8 (Aurora Fade)
  - Secondary: #4F46E5 (Electric Violet)
  - Accent: #8B5CF6 (Purple)
- **Related Files**: `DESIGN_TOKENS.md`, `V2_STYLE_GUIDE.md`

---

## 🚀 Deployment & Infrastructure

### Vercel
- **Purpose**: Hosting and deployment
- **Website**: https://vercel.com/
- **Documentation**: https://vercel.com/docs
- **Features**:
  - Edge functions
  - Preview deployments
  - Analytics
  - Auto-fix integration
- **Related Files**: `vercel.json`

### GitHub Actions
- **Purpose**: CI/CD and automation
- **Website**: https://github.com/features/actions
- **Documentation**: https://docs.github.com/en/actions
- **Workflows**:
  - Auto-fix deployment
  - Type checking
  - Linting
- **Related Files**: `.github/workflows/`

### MCP-Vercel Integration
- **Purpose**: Deployment monitoring and auto-fixing
- **Features**:
  - Real-time status
  - Automatic error detection
  - Claude Code integration
- **Related Files**: `AUTO_FIX_SYSTEM.md`

---

## 🔮 Future/Planned Technologies

### LangChain (Evaluation)
- **Purpose**: LLM application framework
- **Status**: Under evaluation
- **Alternative**: Current OpenRouter + Zep solution

### Vector Database (TBD)
- **Purpose**: Embedding storage for semantic search
- **Options**: Pinecone, Weaviate, Qdrant
- **Status**: Evaluating need

### Redis (Potential)
- **Purpose**: Caching and session storage
- **Use Case**: High-performance caching layer
- **Status**: If performance requires

### Temporal (Potential)
- **Purpose**: Workflow orchestration
- **Use Case**: Complex multi-step AI workflows
- **Status**: If n8n insufficient

---

## 📚 Documentation References

### Internal Documentation
- `CLAUDE.md` - AI assistant context
- `V2_MCP_INTEGRATION_STRATEGY.md` - MCP roadmap
- `GENERATIVE_UI.md` - thesys.dev patterns
- `DESIGN_SYSTEM.md` - Visual standards
- `DATA_ARCHITECTURE.md` - Data flow strategy

### External Resources
- [Quest Core Manifesto](./QUEST_CORE_MANIFESTO.md)
- [V2 Style Guide](./V2_STYLE_GUIDE.md)
- [Implementation Guide](./QUEST_CORE_V2_IMPLEMENTATION_GUIDE.md)

---

## 🔧 Version Management

### Package Management
- **npm**: Primary package manager
- **Node.js**: v18+ required
- **Package.json**: Central dependency management

### Version Control
- **Git**: Source control
- **GitHub**: Repository hosting
- **Branching**: Feature branches → main

---

## 💡 Quick Reference

### Essential Environment Variables
```env
# Database
DATABASE_URL=             # Neon PostgreSQL

# Authentication  
CLERK_SECRET_KEY=
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=

# AI Services
OPEN_ROUTER_API_KEY=      # AI Gateway
HUME_API_KEY=            # Voice AI
HUME_CLIENT_SECRET=

# Scraping
APIFY_API_TOKEN=         # Web scraping

# Future
ZEP_API_KEY=             # Memory (pending)
THESYS_API_KEY=          # Generative UI (future)
```

### Key Commands
```bash
npm run dev              # Development
npm run build            # Production build
npm run lint             # Linting
npm run type-check       # TypeScript check
npx prisma studio        # Database GUI
npm run test             # Vitest
npm run e2e              # Playwright
```

---

**Last Updated**: 2025-07-26  
**Maintained By**: Quest Core Development Team

### Recent Updates
- Added Sequential Thinking MCP for structured Trinity analysis
- Enhanced Playwright MCP with browser automation capabilities from SuperClaude insights
- Updated MCP server priorities based on Quest Core V2 needs
- **NEW**: Integrated Kimi K2 (Moonshot AI) for cost-effective technical tasks
- **NEW**: Configured Kimi K2 as Skills Coach and added free Technical Coach role
- **NEW**: Upgraded to Hume AI EVI 3 for speech-to-speech and voice cloning
- **NEW**: Documented EVI 3 migration requirements (mandatory by Aug 2025)
- **NEW**: Added LinkedIn Mirror & Journey Visualization use case for V2
- **NEW**: Enhanced React Force Graph for professional journey timeline visualization
- **NEW**: Integrated journey proximity with EVI 3 voice modulation
- **NEW**: Documented Tavily and LinkUp web search integration for Phase 2/3
- **NEW**: Repositioned Neo4j as Phase 2 priority for relationship intelligence
- **NEW**: Added Graphiti temporal knowledge graph framework for Trinity evolution tracking
- **NEW**: Documented revolutionary 3D layered visualization system from V1
- **NEW**: Added React Force Graph 3D transparent background technique
- **NEW**: Preserved Three.js integration patterns and TypeScript solutions
- **NEW**: Created comprehensive project evolution comparison report

*This document serves as the single source of truth for all technologies used in Quest Core V2.*