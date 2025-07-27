import { currentUser } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    const user = await currentUser()
    
    if (!user) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }
    
    // Try to find user in database
    let databaseUser = null
    try {
      databaseUser = await prisma.user.findUnique({
        where: { clerkId: user.id },
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
      clerkId: user.id,
      email: user.emailAddresses?.[0]?.emailAddress,
      firstName: user.firstName,
      lastName: user.lastName,
      imageUrl: user.imageUrl,
      createdAt: user.createdAt,
      databaseUser,
      databaseStatus: databaseUser ? 'synced' : 'not_synced'
    })
  } catch (error) {
    console.error('Error getting user:', error)
    return NextResponse.json({ 
      error: 'Failed to get user',
      details: error instanceof Error ? error.message : 'Unknown error',
      hint: 'Database might not be initialized. Run: npx prisma db push'
    }, { status: 500 })
  }
}