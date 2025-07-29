'use client'

import { useState } from 'react'

export default function HumeSimplePage() {
  const [status, setStatus] = useState('Ready to test')
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [messages, setMessages] = useState<string[]>([])

  const addMessage = (msg: string) => {
    console.log(msg)
    setMessages(prev => [...prev, msg])
  }

  const testMinimalConnection = async () => {
    setStatus('Testing...')
    addMessage('Starting minimal connection test')

    // First, let's check if we can even reach Hume's API
    try {
      // Test 1: Can we reach Hume's API at all?
      addMessage('Test 1: Checking Hume API availability...')
      const testResponse = await fetch('https://api.hume.ai/v0/evi/tools', {
        method: 'GET',
        headers: {
          'X-Hume-Api-Key': 'test' // This will fail but we can see the response
        }
      }).catch(err => {
        addMessage(`Hume API unreachable: ${err.message}`)
        return null
      })

      if (testResponse) {
        addMessage(`Hume API response: ${testResponse.status} ${testResponse.statusText}`)
      }

      // Test 2: Check our environment setup
      addMessage('\nTest 2: Checking environment...')
      const envCheck = {
        hasApiKey: !!process.env.NEXT_PUBLIC_HUME_API_KEY,
        hasSecret: !!process.env.NEXT_PUBLIC_HUME_SECRET_KEY,
        nodeEnv: process.env.NODE_ENV
      }
      addMessage(`Environment: ${JSON.stringify(envCheck)}`)

      // Test 3: Try a basic WebSocket connection (will fail without auth)
      addMessage('\nTest 3: Testing WebSocket...')
      const testWs = new WebSocket('wss://api.hume.ai/v0/evi/chat')
      
      testWs.onopen = () => {
        addMessage('WebSocket opened (unexpected)')
      }
      
      testWs.onerror = (error) => {
        addMessage('WebSocket error (expected without auth)')
      }
      
      testWs.onclose = (event) => {
        addMessage(`WebSocket closed: ${event.code} - ${event.reason}`)
      }

      // Test 4: Manual token request
      addMessage('\nTest 4: Manual token request...')
      if (process.env.NEXT_PUBLIC_HUME_API_KEY && process.env.NEXT_PUBLIC_HUME_SECRET_KEY) {
        const tokenBody = new URLSearchParams({
          grant_type: 'client_credentials',
          client_id: process.env.NEXT_PUBLIC_HUME_API_KEY,
          client_secret: process.env.NEXT_PUBLIC_HUME_SECRET_KEY
        })

        addMessage(`Token request body: ${tokenBody.toString().substring(0, 50)}...`)
        
        const tokenResponse = await fetch('https://api.hume.ai/oauth2-cc/token', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: tokenBody
        })

        addMessage(`Token response: ${tokenResponse.status} ${tokenResponse.statusText}`)
        
        if (tokenResponse.ok) {
          const tokenData = await tokenResponse.json()
          addMessage(`Token received! Type: ${tokenData.token_type}`)
          addMessage(`Access token: ${tokenData.access_token?.substring(0, 20)}...`)
          
          // Test 5: Connect with token
          addMessage('\nTest 5: Connecting with token...')
          const authWs = new WebSocket(
            `wss://api.hume.ai/v0/evi/chat?access_token=${tokenData.access_token}`
          )
          
          authWs.onopen = () => {
            addMessage('✅ WebSocket connected with auth!')
            setStatus('Connected!')
            setWs(authWs)
            
            // Send initial config
            const config = {
              type: 'session_settings',
              session_settings: {
                type: 'session_settings',
                system_prompt: 'You are a helpful assistant.',
                voice: {
                  provider: 'hume_ai',
                  voice_id: 'kora'
                }
              }
            }
            addMessage(`Sending config: ${JSON.stringify(config)}`)
            authWs.send(JSON.stringify(config))
          }
          
          authWs.onmessage = (event) => {
            addMessage(`Message received: ${event.data}`)
          }
          
          authWs.onerror = (error) => {
            addMessage(`Auth WebSocket error: ${error}`)
          }
          
          authWs.onclose = (event) => {
            addMessage(`Auth WebSocket closed: ${event.code} - ${event.reason}`)
            setStatus('Disconnected')
          }
        } else {
          const errorText = await tokenResponse.text()
          addMessage(`Token error: ${errorText}`)
        }
      } else {
        addMessage('⚠️ Missing API credentials in environment variables')
        addMessage('Please set NEXT_PUBLIC_HUME_API_KEY and NEXT_PUBLIC_HUME_SECRET_KEY')
      }

    } catch (error) {
      addMessage(`Error: ${error}`)
      setStatus('Error')
    }
  }

  const sendTestMessage = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      const msg = {
        type: 'user_input',
        text: 'Hello, can you hear me?'
      }
      addMessage(`Sending: ${JSON.stringify(msg)}`)
      ws.send(JSON.stringify(msg))
    } else {
      addMessage('WebSocket not connected')
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <h1 className="text-3xl font-bold mb-6">Hume AI Simple Test</h1>
      
      <div className="mb-6">
        <p className="text-xl mb-4">Status: <span className="text-yellow-400">{status}</span></p>
        
        <button
          onClick={testMinimalConnection}
          className="bg-blue-500 px-6 py-3 rounded-lg hover:bg-blue-600 mr-4"
        >
          Run Connection Test
        </button>
        
        <button
          onClick={sendTestMessage}
          disabled={!ws || ws.readyState !== WebSocket.OPEN}
          className="bg-green-500 px-6 py-3 rounded-lg hover:bg-green-600 disabled:opacity-50"
        >
          Send Test Message
        </button>
      </div>

      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Debug Messages:</h2>
        <div className="font-mono text-sm space-y-2 max-h-96 overflow-y-auto">
          {messages.map((msg, i) => (
            <div key={i} className="text-gray-300 whitespace-pre-wrap">{msg}</div>
          ))}
        </div>
      </div>

      <div className="mt-6 text-sm text-gray-400">
        <p>This page tests the Hume AI connection step by step:</p>
        <ol className="list-decimal list-inside mt-2 space-y-1">
          <li>Check if Hume API is reachable</li>
          <li>Verify environment variables are loaded</li>
          <li>Test basic WebSocket connectivity</li>
          <li>Request OAuth token</li>
          <li>Connect with authentication</li>
        </ol>
      </div>
    </div>
  )
}