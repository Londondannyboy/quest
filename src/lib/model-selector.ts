import { ModelType, OPENROUTER_MODELS } from './openrouter'

/**
 * Intelligent model selection based on task requirements
 * Uses models configured via BYOK in OpenRouter dashboard
 */

interface TaskContext {
  type: 'chat' | 'analysis' | 'code' | 'creative' | 'debug'
  contextSize?: number
  needsReasoning?: boolean
  costSensitive?: boolean
  requiresSpeed?: boolean
}

/**
 * Select the best model for a given task
 */
export function selectModel(context: TaskContext): ModelType {
  const { type, contextSize = 0, needsReasoning = false, costSensitive = true, requiresSpeed = false } = context

  switch (type) {
    case 'debug':
      // For debugging, we need large context and good reasoning
      if (contextSize > 32000) {
        return 'LARGE_CONTEXT' // Gemini Pro 1.5 (1M+ context)
      }
      return needsReasoning ? 'QUALITY' : 'BALANCED'

    case 'code':
      // For code tasks, use specialized models
      return requiresSpeed ? 'CODE_GENERATION' : 'CODE_REVIEW'

    case 'analysis':
      // For analysis, balance context size and quality
      if (contextSize > 100000) {
        return 'LARGE_CONTEXT' // Gemini Pro 1.5
      }
      return costSensitive ? 'BALANCED_ALTERNATIVE' : 'QUALITY'

    case 'creative':
      // For creative tasks, prefer Claude
      return costSensitive ? 'BALANCED' : 'QUALITY'

    case 'chat':
    default:
      // For general chat, optimize for speed and cost
      if (requiresSpeed) {
        return costSensitive ? 'FAST' : 'FAST_ALTERNATIVE'
      }
      return 'BALANCED'
  }
}

/**
 * Get model capabilities
 */
export function getModelCapabilities(model: ModelType): {
  contextWindow: number
  strengths: string[]
  costTier: 'low' | 'medium' | 'high'
} {
  const capabilities: Record<string, ReturnType<typeof getModelCapabilities>> = {
    // Claude models
    'anthropic/claude-3-haiku': {
      contextWindow: 200000,
      strengths: ['speed', 'cost-effective', 'general-purpose'],
      costTier: 'low'
    },
    'anthropic/claude-3-sonnet': {
      contextWindow: 200000,
      strengths: ['balanced', 'code-generation', 'creative'],
      costTier: 'medium'
    },
    'anthropic/claude-3-opus': {
      contextWindow: 200000,
      strengths: ['reasoning', 'complex-tasks', 'nuanced'],
      costTier: 'high'
    },
    
    // Gemini models
    'google/gemini-flash-1.5': {
      contextWindow: 1000000,
      strengths: ['ultra-fast', 'large-context', 'multimodal'],
      costTier: 'low'
    },
    'google/gemini-pro-1.5': {
      contextWindow: 2000000,
      strengths: ['massive-context', 'analysis', 'reasoning'],
      costTier: 'medium'
    },
    
    // OpenAI models
    'openai/gpt-3.5-turbo': {
      contextWindow: 16385,
      strengths: ['fast', 'general-purpose', 'cost-effective'],
      costTier: 'low'
    },
    'openai/gpt-4': {
      contextWindow: 8192,
      strengths: ['reasoning', 'accuracy', 'consistency'],
      costTier: 'high'
    },
    'openai/gpt-4-turbo': {
      contextWindow: 128000,
      strengths: ['code-review', 'reasoning', 'large-context'],
      costTier: 'high'
    }
  }

  const modelId = OPENROUTER_MODELS[model as keyof typeof OPENROUTER_MODELS]
  return capabilities[modelId] || {
    contextWindow: 4096,
    strengths: ['general-purpose'],
    costTier: 'medium'
  }
}

/**
 * Estimate token count (rough approximation)
 */
export function estimateTokens(text: string): number {
  // Rough estimate: ~4 characters per token
  return Math.ceil(text.length / 4)
}

/**
 * Select model with automatic fallback based on context size
 */
export function selectModelWithFallback(
  text: string,
  taskType: TaskContext['type'] = 'chat'
): ModelType {
  const estimatedTokens = estimateTokens(text)
  
  // If context is very large, use Gemini
  if (estimatedTokens > 100000) {
    return 'LARGE_CONTEXT'
  }
  
  // Otherwise, use task-based selection
  return selectModel({
    type: taskType,
    contextSize: estimatedTokens,
    needsReasoning: taskType === 'analysis' || taskType === 'debug',
    costSensitive: true,
    requiresSpeed: taskType === 'chat'
  })
}