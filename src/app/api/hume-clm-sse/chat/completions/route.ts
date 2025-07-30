import { NextRequest } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'
import { getOrCreateSession, addMessage, getUserJourneyContext } from '@/lib/zep'
import { User, Trinity, ProfessionalMirror } from '@prisma/client'

export async function POST(req: NextRequest) {
  // Log CLM call details
  const callId = `clm_${Date.now()}`
  console.log(`[CLM ${callId}] ========== NEW CLM REQUEST ==========`)
  
  try {
    // Get the current user
    // Try to get userId from multiple sources
    let userId = null
    let userSource = 'none'
    
    // First try from auth (won't work for Hume server-to-server calls)
    const authResult = await auth()
    if (authResult?.userId) {
      userId = authResult.userId
      userSource = 'clerk_auth'
    }
    
    // Parse the request from Hume
    const body = await req.json()
    const messages = body.messages || []
    const lastUserMessage = messages.findLast((m: { role: string; content?: string }) => m.role === 'user')?.content || ''
    
    // Log request details
    console.log(`[CLM ${callId}] Request body:`, {
      messageCount: messages.length,
      lastMessage: lastUserMessage?.substring(0, 50) + '...',
      model: body.model,
      stream: body.stream
    })
    
    // Try to get userId from headers if not from auth
    if (!userId) {
      // Check various header formats
      const headerChecks = [
        'x-hume-user-id',
        'x-user-id',
        'x-forwarded-user',
        'x-custom-user-id',
        'hume-user-id',
        'user-id'
      ]
      
      for (const header of headerChecks) {
        const value = req.headers.get(header)
        if (value) {
          userId = value
          userSource = `header:${header}`
          break
        }
      }
      
      // Check if user info is in the request body metadata
      const messages = body.messages || []
      if (!userId && messages.length > 0) {
        const lastMessage = messages[messages.length - 1]
        if (lastMessage.metadata?.user_id) {
          userId = lastMessage.metadata.user_id
          userSource = 'message_metadata'
          console.log(`[CLM ${callId}] Found user from message metadata:`, userId)
        }
      }
      
      // Log all headers for debugging
      console.log(`[CLM ${callId}] Headers:`, Object.fromEntries(req.headers.entries()))
      
      // TEMPORARY: For testing, use the most recent user in the system
      // TODO: Pass user ID from Hume configuration
      if (!userId) {
        console.log(`[CLM ${callId}] No userId found in headers, using most recent user for testing`)
        
        // Get the most recent user with trinity data
        const recentUser = await prisma.user.findFirst({
          where: {
            trinity: {
              isNot: null
            }
          },
          orderBy: { updatedAt: 'desc' },
          include: {
            professionalMirror: true
          }
        })
        
        userId = recentUser?.clerkId || null
        userSource = 'database_fallback'
        console.log(`[CLM ${callId}] Found recent user:`, recentUser?.name || 'Unknown')
      }
    }
    
    console.log(`[CLM ${callId}] User identification:`, { userId, userSource })

    // Get user context if authenticated
    let userContext = ''
    let user: (User & {
      trinity: Trinity | null
      professionalMirror: ProfessionalMirror | null
    }) | null = null
    
    if (userId) {
      try {
        user = await prisma.user.findUnique({
          where: { clerkId: userId },
          include: {
            trinity: true,
            professionalMirror: true,
          }
        })

        if (user) {
          // Get memory context from Zep
          const journeyContext = await getUserJourneyContext(user.id)
          
          userContext = `
User Context:
- Name: ${user.name || 'Unknown'}
- Has Trinity: ${user.trinity ? 'Yes' : 'No'}
- Has Professional Mirror: ${user.professionalMirror ? 'Yes' : 'No'}
`
          
          // Add professional mirror data if available
          if (user.professionalMirror) {
            const pmData = user.professionalMirror
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const linkedinData = pmData.rawLinkedinData as any
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const enrichmentData = pmData.enrichmentData as any
            
            userContext += `
Professional Background:
- LinkedIn: ${pmData.linkedinUrl || 'Not connected'}
- Last scraped: ${pmData.lastScraped ? new Date(pmData.lastScraped).toLocaleDateString() : 'Never'}
`
            
            if (linkedinData) {
              userContext += `- Current Role: ${linkedinData.headline || 'Unknown'}
- Location: ${linkedinData.location || 'Unknown'}
- Experience: ${linkedinData.experience?.length || 0} positions
`
            }
            
            if (enrichmentData) {
              userContext += `- Company: ${enrichmentData.company || 'Unknown'}
- Industry: ${enrichmentData.industry || 'Unknown'}
`
            }
          }
          if (user.trinity) {
            userContext += `
Trinity Summary:
- Past Quest: ${user.trinity.pastQuest?.substring(0, 50)}...
- Present Quest: ${user.trinity.presentQuest?.substring(0, 50)}...
- Future Quest: ${user.trinity.futureQuest?.substring(0, 50)}...
- Clarity Score: ${user.trinity.clarityScore}%
`
          }
          
          // Add journey context from memory
          userContext += `\n${journeyContext}`
          
          // Create/update Zep session
          const session = await getOrCreateSession(user.id, 'trinity', {
            trinityClarity: user.trinity?.clarityScore || 0
          })
          
          // Store the conversation in memory
          if (lastUserMessage && session.sessionId) {
            await addMessage(session.sessionId, 'user', lastUserMessage)
          }
        }
      } catch (error) {
        console.error('Error fetching user context:', error)
      }
    }

    // Determine which coach personality based on the conversation
    const coachPrompt = determineCoachPrompt(messages, userContext)

    // Create the response in OpenAI SSE format
    const encoder = new TextEncoder()
    const stream = new ReadableStream({
      async start(controller) {
        try {
          // Send initial message
          const initialChunk = {
            id: `chatcmpl-${Date.now()}`,
            object: 'chat.completion.chunk',
            created: Math.floor(Date.now() / 1000),
            model: 'gpt-4',
            choices: [{
              index: 0,
              delta: { role: 'assistant', content: '' },
              finish_reason: null
            }]
          }
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(initialChunk)}\n\n`))

          // Generate response based on coach personality with context
          const response = await generateCoachResponse(lastUserMessage, coachPrompt, userContext)
          
          // Store assistant response in memory if user is authenticated
          if (userId && user) {
            const session = await getOrCreateSession(user.id, 'trinity')
            if (session.sessionId) {
              await addMessage(session.sessionId, 'assistant', response, {
                coachType: coachPrompt.includes('Story Coach') ? 'STORY_COACH' : 
                          coachPrompt.includes('Quest Coach') ? 'QUEST_COACH' : 'DELIVERY_COACH'
              })
            }
          }
          
          // Stream the response in chunks
          const words = response.split(' ')
          for (let i = 0; i < words.length; i++) {
            const chunk = {
              id: `chatcmpl-${Date.now()}`,
              object: 'chat.completion.chunk',
              created: Math.floor(Date.now() / 1000),
              model: 'gpt-4',
              choices: [{
                index: 0,
                delta: { content: words[i] + (i < words.length - 1 ? ' ' : '') },
                finish_reason: null
              }]
            }
            controller.enqueue(encoder.encode(`data: ${JSON.stringify(chunk)}\n\n`))
            
            // Small delay to simulate streaming
            await new Promise(resolve => setTimeout(resolve, 50))
          }

          // Send completion
          const finalChunk = {
            id: `chatcmpl-${Date.now()}`,
            object: 'chat.completion.chunk',
            created: Math.floor(Date.now() / 1000),
            model: 'gpt-4',
            choices: [{
              index: 0,
              delta: {},
              finish_reason: 'stop'
            }]
          }
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(finalChunk)}\n\n`))
          controller.enqueue(encoder.encode('data: [DONE]\n\n'))
          
          controller.close()
        } catch (error) {
          console.error('Stream error:', error)
          controller.error(error)
        }
      }
    })

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    })
  } catch (error) {
    console.error('Hume CLM error:', error)
    return new Response('Internal Server Error', { status: 500 })
  }
}

