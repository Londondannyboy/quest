import { ApifyClient } from 'apify-client'

// Initialize the ApifyClient with your API token
const client = new ApifyClient({
  token: process.env.APIFY_TOKEN || process.env.APIFY_API_KEY,
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
    // LinkedIn Profile Scraper actor ID
    const actorId = 'vdrmota/linkedin-profile-scraper'
    
    // Run the actor
    const run = await client.actor(actorId).call({
      profileUrls: [linkedinUrl],
      proxy: {
        useApifyProxy: true,
        apifyProxyGroups: ['RESIDENTIAL']
      }
    })
    
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
    throw new Error('Failed to scrape LinkedIn profile')
  }
}