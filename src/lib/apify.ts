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
    
    // LinkedIn Profile Scraper actor ID - HarvestAPI
    const actorId = 'harvestapi/linkedin-profile-scraper'
    // Alternative: Use the actor ID directly: 'LpVuK3Zozwuipa5bp'
    
    console.log('Using actor:', actorId)
    
    // Run the actor - HarvestAPI expects both 'queries' and 'urls'
    const input = {
      queries: [linkedinUrl],  // HarvestAPI uses 'queries'
      urls: [linkedinUrl]      // And also 'urls' as fallback
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
    
    console.log('Raw profile data keys:', Object.keys(profile))
    
    // Transform the data to our format - adjusted for HarvestAPI output
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