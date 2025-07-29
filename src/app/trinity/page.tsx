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
  // const [emotion, setEmotion] = useState<string>('neutral') // TODO: Implement emotion tracking
  const [phase, setPhase] = useState<'welcome' | 'exploring' | 'complete'>('welcome')
  const [accessToken, setAccessToken] = useState<string>('')
  const [sessionStarted, setSessionStarted] = useState(false)
  
  const socketRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const audioQueueRef = useRef<AudioBufferSourceNode[]>([])
  const isConnectingRef = useRef(false)
  const processedAudioIds = useRef<Set<string>>(new Set())
  const lastAudioSequence = useRef<number>(0)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)

  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    }
  }, [isSignedIn, router])

  // Get access token on mount
  useEffect(() => {
    getAccessToken()
    
    // Cleanup on unmount
    return () => {
      disconnectChat()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Remove auto-connect - user must click start button
  // This prevents duplicate connections

  const getAccessToken = async () => {
    try {
      const response = await fetch('/api/hume/token')
      const data = await response.json()
      if (data.accessToken) {
        setAccessToken(data.accessToken)
      }
    } catch (error) {
      console.error('Failed to get access token:', error)
    }
  }

  const connectToHume = async () => {
    // Prevent duplicate connections with ref
    if (isConnectingRef.current) {
      console.log('Already attempting to connect')
      return
    }
    
    if (socketRef.current?.readyState === WebSocket.OPEN || 
        socketRef.current?.readyState === WebSocket.CONNECTING) {
      console.log('WebSocket already connected or connecting')
      return
    }
    
    isConnectingRef.current = true
    
    try {
      // Initialize audio context only if not already created
      if (!audioContextRef.current) {
        audioContextRef.current = new AudioContext()
        console.log('Created new AudioContext')
      }
      
      // Connect to WebSocket with EVI 3 format and config ID
      const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID
      const ws = new WebSocket(
        `wss://api.hume.ai/v0/evi/chat?access_token=${accessToken}&config_id=${configId}`
      )
      
      ws.onopen = () => {
        console.log('Connected to Hume AI EVI 3 - Socket ID:', Date.now())
        setIsConnected(true)
        isConnectingRef.current = false
        
        // No need to send session_settings when using config_id
        // The configuration is already set in Hume dashboard
      }
      
      ws.onmessage = async (event) => {
        const data = JSON.parse(event.data)
        console.log('Received:', data.type, data)
        
        switch (data.type) {
          case 'audio_output':
            // Handle audio output with sequence checking
            if (data.data && data.sequence_number) {
              // Only play if this is a new sequence
              if (data.sequence_number > lastAudioSequence.current) {
                lastAudioSequence.current = data.sequence_number
                await playAudioChunk(data.data)
              } else {
                console.log('Skipping out-of-order audio chunk')
              }
            } else if (data.data) {
              // Fallback for audio without sequence numbers
              await playAudioChunk(data.data)
            }
            break
            
          case 'assistant_message':
            // Coach is speaking
            if (data.message?.content) {
              console.log('Coach:', data.message.content)
              checkPhaseTransition(data.message.content)
            }
            break
            
          case 'assistant_end':
            // Assistant finished speaking
            console.log('Assistant finished')
            break
            
          case 'user_message':
            // User's speech was transcribed
            console.log('User:', data.message?.content)
            break
            
          case 'user_interruption':
            // User interrupted, stop audio
            stopAllAudio()
            break
            
          case 'error':
            console.error('Hume error:', data.error)
            break
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
        isConnectingRef.current = false
      }
      
      ws.onclose = () => {
        console.log('Disconnected from Hume')
        setIsConnected(false)
        isConnectingRef.current = false
      }
      
      socketRef.current = ws
    } catch (error) {
      console.error('Failed to connect to Hume:', error)
      isConnectingRef.current = false
    }
  }

  const playAudioChunk = async (base64Audio: string) => {
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
      source.start()
      
      // Track for cleanup
      audioQueueRef.current.push(source)
      
      // Remove from queue when done
      source.onended = () => {
        audioQueueRef.current = audioQueueRef.current.filter(s => s !== source)
      }
    } catch (error) {
      console.error('Error playing audio:', error)
    }
  }

  const stopAllAudio = () => {
    audioQueueRef.current.forEach(source => {
      try {
        source.stop()
      } catch {
        // Ignore if already stopped
      }
    })
    audioQueueRef.current = []
  }

  const checkPhaseTransition = (message: string) => {
    // Simple phase detection
    if (message.toLowerCase().includes('trinity') && currentCoach === 'STORY_COACH') {
      switchToQuestCoach()
    } else if (message.toLowerCase().includes('ready') && currentCoach === 'QUEST_COACH') {
      switchToDeliveryCoach()
    }
  }

  const switchToQuestCoach = () => {
    setCurrentCoach('QUEST_COACH')
    playTransitionSound()
    updateCoachSettings('QUEST_COACH')
  }

  const switchToDeliveryCoach = () => {
    setCurrentCoach('DELIVERY_COACH')
    playTransitionSound()
    updateCoachSettings('DELIVERY_COACH')
  }

  const updateCoachSettings = (coachType: typeof currentCoach) => {
    // Coach personality is now handled by the CLM endpoint
    // No need to update settings when using config_id
    console.log(`Switched to ${coachType}`)
  }

  const playTransitionSound = () => {
    const audio = new Audio('/sounds/coach-transition.mp3')
    audio.play().catch(console.error)
  }

  const startContinuousListening = async () => {
    if (!isConnected || mediaRecorderRef.current) {
      console.log('Not ready for continuous listening')
      return
    }

    try {
      console.log('Starting continuous listening...')
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0 && socketRef.current?.readyState === WebSocket.OPEN) {
          // Send audio continuously
          const reader = new FileReader()
          reader.onloadend = () => {
            const base64Audio = reader.result?.toString().split(',')[1]
            if (base64Audio) {
              socketRef.current?.send(JSON.stringify({
                type: 'audio_input',
                data: base64Audio
              }))
            }
          }
          reader.readAsDataURL(event.data)
        }
      }
      
      // Start recording with 100ms chunks for real-time
      mediaRecorder.start(100)
      mediaRecorderRef.current = mediaRecorder
      setIsListening(true)
      
      // Update phase
      if (phase === 'welcome') {
        setPhase('exploring')
      }
      
      console.log('Continuous listening started')
      
    } catch (error) {
      console.error('Failed to start continuous listening:', error)
    }
  }

  const startSession = async () => {
    // Re-fetch token if needed
    if (!accessToken) {
      console.log('No access token, fetching...')
      await getAccessToken()
      // Wait a bit for state to update
      setTimeout(async () => {
        if (accessToken) {
          setSessionStarted(true)
          await connectToHume()
          // Start continuous listening after connection
          setTimeout(() => startContinuousListening(), 1000)
        }
      }, 100)
    } else {
      setSessionStarted(true)
      await connectToHume()
      // Start continuous listening after connection
      setTimeout(() => startContinuousListening(), 1000)
    }
  }

  const disconnectChat = () => {
    // Stop recording if active
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current = null
    }
    
    // Stop all audio
    stopAllAudio()
    
    // Close WebSocket
    if (socketRef.current) {
      console.log('Closing WebSocket connection')
      socketRef.current.close()
      socketRef.current = null
    }
    
    // Close audio context
    if (audioContextRef.current) {
      console.log('Closing AudioContext')
      audioContextRef.current.close()
      audioContextRef.current = null
    }
    
    // Reset states
    setIsConnected(false)
    setIsListening(false)
    setPhase('welcome')
    setSessionStarted(false)
    
    // Clear processed audio IDs and sequence
    processedAudioIds.current.clear()
    lastAudioSequence.current = 0
    
    console.log('Disconnected from Hume')
  }

  // Remove toggleListening - we use continuous listening now

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
            {!sessionStarted ? 'Click Start Session to begin' :
             !isConnected ? 'Connecting to your coach...' :
             phase === 'welcome' ? 'Click the circle to speak' : 
             `Speaking with ${getCoachInfo().name}`}
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
          
          {/* Main circle indicator - no longer a button */}
          <div
            className={`relative w-64 h-64 rounded-full transition-all duration-300 ${
              isListening ? 'scale-110 animate-pulse' : 'scale-100'
            } ${
              getCoachColor() === 'purple' ? 'bg-purple-500' :
              getCoachColor() === 'blue' ? 'bg-blue-500' :
              'bg-green-500'
            } ${
              (!isConnected || !sessionStarted) ? 'opacity-50' : ''
            }`}
          >
            <div className="flex flex-col items-center justify-center h-full">
              <span className="text-6xl mb-4">{getCoachInfo().icon}</span>
              <span className="text-xl font-semibold">
                {!sessionStarted ? 'Start Session First' :
                 !isConnected ? 'Connecting...' :
                 isListening ? 'Listening...' : 'Setting up...'}
              </span>
            </div>
          </div>
          
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

        {/* Connection Status and Controls */}
        <div className="mt-8 flex flex-col items-center gap-4">
          {sessionStarted && (
            <div className={`inline-flex items-center text-sm ${
              isConnected ? 'text-green-400' : 'text-yellow-400'
            }`}>
              <div className={`w-2 h-2 rounded-full mr-2 ${
                isConnected ? 'bg-green-400' : 'bg-yellow-400 animate-pulse'
              }`} />
              {isConnected ? 'Connected' : 'Connecting...'}
            </div>
          )}
          
          {/* Start/Pause Toggle Button */}
          <button
            onClick={sessionStarted ? disconnectChat : startSession}
            disabled={!accessToken && sessionStarted}
            className={`px-8 py-3 rounded-full transition-all duration-300 text-white font-medium ${
              sessionStarted 
                ? 'bg-orange-600 hover:bg-orange-700' 
                : 'bg-green-600 hover:bg-green-700 transform hover:scale-105'
            }`}
          >
            {sessionStarted ? 'Pause Session' : 'Start Session'}
          </button>
        </div>

        {/* Debug info */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-8 text-xs text-gray-600">
            <p>Token: {accessToken ? 'Available' : 'Fetching...'}</p>
            <p>Coach: {currentCoach}</p>
            <p>Phase: {phase}</p>
          </div>
        )}

        {/* Navigation options */}
        <div className="mt-12 flex flex-col items-center gap-3">
          <button
            onClick={() => router.push('/trinity-visualization')}
            className="text-sm text-blue-400 hover:text-blue-300"
          >
            View Trinity Visualization →
          </button>
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