'use client'

import { useState, useEffect, useCallback } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { CoachType } from '@prisma/client'
import { VoiceCoach } from '@/components/voice-coach'

interface UserProfile {
  databaseUser?: {
    professionalMirror?: Record<string, unknown>
    trinity?: TrinityData | null
    [key: string]: unknown
  }
  [key: string]: unknown
}

interface TrinityData {
  pastQuest?: string
  pastService?: string
  pastPledge?: string
  presentQuest?: string
  presentService?: string
  presentPledge?: string
  futureQuest?: string
  futureService?: string
  futurePledge?: string
  clarityScore?: number
}

// Coach assignments for each Trinity phase
type TrinityFieldKey = Exclude<keyof TrinityData, 'clarityScore'>
const fieldCoachMap: Record<TrinityFieldKey, CoachType> = {
  pastQuest: CoachType.STORY_COACH,
  pastService: CoachType.STORY_COACH,
  pastPledge: CoachType.STORY_COACH,
  presentQuest: CoachType.QUEST_COACH,
  presentService: CoachType.QUEST_COACH,
  presentPledge: CoachType.QUEST_COACH,
  futureQuest: CoachType.QUEST_COACH,
  futureService: CoachType.DELIVERY_COACH,
  futurePledge: CoachType.DELIVERY_COACH,
}

