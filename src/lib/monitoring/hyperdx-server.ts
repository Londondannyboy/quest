// Initialize HyperDX for server-side monitoring
export async function initServerMonitoring() {
  // Only initialize in Node.js runtime, not during build
  if (typeof window === 'undefined' && process.env.HYPERDX_PERSONAL_API_TOKEN) {
    try {
      const { init } = await import('@hyperdx/node-opentelemetry')
      
      init({
        apiKey: process.env.HYPERDX_PERSONAL_API_TOKEN,
        service: 'quest-core-v2-api',
        consoleCapture: true,
      })
      
      console.log('HyperDX monitoring initialized for', process.env.NODE_ENV)
    } catch (error) {
      console.warn('Failed to initialize HyperDX monitoring:', error)
    }
  }
}

// Error capturing for server-side
export function captureServerError(error: Error, context?: Record<string, unknown>) {
  console.error('Server error:', error, context)
  
  // HyperDX will automatically capture console.error
  // Additional custom logic can be added here
}