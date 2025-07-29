'use client'

import { useState } from 'react'

export default function HumeWebSocketTest() {
  const [status, setStatus] = useState('Not connected')
  const [logs, setLogs] = useState<string[]>([])
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [accessToken, setAccessToken] = useState('')

  const addLog = (message: string) => {
    console.log(message)
    setLogs(prev => [...prev, `${new Date().toISOString()}: ${message}`])
  }

  // Step 1: Get access token
  const getAccessToken = async () => {
    try {
      addLog('Fetching access token...')
      const response = await fetch('/api/hume/token')
      const data = await response.json()
      
      if (data.success) {
        setAccessToken(data.accessToken)
        addLog(`Access token obtained! Config ID: ${data.configId || 'NOT SET'}`)
        return data
      } else {
        addLog(`Failed to get token: ${data.error}`)
        return null
      }
    } catch (error) {
      addLog(`Token error: ${error instanceof Error ? error.message : 'Unknown'}`)
      return null
    }
  }

  // Step 2: Test REST API
  const testRestApi = async () => {
    try {
      addLog('Testing REST API connection...')
      const response = await fetch('/api/hume/test-connection')
      const data = await response.json()
      
      addLog(`REST API test: ${data.success ? 'SUCCESS' : 'FAILED'}`)
      if (data.logs) {
        data.logs.forEach((log: string) => addLog(`  > ${log}`))
      }
    } catch (error) {
      addLog(`REST API error: ${error instanceof Error ? error.message : 'Unknown'}`)
    }
  }

  // Step 3: Connect WebSocket
  const connectWebSocket = async () => {
    try {
      const tokenData = await getAccessToken()
      if (!tokenData) {
        setStatus('Failed to get token')
        return
      }

      addLog('Creating WebSocket connection...')
      setStatus('Connecting...')

      // Build WebSocket URL
      const wsUrl = tokenData.configId 
        ? `wss://api.hume.ai/v0/evi/chat?access_token=${tokenData.accessToken}&config_id=${tokenData.configId}`
        : `wss://api.hume.ai/v0/evi/chat?access_token=${tokenData.accessToken}`
      
      addLog(`WebSocket URL: wss://api.hume.ai/v0/evi/chat?access_token=***&config_id=${tokenData.configId || 'none'}`)

      const websocket = new WebSocket(wsUrl)
      
      websocket.onopen = () => {
        addLog('WebSocket opened!')
        setStatus('Connected')
        setWs(websocket)
      }

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          addLog(`Message: ${data.type || 'unknown type'}`)
          console.log('Full message:', data)
        } catch {
          addLog(`Message (raw): ${event.data}`)
        }
      }

      websocket.onerror = () => {
        addLog(`WebSocket error occurred`)
        console.error('WebSocket error occurred')
        setStatus('Error')
      }

      websocket.onclose = (event) => {
        addLog(`WebSocket closed: code=${event.code}, reason=${event.reason || 'none'}`)
        setStatus('Disconnected')
        setWs(null)
      }

    } catch (error) {
      addLog(`Connection error: ${error instanceof Error ? error.message : 'Unknown'}`)
      setStatus('Error')
    }
  }

  // Send audio input message
  const sendAudioInput = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      try {
        // Send a simple audio input message (empty for now)
        const message = {
          type: 'audio_input',
          data: '' // Would be base64 audio data
        }
        ws.send(JSON.stringify(message))
        addLog('Sent audio_input message')
      } catch (error) {
        addLog(`Send error: ${error instanceof Error ? error.message : 'Unknown'}`)
      }
    } else {
      addLog('WebSocket not connected')
    }
  }

  // Disconnect
  const disconnect = () => {
    if (ws) {
      ws.close()
      setWs(null)
      setStatus('Disconnected')
      addLog('Disconnected')
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Hume WebSocket Test (Raw)</h1>
        
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Status</h2>
          <p className={`text-lg ${
            status === 'Connected' ? 'text-green-400' : 
            status === 'Error' ? 'text-red-400' : 
            'text-yellow-400'
          }`}>
            {status}
          </p>
          {accessToken && (
            <p className="text-sm text-gray-400 mt-2">
              Token: {accessToken.substring(0, 20)}...
            </p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <button
            onClick={testRestApi}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
          >
            Test REST API
          </button>
          
          <button
            onClick={connectWebSocket}
            disabled={status === 'Connected' || status === 'Connecting...'}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 rounded-lg transition-colors"
          >
            Connect WebSocket
          </button>
          
          <button
            onClick={sendAudioInput}
            disabled={status !== 'Connected'}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 rounded-lg transition-colors"
          >
            Send Audio Input
          </button>
          
          <button
            onClick={disconnect}
            disabled={!ws}
            className="px-6 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 rounded-lg transition-colors"
          >
            Disconnect
          </button>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Logs</h2>
            <button
              onClick={() => setLogs([])}
              className="text-sm text-gray-400 hover:text-white"
            >
              Clear
            </button>
          </div>
          <div className="font-mono text-sm space-y-1 max-h-96 overflow-y-auto">
            {logs.length === 0 ? (
              <p className="text-gray-500">No logs yet...</p>
            ) : (
              logs.map((log, index) => (
                <div key={index} className="text-gray-300">
                  {log}
                </div>
              ))
            )}
          </div>
        </div>

        <div className="mt-6 text-sm text-gray-500">
          <p>This page tests raw WebSocket connection to Hume EVI.</p>
          <p>1. Click &quot;Test REST API&quot; to verify credentials</p>
          <p>2. Click &quot;Connect WebSocket&quot; to establish connection</p>
          <p>3. Check browser console for detailed logs</p>
        </div>
      </div>
    </div>
  )
}