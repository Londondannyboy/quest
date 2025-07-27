import { NextResponse } from 'next/server'
import { scrapeLinkedInProfile } from '@/lib/apify'

export const dynamic = 'force-dynamic'

export async function POST(req: Request) {
  try {
    const { linkedinUrl } = await req.json()
    
    if (!linkedinUrl) {
      return NextResponse.json({ error: 'LinkedIn URL is required' }, { status: 400 })
    }
    
    // Check if Apify is configured
    const hasApifyToken = !!(process.env.APIFY_TOKEN || process.env.APIFY_API_KEY)
    
    if (!hasApifyToken) {
      return NextResponse.json({ 
        error: 'Apify not configured',
        message: 'APIFY_TOKEN or APIFY_API_KEY environment variable is not set',
        suggestion: 'Add your Apify API key to Vercel environment variables'
      }, { status: 503 })
    }
    
    // Try to scrape
    console.log('Starting LinkedIn scrape for:', linkedinUrl)
    const startTime = Date.now()
    
    try {
      const scrapedData = await scrapeLinkedInProfile(linkedinUrl)
      const duration = Date.now() - startTime
      
      return NextResponse.json({
        success: true,
        duration: `${duration}ms`,
        data: scrapedData,
        message: 'LinkedIn profile scraped successfully!'
      })
    } catch (scrapeError) {
      console.error('Scraping error:', scrapeError)
      
      return NextResponse.json({
        success: false,
        error: 'Scraping failed',
        details: scrapeError instanceof Error ? scrapeError.message : 'Unknown error',
        suggestions: [
          'Verify the LinkedIn URL is correct and publicly accessible',
          'Check if your Apify account has credits',
          'Ensure the LinkedIn Profile Scraper actor is available',
          'Try a different LinkedIn profile URL'
        ]
      }, { status: 500 })
    }
  } catch (error) {
    console.error('Test scrape error:', error)
    return NextResponse.json({ 
      error: 'Test endpoint failed',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}