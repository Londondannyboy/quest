import { NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'

export async function GET() {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const HUME_API_KEY = process.env.NEXT_PUBLIC_HUME_API_KEY
    const HUME_SECRET_KEY = process.env.NEXT_PUBLIC_HUME_SECRET_KEY

    if (!HUME_API_KEY || !HUME_SECRET_KEY) {
      console.error('Hume API credentials not configured')
      return NextResponse.json({ error: 'Hume API not configured' }, { status: 500 })
    }

    // Get access token from Hume
    const tokenResponse = await fetch('https://api.hume.ai/oauth2-cc/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: HUME_API_KEY,
        client_secret: HUME_SECRET_KEY,
      }),
    })

    if (!tokenResponse.ok) {
      const error = await tokenResponse.text()
      console.error('Hume token error:', error)
      return NextResponse.json({ error: 'Failed to get access token' }, { status: 500 })
    }

    const { access_token } = await tokenResponse.json()

    return NextResponse.json({ accessToken: access_token })
  } catch (error) {
    console.error('Hume token route error:', error)
    return NextResponse.json(
      { error: 'Failed to generate access token' },
      { status: 500 }
    )
  }
}