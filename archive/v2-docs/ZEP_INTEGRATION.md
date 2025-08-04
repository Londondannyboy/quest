# Zep Integration - Technical Implementation Guide

> **Architecture Decision**: Hybrid approach with PostgreSQL as single source of truth and Zep for conversational memory management

## 🎯 **Current Status: 70% Complete**

### ✅ **What's Working**
- **API Connection**: Zep client successfully connects with both ZEP_API_KEY and zeb_api_key
- **Message Storage**: Voice conversations stored in Zep memory via `/api/zep-message`
- **Fact Extraction**: Zep extracts 13+ detailed entities from conversations
- **Contextual Visualization**: Bottom panel graph (800x400px) shows relationships
- **Test Endpoint**: `/api/zep-test` confirms integration working
- **Entity Recognition**: football, Spain, tapas, beaches, Valencia, baseball

### ❌ **What's Not Working**
- **Real-time Updates**: Graph doesn't update when new topics mentioned (France, French food)
- **Cross-session Memory**: Previous conversations not persisting, graph starts empty
- **Dynamic Topics**: Entity recognition limited to hardcoded patterns
- **Update Frequency**: 10-second refresh not reflecting changes

### 🔄 **Current Architecture (Implemented)**
```
Voice Input → Zep Memory → Fact Extraction → Contextual Relationships → Graph
                    ↓
            Periodic Insights → PostgreSQL DeepInsights
```

## 🎯 **Integration Overview**

### **Why Zep for Quest Core**
- **Temporal Knowledge Graphs**: Automatic extraction of relationships from conversations
- **Token Optimization**: 60-70% reduction in LLM context costs
- **Persistent Memory**: Cross-session continuity for voice coaching
- **Trinity Evolution**: Track how user's Quest, Service, Pledge evolve over time
- **Multi-Coach Context**: Shared memory across specialized AI coaches

### **Zep vs Neo4j Distinction**
- **Zep**: Conversational memory, behavioral insights, Trinity evolution
- **Neo4j**: Professional relationships, skill dependencies, company networks
- **PostgreSQL**: Single source of truth for all permanent data

## 🏗️ **Architecture Pattern**

### **Data Flow**
```
Voice Session → Zep → Extract Insights → Sync to PostgreSQL
     ↓                                          ↑
Conversational Memory                    Master Repository
     ↓                                          ↑
Multi-Coach Context ←--------------→ Professional Data
```

### **User ID Strategy**
```typescript
// Master ID: Clerk User ID everywhere
const MASTER_USER_ID = clerkUser.id; // e.g. "user_2NNEqL2nrIRdJ194ndJqAHwEfxC"

// PostgreSQL
user.id = clerkUser.id

// Zep
zep.user.add({ user_id: clerkUser.id })

// No ID translation needed
```

## 🚀 **Implementation Phases**

### **Phase 1: Core Integration (Week 1-2)**

#### **1.1 Environment Setup**
```bash
npm install zep-cloud
```

```env
# Add to .env.local
ZEP_API_KEY=your_zep_api_key_here
ZEP_PROJECT_ID=your_project_id_here
```

#### **1.2 User Management Integration**
```typescript
// lib/zep-client.ts
import { Zep } from 'zep-cloud'

const zep = new Zep({
  apiKey: process.env.ZEP_API_KEY!
})

export async function createZepUser(clerkUser: any) {
  try {
    const zepUser = await zep.user.add({
      user_id: clerkUser.id,  // Use Clerk ID directly
      email: clerkUser.emailAddresses[0].emailAddress,
      first_name: clerkUser.firstName,
      last_name: clerkUser.lastName,
      metadata: {
        created_at: new Date().toISOString(),
        source: 'quest_core',
        trinity_initialized: false
      }
    })
    
    return zepUser
  } catch (error) {
    console.error('Error creating Zep user:', error)
    throw error
  }
}

export async function initializeUserGraph(userId: string, profileData: any) {
  // Add initial professional data to user's graph
  await zep.graph.add({
    user_id: userId,
    type: 'json',
    data: JSON.stringify({
      profile: {
        name: `${profileData.firstName} ${profileData.lastName}`,
        email: profileData.email,
        quest_core_joined: new Date().toISOString()
      }
    })
  })
}
```

