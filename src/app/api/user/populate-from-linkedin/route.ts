import { NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'

export async function POST() {
  try {
    const { userId } = await auth()
    
    if (!userId) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }
    
    // Find user with professional mirror data
    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
      include: {
        professionalMirror: true,
        trinity: true
      }
    })
    
    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }
    
    if (!user.professionalMirror) {
      return NextResponse.json({ error: 'No LinkedIn data found. Please scrape your profile first.' }, { status: 404 })
    }
    
    // Extract name from LinkedIn data
    const linkedinData = user.professionalMirror.rawLinkedinData as Record<string, unknown>
    let extractedName = user.name // Keep existing if we can't extract
    
    // Debug: Log the actual structure
    console.log('LinkedIn data structure:', JSON.stringify(linkedinData, null, 2))
    
    if (linkedinData) {
      // Check if data is nested under a 'data' property
      const actualData = (linkedinData.data as Record<string, unknown>) || linkedinData
      
      // Try different fields where name might be stored
      extractedName = (actualData.name as string) || 
                     (actualData.fullName as string) ||
                     (actualData.displayName as string) ||
                     (actualData.firstName && actualData.lastName 
                       ? `${actualData.firstName} ${actualData.lastName}`.trim()
                       : null) ||
                     (actualData.headline as string)?.split(' at ')[0] ||
                     (actualData.title as string) ||
                     user.name
      
      // If still no name, check for nested profile object
      if (extractedName === user.name && actualData.profile) {
        const profile = actualData.profile as Record<string, unknown>
        extractedName = (profile.name as string) || 
                       (profile.fullName as string) ||
                       (profile.firstName && profile.lastName 
                         ? `${profile.firstName} ${profile.lastName}`.trim()
                         : null) ||
                       extractedName
      }
    }
    
    // Update user with extracted name
    const updatedUser = await prisma.user.update({
      where: { id: user.id },
      data: {
        name: extractedName
      }
    })
    
    return NextResponse.json({
      message: 'Profile populated from LinkedIn data',
      user: {
        id: updatedUser.id,
        name: updatedUser.name,
        email: updatedUser.email,
        hasLinkedIn: !!user.professionalMirror,
        hasTrinity: !!user.trinity,
        linkedinUrl: user.professionalMirror.linkedinUrl,
        lastScraped: user.professionalMirror.lastScraped
      },
      linkedinData: {
        headline: linkedinData?.headline,
        location: linkedinData?.location,
        company: user.professionalMirror.enrichmentData 
          ? (user.professionalMirror.enrichmentData as Record<string, unknown>).company 
          : null
      }
    })
  } catch (error) {
    console.error('Error populating from LinkedIn:', error)
    return NextResponse.json({
      error: 'Failed to populate from LinkedIn',
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 })
  }
}