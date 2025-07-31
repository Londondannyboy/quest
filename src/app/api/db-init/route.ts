import { NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'

export async function GET() {
  try {
    const { userId } = await auth()
    
    if (!userId) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }
    
    // Check environment variables
    const envCheck = {
      NEON_DATABASE_URL: !!process.env.NEON_DATABASE_URL,
      NEON_DATABASE_URL_LENGTH: process.env.NEON_DATABASE_URL?.length || 0,
      NEON_DATABASE_DIRECT: !!process.env.NEON_DATABASE_DIRECT,
      NODE_ENV: process.env.NODE_ENV
    }
    
    // Parse the database URL to check format
    let dbUrlAnalysis = null
    if (process.env.NEON_DATABASE_URL) {
      const url = process.env.NEON_DATABASE_URL
      try {
        const parsed = new URL(url)
        dbUrlAnalysis = {
          protocol: parsed.protocol,
          host: parsed.host,
          hostname: parsed.hostname,
          port: parsed.port || 'default',
          pathname: parsed.pathname,
          hasPassword: !!parsed.password,
          hasUsername: !!parsed.username
        }
      } catch {
        dbUrlAnalysis = {
          error: 'Invalid URL format',
          startsWithProtocol: url.startsWith('postgres://') || url.startsWith('postgresql://'),
          length: url.length,
          sample: url.substring(0, 20) + '...'
        }
      }
    }
    
    // Try a simple connection test without Prisma
    let connectionTest = null
    if (process.env.NEON_DATABASE_URL) {
      try {
        const url = process.env.NEON_DATABASE_URL
        // Basic URL validation
        const urlObj = new URL(url)
        connectionTest = {
          status: 'URL is valid',
          protocol: urlObj.protocol,
          host: urlObj.host,
          pathname: urlObj.pathname
        }
      } catch (error) {
        connectionTest = {
          status: 'URL parsing failed',
          error: error instanceof Error ? error.message : String(error)
        }
      }
    }
    
    return NextResponse.json({
      timestamp: new Date().toISOString(),
      auth: {
        userId,
        isAuthenticated: true
      },
      env: envCheck,
      dbUrlAnalysis,
      connectionTest,
      instructions: [
        "1. Check that NEON_DATABASE_URL is set in Vercel",
        "2. Ensure the URL doesn't have extra quotes or spaces",
        "3. Make sure the database is not paused in Neon dashboard",
        "4. Verify the connection string format: postgresql://user:pass@host/dbname",
        "5. Check if Neon is in the same region as Vercel deployment"
      ]
    })
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to check database',
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 })
  }
}