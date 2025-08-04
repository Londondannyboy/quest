# Quest Core - Product Requirements Document

> **Vision**: "LinkedIn shows who you were. Quest shows who you're becoming."

## 🎯 Product Vision

Quest Core is a revolutionary professional development platform built on a **3-layer repository system** that manages your complete professional identity journey - from public profile to private development to deep AI-generated insights.

### **Core Philosophy**
- **3-Layer Repo System**: Surface (Public), Personal (Private), Deep (System)
- **Trinity System**: Quest (purpose), Service (value), Pledge (commitment) - embedded in Deep Repo
- **Context Engineering**: Cole Medin's advanced AI methodology
- **Voice-First Coaching**: Empathic AI conversations with emotional intelligence
- **Progressive Identity**: Focus on becoming, not just being

## 🏗️ Quest Repo Architecture

### **4-Layer Repository System**
```
┌─────────────────────────────────────────────────────────────────┐
│                        SURFACE REPO (Public)                   │
│           LinkedIn-style • Basic Professional Profile          │
│                     URL: /profile/[username]                    │
├─────────────────────────────────────────────────────────────────┤
│                       WORKING REPO (Selective)                 │
│  Rich Portfolio • Detailed Achievements • Multimedia Content   │
│   Project Showcases • Selective Access • Recruiter-Friendly    │
│                     URL: /work/[username]                       │
├─────────────────────────────────────────────────────────────────┤
│                       PERSONAL REPO (Private)                  │
│   Career Planning • Goals • OKRs • Personal Notes • Development │
│                       URL: /repo/personal                       │
├─────────────────────────────────────────────────────────────────┤
│                        DEEP REPO (System)                      │
│    AI Insights • Trinity Core • Identity Analysis • Encrypted   │
│                    System-managed, Not User-Editable            │
└─────────────────────────────────────────────────────────────────┘
```

### **User Journey Flow**
```
Registration → Profile Setup → Trinity Discovery → Personal Repo → Voice Coaching → Continuous Development
     ↓              ↓              ↓               ↓               ↓                    ↓
Surface Repo → Initial Data → Deep Repo Gen → Personal Goals → AI Mentorship → Growth Tracking
```

## 🎯 Core Features

### **1. Surface Repo (Public Profile)**
**Status**: Not implemented ❌
**Priority**: High

**User Story**: As a professional, I want a LinkedIn-style public profile that provides basic professional information to anyone who finds me.

**Features**:
- **Basic Professional Info**: Name, headline, location, contact
- **Work History**: Job titles, companies, dates (basic level)
- **Education**: Degrees and institutions
- **Skills**: Core competencies (high-level)
- **Public URL**: Shareable profile at `/profile/[username]`
- **SEO Optimized**: Discoverable through search engines

**Philosophy**: Clean, professional, safe to share publicly - like a business card that's always available.

### **2. Working Repo (Selective Portfolio)**
**Status**: Not implemented ❌
**Priority**: High - **This is our unique value proposition**

**User Story**: As a professional, I want a rich portfolio space where I can share detailed achievements, project showcases, and multimedia content with selected people like recruiters, potential collaborators, or close professional connections.

**Key Innovation**: The missing layer between public LinkedIn profiles and private career planning. Solves the problem of LinkedIn being too basic while avoiding the arrogance of oversharing publicly.

**Features**:

**🎯 Selective Access Control**:
- **Granular Permissions**: Grant access to specific individuals or groups
- **Access Levels**: Recruiter view, collaborator view, mentor view
- **Time-Limited Access**: Temporary access for specific opportunities
- **Access Analytics**: Track who viewed what and when

**🎨 Rich Portfolio Content**:
- **Project Showcases**: Detailed project descriptions with context
- **Achievement Stories**: Narrative-driven accomplishments with impact
- **Multimedia Support**: Videos, graphics, presentations, documents
- **Work Samples**: Code repositories, design portfolios, writing samples
- **Company Projects**: Internal project names, program details, case studies

**📊 Professional Depth**:
- **Quantified Impact**: Detailed metrics and business outcomes
- **Challenge-Solution Stories**: Problem-solving narratives
- **Collaboration Examples**: Team leadership and partnership stories
- **Skills in Context**: How skills were applied in real situations
- **Growth Trajectory**: Professional evolution and learning journey

