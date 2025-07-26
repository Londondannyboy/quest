import { NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { scrapeLinkedInProfile } from '@/services/scraping'
import { prisma } from '@/lib/prisma'

export async function POST(req: Request) {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const { linkedinUrl } = await req.json()
    if (!linkedinUrl) {
      return NextResponse.json({ error: 'LinkedIn URL required' }, { status: 400 })
    }

    // Get the database user
    const user = await prisma.user.findUnique({
      where: { clerkId: userId }
    })

    if (!user) {
      // Create user if doesn't exist
      const newUser = await prisma.user.create({
        data: {
          clerkId: userId,
          email: 'placeholder@example.com', // Will be updated by webhook
        }
      })
      
      // Start scraping
      const profileData = await scrapeLinkedInProfile(linkedinUrl, newUser.id)
      
      return NextResponse.json({
        success: true,
        experiences: profileData.experience || [],
        education: profileData.education || [],
        skills: profileData.skills || [],
      })
    }

    // Start scraping
    const profileData = await scrapeLinkedInProfile(linkedinUrl, user.id)
    
    // Create story session
    await prisma.storySession.create({
      data: {
        userId: user.id,
        phase: 'professional_mirror',
        storyDepth: 20, // Initial depth
      }
    })

    return NextResponse.json({
      success: true,
      experiences: profileData.experience || [],
      education: profileData.education || [],
      skills: profileData.skills || [],
    })
  } catch (error) {
    console.error('Scraping API error:', error)
    return NextResponse.json(
      { error: 'Failed to scrape profile' },
      { status: 500 }
    )
  }
}