import { prisma } from '@/lib/prisma'
import { EntityStatus, Prisma } from '@prisma/client'

interface CreateSkillEntityInput {
  name: string
  clusterId?: string
  parentSkillId?: string
  confidence?: number
  marketIntelligence?: {
    marketDemand?: number
    salaryPremium?: number
    demandTrend?: string
  }
}

/**
 * Create or update a skill entity with deduplication
 */
export async function createOrUpdateSkillEntity(input: CreateSkillEntityInput) {
  const { name, marketIntelligence, ...rest } = input

  // Normalize skill name
  const normalizedName = name.trim().toLowerCase()

  // Try to find existing skill
  const existingSkill = await prisma.skillEntity.findFirst({
    where: {
      name: { equals: normalizedName, mode: 'insensitive' as Prisma.QueryMode }
    }
  })

  if (existingSkill) {
    // Update if new data has higher confidence
    if (input.confidence && input.confidence > existingSkill.confidence) {
      return prisma.skillEntity.update({
        where: { id: existingSkill.id },
        data: {
          ...rest,
          ...(marketIntelligence || {}),
          confidence: input.confidence
        }
      })
    }
    return existingSkill
  }

  // Create new skill entity
  return prisma.skillEntity.create({
    data: {
      name: normalizedName,
      ...rest,
      ...(marketIntelligence || {})
    }
  })
}

/**
 * Create skill clusters based on similarity
 */
export async function createSkillCluster(name: string, parentClusterId?: string) {
  return prisma.skillCluster.create({
    data: {
      name,
      parentClusterId
    }
  })
}

/**
 * Assign skills to clusters using AI
 */
export async function assignSkillsToCluster(skillIds: string[], clusterId: string) {
  return prisma.skillEntity.updateMany({
    where: {
      id: { in: skillIds }
    },
    data: {
      clusterId
    }
  })
}

/**
 * Find similar skills
 */
export async function findSimilarSkills(skillName: string, limit = 10) {
  const normalizedName = skillName.trim().toLowerCase()

  // First try skills in the same cluster
  const skill = await prisma.skillEntity.findFirst({
    where: {
      name: { equals: normalizedName, mode: 'insensitive' as Prisma.QueryMode }
    },
    include: {
      cluster: {
        include: {
          skills: {
            where: {
              NOT: { name: normalizedName }
            },
            take: limit
          }
        }
      }
    }
  })

  if (skill?.cluster?.skills.length) {
    return skill.cluster.skills
  }

  // Fallback to name similarity
  return prisma.skillEntity.findMany({
    where: {
      name: { contains: normalizedName, mode: 'insensitive' as Prisma.QueryMode },
      NOT: { name: normalizedName }
    },
    take: limit
  })
}

/**
 * Validate a skill entity
 */
export async function validateSkillEntity(
  skillId: string,
  userId: string,
  isValid: boolean
) {
  const skill = await prisma.skillEntity.findUnique({
    where: { id: skillId },
    include: { validators: true }
  })

  if (!skill) {
    throw new Error('Skill not found')
  }

  // Add user as validator
  await prisma.skillEntity.update({
    where: { id: skillId },
    data: {
      validators: {
        connect: { id: userId }
      }
    }
  })

  // Update status based on validation
  const validatorCount = skill.validators.length + 1
  const validationThreshold = 3

  if (isValid && validatorCount >= validationThreshold) {
    await prisma.skillEntity.update({
      where: { id: skillId },
      data: {
        status: EntityStatus.VALIDATED,
        confidence: 1.0
      }
    })
  } else if (!isValid) {
    await prisma.skillEntity.update({
      where: { id: skillId },
      data: {
        status: EntityStatus.REJECTED,
        confidence: 0
      }
    })
  }

  return prisma.skillEntity.findUnique({
    where: { id: skillId },
    include: { validators: true }
  })
}

/**
 * Extract skills from text
 */
export async function extractSkillsFromText(text: string): Promise<string[]> {
  // Common skill indicators
  const skillPatterns = [
    /skills?:?\s*([^.]+)/gi,
    /experience with\s+([^.]+)/gi,
    /proficient in\s+([^.]+)/gi,
    /expertise in\s+([^.]+)/gi,
    /knowledge of\s+([^.]+)/gi
  ]

  const skills = new Set<string>()

  for (const pattern of skillPatterns) {
    const matches = text.matchAll(pattern)
    for (const match of matches) {
      const skillText = match[1]
      // Split by common separators
      const individualSkills = skillText.split(/[,;]|\s+and\s+/)
      individualSkills.forEach(skill => {
        const cleaned = skill.trim().toLowerCase()
        if (cleaned.length > 2 && cleaned.length < 50) {
          skills.add(cleaned)
        }
      })
    }
  }

  return Array.from(skills)
}

/**
 * Get skill hierarchy
 */
export async function getSkillHierarchy(skillId: string) {
  return prisma.skillEntity.findUnique({
    where: { id: skillId },
    include: {
      parentSkill: true,
      childSkills: {
        include: {
          childSkills: true
        }
      },
      cluster: {
        include: {
          parentCluster: true,
          childClusters: true
        }
      }
    }
  })
}

/**
 * Update market intelligence for skills
 */
export async function updateSkillMarketIntelligence(
  skillId: string,
  data: {
    marketDemand?: number
    salaryPremium?: number
    demandTrend?: string
  }
) {
  return prisma.skillEntity.update({
    where: { id: skillId },
    data
  })
}

/**
 * Get trending skills by cluster
 */
export async function getTrendingSkills(clusterId?: string) {
  const where = clusterId ? { clusterId } : {}
  
  return prisma.skillEntity.findMany({
    where: {
      ...where,
      marketDemand: { gte: 0.7 },
      demandTrend: 'increasing'
    },
    orderBy: [
      { marketDemand: 'desc' },
      { salaryPremium: 'desc' }
    ],
    take: 20,
    include: {
      cluster: true
    }
  })
}