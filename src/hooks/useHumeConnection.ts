import { useState, useRef, useCallback, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import { logger } from '@/lib/logger'

interface UseHumeConnectionOptions {
  configId?: string
  onMessage?: (data: unknown) => void
  onAudioOutput?: (audioData: string) => void
  onError?: (error: Error) => void
  onConnect?: () => void
  onDisconnect?: () => void
}

export function useHumeConnection(options: UseHumeConnectionOptions = {}) {
  const { user } = useUser()
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [accessToken, setAccessToken] = useState<string>('')
  const socketRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined)
  
  // Get access token
  const getAccessToken = useCallback(async () => {
    try {
      const response = await fetch('/api/hume/token')
      const data = await response.json()
      if (data.accessToken) {
        setAccessToken(data.accessToken)
        return data.accessToken
      }
    } catch (error) {
      logger.error('Failed to get access token', error)
    }
    return null
  }, [])
  
  // Connect to WebSocket
  const connect = useCallback(async () => {
    if (isConnecting || socketRef.current?.readyState === WebSocket.OPEN) {
      return
    }
    
    setIsConnecting(true)
    
    const token = accessToken || await getAccessToken()
    if (!token) {
      setIsConnecting(false)
      return
    }
    
    try {
      const configId = options.configId || process.env.NEXT_PUBLIC_HUME_CONFIG_ID
      const params = new URLSearchParams({
        access_token: token,
        config_id: configId || '',
        user_id: user?.id || 'anonymous',
        user_name: user?.fullName || user?.firstName || 'User',
      })
      
      const ws = new WebSocket(`wss://api.hume.ai/v0/evi/chat?${params}`)
      
      ws.onopen = () => {
        logger.ws('Connected to Hume', { userId: user?.id })
        setIsConnected(true)
        setIsConnecting(false)
        options.onConnect?.()
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'audio_output' && data.data) {
            options.onAudioOutput?.(data.data)
          }
          
          options.onMessage?.(data)
        } catch (error) {
          logger.error('Failed to parse WebSocket message', error)
        }
      }
      
      ws.onerror = (error) => {
        logger.error('WebSocket error', error)
        options.onError?.(new Error('WebSocket error'))
      }
      
      ws.onclose = () => {
        logger.ws('Disconnected from Hume')
        setIsConnected(false)
        setIsConnecting(false)
        socketRef.current = null
        options.onDisconnect?.()
        
        // Auto-reconnect in production
        if (process.env.NODE_ENV === 'production') {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, 5000)
        }
      }
      
      socketRef.current = ws
    } catch (error) {
      logger.error('Failed to connect to Hume', error)
      setIsConnecting(false)
      options.onError?.(error as Error)
    }
  }, [accessToken, user, options, getAccessToken])
  
  // Disconnect
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    
    if (socketRef.current) {
      socketRef.current.close()
      socketRef.current = null
    }
    
    setIsConnected(false)
  }, [])
  
  // Send message
  const sendMessage = useCallback((message: unknown) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(message))
    } else {
      logger.warn('Cannot send message: WebSocket not connected')
    }
  }, [])
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])
  
  // Initialize access token
  useEffect(() => {
    getAccessToken()
  }, [getAccessToken])
  
  return {
    isConnected,
    isConnecting,
    connect,
    disconnect,
    sendMessage,
    socket: socketRef.current,
  }
}