#### **1.3 Modify User Creation Flow**
```typescript
// Update existing user creation in middleware or auth callbacks
import { createZepUser, initializeUserGraph } from '@/lib/zep-client'

export async function createUser(clerkUser: ClerkUser) {
  // 1. Create in PostgreSQL (existing code)
  const dbUser = await prisma.user.create({
    data: {
      id: clerkUser.id,  // Clerk ID as primary key
      email: clerkUser.emailAddresses[0].emailAddress,
      firstName: clerkUser.firstName,
      lastName: clerkUser.lastName
    }
  })
  
  // 2. Create in Zep with same ID
  try {
    await createZepUser(clerkUser)
    await initializeUserGraph(clerkUser.id, dbUser)
  } catch (error) {
    console.error('Zep user creation failed:', error)
    // Continue - Zep is enhancement, not critical path
  }
  
  return dbUser
}
```

### **Phase 2: Voice Coaching Integration (Week 2-3)**

#### **2.1 Enhanced Voice Session Management**
```typescript
// lib/voice-session.ts
import { zep } from '@/lib/zep-client'
import { Message } from 'zep-cloud/types'

export async function startVoiceSession(
  userId: string, 
  sessionType: 'trinity' | 'skills' | 'career' | 'wellness'
) {
  // Create Zep session
  const sessionId = `voice_${userId}_${Date.now()}`
  
  await zep.memory.add_session({
    session_id: sessionId,
    user_id: userId,
    metadata: {
      session_type: sessionType,
      started_at: new Date().toISOString(),
      platform: 'hume_voice'
    }
  })
  
  return sessionId
}

export async function addVoiceInteraction(
  sessionId: string,
  userMessage: string,
  aiResponse: string,
  emotionalContext?: any
) {
  const messages: Message[] = [
    {
      role: "Human",
      content: userMessage,
      role_type: "user",
      metadata: {
        emotional_context: emotionalContext,
        timestamp: new Date().toISOString()
      }
    },
    {
      role: "AI Coach",
      content: aiResponse,
      role_type: "assistant",
      metadata: {
        timestamp: new Date().toISOString()
      }
    }
  ]
  
  await zep.memory.add(sessionId, { messages })
}
```

#### **2.2 Context-Aware Coaching**
```typescript
// lib/coaching-context.ts
export async function getCoachingContext(
  userId: string, 
  currentMessage: string,
  sessionId?: string
) {
  // Get relevant long-term facts from user's graph
  const relevantFacts = await zep.graph.search({
    user_id: userId,
    query: currentMessage,
    limit: 5,
    min_score: 0.7
  })
  
  // Get recent conversation history
  const recentHistory = sessionId 
    ? await zep.memory.get(sessionId, { limit: 10 })
    : null
  
  // Get Trinity context from PostgreSQL
  const trinityData = await prisma.trinity.findUnique({
    where: { userId }
  })
  
  return {
    relevantFacts: relevantFacts.facts || [],
    recentMessages: recentHistory?.messages || [],
    trinity: trinityData,
    contextSummary: relevantFacts.summary
  }
}
```

#### **2.3 Update HumeVoiceInterface.tsx**
```typescript
// Enhance existing voice interface
import { addVoiceInteraction, getCoachingContext } from '@/lib/voice-session'

export function HumeVoiceInterface({ sessionType, onEndSession }: Props) {
  const [zepSessionId, setZepSessionId] = useState<string>()
  
  // Start Zep session when voice session begins
  useEffect(() => {
    if (status.value === 'connected' && userId) {
      startVoiceSession(userId, sessionType).then(setZepSessionId)
    }
  }, [status.value, userId, sessionType])
  
  // Enhanced message processing with Zep integration
  const processVoiceMessage = async (userMessage: string) => {
    if (!zepSessionId || !userId) return
    
    // Get context before AI response
    const context = await getCoachingContext(userId, userMessage, zepSessionId)
    
    // Send to AI with enhanced context
    const aiResponse = await generateCoachingResponse(userMessage, context)
    
    // Store interaction in Zep
    await addVoiceInteraction(zepSessionId, userMessage, aiResponse)
    
    return aiResponse
  }
}
```

