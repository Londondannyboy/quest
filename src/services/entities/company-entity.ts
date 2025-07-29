import { prisma } from '@/lib/prisma'
import { EntityStatus, Prisma } from '@prisma/client'

interface CreateCompanyEntityInput {
  name: string
  domain?: string
  linkedinUrl?: string
  parentCompanyId?: string
  confidence?: number
  source?: string
  metadata?: {
    employeeCount?: number
    foundedYear?: number
    industry?: string
    headquarters?: string
    description?: string
  }
}

/**
 * Create or update a company entity with deduplication
 */
export async function createOrUpdateCompanyEntity(input: CreateCompanyEntityInput) {
  const { name, domain, linkedinUrl, metadata, ...rest } = input

  // Try to find existing company by domain or linkedinUrl
  const existingCompany = await prisma.companyEntity.findFirst({
    where: {
      OR: [
        ...(domain ? [{ domain }] : []),
        ...(linkedinUrl ? [{ linkedinUrl }] : []),
        { name: { equals: name, mode: 'insensitive' as Prisma.QueryMode } }
      ]
    }
  })

  if (existingCompany) {
    // Update existing company if confidence is higher
    if (input.confidence && input.confidence > existingCompany.confidence) {
      return prisma.companyEntity.update({
        where: { id: existingCompany.id },
        data: {
          ...rest,
          ...(metadata || {}),
          confidence: input.confidence,
          lastScraped: new Date()
        }
      })
    }
    return existingCompany
  }

  // Create new company entity
  return prisma.companyEntity.create({
    data: {
      name,
      domain,
      linkedinUrl,
      ...rest,
      ...(metadata || {}),
      lastScraped: new Date()
    }
  })
}

/**
 * Find companies using fuzzy matching
 */
export async function findCompaniesByName(name: string, limit = 10) {
  // First try exact match
  const exactMatches = await prisma.companyEntity.findMany({
    where: {
      name: { equals: name, mode: 'insensitive' as Prisma.QueryMode }
    },
    take: limit
  })

  if (exactMatches.length >= limit) {
    return exactMatches
  }

  // Then try contains match
  const containsMatches = await prisma.companyEntity.findMany({
    where: {
      name: { contains: name, mode: 'insensitive' as Prisma.QueryMode }
    },
    take: limit - exactMatches.length
  })

  return [...exactMatches, ...containsMatches]
}

/**
 * Validate a company entity
 */
export async function validateCompanyEntity(
  companyId: string,
  userId: string,
  isValid: boolean
) {
  const company = await prisma.companyEntity.findUnique({
    where: { id: companyId },
    include: { validators: true }
  })

  if (!company) {
    throw new Error('Company not found')
  }

  // Add user as validator
  await prisma.companyEntity.update({
    where: { id: companyId },
    data: {
      validators: {
        connect: { id: userId }
      }
    }
  })

  // Update status based on validation threshold
  const validatorCount = company.validators.length + 1
  const validationThreshold = 3 // Number of validations needed

  if (isValid && validatorCount >= validationThreshold) {
    await prisma.companyEntity.update({
      where: { id: companyId },
      data: {
        status: EntityStatus.VALIDATED,
        confidence: 1.0
      }
    })
  } else if (!isValid) {
    await prisma.companyEntity.update({
      where: { id: companyId },
      data: {
        status: EntityStatus.REJECTED,
        confidence: 0
      }
    })
  }

  return prisma.companyEntity.findUnique({
    where: { id: companyId },
    include: { validators: true }
  })
}

/**
 * Extract company entities from text using AI
 */
export async function extractCompaniesFromText(text: string): Promise<string[]> {
  // This would use OpenRouter to extract company names
  // For now, return a simple regex extraction
  const companyPattern = /(?:at|with|for|joined)\s+([A-Z][A-Za-z0-9\s&]+?)(?:\s+as|\s+in|\s+to|,|\.|$)/g
  const matches = text.matchAll(companyPattern)
  const companies = Array.from(matches, m => m[1].trim())
  
  return [...new Set(companies)]
}

/**
 * Get company hierarchy
 */
export async function getCompanyHierarchy(companyId: string) {
  const company = await prisma.companyEntity.findUnique({
    where: { id: companyId },
    include: {
      parentCompany: true,
      subsidiaries: {
        include: {
          subsidiaries: true
        }
      }
    }
  })

  return company
}

/**
 * Merge duplicate companies
 */
export async function mergeCompanies(primaryId: string, duplicateId: string) {
  // Transfer all relationships to primary company
  await prisma.$transaction(async (tx) => {
    // Update all references
    await tx.company.updateMany({
      where: { id: duplicateId },
      data: { id: primaryId }
    })

    // Merge validators
    const duplicate = await tx.companyEntity.findUnique({
      where: { id: duplicateId },
      include: { validators: true }
    })

    if (duplicate) {
      await tx.companyEntity.update({
        where: { id: primaryId },
        data: {
          validators: {
            connect: duplicate.validators.map(v => ({ id: v.id }))
          }
        }
      })
    }

    // Delete duplicate
    await tx.companyEntity.delete({
      where: { id: duplicateId }
    })
  })
}