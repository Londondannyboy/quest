# Arcade.dev Implementation Guide for Quest Core

*Last Updated: December 2024*

## Overview

This guide provides step-by-step instructions for integrating Arcade.dev into Quest Core, enabling AI-powered authenticated actions on behalf of users. We'll implement the job application workflow as our first use case.

## Prerequisites

- Quest Core V2 development environment
- Node.js 18+ and TypeScript
- Arcade.dev account (free tier to start)
- LangGraph knowledge (for workflows)

## Step 1: Initial Setup

### 1.1 Install Dependencies

```bash
npm install @arcade-ai/sdk @arcade-ai/langchain langchain @langchain/core
npm install --save-dev @types/node
```

### 1.2 Environment Configuration

Add to `.env.local`:
```env
# Arcade Configuration
ARCADE_API_KEY=your_arcade_api_key
ARCADE_WEBHOOK_SECRET=your_webhook_secret

# Existing Quest Core config
CLERK_USER_ID_FIELD=user_id
OPENROUTER_API_KEY=your_openrouter_key
```

### 1.3 Create Arcade Client

Create `lib/arcade/client.ts`:
```typescript
import { ArcadeClient } from '@arcade-ai/sdk'
import { auth } from '@clerk/nextjs'

let arcadeClient: ArcadeClient | null = null

export function getArcadeClient(): ArcadeClient {
  if (!arcadeClient) {
    arcadeClient = new ArcadeClient({
      apiKey: process.env.ARCADE_API_KEY!,
      environment: process.env.NODE_ENV === 'production' ? 'production' : 'development'
    })
  }
  return arcadeClient
}

export async function getArcadeToolManager(userId: string) {
  const client = getArcadeClient()
  return client.createToolManager({
    userId,
    userIdField: 'clerk_user_id'
  })
}
```

## Step 2: Authentication Flow

### 2.1 Create Auth Component

Create `components/arcade/ArcadeAuthButton.tsx`:
```typescript
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/use-toast'
import { Shield, CheckCircle } from 'lucide-react'

interface ArcadeAuthButtonProps {
  service: string
  userId: string
  onAuthComplete?: () => void
}

export function ArcadeAuthButton({ 
  service, 
  userId, 
  onAuthComplete 
}: ArcadeAuthButtonProps) {
  const [isAuthorized, setIsAuthorized] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { toast } = useToast()

  const handleAuth = async () => {
    setIsLoading(true)
    
    try {
      const response = await fetch('/api/arcade/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service, userId })
      })
      
      const data = await response.json()
      
      if (data.authUrl) {
        // Open OAuth flow in new window
        const authWindow = window.open(
          data.authUrl, 
          'arcade-auth', 
          'width=500,height=600'
        )
        
        // Poll for completion
        const checkAuth = setInterval(async () => {
          const statusRes = await fetch(`/api/arcade/auth/status?service=${service}`)
          const status = await statusRes.json()
          
          if (status.authorized) {
            clearInterval(checkAuth)
            authWindow?.close()
            setIsAuthorized(true)
            toast({
              title: "Authorization successful",
              description: `Connected to ${service}`
            })
            onAuthComplete?.()
          }
        }, 2000)
      }
    } catch (error) {
      toast({
        title: "Authorization failed",
        description: "Please try again",
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Button
      onClick={handleAuth}
      disabled={isLoading || isAuthorized}
      variant={isAuthorized ? "secondary" : "default"}
      className="gap-2"
    >
      {isAuthorized ? (
        <>
          <CheckCircle className="h-4 w-4" />
          Connected to {service}
        </>
      ) : (
        <>
          <Shield className="h-4 w-4" />
          Connect {service}
        </>
      )}
    </Button>
  )
}
```

### 2.2 API Routes for Auth

