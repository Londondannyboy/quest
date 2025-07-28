import { NextResponse } from 'next/server'
import { currentUser } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    const user = await currentUser()
    
    if (!user) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }
    
    // Get the database user with colleagues
    const dbUser = await prisma.user.findUnique({
      where: { clerkId: user.id },
      include: {
        colleagues: {
          include: {
            company: true
          },
          orderBy: {
            createdAt: 'desc'
          }
        },
        professionalMirror: true
      }
    })
    
    if (!dbUser) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }
    
    return NextResponse.json({
      colleagues: dbUser.colleagues,
      companyScraped: dbUser.professionalMirror?.companyScraped || false,
      employeesScrapedAt: dbUser.professionalMirror?.employeesScrapedAt
    })
    
  } catch (error) {
    console.error('Error fetching colleagues:', error)
    return NextResponse.json({
      error: 'Failed to fetch colleagues',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}