import { ApifyClient } from 'apify-client'
import { LinkedInProfileData, ScrapingError } from './types'

const ACTOR_ID = 'harvestapi/linkedin-profile-scraper'

export class LinkedInProfileScraper {
  private client: ApifyClient

  constructor(token?: string) {
    const apiToken = token || process.env.APIFY_TOKEN || process.env.APIFY_API_KEY
    
    if (!apiToken) {
      throw new Error('Apify API token not configured')
    }

    this.client = new ApifyClient({ token: apiToken })
  }

  async scrapeProfile(linkedinUrl: string): Promise<LinkedInProfileData> {
    try {
      // Validate URL
      if (!linkedinUrl || !linkedinUrl.includes('linkedin.com/in/')) {
        const error = new Error('Invalid LinkedIn profile URL') as ScrapingError
        error.code = 'INVALID_URL'
        throw error
      }

      // Run the actor - HarvestAPI expects both 'queries' and 'urls'
      const input = {
        queries: [linkedinUrl],
        urls: [linkedinUrl]
      }
      
      const run = await this.client.actor(ACTOR_ID).call(input)
      
      // Fetch results
      const { items } = await this.client.dataset(run.defaultDatasetId).listItems()
      
      if (!items || items.length === 0) {
        const error = new Error('No data scraped from LinkedIn') as ScrapingError
        error.code = 'SCRAPING_FAILED'
        throw error
      }
      
      const profile = items[0] as Record<string, unknown>
      
      // Transform the data to our format
      const experiences = profile.experience as Array<Record<string, unknown>> || []
      const currentPosition = experiences.find(exp => exp.current === true)
      
      return {
        url: linkedinUrl,
        name: (profile.name || profile.fullName || profile.full_name) as string | undefined,
        headline: (profile.headline || profile.title) as string | undefined,
        about: (profile.about || profile.summary || profile.description) as string | undefined,
        currentPosition: currentPosition ? {
          title: (currentPosition.title || currentPosition.position) as string,
          company: (currentPosition.companyName || currentPosition.company_name || currentPosition.company) as string,
          duration: currentPosition.duration as string
        } : undefined,
        experiences: experiences?.map((exp) => ({
          title: (exp.title || exp.position) as string,
          company: (exp.companyName || exp.company_name || exp.company) as string,
          duration: exp.duration as string,
          description: exp.description as string | undefined
        })),
        education: (profile.education as Array<Record<string, unknown>>)?.map((edu) => ({
          school: (edu.schoolName || edu.school_name || edu.school) as string,
          degree: edu.degree as string | undefined,
          field: (edu.fieldOfStudy || edu.field_of_study || edu.field) as string | undefined,
          dates: edu.dates as string | undefined
        })),
        skills: (profile.skills || profile.skill || []) as string[]
      }
    } catch (error) {
      if ((error as ScrapingError).code) {
        throw error
      }
      
      // Handle specific Apify errors
      if (error instanceof Error) {
        const scrapingError = new Error(error.message) as ScrapingError
        
        if (error.message.includes('Actor not found')) {
          scrapingError.code = 'ACTOR_NOT_FOUND'
          scrapingError.message = 'LinkedIn scraper actor not found. The actor ID may be incorrect.'
        } else if (error.message.includes('insufficient')) {
          scrapingError.code = 'INSUFFICIENT_CREDITS'
          scrapingError.message = 'Insufficient Apify credits. Please check your account balance.'
        } else {
          scrapingError.code = 'SCRAPING_FAILED'
          scrapingError.message = `Scraping failed: ${error.message}`
        }
        
        throw scrapingError
      }
      
      const fallbackError = new Error('Failed to scrape LinkedIn profile') as ScrapingError
      fallbackError.code = 'SCRAPING_FAILED'
      throw fallbackError
    }
  }
}