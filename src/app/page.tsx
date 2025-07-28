'use client'

import { useEffect } from 'react'
import { SignInButton, SignOutButton, useUser } from '@clerk/nextjs'
import Link from 'next/link'
function AuthContent() {
  const { isSignedIn, user } = useUser()

  useEffect(() => {
    // Auto-sync user on sign in
    if (isSignedIn && user) {
      fetch('/api/user/sync', { method: 'POST' })
        .then(response => {
          if (!response.ok) {
            console.error('Failed to sync user')
          }
        })
        .catch(error => {
          console.error('Error syncing user:', error)
        })
    }
  }, [isSignedIn, user])

  return (
    <div className="bg-gray-800 rounded-lg p-8 max-w-2xl mx-auto">
      {isSignedIn ? (
        <>
          <h2 className="text-2xl font-semibold mb-4">Welcome back!</h2>
          <p className="text-gray-300 mb-6">
            Hello {user.firstName || user.emailAddresses?.[0]?.emailAddress}
          </p>
          
          <div className="space-y-4">
            <Link 
              href="/professional-mirror"
              className="block w-full px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all text-lg font-semibold text-center"
            >
              Begin Your Quest Journey →
            </Link>
            
            <div className="text-center">
              <SignOutButton>
                <button className="px-4 py-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors text-sm">
                  Sign Out
                </button>
              </SignOutButton>
            </div>
          </div>
        </>
      ) : (
        <>
          <h2 className="text-2xl font-semibold mb-6">Begin Your Journey</h2>
          <p className="text-gray-300 mb-6">
            Sign in to start your Quest
          </p>
          <SignInButton mode="modal">
            <button className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all">
              Sign In
            </button>
          </SignInButton>
        </>
      )}
    </div>
  )
}

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
            Quest Core V2
          </h1>
          
          <p className="text-xl md:text-2xl mb-4 text-gray-300">
            You can&apos;t begin your Quest until we understand your story
          </p>
          
          <p className="text-lg mb-12 text-gray-400">
            A revolutionary professional development platform
          </p>

          <AuthContent />
        </div>
      </div>
    </main>
  )
}