'use client'

import { useEffect, useRef, useState } from 'react'
import { CoachType } from '@prisma/client'
import { HUME_COACHES, EVI_3_CONFIG } from '@/lib/hume-config'

interface VoiceCoachProps {
  currentCoach: CoachType
  onCoachMessage?: (message: string) => void
  isActive: boolean
  currentField?: string
}

// Hume AI EVI 3 configuration
const HUME_API_KEY = process.env.NEXT_PUBLIC_HUME_API_KEY
const HUME_SECRET_KEY = process.env.NEXT_PUBLIC_HUME_SECRET_KEY

// EVI 3 Voice IDs from Voice Library (these would be actual voice IDs)
const VOICE_IDS = {
  STORY_COACH: 'kora', // Female, warm voice
  QUEST_COACH: 'dacher', // Male, energetic voice  
  DELIVERY_COACH: 'ito' // Clear, authoritative voice
}

export function VoiceCoach({ currentCoach, onCoachMessage, isActive }: VoiceCoachProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [emotion, setEmotion] = useState<string>('neutral')
  const socketRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  
  // Get current coach configuration
  const currentConfig = HUME_COACHES[currentCoach]
  const coachVisuals = {
    STORY_COACH: { icon: '📖', color: 'purple' },
    QUEST_COACH: { icon: '🧭', color: 'blue' },
    DELIVERY_COACH: { icon: '🎯', color: 'green' }
  }
  const currentVisual = coachVisuals[currentCoach]
  
  useEffect(() => {
    if (!isActive || !HUME_API_KEY) return
    
    // Initialize Hume AI EVI 3 WebSocket connection
    const connectToHume = async () => {
      try {
        // First, get an access token
        const tokenResponse = await fetch('https://api.hume.ai/oauth2-cc/token', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams({
            grant_type: 'client_credentials',
            client_id: HUME_API_KEY || '',
            client_secret: HUME_SECRET_KEY || '',
          }),
        })
        
        const { access_token } = await tokenResponse.json()
        
        // Create WebSocket connection to Hume AI EVI 3
        const ws = new WebSocket(
          `wss://api.hume.ai/v0/evi/chat?access_token=${access_token}`
        )
        
        ws.onopen = () => {
          console.log('Connected to Hume AI EVI 3')
          setIsConnected(true)
          
          // Send session settings for EVI 3
          ws.send(JSON.stringify({
            type: 'session_settings',
            ...EVI_3_CONFIG,
            voice: {
              provider: 'hume_ai',
              voice_id: currentConfig.voice_id
            },
            language_model: {
              ...currentConfig.language_model,
              system_prompt: currentConfig.system_prompt
            },
            tools: []
          }))
        }
        
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data)
          
          // Handle different EVI 3 message types
          switch (data.type) {
            case 'chat_metadata':
              console.log('Chat metadata:', data)
              break
              
            case 'user_message':
              // User's transcribed speech
              if (data.message?.content) {
                console.log('User said:', data.message.content)
              }
              break
              
            case 'assistant_message':
              // Assistant's response
              if (data.message?.content && onCoachMessage) {
                onCoachMessage(data.message.content)
              }
              break
              
            case 'assistant_prosody':
              // EVI 3 sends prosody separately
              if (data.prosody?.emotions) {
                const topEmotion = Object.entries(data.prosody.emotions)
                  .sort(([, a], [, b]) => (b as number) - (a as number))[0]
                setEmotion(topEmotion[0])
              }
              break
              
            case 'audio_output':
              // Handle audio playback if needed
              break
              
            case 'error':
              console.error('Hume AI error:', data)
              break
          }
        }
        
        ws.onerror = (error) => {
          console.error('Hume AI error:', error)
          setIsConnected(false)
        }
        
        ws.onclose = () => {
          console.log('Disconnected from Hume AI')
          setIsConnected(false)
        }
        
        socketRef.current = ws
      } catch (error) {
        console.error('Failed to connect to Hume AI:', error)
      }
    }
    
    connectToHume()
    
    // Cleanup
    return () => {
      if (socketRef.current) {
        socketRef.current.close()
      }
    }
  }, [isActive, currentCoach, currentConfig, onCoachMessage])
  
  // Start/stop listening
  const toggleListening = async () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext()
    }
    
    if (isListening) {
      setIsListening(false)
      // Stop audio capture
    } else {
      try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        
        // For EVI 3, we need to send audio in base64 format
        const mediaRecorder = new MediaRecorder(stream, {
          mimeType: 'audio/webm;codecs=opus'
        })
        
        mediaRecorder.ondataavailable = async (event) => {
          if (event.data.size > 0 && socketRef.current?.readyState === WebSocket.OPEN) {
            // Convert audio blob to base64
            const reader = new FileReader()
            reader.onloadend = () => {
              const base64Audio = reader.result?.toString().split(',')[1]
              if (base64Audio) {
                socketRef.current!.send(JSON.stringify({
                  type: 'audio_input',
                  data: base64Audio
                }))
              }
            }
            reader.readAsDataURL(event.data)
          }
        }
        
        // Start recording in chunks
        mediaRecorder.start(100) // 100ms chunks
        
        setIsListening(true)
      } catch (error) {
        console.error('Failed to access microphone:', error)
      }
    }
  }
  
  if (!isActive) return null
  
  return (
    <div className={`fixed bottom-8 right-8 z-50 transition-all duration-500 ${
      isConnected ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
    }`}>
      <div className={`bg-gray-900 rounded-2xl shadow-2xl p-6 border-2 ${
        currentVisual.color === 'purple' ? 'border-purple-500' :
        currentVisual.color === 'blue' ? 'border-blue-500' :
        'border-green-500'
      }`}>
        {/* Coach Avatar */}
        <div className="flex items-center mb-4">
          <div className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl ${
            currentVisual.color === 'purple' ? 'bg-purple-500' :
            currentVisual.color === 'blue' ? 'bg-blue-500' :
            'bg-green-500'
          }`}>
            {currentVisual.icon}
          </div>
          <div className="ml-4">
            <h3 className="text-lg font-semibold">{currentConfig.name}</h3>
            <p className="text-sm text-gray-400">
              {isListening ? 'Listening...' : 'Click to speak'}
            </p>
          </div>
        </div>
        
        {/* Emotion Indicator */}
        {emotion !== 'neutral' && (
          <div className="mb-4 text-sm text-gray-400">
            Detecting: {emotion}
          </div>
        )}
        
        {/* Voice Button */}
        <button
          onClick={toggleListening}
          className={`w-full py-3 rounded-lg font-semibold transition-all ${
            isListening
              ? 'bg-red-500 hover:bg-red-600 animate-pulse'
              : currentVisual.color === 'purple'
              ? 'bg-purple-500 hover:bg-purple-600'
              : currentVisual.color === 'blue'
              ? 'bg-blue-500 hover:bg-blue-600'
              : 'bg-green-500 hover:bg-green-600'
          }`}
        >
          {isListening ? '🎤 Stop Speaking' : '🎙️ Start Speaking'}
        </button>
        
        {/* Connection Status */}
        <div className="mt-4 text-center">
          <div className={`inline-flex items-center text-sm ${
            isConnected ? 'text-green-400' : 'text-red-400'
          }`}>
            <div className={`w-2 h-2 rounded-full mr-2 ${
              isConnected ? 'bg-green-400' : 'bg-red-400'
            }`} />
            {isConnected ? 'Connected' : 'Connecting...'}
          </div>
        </div>
      </div>
    </div>
  )
}