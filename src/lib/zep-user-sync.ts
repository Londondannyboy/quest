import { ZepClient } from '@getzep/zep-js'
import { prisma } from '@/lib/prisma'
import { User, Trinity, ProfessionalMirror } from '@prisma/client'

// Initialize Zep client only if API key is available
let zepClient: ZepClient | null = null

if (process.env.ZEP_API_KEY) {
  zepClient = new ZepClient({
    apiKey: process.env.ZEP_API_KEY,
    baseUrl: process.env.ZEP_BASE_URL || 'https://api.getzep.com',
  })
}

export interface UserProfile {
  userId: string
  clerkId: string
  name: string
  email: string
  trinity?: {
    pastQuest?: string
    presentQuest?: string
    futureQuest?: string
    clarityScore: number
  }
  professionalMirror?: {
    linkedinUrl?: string
    headline?: string
    company?: string
    location?: string
  }
}

/**
 * Sync user data from database to Zep
 * This ensures Zep always has the latest user information
 */
export async function syncUserToZep(clerkId: string): Promise<UserProfile | null> {
  try {
    // Try to get user from database
    let user: (User & {
      trinity: Trinity | null
      professionalMirror: ProfessionalMirror | null
    }) | null = null
    
    try {
      user = await prisma.user.findUnique({
        where: { clerkId },
        include: {
          trinity: true,
          professionalMirror: true,
        }
      })
    } catch (dbError) {
      console.error('Database error in syncUserToZep:', dbError)
    }
    
    // If database is down, try to get from Zep
    if (!user) {
      const zepUser = await getUserFromZep(clerkId)
      if (zepUser) {
        return zepUser
      }
      return null
    }
    
    // Build user profile
    const profile: UserProfile = {
      userId: user.id,
      clerkId: user.clerkId,
      name: user.name || 'Unknown',
      email: user.email,
    }
    
    if (user.trinity) {
      profile.trinity = {
        pastQuest: user.trinity.pastQuest || undefined,
        presentQuest: user.trinity.presentQuest || undefined,
        futureQuest: user.trinity.futureQuest || undefined,
        clarityScore: user.trinity.clarityScore,
      }
    }
    
    if (user.professionalMirror) {
      const linkedinData = user.professionalMirror.rawLinkedinData as Record<string, unknown>
      profile.professionalMirror = {
        linkedinUrl: user.professionalMirror.linkedinUrl || undefined,
        headline: linkedinData?.headline as string | undefined,
        company: linkedinData?.company as string | undefined,
        location: linkedinData?.location as string | undefined,
      }
    }
    
    // Store in Zep user metadata if client is available
    if (zepClient) {
      try {
        await zepClient.user.add({
          userId: clerkId,
          metadata: profile as unknown as Record<string, unknown>,
        })
      } catch {
        // Update if user already exists
        await zepClient.user.update(clerkId, {
          metadata: profile as unknown as Record<string, unknown>,
        })
      }
    }
    
    return profile
  } catch (error) {
    console.error('Error syncing user to Zep:', error)
    return null
  }
}

/**
 * Get user profile from Zep
 * This is the fallback when database is unavailable
 */
export async function getUserFromZep(clerkId: string): Promise<UserProfile | null> {
  if (!zepClient) {
    return null
  }
  
  try {
    const zepUser = await zepClient.user.get(clerkId)
    if (zepUser && zepUser.metadata) {
      return zepUser.metadata as unknown as UserProfile
    }
    return null
  } catch (error) {
    console.error('Error getting user from Zep:', error)
    return null
  }
}

/**
 * Update user profile in both Zep and database
 * Zep acts as the source of truth when database is down
 */
export async function updateUserProfile(
  clerkId: string, 
  updates: Partial<UserProfile>
): Promise<UserProfile | null> {
  try {
    // Get current profile from Zep
    const currentProfile = await getUserFromZep(clerkId) || {
      userId: '',
      clerkId,
      name: 'Unknown',
      email: '',
    }
    
    // Merge updates
    const updatedProfile: UserProfile = {
      ...currentProfile,
      ...updates,
    }
    
    // Update Zep first (source of truth) if available
    if (zepClient) {
      await zepClient.user.update(clerkId, {
        metadata: updatedProfile as unknown as Record<string, unknown>,
      })
    }
    
    // Try to update database
    try {
      if (updatedProfile.userId) {
        await prisma.user.update({
          where: { clerkId },
          data: {
            name: updatedProfile.name,
            email: updatedProfile.email,
          }
        })
        
        if (updatedProfile.trinity) {
          await prisma.trinity.upsert({
            where: { userId: updatedProfile.userId },
            create: {
              userId: updatedProfile.userId,
              ...updatedProfile.trinity,
            },
            update: updatedProfile.trinity,
          })
        }
      }
    } catch (dbError) {
      console.error('Database update failed, but Zep updated successfully:', dbError)
    }
    
    return updatedProfile
  } catch (error) {
    console.error('Error updating user profile:', error)
    return null
  }
}

/**
 * Initialize user in Zep from Clerk data
 * Called when a new user signs up
 */
export async function initializeUserInZep(
  clerkId: string,
  email: string,
  name?: string
): Promise<UserProfile> {
  const profile: UserProfile = {
    userId: clerkId, // Use clerkId as userId initially
    clerkId,
    name: name || email.split('@')[0],
    email,
  }
  
  if (zepClient) {
    try {
      await zepClient.user.add({
        userId: clerkId,
        metadata: profile as unknown as Record<string, unknown>,
      })
    } catch {
      // Update if already exists
      await zepClient.user.update(clerkId, {
        metadata: profile as unknown as Record<string, unknown>,
      })
    }
  }
  
  return profile
}