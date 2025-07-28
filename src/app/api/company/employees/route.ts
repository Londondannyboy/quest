import { NextRequest, NextResponse } from 'next/server'
import { currentUser } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'
import { scrapeCompanyEmployees, type LinkedInEmployeeData } from '@/lib/apify'

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
            company: {
              include: {
                colleagues: true
              }
            }
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
    
    // Get the user's LinkedIn URL from their professional mirror
    const userLinkedInUrl = dbUser.professionalMirror?.linkedinUrl
    
    // Create colleague records
    const colleagues = await Promise.all(
      employees.slice(0, 50).map(async (employee: LinkedInEmployeeData) => { // Limit to 50 for now
        // Check if this colleague is actually the user themselves
        if (userLinkedInUrl && employee.url === userLinkedInUrl) {
          // Skip creating a colleague record for the user themselves
          // Instead, mark that they've been found in the company scrape
          console.log(`Found user ${dbUser.email} in company scrape as ${employee.name}`)
          
          // Optionally update the user's professional mirror with company-scraped data
          if (dbUser.professionalMirror) {
            await prisma.professionalMirror.update({
              where: { id: dbUser.professionalMirror.id },
              data: {
                enrichmentData: {
                  companyScrapeMatch: {
                    name: employee.name,
                    title: employee.title,
                    profileImageUrl: employee.profileImageUrl,
                    matchedAt: new Date()
                  }
                }
              }
            })
          }
          
          return null // Skip this employee
        }
        
        // Check if this LinkedIn URL already exists as a colleague
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
        
        // Check if this person is already a Quest user
        const existingUser = await prisma.user.findFirst({
          where: {
            professionalMirror: {
              linkedinUrl: employee.url
            }
          }
        })
        
        // Create new colleague
        return prisma.colleague.create({
          data: {
            userId: dbUser.id,
            linkedinUrl: employee.url,
            name: employee.name,
            title: employee.title,
            profileImageUrl: employee.profileImageUrl,
            companyId: company.id,
            isQuestUser: !!existingUser,
            questUserId: existingUser?.id
          }
        })
      })
    )
    
    // Filter out null values (where we skipped the user themselves)
    const validColleagues = colleagues.filter(c => c !== null)
    
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
      colleagues: validColleagues.length,
      totalEmployees,
      foundUserInScrape: userLinkedInUrl ? employees.some(e => e.url === userLinkedInUrl) : false
    })
    
  } catch (error) {
    console.error('Company employees scraping error:', error)
    return NextResponse.json({
      error: 'Failed to scrape company employees',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}