Create `app/api/arcade/auth/route.ts`:
```typescript
import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs'
import { getArcadeToolManager } from '@/lib/arcade/client'

export async function POST(request: NextRequest) {
  const { userId } = auth()
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { service } = await request.json()
  
  try {
    const toolManager = await getArcadeToolManager(userId)
    const authData = await toolManager.requestAuthorization(service)
    
    return NextResponse.json({
      authUrl: authData.authorizationUrl,
      authId: authData.authorizationId
    })
  } catch (error) {
    console.error('Arcade auth error:', error)
    return NextResponse.json(
      { error: 'Failed to initialize authorization' },
      { status: 500 }
    )
  }
}
```

## Step 3: LangGraph Workflow Integration

### 3.1 Create Base Workflow

Create `lib/arcade/workflows/base.ts`:
```typescript
import { StateGraph, END } from '@langchain/langgraph'
import { BaseMessage, HumanMessage, AIMessage } from '@langchain/core/messages'
import { ChatOpenAI } from '@langchain/openai'
import { getArcadeToolManager } from '../client'

// Define the state interface
export interface WorkflowState {
  messages: BaseMessage[]
  userId: string
  requiresAuth: boolean
  authServices: string[]
}

// Create base workflow class
export class ArcadeWorkflow {
  private graph: StateGraph<WorkflowState>
  private model: ChatOpenAI

  constructor() {
    this.model = new ChatOpenAI({
      temperature: 0.7,
      modelName: 'gpt-4-turbo-preview'
    })
    
    this.graph = new StateGraph<WorkflowState>({
      channels: {
        messages: {
          value: (x: BaseMessage[], y: BaseMessage[]) => x.concat(y),
          default: () => []
        },
        userId: {
          value: (x: string) => x,
          default: () => ''
        },
        requiresAuth: {
          value: (x: boolean) => x,
          default: () => false
        },
        authServices: {
          value: (x: string[]) => x,
          default: () => []
        }
      }
    })
    
    this.setupNodes()
    this.setupEdges()
  }

  private setupNodes() {
    // Agent node
    this.graph.addNode('agent', async (state) => {
      const toolManager = await getArcadeToolManager(state.userId)
      const tools = await toolManager.getTools(['gmail', 'linkedin', 'calendar'])
      
      const modelWithTools = this.model.bind({
        tools: tools.map(t => t.schema)
      })
      
      const response = await modelWithTools.invoke(state.messages)
      
      return {
        messages: [response],
        requiresAuth: false,
        authServices: []
      }
    })

    // Authorization check node
    this.graph.addNode('auth_check', async (state) => {
      const lastMessage = state.messages[state.messages.length - 1]
      
      if ('tool_calls' in lastMessage) {
        const toolManager = await getArcadeToolManager(state.userId)
        const requiredAuth = await toolManager.checkRequiredAuth(
          lastMessage.tool_calls
        )
        
        return {
          requiresAuth: requiredAuth.length > 0,
          authServices: requiredAuth
        }
      }
      
      return {
        requiresAuth: false,
        authServices: []
      }
    })

    // Tool execution node
    this.graph.addNode('tools', async (state) => {
      const toolManager = await getArcadeToolManager(state.userId)
      const lastMessage = state.messages[state.messages.length - 1]
      
      if ('tool_calls' in lastMessage) {
        const results = await toolManager.executeTool(
          lastMessage.tool_calls[0]
        )
        
        return {
          messages: [
            new AIMessage({
              content: JSON.stringify(results),
              name: 'tool_result'
            })
          ]
        }
      }
      
      return { messages: [] }
    })
  }

  private setupEdges() {
    this.graph.setEntryPoint('agent')
    
    this.graph.addConditionalEdges('agent', (state) => {
      const lastMessage = state.messages[state.messages.length - 1]
      
      if ('tool_calls' in lastMessage && lastMessage.tool_calls.length > 0) {
        return 'auth_check'
      }
      return END
    })
    
    this.graph.addConditionalEdges('auth_check', (state) => {
      if (state.requiresAuth) {
        return END // Pause for auth
      }
      return 'tools'
    })
    
    this.graph.addEdge('tools', 'agent')
  }

  compile() {
    return this.graph.compile()
  }
}
```

