import type { ChatCompletionMessageParam } from 'openai/resources/index'

// OpenRouter configuration
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY || ''
const OPENROUTER_BASE_URL = process.env.OPENROUTER_BASE_URL || 'https://openrouter.ai/api/v1'
const PREFER_COST = process.env.OPENROUTER_PREFER_COST === 'true'
const FALLBACK_ENABLED = process.env.OPENROUTER_FALLBACK_ENABLED === 'true'

// Model preferences for different use cases
// These models are available via BYOK configuration in OpenRouter dashboard
export const OPENROUTER_MODELS = {
  // Fast, cost-effective for simple tasks
  FAST: 'anthropic/claude-3-haiku',
  FAST_ALTERNATIVE: 'google/gemini-flash-1.5',
  
  // Balanced performance and cost
  BALANCED: 'anthropic/claude-3-sonnet',
  BALANCED_ALTERNATIVE: 'google/gemini-pro-1.5',
  
  // High quality for complex reasoning
  QUALITY: 'anthropic/claude-3-opus',
  QUALITY_ALTERNATIVE: 'openai/gpt-4-turbo',
  
  // Large context window for analysis
  LARGE_CONTEXT: 'google/gemini-pro-1.5', // 1M+ context window
  
  // Code-specific models
  CODE_REVIEW: 'openai/gpt-4-turbo', // Good at code analysis
  CODE_GENERATION: 'anthropic/claude-3-sonnet', // Good at code generation
  
  // Alternative models for fallback
  FALLBACK_FAST: 'openai/gpt-3.5-turbo',
  FALLBACK_BALANCED: 'openai/gpt-4',
  FALLBACK_QUALITY: 'google/gemini-pro-1.5',
} as const

export type ModelType = keyof typeof OPENROUTER_MODELS

interface OpenRouterResponse {
  id: string
  model: string
  choices: Array<{
    message: {
      role: string
      content: string
    }
    finish_reason: string
  }>
  usage?: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
}

interface OpenRouterError {
  error: {
    message: string
    type: string
    code: string
  }
}

export interface ChatOptions {
  model?: ModelType
  temperature?: number
  max_tokens?: number
  stream?: boolean
  fallbackOnError?: boolean
}

/**
 * Send a chat completion request to OpenRouter
 */
export async function chat(
  messages: ChatCompletionMessageParam[],
  options: ChatOptions = {}
): Promise<string> {
  const {
    model = 'BALANCED',
    temperature = 0.7,
    max_tokens = 2000,
    stream = false,
    fallbackOnError = FALLBACK_ENABLED
  } = options

  const selectedModel = OPENROUTER_MODELS[model]
  
  try {
    const response = await fetch(`${OPENROUTER_BASE_URL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://quest-core.vercel.app',
        'X-Title': 'Quest Core V2',
        ...(PREFER_COST && { 'X-Prefer-Cost': 'true' })
      },
      body: JSON.stringify({
        model: selectedModel,
        messages,
        temperature,
        max_tokens,
        stream
      })
    })

    if (!response.ok) {
      const error = await response.json() as OpenRouterError
      throw new Error(error.error?.message || 'OpenRouter API error')
    }

    const data = await response.json() as OpenRouterResponse
    return data.choices[0]?.message?.content || ''
  } catch (error) {
    console.error('OpenRouter error:', error)
    
    // Try fallback model if enabled
    if (fallbackOnError && !model.startsWith('FALLBACK_')) {
      const fallbackModel = `FALLBACK_${model}` as ModelType
      console.log(`Falling back to ${OPENROUTER_MODELS[fallbackModel]}`)
      
      return chat(messages, {
        ...options,
        model: fallbackModel,
        fallbackOnError: false // Prevent infinite recursion
      })
    }
    
    throw error
  }
}

/**
 * Stream a chat completion from OpenRouter
 */
export async function streamChat(
  messages: ChatCompletionMessageParam[],
  options: ChatOptions = {},
  onChunk: (chunk: string) => void
): Promise<void> {
  const {
    model = 'BALANCED',
    temperature = 0.7,
    max_tokens = 2000
  } = options

  const selectedModel = OPENROUTER_MODELS[model]
  
  const response = await fetch(`${OPENROUTER_BASE_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': 'https://quest-core.vercel.app',
      'X-Title': 'Quest Core V2',
      ...(PREFER_COST && { 'X-Prefer-Cost': 'true' })
    },
    body: JSON.stringify({
      model: selectedModel,
      messages,
      temperature,
      max_tokens,
      stream: true
    })
  })

  if (!response.ok) {
    const error = await response.json() as OpenRouterError
    throw new Error(error.error?.message || 'OpenRouter API error')
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (data === '[DONE]') return
        
        try {
          const parsed = JSON.parse(data)
          const content = parsed.choices[0]?.delta?.content
          if (content) {
            onChunk(content)
          }
        } catch {
          // Ignore parse errors
        }
      }
    }
  }
}

