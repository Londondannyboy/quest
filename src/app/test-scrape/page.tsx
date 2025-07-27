'use client'

import { useState } from 'react'

interface ScrapeResult {
  success?: boolean
  error?: string
  details?: string
  data?: {
    name?: string
    headline?: string
    currentPosition?: {
      title: string
      company: string
    }
    skills?: string[]
  }
}

export default function TestScrapePage() {
  const [linkedinUrl, setLinkedinUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ScrapeResult | null>(null)

  const testScrape = async () => {
    setLoading(true)
    setResult(null)

    try {
      const response = await fetch('/api/test-scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ linkedinUrl })
      })

      const data = await response.json()
      setResult(data)
    } catch (error) {
      setResult({
        error: 'Network error',
        details: error instanceof Error ? error.message : 'Unknown error'
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Test LinkedIn Scraping</h1>
        
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <label className="block mb-2">LinkedIn Profile URL:</label>
          <input
            type="url"
            value={linkedinUrl}
            onChange={(e) => setLinkedinUrl(e.target.value)}
            placeholder="https://www.linkedin.com/in/username"
            className="w-full px-4 py-2 bg-gray-700 rounded mb-4"
          />
          
          <button
            onClick={testScrape}
            disabled={loading || !linkedinUrl}
            className="px-6 py-2 bg-blue-500 rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {loading ? 'Scraping...' : 'Test Scrape'}
          </button>
        </div>

        {result && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">
              {result.success ? '✅ Success!' : '❌ Failed'}
            </h2>
            
            <pre className="bg-gray-900 p-4 rounded overflow-auto max-h-96 text-sm">
              {JSON.stringify(result, null, 2)}
            </pre>
            
            {result.data && (
              <div className="mt-6 space-y-4">
                <h3 className="text-lg font-semibold">Extracted Data:</h3>
                
                {result.data.name && (
                  <p><strong>Name:</strong> {result.data.name}</p>
                )}
                
                {result.data.headline && (
                  <p><strong>Headline:</strong> {result.data.headline}</p>
                )}
                
                {result.data.currentPosition && (
                  <div>
                    <strong>Current Position:</strong>
                    <p className="ml-4">
                      {result.data.currentPosition.title} at {result.data.currentPosition.company}
                    </p>
                  </div>
                )}
                
                {result.data.skills && result.data.skills.length > 0 && (
                  <div>
                    <strong>Skills:</strong>
                    <p className="ml-4">{result.data.skills.join(', ')}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  )
}