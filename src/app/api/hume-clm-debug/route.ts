import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'

export async function GET(req: NextRequest) {
  const debugInfo: Record<string, unknown> = {
    timestamp: new Date().toISOString(),
    headers: {},
    auth: {},
    database: {},
    env: {},
    request: {}
  }

  try {
    // Check all headers
    const headerEntries = Object.fromEntries(req.headers.entries())
    debugInfo.headers = {
      all: headerEntries,
      userRelated: {
        'x-hume-user-id': req.headers.get('x-hume-user-id'),
        'x-user-id': req.headers.get('x-user-id'),
        'x-forwarded-user': req.headers.get('x-forwarded-user'),
        'x-custom-user-id': req.headers.get('x-custom-user-id'),
        'hume-user-id': req.headers.get('hume-user-id'),
        'user-id': req.headers.get('user-id'),
        'authorization': req.headers.get('authorization') ? 'Present' : 'Not present',
        'cookie': req.headers.get('cookie') ? 'Present' : 'Not present'
      }
    }

    // Check Clerk auth
    try {
      const authResult = await auth()
      debugInfo.auth = {
        userId: authResult?.userId || null,
        sessionId: authResult?.sessionId || null,
        isSignedIn: !!authResult?.userId
      }
    } catch (error) {
      debugInfo.auth = {
        error: 'Failed to get auth',
        message: error instanceof Error ? error.message : String(error)
      }
    }

    // Check database connection
    try {
      const userCount = await prisma.user.count()
      const recentUser = await prisma.user.findFirst({
        where: {
          trinity: {
            isNot: null
          }
        },
        orderBy: { updatedAt: 'desc' },
        select: {
          id: true,
          clerkId: true,
          name: true,
          email: true,
          updatedAt: true,
          trinity: {
            select: {
              clarityScore: true,
              updatedAt: true
            }
          }
        }
      })

      debugInfo.database = {
        connected: true,
        userCount,
        recentUserWithTrinity: recentUser ? {
          ...recentUser,
          email: recentUser.email ? `${recentUser.email.substring(0, 3)}***` : null
        } : null
      }
    } catch (error) {
      debugInfo.database = {
        connected: false,
        error: error instanceof Error ? error.message : String(error)
      }
    }

    // Check environment variables
    debugInfo.env = {
      NEON_DATABASE_URL: process.env.NEON_DATABASE_URL ? 'Set' : 'Not set',
      NEON_DATABASE_DIRECT: process.env.NEON_DATABASE_DIRECT ? 'Set' : 'Not set',
      DATABASE_URL: process.env.DATABASE_URL ? 'Set' : 'Not set',
      DATABASE_URL_LENGTH: process.env.DATABASE_URL ? process.env.DATABASE_URL.length : 0,
      POSTGRES_URL: process.env.POSTGRES_URL ? 'Set' : 'Not set',
      POSTGRES_PRISMA_URL: process.env.POSTGRES_PRISMA_URL ? 'Set' : 'Not set',
      POSTGRES_URL_NON_POOLING: process.env.POSTGRES_URL_NON_POOLING ? 'Set' : 'Not set',
      NEXT_PUBLIC_HUME_API_KEY: process.env.NEXT_PUBLIC_HUME_API_KEY ? 'Set' : 'Not set',
      NEXT_PUBLIC_HUME_SECRET_KEY: process.env.NEXT_PUBLIC_HUME_SECRET_KEY ? 'Set' : 'Not set',
      NEXT_PUBLIC_HUME_CONFIG_ID: process.env.NEXT_PUBLIC_HUME_CONFIG_ID ? 'Set' : 'Not set',
      CLERK_SECRET_KEY: process.env.CLERK_SECRET_KEY ? 'Set' : 'Not set',
      NODE_ENV: process.env.NODE_ENV
    }

    // Request info
    debugInfo.request = {
      url: req.url,
      method: req.method,
      nextUrl: {
        pathname: req.nextUrl.pathname,
        search: req.nextUrl.search
      }
    }

    return NextResponse.json(debugInfo, { status: 200 })
  } catch (error) {
    return NextResponse.json({
      error: 'Debug endpoint error',
      message: error instanceof Error ? error.message : String(error),
      debugInfo
    }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  // Test CLM endpoint with debug info
  try {
    const body = await req.json()
    const testMessage = body.message || "Hello, who am I?"
    
    // Get auth info
    const authResult = await auth()
    const userId = authResult?.userId
    
    // Build context message with ClerkID
    const contextMessage = userId ? `User ClerkID: ${userId}` : 'No user ID available'
    
    // Call the CLM endpoint
    const clmUrl = new URL('/api/hume-clm-sse/chat/completions', req.url)
    const clmResponse = await fetch(clmUrl.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-clerk-user-id': userId || '',
        cookie: req.headers.get('cookie') || ''
      },
      body: JSON.stringify({
        messages: [
          { role: 'system', content: `You are a helpful assistant. ${contextMessage}` },
          { role: 'user', content: testMessage }
        ],
        model: 'gpt-4',
        stream: false
      })
    })

    const responseText = await clmResponse.text()
    
    // Try to parse as JSON first
    let parsedResponse
    try {
      parsedResponse = JSON.parse(responseText)
    } catch {
      parsedResponse = responseText
    }
    
    return NextResponse.json({
      status: clmResponse.status,
      statusText: clmResponse.statusText,
      response: parsedResponse,
      debug: {
        userId,
        contextMessage,
        clmUrl: clmUrl.toString(),
        requestBody: {
          messages: [
            { role: 'system', content: `You are a helpful assistant. ${contextMessage}` },
            { role: 'user', content: testMessage }
          ]
        }
      }
    })
  } catch (error) {
    console.error('CLM debug test error:', error)
    return NextResponse.json({
      error: 'CLM test error',
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined
    }, { status: 500 })
  }
}