# Quest Core - Data Architecture Strategy

> **Single Source of Truth with Specialized Memory Systems**

## 🎯 **Architecture Overview**

Quest Core implements a hybrid data architecture that combines the reliability of traditional databases with the intelligence of modern AI memory systems.

### **Core Principle**
**PostgreSQL as Single Source of Truth** + **Specialized Systems for Enhanced Capabilities**

```
┌─────────────────────────────────────────────────────────┐
│                    PostgreSQL (Neon)                     │
│                  SINGLE SOURCE OF TRUTH                  │
│                                                           │
│  ✅ User Accounts (Clerk ID as master)                  │
│  ✅ Professional Profiles                               │
│  ✅ Work History & Skills                               │
│  ✅ Trinity Data                                        │
│  ✅ Key Insights from AI Sessions                       │
│  ✅ Audit Trail & Compliance Data                       │
└─────────────────┬───────────────────────┬──────────────┘
                  │                       │
        Sync Key Insights          Read for Context
                  │                       │
                  ↓                       ↓
         ┌────────────────┐      ┌────────────────┐
         │      Zep       │      │     Neo4j      │
         │ Conversations  │      │ Professional   │
         │ Memory & Goals │      │ Relationships  │
         │ Trinity Evol.  │      │ Network Intel  │
         │ Temporal KG    │      │ Graph Analysis │
         └────────────────┘      └────────────────┘
                  │                       │
                  └──── Context & Memory ──┘
                            ↓
                   ┌─────────────────┐
                   │ OpenRouter.AI   │
                   │   AI Gateway    │
                   │ Model Routing   │
                   └─────────┬───────┘
                            ↓
          ┌──────────────────┼──────────────────┐
          │                  │                  │
      ┌───▼───┐      ┌──────▼─────┐      ┌────▼─────┐
      │ GPT-4 │      │ Claude-3   │      │ Gemini   │
      │Turbo  │      │ Sonnet     │      │ Pro      │
      └───────┘      └────────────┘      └──────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                            ↓
                   ┌─────────────────┐
                   │   Multi-Coach   │
                   │   AI System     │
                   └─────────┬───────┘
                            │
                    AI Coaching Response
                            │
                            ↓
                   ┌─────────────────┐
                   │   thesys.dev    │
                   │  Generative UI  │
                   │ Adaptive Layer  │
                   └─────────┬───────┘
                            │
                    Dynamic Interface
                            │
                            ↓
                   ┌─────────────────┐
                   │   User Interface │
                   │ Adaptive • Real-time │
                   │ Context-Aware   │
                   └─────────────────┘
```

## 🔑 **User Identity Strategy**

### **Master User ID: Clerk User ID**
All systems use the same identifier for perfect data correlation:

```typescript
// Example Clerk ID
const MASTER_USER_ID = "user_2NNEqL2nrIRdJ194ndJqAHwEfxC"

// PostgreSQL
user.id = MASTER_USER_ID  // Primary key

// Zep
zep.user.add({ user_id: MASTER_USER_ID })

// Neo4j (future)
CREATE (u:User {id: MASTER_USER_ID})

// No ID translation needed anywhere
```

### **Benefits of Consistent ID Strategy**
- **Simplified Debugging**: Same ID across all logs and systems
- **Easy Data Correlation**: Join data across systems without mapping
- **Reduced Complexity**: No ID translation or mapping tables
- **Clear Audit Trail**: Track user actions across entire architecture

## 🗂️ **Data Distribution Strategy**

### **PostgreSQL: Master Repository**
**Stores**: Permanent, authoritative data that requires ACID compliance

```sql
-- Core user data
users (id, email, firstName, lastName, createdAt)
trinity_core (userId, quest, service, pledge, lastUpdated)
work_experiences (userId, companyId, title, achievements)
user_skills (userId, skillId, proficiencyLevel)

-- AI session insights (synced from Zep)
coaching_sessions (userId, sessionId, insights, trinityUpdates)
user_insights (userId, type, content, sourceSystem, createdAt)

-- Entity data
companies (id, name, industry, verified)
skills (id, name, category, marketDemand)
```

