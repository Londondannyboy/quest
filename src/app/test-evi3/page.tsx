'use client'

import { useState, useRef, useEffect } from 'react'

export default function TestEVI3Page() {
  const [status, setStatus] = useState('Initializing...')
  const [isConnected, setIsConnected] = useState(false)
  const [messages, setMessages] = useState<string[]>([])
  const socketRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)

  const log = (msg: string) => {
    console.log(msg)
    setMessages(prev => [...prev, `${new Date().toLocaleTimeString()}: ${msg}`])
  }

  useEffect(() => {
    connectToHume()
    return () => {
      if (socketRef.current) {
        socketRef.current.close()
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const connectToHume = async () => {
    try {
      log('Fetching access token...')
      const tokenResponse = await fetch('/api/hume/token')
      
      if (!tokenResponse.ok) {
        log(`Token fetch failed: ${tokenResponse.status}`)
        setStatus('Token fetch failed')
        return
      }

      const { accessToken } = await tokenResponse.json()
      log('Access token received')

      // Initialize audio context
      audioContextRef.current = new AudioContext()
      log('Audio context created')

      // Get config ID from environment
      const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID
      const wsUrl = `wss://api.hume.ai/v0/evi/chat?access_token=${accessToken}&config_id=${configId}`
      
      log('Connecting to Hume...')
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        log('✅ Connected to Hume AI!')
        setIsConnected(true)
        setStatus('Connected - Click to speak')
      }

      ws.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data)
          log(`Received: ${data.type}`)

          if (data.type === 'audio_output' && data.data) {
            // Play audio
            const audioData = atob(data.data)
            const audioBytes = new Uint8Array(audioData.length)
            for (let i = 0; i < audioData.length; i++) {
              audioBytes[i] = audioData.charCodeAt(i)
            }

            try {
              const audioBuffer = await audioContextRef.current!.decodeAudioData(audioBytes.buffer)
              const source = audioContextRef.current!.createBufferSource()
              source.buffer = audioBuffer
              source.connect(audioContextRef.current!.destination)
              source.start()
              log('Audio playing')
            } catch (e) {
              log(`Audio decode error: ${e}`)
            }
          }

          if (data.type === 'assistant_message') {
            log(`Assistant: ${data.message?.content || 'No content'}`)
          }

          if (data.type === 'error') {
            log(`Error: ${JSON.stringify(data)}`)
          }
        } catch (e) {
          log(`Message parse error: ${e}`)
        }
      }

      ws.onerror = (error) => {
        log(`WebSocket error: ${error}`)
        setStatus('Connection error')
      }

      ws.onclose = (event) => {
        log(`Disconnected: ${event.code} - ${event.reason}`)
        setIsConnected(false)
        setStatus('Disconnected')
      }

      socketRef.current = ws
    } catch (error) {
      log(`Connection error: ${error}`)
      setStatus('Failed to connect')
    }
  }

  const sendAudio = async () => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      log('Not connected')
      return
    }

    try {
      log('Getting microphone...')
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      const chunks: Blob[] = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data)
      }

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' })
        const reader = new FileReader()
        
        reader.onloadend = () => {
          const base64 = reader.result?.toString().split(',')[1]
          if (base64) {
            socketRef.current!.send(JSON.stringify({
              type: 'audio_input',
              data: base64
            }))
            log('Audio sent')
          }
        }
        
        reader.readAsDataURL(blob)
        stream.getTracks().forEach(track => track.stop())
      }

      log('Recording for 3 seconds...')
      mediaRecorder.start()
      
      setTimeout(() => {
        mediaRecorder.stop()
        log('Recording stopped')
      }, 3000)
    } catch (error) {
      log(`Microphone error: ${error}`)
    }
  }

  const sendText = () => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      log('Not connected')
      return
    }

    const message = {
      type: 'user_input',
      text: 'Hello, can you hear me?'
    }
    
    socketRef.current.send(JSON.stringify(message))
    log(`Sent: ${JSON.stringify(message)}`)
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <h1 className="text-2xl font-bold mb-4">EVI 3 Test - Config: 671d99bc</h1>
      
      <div className="mb-6">
        <p className="text-lg mb-2">Status: <span className="text-green-400">{status}</span></p>
        <p className="text-sm text-gray-400">Using &quot;Inspired Man&quot; voice</p>
      </div>

      <div className="space-x-4 mb-8">
        <button
          onClick={sendText}
          disabled={!isConnected}
          className="bg-blue-500 px-4 py-2 rounded disabled:opacity-50"
        >
          Send Text Message
        </button>
        
        <button
          onClick={sendAudio}
          disabled={!isConnected}
          className="bg-purple-500 px-4 py-2 rounded disabled:opacity-50"
        >
          Record 3s Audio
        </button>
        
        <button
          onClick={connectToHume}
          className="bg-green-500 px-4 py-2 rounded"
        >
          Reconnect
        </button>
      </div>

      <div className="bg-gray-800 p-4 rounded">
        <h2 className="font-semibold mb-2">Debug Log:</h2>
        <div className="text-xs font-mono space-y-1 max-h-64 overflow-y-auto">
          {messages.map((msg, i) => (
            <div key={i}>{msg}</div>
          ))}
        </div>
      </div>
    </div>
  )
}