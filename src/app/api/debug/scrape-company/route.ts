import { NextRequest, NextResponse } from 'next/server'
import { scrapeCompanyEmployees } from '@/lib/apify'
import { prisma } from '@/lib/prisma'

export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { companyUrl, userId } = body
    
    if (!companyUrl) {
      return NextResponse.json({ error: 'Company URL required' }, { status: 400 })
    }
    
    // For testing, allow passing a userId or use the first user
    let dbUser
    if (userId) {
      dbUser = await prisma.user.findUnique({
        where: { id: userId }
      })
    } else {
      dbUser = await prisma.user.findFirst()
    }
    
    if (!dbUser) {
      return NextResponse.json({ error: 'No user found for testing' }, { status: 404 })
    }
    
    // Test scraping
    const { employees, totalEmployees } = await scrapeCompanyEmployees(companyUrl)
    
    // Extract company domain
    const companyDomain = new URL(companyUrl).hostname.replace('www.', '')
    
    // Find or create company
    const company = await prisma.company.upsert({
      where: { domain: companyDomain },
      update: { lastScraped: new Date() },
      create: {
        name: companyDomain.split('.')[0],
        domain: companyDomain,
        website: companyUrl,
        status: 'PROVISIONAL'
      }
    })
    
    // Save first 5 colleagues for testing
    const savedColleagues = []
    for (const employee of employees.slice(0, 5)) {
      try {
        const colleague = await prisma.colleague.upsert({
          where: { linkedinUrl: employee.url },
          update: {
            name: employee.name,
            title: employee.title,
            lastUpdated: new Date()
          },
          create: {
            userId: dbUser.id,
            linkedinUrl: employee.url,
            name: employee.name,
            title: employee.title,
            profileImageUrl: employee.profileImageUrl,
            companyId: company.id
          }
        })
        savedColleagues.push(colleague)
      } catch (err) {
        console.error('Error saving colleague:', err)
      }
    }
    
    return NextResponse.json({
      success: true,
      message: 'Debug scrape complete',
      userId: dbUser.id,
      company: {
        id: company.id,
        name: company.name,
        domain: company.domain
      },
      scrapedCount: employees.length,
      savedCount: savedColleagues.length,
      totalEmployees
    })
    
  } catch (error) {
    console.error('Debug scraping error:', error)
    return NextResponse.json({
      error: 'Debug scrape failed',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}