**Why PostgreSQL for this data**:
- **Compliance**: GDPR, data retention, legal requirements
- **Backup/Recovery**: Single point for complete data backup
- **Relational Integrity**: Foreign keys and constraints
- **Reporting**: SQL queries for analytics and insights

### **Zep: Conversational Memory**
**Stores**: Conversations, behavioral patterns, goal evolution

```typescript
// Zep data examples
{
  user_id: "user_2NNEqL2nrIRdJ194ndJqAHwEfxC",
  sessions: [
    {
      session_id: "voice_session_123",
      messages: [...],
      metadata: { sessionType: "trinity", platform: "hume" }
    }
  ],
  knowledge_graph: {
    entities: ["Software Engineering", "Management Goals", "Team Leadership"],
    relationships: [
      { from: "User", to: "Management Goals", type: "ASPIRES_TO" },
      { from: "User", to: "Software Engineering", type: "SKILLED_IN" }
    ]
  }
}
```

**Why Zep for this data**:
- **Temporal Intelligence**: Tracks how facts change over time
- **Context Optimization**: Retrieves only relevant facts for AI
- **Conversation Memory**: Maintains session continuity
- **Token Efficiency**: 60-70% reduction in LLM context costs

### **Neo4j: Professional Relationships** (Future)
**Stores**: Complex relationship graphs and network analytics

```cypher
// Neo4j data examples
(u:User {id: "user_2NNEqL2nrIRdJ194ndJqAHwEfxC"})
-[:WORKED_AT]->(c:Company {name: "Sony"})
-[:EMPLOYS]->(p:Person {name: "Manager Name"})
-[:KNOWS]->(u)

(u)-[:HAS_SKILL]->(s:Skill {name: "Python"})
(s)-[:REQUIRED_BY]->(j:JobPosting {title: "Senior Developer"})
```

**Why Neo4j for this data**:
- **Graph Algorithms**: Shortest path, centrality, community detection
- **Complex Queries**: Multi-hop relationship analysis
- **Network Intelligence**: Professional network insights
- **Performance**: Optimized for relationship traversal

### **thesys.dev: Adaptive UI Generation**
**Stores**: Interface specifications, user interaction patterns, UI adaptation rules

```typescript
// thesys.dev integration data
{
  user_id: "user_2NNEqL2nrIRdJ194ndJqAHwEfxC",
  interface_contexts: [
    {
      interface_type: "trinity-discovery",
      user_state: {
        trinityCompletion: 0.4,
        currentFocus: "quest-exploration",
        adaptationLevel: "moderate"
      },
      generated_ui: {
        componentTree: [...],
        styling: { adaptiveTheme: "encouraging", complexity: "simplified" },
        interactions: { voiceIntegration: true, realTimeUpdates: true }
      }
    }
  ],
  adaptation_patterns: {
    triggers: ["trinity-progress", "voice-session-start", "coaching-insight"],
    preferences: { visualStyle: "metaphorical", pace: "gradual", depth: "progressive" }
  }
}
```

**Why thesys.dev for this data**:
- **Dynamic Interface Generation**: Real-time UI creation based on user context
- **Adaptive Experiences**: Interfaces that evolve with user progress
- **Context Integration**: Seamlessly incorporates Zep memory and AI coaching
- **Cutting-Edge UX**: "Shock and awe" experience differentiation

## 🔄 **Data Flow Patterns**

### **1. User Onboarding Flow**
```
1. Clerk Authentication → PostgreSQL User Creation
                       ↓
2. Profile Setup → PostgreSQL (companies, skills, education)
                ↓
3. Zep User Creation → Initialize user graph with profile data
                    ↓
4. First Voice Session → Zep session + PostgreSQL session record
```

### **2. Enhanced Voice Coaching Flow with AI Gateway**
```
1. User Message → Zep context retrieval (relevant facts)
              ↓
2. Coach Selection → Determine optimal AI model via OpenRouter
                  ↓
3. AI Response Generation → Route to GPT-4/Claude-3/Gemini based on use case
                         ↓
4. Store Interaction → Zep (conversation) + PostgreSQL (insights + model used)
                    ↓
5. Trinity Evolution → Update both Zep graph + PostgreSQL trinity table
                    ↓
6. Cost Tracking → Monitor model usage and costs per coaching session
```

