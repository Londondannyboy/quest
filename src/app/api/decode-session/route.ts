import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import jwt from 'jsonwebtoken'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    const cookieStore = await cookies()
    const sessionToken = cookieStore.get('__session')?.value
    
    if (!sessionToken) {
      return NextResponse.json({
        authenticated: false,
        reason: 'No session cookie'
      })
    }
    
    // Decode without verification for debugging
    const decoded = jwt.decode(sessionToken) as Record<string, unknown>
    
    if (!decoded) {
      return NextResponse.json({
        authenticated: false,
        reason: 'Could not decode token'
      })
    }
    
    return NextResponse.json({
      authenticated: true,
      userId: decoded.sub || decoded.user_id || null,
      email: decoded.email || null,
      sessionClaims: {
        issuedAt: decoded.iat ? new Date((decoded.iat as number) * 1000).toISOString() : null,
        expiresAt: decoded.exp ? new Date((decoded.exp as number) * 1000).toISOString() : null,
        issuer: decoded.iss || null,
      },
      // For debugging
      allClaims: Object.keys(decoded)
    })
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to decode session',
      message: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}