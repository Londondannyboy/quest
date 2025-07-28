import HyperDX from '@hyperdx/browser'

let initialized = false

export function initHyperDX() {
  if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_HYPERDX_PERSONAL_API_TOKEN && !initialized) {
    HyperDX.init({
      apiKey: process.env.NEXT_PUBLIC_HYPERDX_PERSONAL_API_TOKEN,
      service: 'quest-core-v2',
      tracePropagationTargets: [/quest-omega-wheat\.vercel\.app/i],
      consoleCapture: true,
      advancedNetworkCapture: true,
    })
    initialized = true
  }
}

export function captureError(error: Error, context?: Record<string, unknown>) {
  console.error('Error captured:', error, context)
  
  if (initialized) {
    // HyperDX automatically captures console.error
    // We can also add a custom action for additional tracking
    HyperDX.addAction('error_captured', {
      error: error.message,
      stack: error.stack,
      ...context,
    })
  }
}

export function captureMessage(message: string, level: 'info' | 'warning' | 'error' = 'info') {
  if (initialized) {
    // Use console methods which HyperDX automatically captures
    switch (level) {
      case 'error':
        console.error(message)
        break
      case 'warning':
        console.warn(message)
        break
      case 'info':
      default:
        console.info(message)
        break
    }
    
    // Also add as a custom action
    HyperDX.addAction(`message_${level}`, { message })
  }
}

export function setUser(userId: string, email?: string) {
  if (initialized) {
    const attributes: Record<string, string> = { userId }
    if (email) {
      attributes.userEmail = email
    }
    HyperDX.setGlobalAttributes(attributes)
  }
}

export function addBreadcrumb(message: string, data?: Record<string, unknown>) {
  if (initialized) {
    // HyperDX doesn't have a breadcrumb API, use addAction instead
    HyperDX.addAction('breadcrumb', {
      message,
      timestamp: Date.now(),
      ...data,
    })
  }
}