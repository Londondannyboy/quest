import { NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'

export async function GET() {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const apiKey = process.env.NEXT_PUBLIC_HUME_API_KEY
    const secretKey = process.env.NEXT_PUBLIC_HUME_SECRET_KEY
    const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID

    // Get access token first
    const tokenResponse = await fetch('https://api.hume.ai/oauth2-cc/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: apiKey || '',
        client_secret: secretKey || ''
      })
    })

    const tokenData = await tokenResponse.json()
    const accessToken = tokenData.access_token

    // Get config details
    const configResponse = await fetch(`https://api.hume.ai/v0/evi/configs/${configId}`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    })

    const configData = await configResponse.json()

    // Check what's configured
    const analysis = {
      configId,
      hasCustomLLM: !!configData.custom_llm_url,
      customLLMUrl: configData.custom_llm_url || null,
      voiceProvider: configData.voice?.provider || 'unknown',
      voiceId: configData.voice?.voice_id || 'unknown',
      languageModel: configData.language_model || null,
      systemPrompt: configData.system_prompt?.substring(0, 100) + '...' || null,
      eventHandlers: configData.event_handlers || [],
      metadata: {
        createdAt: configData.created_at,
        updatedAt: configData.updated_at
      }
    }

    // Test if CLM endpoint is reachable
    let clmStatus = 'not_configured'
    if (configData.custom_llm_url) {
      try {
        const clmResponse = await fetch(configData.custom_llm_url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: [{ role: 'user', content: 'test' }]
          })
        })
        clmStatus = clmResponse.ok ? 'reachable' : `error_${clmResponse.status}`
      } catch (error) {
        clmStatus = 'unreachable'
      }
    }

    return NextResponse.json({
      success: true,
      config: analysis,
      clmStatus,
      recommendations: [
        !configData.custom_llm_url ? 'Configure custom LLM URL in Hume dashboard' : null,
        configData.custom_llm_url?.includes('localhost') ? 'Update CLM URL to production URL' : null,
        !configData.system_prompt ? 'Add system prompt for better context' : null
      ].filter(Boolean)
    })
  } catch (error) {
    console.error('Config verification error:', error)
    return NextResponse.json({ 
      error: 'Failed to verify config',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}