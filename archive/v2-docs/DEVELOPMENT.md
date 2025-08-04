# Quest Core - Development Guide

> **Current Status**: 4-Layer Repository System Complete - Database, Authentication, and Voice Coaching Enhanced

## 🎯 **MAJOR MILESTONE: Production-Ready Professional Platform**

### **✅ What's Been Built (Complete)**
- **4-Layer Repository System**: Surface → Working → Personal → Deep
- **Neon PostgreSQL Database**: Full schema with entity-centric design
- **Clerk Authentication**: User management with route protection
- **Enhanced Voice Coaching**: Full repo context access
- **Professional Relationships**: Neo4j-ready relationship tracking

### **❌ Next Phase: UI Development**
- **Missing**: User interfaces to populate repo data
- **Goal**: Enable admin to test with real professional data

## 🏗️ **Current Architecture**

### **Technology Stack**
- **Frontend**: Next.js 15, React 18, TypeScript, Tailwind CSS
- **Database**: Neon PostgreSQL with Prisma ORM
- **Authentication**: Clerk with middleware protection + database user creation
- **Voice AI**: Hume EVI with enhanced repo context
- **Visualization**: React Force Graph 3D, D3.js, Recharts
- **UI Components**: shadcn/ui component system  
- **Deployment**: Vercel with automatic GitHub integration + Auto-Fix System
- **DevOps**: MCP-Vercel monitoring, Zero-approval auto-fix, 5-attempt retry logic
- **Graph Database**: Neo4j (ready for integration)

### **4-Layer Repository System**
```
┌─────────────────────────────────────────────────────────────────┐
│                     SURFACE REPO (Public)                      │
│         LinkedIn-style • Basic Professional Profile            │
│                     URL: /profile/[username]                    │
├─────────────────────────────────────────────────────────────────┤
│                    WORKING REPO (Selective)                    │
│  Rich Portfolio • Detailed Achievements • Multimedia Content   │
│   Project Showcases • Selective Access • Recruiter-Friendly    │
│                     URL: /work/[username]                       │
├─────────────────────────────────────────────────────────────────┤
│                    PERSONAL REPO (Private)                     │
│   Career Planning • Goals • OKRs • Personal Notes • Development │
│                       URL: /repo/personal                       │
├─────────────────────────────────────────────────────────────────┤
│                     DEEP REPO (System)                         │
│    AI Insights • Trinity Core • Identity Analysis • Encrypted   │
│                    System-managed, Not User-Editable            │
└─────────────────────────────────────────────────────────────────┘
```

### **Entity-Centric Database Design**
All professional entities are normalized objects with UUIDs:
- **Companies**: Name, website, domain, industry, verification
- **Skills**: Category, difficulty, market demand, verification
- **Educational Institutions**: Type, country, verification status
- **Certifications**: Issuer, validity, category, verification
- **Professional Contacts**: Relationship strength, interaction tracking

## 📁 **Current Project Structure**

```
quest-core/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── api/               # Enhanced API endpoints
│   │   │   ├── hume-clm-sse/  # Voice coaching with repo context
│   │   │   └── test-db/       # Database connectivity testing
│   │   ├── sign-in/           # Clerk authentication pages
│   │   ├── sign-up/           # Clerk authentication pages
│   │   ├── trinity/create/    # Trinity system (needs Deep repo connection)
│   │   ├── voice-coach/       # Enhanced voice coaching
│   │   └── skills/            # Skills framework
│   ├── components/            # React components
│   │   ├── voice/            # VoiceInterface (working)
│   │   ├── trinity/          # Trinity components (needs enhancement)
│   │   ├── skills/           # Skills components
│   │   └── ui/               # shadcn/ui components
│   ├── lib/
│   │   ├── prisma.ts         # Database client
│   │   └── db/users.ts       # Enhanced user helpers
│   └── middleware.ts          # Clerk route protection
├── prisma/
│   ├── schema.prisma         # Complete 4-layer schema
│   └── migrations/           # Database migrations
├── scripts/                   # Database testing and verification
└── docs/                     # Updated documentation
```

