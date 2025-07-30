'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { HUME_COACHES } from '@/lib/hume-config'

interface HumeMessage {
  type: string
  data?: string
  message?: {
    content?: string
    role?: string
  }
  error?: unknown
  code?: string
  session_settings?: {
    custom_session_id?: string
    context?: Record<string, unknown>
  }
}

export default function TrinityCleanPage() {
  const { isSignedIn } = useUser()
  const router = useRouter()
  
  // State
  const [isConnected, setIsConnected] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [currentCoach] = useState<'STORY_COACH' | 'QUEST_COACH' | 'DELIVERY_COACH'>('STORY_COACH')
  const [accessToken, setAccessToken] = useState('')
  const [transcript, setTranscript] = useState<string[]>([])
  
  // Refs
  const socketRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioQueueRef = useRef<AudioBufferSourceNode[]>([])
  
  // Redirect if not signed in
  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    }
  }, [isSignedIn, router])
  
  // Get access token on mount
  useEffect(() => {
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
        console.log('[Trinity Clean] Access token received')
      }
    } catch (error) {
      console.error('[Trinity Clean] Failed to get access token:', error)
    }
  }
  
  const connect = useCallback(async () => {
    if (!accessToken || socketRef.current?.readyState === WebSocket.OPEN) {
      return
    }
    
    try {
      // Initialize audio context
      if (!audioContextRef.current) {
        audioContextRef.current = new AudioContext()
      }
      
      // Build WebSocket URL
      const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID
      const params = new URLSearchParams({
        access_token: accessToken,
        config_id: configId || ''
      })
      
      const ws = new WebSocket(`wss://api.hume.ai/v0/evi/chat?${params}`)
      
      ws.onopen = () => {
        console.log('[Trinity Clean] Connected to Hume')
        setIsConnected(true)
        
        // Send initial session settings if needed
        const settings: HumeMessage = {
          type: 'session_settings',
          session_settings: {}
        }
        ws.send(JSON.stringify(settings))
      }
      
      ws.onmessage = async (event) => {
        const message: HumeMessage = JSON.parse(event.data)
        console.log('[Trinity Clean] Received:', message.type)
        
        switch (message.type) {
          case 'audio_output':
            // Play audio immediately as it arrives
            if (message.data) {
              await playAudioChunk(message.data)
            }
            break
            
          case 'assistant_message':
            if (message.message?.content) {
              console.log('[Trinity Clean] Assistant:', message.message.content)
              setTranscript(prev => [...prev, `Coach: ${message.message.content}`])
            }
            break
            
          case 'user_message':
            if (message.message?.content) {
              console.log('[Trinity Clean] User:', message.message.content)
              setTranscript(prev => [...prev, `You: ${message.message.content}`])
            }
            break
            
          case 'user_interruption':
            console.log('[Trinity Clean] User interrupted')
            stopAllAudio()
            break
            
          case 'error':
            console.error('[Trinity Clean] Error:', message)
            break
            
          case 'chat_metadata':
            console.log('[Trinity Clean] Chat metadata:', message)
            break
            
          case 'assistant_end':
            console.log('[Trinity Clean] Assistant finished')
            break
        }
      }
      
      ws.onerror = (error) => {
        console.error('[Trinity Clean] WebSocket error:', error)
      }
      
      ws.onclose = (event) => {
        console.log('[Trinity Clean] Disconnected:', event.code, event.reason)
        setIsConnected(false)
        setIsListening(false)
      }
      
      socketRef.current = ws
    } catch (error) {
      console.error('[Trinity Clean] Connection error:', error)
    }
  }, [accessToken])
  
  const playAudioChunk = async (base64Audio: string): Promise<void> => {
    if (!audioContextRef.current) return
    
    try {
      // Decode base64 to ArrayBuffer
      const binaryString = atob(base64Audio)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      
      // Decode audio data
      const audioBuffer = await audioContextRef.current.decodeAudioData(bytes.buffer)
      
      // Create and play audio source
      const source = audioContextRef.current.createBufferSource()
      source.buffer = audioBuffer
      source.connect(audioContextRef.current.destination)
      
      // Track for cleanup
      audioQueueRef.current.push(source)
      
      source.onended = () => {
        const index = audioQueueRef.current.indexOf(source)
        if (index > -1) {
          audioQueueRef.current.splice(index, 1)
        }
      }
      
      // Play immediately
      source.start()
      console.log(`[Trinity Clean] Playing audio chunk, duration: ${audioBuffer.duration}s`)
    } catch (error) {
      console.error('[Trinity Clean] Audio playback error:', error)
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
  }
  
  const startListening = async () => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      console.error('[Trinity Clean] WebSocket not connected')
      return
    }
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0) {
          // Convert to base64 and send
          const reader = new FileReader()
          reader.onloadend = () => {
            const base64Audio = reader.result?.toString().split(',')[1]
            if (base64Audio && socketRef.current?.readyState === WebSocket.OPEN) {
              const message: HumeMessage = {
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
      
      // Start recording in chunks
      mediaRecorder.start(100) // 100ms chunks
      mediaRecorderRef.current = mediaRecorder
      setIsListening(true)
      console.log('[Trinity Clean] Started listening')
    } catch (error) {
      console.error('[Trinity Clean] Microphone error:', error)
    }
  }
  
  const stopListening = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current = null
      setIsListening(false)
      console.log('[Trinity Clean] Stopped listening')
    }
  }
  
  const disconnect = () => {
    stopListening()
    stopAllAudio()
    
    if (socketRef.current) {
      socketRef.current.close()
      socketRef.current = null
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
    
    setIsConnected(false)
    setTranscript([])
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
        <h1 className="text-3xl font-bold mb-8 text-center">Trinity Clean Implementation</h1>
        
        {/* Status */}
        <div className="bg-gray-800 p-6 rounded-lg mb-8">
          <div className="grid grid-cols-3 gap-4 text-center">
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
                <p key={i} className={line.startsWith('You:') ? 'text-blue-400' : 'text-green-400'}>
                  {line}
                </p>
              ))
            )}
          </div>
        </div>
        
        {/* Debug Info */}
        <div className="mt-8 text-sm text-gray-500 text-center">
          <p>Clean implementation of Hume EVI API</p>
          <p>Audio plays immediately as chunks arrive</p>
        </div>
      </div>
    </main>
  )
}