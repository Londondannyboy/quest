# Quest Core - Clean Restart Context

> **Optimized restart prompt for `/clear` sessions**  
> **Last Updated**: July 19, 2025 - Post Design System Integration

## 🎯 **Essential Project Context**

Quest Core is a revolutionary professional development platform built on a **4-layer repository system** that guides users through discovering their authentic professional identity via the Trinity system: **Quest** (what drives you), **Service** (how you serve), and **Pledge** (what you commit to).

> **Core Innovation**: "LinkedIn shows who you were. Quest shows who you're becoming."

### **Value Proposition**
- **Working Repo**: The missing layer between public LinkedIn profiles and private career planning
- **Selective Portfolio**: Rich multimedia project showcases with granular access control
- **AI-Powered Coaching**: Voice-first coaching with persistent memory and Trinity evolution
- **Premium Experience**: Sophisticated visual language with cutting-edge adaptive interfaces

## 🏗️ **Current Architecture (Stable Foundation)**

### **✅ Production-Ready Systems**
- **Frontend**: Next.js 15, React 18, TypeScript, Tailwind CSS
- **Authentication**: Clerk with PostgreSQL user creation (working)
- **Database**: Neon PostgreSQL with comprehensive 4-layer schema (deployed)
- **Voice Coaching**: Hume AI EVI integration (functional)
- **3D Visualization**: React Force Graph for professional networks (complete)
- **Design System**: Premium visual language with GT Walsheim typography (complete)

### **✅ Completed Major Features**
1. **User Authentication & Profiles**: Clerk → PostgreSQL integration working
2. **Entity-Centric Design**: Companies, skills, institutions as searchable objects
3. **3D Professional Graphs**: Interactive network visualization
4. **Voice Coaching Foundation**: AI coaching with repo context access
5. **Premium Design System**: Complete visual language with DESIGN_SYSTEM.md and DESIGN_TOKENS.md
6. **Auto-Fix Deployment**: Zero-approval error correction system

### **📊 Database Schema Summary**
```
✅ Users: Clerk-integrated with auto database creation
✅ Core Entities: Companies, Skills, Educational Institutions, Certifications  
✅ Surface Repo: Public LinkedIn-style profiles (schema ready)
🚧 Working Repo: Selective portfolio (schema ready, needs implementation)
📝 Personal Repo: Private goals and development tracking (schema ready)
🤖 Deep Repo: AI insights and Trinity analysis (partial - needs enhancement)
🤝 Professional Relationships: Neo4j-ready relationship tracking (schema ready)
```

## 🎯 **Strategic Architecture Decisions (Finalized)**

### **Hybrid Data Strategy**
- **PostgreSQL (Neon)**: Single source of truth for all user data
- **Zep**: Conversational memory and behavioral insights (ready to integrate)
- **OpenRouter**: AI gateway for model routing and cost optimization (ready to integrate)
- **thesys.dev**: Generative UI for adaptive interfaces (ready to integrate)
- **PocketFlow**: AI development acceleration tool (evaluated, ready to use)
- **Neo4j**: Professional relationship graphs (future phase)

### **AI Coaching Architecture**
- **Master Coach**: Orchestrator using OpenRouter model routing
- **Specialist Coaches**: Career, Skills, Leadership, Network coaches with optimized models
- **Shared Context**: All coaches access same Zep user memory
- **Cost Optimization**: 40-60% reduction through intelligent model selection

## 🚀 **Current Implementation Status**

### **✅ COMPLETED (100% Working)**
- Premium design system with complete visual language
- User authentication with database integration
- Profile creation with entity search/creation
- 3D visualization of professional networks
- Voice coaching with repo context
- Auto-fix deployment system
- Comprehensive technical documentation

### **⚠️ HIGH-VALUE IMPLEMENTATION GAPS**
1. **Working Repo** - Core value proposition, schema ready, needs UI implementation
2. **Zep Integration** - Memory foundation for all AI features, fully documented
3. **OpenRouter Integration** - Cost optimization and model specialization
4. **thesys.dev Integration** - Cutting-edge adaptive UI experiences

### **🎯 RECOMMENDED NEXT IMPLEMENTATION**
**Primary Choice**: Working Repo implementation (delivers core user value)
**Alternative**: Complete Zep integration (enables all future AI enhancements)

## 📋 **Immediate Session Priorities**

### **Option A: Working Repo Implementation (RECOMMENDED)**
**Time**: 3-4 hours | **Value**: Highest | **Dependencies**: None
- [ ] Implement Working Repo database models and API endpoints
- [ ] Create selective access control system with permissions
- [ ] Build project showcase and achievement story components  
- [ ] Add multimedia support and portfolio presentation
- [ ] Test complete Working Repo workflow

