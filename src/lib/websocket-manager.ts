/**
 * Global WebSocket Manager
 * Ensures only one WebSocket connection to Hume at a time
 */

class WebSocketManager {
  private static instance: WebSocketManager
  private ws: WebSocket | null = null
  private isConnecting = false
  private connectionId = 0
  
  private constructor() {}
  
  static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager()
    }
    return WebSocketManager.instance
  }
  
  async connect(
    url: string,
    handlers: {
      onopen?: (event: Event) => void
      onmessage?: (event: MessageEvent) => void
      onerror?: (event: Event) => void
      onclose?: (event: CloseEvent) => void
    }
  ): Promise<WebSocket | null> {
    // If already connected, close existing connection
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('[WSManager] Closing existing connection')
      this.ws.close()
      await new Promise(resolve => setTimeout(resolve, 100))
    }
    
    // If already connecting, wait
    if (this.isConnecting) {
      console.log('[WSManager] Connection already in progress, waiting...')
      await new Promise(resolve => setTimeout(resolve, 500))
      return this.ws
    }
    
    this.isConnecting = true
    this.connectionId++
    const connId = this.connectionId
    
    try {
      console.log(`[WSManager] Creating new connection #${connId}`)
      this.ws = new WebSocket(url)
      
      // Set up handlers
      this.ws.onopen = (event) => {
        console.log(`[WSManager] Connection #${connId} opened`)
        this.isConnecting = false
        handlers.onopen?.(event)
      }
      
      this.ws.onmessage = (event) => {
        handlers.onmessage?.(event)
      }
      
      this.ws.onerror = (event) => {
        console.error(`[WSManager] Connection #${connId} error`)
        this.isConnecting = false
        handlers.onerror?.(event)
      }
      
      this.ws.onclose = (event) => {
        console.log(`[WSManager] Connection #${connId} closed`)
        this.isConnecting = false
        if (this.ws?.readyState === WebSocket.CLOSED) {
          this.ws = null
        }
        handlers.onclose?.(event)
      }
      
      return this.ws
    } catch (error) {
      console.error(`[WSManager] Failed to create connection #${connId}:`, error)
      this.isConnecting = false
      return null
    }
  }
  
  disconnect() {
    if (this.ws) {
      console.log('[WSManager] Disconnecting')
      this.ws.close()
      this.ws = null
    }
  }
  
  getConnection(): WebSocket | null {
    return this.ws
  }
  
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

export const wsManager = WebSocketManager.getInstance()