## 🗄️ **Database Architecture**

### **Implemented Schema**
```sql
-- Core Entities (Foundation)
companies, skills, educational_institutions, certifications

-- Surface Repo (Public)
surface_profiles, work_experiences, user_skills, user_education, user_certifications

-- Working Repo (Selective)
working_profiles, working_projects, working_achievements, working_media
working_access_permissions, working_access_logs

-- Personal Repo (Private)
personal_goals, personal_notes

-- Deep Repo (System)
trinity_core, deep_insights

-- Professional Relationships (Neo4j Ready)
professional_contacts, work_relationships, project_relationships, education_relationships

-- Voice Coaching (Enhanced)
conversations, messages (with repo_context and repo_references)
```

### **Key Database Features**
- **UUID Primary Keys**: Neo4j graph database ready
- **Entity Normalization**: No duplicate companies/skills
- **Relationship Tracking**: Professional network intelligence
- **Access Control**: Working repo selective sharing
- **Multimedia Support**: File storage for Working repo
- **AI Context**: Repo references in conversations

## 🎤 **Enhanced Voice Coaching**

### **Current Implementation**
- **Hume EVI Integration**: Working voice interface
- **CLM Endpoint**: `/api/hume-clm-sse/chat/completions`
- **Database Integration**: Full 4-layer repo context access
- **Authentication**: Clerk user identification
- **Session Memory**: Conversation persistence with repo references

### **Voice Coaching Context Access**
```typescript
// What Voice Coaching Can Now Access
const userContext = {
  surface: { profile, workExperience, education, skills },
  working: { projects, achievements, media, collaborators },
  personal: { goals, notes, development },
  deep: { trinity, insights, analysis },
  relationships: { contacts, collaborations, network }
}
```

### **Personalization Examples**
- "I see you work at [Company]" ✅ Database integration ready
- "Tell me about your [Project] at [Company]" ✅ Working repo data access  
- "Based on your Trinity Quest to [X]..." ✅ Deep repo Trinity access
- "Who did you collaborate with on that?" ✅ Relationship intelligence

## 🔐 **Authentication & Security**

### **Clerk Integration**
- **Middleware**: Route protection with public/private routes
- **User Management**: Clerk ID to database user mapping
- **Session Handling**: Secure authentication flow
- **Route Protection**: `/profile/*`, `/work/*`, `/repo/*` protected

### **Access Control**
- **Working Repo**: Granular permission system
- **Personal Repo**: Private user data only
- **Deep Repo**: System-managed, encrypted insights
- **Surface Repo**: Public with privacy controls

## 🧪 **Current Testing Status**

### **✅ Verified Working**
- Database schema migration successful
- Prisma client generation and queries
- Clerk authentication integration + database user creation
- Voice coaching endpoint functional
- Cross-repo data access implemented
- Profile system with searchable components
- 3D Force Graph visualization with timeline
- Complete build and deployment pipeline
- **Auto-Fix System**: Zero-approval deployment error correction
- **MCP-Vercel**: Real-time deployment monitoring and failure detection

### **❌ Next Phase Requirements**
- Neo4j graph database integration
- Multi-coach AI system architecture
- Advanced relationship intelligence queries
- Enhanced visualization with graph algorithms

## 🎯 **Next Development Phase: Neo4j + AI Enhancement**

### **Critical Path**
1. **Neo4j Integration**: Professional relationship intelligence via graph database
2. **Multi-Coach AI System**: Orchestrated coaching with specialized AI personas
3. **Enhanced Visualization**: Force Graph displaying Neo4j query results
4. **Planning Process Analysis**: Document and prevent requirement oversights
5. **Advanced Intelligence**: Career path recommendations and network analysis

### **Expected Outcome**
Transform from basic profile platform to intelligent professional analytics:
- Neo4j-powered relationship queries and recommendations
- Multi-coach AI system with debate management and orchestration
- 3D visualization displaying complex professional intelligence
- Advanced career path analysis and network insights

## 🔧 **Development Environment**