**🤖 AI-Enhanced Content**:
- **Story Crafting**: AI coaching to create compelling narratives
- **Impact Amplification**: Help articulate achievements without arrogance
- **Content Optimization**: Tailor content for different audiences
- **Suggestion Engine**: Recommend content based on goals and opportunities

**Technical Requirements**:
- **Media Storage**: Secure cloud storage for multimedia content
- **Access Management**: Role-based permissions system
- **Content Versioning**: Track changes and updates
- **Analytics Dashboard**: Usage and engagement metrics
- **Mobile-Responsive**: Full functionality on mobile devices
- **Export Options**: PDF/presentation generation for specific audiences

**Success Criteria**:
- **Adoption Rate**: >80% of users create Working Repo content
- **Access Grants**: Average 5+ people granted access per user
- **Engagement**: >60% of shared content is viewed/interacted with
- **Professional Outcomes**: >50% report improved professional opportunities

**URL Structure**: `/work/[username]` with access-controlled sections

### **3. Personal Repo (Private Development)**
**Status**: Not implemented ❌
**Priority**: High

**User Story**: As a professional, I want a private space to plan my career development and track my progress.

**Features**:
- **Career Planning**: Future goals and development paths
- **OKRs Management**: Personal objectives and key results
- **Private Notes**: Personal reflections and insights
- **Development Tracking**: Progress monitoring and analytics
- **Goal Setting**: SMART goals with AI assistance

**Technical Requirements**:
- Private dashboard interface
- Goal tracking system
- Progress analytics
- Data encryption

### **4. Deep Repo (AI-Generated Insights)**
**Status**: Partial (Trinity foundation) 🔄
**Priority**: High

**User Story**: As a user, I want AI-generated insights about my professional identity that I can't see directly but that powers my coaching.

**Features**:
- **Trinity Core**: AI-managed Quest, Service, Pledge
- **Identity Analysis**: Deep professional identity insights
- **Behavioral Patterns**: AI-detected career patterns
- **Predictive Modeling**: Future career trajectory insights
- **Encrypted Storage**: System-managed, secure data

**Technical Requirements**:
- AI insight generation
- Encrypted data storage
- System-only access controls
- Background processing

### **5. Voice Coaching (Cross-Repo Integration)**
**Status**: Interface ready, needs full repo integration 🔄
**Priority**: High

**User Story**: As a professional, I want voice coaching that understands my complete professional identity across all repo layers.

**Features**:
- **Repo-Aware Coaching**: Access to all four layers for context
- **Trinity Integration**: Deep repo Trinity data for personalization
- **Goal Alignment**: Personal repo goals inform coaching
- **Profile Enhancement**: Suggestions for Surface repo improvements
- **Session Continuity**: Memory across coaching sessions

**Technical Requirements**:
- Cross-repo data access
- Voice interface with Hume EVI
- Real-time coaching logic
- Session management

### **6. Professional Relationship Intelligence (Future)**
**Status**: Not implemented ❌
**Priority**: Medium (Future Phase)

**User Story**: As a professional, I want to understand and visualize my professional relationships and have conversational access to my network context.

**Key Innovation**: Transform static professional profiles into dynamic relationship maps that power both visualization and conversational intelligence.

**Features**:

**🕸️ Neo4j Graph Visualization**:
- **Interactive Network Maps**: Visual representation of professional connections
- **Relationship Strength Indicators**: Visual strength scoring (1-5 scale)
- **Career Path Analysis**: Track career progression through connections
- **Skill Flow Mapping**: How skills moved through professional relationships
- **Company Network Analysis**: Connections across different companies
- **Temporal Relationship View**: How relationships evolved over time

**🤖 Conversational Relationship Intelligence**:
- **Context-Aware Coaching**: "I saw you worked on X project at Sony, who did you report to?"
- **Relationship Queries**: "Who were your key collaborators on that project?"
- **Network Analysis**: "Who in your network could help with Y opportunity?"
- **Introduction Facilitation**: "Should I remind you to reconnect with [contact]?"
- **Professional Context**: "Tell me about your working relationship with [person]"

**📊 Professional Network Analytics**:
- **Relationship Strength Scoring**: Automatic scoring based on interaction frequency
- **Network Diversity Analysis**: Industry, role, and skill diversity in network
- **Influence Mapping**: Identify key connectors and influencers
- **Opportunity Identification**: Spot potential collaborations and referrals
- **Network Growth Tracking**: Monitor relationship building over time

