import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json({ 
    status: 'ok',
    timestamp: new Date().toISOString(),
    env: {
      hasHumeKey: !!process.env.NEXT_PUBLIC_HUME_API_KEY,
      hasHumeSecret: !!process.env.NEXT_PUBLIC_HUME_SECRET_KEY,
      hasHumeConfig: !!process.env.NEXT_PUBLIC_HUME_CONFIG_ID
    }
  })
}