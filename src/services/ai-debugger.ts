import { chat } from '@/lib/openrouter'
import { getMemory } from '@/lib/zep'
import { debugVoiceCoachWithZen, initializeZenMCP } from '@/lib/mcp/zen-mcp-client'
import type { ChatCompletionMessageParam } from 'openai/resources/index'

interface DebugContext {
  sessionId: string
  issue: string
  codeSnippets?: string[]
  errorLogs?: string[]
}

interface DebugResult {
  analysis: string
  suggestions: string[]
  codeChanges?: string[]
  confidence: number
}

// Add Gemini model for large context debugging
// const GEMINI_MODEL = 'google/gemini-pro-1.5' // TODO: Enable when adding Gemini support

/**
 * Use AI to debug voice coach issues by analyzing session data
 */
export async function debugVoiceCoachSession(context: DebugContext): Promise<DebugResult> {
  try {
    // Get session memory from Zep
    const memory = await getMemory(context.sessionId)
    
    // Extract audio events from memory
    const audioEvents = memory?.messages?.filter(m => {
      const type = m.metadata?.type
      return type && typeof type === 'string' && (
        type.includes('audio_') || 
        type === 'connection_event'
      )
    }) || []
    
    // Check if Zen MCP is available
    const zenAvailable = await initializeZenMCP()
    
    if (zenAvailable) {
      // Use Zen MCP for multi-model debugging
      console.log('Using Zen MCP for collaborative debugging')
      
      const zenResult = await debugVoiceCoachWithZen({
        events: audioEvents.map(e => ({
          type: String(e.metadata?.type || 'unknown'),
          timestamp: String(e.metadata?.timestamp || ''),
          data: e.metadata
        })),
        errorLogs: context.errorLogs || [],
        codeContext: context.codeSnippets?.join('\n\n') || ''
      })
      
      return {
        analysis: zenResult.analysis,
        suggestions: zenResult.solutions,
        codeChanges: [], // Extract from model insights if needed
        confidence: 0.9 // Higher confidence with multi-model consensus
      }
    }
    
    // Fallback to single model if Zen MCP not available
    console.log('Zen MCP not available, using OpenRouter')
    
    // Build context for debugging
    const messages: ChatCompletionMessageParam[] = [
      {
        role: 'system',
        content: `You are an expert debugging assistant specializing in WebSocket audio streaming applications and Hume AI EVI integration. Analyze the provided session data to identify issues with duplicate audio streams and interruption handling.`
      },
      {
        role: 'user',
        content: buildDebugPrompt(context, audioEvents)
      }
    ]
    
    // Use Gemini for large context window analysis
    const analysis = await chat(messages, {
      model: 'LARGE_CONTEXT', // Uses Gemini Pro 1.5 with 1M+ context
      temperature: 0.3,
      max_tokens: 3000
    })
    
    // Parse the analysis
    return parseDebugResult(analysis)
  } catch (error) {
    console.error('AI debugging error:', error)
    return {
      analysis: 'Failed to analyze session',
      suggestions: ['Check Zep connection', 'Verify session data exists'],
      confidence: 0
    }
  }
}

/**
 * Analyze code patterns to identify potential issues
 */
export async function analyzeCodeForIssues(
  codeFiles: { path: string; content: string }[],
  knownIssue: string
): Promise<DebugResult> {
  const messages: ChatCompletionMessageParam[] = [
    {
      role: 'system',
      content: `You are a senior software engineer expert in React, WebSockets, and audio streaming. Analyze the code for issues related to: ${knownIssue}`
    },
    {
      role: 'user',
      content: `Known issue: ${knownIssue}\n\nCode files:\n${codeFiles.map(f => `\n=== ${f.path} ===\n${f.content}`).join('\n')}`
    }
  ]
  
  const analysis = await chat(messages, {
    model: 'CODE_REVIEW', // Uses GPT-4 Turbo for code analysis
    temperature: 0.2,
    max_tokens: 4000
  })
  
  return parseDebugResult(analysis)
}

/**
 * Compare with successful implementation to find differences
 */