### **Phase 3: Multi-Coach Implementation with OpenRouter (Week 3-4)**

#### **3.1 AI Gateway Integration for Coach Routing**
```typescript
// lib/ai-client.ts - OpenRouter integration
import OpenAI from 'openai';

export class AIClient {
  private openrouter: OpenAI;
  
  constructor() {
    this.openrouter = new OpenAI({
      baseURL: process.env.OPENROUTER_BASE_URL,
      apiKey: process.env.OPENROUTER_API_KEY,
    });
  }
  
  async generateCoachResponse(
    coachType: CoachType, 
    context: ZepContext, 
    userQuery: string
  ) {
    const model = this.selectModelForCoach(coachType);
    const prompt = this.buildCoachPrompt(coachType, context, userQuery);
    
    return await this.openrouter.chat.completions.create({
      model,
      messages: prompt,
      temperature: this.getTemperatureForCoach(coachType),
      max_tokens: this.getMaxTokensForCoach(coachType)
    });
  }
  
  private selectModelForCoach(coachType: CoachType): string {
    const modelMap = {
      master: process.env.COACH_MODEL_MASTER || 'openai/gpt-4-turbo',
      career: process.env.COACH_MODEL_CAREER || 'anthropic/claude-3-sonnet',
      skills: process.env.COACH_MODEL_SKILLS || 'openai/gpt-4',
      leadership: process.env.COACH_MODEL_LEADERSHIP || 'google/gemini-pro',
      network: process.env.COACH_MODEL_NETWORK || 'anthropic/claude-3-sonnet'
    };
    
    return modelMap[coachType] || 'openai/gpt-3.5-turbo';
  }
}
```

#### **3.2 Enhanced Multi-Coach Context with Model Awareness**
```typescript
// lib/multi-coach.ts
interface CoachContext {
  role: 'master' | 'career' | 'skills' | 'leadership' | 'network'
  model: string  // Track which AI model is being used
  userContext: ZepContext
  conversationHistory: Message[]
  specialistFocus: string[]
  costTracking: {
    tokensUsed: number
    modelCost: number
    responseTime: number
  }
}

export async function getSpecialistCoachContext(
  userId: string,
  coachRole: string,
  currentQuery: string
) {
  // Query Zep for coach-specific context
  const coachSpecificQuery = `${currentQuery} ${coachRole} expertise`
  
  const context = await zep.graph.search({
    user_id: userId,
    query: coachSpecificQuery,
    limit: 3,
    min_score: 0.7
  })
  
  const aiClient = new AIClient();
  const selectedModel = aiClient.selectModelForCoach(coachRole);
  
  return {
    role: coachRole,
    model: selectedModel,
    relevantFacts: context.facts,
    userHistory: context.summary,
    specialization: getCoachSpecialization(coachRole),
    costTracking: {
      tokensUsed: 0,
      modelCost: 0,
      responseTime: 0
    }
  }
}

function getCoachSpecialization(role: string): string[] {
  const specializations = {
    career: ['strategy', 'market_trends', 'positioning', 'transitions'],
    skills: ['technical_development', 'learning_paths', 'competency_gaps'],
    leadership: ['management', 'communication', 'team_building'],
    network: ['relationships', 'networking', 'professional_connections']
  }
  
  return specializations[role] || []
}
```

