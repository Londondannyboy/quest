import { NextResponse } from 'next/server'
import { auth, currentUser } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'

export async function POST() {
  try {
    const { userId } = await auth()
    const clerkUser = await currentUser()
    
    if (!userId || !clerkUser) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }
    
    // Check if user already exists
    const existingUser = await prisma.user.findUnique({
      where: { clerkId: userId }
    })
    
    if (existingUser) {
      // Update user with latest info from Clerk
      const updatedUser = await prisma.user.update({
        where: { clerkId: userId },
        data: {
          name: clerkUser.fullName || 
                `${clerkUser.firstName || ''} ${clerkUser.lastName || ''}`.trim() ||
                clerkUser.username ||
                'User',
          email: clerkUser.emailAddresses[0]?.emailAddress || existingUser.email,
          updatedAt: new Date()
        },
        include: {
          trinity: true,
          professionalMirror: true
        }
      })
      
      return NextResponse.json({
        message: 'User profile updated',
        user: {
          id: updatedUser.id,
          clerkId: updatedUser.clerkId,
          name: updatedUser.name,
          email: updatedUser.email,
          hasTrinity: !!updatedUser.trinity,
          hasProfessionalMirror: !!updatedUser.professionalMirror
        }
      })
    } else {
      // Create new user
      const newUser = await prisma.user.create({
        data: {
          clerkId: userId,
          email: clerkUser.emailAddresses[0]?.emailAddress || `${userId}@example.com`,
          name: clerkUser.fullName || 
                `${clerkUser.firstName || ''} ${clerkUser.lastName || ''}`.trim() ||
                clerkUser.username ||
                'User'
        },
        include: {
          trinity: true,
          professionalMirror: true
        }
      })
      
      return NextResponse.json({
        message: 'User profile created',
        user: {
          id: newUser.id,
          clerkId: newUser.clerkId,
          name: newUser.name,
          email: newUser.email,
          hasTrinity: !!newUser.trinity,
          hasProfessionalMirror: !!newUser.professionalMirror
        }
      })
    }
  } catch (error) {
    console.error('Error creating/updating user profile:', error)
    return NextResponse.json({
      error: 'Failed to create/update profile',
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 })
  }
}