**🎯 Privacy-First Approach**:
- **Consent-Based**: Only track relationships user explicitly adds
- **Selective Sharing**: Users control what relationship data is visible
- **No Automatic Scraping**: Manual entry ensures quality and consent
- **Relationship Permissions**: Different visibility levels for different contacts

**Technical Requirements**:
- Neo4j integration for graph storage and queries
- Relationship data normalization
- Graph visualization library (D3.js or similar)
- Real-time graph updates
- Privacy and consent management
- Conversational AI integration with graph context

## 🏗️ Data Architecture Strategy

### **Hybrid Architecture Decision (December 2024)**
**Single Source of Truth**: PostgreSQL (Neon) maintains all permanent user data
**Specialized Systems**: Zep for conversational memory, Neo4j for relationship graphs

```
┌─────────────────────────────────────────────────────────┐
│                    PostgreSQL (Neon)                     │
│                  SINGLE SOURCE OF TRUTH                  │
│  - Users (Clerk ID as master)                          │
│  - Professional profiles                                │
│  - 4-layer repository data                             │
│  - Key insights from Zep sessions                      │
└─────────────────┬───────────────────────┬──────────────┘
                  │                       │
        Sync Key Insights          Read for Context
                  │                       │
                  ↓                       ↓
         ┌────────────────┐      ┌────────────────┐
         │      Zep       │      │     Neo4j      │
         │ Conversations  │      │ Relationships  │
         │ Behavioral     │      │ Graph Queries  │
         │ Temporal KG    │      │ Professional   │
         └────────────────┘      └────────────────┘
```

### **AI Gateway Integration with OpenRouter**
- **Multi-Model Routing**: Access to 300+ AI models through unified API
- **Cost Optimization**: Automatic selection of most cost-effective model per use case
- **Coach Specialization**: Different models optimized for different coaching types
- **Reliability**: Automatic fallbacks when primary providers are unavailable
- **Performance**: OpenAI-compatible API with <25ms routing overhead

### **Zep Integration for Conversational Memory**
- **Temporal Knowledge Graphs**: Automatic extraction of entities and relationships from conversations
- **User Session Management**: Persistent memory across voice coaching sessions
- **Context Optimization**: Query only relevant facts (3-5 most relevant) instead of full history
- **Trinity Evolution Tracking**: How Quest, Service, Pledge evolve through conversations
- **Token Cost Optimization**: 60-70% reduction in LLM context tokens

### **Combined Benefits: OpenRouter + Zep**
- **Intelligent Coaching**: Right model + right context for each interaction
- **Cost Efficiency**: Model optimization + context optimization = 40-60% cost reduction
- **Enhanced Quality**: Specialized models with rich historical context
- **Scalability**: Handle increased load through intelligent routing and memory management

### **User ID Strategy**
**Master ID**: Clerk User ID used consistently across all systems
- PostgreSQL: Primary key = Clerk ID
- Zep: user_id = Clerk ID (no translation needed)
- Neo4j (future): User nodes use Clerk ID

### **Current State**
- Basic user, trinity, skills, conversations tables
- Authentication with Clerk
- Voice coaching infrastructure
- Ready for Zep integration

### **Required Schema Changes - Entity-Centric Design**

**Core Philosophy**: All professional entities (companies, skills, certificates, education) are normalized objects with unique identifiers, enabling rich relationship graphs and professional networking. The system captures **professional relationships** within each experience to power Neo4j graph visualization and conversational intelligence.

**Relationship Intelligence**: The system tracks "who worked with whom" on projects, "who reported to whom," "who taught whom," and "who delivered what for whom" - enabling powerful network analysis and conversational coaching insights.