#### **3.3 Master Coach Orchestration with Cost Optimization**
```typescript
// lib/master-coach.ts
export async function orchestrateCoachingSession(
  userId: string,
  userQuery: string,
  sessionId: string
) {
  const aiClient = new AIClient();
  const startTime = Date.now();
  
  // 1. Master coach analyzes query and determines needed specialists
  const masterAnalysis = await aiClient.generateCoachResponse(
    'master',
    await getCoachingContext(userId, userQuery, sessionId),
    `Analyze this query and determine which specialist coaches to consult: ${userQuery}`
  );
  
  // 2. Get context from Zep for each needed specialist
  const neededCoaches = extractNeededCoaches(masterAnalysis);
  const specialistContexts = await Promise.all(
    neededCoaches.map(async coach => ({
      ...await getSpecialistCoachContext(userId, coach, userQuery),
      startTime: Date.now()
    }))
  );
  
  // 3. Generate specialist responses with model routing
  const specialistResponses = await Promise.all(
    specialistContexts.map(async context => {
      const response = await aiClient.generateCoachResponse(
        context.role,
        context.userContext,
        userQuery
      );
      
      // Track cost and performance
      context.costTracking = {
        tokensUsed: response.usage?.total_tokens || 0,
        modelCost: calculateModelCost(context.model, response.usage?.total_tokens || 0),
        responseTime: Date.now() - context.startTime
      };
      
      return { ...context, response };
    })
  );
  
  // 4. Master coach synthesizes final response
  const masterResponse = await aiClient.generateCoachResponse(
    'master',
    await getCoachingContext(userId, userQuery, sessionId),
    `Synthesize these specialist responses into final guidance: ${JSON.stringify(specialistResponses.map(r => r.response))}`
  );
  
  // 5. Store complete interaction in Zep with cost tracking
  const sessionData = {
    query: userQuery,
    response: masterResponse.choices[0].message.content,
    coaches_used: neededCoaches,
    total_cost: specialistResponses.reduce((sum, r) => sum + r.costTracking.modelCost, 0),
    total_tokens: specialistResponses.reduce((sum, r) => sum + r.costTracking.tokensUsed, 0),
    session_duration: Date.now() - startTime,
    models_used: specialistResponses.map(r => ({ coach: r.role, model: r.model }))
  };
  
  await addVoiceInteraction(sessionId, userQuery, masterResponse.choices[0].message.content);
  await trackCoachingCosts(userId, sessionId, sessionData);
  
  return {
    masterResponse,
    specialistInputs: specialistResponses,
    costBreakdown: sessionData,
    coachingFlow: neededCoaches
  }
}

function calculateModelCost(model: string, tokens: number): number {
  // OpenRouter pricing (approximate per 1M tokens)
  const pricing = {
    'openai/gpt-4-turbo': 10.0,
    'openai/gpt-4': 30.0,
    'anthropic/claude-3-sonnet': 3.0,
    'anthropic/claude-3-opus': 15.0,
    'google/gemini-pro': 0.5,
    'openai/gpt-3.5-turbo': 0.5
  };
  
  const costPer1M = pricing[model] || 1.0;
  return (tokens / 1000000) * costPer1M;
}
```

### **Phase 4: PostgreSQL Sync (Week 4)**

#### **4.1 Session Insights Sync**
```typescript
// lib/session-sync.ts
export async function syncSessionInsights(
  userId: string,
  sessionId: string
) {
  try {
    // Get session summary from Zep
    const sessionSummary = await zep.memory.get_session_summary(sessionId)
    
    // Extract key insights
    const insights = {
      keyPoints: sessionSummary.key_points || [],
      trinityUpdates: sessionSummary.trinity_changes || {},
      goalsProgress: sessionSummary.goal_updates || [],
      emotionalInsights: sessionSummary.emotional_patterns || {}
    }
    
    // Store in PostgreSQL
    await prisma.coachingSession.create({
      data: {
        userId,
        sessionId,
        sessionType: sessionSummary.metadata?.session_type,
        insights: insights,
        duration: sessionSummary.duration_minutes,
        satisfaction: sessionSummary.user_satisfaction,
        sourceSystem: 'zep',
        createdAt: new Date()
      }
    })
    
    // Update Trinity if changed
    if (insights.trinityUpdates && Object.keys(insights.trinityUpdates).length > 0) {
      await updateTrinityFromZep(userId, insights.trinityUpdates)
    }
    
    return insights
  } catch (error) {
    console.error('Session sync failed:', error)
    throw error
  }
}

async function updateTrinityFromZep(userId: string, trinityUpdates: any) {
  const existingTrinity = await prisma.trinity.findUnique({
    where: { userId }
  })
  
  const updatedTrinity = {
    ...existingTrinity,
    quest: trinityUpdates.quest || existingTrinity?.quest,
    service: trinityUpdates.service || existingTrinity?.service,
    pledge: trinityUpdates.pledge || existingTrinity?.pledge,
    lastUpdated: new Date(),
    updatedVia: 'zep_session'
  }
  
  await prisma.trinity.upsert({
    where: { userId },
    update: updatedTrinity,
    create: { userId, ...updatedTrinity }
  })
}
```

