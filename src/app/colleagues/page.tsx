'use client'

import { useState, useEffect, useCallback } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'

interface Colleague {
  id: string
  name: string
  title?: string
  linkedinUrl: string
  profileImageUrl?: string
  company?: {
    name: string
    domain?: string
  }
  isQuestUser: boolean
}

export default function ColleaguesPage() {
  const { isSignedIn } = useUser()
  const router = useRouter()
  const [colleagues, setColleagues] = useState<Colleague[]>([])
  const [loading, setLoading] = useState(true)
  const [companyScraped, setCompanyScraped] = useState(false)

  const fetchColleagues = useCallback(async () => {
    try {
      const response = await fetch('/api/colleagues')
      const data = await response.json()
      
      if (response.ok) {
        setColleagues(data.colleagues || [])
        setCompanyScraped(data.companyScraped || false)
      }
      
      setLoading(false)
    } catch (error) {
      console.error('Error fetching colleagues:', error)
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    } else {
      fetchColleagues()
    }
  }, [isSignedIn, router, fetchColleagues])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white flex items-center justify-center">
        <p>Loading colleagues...</p>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
              Your Professional Network
            </h1>
            <Link 
              href="/trinity"
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
            >
              Back to Trinity
            </Link>
          </div>
          
          {!companyScraped && (
            <div className="bg-blue-500/10 border border-blue-500 rounded-lg p-4 mb-6">
              <p className="text-blue-400">
                Company employee data will be scraped after you complete your Professional Mirror.
              </p>
            </div>
          )}
          
          {colleagues.length === 0 ? (
            <div className="bg-gray-800 rounded-lg p-8 text-center">
              <p className="text-gray-400 text-lg mb-4">
                No colleagues found yet.
              </p>
              <p className="text-gray-500">
                Complete your Professional Mirror to discover your professional network.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {colleagues.map((colleague) => (
                <div key={colleague.id} className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition-colors">
                  <div className="flex items-start space-x-4">
                    {colleague.profileImageUrl ? (
                      <Image
                        src={colleague.profileImageUrl}
                        alt={colleague.name}
                        width={64}
                        height={64}
                        className="rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-xl">
                        {colleague.name.charAt(0)}
                      </div>
                    )}
                    
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">{colleague.name}</h3>
                      {colleague.title && (
                        <p className="text-gray-400 text-sm">{colleague.title}</p>
                      )}
                      {colleague.company && (
                        <p className="text-gray-500 text-xs mt-1">{colleague.company.name}</p>
                      )}
                      
                      <div className="mt-3 flex items-center space-x-3">
                        <a
                          href={colleague.linkedinUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300 text-sm"
                        >
                          View LinkedIn
                        </a>
                        
                        {colleague.isQuestUser && (
                          <span className="text-green-400 text-sm">
                            Quest Member
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          <div className="mt-12 bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">About Your Network</h2>
            <p className="text-gray-400">
              These are professionals from your company who may share similar journeys. 
              As more people join Quest, you&apos;ll be able to connect and learn from their experiences.
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}