```sql
-- Core Entity Tables
CREATE TABLE companies (
  id UUID PRIMARY KEY,
  name VARCHAR NOT NULL,
  website VARCHAR UNIQUE,
  domain VARCHAR, -- extracted from website
  industry VARCHAR,
  size_range VARCHAR,
  logo_url VARCHAR,
  description TEXT,
  verified BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE skills (
  id UUID PRIMARY KEY,
  name VARCHAR UNIQUE NOT NULL,
  category VARCHAR,
  subcategory VARCHAR,
  difficulty_level VARCHAR,
  market_demand_score INTEGER,
  description TEXT,
  verified BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE educational_institutions (
  id UUID PRIMARY KEY,
  name VARCHAR NOT NULL,
  website VARCHAR,
  type VARCHAR, -- university, college, bootcamp, online
  country VARCHAR,
  verified BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE certifications (
  id UUID PRIMARY KEY,
  name VARCHAR NOT NULL,
  issuing_organization VARCHAR,
  website VARCHAR,
  category VARCHAR,
  validity_period INTEGER, -- months
  description TEXT,
  verified BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Surface Repo Tables
CREATE TABLE surface_profiles (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  username VARCHAR UNIQUE,
  public_bio TEXT,
  headline VARCHAR,
  location VARCHAR,
  website VARCHAR,
  is_public BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE work_experiences (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  company_id UUID REFERENCES companies(id),
  title VARCHAR NOT NULL,
  employment_type VARCHAR, -- full-time, part-time, contract
  start_date DATE,
  end_date DATE,
  is_current BOOLEAN DEFAULT false,
  description TEXT,
  achievements TEXT[],
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_skills (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  skill_id UUID REFERENCES skills(id),
  proficiency_level VARCHAR, -- beginner, intermediate, advanced, expert
  years_of_experience INTEGER,
  is_showcase BOOLEAN DEFAULT false, -- show on public profile
  endorsements_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, skill_id)
);

CREATE TABLE user_education (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  institution_id UUID REFERENCES educational_institutions(id),
  degree VARCHAR,
  field_of_study VARCHAR,
  start_date DATE,
  end_date DATE,
  gpa VARCHAR,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_certifications (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  certification_id UUID REFERENCES certifications(id),
  issued_date DATE,
  expiry_date DATE,
  credential_id VARCHAR,
  credential_url VARCHAR,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Professional Relationship Tables (Neo4j Ready)
CREATE TABLE professional_contacts (
  id UUID PRIMARY KEY,
  name VARCHAR NOT NULL,
  email VARCHAR,
  linkedin_url VARCHAR,
  current_company_id UUID REFERENCES companies(id),
  current_title VARCHAR,
  phone VARCHAR,
  notes TEXT,
  relationship_strength INTEGER, -- 1-5 scale
  last_interaction_date DATE,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE work_relationships (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  work_experience_id UUID REFERENCES work_experiences(id),
  contact_id UUID REFERENCES professional_contacts(id),
  relationship_type VARCHAR, -- manager, direct_report, peer, client, vendor, mentor
  relationship_description TEXT,
  collaboration_context TEXT,
  start_date DATE,
  end_date DATE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE project_relationships (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  project_id UUID REFERENCES working_projects(id),
  contact_id UUID REFERENCES professional_contacts(id),
  relationship_type VARCHAR, -- project_manager, team_member, client, stakeholder, vendor
  role_description TEXT,
  collaboration_details TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE education_relationships (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  education_id UUID REFERENCES user_education(id),
  contact_id UUID REFERENCES professional_contacts(id),
  relationship_type VARCHAR, -- professor, mentor, classmate, advisor
  subject_area VARCHAR,
  interaction_context TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Working Repo Tables (Selective Portfolio)
CREATE TABLE working_profiles (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  title VARCHAR NOT NULL,
  description TEXT,
  banner_image VARCHAR,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE working_projects (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  working_profile_id UUID REFERENCES working_profiles(id),
  title VARCHAR NOT NULL,
  company_id UUID REFERENCES companies(id),
  description TEXT,
  challenge TEXT,
  solution TEXT,
  impact TEXT,
  technologies JSONB,
  start_date DATE,
  end_date DATE,
  project_type VARCHAR, -- internal, client, personal, open-source
  display_order INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE working_achievements (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  working_profile_id UUID REFERENCES working_profiles(id),
  title VARCHAR NOT NULL,
  description TEXT,
  context TEXT,
  quantified_impact JSONB, -- metrics, numbers, percentages
  skills_demonstrated JSONB, -- skill IDs and how they were used
  recognition TEXT,
  date_achieved DATE,
  display_order INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE working_media (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  working_profile_id UUID REFERENCES working_profiles(id),
  project_id UUID REFERENCES working_projects(id),
  achievement_id UUID REFERENCES working_achievements(id),
  media_type VARCHAR, -- video, image, document, presentation, code
  title VARCHAR,
  description TEXT,
  file_url VARCHAR,
  file_size INTEGER,
  mime_type VARCHAR,
  thumbnail_url VARCHAR,
  display_order INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE working_access_permissions (
  id UUID PRIMARY KEY,
  working_profile_id UUID REFERENCES working_profiles(id),
  granted_to_email VARCHAR,
  granted_to_name VARCHAR,
  access_level VARCHAR, -- recruiter, collaborator, mentor, full
  granted_by UUID REFERENCES users(id),
  granted_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  is_revoked BOOLEAN DEFAULT false,
  access_token VARCHAR UNIQUE -- for secure access without signup
);

CREATE TABLE working_access_logs (
  id UUID PRIMARY KEY,
  working_profile_id UUID REFERENCES working_profiles(id),
  accessed_by_email VARCHAR,
  accessed_by_name VARCHAR,
  access_token VARCHAR,
  accessed_at TIMESTAMP DEFAULT NOW(),
  ip_address VARCHAR,
  user_agent TEXT,
  pages_viewed JSONB -- track what sections were viewed
);

-- Personal Repo Tables  
CREATE TABLE personal_goals (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  goal_type VARCHAR, -- career, skill, personal
  title VARCHAR,
  description TEXT,
  target_date DATE,
  progress_percentage INTEGER,
  okrs JSONB
);

CREATE TABLE personal_notes (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  note_type VARCHAR,
  content TEXT,
  tags JSONB,
  created_at TIMESTAMP
);

-- Deep Repo Tables (System-managed)
CREATE TABLE deep_insights (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  insight_type VARCHAR,
  ai_analysis JSONB,
  confidence_score FLOAT,
  generated_at TIMESTAMP
);

CREATE TABLE trinity_core (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  quest_analysis JSONB,
  service_analysis JSONB,
  pledge_analysis JSONB,
  coherence_score FLOAT,
  last_updated TIMESTAMP
);
```