export async function compareImplementations(
  currentCode: string,
  successfulCode: string,
  focusArea: string
): Promise<DebugResult> {
  const messages: ChatCompletionMessageParam[] = [
    {
      role: 'system',
      content: 'You are an expert at comparing code implementations to identify critical differences that could cause issues.'
    },
    {
      role: 'user',
      content: `Compare these two implementations focusing on ${focusArea}:

=== CURRENT (PROBLEMATIC) ===
${currentCode}

=== SUCCESSFUL REFERENCE ===
${successfulCode}

Identify key differences that could cause:
1. Duplicate audio streams
2. No interruption capability
3. User context not being passed

Provide specific code changes needed.`
    }
  ]
  
  const analysis = await chat(messages, {
    model: 'QUALITY',
    temperature: 0.2,
    max_tokens: 3000
  })
  
  return parseDebugResult(analysis)
}

function buildDebugPrompt(context: DebugContext, audioEvents: Array<{ content?: string, metadata?: Record<string, unknown> }>): string {
  return `Debug this voice coach session issue:

ISSUE: ${context.issue}

SESSION EVENTS (${audioEvents.length} total):
${audioEvents.map(e => `- ${e.metadata?.timestamp}: ${e.content} (${JSON.stringify(e.metadata)})`).join('\n')}

${context.codeSnippets ? `\nCODE SNIPPETS:\n${context.codeSnippets.join('\n\n')}` : ''}

${context.errorLogs ? `\nERROR LOGS:\n${context.errorLogs.join('\n')}` : ''}

Analyze the pattern of events and identify:
1. Why duplicate audio might be occurring
2. Missing or incorrect event handling
3. Potential race conditions
4. Suggested fixes with specific code

Focus on:
- WebSocket connection management
- Audio chunk processing
- Event deduplication
- User context passing`
}

function parseDebugResult(rawAnalysis: string): DebugResult {
  // Simple parsing - in production would use structured output
  const lines = rawAnalysis.split('\n')
  const analysis = lines[0] || 'No analysis provided'
  
  const suggestions: string[] = []
  const codeChanges: string[] = []
  let inCodeBlock = false
  let currentCode = ''
  
  for (const line of lines) {
    if (line.startsWith('- ') || line.match(/^\d+\./)) {
      suggestions.push(line.replace(/^[-\d]+\.?\s*/, ''))
    } else if (line.includes('```')) {
      if (inCodeBlock && currentCode) {
        codeChanges.push(currentCode.trim())
        currentCode = ''
      }
      inCodeBlock = !inCodeBlock
    } else if (inCodeBlock) {
      currentCode += line + '\n'
    }
  }
  
  return {
    analysis,
    suggestions: suggestions.filter(s => s.length > 0),
    codeChanges: codeChanges.filter(c => c.length > 0),
    confidence: 0.8 // Would calculate based on analysis
  }
}

/**
 * Generate a comprehensive debug report
 */
export async function generateDebugReport(sessionId: string): Promise<string> {
  const memory = await getMemory(sessionId)
  const events = memory?.messages || []
  
  // Group events by type
  const eventGroups: Record<string, Array<{ content?: string, metadata?: Record<string, unknown> }>> = {}
  events.forEach(event => {
    const type = String(event.metadata?.type || 'unknown')
    if (!eventGroups[type]) eventGroups[type] = []
    eventGroups[type].push(event)
  })
  
  // Analyze patterns
  const audioOutputCount = eventGroups['audio_output']?.length || 0
  const audioPlayedCount = eventGroups['audio_played']?.length || 0
  const audioDuplicateCount = eventGroups['audio_duplicate']?.length || 0
  
  const report = `
# Voice Coach Debug Report
Session: ${sessionId}

## Event Summary
- Total Events: ${events.length}
- Audio Output Events: ${audioOutputCount}
- Audio Played: ${audioPlayedCount}
- Duplicates Detected: ${audioDuplicateCount}
- Duplicate Rate: ${audioOutputCount > 0 ? ((audioDuplicateCount / audioOutputCount) * 100).toFixed(1) : 0}%

## Event Timeline
${events.slice(-20).map(e => `${e.metadata?.timestamp}: ${e.content}`).join('\n')}

## Potential Issues
${audioDuplicateCount > 0 ? '- High duplicate audio rate detected' : ''}
${audioPlayedCount < audioOutputCount * 0.8 ? '- Many audio chunks not being played' : ''}
${eventGroups['connection_event']?.length > 1 ? '- Multiple connection events detected' : ''}
`
  
  return report
}