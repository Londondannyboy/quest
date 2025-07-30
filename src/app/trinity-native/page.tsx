'use client'

import { useEffect, useState } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { VoiceProvider, useVoice } from '@humeai/voice-react'
import { HUME_COACHES } from '@/lib/hume-config'

function TrinityVoiceInterface() {
  const { connect, disconnect, status, messages } = useVoice()
  const [currentCoach] = useState<'STORY_COACH' | 'QUEST_COACH' | 'DELIVERY_COACH'>('STORY_COACH')
  
  // Extract conversation from messages
  const conversation = messages.filter(msg => 
    msg.type === 'user_message' || msg.type === 'assistant_message'
  )
  
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
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-center">Trinity Native SDK</h1>
      
      {/* Status */}
      <div className="bg-gray-800 p-6 rounded-lg mb-8">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-sm text-gray-400">Connection</p>
            <p className={`text-xl font-bold ${
              status.value === 'connected' ? 'text-green-500' : 
              status.value === 'connecting' ? 'text-yellow-500' :
              'text-red-500'
            }`}>
              {status.value}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Microphone</p>
            <p className={`text-xl font-bold ${
              status.value === 'connected' ? 'text-green-500' : 'text-gray-500'
            }`}>
              {status.value === 'connected' ? 'Active' : 'Inactive'}
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
        {status.value !== 'connected' ? (
          <button
            onClick={async () => {
              const apiKey = process.env.NEXT_PUBLIC_HUME_API_KEY
              const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID
              if (!apiKey) {
                console.error('Hume API key not configured')
                return
              }
              await connect({
                auth: { type: 'apiKey', value: apiKey },
                configId: configId || undefined
              })
            }}
            disabled={status.value === 'connecting'}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50"
          >
            {status.value === 'connecting' ? 'Connecting...' : 'Connect to Hume'}
          </button>
        ) : (
          <button
            onClick={() => disconnect()}
            className="px-6 py-3 bg-red-600 hover:bg-red-700 rounded-lg"
          >
            Disconnect
          </button>
        )}
      </div>
      
      {/* Error Display */}
      {status.value === 'error' && (
        <div className="bg-red-900/50 border border-red-600 text-red-200 p-4 rounded mb-6">
          {status.reason || 'Connection error occurred'}
        </div>
      )}
      
      {/* Transcript */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Conversation</h2>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {conversation.length === 0 ? (
            <p className="text-gray-500">No conversation yet...</p>
          ) : (
            conversation.map((msg, i) => {
              const isUser = msg.type === 'user_message'
              const content = 'message' in msg ? msg.message?.content : ''
              
              return content ? (
                <p key={i} className={isUser ? 'text-blue-400' : 'text-green-400'}>
                  {isUser ? 'You: ' : 'Coach: '}{content}
                </p>
              ) : null
            })
          )}
        </div>
      </div>
      
      {/* Debug Info */}
      <div className="mt-8 text-sm text-gray-500 text-center">
        <p>Using @humeai/voice-react native SDK</p>
        <p>Automatic audio handling and state management</p>
      </div>
    </div>
  )
}

export default function TrinityNativePage() {
  const { isSignedIn } = useUser()
  const router = useRouter()
  const [accessToken, setAccessToken] = useState<string>('')
  
  // Redirect if not signed in
  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    }
  }, [isSignedIn, router])
  
  // Get access token
  useEffect(() => {
    const getToken = async () => {
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
    getToken()
  }, [])
  
  if (!accessToken) {
    return (
      <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white p-8 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Loading...</h1>
          <p className="text-gray-400">Getting access token...</p>
        </div>
      </main>
    )
  }
  
  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white p-8">
      <VoiceProvider
        onMessage={(message) => {
          console.log('[Trinity Native] Message:', message)
        }}
        onError={(error) => {
          console.error('[Trinity Native] Error:', error)
        }}
        onClose={() => {
          console.log('[Trinity Native] Connection closed')
        }}
      >
        <TrinityVoiceInterface />
      </VoiceProvider>
    </main>
  )
}