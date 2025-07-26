'use client'

import { useUser, SignInButton, SignOutButton } from '@clerk/nextjs'
import { useEffect, useState } from 'react'

export default function TestClerk() {
  const { isLoaded, isSignedIn, user } = useUser()
  const [apiTest, setApiTest] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const testAPI = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/test-clerk')
      const data = await response.json()
      setApiTest(data)
    } catch (error) {
      setApiTest({ error: 'Failed to test API' })
    }
    setLoading(false)
  }

  useEffect(() => {
    testAPI()
  }, [])

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Clerk Connection Test</h1>
        
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Frontend Status</h2>
          <div className="space-y-2">
            <p>Clerk Loaded: {isLoaded ? '✅ Yes' : '❌ No'}</p>
            <p>User Signed In: {isSignedIn ? '✅ Yes' : '❌ No'}</p>
            {user && (
              <>
                <p>User ID: {user.id}</p>
                <p>Email: {user.emailAddresses?.[0]?.emailAddress}</p>
              </>
            )}
          </div>
          
          <div className="mt-4">
            {isSignedIn ? (
              <SignOutButton>
                <button className="bg-red-500 px-4 py-2 rounded hover:bg-red-600">
                  Sign Out
                </button>
              </SignOutButton>
            ) : (
              <SignInButton>
                <button className="bg-blue-500 px-4 py-2 rounded hover:bg-blue-600">
                  Sign In
                </button>
              </SignInButton>
            )}
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">API Test Results</h2>
          <button 
            onClick={testAPI}
            disabled={loading}
            className="bg-green-500 px-4 py-2 rounded hover:bg-green-600 mb-4 disabled:opacity-50"
          >
            {loading ? 'Testing...' : 'Test API Connection'}
          </button>
          
          {apiTest && (
            <pre className="bg-gray-900 p-4 rounded overflow-auto text-sm">
              {JSON.stringify(apiTest, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </div>
  )
}