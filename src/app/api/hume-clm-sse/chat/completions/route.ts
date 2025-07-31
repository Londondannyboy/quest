import { NextRequest } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'
import { getOrCreateSession, addMessage, getUserJourneyContext } from '@/lib/zep'
import { syncUserToZep, getUserFromZep, UserProfile } from '@/lib/zep-user-sync'
import { User, Trinity, ProfessionalMirror } from '@prisma/client'

export async function POST(req: NextRequest) {
  // Log CLM call details
  const callId = `clm_${Date.now()}`
  console.log(`[CLM ${callId}] ========== NEW CLM REQUEST ==========`)
  console.log(`[CLM ${callId}] Request method:`, req.method)
  console.log(`[CLM ${callId}] Request URL:`, req.url)
  
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
    
    // Log all messages to see if context is being passed
    console.log(`[CLM ${callId}] All messages:`, messages.map((m: { role: string; content?: string; metadata?: unknown }) => ({
      role: m.role,
      content: m.content?.substring(0, 100) + '...',
      hasMetadata: !!m.metadata
    })))
    
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
        // Check for ClerkID in context messages
        for (const msg of messages) {
          if (msg.content && typeof msg.content === 'string') {
            const clerkIdMatch = msg.content.match(/ClerkID:\s*([\w-]+)/)
            if (clerkIdMatch) {
              userId = clerkIdMatch[1]
              userSource = 'context_clerkid'
              console.log(`[CLM ${callId}] Found ClerkID from context:`, userId)
              break
            }
          }
        }
        
        // Also check metadata
        const lastMessage = messages[messages.length - 1]
        if (!userId && lastMessage.metadata?.user_id) {
          userId = lastMessage.metadata.user_id
          userSource = 'message_metadata'
          console.log(`[CLM ${callId}] Found user from message metadata:`, userId)
        }
      }
      
      // Log all headers for debugging
      const allHeaders = Object.fromEntries(req.headers.entries())
      console.log(`[CLM ${callId}] Headers:`, allHeaders)
      
      // Check for Clerk session in cookies
      const cookieHeader = req.headers.get('cookie')
      if (cookieHeader && cookieHeader.includes('__session')) {
        console.log(`[CLM ${callId}] Found Clerk session cookie`)
      }
      
      // Try to extract from system message or any message containing ClerkID
      if (!userId && body.messages) {
        for (const msg of body.messages) {
          if (msg.role === 'system' && msg.content) {
            const systemClerkId = msg.content.match(/ClerkID:\s*([\w-]+)/)
            if (systemClerkId) {
              userId = systemClerkId[1]
              userSource = 'system_message'
              console.log(`[CLM ${callId}] Found ClerkID in system message:`, userId)
              break
            }
          }
        }
      }
      
      // TEMPORARY: For testing, use the most recent user in the system
      // TODO: Pass user ID from Hume configuration
      if (!userId) {
        console.log(`[CLM ${callId}] No userId found, checking database fallback`)
        
        try {
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
        } catch (dbError) {
          console.error(`[CLM ${callId}] Database error:`, dbError)
          console.log(`[CLM ${callId}] Using hardcoded fallback for demo`)
          // For demo purposes, use the auth userId if available
          if (authResult?.userId) {
            userId = authResult.userId
            userSource = 'auth_fallback'
          }
        }
      }
    }
    
    console.log(`[CLM ${callId}] User identification:`, { userId, userSource })
    
    // Log the full request for debugging
    console.log(`[CLM ${callId}] Full request body:`, JSON.stringify(body, null, 2))

    // Get user context if authenticated
    let userContext = ''
    let userProfile: UserProfile | null = null
    let user: (User & {
      trinity: Trinity | null
      professionalMirror: ProfessionalMirror | null
    }) | null = null
    
    if (userId) {
      // First, try to sync from database to Zep
      console.log(`[CLM ${callId}] Syncing user data for ClerkID:`, userId)
      userProfile = await syncUserToZep(userId)
      
      if (!userProfile) {
        console.log(`[CLM ${callId}] No user profile found, trying Zep directly`)
        userProfile = await getUserFromZep(userId)
      }
      
      if (userProfile) {
        console.log(`[CLM ${callId}] User profile from Zep:`, {
          name: userProfile.name,
          email: userProfile.email,
          hasTrinity: !!userProfile.trinity,
          hasProfessionalMirror: !!userProfile.professionalMirror
        })
        
        // Convert UserProfile to User format for compatibility
        user = {
          id: userProfile.userId,
          clerkId: userProfile.clerkId,
          email: userProfile.email,
          name: userProfile.name,
          trinity: userProfile.trinity ? {
            id: 'zep-trinity',
            userId: userProfile.userId,
            pastQuest: userProfile.trinity.pastQuest || null,
            presentQuest: userProfile.trinity.presentQuest || null,
            futureQuest: userProfile.trinity.futureQuest || null,
            pastService: null,
            presentService: null,
            futureService: null,
            pastPledge: null,
            presentPledge: null,
            futurePledge: null,
            clarityScore: userProfile.trinity.clarityScore,
            evolutionData: null,
            createdAt: new Date(),
            updatedAt: new Date()
          } : null,
          professionalMirror: userProfile.professionalMirror ? {
            id: 'zep-pm',
            userId: userProfile.userId,
            linkedinUrl: userProfile.professionalMirror.linkedinUrl || null,
            lastScraped: null,
            rawLinkedinData: {
              headline: userProfile.professionalMirror.headline,
              company: userProfile.professionalMirror.company,
              location: userProfile.professionalMirror.location
            },
            enrichmentData: null,
            companyScraped: false,
            employeesScrapedAt: null,
            createdAt: new Date(),
            updatedAt: new Date()
          } : null,
          createdAt: new Date(),
          updatedAt: new Date()
        } as User & {
          trinity: Trinity | null
          professionalMirror: ProfessionalMirror | null
        }
      } else {
        // Ultimate fallback for known users
        console.log(`[CLM ${callId}] No profile in Zep, using hardcoded fallback`)
        const isKnownUser = userId === 'user_30WYPgDczAxAn5M24tqNcfd0w1E'
        user = {
          id: isKnownUser ? 'dan-keegan' : 'demo-user',
          clerkId: userId,
          email: isKnownUser ? 'keegan.dan@gmail.com' : 'demo@example.com',
          name: isKnownUser ? 'Dan' : 'Demo User',
          trinity: null,
          professionalMirror: null,
          createdAt: new Date(),
          updatedAt: new Date()
        } as User & {
          trinity: Trinity | null
          professionalMirror: ProfessionalMirror | null
        }
      }

      if (user) {
        try {
          // Get memory context from Zep
          let journeyContext = ''
          try {
            journeyContext = await getUserJourneyContext(user.id)
          } catch (error) {
            console.error(`[CLM ${callId}] Error getting journey context:`, error)
          }
          
          userContext = `
User Context:
- Name: ${user.name || 'Unknown'}
- Email: ${user.email || 'Unknown'}
- Clerk ID: ${user.clerkId}
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
        } catch (error) {
          console.error('Error fetching user context:', error)
        }
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

          // Log what we're sending to the coach
          console.log(`[CLM ${callId}] Generating response with context:`, {
            hasUser: !!user,
            userName: user?.name || 'Unknown',
            contextLength: userContext.length
          })

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
            
            // Minimal delay for natural streaming
            if (i % 3 === 0) { // Only delay every 3rd word
              await new Promise(resolve => setTimeout(resolve, 5))
            }
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

async function generateCoachResponse(userMessage: string, coachPrompt: string, userContext: string): Promise<string> {
  // Enhanced responses with user context
  // TODO: Use contextualPrompt with OpenRouter or Claude API
  // const contextualPrompt = `${coachPrompt}\n\nUser Context:\n${userContext}\n\nUser says: ${userMessage}\n\nRespond naturally and personally, using their name if available.`
  
  const lowerMessage = userMessage.toLowerCase()
  
  // Extract user name from context
  const nameMatch = userContext.match(/Name:\s*([^\n]+)/);
  const userName = nameMatch && nameMatch[1] !== 'Unknown' ? nameMatch[1] : null;
  
  // For demo mode when database is not available
  const emailMatch = userContext.match(/email:\s*([^\n]+)/);
  const userEmail = emailMatch ? emailMatch[1] : null;
  
  if (lowerMessage.includes('who am i') || lowerMessage.includes('my name')) {
    if (userName) {
      return `You're ${userName}! ${userContext.includes('Has Trinity: Yes') ? "I can see you've already begun exploring your Trinity. " : "I'm here to help you discover your Trinity. "}How can I support you today?`;
    } else if (userEmail) {
      return `I can see your email is ${userEmail}, but I don't have your name yet. I'm here to help you discover your Trinity. What should I call you?`;
    } else if (userContext.includes('Demo User')) {
      return "I'm in demo mode right now, but I'm still here to help you explore your Trinity! I'm your Story Coach. What brings you to this moment of reflection?";
    } else {
      return "I don't have your name yet, but I'm here to help you discover your Trinity. What should I call you?";
    }
  }
  
  if (lowerMessage.includes('hello') || lowerMessage.includes('hi')) {
    const greeting = userName ? `Hello ${userName}!` : "Hello there!";
    if (coachPrompt.includes('Story Coach')) {
      return `${greeting} I'm your Story Coach, and I'm here to help you explore the deeper narrative of your professional journey. What brings you to this moment of reflection today?`
    } else if (coachPrompt.includes('Quest Coach')) {
      return `${greeting} I'm your Quest Coach, and I'm excited to help you discover your Trinity - your Quest, Service, and Pledge. What's calling to you right now?`
    } else {
      return `${greeting} I'm your Delivery Coach. Let's turn that vision into reality. What's the first concrete step you need to take?`
    }
  }
  
  // Context-aware responses
  if (userContext.includes('Has Trinity: Yes') && userContext.includes('clarityScore')) {
    const clarityMatch = userContext.match(/Clarity Score:\s*(\d+)/);
    const clarity = clarityMatch ? parseInt(clarityMatch[1]) : 0;
    if (clarity < 50) {
      return "I see you've started exploring your Trinity, but there's more clarity to discover. What aspect feels most unclear to you right now?";
    }
  }
  
  // Default contextual response
  return "I hear you. Tell me more about that - what does this mean for your journey?"
}