import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'
import { z } from 'zod'

// Trinity validation schema
const trinitySchema = z.object({
  pastQuest: z.string().min(10, 'Past Quest must be at least 10 words'),
  pastService: z.string().min(10, 'Past Service must be at least 10 words'),
  pastPledge: z.string().min(10, 'Past Pledge must be at least 10 words'),
  presentQuest: z.string().min(10, 'Present Quest must be at least 10 words'),
  presentService: z.string().min(10, 'Present Service must be at least 10 words'),
  presentPledge: z.string().min(10, 'Present Pledge must be at least 10 words'),
  futureQuest: z.string().min(10, 'Future Quest must be at least 10 words'),
  futureService: z.string().min(10, 'Future Service must be at least 10 words'),
  futurePledge: z.string().min(10, 'Future Pledge must be at least 10 words'),
})

// Calculate Trinity clarity score based on completeness and quality
function calculateClarityScore(trinity: z.infer<typeof trinitySchema>): number {
  const fields = Object.values(trinity)
  
  // Base score for having all fields
  let score = 0
  
  // Check completeness (30%)
  const completedFields = fields.filter(f => f && f.length > 0).length
  const completenessScore = (completedFields / 9) * 30
  
  // Check quality - average word count (40%)
  const totalWords = fields.reduce((acc, field) => {
    return acc + (field ? field.split(' ').length : 0)
  }, 0)
  const avgWords = totalWords / 9
  const qualityScore = Math.min((avgWords / 50) * 40, 40) // Cap at 40 points
  
  // Check evolution clarity - how different are past/present/future (30%)
  const evolutionScore = calculateEvolutionClarity(trinity)
  
  score = completenessScore + qualityScore + evolutionScore
  
  return Math.round(score)
}

// Calculate how well the Trinity shows evolution through time
function calculateEvolutionClarity(trinity: z.infer<typeof trinitySchema>): number {
  let evolutionScore = 0
  
  // Compare quest evolution
  const questEvolution = [
    trinity.pastQuest?.toLowerCase(),
    trinity.presentQuest?.toLowerCase(),
    trinity.futureQuest?.toLowerCase()
  ]
  
  // Check for meaningful differences
  if (questEvolution[0] !== questEvolution[1] && questEvolution[1] !== questEvolution[2]) {
    evolutionScore += 10
  }
  
  // Check for progression keywords
  const progressionKeywords = ['evolved', 'transformed', 'grown', 'developed', 'advanced']
  const hasProgression = questEvolution.some(q => 
    progressionKeywords.some(keyword => q?.includes(keyword))
  )
  if (hasProgression) evolutionScore += 10
  
  // Check for future orientation
  const futureKeywords = ['will', 'aspire', 'aim', 'vision', 'goal']
  const hasFutureOrientation = [
    trinity.futureQuest,
    trinity.futureService,
    trinity.futurePledge
  ].some(f => futureKeywords.some(keyword => f?.toLowerCase().includes(keyword)))
  
  if (hasFutureOrientation) evolutionScore += 10
  
  return evolutionScore
}

// POST /api/trinity - Save Trinity data
export async function POST(req: NextRequest) {
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

    // Parse and validate request body
    const body = await req.json()
    const validatedData = trinitySchema.parse(body)
    
    // Calculate clarity score
    const clarityScore = calculateClarityScore(validatedData)
    
    // Prepare evolution data for pattern recognition
    const evolutionData = {
      questEvolution: {
        past: validatedData.pastQuest,
        present: validatedData.presentQuest,
        future: validatedData.futureQuest,
      },
      serviceEvolution: {
        past: validatedData.pastService,
        present: validatedData.presentService,
        future: validatedData.futureService,
      },
      pledgeEvolution: {
        past: validatedData.pastPledge,
        present: validatedData.presentPledge,
        future: validatedData.futurePledge,
      },
      clarityScore,
      timestamp: new Date().toISOString(),
    }
    
    // Create or update Trinity
    const trinity = await prisma.trinity.upsert({
      where: { userId: user.id },
      create: {
        userId: user.id,
        ...validatedData,
        clarityScore,
        evolutionData,
      },
      update: {
        ...validatedData,
        clarityScore,
        evolutionData,
      },
    })
    
    // Update story session if exists
    const latestSession = await prisma.storySession.findFirst({
      where: { userId: user.id },
      orderBy: { createdAt: 'desc' },
    })
    
    if (latestSession) {
      await prisma.storySession.update({
        where: { id: latestSession.id },
        data: {
          trinityClarity: clarityScore,
          futureOrientation: validatedData.futureQuest.includes('will') || 
                           validatedData.futureQuest.includes('aspire') ? 80 : 60,
        },
      })
    }
    
    return NextResponse.json({
      success: true,
      trinity,
      clarityScore,
      message: clarityScore >= 70 
        ? 'Your Trinity is clear and powerful!' 
        : 'Keep refining your Trinity for greater clarity.',
    })
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Validation failed', details: error.errors },
        { status: 400 }
      )
    }
    
    console.error('Trinity save error:', error)
    return NextResponse.json(
      { error: 'Failed to save Trinity' },
      { status: 500 }
    )
  }
}

// GET /api/trinity - Retrieve user's Trinity
export async function GET(req: NextRequest) {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Get user from database
    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
      include: {
        trinity: true,
      },
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    if (!user.trinity) {
      return NextResponse.json({
        trinity: null,
        message: 'No Trinity found. Begin your journey to discover it.',
      })
    }
    
    // Get coaching context if available
    const coachingSessions = await prisma.coachingSession.findMany({
      where: { userId: user.id },
      orderBy: { createdAt: 'desc' },
      take: 5,
    })
    
    return NextResponse.json({
      trinity: user.trinity,
      coachingContext: coachingSessions.length > 0 ? {
        sessionsCount: coachingSessions.length,
        lastCoach: coachingSessions[0].coachType,
        lastSessionAt: coachingSessions[0].createdAt,
      } : null,
    })
  } catch (error) {
    console.error('Trinity fetch error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch Trinity' },
      { status: 500 }
    )
  }
}