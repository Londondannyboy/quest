'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'

export default function VoiceCoachDebugPage() {
  const { isSignedIn } = useUser()
  const router = useRouter()
  const [debugResult, setDebugResult] = useState<{
    error?: string
    analysis?: string
    suggestions?: string[]
    codeChanges?: string[]
    report?: string
    confidence?: number
  } | null>(null)
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState('')
  const [selectedAction, setSelectedAction] = useState('analyze-code')

  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    }
  }, [isSignedIn, router])

  const runDebug = async () => {
    setLoading(true)
    setDebugResult(null)
    
    try {
      const response = await fetch('/api/debug/voice-coach', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: selectedAction,
          sessionId: sessionId || undefined,
          issue: 'Duplicate voice streams, no interruption capability, user context not working'
        })
      })
      
      const data = await response.json()
      setDebugResult(data)
    } catch (error) {
      console.error('Debug error:', error)
      setDebugResult({ error: 'Debug failed' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Voice Coach AI Debugger</h1>
        
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Debug Controls</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Debug Action</label>
              <select
                value={selectedAction}
                onChange={(e) => setSelectedAction(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 rounded"
              >
                <option value="analyze-code">Analyze Code for Issues</option>
                <option value="debug-session">Debug Specific Session</option>
                <option value="generate-report">Generate Session Report</option>
              </select>
            </div>
            
            {(selectedAction === 'debug-session' || selectedAction === 'generate-report') && (
              <div>
                <label className="block text-sm font-medium mb-2">Session ID</label>
                <input
                  type="text"
                  value={sessionId}
                  onChange={(e) => setSessionId(e.target.value)}
                  placeholder="Enter Zep session ID"
                  className="w-full px-3 py-2 bg-gray-700 rounded"
                />
              </div>
            )}
            
            <button
              onClick={runDebug}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded font-medium disabled:opacity-50"
            >
              {loading ? 'Running Debug...' : 'Run Debug Analysis'}
            </button>
          </div>
        </div>
        
        {debugResult && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Debug Results</h2>
            
            {debugResult.error ? (
              <p className="text-red-400">{debugResult.error}</p>
            ) : (
              <div className="space-y-4">
                {debugResult.analysis && (
                  <div>
                    <h3 className="font-medium mb-2">Analysis</h3>
                    <p className="text-gray-300 whitespace-pre-wrap">{debugResult.analysis}</p>
                  </div>
                )}
                
                {debugResult.suggestions && debugResult.suggestions.length > 0 && (
                  <div>
                    <h3 className="font-medium mb-2">Suggestions</h3>
                    <ul className="list-disc list-inside space-y-1">
                      {debugResult.suggestions.map((s: string, i: number) => (
                        <li key={i} className="text-gray-300">{s}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {debugResult.codeChanges && debugResult.codeChanges.length > 0 && (
                  <div>
                    <h3 className="font-medium mb-2">Suggested Code Changes</h3>
                    {debugResult.codeChanges.map((code: string, i: number) => (
                      <pre key={i} className="bg-gray-900 p-3 rounded text-sm overflow-x-auto mb-2">
                        <code>{code}</code>
                      </pre>
                    ))}
                  </div>
                )}
                
                {debugResult.report && (
                  <div>
                    <h3 className="font-medium mb-2">Session Report</h3>
                    <pre className="bg-gray-900 p-3 rounded text-sm overflow-x-auto whitespace-pre-wrap">
                      {debugResult.report}
                    </pre>
                  </div>
                )}
                
                {debugResult.confidence !== undefined && (
                  <div>
                    <h3 className="font-medium mb-2">Confidence</h3>
                    <div className="w-full bg-gray-700 rounded">
                      <div 
                        className="bg-green-600 text-xs font-medium text-center p-1 rounded"
                        style={{ width: `${debugResult.confidence * 100}%` }}
                      >
                        {(debugResult.confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        
        <div className="mt-8 space-y-2">
          <a href="/trinity" className="text-blue-400 hover:text-blue-300">
            ← Back to Trinity Voice Coach
          </a>
          <br />
          <a href="/hume-diagnostic" className="text-blue-400 hover:text-blue-300">
            View Hume Diagnostic
          </a>
        </div>
      </div>
    </main>
  )
}