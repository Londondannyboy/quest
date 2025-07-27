import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET() {
  return NextResponse.json({
    message: 'This endpoint works without any auth',
    timestamp: new Date().toISOString(),
    random: Math.random()
  })
}