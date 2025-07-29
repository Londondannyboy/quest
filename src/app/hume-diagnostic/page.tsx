'use client'

import { useState } from 'react'

export default function HumeDiagnostic() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [results, setResults] = useState<Record<string, any> | null>(null)
  const [loading, setLoading] = useState(false)

  const runDiagnostic = async () => {
    setLoading(true)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const diagnostics: Record<string, any> = {
      environment: {},
      tokenTest: null,
      connectionTest: null,
      clmTest: null,
      errors: []
    }

    try {
      // 1. Check environment variables (client-side)
      diagnostics.environment = {
        hasApiKey: !!process.env.NEXT_PUBLIC_HUME_API_KEY,
        hasSecretKey: !!process.env.NEXT_PUBLIC_HUME_SECRET_KEY,
        hasConfigId: !!process.env.NEXT_PUBLIC_HUME_CONFIG_ID,
        configId: process.env.NEXT_PUBLIC_HUME_CONFIG_ID || 'NOT SET'
      }

      // 2. Test token endpoint
      try {
        const tokenResponse = await fetch('/api/hume/token')
        const tokenData = await tokenResponse.json()
        diagnostics.tokenTest = {
          status: tokenResponse.status,
          success: tokenData.success,
          hasToken: !!tokenData.accessToken,
          error: tokenData.error
        }
      } catch (error) {
        diagnostics.tokenTest = { error: error instanceof Error ? error.message : 'Failed' }
      }

      // 3. Test connection endpoint
      try {
        const connResponse = await fetch('/api/hume/test-connection')
        const connData = await connResponse.json()
        diagnostics.connectionTest = {
          status: connResponse.status,
          success: connData.success,
          results: connData.results,
          error: connData.error
        }
      } catch (error) {
        diagnostics.connectionTest = { error: error instanceof Error ? error.message : 'Failed' }
      }

      // 4. Test CLM endpoint
      try {
        const clmResponse = await fetch('/api/hume-clm-sse/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Hume-User-Id': 'test-user'
          },
          body: JSON.stringify({
            messages: [
              { role: 'user', content: 'Hello, this is a test' }
            ],
            stream: false
          })
        })
        
        const clmText = await clmResponse.text()
        diagnostics.clmTest = {
          status: clmResponse.status,
          headers: Object.fromEntries(clmResponse.headers.entries()),
          responseLength: clmText.length,
          response: clmText.substring(0, 200) + (clmText.length > 200 ? '...' : '')
        }
      } catch (error) {
        diagnostics.clmTest = { error: error instanceof Error ? error.message : 'Failed' }
      }

    } catch (error) {
      diagnostics.errors.push(error instanceof Error ? error.message : 'Unknown error')
    }

    setResults(diagnostics)
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Hume Voice Coach Diagnostic</h1>
        
        <div className="mb-8">
          <button
            onClick={runDiagnostic}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 rounded-lg"
          >
            {loading ? 'Running Diagnostic...' : 'Run Full Diagnostic'}
          </button>
        </div>

        {results && (
          <div className="space-y-6">
            {/* Environment Check */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">1. Environment Variables</h2>
              <div className="space-y-2 font-mono text-sm">
                <p className={results.environment.hasApiKey ? 'text-green-400' : 'text-red-400'}>
                  API Key: {results.environment.hasApiKey ? '✓ Set' : '✗ Missing'}
                </p>
                <p className={results.environment.hasSecretKey ? 'text-green-400' : 'text-red-400'}>
                  Secret Key: {results.environment.hasSecretKey ? '✓ Set' : '✗ Missing'}
                </p>
                <p className={results.environment.hasConfigId ? 'text-green-400' : 'text-red-400'}>
                  Config ID: {results.environment.configId}
                </p>
              </div>
            </div>

            {/* Token Test */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">2. Access Token Generation</h2>
              <div className="font-mono text-sm">
                {results.tokenTest.error ? (
                  <p className="text-red-400">Error: {results.tokenTest.error}</p>
                ) : (
                  <>
                    <p className={results.tokenTest.success ? 'text-green-400' : 'text-red-400'}>
                      Status: {results.tokenTest.status} - {results.tokenTest.success ? 'Success' : 'Failed'}
                    </p>
                    <p className={results.tokenTest.hasToken ? 'text-green-400' : 'text-red-400'}>
                      Token: {results.tokenTest.hasToken ? '✓ Generated' : '✗ Not generated'}
                    </p>
                    {results.tokenTest.error && (
                      <p className="text-yellow-400 mt-2">Error: {results.tokenTest.error}</p>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Connection Test */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">3. API Connection Test</h2>
              <div className="font-mono text-sm">
                {results.connectionTest.error ? (
                  <p className="text-red-400">Error: {results.connectionTest.error}</p>
                ) : (
                  <>
                    <p className={results.connectionTest.success ? 'text-green-400' : 'text-red-400'}>
                      Status: {results.connectionTest.status} - {results.connectionTest.success ? 'Success' : 'Failed'}
                    </p>
                    {results.connectionTest.results && (
                      <div className="mt-2 text-xs">
                        <p>Has Token: {results.connectionTest.results.hasAccessToken ? '✓' : '✗'}</p>
                        <p>Config ID: {results.connectionTest.results.configId}</p>
                        <p>Available Configs: {results.connectionTest.results.availableConfigs}</p>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* CLM Test */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">4. Custom Language Model (CLM) Test</h2>
              <div className="font-mono text-sm">
                {results.clmTest.error ? (
                  <p className="text-red-400">Error: {results.clmTest.error}</p>
                ) : (
                  <>
                    <p className={results.clmTest.status === 200 ? 'text-green-400' : 'text-red-400'}>
                      Status: {results.clmTest.status}
                    </p>
                    <p>Response Length: {results.clmTest.responseLength} bytes</p>
                    <div className="mt-2 p-2 bg-gray-900 rounded text-xs overflow-x-auto">
                      <pre>{results.clmTest.response}</pre>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Overall Status */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Summary</h2>
              <div className="space-y-2">
                <p className="text-lg">
                  {results.environment.hasApiKey && results.environment.hasSecretKey && results.environment.hasConfigId ? (
                    <span className="text-green-400">✓ Environment variables are set</span>
                  ) : (
                    <span className="text-red-400">✗ Missing environment variables</span>
                  )}
                </p>
                <p className="text-lg">
                  {results.tokenTest.success ? (
                    <span className="text-green-400">✓ Token generation works</span>
                  ) : (
                    <span className="text-red-400">✗ Token generation failed</span>
                  )}
                </p>
                <p className="text-lg">
                  {results.connectionTest.success ? (
                    <span className="text-green-400">✓ API connection works</span>
                  ) : (
                    <span className="text-red-400">✗ API connection failed</span>
                  )}
                </p>
                <p className="text-lg">
                  {results.clmTest.status === 200 ? (
                    <span className="text-green-400">✓ CLM endpoint works</span>
                  ) : (
                    <span className="text-red-400">✗ CLM endpoint failed</span>
                  )}
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="mt-8 text-sm text-gray-500">
          <p>This diagnostic checks:</p>
          <ul className="list-disc list-inside mt-2">
            <li>Environment variable presence</li>
            <li>Access token generation from API key/secret</li>
            <li>Hume API connection and config retrieval</li>
            <li>Custom Language Model endpoint functionality</li>
          </ul>
        </div>
      </div>
    </div>
  )
}