import { prisma } from '@/lib/prisma'
import { Company, Skill, EntityStatus } from '@prisma/client'

// Extract domain from various URL formats
export function extractDomain(url: string | null | undefined): string | null {
  if (!url) return null
  
  try {
    // Handle URLs without protocol
    const urlWithProtocol = url.startsWith('http') ? url : `https://${url}`
    const urlObj = new URL(urlWithProtocol)
    return urlObj.hostname.replace('www.', '').toLowerCase()
  } catch {
    return null
  }
}

// Create or find existing company entity
export async function upsertCompany({
  name,
  website,
  linkedinUrl,
  confidence = 0.5,
}: {
  name: string
  website?: string | null
  linkedinUrl?: string | null
  confidence?: number
}): Promise<Company> {
  const domain = extractDomain(website || linkedinUrl)
  
  // Try to find by domain first
  if (domain) {
    const existing = await prisma.company.findUnique({
      where: { domain }
    })
    
    if (existing) {
      // Update lastScraped time
      return await prisma.company.update({
        where: { id: existing.id },
        data: { lastScraped: new Date() }
      })
    }
  }
  
  // Create new company entity
  return await prisma.company.create({
    data: {
      name,
      domain,
      website,
      status: EntityStatus.PROVISIONAL,
      confidence,
      lastScraped: new Date()
    }
  })
}

// Create or find existing skill entity
export async function upsertSkill({
  name,
  confidence = 0.5,
}: {
  name: string
  confidence?: number
}): Promise<Skill> {
  const normalizedName = name.trim().toLowerCase()
  
  // Try to find existing skill
  const existing = await prisma.skill.findUnique({
    where: { name: normalizedName }
  })
  
  if (existing) return existing
  
  // Create new skill entity
  return await prisma.skill.create({
    data: {
      name: normalizedName,
      status: EntityStatus.PROVISIONAL,
      confidence
    }
  })
}

// Check if entity needs rescraping
export function shouldRescrape(entity: { lastScraped: Date | null }): boolean {
  if (!entity.lastScraped) return true
  
  const sixMonthsAgo = new Date()
  sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6)
  
  return entity.lastScraped < sixMonthsAgo
}

// Calculate readiness score
export function calculateReadinessScore({
  storyDepth,
  trinityClarity,
  futureOrientation
}: {
  storyDepth: number
  trinityClarity: number
  futureOrientation: number
}): {
  score: number
  outcome: 'QUEST_READY' | 'PREPARING' | 'NOT_YET'
} {
  const score = 
    (storyDepth * 0.3) +      // How much they shared
    (trinityClarity * 0.4) +  // How clear their purpose
    (futureOrientation * 0.3) // How ready for growth
  
  let outcome: 'QUEST_READY' | 'PREPARING' | 'NOT_YET'
  
  if (score >= 70) {
    outcome = 'QUEST_READY'
  } else if (score >= 40) {
    outcome = 'PREPARING'
  } else {
    outcome = 'NOT_YET'
  }
  
  return { score, outcome }
}

// Fuzzy match for deduplication
export function fuzzyMatch(str1: string, str2: string): number {
  const s1 = str1.toLowerCase().trim()
  const s2 = str2.toLowerCase().trim()
  
  if (s1 === s2) return 1
  
  // Simple Levenshtein-based similarity
  const longer = s1.length > s2.length ? s1 : s2
  const shorter = s1.length > s2.length ? s2 : s1
  
  if (longer.length === 0) return 1
  
  const editDistance = levenshteinDistance(longer, shorter)
  return (longer.length - editDistance) / longer.length
}

function levenshteinDistance(str1: string, str2: string): number {
  const matrix: number[][] = []
  
  for (let i = 0; i <= str2.length; i++) {
    matrix[i] = [i]
  }
  
  for (let j = 0; j <= str1.length; j++) {
    matrix[0][j] = j
  }
  
  for (let i = 1; i <= str2.length; i++) {
    for (let j = 1; j <= str1.length; j++) {
      if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1]
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        )
      }
    }
  }
  
  return matrix[str2.length][str1.length]
}