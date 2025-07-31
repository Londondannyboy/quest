'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'

export default function TrinityClmDebugPage() {
  const { user, isLoaded } = useUser()
  const [debugInfo, setDebugInfo] = useState<Record<string, unknown> | null>(null)
  const [clmTest, setClmTest] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [testMessage, setTestMessage] = useState("Hello, who am I?")
  const [profileStatus, setProfileStatus] = useState<string>('')
  const [userName, setUserName] = useState<string>('')
  const [linkedinData, setLinkedinData] = useState<Record<string, unknown> | null>(null)
  const [linkedinStructure, setLinkedinStructure] = useState<Record<string, unknown> | null>(null)
  const [dbTestResult, setDbTestResult] = useState<Record<string, unknown> | null>(null)
  const [zepStatus, setZepStatus] = useState<string>('')

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

  // Populate from LinkedIn
  const populateFromLinkedIn = async () => {
    setLoading(true)
    setProfileStatus('Loading LinkedIn data...')
    try {
      const response = await fetch('/api/user/populate-from-linkedin', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })
      const data = await response.json()
      if (response.ok) {
        setProfileStatus(`✅ Profile populated! Name: ${data.user.name}`)
        setLinkedinData(data)
        // Refresh debug info
        await fetchDebugInfo()
      } else {
        setProfileStatus(`❌ Error: ${data.error}`)
      }
    } catch (error) {
      console.error('LinkedIn populate error:', error)
      setProfileStatus(`❌ Error: ${String(error)}`)
    } finally {
      setLoading(false)
    }
  }
  
  // Update user name
  const updateUserName = async () => {
    if (!userName.trim()) {
      setProfileStatus('❌ Please enter a name')
      return
    }
    
    setLoading(true)
    setProfileStatus('Updating name...')
    try {
      const response = await fetch('/api/user/update-name', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: userName })
      })
      const data = await response.json()
      if (response.ok) {
        setProfileStatus(`✅ Name updated to: ${data.user.name}`)
        setUserName('')
        // Refresh debug info to show updated name
        await fetchDebugInfo()
      } else {
        setProfileStatus(`❌ Error: ${data.error}`)
      }
    } catch (error) {
      console.error('Name update error:', error)
      setProfileStatus(`❌ Error: ${String(error)}`)
    } finally {
      setLoading(false)
    }
  }
  
  // Create or update user profile
  const createOrUpdateProfile = async () => {
    setLoading(true)
    setProfileStatus('Creating/updating profile...')
    try {
      const response = await fetch('/api/user/create-profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })
      const data = await response.json()
      if (response.ok) {
        setProfileStatus(`✅ ${data.message} - Name: ${data.user.name}`)
        // Refresh debug info to show updated database status
        await fetchDebugInfo()
      } else {
        setProfileStatus(`❌ Error: ${data.error}`)
      }
    } catch (error) {
      console.error('Profile creation error:', error)
      setProfileStatus(`❌ Error: ${String(error)}`)
    } finally {
      setLoading(false)
    }
  }
  
  // Show LinkedIn data structure
  const showLinkedInStructure = async () => {
    setLoading(true)
    setProfileStatus('Fetching LinkedIn data structure...')
    try {
      const response = await fetch('/api/user/show-linkedin-data')
      const data = await response.json()
      if (response.ok) {
        setLinkedinStructure(data)
        setProfileStatus('✅ LinkedIn data structure loaded')
      } else {
        setProfileStatus(`❌ Error: ${data.error}`)
      }
    } catch (error) {
      console.error('LinkedIn structure error:', error)
      setProfileStatus(`❌ Error: ${String(error)}`)
    } finally {
      setLoading(false)
    }
  }
  
  // Test database connection
  const testDatabase = async () => {
    setLoading(true)
    setProfileStatus('Testing database connection...')
    try {
      const response = await fetch('/api/test-db')
      const data = await response.json()
      setDbTestResult(data)
      if (data.database?.status === 'Connected') {
        setProfileStatus('✅ Database connected successfully')
      } else {
        setProfileStatus(`❌ Database connection failed: ${data.database?.error}`)
      }
    } catch (error) {
      console.error('Database test error:', error)
      setProfileStatus(`❌ Error: ${String(error)}`)
    } finally {
      setLoading(false)
    }
  }
  
  // Initialize user in Zep
  const initializeZep = async () => {
    setLoading(true)
    setZepStatus('Initializing user in Zep...')
    try {
      const response = await fetch('/api/user/init-zep', {
        method: 'POST'
      })
      const data = await response.json()
      if (response.ok) {
        setZepStatus(`✅ ${data.message}`)
        // Refresh debug info to see updated status
        await fetchDebugInfo()
      } else {
        setZepStatus(`❌ Error: ${data.error}`)
      }
    } catch (error) {
      console.error('Zep init error:', error)
      setZepStatus(`❌ Error: ${String(error)}`)
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

        {/* Update Name Section */}
        <div className="bg-gray-800 p-6 rounded-lg mb-6">
          <h2 className="text-xl font-semibold mb-4">Update Your Name</h2>
          <div className="flex gap-4">
            <input
              type="text"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              placeholder="Enter your name..."
              className="flex-1 px-4 py-2 bg-gray-700 rounded text-white"
            />
            <button
              onClick={updateUserName}
              disabled={loading || !userName.trim()}
              className="px-6 py-2 bg-purple-600 hover:bg-purple-700 rounded disabled:opacity-50"
            >
              Update Name
            </button>
          </div>
        </div>

        {/* Profile Status */}
        {profileStatus && (
          <div className="bg-gray-800 p-4 rounded-lg mb-6">
            <p className="text-sm">{profileStatus}</p>
          </div>
        )}
        
        {/* Zep Status */}
        {zepStatus && (
          <div className="bg-gray-800 p-4 rounded-lg mb-6">
            <p className="text-sm font-mono">{zepStatus}</p>
          </div>
        )}
        
        {/* LinkedIn Data */}
        {linkedinData && (
          <div className="bg-gray-800 p-6 rounded-lg mb-6">
            <h2 className="text-xl font-semibold mb-4">LinkedIn Data Found</h2>
            <pre className="text-sm overflow-x-auto">
              {JSON.stringify(linkedinData, null, 2)}
            </pre>
          </div>
        )}
        
        {/* LinkedIn Structure Analysis */}
        {linkedinStructure && (
          <div className="bg-gray-800 p-6 rounded-lg mb-6">
            <h2 className="text-xl font-semibold mb-4">LinkedIn Data Structure Analysis</h2>
            <pre className="text-sm overflow-x-auto">
              {JSON.stringify(linkedinStructure, null, 2)}
            </pre>
          </div>
        )}
        
        {/* Database Test Results */}
        {dbTestResult && (
          <div className="bg-gray-800 p-6 rounded-lg mb-6">
            <h2 className="text-xl font-semibold mb-4">Database Test Results</h2>
            <pre className="text-sm overflow-x-auto">
              {JSON.stringify(dbTestResult, null, 2)}
            </pre>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4 flex-wrap">
          <button
            onClick={fetchDebugInfo}
            disabled={loading}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 rounded disabled:opacity-50"
          >
            Refresh Debug Info
          </button>
          <button
            onClick={createOrUpdateProfile}
            disabled={loading}
            className="px-6 py-3 bg-yellow-600 hover:bg-yellow-700 rounded disabled:opacity-50"
          >
            Create/Update Profile
          </button>
          <button
            onClick={populateFromLinkedIn}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded disabled:opacity-50"
          >
            Populate from LinkedIn
          </button>
          <button
            onClick={showLinkedInStructure}
            disabled={loading}
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 rounded disabled:opacity-50"
          >
            Show LinkedIn Structure
          </button>
          <button
            onClick={testDatabase}
            disabled={loading}
            className="px-6 py-3 bg-red-600 hover:bg-red-700 rounded disabled:opacity-50"
          >
            Test Database
          </button>
          <button
            onClick={initializeZep}
            disabled={loading}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 rounded disabled:opacity-50"
          >
            Initialize Zep
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