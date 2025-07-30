'use client'

import { useEffect, useState, useCallback } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { VoiceProvider, useVoice } from '@humeai/voice-react'
import { HUME_COACHES } from '@/lib/hume-config'
import { getOrCreateSession, addMessage } from '@/lib/zep'
import { debugVoiceCoachWithZen, planTrinitySessionWithZen } from '@/lib/mcp/zen-mcp-client'

interface TrinitySession {
  sessionId: string
  zepSessionId?: string
  startTime: Date
  coach: keyof typeof HUME_COACHES
  phase: 'welcome' | 'exploring' | 'deepening' | 'complete'
  insights: string[]
}

function TrinityVoiceInterface() {
  const { connect, disconnect, status, messages, sendSessionSettings } = useVoice()
  const { user } = useUser()
  const [session, setSession] = useState<TrinitySession>({
    sessionId: Date.now().toString(),
    startTime: new Date(),
    coach: 'STORY_COACH',
    phase: 'welcome',
    insights: []
  })
  const [debugMode, setDebugMode] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  
  // Initialize Zep session
  useEffect(() => {
    const initZepSession = async () => {
      if (!user?.id) return
      
      try {
        // Get database user
        const response = await fetch('/api/user/profile')
        const userData = await response.json()
        
        if (userData.id) {
          const zepSession = await getOrCreateSession(userData.id, 'trinity-ultimate', {
            sessionId: session.sessionId,
            startTime: session.startTime.toISOString(),
            sdkVersion: 'ultimate'
          })
          
          setSession(prev => ({ ...prev, zepSessionId: zepSession.sessionId }))
          
          // Plan session with MCP if available
          if (userData.professionalMirror?.rawLinkedinData) {
            try {
              const plan = await planTrinitySessionWithZen({
                linkedinData: userData.professionalMirror.rawLinkedinData,
                goals: ['Discover Trinity', 'Clarify Quest', 'Build confidence']
              })
              
              console.log('[Trinity Ultimate] MCP Session Plan:', plan)
              
              // Store plan in Zep
              if (zepSession.sessionId) {
                await addMessage(
                  zepSession.sessionId,
                  'assistant',
                  `[MCP PLAN] ${plan.coachingStrategy}`,
                  { questions: plan.questions }
                )
              }
            } catch (error) {
              console.log('[Trinity Ultimate] MCP planning not available:', error)
            }
          }
        }
      } catch (error) {
        console.error('[Trinity Ultimate] Failed to initialize Zep:', error)
      }
    }
    
    initZepSession()
  }, [user?.id, session.sessionId, session.startTime])
  
  // Track messages in Zep
  useEffect(() => {
    const trackMessage = async () => {
      if (!session.zepSessionId || messages.length === 0) return
      
      const lastMessage = messages[messages.length - 1]
      if (lastMessage.type === 'user_message' || lastMessage.type === 'assistant_message') {
        const role = lastMessage.type === 'user_message' ? 'user' : 'assistant'
        const content = 'message' in lastMessage ? lastMessage.message?.content : ''
        
        if (content) {
          await addMessage(session.zepSessionId, role, content, {
            timestamp: new Date().toISOString(),
            phase: session.phase
          })
        }
      }
    }
    
    trackMessage()
  }, [messages, session.zepSessionId, session.phase])
  
  // Enhanced connection with user context
  const handleConnect = useCallback(async () => {
    await connect()
    
    // Send user context when connected
    if (status.value === 'connected' && user) {
      await sendSessionSettings({
        context: {
          user_id: user.id,
          user_name: user.fullName || user.firstName || 'User',
          session_id: session.sessionId,
          sdk_version: 'ultimate'
        }
      })
    }
  }, [connect, sendSessionSettings, status.value, user, session.sessionId])
  
  // Debug with MCP
  const analyzeWithMCP = async () => {
    if (!debugMode) return
    
    setIsAnalyzing(true)
    try {
      const events = messages.map(msg => ({
        type: msg.type,
        timestamp: new Date().toISOString(),
        data: msg
      }))
      
      const analysis = await debugVoiceCoachWithZen({
        events,
        errorLogs: messages.filter(m => m.type === 'error').map(m => JSON.stringify(m)),
        codeContext: 'Trinity Ultimate SDK Implementation'
      })
      
      console.log('[Trinity Ultimate] MCP Analysis:', analysis)
      
      // Store insights
      setSession(prev => ({
        ...prev,
        insights: [...prev.insights, analysis.analysis]
      }))
    } catch (error) {
      console.error('[Trinity Ultimate] MCP analysis failed:', error)
    } finally {
      setIsAnalyzing(false)
    }
  }
  
  // Extract conversation
  const conversation = messages.filter(msg => 
    msg.type === 'user_message' || msg.type === 'assistant_message'
  )
  
  const getCoachInfo = () => {
    const coach = HUME_COACHES[session.coach]
    return {
      name: coach.name,
      icon: session.coach === 'STORY_COACH' ? '📖' : 
            session.coach === 'QUEST_COACH' ? '🧭' : '🎯',
      color: session.coach === 'STORY_COACH' ? 'purple' : 
             session.coach === 'QUEST_COACH' ? 'blue' : 'green'
    }
  }
  
  const coachInfo = getCoachInfo()
  
  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-center">Trinity Ultimate</h1>
      <p className="text-center text-gray-400 mb-8">
        Native SDK + React Components + MCP Integration + Zep Memory
      </p>
      
      {/* Status Dashboard */}
      <div className="bg-gray-800 p-6 rounded-lg mb-8">
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-sm text-gray-400">Connection</p>
            <p className={`text-xl font-bold ${
              status.value === 'connected' ? 'text-green-500' : 
              status.value === 'connecting' ? 'text-yellow-500' :
              'text-red-500'
            }`}>
              {status.value}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Phase</p>
            <p className="text-xl font-bold text-blue-500">
              {session.phase}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Coach</p>
            <p className={`text-xl font-bold text-${coachInfo.color}-500`}>
              {coachInfo.icon} {coachInfo.name}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Session</p>
            <p className="text-xl font-bold text-gray-400">
              {session.sessionId.slice(-6)}
            </p>
          </div>
        </div>
      </div>
      
      {/* Controls */}
      <div className="flex justify-center gap-4 mb-8">
        {status.value !== 'connected' ? (
          <button
            onClick={handleConnect}
            disabled={status.value === 'connecting'}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50"
          >
            {status.value === 'connecting' ? 'Connecting...' : 'Start Trinity Session'}
          </button>
        ) : (
          <>
            <button
              onClick={() => disconnect()}
              className="px-6 py-3 bg-red-600 hover:bg-red-700 rounded-lg"
            >
              End Session
            </button>
            <button
              onClick={() => setDebugMode(!debugMode)}
              className={`px-6 py-3 rounded-lg ${
                debugMode ? 'bg-yellow-600 hover:bg-yellow-700' : 'bg-gray-600 hover:bg-gray-700'
              }`}
            >
              {debugMode ? 'Debug On' : 'Debug Off'}
            </button>
            {debugMode && (
              <button
                onClick={analyzeWithMCP}
                disabled={isAnalyzing}
                className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg disabled:opacity-50"
              >
                {isAnalyzing ? 'Analyzing...' : 'Analyze with MCP'}
              </button>
            )}
          </>
        )}
      </div>
      
      {/* Error Display */}
      {status.value === 'error' && (
        <div className="bg-red-900/50 border border-red-600 text-red-200 p-4 rounded mb-6">
          {status.message || 'Connection error occurred'}
        </div>
      )}
      
      {/* Transcript */}
      <div className="bg-gray-800 p-6 rounded-lg mb-6">
        <h2 className="text-xl font-semibold mb-4">Conversation</h2>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {conversation.length === 0 ? (
            <p className="text-gray-500">Say hello to begin your Trinity discovery...</p>
          ) : (
            conversation.map((msg, i) => {
              const isUser = msg.type === 'user_message'
              const content = 'message' in msg ? msg.message?.content : ''
              
              return content ? (
                <p key={i} className={isUser ? 'text-blue-400' : 'text-green-400'}>
                  {isUser ? 'You: ' : `${coachInfo.name}: `}{content}
                </p>
              ) : null
            })
          )}
        </div>
      </div>
      
      {/* Insights Panel */}
      {session.insights.length > 0 && (
        <div className="bg-gray-800 p-6 rounded-lg mb-6">
          <h2 className="text-xl font-semibold mb-4">AI Insights</h2>
          <div className="space-y-2">
            {session.insights.map((insight, i) => (
              <p key={i} className="text-sm text-gray-400">{insight}</p>
            ))}
          </div>
        </div>
      )}
      
      {/* Debug Panel */}
      {debugMode && (
        <div className="bg-gray-900 p-4 rounded-lg">
          <h3 className="text-sm font-semibold mb-2">Debug Info</h3>
          <div className="text-xs font-mono space-y-1">
            <p>Messages: {messages.length}</p>
            <p>Status: {JSON.stringify(status)}</p>
            <p>Zep Session: {session.zepSessionId || 'Not initialized'}</p>
            <p>Audio Events: {messages.filter(m => m.type === 'audio_output').length}</p>
            <p>Errors: {messages.filter(m => m.type === 'error').length}</p>
          </div>
        </div>
      )}
      
      {/* Stack Info */}
      <div className="mt-8 text-xs text-gray-500 text-center space-y-1">
        <p>✓ @humeai/voice-react Native SDK</p>
        <p>✓ Zep Memory Integration</p>
        <p>✓ MCP Multi-Model Collaboration</p>
        <p>✓ Enhanced Error Handling</p>
        <p>✓ Real-time Session Tracking</p>
      </div>
    </div>
  )
}

