import { NextRequest, NextResponse } from 'next/server'
import { currentUser } from '@clerk/nextjs/server'
import { scrapeCompanyEmployees } from '@/lib/apify'

export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  try {
    const user = await currentUser()
    
    if (!user) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }
    
    const body = await req.json()
    const { companyUrl } = body
    
    if (!companyUrl) {
      return NextResponse.json({ error: 'Company URL required' }, { status: 400 })
    }
    
    // Test scraping directly
    const result = await scrapeCompanyEmployees(companyUrl)
    
    return NextResponse.json({
      success: true,
      employees: result.employees.slice(0, 10), // Show first 10
      totalEmployees: result.totalEmployees
    })
    
  } catch (error) {
    console.error('Test scraping error:', error)
    return NextResponse.json({
      error: 'Failed to scrape company',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}