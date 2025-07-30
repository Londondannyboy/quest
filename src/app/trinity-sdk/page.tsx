'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { HumeClient } from 'hume'
import type { SubscribeEvent } from 'hume/api/resources/empathicVoice/resources/chat'
import type { CloseEvent } from 'hume/core/websocket/events'
import {
  convertBlobToBase64,
  ensureSingleValidAudioTrack,
  getAudioStream,
  getBrowserSupportedMimeType,
  MimeType
} from 'hume'
import { HUME_COACHES } from '@/lib/hume-config'

// Note: EVIWebAudioPlayer is imported dynamically when needed to avoid SSR issues

export default function TrinitySdkPage() {
  const { isSignedIn, user } = useUser()
  const router = useRouter()
  
  // State
  const [isConnected, setIsConnected] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [currentCoach] = useState<'STORY_COACH' | 'QUEST_COACH' | 'DELIVERY_COACH'>('STORY_COACH')
  const [transcript, setTranscript] = useState<string[]>([])
  const [audioStatus, setAudioStatus] = useState<'idle' | 'playing'>('idle')
  const [error, setError] = useState<string>('')
  
  // Refs
  const clientRef = useRef<HumeClient | null>(null)
  const socketRef = useRef<{ sendAudioInput: (data: { data: string }) => void, readyState: number, close: () => void, send?: (data: string) => void } | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const playerRef = useRef<{ init: () => Promise<void>, enqueue: (msg: SubscribeEvent) => Promise<void>, stop: () => void } | null>(null)
  const [accessToken, setAccessToken] = useState<string>('')
  
  // Redirect if not signed in
  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    }
  }, [isSignedIn, router])
  
  // Initialize Hume client
  useEffect(() => {
    const initializeClient = async () => {
      try {
        // First try to get access token
        const response = await fetch('/api/hume/token')
        const data = await response.json()
        
        if (data.accessToken) {
          console.log('[Trinity SDK] Using access token from API')
          // Access token approach - preferred
          setAccessToken(data.accessToken)
        } else {
          // Fallback to API key
          const apiKey = process.env.NEXT_PUBLIC_HUME_API_KEY
          if (!apiKey || apiKey === '...') {
            setError('Hume API key not configured - please set NEXT_PUBLIC_HUME_API_KEY in Vercel')
            return
          }
          
          clientRef.current = new HumeClient({
            apiKey,
          })
        }
        
        // Initialize audio player
        import('hume').then(({ EVIWebAudioPlayer }) => {
          playerRef.current = new EVIWebAudioPlayer()
          console.log('[Trinity SDK] Audio player initialized')
        })
      } catch (error) {
        console.error('[Trinity SDK] Initialization error:', error)
        setError(`Initialization failed: ${error}`)
      }
    }
    
    initializeClient()
    
    return () => {
      disconnect()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  
  const handleOpen = useCallback(async () => {
    console.log('[Trinity SDK] Socket opened')
    setIsConnected(true)
    
    // Initialize audio player
    if (playerRef.current) {
      await playerRef.current.init()
      console.log('[Trinity SDK] Audio player initialized')
    }
    
    // Send user context if available
    if (socketRef.current && user) {
      // Note: The SDK may handle this differently than raw WebSocket
      // Check SDK documentation for proper context passing
      console.log('[Trinity SDK] Connected with user:', user.id)
    }
  }, [user])
  
  const handleMessage = useCallback(async (msg: SubscribeEvent) => {
    console.log('[Trinity SDK] Received message:', msg.type)
    
    switch (msg.type) {
      case 'audio_output':
        // Use EVIWebAudioPlayer to handle audio
        if (playerRef.current) {
          await playerRef.current.enqueue(msg)
          setAudioStatus('playing')
        }
        break
        
      case 'assistant_message':
        if ('message' in msg && msg.message?.content) {
          console.log('[Trinity SDK] Assistant:', msg.message.content)
          setTranscript(prev => [...prev, `Coach: ${msg.message.content}`])
        }
        break
        
      case 'user_message':
        if ('message' in msg && msg.message?.content) {
          console.log('[Trinity SDK] User:', msg.message.content)
          setTranscript(prev => [...prev, `You: ${msg.message.content}`])
        }
        break
        
      case 'user_interruption':
        console.log('[Trinity SDK] User interrupted')
        if (playerRef.current) {
          playerRef.current.stop()
          setAudioStatus('idle')
        }
        break
        
      case 'assistant_end':
        console.log('[Trinity SDK] Assistant finished')
        setAudioStatus('idle')
        break
        
      case 'error':
        console.error('[Trinity SDK] Error:', msg)
        if ('error' in msg) {
          setError(`Error: ${JSON.stringify(msg.error)}`)
        }
        break
    }
  }, [])
  
  const handleError = useCallback((err: Event | Error) => {
    console.error('[Trinity SDK] WebSocket error:', err)
    setError(`Connection error: ${err.toString()}`)
    setIsConnected(false)
    setIsListening(false)
  }, [])
  
  const handleClose = useCallback((e: CloseEvent) => {
    console.log('[Trinity SDK] Socket closed:', e.code, e.reason)
    setIsConnected(false)
    setIsListening(false)
    setAudioStatus('idle')
  }, [])
  
  const connect = async () => {
    try {
      console.log('[Trinity SDK] Connecting to Hume...')
      
      // Get config ID from environment
      const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID
      if (!configId || configId === '...') {
        setError('Hume config ID not set - please set NEXT_PUBLIC_HUME_CONFIG_ID in Vercel')
        return
      }
      
      // If we have access token, use it directly
      if (accessToken) {
        console.log('[Trinity SDK] Using access token for connection')
        // For access token, we need to use the WebSocket directly
        const params = new URLSearchParams({
          access_token: accessToken,
          config_id: configId
        })
        
        const ws = new WebSocket(`wss://api.hume.ai/v0/evi/chat?${params}`)
        
        ws.onopen = () => handleOpen()
        ws.onmessage = (event) => handleMessage(JSON.parse(event.data))
        ws.onerror = (error) => handleError(error)
        ws.onclose = (event) => handleClose({ code: event.code, reason: event.reason })
        
        socketRef.current = ws as typeof socketRef.current
      } else if (clientRef.current) {
        // Use SDK client
        const socket = await clientRef.current.empathicVoice.chat.connect({
          configId: configId,
        })
        
        socket.on('open', handleOpen)
        socket.on('message', handleMessage)
        socket.on('error', handleError)
        socket.on('close', handleClose)
        
        socketRef.current = socket
      } else {
        setError('No authentication method available')
      }
    } catch (error) {
      console.error('[Trinity SDK] Connection error:', error)
      setError(`Failed to connect: ${error}`)
    }
  }
  
  const startAudioCapture = async (timeSliceMs = 100): Promise<MediaRecorder> => {
    if (!socketRef.current) {
      throw new Error('Socket not connected')
    }
    
    const mimeTypeResult = getBrowserSupportedMimeType()
    const mimeType = mimeTypeResult.success
      ? mimeTypeResult.mimeType
      : MimeType.WEBM
    
    const micAudioStream = await getAudioStream()
    ensureSingleValidAudioTrack(micAudioStream)
    
    const recorder = new MediaRecorder(micAudioStream, { mimeType })
    recorder.ondataavailable = async (e: BlobEvent) => {
      if (e.data.size > 0 && socketRef.current?.readyState === WebSocket.OPEN) {
        const data = await convertBlobToBase64(e.data)
        socketRef.current.sendAudioInput({ data })
      }
    }
    
    recorder.onerror = (e) => console.error('[Trinity SDK] MediaRecorder error:', e)
    recorder.start(timeSliceMs)
    
    return recorder
  }
  
  const startListening = async () => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      setError('WebSocket not connected')
      return
    }
    
    try {
      recorderRef.current = await startAudioCapture()
      setIsListening(true)
      console.log('[Trinity SDK] Started listening')
    } catch (error) {
      console.error('[Trinity SDK] Microphone error:', error)
      setError(`Microphone error: ${error}`)
    }
  }
  
  const stopListening = () => {
    if (recorderRef.current) {
      recorderRef.current.stop()
      // Stop all tracks
      recorderRef.current.stream.getTracks().forEach(track => track.stop())
      recorderRef.current = null
      setIsListening(false)
      console.log('[Trinity SDK] Stopped listening')
    }
  }
  
  const disconnect = () => {
    stopListening()
    
    if (playerRef.current) {
      playerRef.current.stop()
    }
    
    if (socketRef.current) {
      socketRef.current.close()
      socketRef.current = null
    }
    
    setIsConnected(false)
    setTranscript([])
    setAudioStatus('idle')
    setError('')
  }
  
  const getCoachInfo = () => {
    const coach = HUME_COACHES[currentCoach]
    return {
      name: coach.name,
      icon: currentCoach === 'STORY_COACH' ? '📖' : currentCoach === 'QUEST_COACH' ? '🧭' : '🎯',
      color: currentCoach === 'STORY_COACH' ? 'purple' : currentCoach === 'QUEST_COACH' ? 'blue' : 'green'
    }
  }
  
  const coachInfo = getCoachInfo()
  
  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-center">Trinity SDK Implementation</h1>
        
        {/* Error Display */}
        {error && (
          <div className="bg-red-900/50 border border-red-600 text-red-200 p-4 rounded mb-6">
            {error}
          </div>
        )}
        
        {/* Status */}
        <div className="bg-gray-800 p-6 rounded-lg mb-8">
          <div className="grid grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-sm text-gray-400">Connection</p>
              <p className={`text-xl font-bold ${isConnected ? 'text-green-500' : 'text-red-500'}`}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-400">Microphone</p>
              <p className={`text-xl font-bold ${isListening ? 'text-green-500' : 'text-gray-500'}`}>
                {isListening ? 'Listening' : 'Off'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-400">Audio</p>
              <p className={`text-xl font-bold ${
                audioStatus === 'playing' ? 'text-green-500' : 'text-gray-500'
              }`}>
                {audioStatus === 'playing' ? 'Playing' : 'Idle'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-400">Coach</p>
              <p className={`text-xl font-bold text-${coachInfo.color}-500`}>
                {coachInfo.icon} {coachInfo.name}
              </p>
            </div>
          </div>
        </div>
        
        {/* Controls */}
        <div className="flex justify-center gap-4 mb-8">
          {!isConnected ? (
            <button
              onClick={connect}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg"
            >
              Connect to Hume
            </button>
          ) : (
            <>
              <button
                onClick={isListening ? stopListening : startListening}
                className={`px-6 py-3 rounded-lg ${
                  isListening 
                    ? 'bg-red-600 hover:bg-red-700' 
                    : 'bg-green-600 hover:bg-green-700'
                }`}
              >
                {isListening ? 'Stop Speaking' : 'Start Speaking'}
              </button>
              <button
                onClick={disconnect}
                className="px-6 py-3 bg-gray-600 hover:bg-gray-700 rounded-lg"
              >
                Disconnect
              </button>
            </>
          )}
        </div>
        
        {/* Transcript */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Conversation</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {transcript.length === 0 ? (
              <p className="text-gray-500">No conversation yet...</p>
            ) : (
              transcript.map((line, i) => (
                <p key={i} className={
                  line.startsWith('You:') ? 'text-blue-400' : 'text-green-400'
                }>
                  {line}
                </p>
              ))
            )}
          </div>
        </div>
        
        {/* Debug Info */}
        <div className="mt-8 text-sm text-gray-500 text-center">
          <p>Official Hume SDK implementation</p>
          <p>Using EVIWebAudioPlayer for audio handling</p>
          <p className="text-xs mt-2">API Key: {process.env.NEXT_PUBLIC_HUME_API_KEY ? '✓ Configured' : '✗ Missing'}</p>
          <p className="text-xs">Config ID: {process.env.NEXT_PUBLIC_HUME_CONFIG_ID ? '✓ Configured' : '✗ Missing'}</p>
        </div>
      </div>
    </main>
  )
}