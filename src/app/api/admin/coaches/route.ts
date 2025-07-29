import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'

// GET all coaches
export async function GET() {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Check if user is admin (you'll need to implement this check)
    // For now, we'll return default coaches
    
    const coaches = await prisma.coachPrompt.findMany({
      orderBy: { createdAt: 'asc' }
    }).catch(() => [])

    // If no coaches in DB, return defaults
    if (coaches.length === 0) {
      return NextResponse.json({
        coaches: [
          {
            id: 'story-coach',
            name: 'Story Coach',
            role: 'A warm, empathetic Story Coach who helps users discover their authentic professional story.',
            active: true,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          },
          {
            id: 'quest-coach',
            name: 'Quest Coach',
            role: 'An energetic Quest Coach who helps users recognize their Trinity evolution.',
            active: true,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          },
          {
            id: 'delivery-coach',
            name: 'Delivery Coach',
            role: 'A firm, achievement-focused Delivery Coach who helps users turn insights into action.',
            active: true,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          }
        ]
      })
    }

    return NextResponse.json({ coaches })
  } catch (error) {
    console.error('Failed to fetch coaches:', error)
    return NextResponse.json(
      { error: 'Failed to fetch coaches' },
      { status: 500 }
    )
  }
}

// POST create new coach
export async function POST(req: NextRequest) {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const body = await req.json()
    const {
      name,
      role,
      personality,
      conversationGuidelines,
      examples,
      backchanneling,
      emotionalResponses,
      voiceCharacteristics,
      active
    } = body

    const coach = await prisma.coachPrompt.create({
      data: {
        name,
        role,
        personality,
        conversationGuidelines,
        examples,
        backchanneling,
        emotionalResponses,
        voiceCharacteristics,
        active
      }
    })

    return NextResponse.json({ coach })
  } catch (error) {
    console.error('Failed to create coach:', error)
    return NextResponse.json(
      { error: 'Failed to create coach' },
      { status: 500 }
    )
  }
}

// PUT update existing coach
export async function PUT(req: NextRequest) {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const body = await req.json()
    const {
      id,
      name,
      role,
      personality,
      conversationGuidelines,
      examples,
      backchanneling,
      emotionalResponses,
      voiceCharacteristics,
      active
    } = body

    const coach = await prisma.coachPrompt.update({
      where: { id },
      data: {
        name,
        role,
        personality,
        conversationGuidelines,
        examples,
        backchanneling,
        emotionalResponses,
        voiceCharacteristics,
        active,
        updatedAt: new Date()
      }
    })

    return NextResponse.json({ coach })
  } catch (error) {
    console.error('Failed to update coach:', error)
    return NextResponse.json(
      { error: 'Failed to update coach' },
      { status: 500 }
    )
  }
}