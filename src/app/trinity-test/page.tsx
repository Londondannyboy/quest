'use client'

import { useState } from 'react'

export default function TrinityTestPage() {
  const [loading, setLoading] = useState(false)
  const [trinityData, setTrinityData] = useState<Record<string, unknown> | null>(null)
  const [readinessData, setReadinessData] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [userInitialized, setUserInitialized] = useState(false)

  // Sample Trinity data for testing
  const sampleTrinity = {
    pastQuest: "I was driven by a desire to solve complex technical problems and build innovative solutions that could help people in their daily lives",
    pastService: "I served teams by mentoring junior developers and creating robust, scalable systems that enabled business growth and customer satisfaction",
    pastPledge: "I pledged to always write clean, maintainable code and to share my knowledge freely with others to help them grow in their careers",
    presentQuest: "I am now driven by the vision of transforming how professionals discover their purpose and build meaningful careers through technology",
    presentService: "I serve by creating AI-powered coaching experiences that help people uncover their authentic professional story and connect with their true calling",
    presentPledge: "I pledge to build technology that honors human dignity and helps every person realize their unique potential and contribution to the world",
    futureQuest: "I will be driven to democratize access to transformational career coaching and create a world where everyone can pursue work aligned with their purpose",
    futureService: "I will serve by building platforms that connect purpose-driven professionals and enable them to create exponential positive impact together",
    futurePledge: "I pledge to dedicate my skills to closing the gap between human potential and opportunity, ensuring no talent goes undiscovered or unfulfilled"
  }

  const initializeUser = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/test/init-user', {
        method: 'POST',
      })
      const data = await response.json()
      if (data.success) {
        setUserInitialized(true)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    }
    setLoading(false)
  }

  const testGetTrinity = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/trinity')
      const data = await response.json()
      setTrinityData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    }
    setLoading(false)
  }

  const testSaveTrinity = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/trinity', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(sampleTrinity),
      })
      const data = await response.json()
      setTrinityData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    }
    setLoading(false)
  }

  const testReadiness = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/quest/readiness', {
        method: 'POST',
      })
      const data = await response.json()
      setReadinessData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    }
    setLoading(false)
  }

  return (
    <div className="container mx-auto p-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-8">Trinity & Quest Readiness Test</h1>
      
      {/* User Initialization */}
      {!userInitialized && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-2">Initialize User First</h2>
          <p className="text-sm text-gray-600 mb-4">
            You need to initialize your user account before testing the Trinity endpoints.
          </p>
          <button
            onClick={initializeUser}
            disabled={loading}
            className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50"
          >
            Initialize User
          </button>
        </div>
      )}
      
      <div className="space-y-6">
        {/* Trinity Test Section */}
        <div className="border rounded-lg p-6 bg-gray-50">
          <h2 className="text-xl font-semibold mb-4">Trinity Endpoints</h2>
          
          <div className="flex gap-4 mb-4">
            <button
              onClick={testGetTrinity}
              disabled={loading}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            >
              GET /api/trinity
            </button>
            
            <button
              onClick={testSaveTrinity}
              disabled={loading}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
            >
              POST /api/trinity (Save Sample)
            </button>
          </div>
          
          {trinityData && (
            <div className="bg-white p-4 rounded border">
              <h3 className="font-semibold mb-2">Trinity Response:</h3>
              <pre className="text-sm overflow-auto">
                {JSON.stringify(trinityData, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Readiness Test Section */}
        <div className="border rounded-lg p-6 bg-gray-50">
          <h2 className="text-xl font-semibold mb-4">Quest Readiness</h2>
          
          <button
            onClick={testReadiness}
            disabled={loading}
            className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50 mb-4"
          >
            POST /api/quest/readiness
          </button>
          
          {readinessData && (
            <div className="bg-white p-4 rounded border">
              <h3 className="font-semibold mb-2">Readiness Response:</h3>
              <pre className="text-sm overflow-auto">
                {JSON.stringify(readinessData, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded p-4">
            <p className="text-red-600">Error: {error}</p>
          </div>
        )}

        {/* Sample Data Display */}
        <div className="border rounded-lg p-6 bg-blue-50">
          <h2 className="text-xl font-semibold mb-4">Sample Trinity Data</h2>
          <div className="text-sm space-y-2">
            <p><strong>Past Quest:</strong> {sampleTrinity.pastQuest.substring(0, 80)}...</p>
            <p><strong>Present Quest:</strong> {sampleTrinity.presentQuest.substring(0, 80)}...</p>
            <p><strong>Future Quest:</strong> {sampleTrinity.futureQuest.substring(0, 80)}...</p>
          </div>
        </div>
      </div>
    </div>
  )
}