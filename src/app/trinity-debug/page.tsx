'use client'

import { useState, useEffect, useRef } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'

interface DebugEvent {
  timestamp: string
  type: 'connection' | 'audio' | 'message' | 'error' | 'clm'
  source: 'websocket' | 'sse' | 'clm' | 'unknown'
  details: string
  metadata?: Record<string, unknown>
}

export default function TrinityDebugPage() {
  const { isSignedIn, user } = useUser()
  const router = useRouter()
  const [events, setEvents] = useState<DebugEvent[]>([])
  const [connectionCount, setConnectionCount] = useState(0)
  const [audioChunkCount, setAudioChunkCount] = useState(0)
  const [wsState, setWsState] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected')
  const [clmCalls, setClmCalls] = useState(0)
  const [accessToken, setAccessToken] = useState('')
  
  const wsRef = useRef<WebSocket | null>(null)
  const audioSourcesRef = useRef<Map<string, number>>(new Map())
  
  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    }
  }, [isSignedIn, router])

  const logEvent = (type: DebugEvent['type'], source: DebugEvent['source'], details: string, metadata?: Record<string, unknown>) => {
    const event: DebugEvent = {
      timestamp: new Date().toISOString(),
      type,
      source,
      details,
      metadata
    }
    setEvents(prev => [...prev, event])
    console.log('[Trinity Debug]', event)
  }

  const getAccessToken = async () => {
    try {
      const response = await fetch('/api/hume/token')
      const data = await response.json()
      if (data.accessToken) {
        setAccessToken(data.accessToken)
        logEvent('connection', 'unknown', 'Access token received')
      }
    } catch (error) {
      logEvent('error', 'unknown', `Failed to get access token: ${error}`)
    }
  }

  const connectWebSocket = () => {
    if (!accessToken) {
      logEvent('error', 'websocket', 'No access token available')
      return
    }

    // Track connection attempt
    setConnectionCount(prev => prev + 1)
    logEvent('connection', 'websocket', `Connection attempt #${connectionCount + 1}`)
    
    const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID
    
    // Try to include user ID in the connection
    const params = new URLSearchParams({
      access_token: accessToken,
      config_id: configId || ''
    })
    
    // Add user ID if available
    if (user?.id) {
      params.append('user_id', user.id)
      params.append('user_name', user.fullName || user.firstName || 'User')
    }
    
    const ws = new WebSocket(`wss://api.hume.ai/v0/evi/chat?${params}`)
    
    ws.onopen = () => {
      setWsState('connected')
      logEvent('connection', 'websocket', 'WebSocket connected', {
        readyState: ws.readyState,
        url: ws.url,
        userId: user?.id
      })
      
      // Send user context
      if (user) {
        ws.send(JSON.stringify({
          type: 'session_settings',
          session_settings: {
            context: {
              user_id: user.id,
              user_name: user.fullName || user.firstName || 'User',
              user_email: user.emailAddresses?.[0]?.emailAddress
            }
          }
        }))
        logEvent('message', 'websocket', 'Sent user context')
      }
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      logEvent('message', 'websocket', `Received: ${data.type}`, data)
      
      if (data.type === 'audio_output' && data.data) {
        setAudioChunkCount(prev => prev + 1)
        
        // Track audio source
        const audioId = data.id || 'unknown'
        const currentCount = audioSourcesRef.current.get(audioId) || 0
        audioSourcesRef.current.set(audioId, currentCount + 1)
        
        logEvent('audio', 'websocket', `Audio chunk #${audioChunkCount + 1}`, {
          audioId,
          chunkSize: data.data.length,
          sourceCount: currentCount + 1
        })
      }
      
      // Check if CLM is mentioned
      if (data.custom_llm_url || data.llm_url) {
        setClmCalls(prev => prev + 1)
        logEvent('clm', 'websocket', 'CLM endpoint referenced', {
          url: data.custom_llm_url || data.llm_url
        })
      }
    }
    
    ws.onerror = (error) => {
      logEvent('error', 'websocket', 'WebSocket error', { error })
      setWsState('disconnected')
    }
    
    ws.onclose = (event) => {
      logEvent('connection', 'websocket', 'WebSocket closed', {
        code: event.code,
        reason: event.reason
      })
      setWsState('disconnected')
    }
    
    wsRef.current = ws
  }

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }

  const testCLMEndpoint = async () => {
    try {
      const response = await fetch('/api/hume-clm-sse/chat/completions', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-User-Id': user?.id || '',
          'X-Hume-User-Id': user?.id || ''
        },
        body: JSON.stringify({
          messages: [
            { role: 'system', content: 'You are a helpful assistant.' },
            { role: 'user', content: 'Test message' }
          ]
        })
      })
      
      const reader = response.body?.getReader()
      if (reader) {
        logEvent('clm', 'sse', 'CLM endpoint called successfully', {
          status: response.status,
          headers: Object.fromEntries(response.headers.entries())
        })
        
        // Read a bit of the stream
        const { value } = await reader.read()
        const text = new TextDecoder().decode(value)
        logEvent('clm', 'sse', 'CLM response sample', { sample: text.substring(0, 200) })
      }
    } catch (error) {
      logEvent('error', 'clm', `CLM test failed: ${error}`)
    }
  }

  const clearEvents = () => {
    setEvents([])
    setConnectionCount(0)
    setAudioChunkCount(0)
    setClmCalls(0)
    audioSourcesRef.current.clear()
  }

  return (
    <main className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Trinity Voice Coach Debug</h1>
        
        {/* Status Overview */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-800 p-4 rounded">
            <h3 className="text-sm text-gray-400">WebSocket Status</h3>
            <p className={`text-2xl font-bold ${
              wsState === 'connected' ? 'text-green-500' : 
              wsState === 'connecting' ? 'text-yellow-500' : 'text-red-500'
            }`}>{wsState}</p>
          </div>
          
          <div className="bg-gray-800 p-4 rounded">
            <h3 className="text-sm text-gray-400">Connection Attempts</h3>
            <p className="text-2xl font-bold text-blue-500">{connectionCount}</p>
          </div>
          
          <div className="bg-gray-800 p-4 rounded">
            <h3 className="text-sm text-gray-400">Audio Chunks</h3>
            <p className="text-2xl font-bold text-purple-500">{audioChunkCount}</p>
          </div>
          
          <div className="bg-gray-800 p-4 rounded">
            <h3 className="text-sm text-gray-400">CLM Calls</h3>
            <p className="text-2xl font-bold text-orange-500">{clmCalls}</p>
          </div>
        </div>
        
        {/* User Info */}
        <div className="bg-gray-800 p-4 rounded mb-8">
          <h3 className="text-lg font-semibold mb-2">User Context</h3>
          <div className="text-sm space-y-1">
            <p>User ID: <span className="text-blue-400">{user?.id || 'Not available'}</span></p>
            <p>Name: <span className="text-blue-400">{user?.fullName || user?.firstName || 'Not available'}</span></p>
            <p>Email: <span className="text-blue-400">{user?.emailAddresses?.[0]?.emailAddress || 'Not available'}</span></p>
          </div>
        </div>
        
        {/* Controls */}
        <div className="flex gap-4 mb-8">
          <button
            onClick={getAccessToken}
            disabled={!!accessToken}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded disabled:opacity-50"
          >
            Get Token
          </button>
          
          <button
            onClick={connectWebSocket}
            disabled={!accessToken || wsState !== 'disconnected'}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded disabled:opacity-50"
          >
            Connect WS
          </button>
          
          <button
            onClick={disconnect}
            disabled={wsState !== 'connected'}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded disabled:opacity-50"
          >
            Disconnect
          </button>
          
          <button
            onClick={testCLMEndpoint}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded"
          >
            Test CLM
          </button>
          
          <button
            onClick={clearEvents}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded"
          >
            Clear Log
          </button>
        </div>
        
        {/* Audio Sources */}
        <div className="bg-gray-800 p-4 rounded mb-8">
          <h3 className="text-lg font-semibold mb-2">Audio Sources</h3>
          <div className="space-y-1">
            {Array.from(audioSourcesRef.current.entries()).map(([id, count]) => (
              <p key={id} className="text-sm">
                Source {id}: <span className="text-yellow-400">{count} chunks</span>
              </p>
            ))}
            {audioSourcesRef.current.size === 0 && (
              <p className="text-sm text-gray-500">No audio sources detected</p>
            )}
          </div>
        </div>
        
        {/* Event Log */}
        <div className="bg-gray-800 p-4 rounded">
          <h3 className="text-lg font-semibold mb-4">Event Log</h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {events.map((event, i) => (
              <div key={i} className="text-xs font-mono">
                <span className="text-gray-500">{event.timestamp.split('T')[1]}</span>
                <span className={`ml-2 ${
                  event.type === 'error' ? 'text-red-400' :
                  event.type === 'connection' ? 'text-green-400' :
                  event.type === 'audio' ? 'text-purple-400' :
                  event.type === 'clm' ? 'text-orange-400' :
                  'text-blue-400'
                }`}>[{event.type.toUpperCase()}]</span>
                <span className="ml-2 text-gray-400">{event.source}:</span>
                <span className="ml-2">{event.details}</span>
                {event.metadata && (
                  <div className="ml-4 text-gray-600">{JSON.stringify(event.metadata)}</div>
                )}
              </div>
            ))}
            {events.length === 0 && (
              <p className="text-gray-500">No events logged</p>
            )}
          </div>
        </div>
        
        <div className="mt-8 text-sm text-gray-400">
          <p>This debug page helps identify:</p>
          <ul className="list-disc list-inside mt-2">
            <li>Multiple WebSocket connections</li>
            <li>Duplicate audio sources</li>
            <li>CLM endpoint usage</li>
            <li>User context passing</li>
          </ul>
        </div>
      </div>
    </main>
  )
}