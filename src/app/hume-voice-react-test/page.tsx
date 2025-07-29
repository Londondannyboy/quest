'use client'

import { VoiceProvider, useVoice } from '@humeai/voice-react'
import { useEffect, useState } from 'react'

function VoiceComponent() {
  const { connect, disconnect, status, messages } = useVoice()
  const [logs, setLogs] = useState<string[]>([])

  useEffect(() => {
    const log = `Status: ${status.value}`
    setLogs(prev => [...prev, log])
    console.log(log)
  }, [status.value])

  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1]
      const log = `Message: ${lastMessage.type}`
      setLogs(prev => [...prev, log])
      console.log('Full message:', lastMessage)
    }
  }, [messages])

  const handleConnect = async () => {
    try {
      // Get access token from our API
      const response = await fetch('/api/hume/token')
      const data = await response.json()
      
      if (!data.success) {
        throw new Error(data.error || 'Failed to get access token')
      }

      await connect()
      // Note: We're not passing accessToken/configId here as they might 
      // be handled differently in the VoiceProvider
    } catch (error) {
      console.error('Connection error:', error)
      setLogs(prev => [...prev, `Error: ${error instanceof Error ? error.message : 'Unknown'}`])
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Hume Voice React Test</h1>
      
      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Status</h2>
        <p className={`text-lg ${
          status.value === 'connected' ? 'text-green-400' : 
          status.value === 'error' ? 'text-red-400' : 
          status.value === 'connecting' ? 'text-yellow-400' :
          'text-gray-400'
        }`}>
          {status.value}
        </p>
      </div>

      <div className="flex gap-4 mb-6">
        <button
          onClick={handleConnect}
          disabled={status.value === 'connected' || status.value === 'connecting'}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 rounded-lg transition-colors"
        >
          Connect
        </button>
        
        <button
          onClick={disconnect}
          disabled={status.value !== 'connected'}
          className="px-6 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 rounded-lg transition-colors"
        >
          Disconnect
        </button>
      </div>

      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Messages</h2>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {messages.length === 0 ? (
            <p className="text-gray-500">No messages yet...</p>
          ) : (
            messages.slice(-10).map((msg, index) => (
              <div key={index} className="text-sm">
                <span className="text-gray-400">{msg.type}:</span>{' '}
                <span className="text-gray-300">
                  {msg.type === 'user_message' || msg.type === 'assistant_message' 
                    ? msg.message?.content || 'No content'
                    : 'Audio/System message'}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Logs</h2>
        <div className="font-mono text-sm space-y-1 max-h-48 overflow-y-auto">
          {logs.map((log, index) => (
            <div key={index} className="text-gray-300">{log}</div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function HumeVoiceReactTest() {
  const [apiKey, setApiKey] = useState<string>('')
  const [configId, setConfigId] = useState<string>('')
  const [showProvider, setShowProvider] = useState(false)

  const handleSetup = async () => {
    try {
      const response = await fetch('/api/hume/token')
      const data = await response.json()
      
      if (data.success) {
        // We'll use the access token for now
        setApiKey(data.accessToken)
        setConfigId(data.configId || '')
        setShowProvider(true)
      } else {
        console.error('Failed to get token:', data.error)
      }
    } catch (error) {
      console.error('Setup error:', error)
    }
  }

  if (!showProvider) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">Hume Voice React Test</h1>
          <button
            onClick={handleSetup}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg"
          >
            Initialize Voice Provider
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <VoiceProvider
        auth={{ type: 'accessToken', value: apiKey }}
        configId={configId}
        onError={(error) => {
          console.error('VoiceProvider error:', error)
        }}
      >
        <VoiceComponent />
      </VoiceProvider>
    </div>
  )
}