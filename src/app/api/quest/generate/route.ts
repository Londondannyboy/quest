import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'
import { generateTrinityContent } from '@/lib/openrouter'

export async function POST(req: NextRequest) {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const { type } = await req.json()
    
    if (!['summary', 'linkedin', 'bio', 'pitch'].includes(type)) {
      return NextResponse.json({ error: 'Invalid content type' }, { status: 400 })
    }

    // Get user's Trinity
    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
      include: { trinity: true }
    })

    if (!user?.trinity) {
      return NextResponse.json({ error: 'Trinity not found' }, { status: 404 })
    }

    // Check if quest ready
    const clarityScore = user.trinity.clarityScore || 0
    if (clarityScore < 30) {
      return NextResponse.json({ error: 'Not quest ready' }, { status: 403 })
    }

    // Generate content using OpenRouter
    const content = await generateTrinityContent(
      user.trinity,
      type as 'summary' | 'linkedin' | 'bio' | 'pitch'
    )

    // Track generation in database (optional)
    await prisma.coachingSession.create({
      data: {
        userId: user.id,
        coachType: 'QUEST_COACH',
        modelUsed: 'openrouter',
        messages: {
          type,
          content
        }
      }
    }).catch(console.error) // Don't fail if tracking fails

    return NextResponse.json({ content })
  } catch (error) {
    console.error('Quest generation error:', error)
    return NextResponse.json(
      { error: 'Failed to generate content' },
      { status: 500 }
    )
  }
}