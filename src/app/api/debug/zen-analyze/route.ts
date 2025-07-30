import { NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { debugVoiceCoachWithZen, initializeZenMCP } from '@/lib/mcp/zen-mcp-client'
import { getMemory } from '@/lib/zep'

export async function POST(req: Request) {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const { sessionId } = await req.json()

    // Check if Zen MCP is available
    const zenAvailable = await initializeZenMCP()
    if (!zenAvailable) {
      return NextResponse.json({ 
        error: 'Zen MCP not available',
        suggestion: 'Please set up Zen MCP server as per documentation'
      }, { status: 503 })
    }

    // Get session data from Zep
    const memory = await getMemory(sessionId)
    const events = memory?.messages || []

    // Extract relevant events
    const audioEvents = events.filter(e => {
      const metadataType = e.metadata?.type
      return (typeof metadataType === 'string' && metadataType.includes('audio_')) || 
             metadataType === 'connection_event'
    })

    // Prepare detailed context for Zen MCP
    const codeContext = `
// Current WebSocket connection logic
const ws = new WebSocket(\`wss://api.hume.ai/v0/evi/chat?access_token=\${accessToken}&config_id=\${configId}\`)

// Audio handling
ws.onmessage = async (event) => {
  const data = JSON.parse(event.data)
  if (data.type === 'audio_output' && data.data) {
    // Check for duplicate using fingerprinting
    const isDuplicate = globalAudioFingerprinter.isDuplicate(data.data)
    if (!processedAudioIds.current.has(audioId) && !isDuplicate) {
      await playAudioChunk(data.data)
    }
  }
}

// Key discovery: CLM URL was pointing to old Quest Core, not V2
// This explains why user context wasn't working
`

    // Use Zen MCP to analyze with multiple models
    const result = await debugVoiceCoachWithZen({
      events: audioEvents.map(e => ({
        type: String(e.metadata?.type || 'unknown'),
        timestamp: String(e.metadata?.timestamp || ''),
        data: e.metadata
      })),
      errorLogs: [
        'Duplicate voices playing at different times',
        'Voice doesn\'t know user name',
        'CLM was pointing to wrong backend (old Quest Core)',
        'Cannot interrupt voice by speaking'
      ],
      codeContext
    })

    // Generate comprehensive analysis
    const analysis = {
      zenAnalysis: result.analysis,
      solutions: result.solutions,
      modelInsights: result.modelInsights,
      recommendations: [
        'Update CLM URL in Hume dashboard to V2 endpoint',
        'Pass user ID in WebSocket connection parameters',
        'Implement global connection singleton',
        'Add interrupt handling for user speech'
      ],
      keyDiscovery: 'CLM URL was pointing to old backend - this is likely the root cause'
    }

    return NextResponse.json(analysis)
  } catch (error) {
    console.error('Zen MCP analysis error:', error)
    return NextResponse.json({ 
      error: 'Analysis failed',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}