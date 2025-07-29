import { NextRequest, NextResponse } from 'next/server'

// Test endpoint to debug Hume API connection
// NO AUTHENTICATION - just for testing

export async function GET() {
  const logs: string[] = []
  
  try {
    // Step 1: Check environment variables
    const apiKey = process.env.NEXT_PUBLIC_HUME_API_KEY
    const secretKey = process.env.NEXT_PUBLIC_HUME_SECRET_KEY
    const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID

    logs.push(`API Key exists: ${!!apiKey}`)
    logs.push(`Secret Key exists: ${!!secretKey}`)
    logs.push(`Config ID: ${configId || 'NOT SET'}`)

    if (!apiKey || !secretKey) {
      return NextResponse.json({
        success: false,
        error: 'Missing Hume API credentials',
        logs
      })
    }

    // Step 2: Generate access token
    logs.push('Generating access token...')
    
    const authString = Buffer.from(`${apiKey}:${secretKey}`).toString('base64')
    const tokenResponse = await fetch('https://api.hume.ai/oauth2-cc/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': `Basic ${authString}`
      },
      body: 'grant_type=client_credentials'
    })

    const tokenData = await tokenResponse.json()
    logs.push(`Token response status: ${tokenResponse.status}`)
    logs.push(`Token response: ${JSON.stringify(tokenData)}`)

    if (!tokenResponse.ok) {
      return NextResponse.json({
        success: false,
        error: 'Failed to get access token',
        tokenError: tokenData,
        logs
      })
    }

    const accessToken = tokenData.access_token
    logs.push(`Access token obtained: ${accessToken ? 'YES' : 'NO'}`)

    // Step 3: Test WebSocket URL construction
    const wsUrl = configId 
      ? `wss://api.hume.ai/v0/evi/chat?access_token=${accessToken}&config_id=${configId}`
      : `wss://api.hume.ai/v0/evi/chat?access_token=${accessToken}`
    
    logs.push(`WebSocket URL: ${wsUrl.replace(accessToken, 'REDACTED')}`)

    // Step 4: Get EVI configurations (to verify connection)
    logs.push('Testing API connection by fetching EVI configs...')
    
    const configsResponse = await fetch('https://api.hume.ai/v0/evi/configs', {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    })

    const configsData = await configsResponse.json()
    logs.push(`Configs response status: ${configsResponse.status}`)
    logs.push(`Number of configs: ${configsData.configs?.length || 0}`)
    
    if (configsData.configs && configsData.configs.length > 0) {
      logs.push('Available configs:')
      configsData.configs.forEach((config: { name: string; id: string }) => {
        logs.push(`  - ${config.name} (ID: ${config.id})`)
      })
    }

    // Step 5: Return results
    return NextResponse.json({
      success: true,
      message: 'Hume API connection test completed',
      logs,
      results: {
        hasAccessToken: !!accessToken,
        configId: configId || 'none',
        availableConfigs: configsData.configs?.length || 0,
        wsUrl: wsUrl.replace(accessToken, 'REDACTED')
      }
    })

  } catch (error) {
    logs.push(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    return NextResponse.json({
      success: false,
      error: 'Test failed',
      errorDetails: error instanceof Error ? error.message : 'Unknown error',
      logs
    })
  }
}

// POST endpoint to test WebSocket connection
export async function POST(req: NextRequest) {
  const logs: string[] = []
  
  try {
    const { testMessage = 'Hello from Quest Core' } = await req.json()
    
    // Get access token first
    const apiKey = process.env.NEXT_PUBLIC_HUME_API_KEY
    const secretKey = process.env.NEXT_PUBLIC_HUME_SECRET_KEY
    const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID

    if (!apiKey || !secretKey) {
      return NextResponse.json({
        success: false,
        error: 'Missing Hume API credentials'
      })
    }

    // Generate access token
    const authString = Buffer.from(`${apiKey}:${secretKey}`).toString('base64')
    const tokenResponse = await fetch('https://api.hume.ai/oauth2-cc/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': `Basic ${authString}`
      },
      body: 'grant_type=client_credentials'
    })

    const tokenData = await tokenResponse.json()
    const accessToken = tokenData.access_token

    // Since we can't use WebSocket in a serverless function,
    // let's test the chat completions endpoint instead
    logs.push('Testing chat completions endpoint...')
    
    const chatResponse = await fetch('https://api.hume.ai/v0/evi/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        messages: [
          {
            role: 'user',
            content: testMessage
          }
        ],
        config_id: configId
      })
    })

    const chatData = await chatResponse.json()
    logs.push(`Chat response status: ${chatResponse.status}`)
    logs.push(`Chat response: ${JSON.stringify(chatData)}`)

    return NextResponse.json({
      success: chatResponse.ok,
      message: 'Chat completions test completed',
      logs,
      response: chatData
    })

  } catch (error) {
    return NextResponse.json({
      success: false,
      error: 'Test failed',
      errorDetails: error instanceof Error ? error.message : 'Unknown error',
      logs
    })
  }
}