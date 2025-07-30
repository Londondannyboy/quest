/**
 * Audio Buffer Manager
 * Handles buffering and concatenation of audio chunks from Hume
 */

export class AudioBufferManager {
  private audioChunks: Map<string, { chunks: string[]; timestamp: number; messageId?: string }> = new Map()
  private readonly BUFFER_TIMEOUT = 500 // Wait 500ms for all chunks before playing
  private timeoutHandles: Map<string, NodeJS.Timeout> = new Map()
  
  /**
   * Add an audio chunk to the buffer
   */
  addChunk(sessionId: string, audioData: string, messageId?: string): void {
    const key = `${sessionId}_${messageId || 'default'}`
    
    if (!this.audioChunks.has(key)) {
      this.audioChunks.set(key, {
        chunks: [],
        timestamp: Date.now(),
        messageId
      })
    }
    
    const buffer = this.audioChunks.get(key)!
    buffer.chunks.push(audioData)
    
    // Clear existing timeout
    const existingTimeout = this.timeoutHandles.get(key)
    if (existingTimeout) {
      clearTimeout(existingTimeout)
    }
    
    // Set new timeout to process chunks
    const timeout = setTimeout(() => {
      this.processBuffer(key)
    }, this.BUFFER_TIMEOUT)
    
    this.timeoutHandles.set(key, timeout)
  }
  
  /**
   * Process buffered chunks
   */
  private processBuffer(key: string): void {
    const buffer = this.audioChunks.get(key)
    if (!buffer || buffer.chunks.length === 0) return
    
    // For now, just return the first chunk
    // In a real implementation, you might concatenate WAV data properly
    const audioData = buffer.chunks[0]
    
    // Clean up
    this.audioChunks.delete(key)
    this.timeoutHandles.delete(key)
    
    // Trigger callback with the audio data
    if (this.onBufferReady) {
      this.onBufferReady(audioData, buffer.messageId)
    }
  }
  
  /**
   * Callback when buffer is ready to play
   */
  onBufferReady?: (audioData: string, messageId?: string) => void
  
  /**
   * Clear all buffers
   */
  clear(): void {
    // Clear all timeouts
    this.timeoutHandles.forEach(timeout => clearTimeout(timeout))
    this.timeoutHandles.clear()
    this.audioChunks.clear()
  }
}