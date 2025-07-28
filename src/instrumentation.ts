export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    // Dynamically import to avoid build-time issues
    const { initServerMonitoring } = await import('./lib/monitoring/hyperdx-server')
    
    // Initialize HyperDX monitoring on server startup
    await initServerMonitoring()
  }
}