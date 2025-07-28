import { initServerMonitoring } from './lib/monitoring/hyperdx-server'

export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    // Initialize HyperDX monitoring on server startup
    initServerMonitoring()
  }
}