'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { SignInButton, useUser } from '@clerk/nextjs'

export function JourneyEntry() {
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
  )
}