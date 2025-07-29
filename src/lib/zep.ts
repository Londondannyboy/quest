/* eslint-disable @typescript-eslint/no-explicit-any */
import { Zep } from '@getzep/zep-js'
import { Message, Memory, Session } from '@getzep/zep-js/api'

// Initialize Zep client
const ZEP_API_KEY = process.env.ZEP_API_KEY || ''
const ZEP_BASE_URL = process.env.ZEP_BASE_URL || 'https://api.getzep.com'

let zepClient: Zep | null = null

function getZepClient(): Zep {
  if (!zepClient) {
    if (!ZEP_API_KEY) {
      throw new Error('ZEP_API_KEY not configured')
    }
    zepClient = new Zep({
      apiKey: ZEP_API_KEY,
      baseUrl: ZEP_BASE_URL
    })
  }
  return zepClient
}

/**
 * Create or get a session for a user's coaching conversation
 */
export async function getOrCreateSession(
  userId: string,
  sessionType: 'trinity' | 'quest' | 'coaching',
  metadata?: Record<string, unknown>
): Promise<Session> {
  const client = getZepClient()
  const sessionId = `${userId}-${sessionType}`
  
  try {
    // Try to get existing session
    const session = await client.memory.getSession({ sessionId })
    return session
  } catch {
    // Create new session if doesn't exist
    const session = await client.memory.addSession({
      sessionId,
      userId,
      metadata: {
        sessionType,
        createdAt: new Date().toISOString(),
        ...metadata
      }
    })
    return session
  }
}

/**
 * Add a message to the conversation memory
 */
export async function addMessage(
  sessionId: string,
  role: 'user' | 'assistant',
  content: string,
  metadata?: Record<string, unknown>
): Promise<void> {
  const client = getZepClient()
  
  const message: Message = {
    role,
    content,
    roleType: role,
    metadata
  }
  
  await client.memory.add({
    sessionId,
    messages: [message]
  })
}

/**
 * Get conversation memory with context
 */
export async function getMemory(sessionId: string): Promise<Memory | null> {
  const client = getZepClient()
  
  try {
    const memory = await client.memory.get({ sessionId })
    return memory
  } catch (error) {
    console.error('Failed to get memory:', error)
    return null
  }
}

/**
 * Search memories across all user sessions
 */
export async function searchMemories(
  userId: string,
  query: string,
  limit: number = 5
): Promise<any[]> {
  const client = getZepClient()
  
  try {
    const results = await client.memory.searchSessions({
      text: query,
      userId,
      limit
    })
    return results
  } catch (error) {
    console.error('Failed to search memories:', error)
    return []
  }
}

/**
 * Update session metadata (e.g., Trinity progress)
 */
export async function updateSessionMetadata(
  sessionId: string,
  metadata: Record<string, any>
): Promise<void> {
  const client = getZepClient()
  
  try {
    await client.memory.updateSession({
      sessionId,
      metadata
    })
  } catch (error) {
    console.error('Failed to update session metadata:', error)
  }
}

/**
 * Extract facts and insights from conversation
 */
export async function extractInsights(sessionId: string): Promise<{
  facts: unknown[]
  summary: string
  metadata: Record<string, unknown>
}> {
  const client = getZepClient()
  
  try {
    const memory = await client.memory.get({ sessionId })
    
    // Zep automatically extracts facts and summaries
    return {
      facts: memory.facts || [],
      summary: memory.summary || '',
      metadata: memory.metadata || {}
    }
  } catch (error) {
    console.error('Failed to extract insights:', error)
    return { facts: [], summary: '', metadata: {} }
  }
}

/**
 * Store Trinity evolution in memory
 */
export async function storeTrinityEvolution(
  userId: string,
  trinity: {
    past?: { quest?: string; service?: string; pledge?: string }
    present?: { quest?: string; service?: string; pledge?: string }
    future?: { quest?: string; service?: string; pledge?: string }
    clarityScore?: number
  }
): Promise<void> {
  const sessionId = `${userId}-trinity`
  
  // Update session metadata with Trinity data
  await updateSessionMetadata(sessionId, {
    trinityData: trinity,
    lastUpdated: new Date().toISOString(),
    clarityScore: trinity.clarityScore || 0
  })
  
  // Add a system message documenting the Trinity
  const trinityMessage = `Trinity Evolution Update:
Past: ${trinity.past?.quest || 'Not defined'} | ${trinity.past?.service || 'Not defined'} | ${trinity.past?.pledge || 'Not defined'}
Present: ${trinity.present?.quest || 'Not defined'} | ${trinity.present?.service || 'Not defined'} | ${trinity.present?.pledge || 'Not defined'}
Future: ${trinity.future?.quest || 'Not defined'} | ${trinity.future?.service || 'Not defined'} | ${trinity.future?.pledge || 'Not defined'}
Clarity Score: ${trinity.clarityScore || 0}%`

  await addMessage(sessionId, 'assistant', trinityMessage, {
    type: 'trinity_update',
    timestamp: new Date().toISOString()
  })
}

/**
 * Get user's complete journey context
 */
export async function getUserJourneyContext(userId: string): Promise<string> {
  // Search for key moments across all sessions
  const keyMoments = await searchMemories(userId, 'transition change decision important', 10)
  const trinitySession = await getMemory(`${userId}-trinity`)
  
  let context = 'User Journey Context:\n'
  
  if (trinitySession?.metadata?.trinityData) {
    const trinity = trinitySession.metadata.trinityData
    context += `\nCurrent Trinity (${trinity.clarityScore}% clarity):\n`
    context += `- Quest: ${trinity.present?.quest || 'Exploring'}\n`
    context += `- Service: ${trinity.present?.service || 'Discovering'}\n`
    context += `- Pledge: ${trinity.present?.pledge || 'Forming'}\n`
  }
  
  if (keyMoments.length > 0) {
    context += '\nKey Journey Moments:\n'
    keyMoments.forEach((moment, i) => {
      context += `${i + 1}. ${moment.content?.substring(0, 100)}...\n`
    })
  }
  
  return context
}