'use client'

import { useState, useEffect, useRef } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { HUME_COACHES } from '@/lib/hume-config'
import { getOrCreateSession, addMessage, updateSessionMetadata } from '@/lib/zep'
import { globalAudioFingerprinter } from '@/lib/audio-fingerprint'
import { logger } from '@/lib/logger'
import { wsManager } from '@/lib/websocket-manager'
import { HumeAudioProcessor } from '@/lib/hume-audio-processor'

export default function TrinityPage() {
  const { isSignedIn, user } = useUser()
  const router = useRouter()
  const [isConnected, setIsConnected] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [currentCoach, setCurrentCoach] = useState<'STORY_COACH' | 'QUEST_COACH' | 'DELIVERY_COACH'>('STORY_COACH')
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
  const audioProcessorRef = useRef<HumeAudioProcessor | null>(null)

  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    }
  }, [isSignedIn, router])

  // Get access token on mount
  useEffect(() => {
    // Initialize audio processor
    audioProcessorRef.current = new HumeAudioProcessor()
    audioProcessorRef.current.setOnComplete(() => {
      console.log('[Trinity] Audio playback complete')
    })
    
    getAccessToken()
    initializeZepSession()
    
    // Cleanup on unmount
    return () => {
      disconnectChat()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

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
    // Enhanced logging for connection attempts
    const connectionAttemptId = Date.now()
    console.log(`[Trinity] Connection attempt #${connectionAttemptId} started`)
    
    // Prevent duplicate connections with ref
    if (isConnectingRef.current) {
      console.log(`[Trinity] Connection attempt #${connectionAttemptId} blocked - already connecting`)
      logger.warn('Trinity duplicate connection attempt blocked (isConnecting)', {
        attemptId: connectionAttemptId,
        isConnecting: isConnectingRef.current
      })
      return
    }
    
    // Check if WebSocket manager already has a connection
    if (wsManager.isConnected()) {
      console.log(`[Trinity] Connection attempt #${connectionAttemptId} blocked - already connected via manager`)
      logger.warn('Trinity duplicate connection attempt blocked (manager connected)', {
        attemptId: connectionAttemptId
      })
      return
    }
    
    // Clear any existing audio before new connection
    stopAllAudio()
    processedAudioIds.current.clear()
    globalAudioFingerprinter.clear()
    
    isConnectingRef.current = true
    logger.info('Trinity connection initiated', {
      attemptId: connectionAttemptId,
      audioSessionId: audioSessionIdRef.current
    })
    
    try {
      // Initialize audio context only if not already created
      if (!audioContextRef.current) {
        audioContextRef.current = new AudioContext()
        console.log('Created new AudioContext')
      }
      
      // Connect to WebSocket with EVI 3 format and config ID
      const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID
      // Add user context to the connection
      const params = new URLSearchParams({
        access_token: accessToken,
        config_id: configId || '',
        // Add user identification
        user_id: user?.id || 'anonymous',
        user_name: user?.fullName || user?.firstName || 'User',
        session_id: audioSessionIdRef.current
      })
      
      // Use WebSocket manager to ensure singleton connection
      const ws = await wsManager.connect(
        `wss://api.hume.ai/v0/evi/chat?${params.toString()}`,
        {
          onopen: async () => {
            console.log('Connected to Hume AI EVI 3 - Socket ID:', audioSessionIdRef.current)
            console.log('User context sent:', {
              userId: user?.id || 'anonymous',
              userName: user?.fullName || user?.firstName || 'User'
            })
            setIsConnected(true)
            isConnectingRef.current = false
            
            // Track connection in Zep
            if (zepSessionIdRef.current) {
              await addMessage(zepSessionIdRef.current, 'assistant', `[SYSTEM] WebSocket connection established - Session: ${audioSessionIdRef.current}`, {
                type: 'connection_event',
                audioSessionId: audioSessionIdRef.current,
                timestamp: new Date().toISOString()
              })
            }
            
            // Send initial configuration to set user context
            if (user?.id && socketRef.current) {
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
              socketRef.current.send(JSON.stringify(configMessage))
              console.log('Sent user context to Hume:', configMessage)
            }
          },
          onmessage: async (event) => {
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
                // Buffer audio chunks
                if (data.data && audioProcessorRef.current) {
                  await audioProcessorRef.current.addChunk(data.data)
                  console.log(`[Trinity] Buffered chunk ${audioProcessorRef.current.getChunkCount()}`)
                }
                break
                
              case 'assistant_message':
                // Coach is speaking
                if (data.message?.content) {
                  console.log('Coach:', data.message.content)
                  checkPhaseTransition(data.message.content)
                  
                  // Play buffered audio when assistant message arrives
                  if (audioProcessorRef.current && audioProcessorRef.current.getChunkCount() > 0) {
                    console.log('[Trinity] Playing buffered audio')
                    await audioProcessorRef.current.playAll()
                  }
                }
                break
                
              case 'assistant_end':
                // Assistant finished speaking
                console.log('[Trinity] Assistant finished speaking')
                // Play any remaining buffered audio
                if (audioProcessorRef.current && audioProcessorRef.current.getChunkCount() > 0) {
                  console.log('[Trinity] Playing remaining audio')
                  await audioProcessorRef.current.playAll()
                }
                break
                
              case 'user_message':
                // User's speech was transcribed
                console.log('User:', data.message?.content)
                break
                
              case 'user_interruption':
                // User interrupted, stop audio
                stopAllAudio()
                if (audioProcessorRef.current) {
                  audioProcessorRef.current.stop()
                }
                break
                
              case 'error': {
                const errorData = data as { error?: unknown; code?: string; message?: string; type?: string }
                console.error('[Trinity] Hume error:', errorData)
                logger.error('Trinity Hume error received', {
                  error: errorData.error,
                  code: errorData.code,
                  message: errorData.message,
                  type: errorData.type,
                  audioSessionId: audioSessionIdRef.current
                })
                
                // Don't stop audio on error - let it complete
                // The error might just be about missing user context
                console.log('[Trinity] Error received but continuing audio playback')
                break
              }
            }
          },
          onerror: (error) => {
            console.error('WebSocket error:', error)
            logger.error('Trinity WebSocket error', {
              error: error.toString(),
              attemptId: connectionAttemptId
            })
            setIsConnected(false)
            isConnectingRef.current = false
          },
          onclose: (event) => {
            console.log('WebSocket closed:', event.code, event.reason)
            logger.info('Trinity WebSocket closed', {
              code: event.code,
              reason: event.reason,
              attemptId: connectionAttemptId
            })
            setIsConnected(false)
            setIsListening(false)
            isConnectingRef.current = false
            
            // Track disconnection in Zep
            if (zepSessionIdRef.current) {
              addMessage(zepSessionIdRef.current, 'assistant', `[SYSTEM] WebSocket disconnected - Session: ${audioSessionIdRef.current}`, {
                type: 'disconnection_event',
                audioSessionId: audioSessionIdRef.current,
                timestamp: new Date().toISOString(),
                code: event.code,
                reason: event.reason
              })
            }
          }
        }
      )
      
      if (ws) {
        socketRef.current = ws
        logger.info('Trinity WebSocket connection established via manager', {
          attemptId: connectionAttemptId,
          audioSessionId: audioSessionIdRef.current
        })
      } else {
        logger.error('Trinity WebSocket connection failed', {
          attemptId: connectionAttemptId
        })
        isConnectingRef.current = false
      }
    } catch (error) {
      console.error('Failed to connect to Hume:', error)
      logger.error('Trinity connection error', {
        error: error instanceof Error ? error.message : String(error),
        attemptId: connectionAttemptId
      })
      isConnectingRef.current = false
    }
  }
  
  const playAudioChunk = async (base64Audio: string): Promise<void> => {
    if (!audioContextRef.current) {
      console.warn('[Trinity] No audio context available')
      return
    }
    
    try {
      // Decode base64 to ArrayBuffer
      const binaryString = atob(base64Audio)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      
      // Decode audio data
      const audioBuffer = await audioContextRef.current.decodeAudioData(bytes.buffer)
      
      // Create and play source
      const source = audioContextRef.current.createBufferSource()
      source.buffer = audioBuffer
      source.connect(audioContextRef.current.destination)
      
      // Track in queue
      audioQueueRef.current.push(source)
      
      source.onended = () => {
        const index = audioQueueRef.current.indexOf(source)
        if (index > -1) {
          audioQueueRef.current.splice(index, 1)
        }
      }
      
      // Play immediately
      source.start()
      console.log(`[Trinity] Audio chunk playing, duration: ${audioBuffer.duration}s`)
    } catch (error) {
      console.error('[Trinity] Audio playback error:', error)
    }
  }

  const stopAllAudio = () => {
    // Stop all playing audio
    audioQueueRef.current.forEach(source => {
      try {
        source.stop()
      } catch {
        // Ignore if already stopped
      }
    })
    audioQueueRef.current = []
    console.log('[Trinity] Stopped all audio')
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
    if (audioProcessorRef.current) {
      audioProcessorRef.current.stop()
    }
    
    // Disconnect via WebSocket manager
    wsManager.disconnect()
    socketRef.current = null
    
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
    globalAudioFingerprinter.clear()
    
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
            {phase === 'welcome' && 'Discover your professional path through conversation'}
            {phase === 'exploring' && `Speaking with ${getCoachInfo().name}`}
            {phase === 'complete' && 'Your Trinity is ready'}
          </p>
        </div>

        {/* Coach Indicator */}
        {isConnected && (
          <div className="mb-8">
            <div className={`text-6xl mb-2 ${isListening ? 'animate-pulse' : ''}`}>
              {getCoachInfo().icon}
            </div>
            <p className={`text-sm text-${getCoachColor()}-400`}>{getCoachInfo().name}</p>
          </div>
        )}

        {/* Controls */}
        <div className="space-y-4">
          {!sessionStarted ? (
            <button
              onClick={startSession}
              className="px-8 py-3 bg-purple-600 hover:bg-purple-700 rounded-full text-lg font-semibold transition-colors"
            >
              Start Trinity Discovery
            </button>
          ) : (
            <>
              {isConnected && (
                <button
                  onClick={toggleListening}
                  className={`px-8 py-3 rounded-full text-lg font-semibold transition-colors ${
                    isListening 
                      ? 'bg-red-600 hover:bg-red-700' 
                      : 'bg-green-600 hover:bg-green-700'
                  }`}
                >
                  {isListening ? 'Stop Speaking' : 'Start Speaking'}
                </button>
              )}
              
              <button
                onClick={disconnectChat}
                className="px-8 py-3 bg-gray-600 hover:bg-gray-700 rounded-full text-lg font-semibold transition-colors"
              >
                End Session
              </button>
            </>
          )}
        </div>

        {/* Status */}
        <div className="mt-8 text-sm text-gray-500">
          {!isConnected && sessionStarted && 'Connecting...'}
          {isConnected && !isListening && 'Click "Start Speaking" to begin'}
          {isConnected && isListening && 'Listening... Speak naturally'}
        </div>

        {/* Debug Links */}
        <div className="mt-12 space-x-4 text-sm">
          <a href="/trinity-debug" className="text-gray-400 hover:text-white">
            Debug (Auth)
          </a>
          <a href="/trinity-debug-public" className="text-gray-400 hover:text-white">
            Debug (Public)
          </a>
        </div>
      </div>
    </main>
  )
}