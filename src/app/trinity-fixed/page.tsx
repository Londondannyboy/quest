'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { HUME_COACHES } from '@/lib/hume-config'
import { HumeAudioProcessor } from '@/lib/hume-audio-processor'
import { wsManager } from '@/lib/websocket-manager'

interface HumeMessage {
  type: string
  data?: string
  message?: {
    content?: string
    role?: string
  }
  error?: {
    code?: string
    message?: string
    type?: string
  }
}

export default function TrinityFixedPage() {
  const { isSignedIn, user } = useUser()
  const router = useRouter()
  
  // State
  const [isConnected, setIsConnected] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [currentCoach] = useState<'STORY_COACH' | 'QUEST_COACH' | 'DELIVERY_COACH'>('STORY_COACH')
  const [accessToken, setAccessToken] = useState('')
  const [transcript, setTranscript] = useState<string[]>([])
  const [audioStatus, setAudioStatus] = useState<'idle' | 'buffering' | 'playing'>('idle')
  
  // Refs
  const socketRef = useRef<WebSocket | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioProcessorRef = useRef<HumeAudioProcessor | null>(null)
  const sessionIdRef = useRef<string>(Date.now().toString())
  
  // Redirect if not signed in
  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    }
  }, [isSignedIn, router])
  
  // Initialize audio processor and get access token
  useEffect(() => {
    // Create audio processor
    audioProcessorRef.current = new HumeAudioProcessor()
    audioProcessorRef.current.setOnComplete(() => {
      console.log('[Trinity Fixed] Audio playback complete')
      setAudioStatus('idle')
    })
    
    getAccessToken()
    
    return () => {
      disconnect()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  
  const getAccessToken = async () => {
    try {
      const response = await fetch('/api/hume/token')
      const data = await response.json()
      if (data.accessToken) {
        setAccessToken(data.accessToken)
        console.log('[Trinity Fixed] Access token received')
      }
    } catch (error) {
      console.error('[Trinity Fixed] Failed to get access token:', error)
    }
  }
  
  const connect = useCallback(async () => {
    if (!accessToken || wsManager.isConnected()) {
      console.log('[Trinity Fixed] Cannot connect - no token or already connected')
      return
    }
    
    try {
      console.log('[Trinity Fixed] Connecting to Hume...')
      
      // Build WebSocket URL
      const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID
      const params = new URLSearchParams({
        access_token: accessToken,
        config_id: configId || '',
        user_id: user?.id || 'anonymous',
        user_name: user?.fullName || user?.firstName || 'User'
      })
      
      const ws = await wsManager.connect(
        `wss://api.hume.ai/v0/evi/chat?${params}`,
        {
          onopen: () => {
            console.log('[Trinity Fixed] Connected to Hume')
            setIsConnected(true)
            
            // Send initial session settings
            if (socketRef.current) {
              const settings = {
                type: 'session_settings',
                session_settings: {
                  custom_session_id: sessionIdRef.current
                }
              }
              socketRef.current.send(JSON.stringify(settings))
              console.log('[Trinity Fixed] Sent session settings')
            }
          },
          onmessage: async (event) => {
            const message: HumeMessage = JSON.parse(event.data)
            console.log('[Trinity Fixed] Received:', message.type)
            
            switch (message.type) {
              case 'audio_output':
                // Buffer audio chunks
                if (message.data && audioProcessorRef.current) {
                  await audioProcessorRef.current.addChunk(message.data)
                  setAudioStatus('buffering')
                  console.log(`[Trinity Fixed] Buffered chunk ${audioProcessorRef.current.getChunkCount()}`)
                }
                break
                
              case 'assistant_message': {
                const content = message.message?.content
                if (content) {
                  console.log('[Trinity Fixed] Assistant:', content)
                  setTranscript(prev => [...prev, `Coach: ${content}`])
                  
                  // Play buffered audio when assistant message arrives
                  // This ensures we have all chunks before playing
                  if (audioProcessorRef.current && audioProcessorRef.current.getChunkCount() > 0) {
                    console.log('[Trinity Fixed] Playing buffered audio')
                    setAudioStatus('playing')
                    await audioProcessorRef.current.playAll()
                  }
                }
                break
              }
                
              case 'user_message': {
                const content = message.message?.content
                if (content) {
                  console.log('[Trinity Fixed] User:', content)
                  setTranscript(prev => [...prev, `You: ${content}`])
                }
                break
              }
                
              case 'user_interruption':
                console.log('[Trinity Fixed] User interrupted')
                if (audioProcessorRef.current) {
                  audioProcessorRef.current.stop()
                  setAudioStatus('idle')
                }
                break
                
              case 'assistant_end':
                console.log('[Trinity Fixed] Assistant finished')
                // Play any remaining buffered audio
                if (audioProcessorRef.current && audioProcessorRef.current.getChunkCount() > 0) {
                  console.log('[Trinity Fixed] Playing remaining audio')
                  setAudioStatus('playing')
                  await audioProcessorRef.current.playAll()
                }
                break
                
              case 'error': {
                const error = message.error || message
                console.error('[Trinity Fixed] Error:', error)
                setTranscript(prev => [...prev, `Error: ${error.message || 'Unknown error'}`])
                break
              }
                
              case 'chat_metadata':
                console.log('[Trinity Fixed] Chat metadata:', message)
                break
            }
          },
          onerror: (error) => {
            console.error('[Trinity Fixed] WebSocket error:', error)
            setIsConnected(false)
            setIsListening(false)
          },
          onclose: (event) => {
            console.log('[Trinity Fixed] Disconnected:', event.code, event.reason)
            setIsConnected(false)
            setIsListening(false)
            setAudioStatus('idle')
          }
        }
      )
      
      if (ws) {
        socketRef.current = ws
      }
    } catch (error) {
      console.error('[Trinity Fixed] Connection error:', error)
      setIsConnected(false)
    }
  }, [accessToken, user])
  
  const startListening = async () => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      console.error('[Trinity Fixed] WebSocket not connected')
      return
    }
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0) {
          const reader = new FileReader()
          reader.onloadend = () => {
            const base64Audio = reader.result?.toString().split(',')[1]
            if (base64Audio && socketRef.current?.readyState === WebSocket.OPEN) {
              const message = {
                type: 'audio_input',
                data: base64Audio
              }
              socketRef.current.send(JSON.stringify(message))
            }
          }
          reader.readAsDataURL(event.data)
        }
      }
      
      mediaRecorder.onstop = () => {
        stream.getTracks().forEach(track => track.stop())
      }
      
      mediaRecorder.start(100) // 100ms chunks
      mediaRecorderRef.current = mediaRecorder
      setIsListening(true)
      console.log('[Trinity Fixed] Started listening')
    } catch (error) {
      console.error('[Trinity Fixed] Microphone error:', error)
    }
  }
  
  const stopListening = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current = null
      setIsListening(false)
      console.log('[Trinity Fixed] Stopped listening')
    }
  }
  
  const disconnect = () => {
    stopListening()
    
    if (audioProcessorRef.current) {
      audioProcessorRef.current.stop()
    }
    
    wsManager.disconnect()
    socketRef.current = null
    
    setIsConnected(false)
    setTranscript([])
    setAudioStatus('idle')
    
    // Generate new session ID for next connection
    sessionIdRef.current = Date.now().toString()
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
        <h1 className="text-3xl font-bold mb-8 text-center">Trinity Fixed Implementation</h1>
        
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
                audioStatus === 'playing' ? 'text-green-500' : 
                audioStatus === 'buffering' ? 'text-yellow-500' : 
                'text-gray-500'
              }`}>
                {audioStatus === 'playing' ? 'Playing' : 
                 audioStatus === 'buffering' ? 'Buffering' : 
                 'Idle'}
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
              disabled={!accessToken}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50"
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
                  line.startsWith('You:') ? 'text-blue-400' : 
                  line.startsWith('Error:') ? 'text-red-400' :
                  'text-green-400'
                }>
                  {line}
                </p>
              ))
            )}
          </div>
        </div>
        
        {/* Debug Info */}
        <div className="mt-8 text-sm text-gray-500 text-center">
          <p>Fixed implementation with proper audio buffering</p>
          <p>Buffers chunks and plays on assistant message</p>
          <p>Session ID: {sessionIdRef.current}</p>
        </div>
      </div>
    </main>
  )
}