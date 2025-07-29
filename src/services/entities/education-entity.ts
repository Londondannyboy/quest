import { prisma } from '@/lib/prisma'
import { EntityStatus, Prisma } from '@prisma/client'

interface CreateEducationEntityInput {
  name: string
  type: 'university' | 'college' | 'bootcamp' | 'certification'
  linkedinUrl?: string
  confidence?: number
  metadata?: {
    country?: string
    state?: string
    city?: string
    ranking?: number
    website?: string
  }
}

/**
 * Create or update an education entity with deduplication
 */
export async function createOrUpdateEducationEntity(input: CreateEducationEntityInput) {
  const { name, type, linkedinUrl, metadata, ...rest } = input

  // Try to find existing education by linkedinUrl or name
  const existingEducation = await prisma.educationEntity.findFirst({
    where: {
      OR: [
        ...(linkedinUrl ? [{ linkedinUrl }] : []),
        {
          AND: [
            { name: { equals: name, mode: 'insensitive' as Prisma.QueryMode } },
            { type }
          ]
        }
      ]
    }
  })

  if (existingEducation) {
    // Update if confidence is higher
    if (input.confidence && input.confidence > existingEducation.confidence) {
      return prisma.educationEntity.update({
        where: { id: existingEducation.id },
        data: {
          ...rest,
          ...(metadata || {}),
          confidence: input.confidence
        }
      })
    }
    return existingEducation
  }

  // Create new education entity
  return prisma.educationEntity.create({
    data: {
      name,
      type,
      linkedinUrl,
      ...rest,
      ...(metadata || {})
    }
  })
}

/**
 * Find education institutions by name and type
 */
export async function findEducationByName(name: string, type?: string, limit = 10) {
  const where: Prisma.EducationEntityWhereInput = {
    name: { contains: name, mode: 'insensitive' as Prisma.QueryMode }
  }

  if (type) {
    where.type = type
  }

  return prisma.educationEntity.findMany({
    where,
    orderBy: [
      { ranking: 'asc' },
      { name: 'asc' }
    ],
    take: limit
  })
}

/**
 * Validate an education entity
 */
export async function validateEducationEntity(
  educationId: string,
  userId: string,
  isValid: boolean
) {
  const education = await prisma.educationEntity.findUnique({
    where: { id: educationId },
    include: { validators: true }
  })

  if (!education) {
    throw new Error('Education institution not found')
  }

  // Add user as validator
  await prisma.educationEntity.update({
    where: { id: educationId },
    data: {
      validators: {
        connect: { id: userId }
      }
    }
  })

  // Update status based on validation
  const validatorCount = education.validators.length + 1
  const validationThreshold = 3

  if (isValid && validatorCount >= validationThreshold) {
    await prisma.educationEntity.update({
      where: { id: educationId },
      data: {
        status: EntityStatus.VALIDATED,
        confidence: 1.0
      }
    })
  } else if (!isValid) {
    await prisma.educationEntity.update({
      where: { id: educationId },
      data: {
        status: EntityStatus.REJECTED,
        confidence: 0
      }
    })
  }

  return prisma.educationEntity.findUnique({
    where: { id: educationId },
    include: { validators: true }
  })
}

/**
 * Extract education entities from text
 */
export async function extractEducationFromText(text: string): Promise<Array<{name: string, type: string}>> {
  const educationPatterns = [
    { pattern: /(?:graduated from|attended|studied at)\s+([A-Z][A-Za-z\s]+(?:University|College|Institute|School))/g, type: 'university' },
    { pattern: /(?:BA|BS|MA|MS|MBA|PhD|MD)\s+(?:from|at)\s+([A-Z][A-Za-z\s]+)/g, type: 'university' },
    { pattern: /(?:bootcamp at|completed)\s+([A-Z][A-Za-z\s]+(?:Bootcamp|Academy))/g, type: 'bootcamp' },
    { pattern: /(?:certified in|certification from)\s+([A-Z][A-Za-z\s]+)/g, type: 'certification' }
  ]

  const educations = new Map<string, string>()

  for (const { pattern, type } of educationPatterns) {
    const matches = text.matchAll(pattern)
    for (const match of matches) {
      const name = match[1].trim()
      if (name.length > 3 && name.length < 100) {
        educations.set(name, type)
      }
    }
  }

  return Array.from(educations.entries()).map(([name, type]) => ({ name, type }))
}

/**
 * Get education rankings
 */
export async function getTopEducationInstitutions(type?: string, limit = 20) {
  const where: Prisma.EducationEntityWhereInput = {
    status: EntityStatus.VALIDATED
  }

  if (type) {
    where.type = type
  }

  return prisma.educationEntity.findMany({
    where,
    orderBy: [
      { ranking: 'asc' },
      { users: { _count: 'desc' } }
    ],
    take: limit,
    include: {
      _count: {
        select: { users: true }
      }
    }
  })
}

/**
 * Associate user with education
 */
export async function associateUserWithEducation(
  userId: string,
  educationId: string
   
  // degree?: string,
   
  // graduationYear?: number
) {
  // This creates the many-to-many relationship
  return prisma.user.update({
    where: { id: userId },
    data: {
      userEducation: {
        connect: { id: educationId }
      }
    }
  })
}

/**
 * Get alumni network for an institution
 */
export async function getAlumniNetwork(educationId: string) {
  return prisma.educationEntity.findUnique({
    where: { id: educationId },
    include: {
      users: {
        select: {
          id: true,
          name: true,
          professionalMirror: {
            select: {
              enrichmentData: true
            }
          },
          trinity: {
            select: {
              clarityScore: true
            }
          }
        }
      }
    }
  })
}