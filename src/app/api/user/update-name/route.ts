import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'

export async function POST(req: NextRequest) {
  try {
    const { userId } = await auth()
    
    if (!userId) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }
    
    const body = await req.json()
    const { name } = body
    
    if (!name || name.trim().length === 0) {
      return NextResponse.json({ error: 'Name is required' }, { status: 400 })
    }
    
    // Update user name
    const updatedUser = await prisma.user.update({
      where: { clerkId: userId },
      data: {
        name: name.trim()
      }
    })
    
    return NextResponse.json({
      message: 'Name updated successfully',
      user: {
        id: updatedUser.id,
        clerkId: updatedUser.clerkId,
        name: updatedUser.name,
        email: updatedUser.email
      }
    })
  } catch (error) {
    console.error('Error updating name:', error)
    return NextResponse.json({
      error: 'Failed to update name',
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 })
  }
}