#### **4.2 Real-time Business Data Sync**
```typescript
// lib/business-data-sync.ts
export async function syncBusinessDataToZep(userId: string) {
  // Get latest profile data from PostgreSQL
  const userData = await prisma.user.findUnique({
    where: { id: userId },
    include: {
      workExperience: {
        include: { company: true }
      },
      skills: {
        include: { skill: true }
      },
      education: {
        include: { institution: true }
      },
      trinity: true
    }
  })
  
  if (!userData) return
  
  // Format for Zep graph
  const businessData = {
    profile: {
      name: `${userData.firstName} ${userData.lastName}`,
      email: userData.email,
      current_role: userData.workExperience[0]?.title,
      current_company: userData.workExperience[0]?.company?.name
    },
    work_history: userData.workExperience.map(exp => ({
      title: exp.title,
      company: exp.company.name,
      duration: `${exp.startDate} to ${exp.endDate || 'present'}`,
      achievements: exp.achievements
    })),
    skills: userData.skills.map(skill => ({
      name: skill.skill.name,
      proficiency: skill.proficiencyLevel,
      experience_years: skill.yearsOfExperience
    })),
    trinity: userData.trinity ? {
      quest: userData.trinity.quest,
      service: userData.trinity.service,
      pledge: userData.trinity.pledge,
      last_updated: userData.trinity.lastUpdated
    } : null
  }
  
  // Add to Zep graph
  await zep.graph.add({
    user_id: userId,
    type: 'json',
    data: JSON.stringify(businessData)
  })
}
```

## 🔧 **API Integrations**

### **Voice Coaching API Updates**
```typescript
// pages/api/hume-clm-sse/chat/completions/route.ts
import { getCoachingContext, addVoiceInteraction } from '@/lib/voice-session'

export async function POST(request: Request) {
  const { message, userId, sessionId } = await request.json()
  
  try {
    // Get Zep context
    const context = await getCoachingContext(userId, message, sessionId)
    
    // Generate response with context
    const response = await generateContextualResponse(message, context)
    
    // Store in Zep
    await addVoiceInteraction(sessionId, message, response)
    
    return NextResponse.json({ response, context: context.contextSummary })
  } catch (error) {
    console.error('Voice coaching error:', error)
    return NextResponse.json({ error: 'Coaching failed' }, { status: 500 })
  }
}
```

### **Session Management API**
```typescript
// pages/api/coaching/session/route.ts
export async function POST(request: Request) {
  const { userId, sessionType } = await request.json()
  
  try {
    // Start both Hume and Zep sessions
    const zepSessionId = await startVoiceSession(userId, sessionType)
    
    return NextResponse.json({
      sessionId: zepSessionId,
      status: 'started',
      sessionType
    })
  } catch (error) {
    return NextResponse.json({ error: 'Session start failed' }, { status: 500 })
  }
}

export async function DELETE(request: Request) {
  const { sessionId, userId } = await request.json()
  
  try {
    // Sync insights before ending
    await syncSessionInsights(userId, sessionId)
    
    return NextResponse.json({ status: 'session_ended' })
  } catch (error) {
    return NextResponse.json({ error: 'Session end failed' }, { status: 500 })
  }
}
```

## 📊 **Monitoring & Analytics**

