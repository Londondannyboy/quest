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
    
    const profile = items[0] as any
    
    // Transform the data to our format
    return {
      url: linkedinUrl,
      name: profile.name || profile.fullName,
      headline: profile.headline,
      about: profile.about || profile.summary,
      currentPosition: profile.currentPosition ? {
        title: profile.currentPosition.title,
        company: profile.currentPosition.companyName,
        duration: profile.currentPosition.duration
      } : undefined,
      experiences: profile.positions?.map((pos: any) => ({
        title: pos.title,
        company: pos.companyName,
        duration: pos.duration,
        description: pos.description
      })),
      education: profile.education?.map((edu: any) => ({
        school: edu.schoolName,
        degree: edu.degree,
        field: edu.fieldOfStudy,
        dates: edu.dates
      })),
      skills: profile.skills || []
    }
  } catch (error) {
    console.error('Error scraping LinkedIn:', error)
    throw new Error('Failed to scrape LinkedIn profile')
  }
}