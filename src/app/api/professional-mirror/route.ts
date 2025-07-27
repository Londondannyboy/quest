import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import jwt from 'jsonwebtoken'
import { prisma } from '@/lib/prisma'

export const dynamic = 'force-dynamic'

export async function POST(req: Request) {
  try {
    // Get user from session
    const cookieStore = await cookies()
    const sessionToken = cookieStore.get('__session')?.value
    
    if (!sessionToken) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }
    
    const decoded = jwt.decode(sessionToken) as Record<string, unknown>
    const userId = decoded?.sub as string
    
    if (!userId) {
      return NextResponse.json({ error: 'Invalid session' }, { status: 401 })
    }

    // Get the LinkedIn URL from request
    const { linkedinUrl } = await req.json()
    
    if (!linkedinUrl || !linkedinUrl.includes('linkedin.com/in/')) {
      return NextResponse.json({ error: 'Invalid LinkedIn URL' }, { status: 400 })
    }

    // Find the user
    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
      include: { professionalMirror: true }
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found in database' }, { status: 404 })
    }

    // Create or update professional mirror
    let professionalMirror
    
    if (user.professionalMirror) {
      // Update existing
      professionalMirror = await prisma.professionalMirror.update({
        where: { id: user.professionalMirror.id },
        data: {
          linkedinUrl,
          lastScraped: new Date()
        }
      })
    } else {
      // Create new
      professionalMirror = await prisma.professionalMirror.create({
        data: {
          userId: user.id,
          linkedinUrl
        }
      })
    }

    // In a real implementation, you would trigger the Apify scraper here
    // For now, we'll just save the URL

    return NextResponse.json({
      message: 'Professional Mirror created successfully',
      professionalMirror,
      nextStep: '/trinity'
    })
  } catch (error) {
    console.error('Error creating professional mirror:', error)
    return NextResponse.json({ 
      error: 'Failed to create professional mirror',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}