'use client'

import { useState, useEffect, useCallback } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface UserProfile {
  databaseUser?: {
    professionalMirror?: Record<string, unknown>
    [key: string]: unknown
  }
  [key: string]: unknown
}

export default function TrinityPage() {
  const { isSignedIn } = useUser()
  const router = useRouter()
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchUserProfile = useCallback(async () => {
    try {
      const response = await fetch('/api/user-workaround')
      const data = await response.json()
      setUserProfile(data)
      
      // If they don't have a professional mirror yet, redirect back
      if (!data.databaseUser?.professionalMirror) {
        router.push('/professional-mirror')
      }
      
      setLoading(false)
    } catch (error) {
      console.error('Error fetching profile:', error)
      setLoading(false)
    }
  }, [router])

  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    } else {
      fetchUserProfile()
    }
  }, [isSignedIn, router, fetchUserProfile])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white flex items-center justify-center">
        <p>Loading...</p>
      </div>
    )
  }

  const professionalMirror = userProfile?.databaseUser?.professionalMirror
  const linkedinData = professionalMirror?.rawLinkedinData as Record<string, unknown> | null

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
            Trinity Discovery
          </h1>
          
          <p className="text-xl mb-4 text-gray-300">
            Past → Present → Future
          </p>
          
          <p className="text-lg mb-8 text-gray-400">
            Your Trinity is the evolution of your professional self through time.
          </p>

          {/* Professional Mirror Summary */}
          {linkedinData && (
            <div className="bg-gray-800 rounded-lg p-6 mb-8">
              <h2 className="text-2xl font-semibold mb-4">Your Professional Mirror</h2>
              
              {linkedinData.name && (
                <p className="text-xl mb-2">{linkedinData.name as string}</p>
              )}
              
              {linkedinData.headline && (
                <p className="text-gray-400 mb-4">{linkedinData.headline as string}</p>
              )}
              
              {linkedinData.about && (
                <div className="text-gray-300 mb-4">
                  <h3 className="font-semibold mb-2">About</h3>
                  <p className="whitespace-pre-wrap">{linkedinData.about as string}</p>
                </div>
              )}
              
              <Link 
                href="/professional-mirror"
                className="text-blue-400 hover:text-blue-300 text-sm"
              >
                Update LinkedIn URL →
              </Link>
            </div>
          )}

          {/* Trinity Questions */}
          <div className="space-y-8">
            {/* Past */}
            <div className="bg-gray-800 rounded-lg p-8">
              <h2 className="text-3xl font-bold mb-4 text-purple-400">Past</h2>
              <p className="text-gray-400 mb-6">
                Where you&apos;ve been shapes who you are
              </p>
              
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold mb-2">Your Past Quest</h3>
                  <p className="text-sm text-gray-500 mb-3">
                    What was the driving mission that got you to where you are today?
                  </p>
                  <textarea 
                    className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 h-24"
                    placeholder="I wanted to..."
                  />
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-2">Your Past Service</h3>
                  <p className="text-sm text-gray-500 mb-3">
                    Who did you serve and how did you help them?
                  </p>
                  <textarea 
                    className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 h-24"
                    placeholder="I helped..."
                  />
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-2">Your Past Pledge</h3>
                  <p className="text-sm text-gray-500 mb-3">
                    What unique value did you promise to deliver?
                  </p>
                  <textarea 
                    className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 h-24"
                    placeholder="I pledged to..."
                  />
                </div>
              </div>
            </div>

            {/* Present */}
            <div className="bg-gray-800 rounded-lg p-8">
              <h2 className="text-3xl font-bold mb-4 text-blue-400">Present</h2>
              <p className="text-gray-400 mb-6">
                Where you are reveals your current truth
              </p>
              
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold mb-2">Your Present Quest</h3>
                  <p className="text-sm text-gray-500 mb-3">
                    What mission drives you today?
                  </p>
                  <textarea 
                    className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-24"
                    placeholder="I am working to..."
                  />
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-2">Your Present Service</h3>
                  <p className="text-sm text-gray-500 mb-3">
                    Who do you serve now and how?
                  </p>
                  <textarea 
                    className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-24"
                    placeholder="I currently help..."
                  />
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-2">Your Present Pledge</h3>
                  <p className="text-sm text-gray-500 mb-3">
                    What value do you deliver today?
                  </p>
                  <textarea 
                    className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-24"
                    placeholder="I deliver..."
                  />
                </div>
              </div>
            </div>

            {/* Future */}
            <div className="bg-gray-800 rounded-lg p-8">
              <h2 className="text-3xl font-bold mb-4 text-green-400">Future</h2>
              <p className="text-gray-400 mb-6">
                Where you&apos;re going defines your Quest
              </p>
              
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold mb-2">Your Future Quest</h3>
                  <p className="text-sm text-gray-500 mb-3">
                    What mission calls to you?
                  </p>
                  <textarea 
                    className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 h-24"
                    placeholder="I will..."
                  />
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-2">Your Future Service</h3>
                  <p className="text-sm text-gray-500 mb-3">
                    Who will you serve and how will you transform their lives?
                  </p>
                  <textarea 
                    className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 h-24"
                    placeholder="I will help..."
                  />
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-2">Your Future Pledge</h3>
                  <p className="text-sm text-gray-500 mb-3">
                    What unique value will you create in the world?
                  </p>
                  <textarea 
                    className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 h-24"
                    placeholder="I pledge to..."
                  />
                </div>
              </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-center">
              <button
                className="px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all text-lg font-semibold"
              >
                Save Trinity & Continue →
              </button>
            </div>
          </div>

          <div className="mt-12 p-6 bg-gray-900 rounded-lg">
            <h3 className="text-lg font-semibold mb-3">The Trinity Philosophy</h3>
            <p className="text-gray-400 mb-4">
              Your Trinity is not just a career summary. It&apos;s the evolution of your 
              professional soul through time.
            </p>
            <ul className="space-y-2 text-gray-400">
              <li>• Your Past reveals the patterns that shaped you</li>
              <li>• Your Present shows where your energy flows today</li>
              <li>• Your Future unveils the Quest you&apos;re meant to pursue</li>
            </ul>
            <p className="text-gray-400 mt-4">
              Only when all three align can your true Quest emerge.
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}