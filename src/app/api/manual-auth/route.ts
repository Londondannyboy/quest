import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    const cookieStore = await cookies()
    const sessionCookie = cookieStore.get('__session')
    
    // Get all clerk-related cookies
    const allCookies = cookieStore.getAll()
    const clerkCookies = allCookies.filter(c => 
      c.name.includes('__session') || 
      c.name.includes('__clerk') ||
      c.name.includes('__client')
    )
    
    return NextResponse.json({
      hasSession: !!sessionCookie,
      sessionCookieName: sessionCookie?.name || null,
      clerkCookieCount: clerkCookies.length,
      clerkCookieNames: clerkCookies.map(c => c.name),
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to check cookies',
      message: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}