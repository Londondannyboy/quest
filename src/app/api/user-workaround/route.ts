import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    const cookieStore = await cookies()
    const hasSession = cookieStore.has('__session')
    
    if (!hasSession) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }
    
    // For now, just return a mock user object since we know they're authenticated
    // In production, you'd decode the JWT to get the actual user ID
    return NextResponse.json({
      authenticated: true,
      message: 'User is authenticated (workaround mode)',
      clerkId: 'user_temp',
      email: 'user@example.com',
      databaseStatus: 'not_checked',
      workaroundMode: true
    })
  } catch (error) {
    return NextResponse.json({ 
      error: 'Failed to get user',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}