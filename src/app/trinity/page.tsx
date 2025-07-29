'use client'

import { useState, useEffect, useRef } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { HUME_COACHES } from '@/lib/hume-config'

export default function TrinityPage() {
  const { isSignedIn } = useUser()
  const router = useRouter()
  const [isConnected, setIsConnected] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [currentCoach, setCurrentCoach] = useState<'STORY_COACH' | 'QUEST_COACH' | 'DELIVERY_COACH'>('STORY_COACH')
  const [emotion, setEmotion] = useState<string>('neutral')
  const [phase, setPhase] = useState<'welcome' | 'exploring' | 'complete'>('welcome')
  const socketRef = useRef<WebSocket | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  
  // Hume AI configuration
  const HUME_API_KEY = process.env.NEXT_PUBLIC_HUME_API_KEY
  const HUME_SECRET_KEY = process.env.NEXT_PUBLIC_HUME_SECRET_KEY

  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    }
  }, [isSignedIn, router])

  // Connect to Hume AI when component mounts
  useEffect(() => {
    connectToHume()
    
    return () => {
      if (socketRef.current) {
        socketRef.current.close()
      }
    }
  }, [])

  const connectToHume = async () => {
    try {
      // Get access token
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
      
      // Connect to WebSocket
      const ws = new WebSocket(
        `wss://api.hume.ai/v0/evi/chat?access_token=${access_token}`
      )
      
      ws.onopen = () => {
        console.log('Connected to Hume AI')
        setIsConnected(true)
        
        // Send initial configuration
        const coach = HUME_COACHES[currentCoach]
        ws.send(JSON.stringify({
          type: 'session_settings',
          evi_version: '3',
          voice: {
            provider: 'hume_ai',
            voice_id: coach.voice_id
          },
          language_model: {
            ...coach.language_model,
            system_prompt: coach.system_prompt
          },
          tools: []
        }))
      }
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        switch (data.type) {
          case 'assistant_message':
            // Coach is speaking
            if (data.message?.content) {
              console.log('Coach:', data.message.content)
              // Check for phase transitions
              checkPhaseTransition(data.message.content)
            }
            break
            
          case 'assistant_prosody':
            // Update emotion display
            if (data.prosody?.emotions) {
              const topEmotion = Object.entries(data.prosody.emotions)
                .sort(([, a], [, b]) => (b as number) - (a as number))[0]
              setEmotion(topEmotion[0])
            }
            break
            
          case 'user_message':
            // User's speech was transcribed
            console.log('User:', data.message?.content)
            break
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
      }
      
      socketRef.current = ws
    } catch (error) {
      console.error('Failed to connect to Hume:', error)
    }
  }

  const checkPhaseTransition = (message: string) => {
    // Simple phase detection - in production this would be more sophisticated
    if (message.toLowerCase().includes('trinity') && currentCoach === 'STORY_COACH') {
      switchToQuestCoach()
    } else if (message.toLowerCase().includes('ready') && currentCoach === 'QUEST_COACH') {
      switchToDeliveryCoach()
    }
  }

  const switchToQuestCoach = () => {
    setCurrentCoach('QUEST_COACH')
    playTransitionSound()
    // Update session with new coach
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      const coach = HUME_COACHES.QUEST_COACH
      socketRef.current.send(JSON.stringify({
        type: 'session_update',
        voice: {
          provider: 'hume_ai',
          voice_id: coach.voice_id
        },
        language_model: {
          ...coach.language_model,
          system_prompt: coach.system_prompt
        }
      }))
    }
  }

  const switchToDeliveryCoach = () => {
    setCurrentCoach('DELIVERY_COACH')
    playTransitionSound()
    // Update session with new coach
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      const coach = HUME_COACHES.DELIVERY_COACH
      socketRef.current.send(JSON.stringify({
        type: 'session_update',
        voice: {
          provider: 'hume_ai',
          voice_id: coach.voice_id
        },
        language_model: {
          ...coach.language_model,
          system_prompt: coach.system_prompt
        }
      }))
    }
  }

  const playTransitionSound = () => {
    const audio = new Audio('/sounds/coach-transition.mp3')
    audio.play().catch(console.error)
  }

  const toggleListening = async () => {
    if (isListening) {
      // Stop recording
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop()
        mediaRecorderRef.current = null
      }
      setIsListening(false)
    } else {
      try {
        // Start recording
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        const mediaRecorder = new MediaRecorder(stream, {
          mimeType: 'audio/webm;codecs=opus'
        })
        
        mediaRecorder.ondataavailable = async (event) => {
          if (event.data.size > 0 && socketRef.current?.readyState === WebSocket.OPEN) {
            // Convert to base64 and send
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
        
        mediaRecorder.start(100) // 100ms chunks
        mediaRecorderRef.current = mediaRecorder
        setIsListening(true)
        
        if (phase === 'welcome') {
          setPhase('exploring')
        }
      } catch (error) {
        console.error('Failed to access microphone:', error)
      }
    }
  }

  const getCoachColor = () => {
    switch (currentCoach) {
      case 'STORY_COACH': return 'purple'
      case 'QUEST_COACH': return 'blue'
      case 'DELIVERY_COACH': return 'green'
    }
  }

  const getCoachInfo = () => {
    const coach = HUME_COACHES[currentCoach]
    const icons = {
      STORY_COACH: '📖',
      QUEST_COACH: '🧭',
      DELIVERY_COACH: '🎯'
    }
    return {
      name: coach.name,
      icon: icons[currentCoach]
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white flex items-center justify-center">
      <div className="text-center">
        {/* Coach Info */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Trinity Discovery</h1>
          <p className="text-xl text-gray-400">
            {phase === 'welcome' ? 'Click the circle to begin your journey' : `Speaking with ${getCoachInfo().name}`}
          </p>
        </div>

        {/* Pulsating Circle Interface */}
        <div className="relative">
          {/* Outer glow */}
          <div className={`absolute inset-0 rounded-full opacity-20 blur-3xl transition-all duration-1000 ${
            isListening ? 'scale-150' : 'scale-100'
          } ${
            getCoachColor() === 'purple' ? 'bg-purple-500' :
            getCoachColor() === 'blue' ? 'bg-blue-500' :
            'bg-green-500'
          }`} />
          
          {/* Main circle button */}
          <button
            onClick={toggleListening}
            disabled={!isConnected}
            className={`relative w-64 h-64 rounded-full transition-all duration-300 ${
              isListening ? 'scale-110' : 'scale-100 hover:scale-105'
            } ${
              getCoachColor() === 'purple' ? 'bg-purple-500 hover:bg-purple-600' :
              getCoachColor() === 'blue' ? 'bg-blue-500 hover:bg-blue-600' :
              'bg-green-500 hover:bg-green-600'
            } ${
              isListening ? 'animate-pulse' : ''
            } ${
              !isConnected ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            <div className="flex flex-col items-center justify-center h-full">
              <span className="text-6xl mb-4">{getCoachInfo().icon}</span>
              <span className="text-xl font-semibold">
                {!isConnected ? 'Connecting...' :
                 isListening ? 'Listening...' : 'Click to Speak'}
              </span>
            </div>
          </button>
          
          {/* Ripple effect when listening */}
          {isListening && (
            <>
              <div className={`absolute inset-0 rounded-full animate-ping ${
                getCoachColor() === 'purple' ? 'bg-purple-400' :
                getCoachColor() === 'blue' ? 'bg-blue-400' :
                'bg-green-400'
              } opacity-75`} />
              <div className={`absolute inset-0 rounded-full animate-ping animation-delay-200 ${
                getCoachColor() === 'purple' ? 'bg-purple-400' :
                getCoachColor() === 'blue' ? 'bg-blue-400' :
                'bg-green-400'
              } opacity-50`} />
            </>
          )}
        </div>

        {/* Connection Status */}
        <div className="mt-8">
          <div className={`inline-flex items-center text-sm ${
            isConnected ? 'text-green-400' : 'text-gray-400'
          }`}>
            <div className={`w-2 h-2 rounded-full mr-2 ${
              isConnected ? 'bg-green-400' : 'bg-gray-400'
            }`} />
            {isConnected ? 'Connected' : 'Connecting to coach...'}
          </div>
        </div>

        {/* Emotion indicator */}
        {emotion !== 'neutral' && isListening && (
          <div className="mt-4 text-sm text-gray-400">
            Detecting: {emotion}
          </div>
        )}

        {/* Skip to form (temporary) */}
        <div className="mt-12">
          <button
            onClick={() => router.push('/quest-readiness')}
            className="text-sm text-gray-500 hover:text-gray-400"
          >
            Skip to readiness check →
          </button>
        </div>
      </div>
    </main>
  )
}