'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'

export default function ProfessionalMirrorPage() {
  const { isSignedIn, user } = useUser()
  const router = useRouter()
  const [linkedinUrl, setLinkedinUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [userProfile, setUserProfile] = useState<any>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    } else {
      fetchUserProfile()
    }
  }, [isSignedIn, router])

  const fetchUserProfile = async () => {
    try {
      const response = await fetch('/api/user-workaround')
      const data = await response.json()
      setUserProfile(data)
      
      // If they already have a professional mirror, redirect to trinity
      if (data.databaseUser?.professionalMirror) {
        router.push('/trinity')
      }
    } catch (error) {
      console.error('Error fetching profile:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await fetch('/api/professional-mirror', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ linkedinUrl })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to create professional mirror')
      }

      // Success! Redirect to trinity discovery
      router.push('/trinity')
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Something went wrong')
      setLoading(false)
    }
  }

  if (!userProfile) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white flex items-center justify-center">
        <p>Loading...</p>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
            Professional Mirror
          </h1>
          
          <p className="text-xl mb-4 text-gray-300">
            How the world sees you professionally
          </p>
          
          <p className="text-lg mb-8 text-gray-400">
            We'll analyze your LinkedIn profile to understand your professional journey. 
            This is the first step in discovering your Quest.
          </p>

          <div className="bg-gray-800 rounded-lg p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="linkedin" className="block text-sm font-medium mb-2">
                  Your LinkedIn Profile URL
                </label>
                <input
                  id="linkedin"
                  type="url"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  placeholder="https://www.linkedin.com/in/your-profile"
                  className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  pattern="https?://(www\.)?linkedin\.com/in/.*"
                />
                <p className="text-sm text-gray-500 mt-2">
                  Example: https://www.linkedin.com/in/keegan-dan
                </p>
              </div>

              {error && (
                <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 text-red-400">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Analyzing...' : 'Analyze My Professional Mirror'}
              </button>
            </form>

            <div className="mt-8 p-4 bg-gray-900 rounded-lg">
              <h3 className="text-sm font-semibold mb-2">What happens next?</h3>
              <ol className="text-sm text-gray-400 space-y-2">
                <li>1. We'll scan your LinkedIn profile</li>
                <li>2. Extract your professional experiences and skills</li>
                <li>3. Begin your Trinity discovery process</li>
                <li>4. Help you earn your Quest through your story</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}