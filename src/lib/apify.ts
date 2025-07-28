import { ApifyClient } from 'apify-client'

// Initialize the ApifyClient with your API token
const token = process.env.APIFY_TOKEN || process.env.APIFY_API_KEY

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

export interface LinkedInEmployeeData {
  url: string
  name: string
  title?: string
  profileImageUrl?: string
  location?: string
  connectionDegree?: string
}

export interface CompanyEmployeesResult {
  companyUrl: string
  employees: LinkedInEmployeeData[]
  totalEmployees?: number
}

export async function scrapeLinkedInProfile(linkedinUrl: string): Promise<LinkedInProfileData> {
  try {
    // LinkedIn Profile Scraper actor ID - HarvestAPI
    const actorId = 'harvestapi/linkedin-profile-scraper'
    
    // Run the actor - HarvestAPI expects both 'queries' and 'urls'
    const input = {
      queries: [linkedinUrl],  // HarvestAPI uses 'queries'
      urls: [linkedinUrl]      // And also 'urls' as fallback
    }
    
    const run = await client.actor(actorId).call(input)
    
    // Fetch results
    const { items } = await client.dataset(run.defaultDatasetId).listItems()
    
    if (!items || items.length === 0) {
      throw new Error('No data scraped from LinkedIn')
    }
    
    const profile = items[0] as Record<string, unknown>
    
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

export async function scrapeCompanyEmployees(companyUrl: string): Promise<CompanyEmployeesResult> {
  try {
    // LinkedIn Company Employees Scraper actor ID - apimaestro
    const actorId = 'apimaestro/linkedin-company-employees-scraper-no-cookies'
    
    // Run the actor with the company URL
    const input = {
      identifier: companyUrl
    }
    
    const run = await client.actor(actorId).call(input)
    
    // Fetch results
    const { items } = await client.dataset(run.defaultDatasetId).listItems()
    
    if (!items || items.length === 0) {
      throw new Error('No employee data scraped from LinkedIn')
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
    
    // Provide more detailed error information
    if (error instanceof Error) {
      if (error.message.includes('Actor not found')) {
        throw new Error('Company employees scraper actor not found. The actor ID may be incorrect.')
      }
      if (error.message.includes('insufficient')) {
        throw new Error('Insufficient Apify credits. Please check your account balance.')
      }
      throw new Error(`Apify error: ${error.message}`)
    }
    
    throw new Error('Failed to scrape company employees')
  }
}