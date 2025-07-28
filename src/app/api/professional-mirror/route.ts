import { NextResponse } from 'next/server'
import { currentUser } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'
import { scrapeLinkedInProfile } from '@/lib/apify'

export const dynamic = 'force-dynamic'

export async function POST(req: Request) {
  try {
    // Get user from Clerk
    const user = await currentUser()
    
    if (!user) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }

    // Get the LinkedIn URL from request
    const { linkedinUrl } = await req.json()
    
    if (!linkedinUrl || !linkedinUrl.includes('linkedin.com/in/')) {
      return NextResponse.json({ error: 'Invalid LinkedIn URL' }, { status: 400 })
    }

    // Find the database user
    const dbUser = await prisma.user.findUnique({
      where: { clerkId: user.id },
      include: { professionalMirror: true }
    })

    if (!dbUser) {
      return NextResponse.json({ error: 'User not found in database' }, { status: 404 })
    }

    // Create or update professional mirror
    let professionalMirror
    let scrapedData = null
    
    // Try to scrape LinkedIn if Apify token is available
    if (process.env.APIFY_TOKEN || process.env.APIFY_API_KEY) {
      try {
        scrapedData = await scrapeLinkedInProfile(linkedinUrl)
      } catch (error) {
        console.error('Scraping failed, continuing without data:', error)
        // Continue without scraped data
      }
    }
    
    if (dbUser.professionalMirror) {
      // Update existing
      professionalMirror = await prisma.professionalMirror.update({
        where: { id: dbUser.professionalMirror.id },
        data: {
          linkedinUrl,
          lastScraped: new Date(),
          rawLinkedinData: scrapedData ? JSON.parse(JSON.stringify(scrapedData)) : undefined
        }
      })
    } else {
      // Create new
      professionalMirror = await prisma.professionalMirror.create({
        data: {
          userId: dbUser.id,
          linkedinUrl,
          rawLinkedinData: scrapedData ? JSON.parse(JSON.stringify(scrapedData)) : undefined
        }
      })
    }

    // Extract company URL from scraped data and trigger employee scraping
    let companyScrapingResult = null
    if (scrapedData?.currentPosition?.company) {
      // Try to find company LinkedIn URL from the scraped data
      const rawData = scrapedData as Record<string, unknown>
      const currentCompany = rawData.currentCompany as Record<string, unknown> | undefined
      const experiences = rawData.experiences as Array<Record<string, unknown>> | undefined
      const companyUrl = (rawData.currentCompanyUrl as string) || 
                        (currentCompany?.url as string) ||
                        (experiences?.[0]?.companyUrl as string)
      
      if (companyUrl && companyUrl.includes('linkedin.com/company/')) {
        try {
          // Trigger company employee scraping in the background
          fetch(`${process.env.NEXT_PUBLIC_URL || ''}/api/company/employees`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Cookie': req.headers.get('cookie') || ''
            },
            body: JSON.stringify({ companyUrl })
          }).catch(err => console.error('Background company scraping failed:', err))
          
          companyScrapingResult = { triggered: true, companyUrl }
        } catch (error) {
          console.error('Failed to trigger company scraping:', error)
        }
      }
    }

    return NextResponse.json({
      message: 'Professional Mirror created successfully',
      professionalMirror,
      companyScrapingResult,
      nextStep: '/trinity'
    })
  } catch (error) {
    console.error('Error creating professional mirror:', error)
    return NextResponse.json({ 
      error: 'Failed to create professional mirror',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}