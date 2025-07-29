/* eslint-disable @typescript-eslint/no-explicit-any */
export * from './company-entity'
export * from './skill-entity'
export * from './education-entity'
export * from './deduplication'

import { createOrUpdateCompanyEntity, extractCompaniesFromText } from './company-entity'
import { createOrUpdateSkillEntity, extractSkillsFromText } from './skill-entity'
import { createOrUpdateEducationEntity, extractEducationFromText } from './education-entity'
import { ProfessionalMirror } from '@prisma/client'

/**
 * Extract all entities from professional mirror data
 */
export async function extractEntitiesFromProfessionalMirror(
  professionalMirror: ProfessionalMirror
) {
  const entities = {
    companies: [] as any[],
    skills: [] as any[],
    education: [] as any[]
  }

  // Extract from LinkedIn data
  if (professionalMirror.rawLinkedinData) {
    const linkedinData = professionalMirror.rawLinkedinData as any

    // Extract companies from experience
    if (linkedinData.experience) {
      for (const exp of linkedinData.experience) {
        if (exp.company) {
          const company = await createOrUpdateCompanyEntity({
            name: exp.company,
            linkedinUrl: exp.companyLinkedinUrl,
            source: 'linkedin',
            confidence: 0.9,
            metadata: {
              industry: exp.industry,
              employeeCount: exp.companySize
            }
          })
          entities.companies.push(company)
        }
      }
    }

    // Extract education
    if (linkedinData.education) {
      for (const edu of linkedinData.education) {
        if (edu.school) {
          const education = await createOrUpdateEducationEntity({
            name: edu.school,
            type: determineEducationType(edu.school, edu.degree),
            linkedinUrl: edu.schoolLinkedinUrl,
            confidence: 0.9,
            metadata: {
              country: edu.country,
              state: edu.state
            }
          })
          entities.education.push(education)
        }
      }
    }

    // Extract skills
    if (linkedinData.skills) {
      for (const skill of linkedinData.skills) {
        const skillEntity = await createOrUpdateSkillEntity({
          name: skill.name || skill,
          confidence: 0.8
        })
        entities.skills.push(skillEntity)
      }
    }
  }

  // Extract from enrichment data
  if (professionalMirror.enrichmentData) {
    const enrichmentData = professionalMirror.enrichmentData as any

    // Extract current company
    if (enrichmentData.company) {
      const company = await createOrUpdateCompanyEntity({
        name: enrichmentData.company,
        domain: enrichmentData.companyDomain,
        source: 'enrichment',
        confidence: 0.85,
        metadata: {
          industry: enrichmentData.industry,
          description: enrichmentData.companyDescription
        }
      })
      entities.companies.push(company)
    }

    // Extract skills from bio/description
    if (enrichmentData.bio || enrichmentData.description) {
      const text = `${enrichmentData.bio || ''} ${enrichmentData.description || ''}`
      const extractedSkills = await extractSkillsFromText(text)
      
      for (const skillName of extractedSkills) {
        const skill = await createOrUpdateSkillEntity({
          name: skillName,
          confidence: 0.7,
          marketIntelligence: enrichmentData.skillDemand?.[skillName]
        })
        entities.skills.push(skill)
      }
    }
  }

  return entities
}

/**
 * Extract entities from user-provided text (e.g., Trinity responses)
 */
export async function extractEntitiesFromText(text: string) {
  const entities = {
    companies: [] as any[],
    skills: [] as any[],
    education: [] as any[]
  }

  // Extract companies
  const companyNames = await extractCompaniesFromText(text)
  for (const name of companyNames) {
    const company = await createOrUpdateCompanyEntity({
      name,
      source: 'user',
      confidence: 0.6
    })
    entities.companies.push(company)
  }

  // Extract skills
  const skillNames = await extractSkillsFromText(text)
  for (const name of skillNames) {
    const skill = await createOrUpdateSkillEntity({
      name,
      confidence: 0.6
    })
    entities.skills.push(skill)
  }

  // Extract education
  const educationData = await extractEducationFromText(text)
  for (const { name, type } of educationData) {
    const education = await createOrUpdateEducationEntity({
      name,
      type: type as any,
      confidence: 0.6
    })
    entities.education.push(education)
  }

  return entities
}

/**
 * Determine education type from name and degree
 */
function determineEducationType(schoolName: string, degree?: string): 'university' | 'college' | 'bootcamp' | 'certification' {
  const name = schoolName.toLowerCase()
  const deg = degree?.toLowerCase() || ''

  if (name.includes('bootcamp') || name.includes('academy')) {
    return 'bootcamp'
  }
  
  if (deg.includes('certificate') || deg.includes('certification')) {
    return 'certification'
  }
  
  if (name.includes('university') || deg.includes('phd') || deg.includes('master')) {
    return 'university'
  }
  
  return 'college'
}