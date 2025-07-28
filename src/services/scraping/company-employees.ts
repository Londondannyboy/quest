import { ApifyClient } from 'apify-client'
import { LinkedInEmployeeData, CompanyEmployeesResult, ScrapingError } from './types'

const ACTOR_ID = 'apimaestro/linkedin-company-employees-scraper-no-cookies'

export class CompanyEmployeesScraper {
  private client: ApifyClient

  constructor(token?: string) {
    const apiToken = token || process.env.APIFY_TOKEN || process.env.APIFY_API_KEY
    
    if (!apiToken) {
      throw new Error('Apify API token not configured')
    }

    this.client = new ApifyClient({ token: apiToken })
  }

  async scrapeEmployees(companyUrl: string): Promise<CompanyEmployeesResult> {
    try {
      // Validate URL
      if (!companyUrl || !companyUrl.includes('linkedin.com/company/')) {
        const error = new Error('Invalid LinkedIn company URL') as ScrapingError
        error.code = 'INVALID_URL'
        throw error
      }

      // Run the actor with the company URL
      const input = {
        identifier: companyUrl
      }
      
      const run = await this.client.actor(ACTOR_ID).call(input)
      
      // Fetch results
      const { items } = await this.client.dataset(run.defaultDatasetId).listItems()
      
      if (!items || items.length === 0) {
        const error = new Error('No employee data scraped from LinkedIn') as ScrapingError
        error.code = 'SCRAPING_FAILED'
        throw error
      }
      
      // Transform the data to our format
      const employees: LinkedInEmployeeData[] = items.map((item: Record<string, unknown>) => ({
        url: item.profileUrl as string || item.url as string || '',
        name: item.name as string || item.fullName as string || '',
        title: item.title as string || item.headline as string || undefined,
        profileImageUrl: item.profileImageUrl as string || item.imageUrl as string || undefined,
        location: item.location as string || undefined,
        connectionDegree: item.connectionDegree as string || undefined
      }))
      
      return {
        companyUrl,
        employees,
        totalEmployees: items.length
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
          scrapingError.message = 'Company employees scraper actor not found. The actor ID may be incorrect.'
        } else if (error.message.includes('insufficient')) {
          scrapingError.code = 'INSUFFICIENT_CREDITS'
          scrapingError.message = 'Insufficient Apify credits. Please check your account balance.'
        } else {
          scrapingError.code = 'SCRAPING_FAILED'
          scrapingError.message = `Scraping failed: ${error.message}`
        }
        
        throw scrapingError
      }
      
      const fallbackError = new Error('Failed to scrape company employees') as ScrapingError
      fallbackError.code = 'SCRAPING_FAILED'
      throw fallbackError
    }
  }
}