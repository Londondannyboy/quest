import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export const dynamic = 'force-dynamic'

export async function GET() {
  const health = {
    status: 'checking',
    database: {
      connected: false,
      error: null as string | null,
      tables: null as string[] | null,
    },
    environment: {
      DATABASE_URL: !!process.env.DATABASE_URL,
      DIRECT_URL: !!process.env.DIRECT_URL,
      CLERK_PUBLISHABLE_KEY: !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY,
      CLERK_SECRET_KEY: !!process.env.CLERK_SECRET_KEY,
    },
    timestamp: new Date().toISOString(),
  }

  try {
    // Try to connect to database
    await prisma.$connect()
    health.database.connected = true
    
    // Try to count users (this will fail if table doesn't exist)
    const userCount = await prisma.user.count()
    health.database.tables = ['users table exists']
    health.status = 'healthy'
    
    // Add user count to response
    Object.assign(health.database, { userCount })
  } catch (error) {
    health.status = 'unhealthy'
    health.database.error = error instanceof Error ? error.message : 'Unknown error'
    
    // Check if it's a table doesn't exist error
    if (error instanceof Error && error.message.includes('relation')) {
      health.database.error = 'Database tables not created. You need to run: npx prisma db push'
    }
  } finally {
    await prisma.$disconnect()
  }

  return NextResponse.json(health)
}