### **3. Multi-Coach AI Routing**
```
Master Coach Request → OpenRouter selects GPT-4 Turbo (complex orchestration)
                    ↓
Specialist Consultation → Route to optimal models:
- Career Coach → Claude-3 Sonnet (strategic analysis)
- Skills Coach → GPT-4 (technical assessment)  
- Leadership Coach → Gemini Pro (interpersonal growth)
- Network Coach → Claude-3 Sonnet (relationship strategy)
                    ↓
Response Synthesis → Master Coach (GPT-4) synthesizes final guidance
                  ↓
Cost Optimization → Automatic fallback to cheaper models when appropriate
```

### **3. Generative UI Adaptive Flow**
```
1. User Interaction → Gather context from PostgreSQL + Zep
                   ↓
2. AI Coaching → OpenRouter routes to optimal model for response
              ↓
3. Interface Generation → thesys.dev generates adaptive UI based on:
                       - User context (Trinity state, progress)
                       - AI coaching response
                       - Session emotional context
                       - Adaptation rules
                       ↓
4. Real-time Updates → Stream UI updates as conversation evolves
                    ↓
5. User Engagement → Track interaction patterns for future adaptations
                  ↓
6. Adaptation Learning → Store successful UI patterns for similar contexts
```

### **4. Data Sync Patterns**

#### **Zep → PostgreSQL (Insights Sync)**
```typescript
// After each coaching session
const insights = await zep.memory.get_session_summary(sessionId)

await prisma.coachingSession.create({
  data: {
    userId,
    sessionId,
    insights: insights.key_points,
    trinityUpdates: insights.trinity_changes,
    sourceSystem: 'zep',
    createdAt: new Date()
  }
})

// Update Trinity if evolved
if (insights.trinity_changes) {
  await prisma.trinity.update({
    where: { userId },
    data: { 
      ...insights.trinity_changes,
      lastUpdated: new Date(),
      updatedVia: 'zep_conversation'
    }
  })
}
```

#### **PostgreSQL → Zep (Profile Sync)**
```typescript
// When user updates profile
const userData = await prisma.user.findUnique({
  where: { id: userId },
  include: { workExperience: true, skills: true }
})

await zep.graph.add({
  user_id: userId,
  type: 'json',
  data: JSON.stringify({
    profile_update: {
      work_history: userData.workExperience,
      skills: userData.skills,
      updated_at: new Date()
    }
  })
})
```

## 🔐 **Data Security & Privacy**

### **Privacy by Design**
Each system handles appropriate data sensitivity:

```typescript
// Data Classification
const dataClassification = {
  postgresql: {
    public: ['basic_profile', 'work_history', 'skills'],
    private: ['personal_goals', 'notes'],
    encrypted: ['deep_insights', 'trinity_analysis']
  },
  zep: {
    conversational: ['coaching_sessions', 'goal_evolution'],
    behavioral: ['interaction_patterns', 'engagement_metrics'],
    temporal: ['fact_changes', 'relationship_evolution']
  },
  thesys: {
    interface_specs: ['generated_ui_components', 'styling_preferences'],
    adaptation_data: ['user_interaction_patterns', 'ui_effectiveness_metrics'],
    personalization: ['visual_preferences', 'complexity_preferences']
  },
  neo4j: {
    professional: ['work_connections', 'company_networks'],
    public: ['skill_relationships', 'industry_connections']
  }
}
```