export default function TrinityUltimatePage() {
  const { isSignedIn } = useUser()
  const router = useRouter()
  const [accessToken, setAccessToken] = useState<string>('')
  const [loading, setLoading] = useState(true)
  
  // Redirect if not signed in
  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    }
  }, [isSignedIn, router])
  
  // Get access token
  useEffect(() => {
    const getToken = async () => {
      try {
        const response = await fetch('/api/hume/token')
        const data = await response.json()
        if (data.accessToken) {
          setAccessToken(data.accessToken)
        }
      } catch (error) {
        console.error('Failed to get access token:', error)
      } finally {
        setLoading(false)
      }
    }
    getToken()
  }, [])
  
  if (loading || !accessToken) {
    return (
      <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white p-8 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Initializing Trinity Ultimate...</h1>
          <p className="text-gray-400">Setting up all integrations...</p>
        </div>
      </main>
    )
  }
  
  // VoiceProvider configuration with all features
  const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID
  
  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white p-8">
      <VoiceProvider
        auth={{ type: 'accessToken', value: accessToken }}
        configId={configId}
        onMessage={(message) => {
          console.log('[Trinity Ultimate] Message:', message)
        }}
        onError={(error) => {
          console.error('[Trinity Ultimate] Error:', error)
        }}
        onClose={(event) => {
          console.log('[Trinity Ultimate] Connection closed:', event)
        }}
        onOpen={() => {
          console.log('[Trinity Ultimate] Connection opened')
        }}
      >
        <TrinityVoiceInterface />
      </VoiceProvider>
    </main>
  )
}