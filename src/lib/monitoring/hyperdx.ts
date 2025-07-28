import HyperDX from '@hyperdx/browser'

let hdx: typeof HyperDX | null = null

export function initHyperDX() {
  if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_HYPERDX_PERSONAL_API_TOKEN) {
    hdx = HyperDX.init({
      apiKey: process.env.NEXT_PUBLIC_HYPERDX_PERSONAL_API_TOKEN,
      service: 'quest-core-v2',
      tracePropagationTargets: [/quest-omega-wheat\.vercel\.app/i],
      consoleCapture: true,
      advancedNetworkCapture: true,
    })
  }
}

export function captureError(error: Error, context?: Record<string, unknown>) {
  console.error('Error captured:', error, context)
  
  if (hdx) {
    hdx.captureException(error, {
      extra: context,
    })
  }
}

export function captureMessage(message: string, level: 'info' | 'warning' | 'error' = 'info') {
  if (hdx) {
    hdx.captureMessage(message, level)
  }
}

export function setUser(userId: string, email?: string) {
  if (hdx) {
    hdx.setUser({
      id: userId,
      email,
    })
  }
}

export function addBreadcrumb(message: string, data?: Record<string, unknown>) {
  if (hdx) {
    hdx.addBreadcrumb({
      message,
      data,
      timestamp: Date.now(),
    })
  }
}