import { ProfessionalMirror, User } from '@prisma/client'
import { extractEntitiesFromProfessionalMirror, extractEntitiesFromText } from './'

/**
 * Hook to extract entities after professional mirror is created/updated
 */
export async function onProfessionalMirrorUpdate(
  user: User,
  professionalMirror: ProfessionalMirror
) {
  try {
    // Extract entities from professional mirror data
    const entities = await extractEntitiesFromProfessionalMirror(professionalMirror)
    
    console.log(`Extracted entities for user ${user.id}:`, {
      companies: entities.companies.length,
      skills: entities.skills.length,
      education: entities.education.length
    })

    return entities
  } catch (error) {
    console.error('Failed to extract entities from professional mirror:', error)
    throw error
  }
}

/**
 * Hook to extract entities after Trinity is saved
 */
export async function onTrinityUpdate(
  user: User,
  trinity: {
    pastQuest?: string | null
    pastService?: string | null
    pastPledge?: string | null
    presentQuest?: string | null
    presentService?: string | null
    presentPledge?: string | null
    futureQuest?: string | null
    futureService?: string | null
    futurePledge?: string | null
  }
) {
  try {
    // Combine all Trinity text
    const allText = [
      trinity.pastQuest,
      trinity.pastService,
      trinity.pastPledge,
      trinity.presentQuest,
      trinity.presentService,
      trinity.presentPledge,
      trinity.futureQuest,
      trinity.futureService,
      trinity.futurePledge
    ].filter(Boolean).join(' ')

    // Extract entities from Trinity text
    const entities = await extractEntitiesFromText(allText)
    
    console.log(`Extracted entities from Trinity for user ${user.id}:`, {
      companies: entities.companies.length,
      skills: entities.skills.length,
      education: entities.education.length
    })

    return entities
  } catch (error) {
    console.error('Failed to extract entities from Trinity:', error)
    throw error
  }
}