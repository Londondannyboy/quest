import { HyperDX } from '@hyperdx/node-opentelemetry'

// Initialize HyperDX for server-side monitoring
export function initServerMonitoring() {
  if (process.env.HYPERDX_PERSONAL_API_TOKEN) {
    HyperDX.init({
      apiKey: process.env.HYPERDX_PERSONAL_API_TOKEN,
      service: 'quest-core-v2-api',
    })

    // Start HyperDX
    HyperDX.start()
    
    console.log('HyperDX monitoring initialized for', process.env.NODE_ENV)
  }
}

// Error capturing for server-side
export function captureServerError(error: Error, context?: Record<string, unknown>) {
  console.error('Server error:', error, context)
  
  // HyperDX will automatically capture console.error
  // Additional custom logic can be added here
}