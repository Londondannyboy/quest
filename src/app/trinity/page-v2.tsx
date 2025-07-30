'use client'

import { useState, useEffect, useCallback } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { TrinityCoachCircle } from '@/components/trinity/TrinityCoachCircle'
import { TrinityControls } from '@/components/trinity/TrinityControls'
import { useHumeConnection } from '@/hooks/useHumeConnection'
import { useAudioContext } from '@/hooks/useAudioContext'
import { getOrCreateSession, addMessage } from '@/lib/zep'
import { logger } from '@/lib/logger'

const COACHES = {
  STORY: { name: 'Story Coach', color: 'purple', icon: '📖' },
  QUEST: { name: 'Quest Coach', color: 'blue', icon: '🎯' },
  DELIVERY: { name: 'Delivery Coach', color: 'green', icon: '🚀' },
}

export default function TrinityPageV2() {
  const { isSignedIn, user } = useUser()
  const router = useRouter()
  
  // State
  const [currentCoach, setCurrentCoach] = useState<keyof typeof COACHES>('STORY')
  const [phase, setPhase] = useState<'welcome' | 'exploring' | 'complete'>('welcome')
  const [sessionStarted, setSessionStarted] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [showTranscript, setShowTranscript] = useState(false)
  const [transcript, setTranscript] = useState<string[]>([])
  const [zepSessionId, setZepSessionId] = useState<string | null>(null)
  
  // Hooks
  const { playAudioChunk, stopAllAudio } = useAudioContext()
  
  const {
    isConnected,
    connect,
    disconnect,
    sendMessage,
  } = useHumeConnection({
    onAudioOutput: playAudioChunk,
    onMessage: (data: unknown) => {
      const message = data as { type: string; message?: { content?: string } }
      switch (message.type) {
        case 'assistant_message': {
          const content = message.message?.content
          if (content) {
            setTranscript(prev => [...prev, `Coach: ${content}`])
            checkPhaseTransition(content)
          }
          break
        }
          
        case 'user_message': {
          const content = message.message?.content
          if (content) {
            setTranscript(prev => [...prev, `You: ${content}`])
          }
          break
        }
          
        case 'user_interruption':
          stopAllAudio()
          break
          
        case 'error': {
          const errorData = data as { error?: unknown }
          logger.error('Hume error', errorData.error)
          break
        }
      }
    },
  })
  
  // Auth check
  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    }
  }, [isSignedIn, router])
  
  // Initialize Zep session
  useEffect(() => {
    const initSession = async () => {
      if (!user?.id) return
      
      try {
        const response = await fetch('/api/user/profile')
        const userData = await response.json()
        
        if (userData.id) {
          const session = await getOrCreateSession(userData.id, 'trinity', {
            coachType: 'trinity_discovery',
            startTime: new Date().toISOString(),
          })
          setZepSessionId(session.sessionId || null)
        }
      } catch (error) {
        logger.error('Failed to initialize Zep session', error)
      }
    }
    
    initSession()
  }, [user])
  
  // Phase transition logic
  const checkPhaseTransition = useCallback((message: string) => {
    const lowerMessage = message.toLowerCase()
    
    if (lowerMessage.includes('trinity') && currentCoach === 'STORY') {
      setCurrentCoach('QUEST')
      setPhase('exploring')
    } else if (lowerMessage.includes('ready') && currentCoach === 'QUEST') {
      setCurrentCoach('DELIVERY')
      setPhase('complete')
    }
  }, [currentCoach])
  
  // Toggle listening
  const toggleListening = useCallback(async () => {
    if (isListening) {
      sendMessage({ type: 'pause_assistant' })
      setIsListening(false)
    } else {
      sendMessage({ type: 'resume_assistant' })
      setIsListening(true)
      
      // Click-to-talk simulation
      setTimeout(() => {
        sendMessage({ type: 'audio_input', data: '' })
        setIsListening(false)
      }, 3000)
    }
  }, [isListening, sendMessage])
  
  // Toggle session
  const toggleSession = useCallback(async () => {
    if (sessionStarted) {
      disconnect()
      setSessionStarted(false)
      setIsListening(false)
      stopAllAudio()
    } else {
      setSessionStarted(true)
      await connect()
    }
  }, [sessionStarted, connect, disconnect, stopAllAudio])
  
  // Track events in Zep
  useEffect(() => {
    if (!zepSessionId || !isConnected) return
    
    addMessage(zepSessionId, 'assistant', `[SYSTEM] Connected to ${currentCoach}`, {
      type: 'coach_change',
      coach: currentCoach,
      phase,
    })
  }, [currentCoach, phase, zepSessionId, isConnected])
  
  const coachInfo = COACHES[currentCoach]
  
  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white flex items-center justify-center">
      <div className="text-center">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Trinity Discovery</h1>
          <p className="text-xl text-gray-400">
            {!sessionStarted
              ? 'Click Start Session to begin'
              : !isConnected
              ? 'Connecting to your coach...'
              : phase === 'welcome'
              ? 'Click the circle to speak'
              : `Speaking with ${coachInfo.name}`}
          </p>
        </div>
        
        {/* Coach Circle */}
        <TrinityCoachCircle
          isListening={isListening}
          isConnected={isConnected}
          sessionStarted={sessionStarted}
          coachInfo={coachInfo}
          onToggleListening={toggleListening}
        />
        
        {/* Controls */}
        <TrinityControls
          sessionStarted={sessionStarted}
          onToggleSession={toggleSession}
          showTranscript={showTranscript}
          onToggleTranscript={() => setShowTranscript(!showTranscript)}
        />
        
        {/* Transcript */}
        {showTranscript && transcript.length > 0 && (
          <div className="mt-8 max-w-2xl mx-auto bg-gray-800 rounded-lg p-4 max-h-64 overflow-y-auto">
            {transcript.map((line, i) => (
              <p key={i} className="text-left mb-2">
                {line}
              </p>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}