## Step 4: Job Application Workflow

### 4.1 Create Job Application Agent

Create `lib/arcade/workflows/job-application.ts`:
```typescript
import { ArcadeWorkflow } from './base'
import { HumanMessage } from '@langchain/core/messages'

export class JobApplicationWorkflow extends ArcadeWorkflow {
  async applyToJob(
    userId: string,
    jobData: {
      title: string
      company: string
      description: string
      applicationEmail: string
    },
    userProfile: {
      name: string
      trinity: {
        quest: string
        service: string
        pledge: string
      }
      resume: string
    }
  ) {
    const workflow = this.compile()
    
    // Generate Trinity-aligned cover letter
    const coverLetterPrompt = `
      Generate a cover letter for ${userProfile.name} applying to ${jobData.title} at ${jobData.company}.
      
      User's Trinity:
      - Quest: ${userProfile.trinity.quest}
      - Service: ${userProfile.trinity.service}
      - Pledge: ${userProfile.trinity.pledge}
      
      Job Description: ${jobData.description}
      
      Create a compelling cover letter that:
      1. Shows alignment between the user's Trinity and the role
      2. Highlights relevant experience from their background
      3. Expresses authentic enthusiasm
      4. Maintains professional tone while showing personality
      5. Ends with a clear call to action
      
      Then send the application email to ${jobData.applicationEmail} with the cover letter and attached resume.
    `
    
    const initialState = {
      messages: [new HumanMessage(coverLetterPrompt)],
      userId,
      requiresAuth: false,
      authServices: []
    }
    
    // Execute workflow
    const stream = await workflow.stream(initialState)
    
    const results = []
    for await (const chunk of stream) {
      results.push(chunk)
      
      // Check if auth is required
      if (chunk.auth_check?.requiresAuth) {
        return {
          status: 'auth_required',
          services: chunk.auth_check.authServices,
          resumeData: initialState
        }
      }
    }
    
    return {
      status: 'completed',
      results
    }
  }

  async scheduleFollowUp(
    userId: string,
    jobData: {
      title: string
      company: string
      applicationDate: Date
    }
  ) {
    const workflow = this.compile()
    
    const followUpPrompt = `
      Schedule a follow-up task in Google Calendar for 1 week from now to check on the application status for:
      - Position: ${jobData.title}
      - Company: ${jobData.company}
      - Applied on: ${jobData.applicationDate}
      
      Create a calendar event with:
      - Title: "Follow up on ${jobData.company} - ${jobData.title} application"
      - Duration: 30 minutes
      - Description: Include tips for following up professionally
    `
    
    const initialState = {
      messages: [new HumanMessage(followUpPrompt)],
      userId,
      requiresAuth: false,
      authServices: []
    }
    
    return await workflow.stream(initialState)
  }
}
```

### 4.2 Create Job Application UI

