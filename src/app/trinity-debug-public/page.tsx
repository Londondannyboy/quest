'use client'

import { useState, useEffect, useRef } from 'react'

interface DebugEvent {
  timestamp: string
  type: 'connection' | 'audio' | 'message' | 'error' | 'duplicate'
  source: 'websocket' | 'audio-processor' | 'fingerprint' | 'unknown'
  details: string
  metadata?: Record<string, unknown>
}

interface AudioStats {
  totalChunks: number
  uniqueChunks: number
  duplicatesDetected: number
  fingerprintMatches: number
  idMatches: number
}

export default function TrinityDebugPublicPage() {
  const [events, setEvents] = useState<DebugEvent[]>([])
  const [connectionCount, setConnectionCount] = useState(0)
  const [audioStats, setAudioStats] = useState<AudioStats>({
    totalChunks: 0,
    uniqueChunks: 0,
    duplicatesDetected: 0,
    fingerprintMatches: 0,
    idMatches: 0
  })
  const [wsState, setWsState] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected')
  const [accessToken, setAccessToken] = useState('')
  const [isPlaying, setIsPlaying] = useState(false)
  
  const wsRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const audioQueueRef = useRef<AudioBufferSourceNode[]>([])
  const processedAudioIds = useRef<Set<string>>(new Set())
  const audioFingerprints = useRef<Map<string, number>>(new Map())
  const activeConnections = useRef<Set<number>>(new Set())
  
  const logEvent = (type: DebugEvent['type'], source: DebugEvent['source'], details: string, metadata?: Record<string, unknown>) => {
    const event: DebugEvent = {
      timestamp: new Date().toISOString(),
      type,
      source,
      details,
      metadata
    }
    setEvents(prev => [event, ...prev].slice(0, 100)) // Keep last 100 events
    console.log('[Trinity Debug Public]', event)
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

  // Improved fingerprint function that skips WAV header
  const generateFingerprint = (audioData: string): string => {
    // Skip WAV header (first 44 chars in base64 ≈ 33 bytes) to get to actual audio data
    const skipHeader = 60
    
    // Take samples from different parts of the actual audio data
    const samples = [
      audioData.substring(skipHeader, skipHeader + 40),
      audioData.substring(audioData.length / 4, audioData.length / 4 + 40),
      audioData.substring(audioData.length / 2 - 20, audioData.length / 2 + 20),
      audioData.substring(audioData.length * 3 / 4, audioData.length * 3 / 4 + 40),
      audioData.substring(audioData.length - 40)
    ]
    
    // Create a more unique fingerprint by combining samples
    return samples.join('|')
  }

  const connectWebSocket = () => {
    if (!accessToken) {
      logEvent('error', 'websocket', 'No access token available')
      return
    }

    // Check for existing connections
    if (wsRef.current?.readyState === WebSocket.OPEN || 
        wsRef.current?.readyState === WebSocket.CONNECTING) {
      logEvent('duplicate', 'websocket', 'Prevented duplicate connection attempt', {
        currentState: wsRef.current.readyState
      })
      return
    }

    // Track connection attempt
    const connectionId = Date.now()
    activeConnections.current.add(connectionId)
    setConnectionCount(prev => prev + 1)
    logEvent('connection', 'websocket', `Connection attempt #${connectionCount + 1}`, {
      connectionId,
      activeConnectionCount: activeConnections.current.size
    })
    
    setWsState('connecting')
    const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID
    
    const params = new URLSearchParams({
      access_token: accessToken,
      config_id: configId || ''
    })
    
    const ws = new WebSocket(`wss://api.hume.ai/v0/evi/chat?${params}`)
    
    ws.onopen = () => {
      setWsState('connected')
      logEvent('connection', 'websocket', 'WebSocket connected', {
        connectionId,
        readyState: ws.readyState
      })
      
      // Send minimal settings
      ws.send(JSON.stringify({
        type: 'session_settings',
        session_settings: {
          custom_session_id: `debug_${connectionId}`
        }
      }))
    }
    
    ws.onmessage = async (event) => {
      const data = JSON.parse(event.data)
      logEvent('message', 'websocket', `Received: ${data.type}`, {
        messageType: data.type,
        hasData: !!data.data
      })
      
      if (data.type === 'audio_output' && data.data) {
        setAudioStats(prev => ({
          ...prev,
          totalChunks: prev.totalChunks + 1
        }))
        
        // Check for duplicates
        const audioId = `${connectionId}_${Date.now()}_${data.data.substring(0, 20)}`
        const fingerprint = generateFingerprint(data.data)
        
        let isDuplicate = false
        let duplicateType = ''
        
        // Check ID-based duplicate
        if (processedAudioIds.current.has(audioId)) {
          isDuplicate = true
          duplicateType = 'id'
          setAudioStats(prev => ({
            ...prev,
            duplicatesDetected: prev.duplicatesDetected + 1,
            idMatches: prev.idMatches + 1
          }))
        }
        
        // Check fingerprint-based duplicate
        const fingerprintTime = audioFingerprints.current.get(fingerprint)
        if (fingerprintTime && Date.now() - fingerprintTime < 5000) {
          isDuplicate = true
          duplicateType = duplicateType ? 'both' : 'fingerprint'
          setAudioStats(prev => ({
            ...prev,
            duplicatesDetected: prev.duplicatesDetected + (duplicateType === 'fingerprint' ? 1 : 0),
            fingerprintMatches: prev.fingerprintMatches + 1
          }))
        }
        
        if (isDuplicate) {
          logEvent('duplicate', 'audio-processor', `Duplicate audio detected (${duplicateType})`, {
            audioId,
            fingerprint: fingerprint.substring(0, 20),
            duplicateType
          })
        } else {
          // Process unique audio
          processedAudioIds.current.add(audioId)
          audioFingerprints.current.set(fingerprint, Date.now())
          
          setAudioStats(prev => ({
            ...prev,
            uniqueChunks: prev.uniqueChunks + 1
          }))
          
          logEvent('audio', 'audio-processor', 'Unique audio chunk processed', {
            audioId,
            fingerprint: fingerprint.substring(0, 20),
            chunkSize: data.data.length
          })
          
          // Play audio
          await playAudioChunk(data.data)
          
          // Clean up old entries
          setTimeout(() => {
            processedAudioIds.current.delete(audioId)
          }, 10000)
        }
      }
      
      if (data.type === 'assistant_message') {
        logEvent('message', 'websocket', 'Assistant message', {
          content: data.message?.content?.substring(0, 100)
        })
      }
      
      if (data.type === 'user_interruption') {
        logEvent('message', 'websocket', 'User interruption detected')
        stopAllAudio()
      }
    }
    
    ws.onerror = (error) => {
      logEvent('error', 'websocket', 'WebSocket error', { 
        error: error.toString(),
        connectionId 
      })
      setWsState('disconnected')
    }
    
    ws.onclose = (event) => {
      activeConnections.current.delete(connectionId)
      logEvent('connection', 'websocket', 'WebSocket closed', {
        connectionId,
        code: event.code,
        reason: event.reason,
        remainingConnections: activeConnections.current.size
      })
      setWsState('disconnected')
    }
    
    wsRef.current = ws
  }

  const playAudioChunk = async (base64Audio: string) => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new AudioContext()
      }
      
      setIsPlaying(true)
      
      // Decode base64 to audio
      const audioData = atob(base64Audio)
      const arrayBuffer = new ArrayBuffer(audioData.length)
      const view = new Uint8Array(arrayBuffer)
      for (let i = 0; i < audioData.length; i++) {
        view[i] = audioData.charCodeAt(i)
      }
      
      const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer)
      const source = audioContextRef.current.createBufferSource()
      source.buffer = audioBuffer
      source.connect(audioContextRef.current.destination)
      
      source.onended = () => {
        const index = audioQueueRef.current.indexOf(source)
        if (index > -1) {
          audioQueueRef.current.splice(index, 1)
        }
        if (audioQueueRef.current.length === 0) {
          setIsPlaying(false)
        }
      }
      
      audioQueueRef.current.push(source)
      source.start()
    } catch (error) {
      logEvent('error', 'audio-processor', `Failed to play audio: ${error}`)
    }
  }

  const stopAllAudio = () => {
    audioQueueRef.current.forEach(source => {
      try {
        source.stop()
      } catch {
        // Already stopped
      }
    })
    audioQueueRef.current = []
    setIsPlaying(false)
  }

  const disconnect = () => {
    stopAllAudio()
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    processedAudioIds.current.clear()
    audioFingerprints.current.clear()
  }

  const clearAll = () => {
    disconnect()
    setEvents([])
    setConnectionCount(0)
    setAudioStats({
      totalChunks: 0,
      uniqueChunks: 0,
      duplicatesDetected: 0,
      fingerprintMatches: 0,
      idMatches: 0
    })
    activeConnections.current.clear()
  }

  // Auto-get token on mount
  useEffect(() => {
    getAccessToken()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const duplicateRate = audioStats.totalChunks > 0 
    ? ((audioStats.duplicatesDetected / audioStats.totalChunks) * 100).toFixed(1)
    : '0'

  return (
    <main className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Trinity Debug (Public - No Auth)</h1>
        <p className="text-gray-400 mb-8">Diagnostic page to identify WebSocket and audio duplication issues</p>
        
        {/* Status Overview */}
        <div className="grid grid-cols-5 gap-4 mb-8">
          <div className="bg-gray-800 p-4 rounded">
            <h3 className="text-sm text-gray-400">WebSocket</h3>
            <p className={`text-2xl font-bold ${
              wsState === 'connected' ? 'text-green-500' : 
              wsState === 'connecting' ? 'text-yellow-500' : 'text-red-500'
            }`}>{wsState}</p>
          </div>
          
          <div className="bg-gray-800 p-4 rounded">
            <h3 className="text-sm text-gray-400">Connections</h3>
            <p className="text-2xl font-bold text-blue-500">{connectionCount}</p>
            <p className="text-xs text-gray-500">Active: {activeConnections.current.size}</p>
          </div>
          
          <div className="bg-gray-800 p-4 rounded">
            <h3 className="text-sm text-gray-400">Audio Chunks</h3>
            <p className="text-2xl font-bold text-purple-500">{audioStats.totalChunks}</p>
            <p className="text-xs text-gray-500">Unique: {audioStats.uniqueChunks}</p>
          </div>
          
          <div className="bg-gray-800 p-4 rounded">
            <h3 className="text-sm text-gray-400">Duplicates</h3>
            <p className="text-2xl font-bold text-orange-500">{audioStats.duplicatesDetected}</p>
            <p className="text-xs text-gray-500">{duplicateRate}% rate</p>
          </div>
          
          <div className="bg-gray-800 p-4 rounded">
            <h3 className="text-sm text-gray-400">Audio Status</h3>
            <p className={`text-2xl font-bold ${isPlaying ? 'text-green-500' : 'text-gray-500'}`}>
              {isPlaying ? 'Playing' : 'Silent'}
            </p>
          </div>
        </div>
        
        {/* Duplicate Detection Stats */}
        <div className="bg-gray-800 p-4 rounded mb-8">
          <h3 className="text-lg font-semibold mb-2">Duplicate Detection Analysis</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-400">Fingerprint Matches</p>
              <p className="text-xl font-bold text-yellow-500">{audioStats.fingerprintMatches}</p>
            </div>
            <div>
              <p className="text-sm text-gray-400">ID Matches</p>
              <p className="text-xl font-bold text-orange-500">{audioStats.idMatches}</p>
            </div>
          </div>
        </div>
        
        {/* Controls */}
        <div className="flex gap-4 mb-8">
          <button
            onClick={connectWebSocket}
            disabled={!accessToken || wsState !== 'disconnected'}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded disabled:opacity-50"
          >
            Connect
          </button>
          
          <button
            onClick={disconnect}
            disabled={wsState !== 'connected'}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded disabled:opacity-50"
          >
            Disconnect
          </button>
          
          <button
            onClick={() => {
              // Simulate duplicate connection attempt
              connectWebSocket()
              setTimeout(() => connectWebSocket(), 100)
            }}
            disabled={!accessToken}
            className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded disabled:opacity-50"
          >
            Test Duplicate Connect
          </button>
          
          <button
            onClick={stopAllAudio}
            disabled={!isPlaying}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded disabled:opacity-50"
          >
            Stop Audio
          </button>
          
          <button
            onClick={clearAll}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded"
          >
            Clear All
          </button>
        </div>
        
        {/* Event Log */}
        <div className="bg-gray-800 p-4 rounded">
          <h3 className="text-lg font-semibold mb-4">Event Log</h3>
          <div className="space-y-1 max-h-96 overflow-y-auto font-mono text-xs">
            {events.map((event, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-gray-500 flex-shrink-0">
                  {event.timestamp.split('T')[1].split('.')[0]}
                </span>
                <span className={`flex-shrink-0 ${
                  event.type === 'error' ? 'text-red-400' :
                  event.type === 'connection' ? 'text-green-400' :
                  event.type === 'audio' ? 'text-purple-400' :
                  event.type === 'duplicate' ? 'text-orange-400' :
                  'text-blue-400'
                }`}>[{event.type.toUpperCase()}]</span>
                <span className="text-gray-400 flex-shrink-0">{event.source}:</span>
                <span className="flex-1">{event.details}</span>
                {event.metadata && (
                  <span className="text-gray-600 flex-shrink-0">
                    {JSON.stringify(event.metadata, null, 2)}
                  </span>
                )}
              </div>
            ))}
            {events.length === 0 && (
              <p className="text-gray-500">No events logged</p>
            )}
          </div>
        </div>
        
        <div className="mt-8 text-sm text-gray-400">
          <p className="font-semibold mb-2">Debugging Guide:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>Click &quot;Connect&quot; to establish a WebSocket connection</li>
            <li>Watch for duplicate audio chunks in the event log</li>
            <li>&quot;Test Duplicate Connect&quot; simulates rapid connection attempts</li>
            <li>Monitor the duplicate rate percentage</li>
            <li>Check if fingerprint or ID matches are causing duplicates</li>
          </ul>
        </div>
      </div>
    </main>
  )
}