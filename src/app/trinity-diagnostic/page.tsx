'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'

export default function TrinityDiagnosticPage() {
  const { user } = useUser()
  const [diagnostics, setDiagnostics] = useState<Record<string, unknown>>({})
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    const runDiagnostics = async () => {
      const results: Record<string, unknown> = {}
      
      // Check environment variables
      results.envVars = {
        NEXT_PUBLIC_HUME_API_KEY: process.env.NEXT_PUBLIC_HUME_API_KEY ? 
          (process.env.NEXT_PUBLIC_HUME_API_KEY === '...' ? '❌ Placeholder value' : '✅ Set') : 
          '❌ Not set',
        NEXT_PUBLIC_HUME_SECRET_KEY: process.env.NEXT_PUBLIC_HUME_SECRET_KEY ? 
          (process.env.NEXT_PUBLIC_HUME_SECRET_KEY === '...' ? '❌ Placeholder value' : '✅ Set') : 
          '❌ Not set',
        NEXT_PUBLIC_HUME_CONFIG_ID: process.env.NEXT_PUBLIC_HUME_CONFIG_ID ? 
          (process.env.NEXT_PUBLIC_HUME_CONFIG_ID === '...' ? '❌ Placeholder value' : '✅ Set') : 
          '❌ Not set',
      }
      
      // Test access token endpoint
      try {
        const tokenResponse = await fetch('/api/hume/token')
        const tokenData = await tokenResponse.json()
        results.accessToken = {
          status: tokenResponse.ok ? '✅ Working' : '❌ Failed',
          statusCode: tokenResponse.status,
          hasToken: !!tokenData.accessToken,
          error: tokenData.error
        }
      } catch (error) {
        results.accessToken = {
          status: '❌ Error',
          error: error instanceof Error ? error.message : String(error)
        }
      }
      
      // Test WebSocket connection
      try {
        const accessTokenResult = results.accessToken as { hasToken?: boolean, status: string, error?: string }
        if (accessTokenResult.hasToken) {
          const tokenResponse = await fetch('/api/hume/token')
          const { accessToken } = await tokenResponse.json()
          const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID
          
          if (accessToken && configId && configId !== '...') {
            const params = new URLSearchParams({
              access_token: accessToken,
              config_id: configId
            })
            
            const ws = new WebSocket(`wss://api.hume.ai/v0/evi/chat?${params}`)
            
            await new Promise((resolve, reject) => {
              ws.onopen = () => {
                results.webSocket = { status: '✅ Connected' }
                ws.close()
                resolve(true)
              }
              ws.onerror = (error) => {
                results.webSocket = { status: '❌ Connection failed', error: String(error) }
                reject(error)
              }
              setTimeout(() => {
                results.webSocket = { status: '❌ Timeout' }
                ws.close()
                reject(new Error('Connection timeout'))
              }, 5000)
            })
          } else {
            results.webSocket = { status: '❌ Missing credentials' }
          }
        } else {
          results.webSocket = { status: '❌ No access token' }
        }
      } catch (error) {
        results.webSocket = { 
          status: '❌ Error',
          error: error instanceof Error ? error.message : String(error)
        }
      }
      
      // Check browser capabilities
      results.browser = {
        audioContext: typeof AudioContext !== 'undefined' ? '✅ Supported' : '❌ Not supported',
        mediaDevices: navigator.mediaDevices ? '✅ Available' : '❌ Not available',
        getUserMedia: typeof navigator.mediaDevices?.getUserMedia === 'function' ? '✅ Available' : '❌ Not available',
        webSocket: typeof WebSocket !== 'undefined' ? '✅ Supported' : '❌ Not supported'
      }
      
      // User info
      results.user = {
        isAuthenticated: !!user,
        id: user?.id || 'Not logged in',
        name: user?.fullName || user?.firstName || 'Unknown'
      }
      
      setDiagnostics(results)
      setLoading(false)
    }
    
    runDiagnostics()
  }, [user])
  
  return (
    <main className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Trinity Diagnostic Report</h1>
        
        {loading ? (
          <p>Running diagnostics...</p>
        ) : (
          <div className="space-y-6">
            {/* Environment Variables */}
            <div className="bg-gray-800 p-6 rounded-lg">
              <h2 className="text-xl font-semibold mb-4">Environment Variables</h2>
              <div className="space-y-2">
                {Object.entries(diagnostics.envVars || {}).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-400">{key}:</span>
                    <span>{value}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Access Token */}
            <div className="bg-gray-800 p-6 rounded-lg">
              <h2 className="text-xl font-semibold mb-4">Access Token API</h2>
              <pre className="text-sm overflow-x-auto">
                {JSON.stringify(diagnostics.accessToken, null, 2)}
              </pre>
            </div>
            
            {/* WebSocket */}
            <div className="bg-gray-800 p-6 rounded-lg">
              <h2 className="text-xl font-semibold mb-4">WebSocket Connection</h2>
              <pre className="text-sm overflow-x-auto">
                {JSON.stringify(diagnostics.webSocket, null, 2)}
              </pre>
            </div>
            
            {/* Browser Capabilities */}
            <div className="bg-gray-800 p-6 rounded-lg">
              <h2 className="text-xl font-semibold mb-4">Browser Capabilities</h2>
              <div className="space-y-2">
                {Object.entries(diagnostics.browser || {}).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-400">{key}:</span>
                    <span>{value}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {/* User Info */}
            <div className="bg-gray-800 p-6 rounded-lg">
              <h2 className="text-xl font-semibold mb-4">User Info</h2>
              <pre className="text-sm overflow-x-auto">
                {JSON.stringify(diagnostics.user, null, 2)}
              </pre>
            </div>
            
            {/* Solutions */}
            <div className="bg-yellow-900/50 border border-yellow-600 p-6 rounded-lg">
              <h2 className="text-xl font-semibold mb-4 text-yellow-300">Required Actions</h2>
              <ol className="list-decimal list-inside space-y-2 text-yellow-200">
                <li>Go to Vercel Dashboard → Settings → Environment Variables</li>
                <li>Add these variables with your actual Hume credentials:
                  <ul className="list-disc list-inside ml-6 mt-2">
                    <li>NEXT_PUBLIC_HUME_API_KEY</li>
                    <li>NEXT_PUBLIC_HUME_SECRET_KEY</li>
                    <li>NEXT_PUBLIC_HUME_CONFIG_ID</li>
                  </ul>
                </li>
                <li>Get these values from your Hume dashboard at https://platform.hume.ai</li>
                <li>Make sure to remove the &quot;...&quot; placeholder values</li>
                <li>Redeploy after adding the variables</li>
              </ol>
            </div>
          </div>
        )}
        
        {/* Links */}
        <div className="mt-8 flex gap-4 justify-center">
          <a href="/trinity-compare" className="text-blue-400 hover:underline">
            View All Implementations
          </a>
          <a href="/trinity-native" className="text-blue-400 hover:underline">
            Test Native SDK
          </a>
          <a href="/trinity-sdk" className="text-blue-400 hover:underline">
            Test TypeScript SDK
          </a>
        </div>
      </div>
    </main>
  )
}