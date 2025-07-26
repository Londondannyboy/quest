import OpenAI from 'openai'
import { prisma } from '@/lib/prisma'
import { CoachType } from '@prisma/client'

// Initialize OpenRouter client
const openai = new OpenAI({
  apiKey: process.env.OPENROUTER_API_KEY,
  baseURL: process.env.OPENROUTER_BASE_URL || 'https://openrouter.ai/api/v1',
  defaultHeaders: {
    'HTTP-Referer': process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
    'X-Title': 'Quest Core V2',
  },
})

// Model selection based on coach type and cost optimization
const modelSelection = {
  storyCoach: 'anthropic/claude-3-sonnet',     // Empathetic ($3/M)
  questCoach: 'openai/gpt-4-turbo',           // Insightful ($10/M)
  deliveryCoach: 'moonshotai/kimi-k2',        // Direct ($0.15/M)
  skillsAnalysis: 'moonshotai/kimi-k2:free',  // Zero cost
  patternRecognition: 'google/gemini-pro',     // Large context ($0.5/M)
  fallback: 'openai/gpt-3.5-turbo'            // Budget option ($0.5/M)
}

// Coach personalities and prompts
const coachPersonalities = {
  STORY_COACH: {
    model: modelSelection.storyCoach,
    systemPrompt: `You are a warm, empathetic Story Coach (biographer) for Quest Core V2.
    Your voice is female, patient, and curious. You help users discover their authentic professional story.
    
    Key behaviors:
    - Ask open-ended questions about transitions and choices
    - Notice patterns without judging
    - Draw out emotions and motivations
    - Use phrases like "Tell me about...", "What drew you to...", "I notice..."
    - Be warm but professional
    - Focus on the WHY behind career moves
    
    Remember: You're helping them see their story clearly, not telling them what it means.`,
  },
  QUEST_COACH: {
    model: modelSelection.questCoach,
    systemPrompt: `You are an energetic Quest Coach (pattern seeker) for Quest Core V2.
    Your voice is male, insightful, and forward-looking. You help users recognize their Trinity evolution.
    
    Key behaviors:
    - Connect dots across their timeline
    - Highlight evolution from past to present to future
    - Use phrases like "I see a pattern...", "Your Trinity is emerging...", "What if..."
    - Be enthusiastic about their potential
    - Focus on transformation, not just information
    
    Remember: You're revealing what's already there, helping them see their evolution.`,
  },
  DELIVERY_COACH: {
    model: modelSelection.deliveryCoach,
    systemPrompt: `You are a firm, achievement-focused Delivery Coach for Quest Core V2.
    Your voice is direct and results-oriented. You help users turn insights into action.
    
    Key behaviors:
    - Be direct and challenging (supportively)
    - Focus on commitment and readiness
    - Use phrases like "Let's make this real...", "What's your first step?", "Are you ready?"
    - Push for specificity
    - Don't accept vague answers
    
    Remember: You're the final gate before Quest activation. Only 30% should pass.`,
  },
}

// Route message to appropriate model with fallback
async function routeWithFallback(
  messages: OpenAI.Chat.ChatCompletionMessageParam[],
  model: string,
  fallbackModel: string = modelSelection.fallback
): Promise<OpenAI.Chat.ChatCompletion> {
  try {
    return await openai.chat.completions.create({
      model,
      messages,
      temperature: 0.7,
      max_tokens: 500,
    })
  } catch (error) {
    console.error(`Primary model ${model} failed, using fallback`, error)
    return await openai.chat.completions.create({
      model: fallbackModel,
      messages,
      temperature: 0.7,
      max_tokens: 500,
    })
  }
}

// Main coaching interface
export async function getCoachResponse({
  userId,
  coachType,
  message,
  context,
}: {
  userId: string
  coachType: CoachType
  message: string
  context?: any
}) {
  const coach = coachPersonalities[coachType]
  
  // Build messages array
  const messages: OpenAI.Chat.ChatCompletionMessageParam[] = [
    {
      role: 'system',
      content: coach.systemPrompt,
    },
  ]

  // Add context if provided
  if (context) {
    messages.push({
      role: 'system',
      content: `Context about the user's journey so far: ${JSON.stringify(context)}`,
    })
  }

  // Add user message
  messages.push({
    role: 'user',
    content: message,
  })

  // Get response
  const startTime = Date.now()
  const completion = await routeWithFallback(messages, coach.model)
  const endTime = Date.now()

  const response = completion.choices[0].message.content || ''
  const tokens = completion.usage?.total_tokens || 0
  
  // Calculate approximate cost (simplified)
  const costPerMillion = getModelCost(coach.model)
  const costUSD = (tokens / 1_000_000) * costPerMillion

  // Record coaching session
  await prisma.coachingSession.create({
    data: {
      userId,
      coachType,
      modelUsed: coach.model,
      tokenCount: tokens,
      costUSD,
      messages: { user: message, assistant: response },
      endedAt: new Date(),
    },
  })

  return {
    response,
    responseTime: endTime - startTime,
    tokensUsed: tokens,
    cost: costUSD,
  }
}

// Get model cost per million tokens (simplified)
function getModelCost(model: string): number {
  const costs: Record<string, number> = {
    'anthropic/claude-3-sonnet': 3,
    'openai/gpt-4-turbo': 10,
    'moonshotai/kimi-k2': 0.15,
    'moonshotai/kimi-k2:free': 0,
    'google/gemini-pro': 0.5,
    'openai/gpt-3.5-turbo': 0.5,
  }
  return costs[model] || 1
}

// Analyze patterns in user's story for Trinity recognition
export async function analyzeStoryPatterns(storyData: any) {
  const messages: OpenAI.Chat.ChatCompletionMessageParam[] = [
    {
      role: 'system',
      content: `Analyze this professional story and identify patterns for Trinity (Quest/Service/Pledge) evolution.
      Look for:
      - What drove them in the past
      - What drives them now
      - What might drive them in the future
      - How they've served others
      - What commitments they've made
      
      Return a structured analysis with past, present, and future insights.`,
    },
    {
      role: 'user',
      content: JSON.stringify(storyData),
    },
  ]

  const completion = await routeWithFallback(
    messages,
    modelSelection.patternRecognition
  )

  return completion.choices[0].message.content
}

// Calculate readiness based on coaching interactions
export async function calculateQuestReadiness(userId: string) {
  // Get user's story sessions
  const storySessions = await prisma.storySession.findMany({
    where: { userId },
    orderBy: { createdAt: 'desc' },
  })

  const latestSession = storySessions[0]
  if (!latestSession) {
    return { score: 0, outcome: 'NOT_YET' as const }
  }

  const storyDepth = latestSession.storyDepth || 0
  const trinityClarity = latestSession.trinityClarity || 0
  const futureOrientation = latestSession.futureOrientation || 0

  const score = 
    (storyDepth * 0.3) +
    (trinityClarity * 0.4) +
    (futureOrientation * 0.3)

  let outcome: 'QUEST_READY' | 'PREPARING' | 'NOT_YET'
  
  if (score >= 70) {
    outcome = 'QUEST_READY'
  } else if (score >= 40) {
    outcome = 'PREPARING'
  } else {
    outcome = 'NOT_YET'
  }

  return { score, outcome }
}