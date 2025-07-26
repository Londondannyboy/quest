'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { SignInButton, useUser } from '@clerk/nextjs'

export default function Home() {
  const [linkedinUrl, setLinkedinUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()
  const { isSignedIn } = useUser()

  const handleBeginJourney = async () => {
    if (!linkedinUrl) return
    
    setIsLoading(true)
    
    // Store LinkedIn URL in session storage for after auth
    sessionStorage.setItem('questLinkedInUrl', linkedinUrl)
    
    if (isSignedIn) {
      // Already signed in, go directly to journey
      router.push('/journey/professional-mirror')
    } else {
      // Will redirect to sign in, then to journey
      const signInBtn = document.querySelector('[data-clerk-sign-in]') as HTMLElement
      signInBtn?.click()
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          {/* Hero Section */}
          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
            Quest Core V2
          </h1>
          
          <p className="text-xl md:text-2xl mb-4 text-gray-300">
            You can&apos;t begin your Quest until we understand your story
          </p>
          
          <p className="text-lg mb-12 text-gray-400">
            A revolutionary professional development platform where you must earn your Quest through story
          </p>

          {/* Philosophy */}
          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-2 text-blue-400">Story</h3>
              <p className="text-gray-300">Begin with your authentic professional narrative</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-2 text-purple-400">Trinity</h3>
              <p className="text-gray-300">Discover your Quest, Service, and Pledge through time</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-2 text-green-400">Quest</h3>
              <p className="text-gray-300">Earn your Quest - only 30% achieve readiness</p>
            </div>
          </div>

          {/* Entry Point */}
          <div className="bg-gray-800 rounded-lg p-8 max-w-2xl mx-auto">
            <h2 className="text-2xl font-semibold mb-6">Begin Your Story</h2>
            
            <p className="text-gray-300 mb-6">
              May we discover your professional story? Share your LinkedIn profile to begin.
            </p>

            <div className="space-y-4">
              <input
                type="url"
                placeholder="https://linkedin.com/in/yourprofile"
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-gray-700 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading}
              />

              {isSignedIn ? (
                <button
                  onClick={handleBeginJourney}
                  disabled={!linkedinUrl || isLoading}
                  className="w-full py-3 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {isLoading ? 'Beginning Journey...' : 'Begin Your Journey'}
                </button>
              ) : (
                <div data-clerk-sign-in>
                  <SignInButton mode="modal" forceRedirectUrl="/journey/professional-mirror">
                    <button
                      onClick={() => sessionStorage.setItem('questLinkedInUrl', linkedinUrl)}
                      disabled={!linkedinUrl || isLoading}
                      className="w-full py-3 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      {isLoading ? 'Beginning Journey...' : 'Begin Your Journey'}
                    </button>
                  </SignInButton>
                </div>
              )}
            </div>

            <p className="text-sm text-gray-400 mt-4">
              Or search by name if you don&apos;t have your LinkedIn URL handy
            </p>
          </div>

          {/* Trust Indicators */}
          <div className="mt-16 text-center">
            <p className="text-gray-400 mb-4">Built on these principles:</p>
            <div className="flex flex-wrap justify-center gap-4 text-sm">
              <span className="px-4 py-2 bg-gray-800 rounded-full">Human dignity over conversion</span>
              <span className="px-4 py-2 bg-gray-800 rounded-full">Earned access creates aspiration</span>
              <span className="px-4 py-2 bg-gray-800 rounded-full">Story as foundation</span>
              <span className="px-4 py-2 bg-gray-800 rounded-full">Continuous evolution</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}