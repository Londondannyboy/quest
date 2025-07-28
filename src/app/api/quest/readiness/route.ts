import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'
import { QuestStatus } from '@prisma/client'

// Calculate Quest readiness based on user's journey
async function calculateReadiness(userId: string) {
  // Get user's latest story session
  const storySession = await prisma.storySession.findFirst({
    where: { userId },
    orderBy: { createdAt: 'desc' },
  })

  // Get user's Trinity
  const trinity = await prisma.trinity.findUnique({
    where: { userId },
  })

  // Get coaching sessions count
  const coachingSessions = await prisma.coachingSession.count({
    where: { userId },
  })

  // Calculate component scores
  const storyDepth = storySession?.storyDepth || 0
  const trinityClarity = trinity?.clarityScore || 0
  const futureOrientation = storySession?.futureOrientation || 0
  
  // Apply the readiness formula from requirements
  const readinessScore = 
    (storyDepth * 0.3) +        // How much they shared
    (trinityClarity * 0.4) +    // How clear their purpose
    (futureOrientation * 0.3)   // How ready for growth

  // Determine outcome based on score
  let outcome: 'QUEST_READY' | 'PREPARING' | 'NOT_YET'
  let status: QuestStatus
  
  if (readinessScore >= 70) {
    outcome = 'QUEST_READY'
    status = QuestStatus.QUEST_READY
  } else if (readinessScore >= 40) {
    outcome = 'PREPARING'
    status = QuestStatus.PREPARING
  } else {
    outcome = 'NOT_YET'
    status = QuestStatus.NOT_READY
  }

  // Generate recommendations based on weak areas
  const recommendations = generateRecommendations({
    storyDepth,
    trinityClarity,
    futureOrientation,
    coachingSessions,
  })

  return {
    score: Math.round(readinessScore),
    outcome,
    status,
    components: {
      storyDepth: Math.round(storyDepth),
      trinityClarity: Math.round(trinityClarity),
      futureOrientation: Math.round(futureOrientation),
    },
    recommendations,
    coachingSessions,
  }
}

// Generate specific recommendations based on scores
function generateRecommendations(scores: {
  storyDepth: number
  trinityClarity: number
  futureOrientation: number
  coachingSessions: number
}) {
  const recommendations: string[] = []

  if (scores.storyDepth < 70) {
    recommendations.push(
      'Share more about your professional journey. The Story Coach wants to understand your transitions and motivations.'
    )
  }

  if (scores.trinityClarity < 70) {
    recommendations.push(
      'Your Trinity needs more clarity. Work with the Quest Coach to better articulate your Quest, Service, and Pledge across time.'
    )
  }

  if (scores.futureOrientation < 70) {
    recommendations.push(
      'Focus on your future vision. The Delivery Coach will help you commit to specific goals and first steps.'
    )
  }

  if (scores.coachingSessions < 3) {
    recommendations.push(
      'Engage more with your coaches. Each conversation deepens your understanding and readiness.'
    )
  }

  return recommendations
}

// POST /api/quest/readiness - Check Quest eligibility
export async function POST() {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Get user from database
    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    // Calculate readiness
    const readiness = await calculateReadiness(user.id)

    // Update or create Quest record with readiness data
    await prisma.quest.upsert({
      where: { userId: user.id },
      create: {
        userId: user.id,
        status: readiness.status,
        readinessScore: readiness.score,
      },
      update: {
        status: readiness.status,
        readinessScore: readiness.score,
      },
    })

    // Format response based on outcome
    let message: string
    let nextSteps: string[]

    switch (readiness.outcome) {
      case 'QUEST_READY':
        message = "Congratulations! You've earned your Quest. Your Trinity is clear, your story is deep, and you're ready to make it real."
        nextSteps = [
          'Proceed to Quest activation',
          'Review your Trinity one final time',
          'Prepare your first concrete step',
        ]
        break
      
      case 'PREPARING':
        message = "You're on the right path, but not quite ready. Your coaches will help you strengthen your Trinity and commitment."
        nextSteps = readiness.recommendations
        break
      
      case 'NOT_YET':
        message = "Your Quest journey is just beginning. Take time to explore your story and discover your Trinity with your coaches."
        nextSteps = [
          'Complete your Professional Mirror',
          'Share your story with the Story Coach',
          'Begin discovering your Trinity',
        ]
        break
    }

    return NextResponse.json({
      readiness: {
        score: readiness.score,
        outcome: readiness.outcome,
        components: readiness.components,
      },
      message,
      nextSteps,
      coachingProgress: {
        sessionsCompleted: readiness.coachingSessions,
        minimumRecommended: 3,
      },
    })
  } catch (error) {
    console.error('Quest readiness error:', error)
    return NextResponse.json(
      { error: 'Failed to calculate Quest readiness' },
      { status: 500 }
    )
  }
}

// GET /api/quest/readiness - Get current readiness status
export async function GET() {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Get user from database
    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
      include: {
        quest: true,
      },
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    if (!user.quest) {
      return NextResponse.json({
        status: 'NOT_STARTED',
        message: 'Begin your journey to discover your Quest readiness.',
      })
    }

    // Recalculate current readiness
    const readiness = await calculateReadiness(user.id)

    return NextResponse.json({
      currentStatus: user.quest.status,
      readinessScore: readiness.score,
      components: readiness.components,
      lastChecked: user.quest.updatedAt,
      recommendations: readiness.recommendations,
    })
  } catch (error) {
    console.error('Quest readiness fetch error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch Quest readiness' },
      { status: 500 }
    )
  }
}