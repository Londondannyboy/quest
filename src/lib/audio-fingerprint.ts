/**
 * Simple audio fingerprinting to detect duplicate audio streams
 */

export class AudioFingerprinter {
  private fingerprints: Map<string, { timestamp: number; count: number }> = new Map()
  private readonly FINGERPRINT_EXPIRY = 5000 // 5 seconds
  
  /**
   * Generate a simple fingerprint from base64 audio data
   */
  generateFingerprint(base64Audio: string): string {
    // Take samples from different parts of the audio
    const samples = [
      base64Audio.substring(0, 20),
      base64Audio.substring(base64Audio.length / 2 - 10, base64Audio.length / 2 + 10),
      base64Audio.substring(base64Audio.length - 20)
    ]
    
    // Create a simple hash
    return samples.join('|')
  }
  
  /**
   * Check if this audio has been seen recently
   */
  isDuplicate(base64Audio: string): boolean {
    const fingerprint = this.generateFingerprint(base64Audio)
    const now = Date.now()
    
    // Clean up old fingerprints
    this.cleanupOldFingerprints(now)
    
    // Check if we've seen this fingerprint
    const existing = this.fingerprints.get(fingerprint)
    if (existing && (now - existing.timestamp) < this.FINGERPRINT_EXPIRY) {
      existing.count++
      console.log(`[AudioFingerprint] Duplicate detected! Count: ${existing.count}`)
      return true
    }
    
    // Store new fingerprint
    this.fingerprints.set(fingerprint, { timestamp: now, count: 1 })
    return false
  }
  
  /**
   * Get statistics about duplicates
   */
  getStats(): { totalFingerprints: number; duplicates: Array<{ fingerprint: string; count: number }> } {
    const duplicates = Array.from(this.fingerprints.entries())
      .filter(([_, data]) => data.count > 1)
      .map(([fingerprint, data]) => ({ fingerprint: fingerprint.substring(0, 20) + '...', count: data.count }))
      .sort((a, b) => b.count - a.count)
    
    return {
      totalFingerprints: this.fingerprints.size,
      duplicates
    }
  }
  
  /**
   * Clean up old fingerprints
   */
  private cleanupOldFingerprints(now: number): void {
    for (const [fingerprint, data] of this.fingerprints.entries()) {
      if (now - data.timestamp > this.FINGERPRINT_EXPIRY) {
        this.fingerprints.delete(fingerprint)
      }
    }
  }
  
  /**
   * Clear all fingerprints
   */
  clear(): void {
    this.fingerprints.clear()
  }
}

// Global instance for debugging
export const globalAudioFingerprinter = new AudioFingerprinter()