### **GDPR Compliance Strategy**
```typescript
// Complete user data removal
async function deleteUserCompletely(userId: string) {
  // 1. PostgreSQL - master deletion
  await prisma.user.delete({ where: { id: userId }})
  
  // 2. Zep - conversation and graph data
  await zep.user.delete(userId)
  
  // 3. thesys.dev - UI generation data and preferences
  await thesysClient.deleteUserData(userId)
  
  // 4. Neo4j - relationship cleanup (future)
  // await neo4j.run(`MATCH (u:User {id: $userId}) DETACH DELETE u`, { userId })
  
  return { deleted: true, systems: ['postgresql', 'zep', 'thesys'] }
}

// Data export for portability
async function exportUserData(userId: string) {
  const [postgresData, zepData, thesysData] = await Promise.all([
    exportPostgreSQLUser(userId),
    zep.user.export(userId),
    thesysClient.exportUserData(userId)
  ])
  
  return {
    master_data: postgresData,
    conversational_data: zepData,
    interface_data: thesysData,
    exported_at: new Date(),
    format: 'json'
  }
}
```

## 📊 **Consistency & Validation**

### **Data Consistency Checks**
```typescript
// Validate sync between systems
async function validateDataConsistency(userId: string) {
  const checks = []
  
  // Trinity consistency between PostgreSQL and Zep
  const [pgTrinity, zepTrinity] = await Promise.all([
    prisma.trinity.findUnique({ where: { userId }}),
    getZepTrinityData(userId)
  ])
  
  if (pgTrinity && zepTrinity) {
    checks.push({
      system: 'trinity_sync',
      consistent: compareTrinityData(pgTrinity, zepTrinity),
      last_pg_update: pgTrinity.lastUpdated,
      last_zep_update: zepTrinity.timestamp
    })
  }
  
  // User profile consistency
  const [pgProfile, zepProfile] = await Promise.all([
    getUserProfile(userId),
    getZepUserProfile(userId)
  ])
  
  checks.push({
    system: 'profile_sync',
    consistent: compareProfiles(pgProfile, zepProfile),
    discrepancies: findProfileDiscrepancies(pgProfile, zepProfile)
  })
  
  return {
    overall_consistent: checks.every(c => c.consistent),
    individual_checks: checks,
    checked_at: new Date()
  }
}
```

### **Automated Sync Healing**
```typescript
// Resolve inconsistencies automatically
async function healDataInconsistencies(userId: string) {
  const validation = await validateDataConsistency(userId)
  
  if (!validation.overall_consistent) {
    for (const check of validation.individual_checks) {
      if (!check.consistent) {
        switch (check.system) {
          case 'trinity_sync':
            await healTrinityInconsistency(userId, check)
            break
          case 'profile_sync':
            await healProfileInconsistency(userId, check)
            break
        }
      }
    }
  }
  
  return { healed: true, actions_taken: validation.individual_checks }
}
```

## 🚀 **Performance Optimization**

### **AI Gateway Optimization**

#### **Model Selection Performance**
```typescript
// Cached model selection for performance
const modelCache = new Map<CoachType, string>();

const getOptimalModel = (coach: CoachType, complexity: number) => {
  const cacheKey = `${coach}_${complexity}`;
  
  if (modelCache.has(cacheKey)) {
    return modelCache.get(cacheKey);
  }
  
  const model = complexity > 0.8 
    ? getHighPerformanceModel(coach)  // GPT-4, Claude-3 Opus
    : getCostOptimizedModel(coach);   // GPT-3.5, Claude-3 Haiku
    
  modelCache.set(cacheKey, model);
  return model;
};
```

#### **Cost Optimization Strategy**
```typescript
const costOptimization = {
  simpleQuestions: 'openai/gpt-3.5-turbo',      // $0.50/1M tokens
  complexReasoning: 'openai/gpt-4-turbo',       // $10/1M tokens
  strategicAnalysis: 'anthropic/claude-3-sonnet', // $3/1M tokens
  creativeWork: 'anthropic/claude-3-opus',      // $15/1M tokens
  
  // Automatic fallback rules
  fallbackRules: {
    'openai/gpt-4-turbo': 'openai/gpt-4',
    'anthropic/claude-3-opus': 'anthropic/claude-3-sonnet',
    'google/gemini-pro': 'openai/gpt-3.5-turbo'
  }
};
```

### **Query Optimization Patterns**

