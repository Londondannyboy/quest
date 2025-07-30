'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'

export default function TrinityClmDebugPage() {
  const { user, isLoaded } = useUser()
  const [debugInfo, setDebugInfo] = useState<Record<string, unknown> | null>(null)
  const [clmTest, setClmTest] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [testMessage, setTestMessage] = useState("Hello, who am I?")

  // Fetch debug info
  const fetchDebugInfo = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/hume-clm-debug')
      const data = await response.json()
      setDebugInfo(data)
    } catch (error) {
      console.error('Debug fetch error:', error)
      setDebugInfo({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  // Test CLM endpoint
  const testClmEndpoint = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/hume-clm-debug', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: testMessage })
      })
      const data = await response.json()
      setClmTest(data)
    } catch (error) {
      console.error('CLM test error:', error)
      setClmTest({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isLoaded) {
      fetchDebugInfo()
    }
  }, [isLoaded])

  return (
    <main className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Trinity CLM Debug</h1>
        
        {/* Current User Info */}
        <div className="bg-gray-800 p-6 rounded-lg mb-6">
          <h2 className="text-xl font-semibold mb-4">Current User (Client Side)</h2>
          <pre className="text-sm overflow-x-auto">
            {JSON.stringify({
              isLoaded,
              isSignedIn: !!user,
              userId: user?.id,
              name: user?.fullName || user?.firstName,
              email: user?.emailAddresses?.[0]?.emailAddress
            }, null, 2)}
          </pre>
        </div>

        {/* Debug Info */}
        {debugInfo && (
          <div className="bg-gray-800 p-6 rounded-lg mb-6">
            <h2 className="text-xl font-semibold mb-4">Server Debug Info</h2>
            <pre className="text-sm overflow-x-auto">
              {JSON.stringify(debugInfo, null, 2)}
            </pre>
          </div>
        )}

        {/* CLM Test */}
        <div className="bg-gray-800 p-6 rounded-lg mb-6">
          <h2 className="text-xl font-semibold mb-4">Test CLM Endpoint</h2>
          <div className="flex gap-4 mb-4">
            <input
              type="text"
              value={testMessage}
              onChange={(e) => setTestMessage(e.target.value)}
              className="flex-1 px-4 py-2 bg-gray-700 rounded"
              placeholder="Test message..."
            />
            <button
              onClick={testClmEndpoint}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded disabled:opacity-50"
            >
              Test CLM
            </button>
          </div>
          
          {clmTest && (
            <pre className="text-sm overflow-x-auto bg-gray-900 p-4 rounded">
              {JSON.stringify(clmTest, null, 2)}
            </pre>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          <button
            onClick={fetchDebugInfo}
            disabled={loading}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 rounded disabled:opacity-50"
          >
            Refresh Debug Info
          </button>
          <a
            href="/trinity"
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded inline-block"
          >
            Go to Trinity
          </a>
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-yellow-900/50 border border-yellow-600 p-6 rounded-lg">
          <h3 className="text-xl font-semibold mb-4 text-yellow-300">Debugging Steps</h3>
          <ol className="list-decimal list-inside space-y-2 text-yellow-200">
            <li>Check if your user ID appears in the &quot;Current User&quot; section</li>
            <li>Look at &quot;Server Debug Info&quot; to see if auth is working server-side</li>
            <li>Test the CLM endpoint with &quot;who am I?&quot; to see if it recognizes you</li>
            <li>Check the database section to ensure it&apos;s connected</li>
            <li>If user ID is missing, check Clerk configuration in Vercel</li>
          </ol>
        </div>
      </div>
    </main>
  )
}