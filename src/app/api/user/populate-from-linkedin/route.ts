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
    
    if (linkedinData) {
      // Try different fields where name might be stored
      extractedName = (linkedinData.name as string) || 
                     (linkedinData.fullName as string) ||
                     (linkedinData.firstName && linkedinData.lastName 
                       ? `${linkedinData.firstName} ${linkedinData.lastName}`.trim()
                       : (linkedinData.headline as string)?.split(' at ')[0]) || // Sometimes name is in headline
                         user.name
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