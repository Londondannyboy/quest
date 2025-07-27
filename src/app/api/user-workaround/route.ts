import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import jwt from 'jsonwebtoken'
import { prisma } from '@/lib/prisma'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    const cookieStore = await cookies()
    const sessionToken = cookieStore.get('__session')?.value
    
    if (!sessionToken) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }
    
    // Decode the JWT to get user info
    const decoded = jwt.decode(sessionToken) as Record<string, unknown>
    const userId = decoded?.sub as string
    
    if (!userId) {
      return NextResponse.json({ error: 'Invalid session' }, { status: 401 })
    }
    
    // Try to find user in database
    let databaseUser = null
    try {
      databaseUser = await prisma.user.findUnique({
        where: { clerkId: userId },
        include: {
          professionalMirror: true,
          trinity: true,
          quest: true,
          _count: {
            select: {
              experiences: true,
              educations: true,
              storySessions: true,
            }
          }
        }
      })
    } catch (error) {
      console.error('Error fetching database user:', error)
    }
    
    return NextResponse.json({
      clerkId: userId,
      email: decoded.email || 'dan@quest-core-v2.com', // Placeholder since email not in JWT
      firstName: 'Dan',
      lastName: null,
      imageUrl: null,
      createdAt: decoded.iat ? new Date((decoded.iat as number) * 1000).toISOString() : null,
      databaseUser,
      databaseStatus: databaseUser ? 'synced' : 'not_synced',
      workaroundMode: true
    })
  } catch (error) {
    return NextResponse.json({ 
      error: 'Failed to get user',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}