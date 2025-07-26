'use client'

import { useEffect, useState } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'

interface TimelineNode {
  id: string
  type: 'experience' | 'education' | 'skill'
  title: string
  subtitle: string
  date: string
  description?: string
}

export default function ProfessionalMirror() {
  const { user } = useUser()
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true)
  const [scrapingProgress, setScrapingProgress] = useState(0)
  const [timelineNodes, setTimelineNodes] = useState<TimelineNode[]>([])
  const [selectedNode, setSelectedNode] = useState<TimelineNode | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!user) {
      router.push('/')
      return
    }

    const linkedinUrl = sessionStorage.getItem('questLinkedInUrl')
    if (!linkedinUrl) {
      router.push('/')
      return
    }

    // Start the scraping process
    startScraping(linkedinUrl)
  }, [user, router])

  const startScraping = async (linkedinUrl: string) => {
    try {
      setScrapingProgress(10)
      
      // Call API to start scraping
      const response = await fetch('/api/journey/scrape', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ linkedinUrl }),
      })

      if (!response.ok) {
        throw new Error('Failed to start scraping')
      }

      // Simulate progressive reveal
      const progressIntervals = [30, 50, 70, 90, 100]
      for (const progress of progressIntervals) {
        await new Promise(resolve => setTimeout(resolve, 1000))
        setScrapingProgress(progress)
      }

      const data = await response.json()
      
      // Transform data into timeline nodes
      const nodes: TimelineNode[] = []
      
      // Add experiences
      data.experiences?.forEach((exp: any, index: number) => {
        nodes.push({
          id: `exp-${index}`,
          type: 'experience',
          title: exp.title,
          subtitle: exp.companyName,
          date: exp.startDate || 'Present',
          description: exp.description,
        })
      })

      // Add education
      data.education?.forEach((edu: any, index: number) => {
        nodes.push({
          id: `edu-${index}`,
          type: 'education',
          title: edu.degree || 'Education',
          subtitle: edu.schoolName,
          date: edu.endDate || 'Present',
          description: edu.fieldOfStudy,
        })
      })

      setTimelineNodes(nodes)
      setIsLoading(false)
    } catch (err) {
      console.error('Scraping error:', err)
      setError('Failed to discover your professional story. Please try again.')
      setIsLoading(false)
    }
  }

  const handleNodeClick = (node: TimelineNode) => {
    setSelectedNode(node)
  }

  const handleContinue = () => {
    router.push('/journey/trinity')
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold mb-4">Something went wrong</h2>
          <p className="text-gray-400 mb-8">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="px-6 py-3 bg-blue-500 rounded-lg hover:bg-blue-600 transition-colors"
          >
            Start Over
          </button>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-3xl font-semibold mb-8">Discovering Your Professional Story</h2>
          
          <div className="w-64 h-2 bg-gray-700 rounded-full overflow-hidden mb-4 mx-auto">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-1000"
              style={{ width: `${scrapingProgress}%` }}
            />
          </div>
          
          <p className="text-gray-400">
            {scrapingProgress < 30 && "Accessing your LinkedIn profile..."}
            {scrapingProgress >= 30 && scrapingProgress < 50 && "Analyzing your experience..."}
            {scrapingProgress >= 50 && scrapingProgress < 70 && "Discovering patterns..."}
            {scrapingProgress >= 70 && scrapingProgress < 90 && "Building your professional mirror..."}
            {scrapingProgress >= 90 && "Almost ready..."}
          </p>
        </div>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Your Professional Mirror</h1>
            <p className="text-xl text-gray-400">This is how the world sees you</p>
            <p className="text-sm text-gray-500 mt-2">Click any node to correct our understanding</p>
          </div>

          {/* Timeline Visualization */}
          <div className="relative mb-12">
            <div className="absolute left-1/2 transform -translate-x-1/2 h-full w-1 bg-gray-700"></div>
            
            {timelineNodes.map((node, index) => (
              <div
                key={node.id}
                className={`relative flex items-center mb-8 ${
                  index % 2 === 0 ? 'justify-start' : 'justify-end'
                }`}
              >
                <div
                  className={`w-5/12 ${index % 2 === 0 ? 'pr-8 text-right' : 'pl-8'}`}
                  onClick={() => handleNodeClick(node)}
                >
                  <div className="bg-gray-800 p-6 rounded-lg hover:bg-gray-700 cursor-pointer transition-colors">
                    <h3 className="text-lg font-semibold mb-1">{node.title}</h3>
                    <p className="text-gray-400 mb-2">{node.subtitle}</p>
                    <p className="text-sm text-gray-500">{node.date}</p>
                    {node.description && (
                      <p className="text-sm text-gray-300 mt-2">{node.description}</p>
                    )}
                  </div>
                </div>
                
                <div className="absolute left-1/2 transform -translate-x-1/2 w-4 h-4 bg-blue-500 rounded-full"></div>
              </div>
            ))}
          </div>

          {/* Selected Node Edit */}
          {selectedNode && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
              <div className="bg-gray-800 rounded-lg p-8 max-w-lg w-full">
                <h3 className="text-xl font-semibold mb-4">Correct Our Understanding</h3>
                <p className="text-gray-400 mb-6">
                  Help us better understand this part of your journey
                </p>
                
                <div className="space-y-4 mb-6">
                  <input
                    type="text"
                    value={selectedNode.title}
                    className="w-full px-4 py-2 bg-gray-700 rounded-lg"
                    placeholder="Title"
                  />
                  <input
                    type="text"
                    value={selectedNode.subtitle}
                    className="w-full px-4 py-2 bg-gray-700 rounded-lg"
                    placeholder="Organization"
                  />
                  <textarea
                    className="w-full px-4 py-2 bg-gray-700 rounded-lg h-24"
                    placeholder="Tell us more about this experience..."
                  />
                </div>
                
                <div className="flex gap-4">
                  <button
                    onClick={() => setSelectedNode(null)}
                    className="flex-1 py-2 bg-gray-600 rounded-lg hover:bg-gray-500 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => setSelectedNode(null)}
                    className="flex-1 py-2 bg-blue-500 rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    Save
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Continue Button */}
          <div className="text-center">
            <p className="text-gray-400 mb-6">
              Here's what we found (and might have missed)
            </p>
            <button
              onClick={handleContinue}
              className="px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg font-semibold hover:from-blue-600 hover:to-purple-700 transition-all"
            >
              Continue to Trinity Discovery
            </button>
          </div>
        </div>
      </div>
    </main>
  )
}