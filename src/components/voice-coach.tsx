'use client'

import { useEffect, useRef, useState } from 'react'
import { CoachType } from '@prisma/client'

interface VoiceCoachProps {
  currentCoach: CoachType
  onCoachMessage?: (message: string) => void
  isActive: boolean
  currentField?: string
}

// Hume AI EVI configuration
const HUME_API_KEY = process.env.NEXT_PUBLIC_HUME_API_KEY
const HUME_CONFIG_ID = process.env.NEXT_PUBLIC_HUME_CONFIG_ID

export function VoiceCoach({ currentCoach, onCoachMessage, isActive }: VoiceCoachProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [emotion, setEmotion] = useState<string>('neutral')
  const socketRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  
  // Coach voice configurations
  const coachConfigs = {
    STORY_COACH: {
      name: 'Story Coach',
      voice: 'female-warm',
      accent: 'british-gentle',
      personality: 'empathetic biographer',
      icon: '📖',
      color: 'purple',
      greeting: "Hello, I'm your Story Coach. I'm here to help you discover the authentic story behind your professional journey."
    },
    QUEST_COACH: {
      name: 'Quest Coach',
      voice: 'male-energetic',
      accent: 'california',
      personality: 'insightful pattern-seeker',
      icon: '🧭',
      color: 'blue',
      greeting: "Welcome! I'm your Quest Coach. I see patterns emerging in your story. Let's uncover your Trinity together."
    },
    DELIVERY_COACH: {
      name: 'Delivery Coach',
      voice: 'neutral-firm',
      accent: 'clear-authoritative',
      personality: 'achievement-focused',
      icon: '🎯',
      color: 'green',
      greeting: "I'm your Delivery Coach. Let's turn your insights into action. Are you ready to make this real?"
    }
  }
  
  const currentConfig = coachConfigs[currentCoach]
  
  useEffect(() => {
    if (!isActive || !HUME_API_KEY) return
    
    // Initialize Hume AI WebSocket connection
    const connectToHume = async () => {
      try {
        // Create WebSocket connection to Hume AI
        const ws = new WebSocket(
          `wss://api.hume.ai/v0/stream/models?api_key=${HUME_API_KEY}`
        )
        
        ws.onopen = () => {
          console.log('Connected to Hume AI')
          setIsConnected(true)
          
          // Send initial configuration
          ws.send(JSON.stringify({
            models: {
              prosody: {},
              language: {},
              // Configure voice based on coach type
              voice: {
                config_id: HUME_CONFIG_ID,
                voice_settings: {
                  coach_type: currentCoach,
                  personality: currentConfig.personality
                }
              }
            },
            raw_text: false
          }))
          
          // Send greeting
          if (onCoachMessage) {
            onCoachMessage(currentConfig.greeting)
          }
        }
        
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data)
          
          // Handle emotion detection
          if (data.prosody?.emotions) {
            const topEmotion = Object.entries(data.prosody.emotions)
              .sort(([, a], [, b]) => (b as number) - (a as number))[0]
            setEmotion(topEmotion[0])
          }
          
          // Handle transcription
          if (data.language?.words && onCoachMessage) {
            const transcript = data.language.words.map((w: { word: string }) => w.word).join(' ')
            onCoachMessage(transcript)
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
        
        // Create audio processing pipeline
        const source = audioContextRef.current.createMediaStreamSource(stream)
        const processor = audioContextRef.current.createScriptProcessor(4096, 1, 1)
        
        processor.onaudioprocess = (e) => {
          if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            const inputData = e.inputBuffer.getChannelData(0)
            // Convert to appropriate format and send to Hume
            const audioData = Array.from(inputData)
            socketRef.current.send(JSON.stringify({
              audio: audioData,
              sample_rate: audioContextRef.current!.sampleRate
            }))
          }
        }
        
        source.connect(processor)
        processor.connect(audioContextRef.current.destination)
        
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
        currentConfig.color === 'purple' ? 'border-purple-500' :
        currentConfig.color === 'blue' ? 'border-blue-500' :
        'border-green-500'
      }`}>
        {/* Coach Avatar */}
        <div className="flex items-center mb-4">
          <div className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl ${
            currentConfig.color === 'purple' ? 'bg-purple-500' :
            currentConfig.color === 'blue' ? 'bg-blue-500' :
            'bg-green-500'
          }`}>
            {currentConfig.icon}
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
              : currentConfig.color === 'purple'
              ? 'bg-purple-500 hover:bg-purple-600'
              : currentConfig.color === 'blue'
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