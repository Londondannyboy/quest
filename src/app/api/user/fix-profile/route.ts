import { NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'

export async function GET() {
  try {
    const { userId } = await auth()
    
    if (!userId) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }
    
    // Find ALL data related to this user
    const diagnostics: Record<string, unknown> = {
      clerkId: userId,
      timestamp: new Date().toISOString()
    }
    
    // 1. Check if user exists with this ClerkID
    const userByClerkId = await prisma.user.findUnique({
      where: { clerkId: userId },
      include: {
        professionalMirror: true,
        trinity: true
      }
    })
    
    diagnostics.userByClerkId = userByClerkId ? {
      id: userByClerkId.id,
      name: userByClerkId.name,
      email: userByClerkId.email,
      hasProfessionalMirror: !!userByClerkId.professionalMirror,
      hasTrinity: !!userByClerkId.trinity
    } : null
    
    // 2. Check if there's a user with your email
    const userByEmail = await prisma.user.findFirst({
      where: { email: 'keegan.dan@gmail.com' },
      include: {
        professionalMirror: true,
        trinity: true
      }
    })
    
    diagnostics.userByEmail = userByEmail ? {
      id: userByEmail.id,
      clerkId: userByEmail.clerkId,
      name: userByEmail.name,
      email: userByEmail.email,
      hasProfessionalMirror: !!userByEmail.professionalMirror,
      hasTrinity: !!userByEmail.trinity
    } : null
    
    // 3. Find any professional mirror data
    const allProfessionalMirrors = await prisma.professionalMirror.findMany({
      include: {
        user: {
          select: {
            id: true,
            clerkId: true,
            email: true,
            name: true
          }
        }
      }
    })
    
    diagnostics.professionalMirrors = allProfessionalMirrors.map(pm => ({
      id: pm.id,
      userId: pm.userId,
      userClerkId: pm.user.clerkId,
      userEmail: pm.user.email,
      userName: pm.user.name,
      linkedinUrl: pm.linkedinUrl,
      lastScraped: pm.lastScraped,
      hasRawData: !!pm.rawLinkedinData,
      hasEnrichmentData: !!pm.enrichmentData
    }))
    
    // 4. List all users
    const allUsers = await prisma.user.findMany({
      select: {
        id: true,
        clerkId: true,
        email: true,
        name: true,
        createdAt: true
      }
    })
    
    diagnostics.allUsers = allUsers
    
    return NextResponse.json(diagnostics)
  } catch (error) {
    console.error('Fix profile diagnostic error:', error)
    return NextResponse.json({
      error: 'Failed to run diagnostics',
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 })
  }
}

export async function POST() {
  try {
    const { userId } = await auth()
    
    if (!userId) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }
    
    // Find the user with LinkedIn data
    const userWithLinkedIn = await prisma.user.findFirst({
      where: {
        professionalMirror: {
          isNot: null
        }
      },
      include: {
        professionalMirror: true
      }
    })
    
    if (!userWithLinkedIn) {
      return NextResponse.json({ error: 'No user with LinkedIn data found' }, { status: 404 })
    }
    
    // Update the LinkedIn user's ClerkID to match current user
    if (userWithLinkedIn.clerkId !== userId) {
      // First, delete any existing user with current ClerkID
      await prisma.user.deleteMany({
        where: { clerkId: userId }
      })
      
      // Then update the LinkedIn user to use current ClerkID
      const updatedUser = await prisma.user.update({
        where: { id: userWithLinkedIn.id },
        data: {
          clerkId: userId,
          email: 'keegan.dan@gmail.com' // Ensure email matches
        },
        include: {
          professionalMirror: true,
          trinity: true
        }
      })
      
      // Extract name from LinkedIn data if available
      const linkedinData = updatedUser.professionalMirror?.rawLinkedinData as Record<string, unknown>
      if (linkedinData && updatedUser.name === 'User') {
        const extractedName = (linkedinData.name as string) || 
                            (linkedinData.fullName as string) ||
                            (linkedinData.headline as string)?.split(' at ')[0] ||
                            'Dan Keegan'
        
        await prisma.user.update({
          where: { id: updatedUser.id },
          data: { name: extractedName }
        })
      }
      
      return NextResponse.json({
        message: 'Profile fixed! LinkedIn data now linked to your current account',
        user: {
          id: updatedUser.id,
          clerkId: updatedUser.clerkId,
          name: updatedUser.name,
          email: updatedUser.email,
          hasLinkedIn: !!updatedUser.professionalMirror,
          linkedinUrl: updatedUser.professionalMirror?.linkedinUrl
        }
      })
    } else {
      return NextResponse.json({
        message: 'Profile already correctly linked',
        user: {
          id: userWithLinkedIn.id,
          clerkId: userWithLinkedIn.clerkId,
          name: userWithLinkedIn.name,
          email: userWithLinkedIn.email
        }
      })
    }
  } catch (error) {
    console.error('Fix profile error:', error)
    return NextResponse.json({
      error: 'Failed to fix profile',
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 })
  }
}