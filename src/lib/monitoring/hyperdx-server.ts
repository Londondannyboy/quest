import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node'
import { HyperDX } from '@hyperdx/node-opentelemetry'

// Initialize HyperDX for server-side monitoring
export function initServerMonitoring() {
  if (process.env.HYPERDX_API_KEY && process.env.NODE_ENV === 'production') {
    HyperDX.init({
      apiKey: process.env.HYPERDX_API_KEY,
      service: 'quest-core-v2-api',
      instrumentations: [
        getNodeAutoInstrumentations({
          '@opentelemetry/instrumentation-fs': {
            enabled: false,
          },
        }),
      ],
    })

    // Start HyperDX
    HyperDX.start()
    
    console.log('HyperDX monitoring initialized')
  }
}

// Error capturing for server-side
export function captureServerError(error: Error, context?: Record<string, unknown>) {
  console.error('Server error:', error, context)
  
  // HyperDX will automatically capture console.error
  // Additional custom logic can be added here
}