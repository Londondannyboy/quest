/**
 * Zen MCP Client - Enables multi-LLM collaboration for Quest Core V2
 * 
 * This client allows Claude to orchestrate between multiple AI models
 * for complex tasks like Trinity discovery, code review, and debugging.
 */

// Types will be imported when needed for actual OpenRouter integration

// Zen MCP Server configuration
const ZEN_MCP_BASE_URL = process.env.ZEN_MCP_BASE_URL || 'http://localhost:3000'
const ZEN_MCP_API_KEY = process.env.ZEN_MCP_API_KEY || ''

// Model capabilities mapping
export const MODEL_CAPABILITIES = {
  'gemini-pro': ['code-review', 'large-context', 'analysis'],
  'gpt-4': ['reasoning', 'structured-output', 'planning'],
  'claude-opus': ['creative', 'nuanced', 'complex-reasoning'],
  'ollama-local': ['fast', 'private', 'debugging']
} as const

export type ModelCapability = typeof MODEL_CAPABILITIES[keyof typeof MODEL_CAPABILITIES][number]

interface ZenMCPRequest {
  task: string
  context: string
  models?: string[]
  capabilities?: ModelCapability[]
  preserveContext?: boolean
  workflow?: 'debug' | 'review' | 'plan' | 'implement' | 'test'
}

interface ZenMCPResponse {
  results: Array<{
    model: string
    response: string
    confidence: number
    metadata?: Record<string, unknown>
  }>
  orchestration: {
    primaryModel: string
    supportingModels: string[]
    reasoning: string
  }
  context: string
}

/**
 * Execute a multi-model collaborative task
 */
export async function executeCollaborativeTask(request: ZenMCPRequest): Promise<ZenMCPResponse> {
  try {
    const response = await fetch(`${ZEN_MCP_BASE_URL}/api/orchestrate`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${ZEN_MCP_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    })

    if (!response.ok) {
      throw new Error(`Zen MCP error: ${response.statusText}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Zen MCP collaboration error:', error)
    throw error
  }
}

/**
 * Debug voice coach issues using multiple models
 */
export async function debugVoiceCoachWithZen(
  sessionData: {
    events: Array<{ type: string; timestamp: string; data?: unknown }>
    errorLogs: string[]
    codeContext: string
  }
): Promise<{
  analysis: string
  solutions: string[]
  modelInsights: Record<string, string>
}> {
  const request: ZenMCPRequest = {
    task: 'Debug Hume AI voice coach duplicate audio and interruption issues',
    context: JSON.stringify(sessionData),
    capabilities: ['debugging', 'large-context', 'analysis'],
    workflow: 'debug',
    preserveContext: true
  }

  const response = await executeCollaborativeTask(request)

  // Aggregate insights from different models
  const modelInsights: Record<string, string> = {}
  response.results.forEach(result => {
    modelInsights[result.model] = result.response
  })

  // Extract solutions from responses
  const solutions = response.results
    .flatMap(r => r.response.match(/Solution \d+:.*?(?=Solution \d+:|$)/gs) || [])
    .filter(Boolean)

  return {
    analysis: response.orchestration.reasoning,
    solutions,
    modelInsights
  }
}

/**
 * Review code using multiple models for comprehensive feedback
 */
export async function reviewCodeWithZen(
  code: string,
  files: Array<{ path: string; content: string }>,
  focusAreas: string[]
): Promise<{
  review: string
  improvements: Array<{ file: string; suggestion: string; priority: 'high' | 'medium' | 'low' }>
  consensus: string
}> {
  const request: ZenMCPRequest = {
    task: `Review code focusing on: ${focusAreas.join(', ')}`,
    context: JSON.stringify({ mainCode: code, relatedFiles: files }),
    capabilities: ['code-review', 'analysis', 'structured-output'],
    workflow: 'review'
  }

  const response = await executeCollaborativeTask(request)

  // Parse improvements from model responses
  const improvements: Array<{ file: string; suggestion: string; priority: 'high' | 'medium' | 'low' }> = []
  
  response.results.forEach(result => {
    // Extract structured improvements (this would be more sophisticated in production)
    const suggestionMatches = result.response.matchAll(/File: (.*?)\nSuggestion: (.*?)\nPriority: (high|medium|low)/g)
    for (const match of suggestionMatches) {
      improvements.push({
        file: match[1],
        suggestion: match[2],
        priority: match[3] as 'high' | 'medium' | 'low'
      })
    }
  })

  return {
    review: response.results[0].response, // Primary review
    improvements,
    consensus: response.orchestration.reasoning
  }
}

/**
 * Plan Trinity discovery session using multiple models
 */
export async function planTrinitySessionWithZen(
  userProfile: {
    linkedinData: Record<string, unknown>
    previousSessions?: string[]
    goals?: string[]
  }
): Promise<{
    sessionPlan: string
    questions: string[]
    coachingStrategy: string
    modelRecommendations: Record<string, string>
}> {
  const request: ZenMCPRequest = {
    task: 'Plan personalized Trinity discovery session',
    context: JSON.stringify(userProfile),
    capabilities: ['planning', 'creative', 'nuanced'],
    workflow: 'plan',
    models: ['claude-opus', 'gpt-4'] // Specifically request these for planning
  }

  const response = await executeCollaborativeTask(request)

  // Extract questions from responses
  const questions: string[] = []
  response.results.forEach(result => {
    const questionMatches = result.response.match(/Question \d+:.*?(?=Question \d+:|$)/gs) || []
    questions.push(...questionMatches.map(q => q.replace(/Question \d+:\s*/, '')))
  })

  const modelRecommendations: Record<string, string> = {}
  response.results.forEach(result => {
    modelRecommendations[result.model] = result.response
  })

  return {
    sessionPlan: response.results[0].response,
    questions: [...new Set(questions)], // Remove duplicates
    coachingStrategy: response.orchestration.reasoning,
    modelRecommendations
  }
}

/**
 * Test implementation with multiple models providing verification
 */
export async function testImplementationWithZen(
  implementation: string,
  testCases: string[],
  requirements: string[]
): Promise<{
  testResults: Array<{ test: string; passed: boolean; feedback: string }>
  overallAssessment: string
  modelAgreement: number // 0-1 score
}> {
  const request: ZenMCPRequest = {
    task: 'Test and verify implementation against requirements',
    context: JSON.stringify({ implementation, testCases, requirements }),
    workflow: 'test',
    preserveContext: true
  }

  const response = await executeCollaborativeTask(request)

  // Parse test results
  const testResults: Array<{ test: string; passed: boolean; feedback: string }> = []
  testCases.forEach((test, index) => {
    const passed = response.results.every(r => 
      r.response.toLowerCase().includes(`test ${index + 1}: pass`)
    )
    testResults.push({
      test,
      passed,
      feedback: response.results[0].response // Primary feedback
    })
  })

  // Calculate model agreement
  const modelAgreement = response.results.filter(r => r.confidence > 0.8).length / response.results.length

  return {
    testResults,
    overallAssessment: response.orchestration.reasoning,
    modelAgreement
  }
}

/**
 * Initialize Zen MCP connection
 */
export async function initializeZenMCP(): Promise<boolean> {
  try {
    const response = await fetch(`${ZEN_MCP_BASE_URL}/api/health`, {
      headers: {
        'Authorization': `Bearer ${ZEN_MCP_API_KEY}`
      }
    })
    
    return response.ok
  } catch (error) {
    console.error('Failed to connect to Zen MCP Server:', error)
    return false
  }
}