import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    const cookieStore = await cookies()
    const sessionToken = cookieStore.get('__session')?.value
    
    if (!sessionToken) {
      return NextResponse.json({
        authenticated: false,
        reason: 'No session cookie found'
      })
    }
    
    // For now, just check if we have a session cookie
    // In production, you'd verify the JWT here
    return NextResponse.json({
      authenticated: true,
      hasSession: true,
      message: 'Session cookie found - user is likely authenticated'
    })
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to check auth',
      message: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}