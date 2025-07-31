import { NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'

export async function GET() {
  try {
    const { userId } = await auth()
    
    if (!userId) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }
    
    // Get user with full LinkedIn data
    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
      include: {
        professionalMirror: true
      }
    })
    
    if (!user || !user.professionalMirror) {
      return NextResponse.json({ error: 'No LinkedIn data found' }, { status: 404 })
    }
    
    // Return the raw LinkedIn data so we can see its structure
    const rawData = user.professionalMirror.rawLinkedinData as Record<string, unknown>
    
    // Extract possible name fields
    const possibleNames: Record<string, unknown> = {}
    if (rawData) {
      // Check top level
      possibleNames.topLevel = {
        name: rawData.name,
        fullName: rawData.fullName,
        displayName: rawData.displayName,
        firstName: rawData.firstName,
        lastName: rawData.lastName,
        headline: rawData.headline,
        title: rawData.title
      }
      
      // Check if data is nested
      if (rawData.data && typeof rawData.data === 'object') {
        const nestedData = rawData.data as Record<string, unknown>
        possibleNames.nested = {
          name: nestedData.name,
          fullName: nestedData.fullName,
          displayName: nestedData.displayName,
          firstName: nestedData.firstName,
          lastName: nestedData.lastName,
          headline: nestedData.headline,
          title: nestedData.title
        }
      }
      
      // Check for profile object
      if (rawData.profile && typeof rawData.profile === 'object') {
        const profile = rawData.profile as Record<string, unknown>
        possibleNames.profile = {
          name: profile.name,
          fullName: profile.fullName,
          displayName: profile.displayName,
          firstName: profile.firstName,
          lastName: profile.lastName
        }
      }
    }
    
    return NextResponse.json({
      user: {
        id: user.id,
        name: user.name,
        email: user.email
      },
      professionalMirror: {
        id: user.professionalMirror.id,
        linkedinUrl: user.professionalMirror.linkedinUrl,
        lastScraped: user.professionalMirror.lastScraped,
        rawLinkedinData: user.professionalMirror.rawLinkedinData,
        enrichmentData: user.professionalMirror.enrichmentData
      },
      nameExtraction: {
        currentUserName: user.name,
        possibleNameFields: possibleNames,
        dataKeys: rawData ? Object.keys(rawData) : []
      }
    })
  } catch (error) {
    console.error('Show LinkedIn data error:', error)
    return NextResponse.json({
      error: 'Failed to retrieve LinkedIn data',
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 })
  }
}