### **Zep Performance Metrics**
```typescript
// lib/zep-analytics.ts
export async function getZepPerformanceMetrics(userId: string) {
  try {
    // Query recent sessions
    const sessions = await zep.memory.search_sessions({
      user_id: userId,
      limit: 10
    })
    
    // Calculate metrics
    return {
      total_sessions: sessions.length,
      avg_session_length: calculateAverageLength(sessions),
      context_retrieval_speed: await measureContextSpeed(userId),
      memory_efficiency: calculateMemoryEfficiency(sessions),
      trinity_evolution: await getTrinityEvolutionMetrics(userId)
    }
  } catch (error) {
    console.error('Zep analytics error:', error)
    return null
  }
}

async function measureContextSpeed(userId: string): Promise<number> {
  const start = Date.now()
  
  await zep.graph.search({
    user_id: userId,
    query: "test query",
    limit: 3
  })
  
  return Date.now() - start
}
```

## 🚨 **Error Handling & Fallbacks**

### **Graceful Degradation**
```typescript
// lib/zep-fallback.ts
export async function getContextWithFallback(
  userId: string,
  query: string,
  sessionId?: string
) {
  try {
    // Try Zep first
    return await getCoachingContext(userId, query, sessionId)
  } catch (error) {
    console.error('Zep unavailable, falling back to PostgreSQL:', error)
    
    // Fallback to PostgreSQL only
    return await getPostgreSQLContext(userId)
  }
}

async function getPostgreSQLContext(userId: string) {
  const userData = await prisma.user.findUnique({
    where: { id: userId },
    include: {
      trinity: true,
      workExperience: true,
      skills: true
    }
  })
  
  return {
    relevantFacts: [],
    recentMessages: [],
    trinity: userData?.trinity,
    contextSummary: `Fallback context for ${userData?.firstName}`
  }
}
```

### **Data Consistency Checks**
```typescript
// lib/data-consistency.ts
export async function validateZepPostgreSQLSync(userId: string) {
  try {
    // Get Trinity from both systems
    const [zepTrinity, pgTrinity] = await Promise.all([
      getZepTrinityData(userId),
      prisma.trinity.findUnique({ where: { userId } })
    ])
    
    // Compare and flag inconsistencies
    const inconsistencies = compareTrinitySources(zepTrinity, pgTrinity)
    
    if (inconsistencies.length > 0) {
      console.warn('Trinity sync inconsistencies:', inconsistencies)
      // Optional: Auto-resolve or alert
    }
    
    return { consistent: inconsistencies.length === 0, issues: inconsistencies }
  } catch (error) {
    console.error('Consistency check failed:', error)
    return { consistent: false, error: error.message }
  }
}
```

## 🔐 **Security & Privacy**

### **Data Encryption in Zep**
```typescript
// lib/zep-security.ts
export async function addSensitiveDataToZep(
  userId: string,
  data: any,
  encryptionLevel: 'standard' | 'high'
) {
  // Zep handles encryption, but we can add metadata about sensitivity
  await zep.graph.add({
    user_id: userId,
    type: 'json',
    data: JSON.stringify(data),
    metadata: {
      sensitivity_level: encryptionLevel,
      data_classification: 'personal_professional',
      retention_policy: '7_years'
    }
  })
}
```

### **GDPR Compliance**
```typescript
// lib/gdpr-zep.ts
export async function deleteUserFromZep(userId: string) {
  try {
    // Delete all user sessions
    const sessions = await zep.memory.search_sessions({
      user_id: userId,
      limit: 1000
    })
    
    for (const session of sessions) {
      await zep.memory.delete_session(session.id)
    }
    
    // Delete user graph data
    await zep.user.delete(userId)
    
    return { success: true, deleted_sessions: sessions.length }
  } catch (error) {
    console.error('Zep user deletion failed:', error)
    throw error
  }
}

export async function exportUserZepData(userId: string) {
  try {
    // Export all user data from Zep
    const [sessions, graphData] = await Promise.all([
      zep.memory.search_sessions({ user_id: userId, limit: 1000 }),
      zep.graph.get_subgraph(userId)
    ])
    
    return {
      sessions: sessions,
      knowledge_graph: graphData,
      exported_at: new Date().toISOString()
    }
  } catch (error) {
    console.error('Zep data export failed:', error)
    throw error
  }
}
```

## 📋 **Implementation Checklist**

