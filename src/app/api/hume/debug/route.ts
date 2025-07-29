import { NextResponse } from 'next/server'

export async function GET() {
  // Check environment variables
  const HUME_API_KEY = process.env.NEXT_PUBLIC_HUME_API_KEY
  const HUME_SECRET_KEY = process.env.NEXT_PUBLIC_HUME_SECRET_KEY
  
  const config = {
    hasApiKey: !!HUME_API_KEY,
    hasSecretKey: !!HUME_SECRET_KEY,
    apiKeyLength: HUME_API_KEY?.length || 0,
    secretKeyLength: HUME_SECRET_KEY?.length || 0,
    apiKeyPrefix: HUME_API_KEY?.substring(0, 10) || 'not set',
    configId: process.env.NEXT_PUBLIC_HUME_CONFIG_ID || 'not set'
  }

  // Try to get token if credentials exist
  if (HUME_API_KEY && HUME_SECRET_KEY) {
    try {
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

      const responseText = await tokenResponse.text()
      
      return NextResponse.json({
        config,
        tokenTest: {
          status: tokenResponse.status,
          statusText: tokenResponse.statusText,
          response: responseText.substring(0, 200),
          headers: Object.fromEntries(tokenResponse.headers.entries())
        }
      })
    } catch (error) {
      return NextResponse.json({
        config,
        tokenTest: {
          error: error instanceof Error ? error.message : 'Unknown error'
        }
      })
    }
  }

  return NextResponse.json({ config, tokenTest: { error: 'Missing credentials' } })
}