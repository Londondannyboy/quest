import { auth, currentUser } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

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
    return NextResponse.json({ 
      error: 'Failed to sync user',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}