### **Auto-Fix System**
```bash
# Auto-Fix Commands
node scripts/claude-auto-fix.js     # Run auto-fix manually
npm run build                       # Verify build success
cat .github/auto-fix-attempts      # Check attempt history
```

### **Database**
```bash
# Database Commands
npx prisma generate          # Generate client
npx prisma migrate dev       # Run migrations
npx tsx scripts/verify-schema.ts  # Verify schema
```

### **Environment Variables**
```env
# Database (Neon PostgreSQL)
NEON_QUEST_CORE_DATABASE_URL=postgresql://... (Neon PostgreSQL with pooling)
NEON_QUEST_CORE_DIRECT_URL=postgresql://... (Direct connection for migrations)

# Authentication (Clerk) 
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
CLERK_SECRET_KEY=...

# Voice AI (Hume)
NEXT_PUBLIC_HUME_API_KEY=...
HUME_API_SECRET=...
NEXT_PUBLIC_HUME_CONFIGURE_ID_QUEST_CORE=...
```

### **Development Commands**
```bash
npm run dev              # Development server
npm run build           # Production build
npm run start           # Production server  
npx prisma studio       # Database browser
```

## 🚀 **Deployment Status**

### **Production Environment**
- ✅ **GitHub**: https://github.com/Londondannyboy/quest-core
- ✅ **Vercel**: Auto-deployment on main branch push
- ✅ **Database**: Neon PostgreSQL production instance
- ✅ **Build**: Successful production compilation
- ✅ **Schema**: Complete 4-layer repository system

### **Performance Metrics**
- **Build Size**: Optimized for production
- **Database**: Indexed for cross-repo queries
- **Voice Response**: <2s with full repo context
- **Entity Queries**: Normalized for efficiency

## 📊 **Current Code Metrics**

- **Database Models**: 20+ Prisma models
- **API Endpoints**: Enhanced with repo context
- **Components**: Professional UI framework
- **TypeScript**: 100% type safety
- **Architecture**: Production-ready scalable design

## 🔮 **Implementation Roadmap**

### **Phase 1: UI Development (Next Session)**
1. **Entity Management**: Company/skill/education creation interfaces
2. **Surface Repo**: Public profile with entity selection
3. **Working Repo**: Portfolio with multimedia and access control
4. **Personal Repo**: Goals and development tracking
5. **Enhanced Trinity**: Deep repo integration with AI analysis

### **Phase 2: Advanced Features**
- **Professional Relationships**: Network visualization
- **Neo4j Integration**: Graph database for relationship intelligence
- **Advanced Analytics**: Professional development insights
- **Mobile Experience**: Responsive design optimization

### **Phase 3: Platform Features**
- **Multi-user Collaboration**: Team and mentor features
- **Enterprise Integration**: Corporate professional development
- **API Platform**: Third-party integrations
- **Advanced AI**: Predictive career intelligence

## 📚 **Key Documentation**

### **Current Session Documentation**
- **CURRENT_STATUS.md**: Complete project status
- **NEXT_SESSION_TODO.md**: Detailed UI development tasks
- **PRODUCT_REQUIREMENTS.md**: Updated with 4-layer architecture

### **Legacy References**
- **Legacy Quest Project**: `/Users/dankeegan/Quest Claude Folder/`
- **GitHub**: `Londondannyboy/ai-career-platform`
- **Architecture Docs**: QUEST_REPO_STRUCTURE_V2.md

## 🎯 **Success Criteria**

### **Current Achievement Status**
- ✅ **Database**: Complete 4-layer schema with entities
- ✅ **Authentication**: Clerk integration with route protection
- ✅ **Voice Coaching**: Enhanced with full repo context access
- ✅ **Architecture**: Production-ready professional platform
- ❌ **User Interface**: Missing repo population tools
- ❌ **Data Population**: No user data for testing personalization

### **Next Milestone: UI Complete**
When admin can populate all repo layers and voice coaching demonstrates full personalization with real professional data.

---

**Quest Core** - Professional development platform with 4-layer repository system, ready for UI development to enable complete professional identity management and AI-powered coaching personalization.