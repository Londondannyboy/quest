import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'

// POST /api/test/init-user - Initialize test data for current user
export async function POST() {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Check if user exists, create if not
    let user = await prisma.user.findUnique({
      where: { clerkId: userId },
    })

    if (!user) {
      // Get user email from Clerk if available
      const email = `${userId}@test.quest.com` // Fallback email
      
      user = await prisma.user.create({
        data: {
          clerkId: userId,
          email,
        },
      })
    }

    // Create a story session with initial data
    const existingSession = await prisma.storySession.findFirst({
      where: { userId: user.id },
    })

    if (!existingSession) {
      await prisma.storySession.create({
        data: {
          userId: user.id,
          phase: 'professional_mirror',
          storyDepth: 50, // Starting values
          futureOrientation: 50,
        },
      })
    }

    return NextResponse.json({
      success: true,
      message: 'User initialized successfully',
      userId: user.id,
      hasExistingData: !!existingSession,
    })
  } catch (error) {
    console.error('User initialization error:', error)
    return NextResponse.json(
      { error: 'Failed to initialize user' },
      { status: 500 }
    )
  }
}