export default function TrinityPage() {
  const { isSignedIn } = useUser()
  const router = useRouter()
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [currentCoach, setCurrentCoach] = useState<CoachType>(CoachType.STORY_COACH)
  const [voiceCoachActive, setVoiceCoachActive] = useState(false)
  const [currentFocusField, setCurrentFocusField] = useState<string | undefined>()
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  
  // Trinity form state
  const [trinity, setTrinity] = useState<TrinityData>({
    pastQuest: '',
    pastService: '',
    pastPledge: '',
    presentQuest: '',
    presentService: '',
    presentPledge: '',
    futureQuest: '',
    futureService: '',
    futurePledge: ''
  })

  const fetchUserProfile = useCallback(async () => {
    try {
      const response = await fetch('/api/user')
      const data = await response.json()
      setUserProfile(data)
      
      // If they don't have a professional mirror yet, redirect back
      if (!data.databaseUser?.professionalMirror) {
        router.push('/professional-mirror')
        return
      }
      
      // Load existing Trinity data if available
      if (data.databaseUser?.trinity) {
        setTrinity({
          pastQuest: data.databaseUser.trinity.pastQuest || '',
          pastService: data.databaseUser.trinity.pastService || '',
          pastPledge: data.databaseUser.trinity.pastPledge || '',
          presentQuest: data.databaseUser.trinity.presentQuest || '',
          presentService: data.databaseUser.trinity.presentService || '',
          presentPledge: data.databaseUser.trinity.presentPledge || '',
          futureQuest: data.databaseUser.trinity.futureQuest || '',
          futureService: data.databaseUser.trinity.futureService || '',
          futurePledge: data.databaseUser.trinity.futurePledge || ''
        })
      }
      
      setLoading(false)
    } catch (error) {
      console.error('Error fetching profile:', error)
      setLoading(false)
    }
  }, [router])
  
  // Field change handler
  const handleFieldChange = (field: keyof TrinityData, value: string) => {
    setTrinity(prev => ({ ...prev, [field]: value }))
    
    // Clear error for this field
    setFieldErrors(prev => ({ ...prev, [field]: '' }))
  }
  
  // Handle field focus to activate appropriate coach
  const handleFieldFocus = (field: TrinityFieldKey) => {
    const coach = fieldCoachMap[field]
    if (coach !== currentCoach) {
      setCurrentCoach(coach)
      // Play transition sound effect when coach changes
      playCoachTransition()
    }
    setCurrentFocusField(field)
    setVoiceCoachActive(true)
  }
  
  // Play coach transition sound
  const playCoachTransition = () => {
    // This would play the signature sound effect for coach transitions
    const audio = new Audio('/sounds/coach-transition.mp3')
    audio.play().catch(console.error)
  }
  
  // Validate field
  const validateField = (field: keyof TrinityData): boolean => {
    const value = trinity[field] || ''
    const wordCount = value.trim().split(/\s+/).filter(word => word.length > 0).length
    
    if (wordCount < 10) {
      setFieldErrors(prev => ({
        ...prev,
        [field]: `Please write at least 10 words (currently ${wordCount})`
      }))
      return false
    }
    
    return true
  }
  
  // Save Trinity
  const saveTrinity = async () => {
    // Validate all fields
    const fields = Object.keys(trinity) as Array<keyof TrinityData>
    let hasErrors = false
    
    fields.forEach(field => {
      if (!validateField(field)) {
        hasErrors = true
      }
    })
    
    if (hasErrors) {
      setCoachMessage({
        coach: 'delivery',
        message: "Some fields need more detail. Each response should be at least 10 words to capture your true Trinity."
      })
      return
    }
    
    setSaving(true)
    
    try {
      const response = await fetch('/api/trinity', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(trinity),
      })
      
      const data = await response.json()
      
      if (response.ok) {
        // Redirect to quest readiness after saving
        setTimeout(() => {
          router.push('/quest-readiness')
        }, 1000)
      } else {
        console.error('Trinity save error:', data.error)
      }
    } catch (error) {
      console.error('Error saving Trinity:', error)
    } finally {
      setSaving(false)
    }
  }

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
              
              {(linkedinData?.name as string) && (
                <p className="text-xl mb-2">{linkedinData.name as string}</p>
              )}
              
              {(linkedinData?.headline as string) && (
                <p className="text-gray-400 mb-4">{linkedinData.headline as string}</p>
              )}
              
              {(linkedinData?.about as string) && (
                <div className="text-gray-300 mb-4">
                  <h3 className="font-semibold mb-2">About</h3>
                  <p className="whitespace-pre-wrap">{linkedinData.about as string}</p>
                </div>
              )}
              
              <div className="flex items-center space-x-4">
                <Link 
                  href="/professional-mirror"
                  className="text-blue-400 hover:text-blue-300 text-sm"
                >
                  Update LinkedIn URL →
                </Link>
                <Link 
                  href="/colleagues"
                  className="text-purple-400 hover:text-purple-300 text-sm"
                >
                  View Colleagues →
                </Link>
              </div>
            </div>
          )}

          {/* Voice Coach Activation Banner */}
          <div className="mb-8 p-6 bg-gray-800 rounded-lg border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold mb-2">Voice Coaching Available</h3>
                <p className="text-gray-400">
                  Click on any field to activate your AI coach. They&apos;ll guide you through discovering your Trinity.
                </p>
              </div>
              <div className="text-4xl">
                {currentCoach === CoachType.STORY_COACH ? '📖' :
                 currentCoach === CoachType.QUEST_COACH ? '🧭' : '🎯'}
              </div>
            </div>
          </div>

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
                    value={trinity.pastQuest}
                    onChange={(e) => handleFieldChange('pastQuest', e.target.value)}
                    onFocus={() => handleFieldFocus('pastQuest')}
                    onBlur={() => validateField('pastQuest')}
                  />
                  {fieldErrors.pastQuest && (
                    <p className="text-red-400 text-sm mt-2">{fieldErrors.pastQuest}</p>
                  )}
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-2">Your Past Service</h3>
                  <p className="text-sm text-gray-500 mb-3">
                    Who did you serve and how did you help them?
                  </p>
                  <textarea 
                    className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 h-24"
                    placeholder="I helped..."
                    value={trinity.pastService}
                    onChange={(e) => handleFieldChange('pastService', e.target.value)}
                    onFocus={() => handleFieldFocus('pastService')}
                    onBlur={() => validateField('pastService')}
                  />
                  {fieldErrors.pastService && (
                    <p className="text-red-400 text-sm mt-2">{fieldErrors.pastService}</p>
                  )}
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-2">Your Past Pledge</h3>
                  <p className="text-sm text-gray-500 mb-3">
                    What unique value did you promise to deliver?
                  </p>
                  <textarea 
                    className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 h-24"
                    placeholder="I pledged to..."
                    value={trinity.pastPledge}
                    onChange={(e) => handleFieldChange('pastPledge', e.target.value)}
                    onFocus={() => handleFieldFocus('pastPledge')}
                    onBlur={() => validateField('pastPledge')}
                  />
                  {fieldErrors.pastPledge && (
                    <p className="text-red-400 text-sm mt-2">{fieldErrors.pastPledge}</p>
                  )}
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
                    value={trinity.presentQuest}
                    onChange={(e) => handleFieldChange('presentQuest', e.target.value)}
                    onFocus={() => handleFieldFocus('presentQuest')}
                    onBlur={() => validateField('presentQuest')}
                  />
                  {fieldErrors.presentQuest && (
                    <p className="text-red-400 text-sm mt-2">{fieldErrors.presentQuest}</p>
                  )}
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-2">Your Present Service</h3>
                  <p className="text-sm text-gray-500 mb-3">
                    Who do you serve now and how?
                  </p>
                  <textarea 
                    className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-24"
                    placeholder="I currently help..."
                    value={trinity.presentService}
                    onChange={(e) => handleFieldChange('presentService', e.target.value)}
                    onFocus={() => handleFieldFocus('presentService')}
                    onBlur={() => validateField('presentService')}
                  />
                  {fieldErrors.presentService && (
                    <p className="text-red-400 text-sm mt-2">{fieldErrors.presentService}</p>
                  )}
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-2">Your Present Pledge</h3>
                  <p className="text-sm text-gray-500 mb-3">
                    What value do you deliver today?
                  </p>
                  <textarea 
                    className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-24"
                    placeholder="I deliver..."
                    value={trinity.presentPledge}
                    onChange={(e) => handleFieldChange('presentPledge', e.target.value)}
                    onFocus={() => handleFieldFocus('presentPledge')}
                    onBlur={() => validateField('presentPledge')}
                  />
                  {fieldErrors.presentPledge && (
                    <p className="text-red-400 text-sm mt-2">{fieldErrors.presentPledge}</p>
                  )}
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
                    value={trinity.futureQuest}
                    onChange={(e) => handleFieldChange('futureQuest', e.target.value)}
                    onFocus={() => handleFieldFocus('futureQuest')}
                    onBlur={() => validateField('futureQuest')}
                  />
                  {fieldErrors.futureQuest && (
                    <p className="text-red-400 text-sm mt-2">{fieldErrors.futureQuest}</p>
                  )}
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-2">Your Future Service</h3>
                  <p className="text-sm text-gray-500 mb-3">
                    Who will you serve and how will you transform their lives?
                  </p>
                  <textarea 
                    className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 h-24"
                    placeholder="I will help..."
                    value={trinity.futureService}
                    onChange={(e) => handleFieldChange('futureService', e.target.value)}
                    onFocus={() => handleFieldFocus('futureService')}
                    onBlur={() => validateField('futureService')}
                  />
                  {fieldErrors.futureService && (
                    <p className="text-red-400 text-sm mt-2">{fieldErrors.futureService}</p>
                  )}
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-2">Your Future Pledge</h3>
                  <p className="text-sm text-gray-500 mb-3">
                    What unique value will you create in the world?
                  </p>
                  <textarea 
                    className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 h-24"
                    placeholder="I pledge to..."
                    value={trinity.futurePledge}
                    onChange={(e) => handleFieldChange('futurePledge', e.target.value)}
                    onFocus={() => handleFieldFocus('futurePledge')}
                    onBlur={() => validateField('futurePledge')}
                  />
                  {fieldErrors.futurePledge && (
                    <p className="text-red-400 text-sm mt-2">{fieldErrors.futurePledge}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-center">
              <button
                onClick={saveTrinity}
                disabled={saving}
                className="px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all text-lg font-semibold disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Trinity & Continue →'}
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
      
      {/* Voice Coach Component */}
      <VoiceCoach 
        currentCoach={currentCoach}
        isActive={voiceCoachActive}
        currentField={currentFocusField}
        onCoachMessage={(message) => {
          console.log(`Coach ${currentCoach}:`, message)
        }}
      />
    </main>
  )
}