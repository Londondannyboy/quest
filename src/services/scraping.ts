import axios from 'axios'
import { prisma } from '@/lib/prisma'
import { upsertCompany, upsertSkill } from '@/utils/entities'

// Apify actor IDs
const LINKEDIN_SCRAPER_ID = 'epilot/linkedin-profile-scraper'
const HARVEST_API_ID = 'harvest/harvest-api' // For company enrichment

interface ApifyRunOptions {
  actorId: string
  input: any
  waitForFinish?: boolean
}

// Run Apify actor
export async function runApifyActor({ actorId, input, waitForFinish = true }: ApifyRunOptions) {
  const token = process.env.APIFY_TOKEN
  if (!token) throw new Error('APIFY_TOKEN not configured')

  try {
    // Start the actor run
    const runResponse = await axios.post(
      `https://api.apify.com/v2/acts/${actorId}/runs`,
      input,
      {
        headers: {
          'Content-Type': 'application/json',
        },
        params: {
          token,
          waitForFinish: waitForFinish ? 120 : undefined, // Wait up to 2 minutes
        },
      }
    )

    const runId = runResponse.data.data.id

    if (!waitForFinish) return { runId }

    // Get the results
    const resultsResponse = await axios.get(
      `https://api.apify.com/v2/actor-runs/${runId}/dataset/items`,
      {
        params: { token },
      }
    )

    return resultsResponse.data
  } catch (error) {
    console.error('Apify actor run failed:', error)
    throw error
  }
}

// Scrape LinkedIn profile
export async function scrapeLinkedInProfile(linkedinUrl: string, userId: string) {
  try {
    const results = await runApifyActor({
      actorId: LINKEDIN_SCRAPER_ID,
      input: {
        urls: [linkedinUrl],
        proxy: {
          useApifyProxy: true,
          apifyProxyGroups: ['RESIDENTIAL'],
        },
      },
    })

    // CRITICAL: Data is nested in items[0].element
    const profileData = results[0]?.element
    if (!profileData) {
      throw new Error('No profile data found')
    }

    // Store raw data
    await prisma.professionalMirror.upsert({
      where: { userId },
      create: {
        userId,
        linkedinUrl,
        rawLinkedinData: profileData,
        lastScraped: new Date(),
      },
      update: {
        rawLinkedinData: profileData,
        lastScraped: new Date(),
      },
    })

    // Extract and create entities
    await extractEntitiesFromProfile(profileData, userId)

    return profileData
  } catch (error) {
    console.error('LinkedIn scraping failed:', error)
    throw error
  }
}

// Extract entities from LinkedIn profile data
async function extractEntitiesFromProfile(profileData: any, userId: string) {
  const experiences = profileData.experience || []
  const skills = profileData.skills || []
  const education = profileData.education || []

  // Process experiences and create company entities
  for (const exp of experiences) {
    if (!exp.companyName) continue

    // Create or find company entity
    const company = await upsertCompany({
      name: exp.companyName,
      website: exp.companyUrl,
      linkedinUrl: exp.companyLinkedinUrl,
      confidence: 0.8, // High confidence from LinkedIn
    })

    // Create experience record
    await prisma.experience.create({
      data: {
        userId,
        companyId: company.id,
        title: exp.title || 'Unknown',
        description: exp.description,
        startDate: exp.startDate ? new Date(exp.startDate) : null,
        endDate: exp.endDate ? new Date(exp.endDate) : null,
        isCurrent: exp.isCurrent || false,
      },
    })
  }

  // Process skills and create skill entities
  for (const skillName of skills) {
    if (!skillName || typeof skillName !== 'string') continue

    const skill = await upsertSkill({
      name: skillName,
      confidence: 0.7, // Medium confidence, needs validation
    })

    // Link skill to user for validation tracking
    await prisma.skill.update({
      where: { id: skill.id },
      data: {
        validators: {
          connect: { id: userId },
        },
      },
    })
  }

  // Process education
  for (const edu of education) {
    if (!edu.schoolName) continue

    // Create or find institution entity
    let institution = await prisma.institution.findFirst({
      where: {
        name: {
          equals: edu.schoolName,
          mode: 'insensitive',
        },
      },
    })

    if (!institution) {
      institution = await prisma.institution.create({
        data: {
          name: edu.schoolName,
          status: 'PROVISIONAL',
          confidence: 0.7,
        },
      })
    }

    // Create education record
    await prisma.education.create({
      data: {
        userId,
        institutionId: institution.id,
        degree: edu.degree,
        fieldOfStudy: edu.fieldOfStudy,
        startDate: edu.startDate ? new Date(edu.startDate) : null,
        endDate: edu.endDate ? new Date(edu.endDate) : null,
      },
    })
  }
}

// Enrich company data using Harvest API
export async function enrichCompanyData(companyDomain: string) {
  try {
    const results = await runApifyActor({
      actorId: HARVEST_API_ID,
      input: {
        domains: [companyDomain],
        includeEmployees: false,
        includeTechnologies: true,
      },
    })

    return results[0] || null
  } catch (error) {
    console.error('Company enrichment failed:', error)
    return null
  }
}