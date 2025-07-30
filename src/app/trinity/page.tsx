'use client'

import { useState, useEffect, useRef } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { HUME_COACHES } from '@/lib/hume-config'
import { getOrCreateSession, addMessage, updateSessionMetadata } from '@/lib/zep'

export default function TrinityPage() {
  const { isSignedIn, user } = useUser()
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
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const zepSessionIdRef = useRef<string | null>(null)
  const audioSessionIdRef = useRef<string>(Date.now().toString())

  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    }
  }, [isSignedIn, router])

  // Get access token on mount
  useEffect(() => {
    getAccessToken()
    initializeZepSession()
    
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

  const initializeZepSession = async () => {
    if (!user?.id) return
    
    try {
      // Fetch the database user ID
      const response = await fetch('/api/user/profile')
      const userData = await response.json()
      
      if (userData.id) {
        const session = await getOrCreateSession(userData.id, 'trinity', {
          audioSessionId: audioSessionIdRef.current,
          startTime: new Date().toISOString()
        })
        zepSessionIdRef.current = session.sessionId || null
        console.log('Zep session initialized:', session.sessionId)
      }
    } catch (error) {
      console.error('Failed to initialize Zep session:', error)
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
    
    // Clear any existing audio before new connection
    stopAllAudio()
    processedAudioIds.current.clear()
    
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
      
      // Track connection in Zep
      if (zepSessionIdRef.current) {
        await addMessage(zepSessionIdRef.current, 'assistant', `[SYSTEM] WebSocket connection initiated - Session: ${audioSessionIdRef.current}`, {
          type: 'connection_event',
          audioSessionId: audioSessionIdRef.current,
          timestamp: new Date().toISOString()
        })
      }
      
      ws.onopen = async () => {
        console.log('Connected to Hume AI EVI 3 - Socket ID:', audioSessionIdRef.current)
        setIsConnected(true)
        isConnectingRef.current = false
        
        // Send initial configuration to set user context
        if (user?.id) {
          const configMessage = {
            type: 'session_settings',
            session_settings: {
              custom_session_id: audioSessionIdRef.current,
              context: {
                user_id: user.id,
                user_name: user.fullName || user.firstName || 'User'
              }
            }
          }
          ws.send(JSON.stringify(configMessage))
          console.log('Sent user context to Hume:', configMessage)
        }
      }
      
      ws.onmessage = async (event) => {
        const data = JSON.parse(event.data)
        console.log('Received:', data.type, data)
        
        // Track all events in Zep for debugging
        if (zepSessionIdRef.current) {
          await addMessage(zepSessionIdRef.current, 'assistant', `[AUDIO_EVENT] ${data.type}`, {
            type: 'audio_event',
            eventType: data.type,
            audioSessionId: audioSessionIdRef.current,
            timestamp: new Date().toISOString(),
            hasData: !!data.data
          })
        }
        
        switch (data.type) {
          case 'audio_output':
            // Handle audio output with duplicate prevention
            if (data.data) {
              // Create unique ID for this audio chunk
              const audioId = `${audioSessionIdRef.current}_${Date.now()}_${data.data.substring(0, 20)}`
              
              if (!processedAudioIds.current.has(audioId)) {
                processedAudioIds.current.add(audioId)
                await playAudioChunk(data.data)
                
                // Track successful audio play
                if (zepSessionIdRef.current) {
                  await addMessage(zepSessionIdRef.current, 'assistant', `[AUDIO_PLAYED] Chunk processed`, {
                    type: 'audio_played',
                    audioId,
                    audioSessionId: audioSessionIdRef.current,
                    timestamp: new Date().toISOString()
                  })
                }
                
                // Clean up old IDs after 10 seconds
                setTimeout(() => {
                  processedAudioIds.current.delete(audioId)
                }, 10000)
              } else {
                console.log('Skipping duplicate audio chunk')
                if (zepSessionIdRef.current) {
                  await addMessage(zepSessionIdRef.current, 'assistant', `[AUDIO_DUPLICATE] Skipped duplicate chunk`, {
                    type: 'audio_duplicate',
                    audioId,
                    audioSessionId: audioSessionIdRef.current,
                    timestamp: new Date().toISOString()
                  })
                }
              }
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
        }
      }, 100)
    } else {
      setSessionStarted(true)
      await connectToHume()
    }
  }

  const disconnectChat = async () => {
    // Track disconnection in Zep
    if (zepSessionIdRef.current) {
      await addMessage(zepSessionIdRef.current, 'assistant', `[SYSTEM] Disconnecting - Session: ${audioSessionIdRef.current}`, {
        type: 'disconnection_event',
        audioSessionId: audioSessionIdRef.current,
        timestamp: new Date().toISOString(),
        processedAudioCount: processedAudioIds.current.size
      })
      
      // Update session metadata with summary
      await updateSessionMetadata(zepSessionIdRef.current, {
        endTime: new Date().toISOString(),
        audioSessionId: audioSessionIdRef.current,
        finalCoach: currentCoach,
        finalPhase: phase,
        processedAudioCount: processedAudioIds.current.size
      })
    }
    
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
    
    // Clear processed audio IDs
    processedAudioIds.current.clear()
    
    // Generate new session ID for next connection
    audioSessionIdRef.current = Date.now().toString()
    
    console.log('Disconnected from Hume')
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
          if (event.data.size > 0) {
            // Send audio chunk immediately for real-time processing
            const reader = new FileReader()
            reader.onloadend = () => {
              const base64Audio = reader.result?.toString().split(',')[1]
              if (base64Audio && socketRef.current?.readyState === WebSocket.OPEN) {
                console.log('Sending audio chunk, size:', base64Audio.length)
                socketRef.current.send(JSON.stringify({
                  type: 'audio_input',
                  data: base64Audio
                }))
              }
            }
            reader.readAsDataURL(event.data)
          }
        }
        
        mediaRecorder.onstop = () => {
          // Stop all tracks
          stream.getTracks().forEach(track => track.stop())
        }
        
        // Start recording with continuous chunks
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
          
          {/* Main circle button */}
          <button
            onClick={toggleListening}
            disabled={!isConnected || !sessionStarted}
            className={`relative w-64 h-64 rounded-full transition-all duration-300 ${
              isListening ? 'scale-110' : 'scale-100 hover:scale-105'
            } ${
              getCoachColor() === 'purple' ? 'bg-purple-500 hover:bg-purple-600' :
              getCoachColor() === 'blue' ? 'bg-blue-500 hover:bg-blue-600' :
              'bg-green-500 hover:bg-green-600'
            } ${
              isListening ? 'animate-pulse' : ''
            } ${
              (!isConnected || !sessionStarted) ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            <div className="flex flex-col items-center justify-center h-full">
              <span className="text-6xl mb-4">{getCoachInfo().icon}</span>
              <span className="text-xl font-semibold">
                {!sessionStarted ? 'Start Session First' :
                 !isConnected ? 'Connecting...' :
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