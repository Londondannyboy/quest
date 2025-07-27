import { ApifyClient } from 'apify-client'

// Initialize the ApifyClient with your API token
const token = process.env.APIFY_TOKEN || process.env.APIFY_API_KEY

if (!token) {
  console.warn('Apify token not found in environment variables')
}

const client = new ApifyClient({
  token: token,
})

export interface LinkedInProfileData {
  url: string
  name?: string
  headline?: string
  about?: string
  currentPosition?: {
    title: string
    company: string
    duration: string
  }
  experiences?: Array<{
    title: string
    company: string
    duration: string
    description?: string
  }>
  education?: Array<{
    school: string
    degree?: string
    field?: string
    dates?: string
  }>
  skills?: string[]
}

export async function scrapeLinkedInProfile(linkedinUrl: string): Promise<LinkedInProfileData> {
  try {
    console.log('Starting LinkedIn scrape with URL:', linkedinUrl)
    console.log('Apify token available:', !!token)
    
    // LinkedIn Profile Scraper actor ID
    // Popular options: 'curious_coder/linkedin-profile-scraper', 'voyager/linkedin-profile-scraper'
    const actorId = 'curious_coder/linkedin-profile-scraper'
    
    console.log('Using actor:', actorId)
    
    // Run the actor
    const input = {
      urls: [linkedinUrl],  // Some actors use 'urls' instead of 'profileUrls'
      proxy: {
        useApifyProxy: true,
        apifyProxyGroups: ['RESIDENTIAL']
      }
    }
    
    console.log('Actor input:', JSON.stringify(input, null, 2))
    
    const run = await client.actor(actorId).call(input)
    
    console.log('Actor run ID:', run.id)
    console.log('Actor run status:', run.status)
    
    // Fetch results
    const { items } = await client.dataset(run.defaultDatasetId).listItems()
    
    if (!items || items.length === 0) {
      throw new Error('No data scraped from LinkedIn')
    }
    
    const profile = items[0] as Record<string, unknown>
    
    // Transform the data to our format
    const currentPosition = profile.currentPosition as Record<string, unknown> | undefined
    
    return {
      url: linkedinUrl,
      name: (profile.name || profile.fullName) as string | undefined,
      headline: profile.headline as string | undefined,
      about: (profile.about || profile.summary) as string | undefined,
      currentPosition: currentPosition ? {
        title: currentPosition.title as string,
        company: currentPosition.companyName as string,
        duration: currentPosition.duration as string
      } : undefined,
      experiences: (profile.positions as Array<Record<string, unknown>>)?.map((pos) => ({
        title: pos.title as string,
        company: pos.companyName as string,
        duration: pos.duration as string,
        description: pos.description as string | undefined
      })),
      education: (profile.education as Array<Record<string, unknown>>)?.map((edu) => ({
        school: edu.schoolName as string,
        degree: edu.degree as string | undefined,
        field: edu.fieldOfStudy as string | undefined,
        dates: edu.dates as string | undefined
      })),
      skills: (profile.skills || []) as string[]
    }
  } catch (error) {
    console.error('Error scraping LinkedIn:', error)
    
    // Provide more detailed error information
    if (error instanceof Error) {
      if (error.message.includes('Actor not found')) {
        throw new Error('LinkedIn scraper actor not found. The actor ID may be incorrect.')
      }
      if (error.message.includes('insufficient')) {
        throw new Error('Insufficient Apify credits. Please check your account balance.')
      }
      throw new Error(`Apify error: ${error.message}`)
    }
    
    throw new Error('Failed to scrape LinkedIn profile')
  }
}