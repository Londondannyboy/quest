import { prisma } from '@/lib/prisma'

/**
 * Calculate string similarity using Levenshtein distance
 */
function calculateSimilarity(str1: string, str2: string): number {
  const s1 = str1.toLowerCase().trim()
  const s2 = str2.toLowerCase().trim()
  
  if (s1 === s2) return 1.0
  
  const longer = s1.length > s2.length ? s1 : s2
  const shorter = s1.length > s2.length ? s2 : s1
  
  if (longer.length === 0) return 1.0
  
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

/**
 * Find potential duplicate companies
 */
export async function findDuplicateCompanies(threshold = 0.85) {
  const companies = await prisma.companyEntity.findMany({
    select: {
      id: true,
      name: true,
      domain: true,
      linkedinUrl: true
    }
  })

  const duplicates: Array<{
    company1: typeof companies[0]
    company2: typeof companies[0]
    similarity: number
    reason: string
  }> = []

  for (let i = 0; i < companies.length; i++) {
    for (let j = i + 1; j < companies.length; j++) {
      const company1 = companies[i]
      const company2 = companies[j]

      // Check domain match
      if (company1.domain && company2.domain && company1.domain === company2.domain) {
        duplicates.push({
          company1,
          company2,
          similarity: 1.0,
          reason: 'Same domain'
        })
        continue
      }

      // Check LinkedIn URL match
      if (company1.linkedinUrl && company2.linkedinUrl && company1.linkedinUrl === company2.linkedinUrl) {
        duplicates.push({
          company1,
          company2,
          similarity: 1.0,
          reason: 'Same LinkedIn URL'
        })
        continue
      }

      // Check name similarity
      const nameSimilarity = calculateSimilarity(company1.name, company2.name)
      if (nameSimilarity >= threshold) {
        duplicates.push({
          company1,
          company2,
          similarity: nameSimilarity,
          reason: 'Similar name'
        })
      }
    }
  }

  return duplicates
}

/**
 * Find potential duplicate skills
 */
export async function findDuplicateSkills(threshold = 0.9) {
  const skills = await prisma.skillEntity.findMany({
    select: {
      id: true,
      name: true,
      clusterId: true
    }
  })

  const duplicates: Array<{
    skill1: typeof skills[0]
    skill2: typeof skills[0]
    similarity: number
  }> = []

  for (let i = 0; i < skills.length; i++) {
    for (let j = i + 1; j < skills.length; j++) {
      const skill1 = skills[i]
      const skill2 = skills[j]

      const similarity = calculateSimilarity(skill1.name, skill2.name)
      if (similarity >= threshold) {
        duplicates.push({
          skill1,
          skill2,
          similarity
        })
      }
    }
  }

  return duplicates
}

/**
 * Find potential duplicate education institutions
 */
export async function findDuplicateEducation(threshold = 0.85) {
  const institutions = await prisma.educationEntity.findMany({
    select: {
      id: true,
      name: true,
      type: true,
      linkedinUrl: true,
      country: true,
      state: true
    }
  })

  const duplicates: Array<{
    institution1: typeof institutions[0]
    institution2: typeof institutions[0]
    similarity: number
    reason: string
  }> = []

  for (let i = 0; i < institutions.length; i++) {
    for (let j = i + 1; j < institutions.length; j++) {
      const inst1 = institutions[i]
      const inst2 = institutions[j]

      // Skip if different types
      if (inst1.type !== inst2.type) continue

      // Check LinkedIn URL match
      if (inst1.linkedinUrl && inst2.linkedinUrl && inst1.linkedinUrl === inst2.linkedinUrl) {
        duplicates.push({
          institution1: inst1,
          institution2: inst2,
          similarity: 1.0,
          reason: 'Same LinkedIn URL'
        })
        continue
      }

      // Check name similarity with location context
      const nameSimilarity = calculateSimilarity(inst1.name, inst2.name)
      if (nameSimilarity >= threshold) {
        // Check if they're in the same location
        const sameLocation = inst1.country === inst2.country && inst1.state === inst2.state
        
        duplicates.push({
          institution1: inst1,
          institution2: inst2,
          similarity: nameSimilarity,
          reason: sameLocation ? 'Similar name in same location' : 'Similar name'
        })
      }
    }
  }

  return duplicates
}

/**
 * Merge entities (generic function)
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export async function mergeEntities<T extends { id: string }>(
  entityType: 'company' | 'skill' | 'education',
  primaryId: string,
  duplicateIds: string[]
) {
  const modelMap = {
    company: 'companyEntity',
    skill: 'skillEntity',
    education: 'educationEntity'
  } as const

  const model = modelMap[entityType]

  await prisma.$transaction(async (tx) => {
    // Get all entities
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const primary = await (tx[model] as any).findUnique({
      where: { id: primaryId },
      include: { validators: true }
    })

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const duplicates = await (tx[model] as any).findMany({
      where: { id: { in: duplicateIds } },
      include: { validators: true }
    })

    if (!primary) {
      throw new Error(`Primary ${entityType} not found`)
    }

    // Merge validators
    const allValidatorIds = new Set([
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ...primary.validators.map((v: any) => v.id),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ...duplicates.flatMap((d: any) => d.validators.map((v: any) => v.id))
    ])

    // Update primary with all validators
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await (tx[model] as any).update({
      where: { id: primaryId },
      data: {
        validators: {
          set: Array.from(allValidatorIds).map(id => ({ id }))
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        confidence: Math.max(primary.confidence, ...duplicates.map((d: any) => d.confidence))
      }
    })

    // Delete duplicates
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await (tx[model] as any).deleteMany({
      where: { id: { in: duplicateIds } }
    })
  })
}

/**
 * Automated deduplication run
 */
export async function runDeduplication() {
  const results = {
    companies: 0,
    skills: 0,
    education: 0
  }

  // Find and merge duplicate companies
  const duplicateCompanies = await findDuplicateCompanies()
  for (const dup of duplicateCompanies) {
    if (dup.similarity === 1.0) {
      // Auto-merge exact matches
      await mergeEntities('company', dup.company1.id, [dup.company2.id])
      results.companies++
    }
  }

  // Find and merge duplicate skills
  const duplicateSkills = await findDuplicateSkills()
  for (const dup of duplicateSkills) {
    if (dup.similarity === 1.0) {
      await mergeEntities('skill', dup.skill1.id, [dup.skill2.id])
      results.skills++
    }
  }

  // Find and merge duplicate education
  const duplicateEducation = await findDuplicateEducation()
  for (const dup of duplicateEducation) {
    if (dup.similarity === 1.0 && dup.reason === 'Same LinkedIn URL') {
      await mergeEntities('education', dup.institution1.id, [dup.institution2.id])
      results.education++
    }
  }

  return results
}