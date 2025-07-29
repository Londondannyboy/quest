'use client'

import { useState, useEffect, Suspense } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import dynamic from 'next/dynamic'

// Dynamic import to avoid SSR issues
const TrinityVisualization = dynamic(
  () => import('@/components/trinity-visualization'),
  { 
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full">
        <div className="text-white">Loading 3D Visualization...</div>
      </div>
    )
  }
)

interface Trinity {
  pastQuest?: string | null
  pastService?: string | null
  pastPledge?: string | null
  presentQuest?: string | null
  presentService?: string | null
  presentPledge?: string | null
  futureQuest?: string | null
  futureService?: string | null
  futurePledge?: string | null
  clarityScore?: number
}

function TrinityVisualizationContent() {
  const { isSignedIn } = useUser()
  const router = useRouter()
  const searchParams = useSearchParams()
  const [trinity, setTrinity] = useState<Trinity | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  
  const variant = searchParams.get('variant') as 'timeline' | 'spiral' | 'circular' | 'columns' || 'timeline'

  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
      return
    }
    fetchTrinity()
  }, [isSignedIn, router])

  const fetchTrinity = async () => {
    try {
      const response = await fetch('/api/trinity')
      if (response.ok) {
        const data = await response.json()
        setTrinity(data.trinity)
      }
    } catch (error) {
      console.error('Failed to fetch Trinity:', error)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white">Loading Trinity data...</div>
      </div>
    )
  }

  if (!trinity) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-white mb-4">No Trinity data found</p>
          <Link href="/trinity" className="text-blue-400 hover:underline">
            Create your Trinity
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="h-screen relative">
        <TrinityVisualization
          pastTrinity={{
            quest: trinity.pastQuest,
            service: trinity.pastService,
            pledge: trinity.pastPledge
          }}
          presentTrinity={{
            quest: trinity.presentQuest,
            service: trinity.presentService,
            pledge: trinity.presentPledge
          }}
          futureTrinity={{
            quest: trinity.futureQuest,
            service: trinity.futureService,
            pledge: trinity.futurePledge
          }}
          clarityScore={trinity.clarityScore}
          variant={variant}
        />
        
        {/* Navigation */}
        <div className="absolute bottom-4 left-4 flex gap-4">
          <Link
            href="/trinity"
            className="bg-gray-800 text-white px-4 py-2 rounded hover:bg-gray-700 transition-colors"
          >
            Edit Trinity
          </Link>
          <Link
            href="/quest"
            className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 transition-colors"
          >
            View Quest
          </Link>
        </div>
      </div>
    </div>
  )
}

export default function TrinityVisualizationPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    }>
      <TrinityVisualizationContent />
    </Suspense>
  )
}