import { NextResponse } from 'next/server'

export async function GET() {
  try {
    const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID
    const apiKey = process.env.NEXT_PUBLIC_HUME_API_KEY
    
    if (!configId || !apiKey) {
      return NextResponse.json({
        error: 'Missing configuration',
        configId: configId ? 'Set' : 'Not set',
        apiKey: apiKey ? 'Set' : 'Not set'
      }, { status: 400 })
    }
    
    // Get access token first
    const tokenResponse = await fetch('https://api.hume.ai/oauth2-cc/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': `Basic ${Buffer.from(`${apiKey}:${process.env.NEXT_PUBLIC_HUME_SECRET_KEY}`).toString('base64')}`
      },
      body: 'grant_type=client_credentials'
    })
    
    if (!tokenResponse.ok) {
      return NextResponse.json({
        error: 'Failed to get access token',
        status: tokenResponse.status,
        statusText: tokenResponse.statusText
      }, { status: 500 })
    }
    
    const { access_token } = await tokenResponse.json()
    
    // Check config details
    const configResponse = await fetch(`https://api.hume.ai/v0/evi/configs/${configId}`, {
      headers: {
        'Authorization': `Bearer ${access_token}`,
        'X-Hume-AI-Id': apiKey // Add the required header
      }
    })
    
    if (!configResponse.ok) {
      return NextResponse.json({
        error: 'Failed to fetch config',
        status: configResponse.status,
        statusText: configResponse.statusText,
        configId
      }, { status: 500 })
    }
    
    const configData = await configResponse.json()
    
    return NextResponse.json({
      success: true,
      configId,
      configData,
      analysis: {
        hasCustomLLM: configData.language_model?.custom_language_model_url ? 'Yes' : 'No',
        customLLMUrl: configData.language_model?.custom_language_model_url || 'Not set',
        modelProvider: configData.language_model?.model_provider,
        voice: configData.voice,
        eviVersion: configData.evi_version
      }
    })
  } catch (error) {
    console.error('Config check error:', error)
    return NextResponse.json({
      error: 'Failed to check configuration',
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 })
  }
}