#### **Zep Context Retrieval**
```typescript
// Optimized for coaching performance
const getOptimizedContext = async (userId: string, query: string) => {
  // Start both queries in parallel
  const [relevantFacts, recentHistory] = await Promise.all([
    zep.graph.search({
      user_id: userId,
      query: query,
      limit: 3,        // Optimized for token efficiency
      min_score: 0.7   // Only high-relevance facts
    }),
    zep.memory.get_recent_sessions({
      user_id: userId,
      limit: 2         // Just recent context
    })
  ])
  
  return {
    facts: relevantFacts.facts,
    history: recentHistory.messages.slice(-10),
    response_time: Date.now() - start
  }
}
```

#### **PostgreSQL Efficient Queries**
```sql
-- Optimized user context query
SELECT 
  u.id, u.firstName, u.lastName,
  t.quest, t.service, t.pledge,
  array_agg(DISTINCT s.name) as skills,
  array_agg(DISTINCT c.name) as companies
FROM users u
LEFT JOIN trinity_core t ON u.id = t.userId
LEFT JOIN user_skills us ON u.id = us.userId
LEFT JOIN skills s ON us.skillId = s.id
LEFT JOIN work_experiences we ON u.id = we.userId
LEFT JOIN companies c ON we.companyId = c.id
WHERE u.id = $1
GROUP BY u.id, t.quest, t.service, t.pledge;

-- Single query for complete user context
-- Optimized with proper indexes on userId foreign keys
```

### **Caching Strategy**
```typescript
// Redis cache for expensive operations
const cacheManager = {
  userContext: {
    ttl: 300,  // 5 minutes
    key: (userId) => `user_context:${userId}`
  },
  zepFacts: {
    ttl: 600,  // 10 minutes for stable facts
    key: (userId, query) => `zep_facts:${userId}:${hashQuery(query)}`
  },
  trinityData: {
    ttl: 1800, // 30 minutes for Trinity (changes slowly)
    key: (userId) => `trinity:${userId}`
  }
}
```

## 📈 **Scalability Considerations**

### **Multi-Tenant Architecture**
```typescript
// All systems designed for multi-tenancy
const tenantIsolation = {
  postgresql: {
    strategy: 'shared_database_separate_schemas',
    user_isolation: 'row_level_security_by_userId'
  },
  zep: {
    strategy: 'user_id_isolation',
    data_separation: 'automatic_by_user_graph'
  },
  neo4j: {
    strategy: 'user_subgraphs',
    isolation: 'node_properties_and_relationships'
  }
}
```

### **Data Growth Management**
```typescript
// Automated cleanup strategies
const dataRetention = {
  zep_sessions: {
    active_retention: '90_days',
    archived_retention: '2_years',
    cleanup_strategy: 'summarize_then_archive'
  },
  postgresql_insights: {
    detailed_retention: '1_year',
    summary_retention: '5_years',
    compression: 'json_aggregation'
  }
}
```

## 🎯 **Implementation Roadmap**

### **Phase 1: Foundation (Current)**
- ✅ PostgreSQL schema with Clerk authentication
- ✅ Basic user profiles and Trinity data
- ✅ Voice coaching infrastructure

### **Phase 2: Zep + thesys.dev Integration (Next)**
- [ ] Zep user management with Clerk ID consistency
- [ ] Voice coaching memory persistence
- [ ] Multi-coach context sharing
- [ ] PostgreSQL ↔ Zep sync implementation
- [ ] thesys.dev generative UI integration
- [ ] Adaptive interface generation based on user context
- [ ] Real-time UI updates during coaching sessions

### **Phase 3: Neo4j Enhancement (Future)**
- [ ] Professional relationship modeling
- [ ] Complex graph queries for network intelligence
- [ ] Integration with Zep context for coaching

### **Phase 4: Advanced Intelligence (Future)**
- [ ] Cross-system analytics and insights
- [ ] Predictive modeling using combined data
- [ ] Advanced personalization algorithms

---

**Quest Core Data Architecture** - A hybrid approach that maximizes the strengths of each system while maintaining data integrity, user privacy, and system performance.

**Key Innovation**: Single source of truth for compliance and reliability, combined with specialized AI memory systems for enhanced user experience and intelligence.