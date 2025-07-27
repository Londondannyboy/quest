import { currentUser } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    console.log('Test auth endpoint called')
    
    const user = await currentUser()
    console.log('Current user:', user?.id)
    
    return NextResponse.json({
      authenticated: !!user,
      userId: user?.id || null,
      email: user?.emailAddresses?.[0]?.emailAddress || null,
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    console.error('Test auth error:', error)
    return NextResponse.json({
      error: 'Failed in test-auth',
      message: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    })
  }
}