## 🎯 Implementation Roadmap

### **Phase 1: Core Repo Architecture** (Immediate Priority)
1. **Database Schema Migration**
   - Create all repo tables
   - Migrate existing Trinity data to Deep Repo
   - Set up proper access controls

2. **Surface Repo Implementation**
   - Public profile creation interface
   - Username system
   - Public profile display
   - Privacy controls

3. **Personal Repo Implementation**
   - Private dashboard
   - Goal setting interface
   - Note-taking system
   - Progress tracking

### **Phase 2: Deep Repo & AI Integration** (Next Priority)
1. **Trinity System Enhancement**
   - Move Trinity to Deep Repo
   - AI-powered Trinity analysis
   - Coherence scoring
   - Automated insights

2. **Voice Coaching Integration**
   - Repo-aware coaching system
   - Cross-layer data access
   - Personalized coaching prompts
   - Session continuity

### **Phase 3: Advanced Features** (Future)
1. **Neo4j Graph Visualization**
   - Interactive professional network maps
   - Relationship strength visualization
   - Career path analysis through connections
   - Skill flow through professional relationships

2. **Conversational Relationship Intelligence**
   - Voice coaching with relationship context
   - "Who did you work with on X project?" queries
   - "Who was your manager at Y company?" insights
   - Professional network analysis through conversation

3. **Skills Intelligence**
   - Market-aware skill recommendations
   - Learning path generation
   - Skill verification system

4. **Social Features**
   - Profile sharing
   - Professional networking
   - Mentorship connections

## 🔄 Migration Strategy

### **Existing Data Preservation**
- Current Trinity statements → Deep Repo trinity_core
- User profiles → Enhanced users table
- Conversations → Enhanced with repo context
- Skills → Integrated across Surface/Personal repos

### **New User Onboarding**
1. **Account Creation** (Clerk authentication)
2. **Surface Repo Setup** (Public profile creation)
3. **Trinity Discovery** (Deep Repo population)
4. **Personal Repo Initialization** (Goal setting)
5. **Voice Coaching Introduction** (Cross-repo integration)

## 📊 Success Metrics

