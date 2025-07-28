import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

// GET /api/test/health - Health check for Trinity endpoints
export async function GET() {
  try {
    // Test database connection
    const userCount = await prisma.user.count()
    const trinityCount = await prisma.trinity.count()
    const questCount = await prisma.quest.count()
    
    return NextResponse.json({
      status: 'healthy',
      database: 'connected',
      stats: {
        users: userCount,
        trinities: trinityCount,
        quests: questCount,
      },
      endpoints: {
        trinity: {
          GET: '/api/trinity',
          POST: '/api/trinity',
        },
        questReadiness: {
          GET: '/api/quest/readiness',
          POST: '/api/quest/readiness',
        },
        test: {
          initUser: '/api/test/init-user',
          health: '/api/test/health',
        },
      },
      message: 'Trinity and Quest readiness endpoints are ready for testing',
    })
  } catch (error) {
    console.error('Health check error:', error)
    return NextResponse.json(
      { 
        status: 'error',
        database: 'disconnected',
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    )
  }
}