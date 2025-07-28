'use client'

import { useState } from 'react'

export default function TestScraperPage() {
  const [companyUrl, setCompanyUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch('/api/debug/scrape-company', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ companyUrl })
      })

      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to scrape')
      }

      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Test Company Scraper</h1>
        
        <form onSubmit={handleSubmit} className="mb-8">
          <div className="flex gap-4">
            <input
              type="url"
              value={companyUrl}
              onChange={(e) => setCompanyUrl(e.target.value)}
              placeholder="https://www.linkedin.com/company/example/"
              className="flex-1 px-4 py-2 bg-gray-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50"
            >
              {loading ? 'Scraping...' : 'Scrape Company'}
            </button>
          </div>
        </form>

        {error && (
          <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 mb-4">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {result && (
          <div className="bg-gray-800 rounded-lg p-6 space-y-4">
            <h2 className="text-xl font-semibold">Scraping Results</h2>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Company:</span>
                <p>{result.company?.name} ({result.company?.domain})</p>
              </div>
              <div>
                <span className="text-gray-400">Total Employees Found:</span>
                <p>{result.totalEmployees}</p>
              </div>
              <div>
                <span className="text-gray-400">Scraped Count:</span>
                <p>{result.scrapedCount}</p>
              </div>
              <div>
                <span className="text-gray-400">Saved to Database:</span>
                <p>{result.savedCount}</p>
              </div>
            </div>

            <div className="mt-4 p-4 bg-gray-900 rounded">
              <h3 className="text-sm font-semibold mb-2">Raw Response:</h3>
              <pre className="text-xs overflow-auto">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}