### **Option B: Complete Zep Integration**
**Time**: 3-4 hours | **Value**: High | **Dependencies**: Zep account
- [ ] Install Zep SDK and configure environment
- [ ] Implement user creation with Clerk ID consistency
- [ ] Enhance voice coaching with persistent memory
- [ ] Create context retrieval for coaching responses
- [ ] Test memory continuity across sessions

### **❌ NOT RECOMMENDED: Multi-System Parallel Implementation**
Previous sessions attempted too many integrations simultaneously, leading to incomplete features.

## 🛠️ **Development Environment**

### **Key Commands**
```bash
npm run dev              # Development server
npm run build            # Production build
npm run lint             # ESLint checking  
npm run type-check       # TypeScript validation
npx prisma generate      # Generate Prisma client
npx prisma db push       # Push schema changes
npx prisma studio        # Database GUI
```

### **Environment Variables (Required)**
```env
# Core Database & Auth (✅ Working)
DATABASE_URL=postgresql://...
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...

# Voice Coaching (✅ Working)  
HUME_API_KEY=...
HUME_SECRET_KEY=...

# AI Integration (Next Implementation)
OPENROUTER_API_KEY=...           # For AI gateway
ZEP_API_KEY=...                  # For memory management
THESYS_API_KEY=...               # For generative UI
```

### **File Structure**
```
quest-core/
├── app/                    # Next.js 15 app router
├── components/             # React components
├── lib/                    # Utilities and integrations
├── prisma/                 # Database schema
├── docs/                   # Technical documentation
├── DESIGN_SYSTEM.md        # Premium visual language guide
├── DESIGN_TOKENS.md        # Tailwind CSS configuration
├── CLAUDE.md               # AI assistant context (comprehensive)
└── NEXT_SESSION_TODO.md    # Sequential implementation priorities
```

## 📚 **Key Documentation Files**

### **Architecture & Implementation**
- **CLAUDE.md**: Complete AI assistant context and development guidelines
- **DESIGN_SYSTEM.md**: Premium visual language and component specifications
- **PRODUCT_REQUIREMENTS.md**: 4-layer repository system and feature specifications
- **DATA_ARCHITECTURE.md**: Hybrid data strategy with PostgreSQL as master
- **NEXT_SESSION_TODO.md**: Sequential implementation priorities (refactored)

### **Integration Guides (Ready to Implement)**
- **ZEP_INTEGRATION.md**: Conversational memory implementation guide
- **OPENROUTER_INTEGRATION.md**: AI gateway integration specifications
- **GENERATIVE_UI.md**: thesys.dev adaptive interface implementation
- **POCKETFLOW_EVALUATION.md**: AI development acceleration strategy

### **Status & Planning**
- **CURRENT_STATUS.md**: Latest achievements and next priorities
- **AUTO_FIX_SYSTEM.md**: Zero-approval deployment automation

## 🎯 **Context for AI Assistant**

### **Development Principles**
1. **Sequential Implementation**: Complete one feature fully before starting next
2. **Value-First Approach**: Prioritize core user value over experimental features  
3. **Modular Architecture**: Clear separation between systems with defined interfaces
4. **Premium Quality**: Sophisticated design system with professional polish
5. **User-Centric**: 4-layer repository system addresses real professional needs

### **What's Working Well**
- Clerk authentication with PostgreSQL integration
- Entity-centric database design with searchable components
- 3D visualization with React Force Graph
- Voice coaching with Hume AI integration
- Premium design system with brand compliance
- Auto-fix deployment system

### **Current Challenges**
- Need to implement core value proposition (Working Repo)
- Multiple AI integration opportunities requiring prioritization
- Balance between innovation and feature completion
- Ensure realistic session scope for complete implementations

### **Success Metrics**
- Feature completeness over partial implementations
- User value delivery over technology experimentation
- Working functionality over architectural complexity
- Clear progress over ambitious parallel development

## 🚀 **Recommended Restart Prompt**

```
Quest Core is a professional development platform with a 4-layer repository system (Surface/Working/Personal/Deep) that helps users discover their authentic professional identity through the Trinity system (Quest/Service/Pledge).

CURRENT STATUS:
✅ Working: User auth (Clerk), database (PostgreSQL), voice coaching (Hume AI), 3D visualization, premium design system
🚧 Next Priority: Choose ONE - Working Repo implementation (core value) OR Zep integration (AI memory foundation)

CONTEXT: Previous sessions attempted parallel implementation of multiple AI systems. This session should focus on completing ONE feature fully.

ARCHITECTURE: Hybrid data strategy with PostgreSQL as master, ready to integrate Zep (memory), OpenRouter (AI gateway), thesys.dev (adaptive UI).

DOCUMENTATION: Comprehensive - see CLAUDE.md for full context, NEXT_SESSION_TODO.md for sequential priorities.

GOAL: Deliver complete working feature rather than incomplete experiments.
```

---

**Restart Optimization**: This context provides essential information for productive session continuation while avoiding overwhelming detail that leads to analysis paralysis.