### **Repo Engagement**
- **Surface Repo**: Public profile completion rate >80%
- **Personal Repo**: Active goal management >60%
- **Deep Repo**: Trinity coherence scores >85%
- **Cross-Repo**: Voice coaching utilization >70%

### **User Journey**
- **Onboarding Completion**: >90% complete all repo setup
- **Return Engagement**: >75% return within 7 days
- **Feature Adoption**: >60% use all three repo layers
- **Professional Growth**: >40% report career advancement

## 🎨 **Visual Design & User Experience**

### **Premium Design System**
Quest Core employs a sophisticated, premium visual language that positions the platform as an innovation leader in professional development.

#### **Visual Identity Standards**
- **Brand Philosophy**: Premium professionalism with cutting-edge innovation
- **Color Palette**: Aurora Fade (#00D4B8), Electric Violet (#4F46E5), Purple Accent (#8B5CF6)
- **Typography**: GT Walsheim for premium, professional typography hierarchy
- **Background System**: Deep charcoal (#0A0E1A) primary, elevated surfaces (#1A1D29)
- **Visual Language**: Sophisticated gradient treatments, clean modern design

#### **Quest-Specific UI Patterns**
- **Trinity Visualization**: Interconnected cards with gradient treatments representing Quest/Service/Pledge
- **Professional Network Graphs**: Profile photos with gradient borders, relationship strength indicators
- **AI Coaching Interface**: Specialist coach cards with premium visual hierarchy
- **3D Spherical Elements**: Distinctive gradient spheres reinforcing professional journey metaphor
- **Data Visualization**: Professional graph styling with brand colors for skills, progress, and analytics

#### **Component Design Standards**
- **Cards**: Dark backgrounds (#1A1D29) with subtle borders and sophisticated shadows
- **Buttons**: Primary actions use Quest gradient treatments (#00D4B8 to #4F46E5)
- **Forms**: Clean inputs with Quest color focus states and GT Walsheim typography
- **Navigation**: Premium dark interface with gradient accent elements
- **Data Displays**: Professional styling with Quest chart color palette

#### **Responsive Design Requirements**
- **Mobile-First**: 320px+ with touch-friendly 44px minimum targets
- **Tablet Optimization**: 768px+ with enhanced interaction patterns
- **Desktop Excellence**: 1024px+ with sophisticated data visualization
- **4K Ready**: 1440px+ container max-width with optimal content scaling

#### **Accessibility Standards**
- **WCAG AA Compliance**: 4.5:1 minimum color contrast ratios
- **Keyboard Navigation**: Complete keyboard accessibility with clear focus indicators
- **Screen Reader Support**: Semantic HTML with proper ARIA labels
- **High Contrast Mode**: Alternative theme for enhanced visibility

#### **Generative UI Integration**
When integrating with thesys.dev for adaptive interfaces:
- **Brand Compliance**: All generated components must use Quest color system
- **Typography Consistency**: GT Walsheim font family in all generated content
- **Component Pattern Matching**: Generated UI follows established Quest design patterns
- **Animation Standards**: Subtle, professional animations maintaining premium feel

### **User Experience Principles**
1. **Professional Trust**: Every interface element builds enterprise user confidence
2. **Innovation Leadership**: Cutting-edge design demonstrating platform sophistication
3. **Data Clarity**: Complex professional information presented elegantly
4. **Journey Progression**: Visual elements reinforce professional growth narrative
5. **Premium Feel**: High-quality interactions and attention to detail throughout

## 🚀 Technical Requirements

### **Performance**
- **Repo Access**: <500ms cross-repo queries
- **Voice Coaching**: <2s response with full repo context
- **Profile Loading**: <3s public profile display
- **Data Sync**: Real-time updates across repo layers

### **Security**
- **Layer Isolation**: Strict access controls between repos
- **Encryption**: All Personal and Deep repo data encrypted
- **Privacy**: Granular privacy controls for Surface repo
- **Audit Trail**: Complete access logging for Deep repo

### **Scalability**
- **Multi-tenant**: Support for enterprise repo systems
- **Data Partitioning**: Efficient cross-repo queries
- **Caching**: Intelligent caching for each repo layer
- **API Design**: RESTful APIs for each repo layer

---

**Quest Core Product Requirements** - Building the future of professional development through a comprehensive 3-layer repository system that manages your complete professional identity journey.