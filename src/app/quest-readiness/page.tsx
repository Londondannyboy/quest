'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface ReadinessData {
  score: number
  outcome: 'QUEST_READY' | 'PREPARING' | 'NOT_YET'
  components: {
    storyDepth: number
    trinityClarity: number
    futureOrientation: number
  }
}

export default function QuestReadinessPage() {
  const { isSignedIn } = useUser()
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [readiness, setReadiness] = useState<ReadinessData | null>(null)
  const [message, setMessage] = useState('')
  const [nextSteps, setNextSteps] = useState<string[]>([])

  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
      return
    }

    checkReadiness()
  }, [isSignedIn, router])

  const checkReadiness = async () => {
    try {
      const response = await fetch('/api/quest/readiness', {
        method: 'POST',
      })

      const data = await response.json()

      if (response.ok) {
        setReadiness(data.readiness)
        setMessage(data.message)
        setNextSteps(data.nextSteps || [])
      } else {
        console.error('Readiness check failed:', data.error)
      }
    } catch (error) {
      console.error('Error checking readiness:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-pulse text-4xl mb-4">⚖️</div>
          <p className="text-xl">Evaluating your Quest readiness...</p>
        </div>
      </div>
    )
  }

  if (!readiness) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-xl mb-4">Unable to check readiness</p>
          <Link href="/trinity" className="text-blue-400 hover:text-blue-300">
            ← Return to Trinity
          </Link>
        </div>
      </div>
    )
  }

  const getOutcomeColor = () => {
    switch (readiness.outcome) {
      case 'QUEST_READY':
        return 'from-green-400 to-emerald-600'
      case 'PREPARING':
        return 'from-yellow-400 to-orange-600'
      case 'NOT_YET':
        return 'from-gray-400 to-gray-600'
    }
  }

  const getOutcomeEmoji = () => {
    switch (readiness.outcome) {
      case 'QUEST_READY':
        return '🎉'
      case 'PREPARING':
        return '🌱'
      case 'NOT_YET':
        return '🌅'
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              Quest Readiness Assessment
            </h1>
            <p className="text-xl text-gray-400">
              Your journey to Quest has been evaluated
            </p>
          </div>

          {/* Outcome Display */}
          <div className="mb-12">
            <div className={`bg-gradient-to-r ${getOutcomeColor()} rounded-2xl p-8 text-center text-black`}>
              <div className="text-6xl mb-4">{getOutcomeEmoji()}</div>
              <h2 className="text-3xl font-bold mb-2">
                {readiness.outcome === 'QUEST_READY' ? 'Quest Ready!' :
                 readiness.outcome === 'PREPARING' ? 'Preparing' : 'Not Yet'}
              </h2>
              <p className="text-xl opacity-90">
                Readiness Score: {readiness.score}%
              </p>
            </div>
          </div>

          {/* Message */}
          <div className="bg-gray-800 rounded-lg p-6 mb-8">
            <p className="text-lg text-gray-300 leading-relaxed">
              {message}
            </p>
          </div>

          {/* Component Scores */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">Story Depth</h3>
              <div className="relative pt-1">
                <div className="overflow-hidden h-4 text-xs flex rounded bg-gray-700">
                  <div
                    style={{ width: `${readiness.components.storyDepth}%` }}
                    className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-purple-500"
                  />
                </div>
              </div>
              <p className="text-sm text-gray-400 mt-2">
                {readiness.components.storyDepth}%
              </p>
            </div>

            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">Trinity Clarity</h3>
              <div className="relative pt-1">
                <div className="overflow-hidden h-4 text-xs flex rounded bg-gray-700">
                  <div
                    style={{ width: `${readiness.components.trinityClarity}%` }}
                    className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-500"
                  />
                </div>
              </div>
              <p className="text-sm text-gray-400 mt-2">
                {readiness.components.trinityClarity}%
              </p>
            </div>

            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">Future Orientation</h3>
              <div className="relative pt-1">
                <div className="overflow-hidden h-4 text-xs flex rounded bg-gray-700">
                  <div
                    style={{ width: `${readiness.components.futureOrientation}%` }}
                    className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-green-500"
                  />
                </div>
              </div>
              <p className="text-sm text-gray-400 mt-2">
                {readiness.components.futureOrientation}%
              </p>
            </div>
          </div>

          {/* Next Steps */}
          {nextSteps.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-6 mb-8">
              <h3 className="text-xl font-semibold mb-4">Next Steps</h3>
              <ul className="space-y-3">
                {nextSteps.map((step, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-blue-400 mr-3">→</span>
                    <span className="text-gray-300">{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {readiness.outcome === 'QUEST_READY' ? (
              <Link
                href="/quest"
                className="px-8 py-4 bg-gradient-to-r from-green-500 to-emerald-600 rounded-lg hover:from-green-600 hover:to-emerald-700 transition-all text-lg font-semibold text-center"
              >
                Activate Your Quest →
              </Link>
            ) : (
              <Link
                href="/trinity"
                className="px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all text-lg font-semibold text-center"
              >
                Refine Your Trinity →
              </Link>
            )}
            
            <Link
              href="/professional-mirror"
              className="px-8 py-4 bg-gray-700 rounded-lg hover:bg-gray-600 transition-all text-lg font-semibold text-center"
            >
              Update Professional Mirror
            </Link>
          </div>

          {/* Philosophy Note */}
          <div className="mt-12 p-6 bg-gray-900 rounded-lg text-center">
            <p className="text-gray-400 italic">
              &ldquo;Quest must be earned through story. Only ~30% achieve Quest Ready on their first attempt.
              This is by design - your Quest should represent a true calling, not a casual choice.&rdquo;
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}