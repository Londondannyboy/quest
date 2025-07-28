import { NextRequest, NextResponse } from 'next/server'
import { currentUser } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'
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
    
    // Get the database user
    const dbUser = await prisma.user.findUnique({
      where: { clerkId: user.id },
      include: {
        professionalMirror: true,
        experiences: {
          include: {
            company: true
          }
        }
      }
    })
    
    if (!dbUser) {
      return NextResponse.json({ error: 'User not found in database' }, { status: 404 })
    }
    
    // Check if we've already scraped this company recently
    const recentCompany = dbUser.experiences.find(exp => {
      const companyDomain = exp.company.domain
      return companyDomain && companyUrl.includes(companyDomain)
    })?.company
    
    if (recentCompany?.colleagues && recentCompany.colleagues.length > 0) {
      const hoursSinceLastScrape = recentCompany.updatedAt
        ? (Date.now() - recentCompany.updatedAt.getTime()) / (1000 * 60 * 60)
        : Infinity
        
      if (hoursSinceLastScrape < 24) {
        return NextResponse.json({
          message: 'Company employees already scraped recently',
          colleagues: await prisma.colleague.findMany({
            where: { 
              userId: dbUser.id,
              companyId: recentCompany.id
            }
          })
        })
      }
    }
    
    // Scrape company employees
    const { employees, totalEmployees } = await scrapeCompanyEmployees(companyUrl)
    
    // Extract company domain from URL
    const companyDomain = new URL(companyUrl).hostname.replace('www.', '')
    
    // Find or create the company entity
    const company = await prisma.company.upsert({
      where: { domain: companyDomain },
      update: {
        lastScraped: new Date()
      },
      create: {
        name: companyDomain.split('.')[0], // Basic name extraction
        domain: companyDomain,
        website: companyUrl,
        status: 'PROVISIONAL'
      }
    })
    
    // Create colleague records
    const colleagues = await Promise.all(
      employees.slice(0, 50).map(async (employee) => { // Limit to 50 for now
        // Check if this LinkedIn URL already exists
        const existingColleague = await prisma.colleague.findUnique({
          where: { linkedinUrl: employee.url }
        })
        
        if (existingColleague) {
          // Update existing colleague
          return prisma.colleague.update({
            where: { id: existingColleague.id },
            data: {
              name: employee.name,
              title: employee.title,
              profileImageUrl: employee.profileImageUrl,
              lastUpdated: new Date()
            }
          })
        }
        
        // Create new colleague
        return prisma.colleague.create({
          data: {
            userId: dbUser.id,
            linkedinUrl: employee.url,
            name: employee.name,
            title: employee.title,
            profileImageUrl: employee.profileImageUrl,
            companyId: company.id
          }
        })
      })
    )
    
    // Update professional mirror to indicate company has been scraped
    await prisma.professionalMirror.update({
      where: { userId: dbUser.id },
      data: {
        companyScraped: true,
        employeesScrapedAt: new Date()
      }
    })
    
    return NextResponse.json({
      success: true,
      company: {
        id: company.id,
        name: company.name,
        domain: company.domain
      },
      colleagues: colleagues.length,
      totalEmployees
    })
    
  } catch (error) {
    console.error('Company employees scraping error:', error)
    return NextResponse.json({
      error: 'Failed to scrape company employees',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}