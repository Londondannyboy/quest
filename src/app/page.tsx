'use client'

import { useState } from 'react'
import { SignInButton, SignOutButton, useUser } from '@clerk/nextjs'

function AuthContent() {
  const { isSignedIn, user } = useUser()
  const [userInfo, setUserInfo] = useState<Record<string, unknown> | null>(null)

  const checkUser = async () => {
    try {
      const response = await fetch('/api/user-workaround')
      const data = await response.json()
      setUserInfo(data)
    } catch (error) {
      console.error('Error fetching user:', error)
    }
  }

  const syncUser = async () => {
    try {
      const response = await fetch('/api/user/sync-workaround', { method: 'POST' })
      const data = await response.json()
      
      if (!response.ok) {
        console.error('Sync error:', data)
        alert(`Sync failed: ${data.error}\n\n${data.details}\n\n${data.solution || ''}`)
        return
      }
      
      alert(data.message || 'Sync complete!')
      checkUser() // Refresh user info
    } catch (error) {
      console.error('Error syncing user:', error)
      alert('Sync failed! Check console for details.')
    }
  }

  return (
    <div className="bg-gray-800 rounded-lg p-8 max-w-2xl mx-auto">
      {isSignedIn ? (
        <>
          <h2 className="text-2xl font-semibold mb-4">Welcome back!</h2>
          <p className="text-gray-300 mb-2">
            Hello {user.firstName || user.emailAddresses?.[0]?.emailAddress}
          </p>
          <p className="text-sm text-gray-400 mb-6">
            Clerk ID: {user.id}
          </p>
          
          <div className="flex flex-wrap gap-4 mb-6">
            <button
              onClick={checkUser}
              className="px-6 py-3 bg-blue-500 rounded-lg hover:bg-blue-600 transition-colors"
            >
              Check User API
            </button>
            
            <button
              onClick={syncUser}
              className="px-6 py-3 bg-green-500 rounded-lg hover:bg-green-600 transition-colors"
            >
              Sync to Database
            </button>
            
            <button
              onClick={async () => {
                const res = await fetch('/api/health')
                const data = await res.json()
                console.log('Health check:', data)
                alert(`Database: ${data.database.connected ? 'Connected' : 'Not Connected'}\n${data.database.error || ''}`)
              }}
              className="px-6 py-3 bg-yellow-500 rounded-lg hover:bg-yellow-600 transition-colors"
            >
              Check Database
            </button>
            
            <SignOutButton>
              <button className="px-6 py-3 bg-red-500 rounded-lg hover:bg-red-600 transition-colors">
                Sign Out
              </button>
            </SignOutButton>
          </div>
          
          {userInfo?.databaseStatus === 'synced' && (
            <div className="mt-8">
              <a 
                href="/professional-mirror"
                className="inline-block px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all text-lg font-semibold"
              >
                Begin Your Quest Journey →
              </a>
            </div>
          )}
          
          {userInfo && (
            <div className="mt-6 p-4 bg-gray-900 rounded-lg">
              <p className="text-sm font-mono">API Response:</p>
              <pre className="text-xs mt-2 overflow-auto">
                {JSON.stringify(userInfo, null, 2)}
              </pre>
            </div>
          )}
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