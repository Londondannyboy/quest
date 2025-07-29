'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'

// Hume message types
interface HumeMessage {
  type: string
  data?: string
  message?: {
    content?: string
  }
  error?: string
}

// Singleton WebSocket manager to prevent duplicates
class HumeWebSocketManager {
  private static instance: HumeWebSocketManager
  private ws: WebSocket | null = null
  private audioContext: AudioContext | null = null
  private mediaRecorder: MediaRecorder | null = null
  private audioQueue: AudioBufferSourceNode[] = []
  private isProcessingAudio = false
  
  static getInstance(): HumeWebSocketManager {
    if (!HumeWebSocketManager.instance) {
      HumeWebSocketManager.instance = new HumeWebSocketManager()
    }
    return HumeWebSocketManager.instance
  }
  
  async connect(
    accessToken: string,
    configId: string,
    callbacks: {
      onMessage: (data: HumeMessage) => void
      onOpen: () => void
      onClose: () => void
      onError: (error: Event) => void
    }
  ) {
    // Disconnect existing connection
    this.disconnect()
    
    // Create new WebSocket
    this.ws = new WebSocket(
      `wss://api.hume.ai/v0/evi/chat?access_token=${accessToken}&config_id=${configId}`
    )
    
    this.ws.onopen = callbacks.onOpen
    this.ws.onmessage = (event) => callbacks.onMessage(JSON.parse(event.data))
    this.ws.onclose = callbacks.onClose
    this.ws.onerror = callbacks.onError
    
    // Initialize audio context
    if (!this.audioContext) {
      this.audioContext = new AudioContext()
    }
  }
  
  disconnect() {
    // Stop recording
    if (this.mediaRecorder) {
      this.mediaRecorder.stop()
      this.mediaRecorder = null
    }
    
    // Stop all audio
    this.audioQueue.forEach(source => {
      try { source.stop() } catch {}
    })
    this.audioQueue = []
    
    // Close WebSocket
    if (this.ws && this.ws.readyState !== WebSocket.CLOSED) {
      this.ws.close()
      this.ws = null
    }
  }
  
  send(data: Record<string, unknown>) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
  
  async playAudioChunk(base64Audio: string) {
    if (!this.audioContext || this.isProcessingAudio) return
    
    this.isProcessingAudio = true
    
    try {
      const binaryString = atob(base64Audio)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      
      const audioBuffer = await this.audioContext.decodeAudioData(bytes.buffer)
      const source = this.audioContext.createBufferSource()
      source.buffer = audioBuffer
      source.connect(this.audioContext.destination)
      
      this.audioQueue.push(source)
      source.onended = () => {
        this.audioQueue = this.audioQueue.filter(s => s !== source)
      }
      
      source.start()
    } catch (error) {
      console.error('Audio playback error:', error)
    } finally {
      this.isProcessingAudio = false
    }
  }
  
  stopAudio() {
    this.audioQueue.forEach(source => {
      try { source.stop() } catch {}
    })
    this.audioQueue = []
  }
  
  async startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      this.mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0 && this.ws?.readyState === WebSocket.OPEN) {
          const reader = new FileReader()
          reader.onloadend = () => {
            const base64Audio = reader.result?.toString().split(',')[1]
            if (base64Audio) {
              this.send({
                type: 'audio_input',
                data: base64Audio
              })
            }
          }
          reader.readAsDataURL(event.data)
        }
      }
      
      this.mediaRecorder.start(100) // 100ms chunks
      return true
    } catch (error) {
      console.error('Failed to start recording:', error)
      return false
    }
  }
  
  stopRecording() {
    if (this.mediaRecorder) {
      this.mediaRecorder.stop()
      this.mediaRecorder.stream.getTracks().forEach(track => track.stop())
      this.mediaRecorder = null
    }
  }
}

export default function TrinityV2Page() {
  const { isSignedIn, user } = useUser()
  const router = useRouter()
  const [isConnected, setIsConnected] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [accessToken, setAccessToken] = useState('')
  const [transcript, setTranscript] = useState<string[]>([])
  
  const managerRef = useRef<HumeWebSocketManager | null>(null)

  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    }
  }, [isSignedIn, router])

  useEffect(() => {
    // Get singleton instance
    managerRef.current = HumeWebSocketManager.getInstance()
    
    // Get access token
    getAccessToken()
    
    return () => {
      managerRef.current?.disconnect()
    }
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

  const connect = useCallback(async () => {
    if (!accessToken || !managerRef.current) return
    
    const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID!
    
    await managerRef.current.connect(accessToken, configId, {
      onOpen: () => {
        console.log('Connected to Hume')
        setIsConnected(true)
        
        // Send user context
        if (user) {
          managerRef.current?.send({
            type: 'session_settings',
            session_settings: {
              context: {
                user_name: user.fullName || user.firstName || 'User',
                user_id: user.id
              }
            }
          })
        }
      },
      onMessage: async (data) => {
        console.log('Message:', data.type)
        
        switch (data.type) {
          case 'audio_output':
            if (data.data) {
              await managerRef.current?.playAudioChunk(data.data)
            }
            break
            
          case 'assistant_message':
            if (data.message && data.message.content) {
              setTranscript(prev => [...prev, `Coach: ${data.message.content}`])
            }
            break
            
          case 'user_message':
            if (data.message && data.message.content) {
              setTranscript(prev => [...prev, `You: ${data.message.content}`])
            }
            break
            
          case 'user_interruption':
            managerRef.current?.stopAudio()
            break
        }
      },
      onClose: () => {
        console.log('Disconnected')
        setIsConnected(false)
        setIsListening(false)
      },
      onError: (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
      }
    })
  }, [accessToken, user])

  const toggleListening = async () => {
    if (!managerRef.current) return
    
    if (isListening) {
      managerRef.current.stopRecording()
      setIsListening(false)
    } else {
      const started = await managerRef.current.startRecording()
      if (started) {
        setIsListening(true)
      }
    }
  }

  const disconnect = () => {
    managerRef.current?.disconnect()
    setIsConnected(false)
    setIsListening(false)
    setTranscript([])
  }

  return (
    <main className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Trinity Voice Coach V2 (Debug)</h1>
        
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Connection Status</h2>
          <div className="flex items-center gap-4">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
            {user && <span className="text-gray-400">({user.fullName || user.firstName})</span>}
          </div>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Controls</h2>
          <div className="flex gap-4">
            {!isConnected ? (
              <button
                onClick={connect}
                disabled={!accessToken}
                className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded disabled:opacity-50"
              >
                Connect
              </button>
            ) : (
              <>
                <button
                  onClick={toggleListening}
                  className={`px-6 py-2 rounded ${
                    isListening 
                      ? 'bg-red-600 hover:bg-red-700' 
                      : 'bg-blue-600 hover:bg-blue-700'
                  }`}
                >
                  {isListening ? 'Stop Listening' : 'Start Listening'}
                </button>
                <button
                  onClick={disconnect}
                  className="px-6 py-2 bg-gray-600 hover:bg-gray-700 rounded"
                >
                  Disconnect
                </button>
              </>
            )}
          </div>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Transcript</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {transcript.length === 0 ? (
              <p className="text-gray-400">No conversation yet...</p>
            ) : (
              transcript.map((line, i) => (
                <p key={i} className={line.startsWith('You:') ? 'text-blue-400' : 'text-green-400'}>
                  {line}
                </p>
              ))
            )}
          </div>
        </div>
        
        <div className="mt-8">
          <a href="/trinity" className="text-blue-400 hover:text-blue-300">
            ← Back to Trinity Voice Coach
          </a>
        </div>
      </div>
    </main>
  )
}