### **Phase 1: Core Setup**
- [ ] Install Zep SDK and configure environment
- [ ] Update user creation flow to include Zep
- [ ] Test user ID consistency across systems
- [ ] Implement basic session management

### **Phase 2: Voice Integration**
- [ ] Enhance HumeVoiceInterface with Zep session tracking
- [ ] Implement context retrieval for coaching responses
- [ ] Add conversation storage to Zep
- [ ] Test voice coaching with memory continuity

### **Phase 3: Multi-Coach System**
- [ ] Implement specialist coach context retrieval
- [ ] Build master coach orchestration
- [ ] Test debate management with shared context
- [ ] Validate coaching quality with Zep context

### **Phase 4: Data Sync**
- [ ] Implement session insights sync to PostgreSQL
- [ ] Create business data sync to Zep
- [ ] Build consistency validation tools
- [ ] Test full data flow integrity

### **Phase 5: Production Readiness**
- [ ] Implement error handling and fallbacks
- [ ] Add performance monitoring
- [ ] Ensure GDPR compliance
- [ ] Create backup and recovery procedures

## 🔍 **Current Implementation Issues & Solutions**

### **Issue 1: No Real-Time Updates**
**Problem**: Graph doesn't update when mentioning new topics (France, French food)
**Root Causes**:
- Entity extraction hardcoded to specific patterns
- Refresh trigger mechanism may not be working
- Zep fact extraction delay

**Solution**:
```typescript
// Move from hardcoded patterns to dynamic extraction
const extractDynamicEntities = (fact: string) => {
  // Use NLP-based extraction instead of if statements
  const entities = nlpExtractor.extract(fact);
  return entities;
}
```

### **Issue 2: Cross-Session Memory Not Working**
**Problem**: Graph starts empty despite previous conversations
**Root Causes**:
- Session-based queries vs user-level queries
- Zep facts may not persist permanently
- Query method needs adjustment

**Solution**:
```typescript
// Query user-level facts, not just session
const allUserFacts = await zep.memory.searchUserMemory(userId, {
  limit: 50,
  includeAllSessions: true
});
```

### **Issue 3: Limited Entity Recognition**
**Problem**: Only recognizes predefined countries/foods
**Current State**: Hardcoded patterns for Spain, football, etc.
**Needed**: Dynamic NLP-based entity extraction

### **Key Files & Endpoints**
- `/src/lib/zep-client.ts` - Zep client with fact extraction
- `/src/app/api/zep-message/route.ts` - Stores voice messages
- `/src/app/api/live-context/route.ts` - Extracts relationships
- `/src/app/api/zep-test/route.ts` - Debug endpoint
- `/src/components/voice/ZepRelationshipView.tsx` - Graph display

## 📋 **Implementation Checklist (Updated)**

### **Phase 1: Core Setup** ✅
- [x] Install Zep SDK and configure environment
- [x] Update user creation flow to include Zep
- [x] Test user ID consistency across systems
- [x] Implement basic session management

### **Phase 2: Voice Integration** 🟡
- [x] Enhance HumeVoiceInterface with Zep session tracking
- [x] Implement context retrieval for coaching responses
- [x] Add conversation storage to Zep
- [ ] Test voice coaching with memory continuity (**Issue: Cross-session not working**)

### **Phase 3: Real-Time Updates** ❌
- [ ] Fix refresh trigger mechanism
- [ ] Implement dynamic entity extraction
- [ ] Add proper session vs user-level queries
- [ ] Ensure fact persistence

### **Phase 4: Data Sync** 🟡
- [x] Implement session insights sync to PostgreSQL (structure in place)
- [ ] Create business data sync to Zep
- [ ] Build consistency validation tools
- [ ] Test full data flow integrity

### **Phase 5: Production Readiness**
- [ ] Implement error handling and fallbacks
- [ ] Add performance monitoring
- [ ] Ensure GDPR compliance
- [ ] Create backup and recovery procedures

---

**Zep Integration** - Bringing persistent memory and temporal knowledge graphs to Quest Core's AI coaching system for truly personalized professional development.

**Current Focus**: Fixing real-time updates and cross-session memory to complete the integration.