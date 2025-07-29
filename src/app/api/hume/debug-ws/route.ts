import { NextResponse } from 'next/server'

// Debug endpoint to test WebSocket URL generation
export async function GET() {
  const logs: string[] = []
  
  try {
    // Check environment variables
    const apiKey = process.env.NEXT_PUBLIC_HUME_API_KEY
    const secretKey = process.env.NEXT_PUBLIC_HUME_SECRET_KEY
    const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID

    logs.push('=== Environment Check ===')
    logs.push(`API Key exists: ${!!apiKey}`)
    logs.push(`Secret Key exists: ${!!secretKey}`)
    logs.push(`Config ID: ${configId}`)

    if (!apiKey || !secretKey) {
      return NextResponse.json({
        success: false,
        error: 'Missing Hume API credentials',
        logs
      })
    }

    // Generate access token
    logs.push('\n=== Token Generation ===')
    const authString = Buffer.from(`${apiKey}:${secretKey}`).toString('base64')
    logs.push(`Auth string created: ${authString.substring(0, 20)}...`)
    
    const tokenResponse = await fetch('https://api.hume.ai/oauth2-cc/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': `Basic ${authString}`
      },
      body: 'grant_type=client_credentials'
    })

    logs.push(`Token response status: ${tokenResponse.status}`)
    logs.push(`Token response headers: ${JSON.stringify(Object.fromEntries(tokenResponse.headers.entries()))}`)
    
    const tokenText = await tokenResponse.text()
    logs.push(`Token response body: ${tokenText}`)
    
    let tokenData
    try {
      tokenData = JSON.parse(tokenText)
    } catch {
      logs.push(`Failed to parse token response as JSON`)
      return NextResponse.json({
        success: false,
        error: 'Invalid token response',
        logs
      })
    }

    if (!tokenResponse.ok || !tokenData.access_token) {
      return NextResponse.json({
        success: false,
        error: 'Failed to get access token',
        tokenError: tokenData,
        logs
      })
    }

    const accessToken = tokenData.access_token
    logs.push(`Access token obtained: ${accessToken.substring(0, 20)}...`)

    // Test API with configs endpoint
    logs.push('\n=== API Test ===')
    const configsResponse = await fetch('https://api.hume.ai/v0/evi/configs', {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Accept': 'application/json'
      }
    })

    logs.push(`Configs response status: ${configsResponse.status}`)
    const configsData = await configsResponse.json()
    logs.push(`Configs response: ${JSON.stringify(configsData)}`)

    // Build WebSocket URLs
    logs.push('\n=== WebSocket URLs ===')
    const wsUrlWithConfig = `wss://api.hume.ai/v0/evi/chat?access_token=${accessToken}&config_id=${configId}`
    const wsUrlNoConfig = `wss://api.hume.ai/v0/evi/chat?access_token=${accessToken}`
    
    logs.push(`With config: wss://api.hume.ai/v0/evi/chat?access_token=***&config_id=${configId}`)
    logs.push(`Without config: wss://api.hume.ai/v0/evi/chat?access_token=***`)

    return NextResponse.json({
      success: true,
      logs,
      debug: {
        hasToken: !!accessToken,
        tokenLength: accessToken.length,
        configId,
        configsFound: configsData.configs?.length || 0,
        wsUrls: {
          withConfig: wsUrlWithConfig.replace(accessToken, 'REDACTED'),
          withoutConfig: wsUrlNoConfig.replace(accessToken, 'REDACTED')
        }
      }
    })

  } catch (error) {
    logs.push(`\n=== ERROR ===`)
    logs.push(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    logs.push(`Stack: ${error instanceof Error ? error.stack : 'No stack'}`)
    
    return NextResponse.json({
      success: false,
      error: 'Debug failed',
      errorDetails: error instanceof Error ? error.message : 'Unknown error',
      logs
    })
  }
}