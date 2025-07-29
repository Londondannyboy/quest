'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'

interface Trinity {
  pastQuest?: string
  pastService?: string
  pastPledge?: string
  presentQuest?: string
  presentService?: string
  presentPledge?: string
  futureQuest?: string
  futureService?: string
  futurePledge?: string
  clarityScore: number
}

interface GeneratedContent {
  summary?: string
  linkedin?: string
  bio?: string
  pitch?: string
}

export default function QuestPage() {
  const { isSignedIn } = useUser()
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true)
  const [isQuestReady, setIsQuestReady] = useState(false)
  const [trinity, setTrinity] = useState<Trinity | null>(null)
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent>({})
  const [activeTab, setActiveTab] = useState<'summary' | 'linkedin' | 'bio' | 'pitch'>('summary')
  const [isGenerating, setIsGenerating] = useState(false)
  const [copiedField, setCopiedField] = useState<string | null>(null)

  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
      return
    }
    checkQuestReadiness()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSignedIn, router])

  const checkQuestReadiness = async () => {
    try {
      const response = await fetch('/api/quest/readiness')
      const data = await response.json()
      
      if (data.isReady) {
        setIsQuestReady(true)
        setTrinity(data.trinity)
        // Generate initial summary
        generateContent('summary')
      } else {
        // Not quest ready, redirect to readiness page
        router.push('/quest-readiness')
      }
    } catch (error) {
      console.error('Failed to check quest readiness:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const generateContent = async (type: typeof activeTab) => {
    if (!trinity || generatedContent[type]) return
    
    setIsGenerating(true)
    try {
      const response = await fetch('/api/quest/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type })
      })
      
      if (response.ok) {
        const data = await response.json()
        setGeneratedContent(prev => ({
          ...prev,
          [type]: data.content
        }))
      }
    } catch (error) {
      console.error('Failed to generate content:', error)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab)
    if (!generatedContent[tab]) {
      generateContent(tab)
    }
  }

  const copyToClipboard = async (text: string, field: string) => {
    await navigator.clipboard.writeText(text)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  const regenerateContent = async () => {
    setGeneratedContent(prev => ({
      ...prev,
      [activeTab]: undefined
    }))
    generateContent(activeTab)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p>Checking Quest readiness...</p>
        </div>
      </div>
    )
  }

  if (!isQuestReady) {
    return null // Router will redirect
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Your Quest Activation</h1>
          <p className="text-xl text-gray-400">
            Transform your Trinity into powerful professional assets
          </p>
        </div>

        {/* Trinity Summary */}
        <div className="bg-gray-800 p-6 rounded-lg mb-8">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-2xl font-semibold">Your Trinity Evolution</h2>
            <a 
              href="/trinity-visualization"
              className="text-blue-400 hover:text-blue-300 text-sm"
            >
              View 3D Visualization →
            </a>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Past */}
            <div>
              <h3 className="text-blue-400 font-semibold mb-2">Past</h3>
              <div className="space-y-2 text-sm">
                <p><span className="text-gray-500">Quest:</span> {trinity?.pastQuest}</p>
                <p><span className="text-gray-500">Service:</span> {trinity?.pastService}</p>
                <p><span className="text-gray-500">Pledge:</span> {trinity?.pastPledge}</p>
              </div>
            </div>
            
            {/* Present */}
            <div>
              <h3 className="text-green-400 font-semibold mb-2">Present</h3>
              <div className="space-y-2 text-sm">
                <p><span className="text-gray-500">Quest:</span> {trinity?.presentQuest}</p>
                <p><span className="text-gray-500">Service:</span> {trinity?.presentService}</p>
                <p><span className="text-gray-500">Pledge:</span> {trinity?.presentPledge}</p>
              </div>
            </div>
            
            {/* Future */}
            <div>
              <h3 className="text-purple-400 font-semibold mb-2">Future</h3>
              <div className="space-y-2 text-sm">
                <p><span className="text-gray-500">Quest:</span> {trinity?.futureQuest}</p>
                <p><span className="text-gray-500">Service:</span> {trinity?.futureService}</p>
                <p><span className="text-gray-500">Pledge:</span> {trinity?.futurePledge}</p>
              </div>
            </div>
          </div>
          
          <div className="mt-4 pt-4 border-t border-gray-700">
            <p className="text-sm text-gray-400">
              Trinity Clarity Score: <span className="text-white font-semibold">{trinity?.clarityScore}%</span>
            </p>
          </div>
        </div>

        {/* Content Generation Tabs */}
        <div className="bg-gray-800 rounded-lg">
          {/* Tab Navigation */}
          <div className="flex border-b border-gray-700">
            {(['summary', 'linkedin', 'bio', 'pitch'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => handleTabChange(tab)}
                className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab
                    ? 'text-white border-b-2 border-blue-500'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
                {tab === 'linkedin' && ' About'}
                {tab === 'bio' && ' (3rd Person)'}
                {tab === 'pitch' && ' (30s)'}
              </button>
            ))}
          </div>

          {/* Content Area */}
          <div className="p-6">
            {isGenerating ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
                <p className="text-gray-400">Generating your {activeTab}...</p>
              </div>
            ) : generatedContent[activeTab] ? (
              <div>
                <div className="bg-gray-900 p-4 rounded-lg mb-4">
                  <pre className="whitespace-pre-wrap text-sm leading-relaxed">
                    {generatedContent[activeTab]}
                  </pre>
                </div>
                
                {/* Actions */}
                <div className="flex gap-2">
                  <button
                    onClick={() => copyToClipboard(generatedContent[activeTab]!, activeTab)}
                    className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700 transition-colors"
                  >
                    {copiedField === activeTab ? 'Copied!' : 'Copy to Clipboard'}
                  </button>
                  <button
                    onClick={regenerateContent}
                    className="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600 transition-colors"
                  >
                    Regenerate
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-400">Content will be generated here</p>
              </div>
            )}
          </div>
        </div>

        {/* Next Steps */}
        <div className="mt-12 bg-gradient-to-r from-blue-900 to-purple-900 p-6 rounded-lg">
          <h2 className="text-2xl font-semibold mb-4">Next Steps</h2>
          <div className="space-y-3">
            <div className="flex items-start">
              <span className="text-2xl mr-3">1️⃣</span>
              <div>
                <h3 className="font-semibold">Update Your LinkedIn</h3>
                <p className="text-sm text-gray-300">Use the generated LinkedIn About section to refresh your profile</p>
              </div>
            </div>
            <div className="flex items-start">
              <span className="text-2xl mr-3">2️⃣</span>
              <div>
                <h3 className="font-semibold">Practice Your Pitch</h3>
                <p className="text-sm text-gray-300">Rehearse your 30-second pitch until it feels natural</p>
              </div>
            </div>
            <div className="flex items-start">
              <span className="text-2xl mr-3">3️⃣</span>
              <div>
                <h3 className="font-semibold">Share Your Quest</h3>
                <p className="text-sm text-gray-300">Start conversations about your future vision</p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex justify-center gap-4">
          <button
            onClick={() => router.push('/trinity')}
            className="px-6 py-3 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors"
          >
            Refine Trinity
          </button>
          <button
            onClick={() => window.print()}
            className="px-6 py-3 bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Download Quest Kit
          </button>
        </div>
      </div>
    </main>
  )
}