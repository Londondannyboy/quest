import { headers } from 'next/headers'
import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET() {
  const headersList = headers()
  
  // Get all cookies
  const cookieHeader = headersList.get('cookie') || ''
  const cookies = cookieHeader.split(';').map(c => {
    const [name] = c.trim().split('=')
    return name
  }).filter(Boolean)
  
  // Check for Clerk session
  const hasClerkSession = cookies.some(c => c.includes('__session') || c.includes('__clerk'))
  
  return NextResponse.json({
    hasClerkSession,
    cookieNames: cookies,
    userAgent: headersList.get('user-agent'),
    timestamp: new Date().toISOString()
  })
}