function determineCoachPrompt(messages: { role: string; content: string }[], userContext: string): string {
  // Check conversation history to determine which coach we are
  const conversationText = messages.map((m) => m.content).join(' ').toLowerCase()
  
  if (!userContext.includes('Has Trinity: Yes') || conversationText.includes('story')) {
    return `You are the Story Coach, a warm and empathetic guide helping users explore their professional journey. 
    Your voice is gentle yet purposeful, like a wise mentor who truly cares about understanding their story.
    Ask thoughtful questions about their career transitions, motivations, and what drives them.
    Focus on uncovering the deeper narrative of their professional life.`
  } else if (conversationText.includes('quest') || conversationText.includes('ready')) {
    return `You are the Quest Coach, an inspiring and strategic guide helping users clarify their Trinity.
    Your voice is energetic and focused, like a coach preparing an athlete for their moment.
    Help them articulate their Quest (what they must do), Service (who they help), and Pledge (their promise).
    Guide them to see how their past, present, and future align into a clear mission.`
  } else {
    return `You are the Delivery Coach, a practical and action-oriented guide helping users make their Quest real.
    Your voice is confident and direct, like a seasoned executive who gets things done.
    Focus on concrete next steps, accountability, and turning their vision into reality.
    Help them commit to specific actions and overcome obstacles.`
  }
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
async function generateCoachResponse(userMessage: string, coachPrompt: string, _userContext: string): Promise<string> {
  // For now, return coach-appropriate responses
  // In production, this would call OpenRouter or another LLM
  
  const lowerMessage = userMessage.toLowerCase()
  
  if (lowerMessage.includes('hello') || lowerMessage.includes('hi')) {
    if (coachPrompt.includes('Story Coach')) {
      return "Hello there! I'm so glad you're here. I'm your Story Coach, and I'm here to help you explore the deeper narrative of your professional journey. What brings you to this moment of reflection today?"
    } else if (coachPrompt.includes('Quest Coach')) {
      return "Welcome! I'm your Quest Coach, and I'm excited to help you discover your Trinity - your Quest, Service, and Pledge. Let's clarify what you're truly meant to do. What's calling to you right now?"
    } else {
      return "Let's get to work! I'm your Delivery Coach, and I'm here to help you turn that vision into reality. No more waiting - what's the first concrete step you need to take?"
    }
  }
  
  // Default contextual response
  return "I hear you. Tell me more about that - what does this mean for your journey?"
}