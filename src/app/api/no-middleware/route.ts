import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    // Try importing and using currentUser without any middleware
    const { currentUser } = await import('@clerk/nextjs/server')
    
    console.log('About to call currentUser...')
    const user = await currentUser()
    console.log('currentUser result:', user?.id)
    
    return NextResponse.json({
      success: true,
      userId: user?.id || null,
      email: user?.emailAddresses?.[0]?.emailAddress || null,
      message: 'Called without middleware'
    })
  } catch (error) {
    console.error('Error in no-middleware:', error)
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      message: 'Failed without middleware'
    })
  }
}