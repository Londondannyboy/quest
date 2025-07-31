import { NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { initializeUserInZep, syncUserToZep, updateUserProfile } from '@/lib/zep-user-sync'

export async function POST() {
  try {
    const { userId } = await auth()
    
    if (!userId) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }
    
    // Check if Zep is configured
    if (!process.env.ZEP_API_KEY) {
      return NextResponse.json({ 
        error: 'Zep is not configured',
        details: 'ZEP_API_KEY environment variable is not set'
      }, { status: 503 })
    }
    
    // Initialize user in Zep with known data
    // This is specifically for Dan's account
    if (userId === 'user_30WYPgDczAxAn5M24tqNcfd0w1E') {
      const profile = await initializeUserInZep(
        userId,
        'keegan.dan@gmail.com',
        'Dan'
      )
      
      // Add professional mirror data
      await updateUserProfile(userId, {
        professionalMirror: {
          linkedinUrl: 'https://linkedin.com/in/dankeegan',
          headline: 'Quest Core User',
          company: 'Quest',
          location: 'London'
        }
      })
      
      return NextResponse.json({
        message: 'User initialized in Zep',
        profile
      })
    }
    
    // For other users, try to sync from database
    const profile = await syncUserToZep(userId)
    
    if (!profile) {
      // Initialize with basic info
      const newProfile = await initializeUserInZep(
        userId,
        'user@example.com',
        'User'
      )
      
      return NextResponse.json({
        message: 'New user initialized in Zep',
        profile: newProfile
      })
    }
    
    return NextResponse.json({
      message: 'User synced to Zep',
      profile
    })
  } catch (error) {
    console.error('Error initializing user in Zep:', error)
    return NextResponse.json({
      error: 'Failed to initialize user in Zep',
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 })
  }
}