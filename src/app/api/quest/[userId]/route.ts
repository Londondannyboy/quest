import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET(
  req: NextRequest,
  context: { params: Promise<{ userId: string }> }
) {
  try {
    const { userId } = await context.params
    
    const user = await prisma.user.findUnique({
      where: { id: userId },
      include: {
        trinity: true,
        professionalMirror: true
      }
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    // Check if user is quest-ready
    const clarityScore = user.trinity?.clarityScore || 0
    if (clarityScore < 30) {
      return NextResponse.json({ error: 'User is not quest-ready' }, { status: 403 })
    }

    // Return public profile data
    const publicProfile = {
      id: user.id,
      name: user.name,
      trinity: {
        clarityScore: user.trinity?.clarityScore,
        pastQuest: user.trinity?.pastQuest,
        pastService: user.trinity?.pastService,
        pastPledge: user.trinity?.pastPledge,
        presentQuest: user.trinity?.presentQuest,
        presentService: user.trinity?.presentService,
        presentPledge: user.trinity?.presentPledge,
        futureQuest: user.trinity?.futureQuest,
        futureService: user.trinity?.futureService,
        futurePledge: user.trinity?.futurePledge,
      },
      professional: {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        title: (user.professionalMirror?.enrichmentData as any)?.title,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        company: (user.professionalMirror?.enrichmentData as any)?.company,
        linkedinUrl: user.professionalMirror?.linkedinUrl
      }
    }

    return NextResponse.json(publicProfile)
  } catch (error) {
    console.error('Public quest profile error:', error)
    return NextResponse.json(
      { error: 'Failed to load profile' },
      { status: 500 }
    )
  }
}