/**
 * Generate structured content based on user's Trinity
 */
export async function generateTrinityContent(
  trinity: {
    pastQuest?: string | null
    pastService?: string | null
    pastPledge?: string | null
    presentQuest?: string | null
    presentService?: string | null
    presentPledge?: string | null
    futureQuest?: string | null
    futureService?: string | null
    futurePledge?: string | null
  },
  contentType: 'summary' | 'linkedin' | 'bio' | 'pitch'
): Promise<string> {
  const prompt = buildTrinityPrompt(trinity, contentType)
  
  const messages: ChatCompletionMessageParam[] = [
    {
      role: 'system',
      content: 'You are a professional storytelling expert who helps people articulate their career journey and future vision in compelling ways.'
    },
    {
      role: 'user',
      content: prompt
    }
  ]

  return chat(messages, {
    model: contentType === 'summary' ? 'FAST' : 'BALANCED',
    temperature: 0.8,
    max_tokens: contentType === 'linkedin' ? 3000 : 1500
  })
}

function buildTrinityPrompt(
  trinity: {
    pastQuest?: string | null
    pastService?: string | null
    pastPledge?: string | null
    presentQuest?: string | null
    presentService?: string | null
    presentPledge?: string | null
    futureQuest?: string | null
    futureService?: string | null
    futurePledge?: string | null
  },
  contentType: string
): string {
  const { past, present, future } = {
    past: {
      quest: trinity.pastQuest || '',
      service: trinity.pastService || '',
      pledge: trinity.pastPledge || ''
    },
    present: {
      quest: trinity.presentQuest || '',
      service: trinity.presentService || '',
      pledge: trinity.presentPledge || ''
    },
    future: {
      quest: trinity.futureQuest || '',
      service: trinity.futureService || '',
      pledge: trinity.futurePledge || ''
    }
  }

  switch (contentType) {
    case 'summary':
      return `Based on this person's Trinity evolution, create a concise 2-3 sentence summary that captures their journey and future direction:

Past Trinity:
- Quest: ${past.quest}
- Service: ${past.service}
- Pledge: ${past.pledge}

Present Trinity:
- Quest: ${present.quest}
- Service: ${present.service}
- Pledge: ${present.pledge}

Future Trinity:
- Quest: ${future.quest}
- Service: ${future.service}
- Pledge: ${future.pledge}

Write a compelling summary that shows their evolution and future vision.`

    case 'linkedin':
      return `Create a professional LinkedIn "About" section based on this Trinity evolution. Make it engaging, authentic, and focused on value to others:

Past Trinity:
- Quest: ${past.quest}
- Service: ${past.service}
- Pledge: ${past.pledge}

Present Trinity:
- Quest: ${present.quest}
- Service: ${present.service}
- Pledge: ${present.pledge}

Future Trinity:
- Quest: ${future.quest}
- Service: ${future.service}
- Pledge: ${future.pledge}

Guidelines:
- Start with a compelling hook
- Show the evolution naturally
- Focus on value and impact
- End with future vision
- Keep it professional but personable
- Maximum 2000 characters`

    case 'bio':
      return `Write a professional bio (third person) based on this Trinity:

Current Trinity:
- Quest: ${present.quest}
- Service: ${present.service}
- Pledge: ${present.pledge}

Background:
- Previous Quest: ${past.quest}

Future Vision:
- Future Quest: ${future.quest}

Create a 150-word bio suitable for speaking engagements or company websites.`

    case 'pitch':
      return `Create a 30-second elevator pitch based on this Trinity:

Current Focus:
- Quest: ${present.quest}
- Service: ${present.service}
- Pledge: ${present.pledge}

Write a conversational pitch that:
- Opens with what they do
- Explains who they serve
- Ends with their unique value
- Feels natural to say out loud`

    default:
      return 'Create a summary of this professional Trinity.'
  }
}