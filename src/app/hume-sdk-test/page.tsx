'use client'

import { useState } from 'react'
import { HumeClient } from 'hume'

export default function HumeSdkTest() {
  const [status, setStatus] = useState('Not connected')
  const [logs, setLogs] = useState<string[]>([])
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [socket, setSocket] = useState<any>(null)

  const addLog = (message: string) => {
    console.log(message)
    setLogs(prev => [...prev, `${new Date().toISOString()}: ${message}`])
  }

  const connectToHume = async () => {
    try {
      addLog('Starting connection...')
      setStatus('Connecting...')

      // Get access token from our API
      const tokenResponse = await fetch('/api/hume/token')
      const tokenData = await tokenResponse.json()
      
      if (!tokenData.success) {
        throw new Error(tokenData.error || 'Failed to get access token')
      }

      addLog(`Access token obtained: ${tokenData.accessToken ? 'YES' : 'NO'}`)
      addLog(`Config ID: ${tokenData.configId || 'NOT SET'}`)

      // Create Hume client
      const client = new HumeClient({
        apiKey: tokenData.accessToken, // Use the access token as API key
      })

      addLog('Connecting to EVI chat...')
      
      // Connect to EVI
      const chatSocket = await client.empathicVoice.chat.connect({
        configId: tokenData.configId,
      })

      addLog('WebSocket connected!')
      setSocket(chatSocket)
      setStatus('Connected')

      // Set up event handlers
      chatSocket.on('open', () => {
        addLog('Socket opened')
        setStatus('Connected - Ready')
      })

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      chatSocket.on('message', (msg: any) => {
        addLog(`Message received: ${msg.type}`)
        console.log('Full message:', msg)
      })

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      chatSocket.on('error', (error: any) => {
        addLog(`Error: ${error.message || JSON.stringify(error)}`)
        setStatus('Error')
      })

      chatSocket.on('close', () => {
        addLog('Socket closed')
        setStatus('Disconnected')
      })

    } catch (error) {
      addLog(`Connection error: ${error instanceof Error ? error.message : 'Unknown error'}`)
      setStatus('Error')
      console.error('Full error:', error)
    }
  }

  const sendTestMessage = () => {
    if (socket) {
      try {
        socket.sendUserInput('Hello, this is a test message from Quest Core!')
        addLog('Test message sent')
      } catch (error) {
        addLog(`Send error: ${error instanceof Error ? error.message : 'Unknown error'}`)
      }
    } else {
      addLog('No socket connection')
    }
  }

  const disconnect = () => {
    if (socket) {
      socket.close()
      setSocket(null)
      setStatus('Disconnected')
      addLog('Disconnected')
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Hume SDK Test</h1>
        
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Connection Status</h2>
          <p className={`text-lg ${
            status === 'Connected' || status === 'Connected - Ready' ? 'text-green-400' : 
            status === 'Error' ? 'text-red-400' : 
            'text-yellow-400'
          }`}>
            {status}
          </p>
        </div>

        <div className="flex gap-4 mb-6">
          <button
            onClick={connectToHume}
            disabled={status === 'Connected' || status === 'Connected - Ready' || status === 'Connecting...'}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 rounded-lg transition-colors"
          >
            Connect to Hume
          </button>
          
          <button
            onClick={sendTestMessage}
            disabled={status !== 'Connected - Ready'}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 rounded-lg transition-colors"
          >
            Send Test Message
          </button>
          
          <button
            onClick={disconnect}
            disabled={!socket}
            className="px-6 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 rounded-lg transition-colors"
          >
            Disconnect
          </button>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Logs</h2>
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
          <p>This page tests the Hume SDK connection without authentication.</p>
          <p>Check the browser console for detailed logs.</p>
        </div>
      </div>
    </div>
  )
}