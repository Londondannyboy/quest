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