Create `components/quest/JobApplicationCard.tsx`:
```typescript
import { useState } from 'react'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Briefcase, Mail, Calendar, ChevronRight } from 'lucide-react'
import { ArcadeAuthButton } from '@/components/arcade/ArcadeAuthButton'
import { useToast } from '@/components/ui/use-toast'

interface JobApplicationCardProps {
  job: {
    id: string
    title: string
    company: string
    description: string
    applicationEmail: string
    trinityAlignment: number
  }
  userId: string
  userProfile: any
}

export function JobApplicationCard({ 
  job, 
  userId, 
  userProfile 
}: JobApplicationCardProps) {
  const [isApplying, setIsApplying] = useState(false)
  const [authRequired, setAuthRequired] = useState<string[]>([])
  const { toast } = useToast()

  const handleApply = async () => {
    setIsApplying(true)
    
    try {
      const response = await fetch('/api/jobs/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jobId: job.id,
          jobData: job,
          userProfile
        })
      })
      
      const result = await response.json()
      
      if (result.status === 'auth_required') {
        setAuthRequired(result.services)
        toast({
          title: "Authorization required",
          description: `Please connect ${result.services.join(', ')} to continue`
        })
      } else if (result.status === 'completed') {
        toast({
          title: "Application sent!",
          description: `Successfully applied to ${job.title} at ${job.company}`
        })
      }
    } catch (error) {
      toast({
        title: "Application failed",
        description: "Please try again",
        variant: "destructive"
      })
    } finally {
      setIsApplying(false)
    }
  }

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-xl">{job.title}</CardTitle>
            <CardDescription className="text-lg">{job.company}</CardDescription>
          </div>
          <Badge 
            variant={job.trinityAlignment > 0.8 ? "default" : "secondary"}
            className="ml-4"
          >
            {Math.round(job.trinityAlignment * 100)}% Match
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-3">
          {job.description}
        </p>
        
        {authRequired.length > 0 && (
          <div className="mt-4 space-y-2">
            <p className="text-sm font-medium">Connect services to apply:</p>
            <div className="flex gap-2">
              {authRequired.map(service => (
                <ArcadeAuthButton
                  key={service}
                  service={service}
                  userId={userId}
                  onAuthComplete={() => {
                    setAuthRequired(prev => prev.filter(s => s !== service))
                  }}
                />
              ))}
            </div>
          </div>
        )}
      </CardContent>
      
      <CardFooter className="gap-2">
        <Button
          onClick={handleApply}
          disabled={isApplying || authRequired.length > 0}
          className="flex-1"
        >
          {isApplying ? (
            <>Applying...</>
          ) : (
            <>
              <Mail className="mr-2 h-4 w-4" />
              Apply with Quest
            </>
          )}
        </Button>
        
        <Button variant="outline" size="icon">
          <Calendar className="h-4 w-4" />
        </Button>
        
        <Button variant="ghost" size="icon">
          <ChevronRight className="h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  )
}
```

## Step 5: API Implementation

### 5.1 Job Application API

Create `app/api/jobs/apply/route.ts`:
```typescript
import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs'
import { JobApplicationWorkflow } from '@/lib/arcade/workflows/job-application'

export async function POST(request: NextRequest) {
  const { userId } = auth()
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { jobData, userProfile } = await request.json()
  
  try {
    const workflow = new JobApplicationWorkflow()
    const result = await workflow.applyToJob(
      userId,
      jobData,
      userProfile
    )
    
    // Save application to database
    if (result.status === 'completed') {
      await saveJobApplication({
        userId,
        jobId: jobData.id,
        status: 'applied',
        appliedAt: new Date()
      })
    }
    
    return NextResponse.json(result)
  } catch (error) {
    console.error('Job application error:', error)
    return NextResponse.json(
      { error: 'Failed to submit application' },
      { status: 500 }
    )
  }
}
```

## Step 6: Database Schema Updates

### 6.1 Update Prisma Schema

Add to `prisma/schema.prisma`:
```prisma
model ArcadeAuthorization {
  id          String   @id @default(cuid())
  userId      String
  service     String
  authorized  Boolean  @default(false)
  scopes      String[]
  authorizedAt DateTime?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  
  user        User     @relation(fields: [userId], references: [id])
  
  @@unique([userId, service])
  @@index([userId])
}

model JobApplication {
  id           String   @id @default(cuid())
  userId       String
  jobId        String
  jobTitle     String
  company      String
  status       String   // applied, interview, offer, rejected
  appliedAt    DateTime
  followUpDate DateTime?
  notes        String?
  
  user         User     @relation(fields: [userId], references: [id])
  
  @@index([userId])
  @@index([status])
}
```

## Step 7: Testing

