import { auth, currentUser } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Test auth() function
    const { userId } = await auth()
    
    // Test currentUser() function
    const user = await currentUser()
    
    // Check if Clerk is properly initialized
    const clerkStatus = {
      initialized: true,
      userId: userId || 'Not authenticated',
      userEmail: user?.emailAddresses?.[0]?.emailAddress || 'No user',
      publishableKey: process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ? 'Set' : 'Missing',
      secretKey: process.env.CLERK_SECRET_KEY ? 'Set' : 'Missing',
      webhookSecret: process.env.CLERK_WEBHOOK_SECRET ? 'Set' : 'Missing',
    }
    
    return NextResponse.json({
      success: true,
      message: 'Clerk connection test',
      status: clerkStatus,
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    return NextResponse.json({
      success: false,
      message: 'Clerk connection failed',
      error: error instanceof Error ? error.message : 'Unknown error',
      env: {
        publishableKey: process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ? 'Set' : 'Missing',
        secretKey: process.env.CLERK_SECRET_KEY ? 'Set' : 'Missing',
      }
    }, { status: 500 })
  }
}