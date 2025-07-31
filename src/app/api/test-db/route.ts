import { NextResponse } from 'next/server'
import { PrismaClient } from '@prisma/client'

export async function GET() {
  const results: Record<string, unknown> = {
    timestamp: new Date().toISOString(),
    env: {
      NEON_DATABASE_URL: process.env.NEON_DATABASE_URL ? 'Set' : 'Not set',
      NEON_DATABASE_URL_LENGTH: process.env.NEON_DATABASE_URL?.length || 0,
      NEON_DATABASE_DIRECT: process.env.NEON_DATABASE_DIRECT ? 'Set' : 'Not set',
      DATABASE_URL: process.env.DATABASE_URL ? 'Set' : 'Not set',
      NODE_ENV: process.env.NODE_ENV
    }
  }
  
  // Test direct Prisma connection
  let prisma: PrismaClient | null = null
  
  try {
    // Create a new Prisma client with explicit connection string
    prisma = new PrismaClient({
      datasources: {
        db: {
          url: process.env.NEON_DATABASE_URL
        }
      },
      log: ['error', 'warn']
    })
    
    // Test the connection
    const startTime = Date.now()
    const userCount = await prisma.user.count()
    const connectionTime = Date.now() - startTime
    
    results.database = {
      status: 'Connected',
      userCount,
      connectionTime: `${connectionTime}ms`
    }
    
    // Try to find the current user
    const testUser = await prisma.user.findFirst({
      where: { email: 'keegan.dan@gmail.com' },
      include: {
        professionalMirror: true,
        trinity: true
      }
    })
    
    if (testUser) {
      results.testUser = {
        found: true,
        id: testUser.id,
        clerkId: testUser.clerkId,
        name: testUser.name,
        email: testUser.email,
        hasProfessionalMirror: !!testUser.professionalMirror,
        hasTrinity: !!testUser.trinity
      }
    } else {
      results.testUser = { found: false }
    }
    
  } catch (error) {
    results.database = {
      status: 'Failed',
      error: error instanceof Error ? error.message : String(error),
      errorType: error instanceof Error ? error.constructor.name : typeof error
    }
    
    // Check if it's a connection string issue
    if (process.env.NEON_DATABASE_URL) {
      const url = process.env.NEON_DATABASE_URL
      const hasProtocol = url.startsWith('postgres://') || url.startsWith('postgresql://')
      const hasHost = url.includes('@')
      const hasPort = url.includes(':5432')
      
      results.connectionStringAnalysis = {
        hasProtocol,
        hasHost,
        hasPort,
        length: url.length,
        endsWithSpace: url.endsWith(' '),
        endsWithQuote: url.endsWith('"') || url.endsWith("'")
      }
    }
  } finally {
    if (prisma) {
      await prisma.$disconnect()
    }
  }
  
  return NextResponse.json(results)
}