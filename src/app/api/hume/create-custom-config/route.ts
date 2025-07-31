import { NextResponse } from 'next/server'

export async function POST() {
  try {
    const apiKey = process.env.NEXT_PUBLIC_HUME_API_KEY
    const secretKey = process.env.NEXT_PUBLIC_HUME_SECRET_KEY
    
    if (!apiKey || !secretKey) {
      return NextResponse.json({
        error: 'Missing Hume credentials'
      }, { status: 400 })
    }
    
    // Get access token using form-encoded body (same as working token endpoint)
    const tokenResponse = await fetch('https://api.hume.ai/oauth2-cc/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: apiKey,
        client_secret: secretKey,
      }),
    })
    
    if (!tokenResponse.ok) {
      return NextResponse.json({
        error: 'Failed to get access token',
        status: tokenResponse.status
      }, { status: 500 })
    }
    
    const { access_token } = await tokenResponse.json()
    
    // Create EVI config with custom language model
    const configData = {
      name: 'Quest Trinity Voice Coach',
      voice: {
        provider: 'hume_ai',
        voice_id: 'ito' // Professional voice
      },
      language_model: {
        model_provider: 'custom',
        custom_language_model_url: 'https://quest-omega-wheat.vercel.app/api/hume-clm-sse/chat/completions',
        custom_language_model_request_headers: {
          'Content-Type': 'application/json'
        }
      },
      evi_version: '2', // Use version 2 for custom LLM support
      event_messages: {
        on_new_chat: {
          enabled: false
        },
        on_inactivity_timeout: {
          enabled: false
        },
        on_max_duration_timeout: {
          enabled: false
        }
      }
    }
    
    const createResponse = await fetch('https://api.hume.ai/v0/evi/configs', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${access_token}`,
        'Content-Type': 'application/json',
        'X-Hume-AI-Id': apiKey // Add the required header
      },
      body: JSON.stringify(configData)
    })
    
    if (!createResponse.ok) {
      const errorData = await createResponse.text()
      return NextResponse.json({
        error: 'Failed to create config',
        status: createResponse.status,
        details: errorData
      }, { status: 500 })
    }
    
    const config = await createResponse.json()
    
    return NextResponse.json({
      success: true,
      config,
      instructions: [
        `Config created with ID: ${config.id}`,
        'Add this to your .env.local file:',
        `NEXT_PUBLIC_HUME_CONFIG_ID=${config.id}`,
        '',
        'Then restart your development server.'
      ]
    })
  } catch (error) {
    console.error('Config creation error:', error)
    return NextResponse.json({
      error: 'Failed to create configuration',
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 })
  }
}