import { auth, currentUser } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export const dynamic = 'force-dynamic'

export async function POST() {
  try {
    const { userId } = await auth()
    const user = await currentUser()
    
    if (!userId || !user) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }
    
    // Check if user already exists
    const existingUser = await prisma.user.findUnique({
      where: { clerkId: userId }
    })
    
    if (existingUser) {
      return NextResponse.json({
        message: 'User already synced',
        user: existingUser
      })
    }
    
    // Create user in database
    const newUser = await prisma.user.create({
      data: {
        clerkId: userId,
        email: user.emailAddresses?.[0]?.emailAddress || 'no-email@example.com',
      }
    })
    
    return NextResponse.json({
      message: 'User synced successfully',
      user: newUser
    })
  } catch (error) {
    console.error('Error syncing user:', error)
    
    // Check if it's a database table error
    if (error instanceof Error && error.message.includes('relation')) {
      return NextResponse.json({ 
        error: 'Database not initialized',
        details: 'The database tables have not been created yet.',
        solution: 'Run these commands locally:\n1. npx prisma generate\n2. npx prisma db push',
        rawError: error.message
      }, { status: 500 })
    }
    
    return NextResponse.json({ 
      error: 'Failed to sync user',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}