import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export const dynamic = 'force-dynamic'

// Simple test without any Clerk auth
export async function GET() {
  try {
    // Just get the first user with colleagues for testing
    const testUser = await prisma.user.findFirst({
      include: {
        colleagues: {
          include: {
            company: true
          },
          take: 5
        },
        professionalMirror: true
      }
    })
    
    return NextResponse.json({
      message: 'Debug endpoint - no auth',
      hasUser: !!testUser,
      colleaguesCount: testUser?.colleagues?.length || 0,
      companyScraped: testUser?.professionalMirror?.companyScraped || false
    })
    
  } catch (error) {
    return NextResponse.json({
      error: 'Debug endpoint error',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}