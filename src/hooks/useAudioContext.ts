import { useRef, useCallback, useEffect } from 'react'
import { logger } from '@/lib/logger'
import { globalAudioFingerprinter } from '@/lib/audio-fingerprint'

export function useAudioContext() {
  const audioContextRef = useRef<AudioContext | null>(null)
  const audioQueueRef = useRef<AudioBufferSourceNode[]>([])
  const processedAudioIds = useRef<Set<string>>(new Set())
  
  // Initialize audio context
  const initAudioContext = useCallback(() => {
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext()
      logger.audio('AudioContext initialized')
    }
    return audioContextRef.current
  }, [])
  
  // Play audio chunk
  const playAudioChunk = useCallback(async (base64Audio: string, audioId?: string) => {
    const context = initAudioContext()
    
    try {
      // Check for duplicates
      const id = audioId || `audio_${Date.now()}_${base64Audio.substring(0, 20)}`
      
      if (processedAudioIds.current.has(id)) {
        logger.audio('Skipping duplicate audio (ID match)', { audioId: id })
        return
      }
      
      const isDuplicate = globalAudioFingerprinter.isDuplicate(base64Audio)
      if (isDuplicate) {
        logger.audio('Skipping duplicate audio (fingerprint match)', { audioId: id })
        return
      }
      
      processedAudioIds.current.add(id)
      
      // Decode base64 to ArrayBuffer
      const binaryString = atob(base64Audio)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      
      // Decode audio data
      const audioBuffer = await context.decodeAudioData(bytes.buffer)
      
      // Create and play audio source
      const source = context.createBufferSource()
      source.buffer = audioBuffer
      source.connect(context.destination)
      source.start()
      
      // Track for cleanup
      audioQueueRef.current.push(source)
      
      // Clean up after playback
      source.onended = () => {
        audioQueueRef.current = audioQueueRef.current.filter(s => s !== source)
        // Clean up processed ID after delay
        setTimeout(() => {
          processedAudioIds.current.delete(id)
        }, 10000)
      }
      
      logger.audio('Playing audio chunk', { 
        audioId: id, 
        duration: audioBuffer.duration,
        size: base64Audio.length 
      })
    } catch (error) {
      logger.error('Error playing audio', error)
    }
  }, [initAudioContext])
  
  // Stop all audio
  const stopAllAudio = useCallback(() => {
    audioQueueRef.current.forEach(source => {
      try {
        source.stop()
      } catch {
        // Ignore if already stopped
      }
    })
    audioQueueRef.current = []
    processedAudioIds.current.clear()
    logger.audio('All audio stopped')
  }, [])
  
  // Resume audio context if suspended
  const resumeAudioContext = useCallback(async () => {
    if (audioContextRef.current?.state === 'suspended') {
      await audioContextRef.current.resume()
      logger.audio('AudioContext resumed')
    }
  }, [])
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAllAudio()
      if (audioContextRef.current) {
        audioContextRef.current.close()
        audioContextRef.current = null
      }
    }
  }, [stopAllAudio])
  
  return {
    playAudioChunk,
    stopAllAudio,
    resumeAudioContext,
    audioContext: audioContextRef.current,
    activeAudioCount: audioQueueRef.current.length,
  }
}