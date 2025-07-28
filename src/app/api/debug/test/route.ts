import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET() {
  return NextResponse.json({
    message: 'Debug endpoints are working',
    endpoints: [
      'GET /api/debug/test',
      'GET /api/debug/colleagues', 
      'POST /api/debug/scrape-company'
    ],
    timestamp: new Date().toISOString()
  })
}