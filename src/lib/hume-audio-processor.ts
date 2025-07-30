/**
 * Hume Audio Processor
 * Handles concatenation and playback of audio chunks from Hume AI
 */

export class HumeAudioProcessor {
  private audioContext: AudioContext | null = null
  private audioQueue: AudioBufferSourceNode[] = []
  private chunkBuffers: AudioBuffer[] = []
  private isPlaying = false
  private onComplete?: () => void
  
  constructor() {
    if (typeof window !== 'undefined') {
      this.audioContext = new AudioContext()
    }
  }
  
  /**
   * Add an audio chunk to be processed
   */
  async addChunk(base64Audio: string): Promise<void> {
    if (!this.audioContext) return
    
    try {
      // Decode base64 to ArrayBuffer
      const binaryString = atob(base64Audio)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      
      // Decode audio data
      const audioBuffer = await this.audioContext.decodeAudioData(bytes.buffer)
      this.chunkBuffers.push(audioBuffer)
      console.log(`[HumeAudioProcessor] Added chunk ${this.chunkBuffers.length}, duration: ${audioBuffer.duration}s`)
    } catch (error) {
      console.error('[HumeAudioProcessor] Failed to decode audio chunk:', error)
    }
  }
  
  /**
   * Play all accumulated chunks
   */
  async playAll(): Promise<void> {
    if (!this.audioContext || this.chunkBuffers.length === 0 || this.isPlaying) {
      return
    }
    
    this.isPlaying = true
    console.log(`[HumeAudioProcessor] Starting playback of ${this.chunkBuffers.length} chunks`)
    
    // Calculate total duration
    const totalDuration = this.chunkBuffers.reduce((sum, buffer) => sum + buffer.duration, 0)
    console.log(`[HumeAudioProcessor] Total duration: ${totalDuration}s`)
    
    // Play chunks sequentially
    let currentTime = 0
    for (const buffer of this.chunkBuffers) {
      const source = this.audioContext.createBufferSource()
      source.buffer = buffer
      source.connect(this.audioContext.destination)
      
      // Schedule playback
      const startTime = this.audioContext.currentTime + currentTime
      source.start(startTime)
      
      this.audioQueue.push(source)
      console.log(`[HumeAudioProcessor] Scheduled chunk at ${currentTime}s, duration: ${buffer.duration}s`)
      
      currentTime += buffer.duration
    }
    
    // Set up completion callback
    if (this.audioQueue.length > 0) {
      const lastSource = this.audioQueue[this.audioQueue.length - 1]
      lastSource.onended = () => {
        console.log('[HumeAudioProcessor] Playback complete')
        this.isPlaying = false
        this.clear()
        this.onComplete?.()
      }
    }
  }
  
  /**
   * Stop all audio and clear buffers
   */
  stop(): void {
    console.log('[HumeAudioProcessor] Stopping all audio')
    
    // Stop all playing sources
    this.audioQueue.forEach(source => {
      try {
        source.stop()
        source.disconnect()
      } catch {
        // Already stopped
      }
    })
    
    this.clear()
  }
  
  /**
   * Clear all buffers
   */
  clear(): void {
    this.audioQueue = []
    this.chunkBuffers = []
    this.isPlaying = false
  }
  
  /**
   * Set completion callback
   */
  setOnComplete(callback: () => void): void {
    this.onComplete = callback
  }
  
  /**
   * Get playback status
   */
  getIsPlaying(): boolean {
    return this.isPlaying
  }
  
  /**
   * Get number of chunks
   */
  getChunkCount(): number {
    return this.chunkBuffers.length
  }
}