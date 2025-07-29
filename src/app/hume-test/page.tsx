'use client'

import { useState } from 'react'

export default function HumeTestPage() {
  const [status, setStatus] = useState('Ready')
  const [log, setLog] = useState<string[]>([])
  const [token, setToken] = useState('')

  const addLog = (message: string) => {
    console.log(message)
    setLog(prev => [...prev, `${new Date().toISOString()}: ${message}`])
  }

  const testTokenFetch = async () => {
    setStatus('Fetching token...')
    addLog('Starting token fetch')
    
    try {
      const response = await fetch('/api/hume/token')
      addLog(`Token response status: ${response.status}`)
      
      const data = await response.json()
      addLog(`Token response: ${JSON.stringify(data)}`)
      
      if (data.accessToken) {
        setToken(data.accessToken)
        addLog('Token received successfully')
        return data.accessToken
      } else {
        addLog('No access token in response')
        return null
      }
    } catch (error) {
      addLog(`Token fetch error: ${error}`)
      return null
    }
  }

  const testDirectConnection = async () => {
    const accessToken = await testTokenFetch()
    if (!accessToken) {
      setStatus('Failed to get token')
      return
    }

    setStatus('Connecting to Hume...')
    addLog('Creating WebSocket connection')

    try {
      const ws = new WebSocket(
        `wss://api.hume.ai/v0/evi/chat?access_token=${accessToken}`
      )

      ws.onopen = () => {
        addLog('WebSocket opened!')
        setStatus('Connected!')
        
        // Send a simple message
        const testMessage = {
          type: 'user_input',
          text: 'Hello'
        }
        addLog(`Sending: ${JSON.stringify(testMessage)}`)
        ws.send(JSON.stringify(testMessage))
      }

      ws.onmessage = (event) => {
        addLog(`Received: ${event.data}`)
        try {
          const data = JSON.parse(event.data)
          addLog(`Parsed message type: ${data.type}`)
        } catch (e) {
          addLog(`Failed to parse message: ${e}`)
        }
      }

      ws.onerror = (error) => {
        addLog(`WebSocket error: ${JSON.stringify(error)}`)
        setStatus('Connection error')
      }

      ws.onclose = (event) => {
        addLog(`WebSocket closed: code=${event.code}, reason=${event.reason}`)
        setStatus('Disconnected')
      }
    } catch (error) {
      addLog(`Connection error: ${error}`)
      setStatus('Failed to connect')
    }
  }

  const testHumeConfig = async () => {
    addLog('Testing Hume configuration...')
    
    try {
      const response = await fetch('/api/hume/debug')
      const data = await response.json()
      addLog(`Debug response: ${JSON.stringify(data, null, 2)}`)
    } catch (error) {
      addLog(`Debug error: ${error}`)
    }
  }

  return (
    <div className="min-h-screen bg-black text-white p-8">
      <h1 className="text-2xl font-bold mb-4">Hume AI Debug Test</h1>
      
      <div className="mb-4">
        <p className="text-lg">Status: <span className="text-yellow-400">{status}</span></p>
        {token && <p className="text-sm text-gray-400">Token: {token.substring(0, 20)}...</p>}
      </div>

      <div className="space-y-2 mb-8">
        <button
          onClick={testHumeConfig}
          className="bg-blue-500 px-4 py-2 rounded hover:bg-blue-600 mr-2"
        >
          Test Config
        </button>
        <button
          onClick={testTokenFetch}
          className="bg-green-500 px-4 py-2 rounded hover:bg-green-600 mr-2"
        >
          Test Token Fetch
        </button>
        <button
          onClick={testDirectConnection}
          className="bg-purple-500 px-4 py-2 rounded hover:bg-purple-600"
        >
          Test Connection
        </button>
      </div>

      <div className="bg-gray-900 p-4 rounded">
        <h2 className="text-lg font-semibold mb-2">Debug Log:</h2>
        <div className="text-xs font-mono space-y-1 max-h-96 overflow-y-auto">
          {log.map((entry, i) => (
            <div key={i} className="text-gray-300">{entry}</div>
          ))}
        </div>
      </div>
    </div>
  )
}