### 7.1 Test Authentication Flow

Create `__tests__/arcade-auth.test.ts`:
```typescript
import { getArcadeClient, getArcadeToolManager } from '@/lib/arcade/client'

describe('Arcade Authentication', () => {
  it('should create tool manager for user', async () => {
    const userId = 'test-user-123'
    const toolManager = await getArcadeToolManager(userId)
    
    expect(toolManager).toBeDefined()
    expect(toolManager.userId).toBe(userId)
  })
  
  it('should request Gmail authorization', async () => {
    const userId = 'test-user-123'
    const toolManager = await getArcadeToolManager(userId)
    
    const authData = await toolManager.requestAuthorization('gmail')
    
    expect(authData.authorizationUrl).toContain('accounts.google.com')
    expect(authData.authorizationId).toBeDefined()
  })
})
```

### 7.2 Test Job Application Workflow

Create `__tests__/job-application.test.ts`:
```typescript
import { JobApplicationWorkflow } from '@/lib/arcade/workflows/job-application'

describe('Job Application Workflow', () => {
  it('should generate Trinity-aligned cover letter', async () => {
    const workflow = new JobApplicationWorkflow()
    
    const result = await workflow.applyToJob(
      'test-user-123',
      {
        title: 'Senior Software Engineer',
        company: 'TechCorp',
        description: 'Building AI products...',
        applicationEmail: 'jobs@techcorp.com'
      },
      {
        name: 'John Doe',
        trinity: {
          quest: 'Build AI that empowers humans',
          service: 'Make complex technology accessible',
          pledge: 'Always prioritize user privacy'
        },
        resume: 'resume-content-here'
      }
    )
    
    expect(result.status).toBe('auth_required')
    expect(result.services).toContain('gmail')
  })
})
```

## Step 8: Monitoring & Analytics

### 8.1 Track Usage

Create `lib/arcade/analytics.ts`:
```typescript
export async function trackArcadeUsage(event: {
  userId: string
  action: string
  service: string
  success: boolean
  metadata?: any
}) {
  await fetch('/api/analytics/track', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      event: 'arcade_action',
      ...event
    })
  })
}
```

### 8.2 Usage Dashboard

Create a dashboard to monitor:
- Authorization success rate
- Most used services
- Actions per user
- Error rates

## Step 9: Production Deployment

### 9.1 Environment Variables

Ensure production environment has:
```env
ARCADE_API_KEY=prod_key
ARCADE_WEBHOOK_SECRET=prod_secret
ARCADE_ENVIRONMENT=production
```

### 9.2 Security Checklist

- [ ] Validate all user inputs
- [ ] Use HTTPS for all callbacks
- [ ] Implement rate limiting
- [ ] Add request signing
- [ ] Enable audit logging
- [ ] Set up monitoring alerts

## Step 10: User Documentation

### 10.1 Create Help Center Article

Write documentation covering:
- What is Arcade and why we use it
- Which services are supported
- How to authorize services
- How to revoke access
- Privacy and security FAQ

### 10.2 Onboarding Flow

Update onboarding to include:
1. Explanation of AI actions
2. Optional service connections
3. Example use cases
4. Privacy reassurances

## Next Steps

1. **Expand Workflows**: Add LinkedIn networking, calendar scheduling
2. **Multi-Agent System**: Create specialized agents for different tasks
3. **Cross-Platform**: Integrate with Placement Agents and Quest PR
4. **Advanced Features**: Batch operations, scheduled tasks, webhooks

## Troubleshooting

### Common Issues

1. **"Tool not found" error**
   - Check service name spelling
   - Verify service is enabled in Arcade dashboard

2. **Authentication fails**
   - Check OAuth redirect URLs
   - Verify scopes requested

3. **Rate limits**
   - Implement exponential backoff
   - Use batch operations where possible

---

*This implementation guide will evolve as we discover best practices and optimize the integration.*