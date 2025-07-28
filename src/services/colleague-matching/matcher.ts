import { prisma } from '@/lib/prisma'
import { LinkedInEmployeeData } from '@/services/scraping'
import { Colleague, Company, User } from '@prisma/client'

interface MatchResult {
  isUserMatch: boolean
  existingColleague?: Colleague
  existingQuestUser?: User
}

export class ColleagueMatcher {
  /**
   * Check if an employee from company scrape matches the original user
   */
  async matchEmployee(
    employee: LinkedInEmployeeData, 
    userId: string,
    userLinkedInUrl?: string | null
  ): Promise<MatchResult> {
    // Check if this is the user themselves
    if (userLinkedInUrl && employee.url === userLinkedInUrl) {
      return { isUserMatch: true }
    }

    // Check if this LinkedIn URL already exists as a colleague
    const existingColleague = await prisma.colleague.findUnique({
      where: { linkedinUrl: employee.url }
    })

    // Check if this person is already a Quest user
    const existingQuestUser = await prisma.user.findFirst({
      where: {
        professionalMirror: {
          linkedinUrl: employee.url
        }
      }
    })

    return {
      isUserMatch: false,
      existingColleague: existingColleague || undefined,
      existingQuestUser: existingQuestUser || undefined
    }
  }

  /**
   * Save or update colleague records from company scrape
   */
  async saveColleagues(
    employees: LinkedInEmployeeData[],
    userId: string,
    companyId: string,
    userLinkedInUrl?: string | null,
    limit: number = 50
  ): Promise<{ saved: Colleague[], skipped: number, foundUser: boolean }> {
    const saved: Colleague[] = []
    let skipped = 0
    let foundUser = false

    for (const employee of employees.slice(0, limit)) {
      const match = await this.matchEmployee(employee, userId, userLinkedInUrl)

      if (match.isUserMatch) {
        foundUser = true
        skipped++
        
        // Update user's professional mirror with match info
        await this.updateUserMatchInfo(userId, employee)
        continue
      }

      if (match.existingColleague) {
        // Update existing colleague
        const updated = await prisma.colleague.update({
          where: { id: match.existingColleague.id },
          data: {
            name: employee.name,
            title: employee.title,
            profileImageUrl: employee.profileImageUrl,
            lastUpdated: new Date()
          }
        })
        saved.push(updated)
      } else {
        // Create new colleague
        const created = await prisma.colleague.create({
          data: {
            userId,
            linkedinUrl: employee.url,
            name: employee.name,
            title: employee.title,
            profileImageUrl: employee.profileImageUrl,
            companyId,
            isQuestUser: !!match.existingQuestUser,
            questUserId: match.existingQuestUser?.id
          }
        })
        saved.push(created)
      }
    }

    return { saved, skipped, foundUser }
  }

  /**
   * Update user's professional mirror when found in company scrape
   */
  private async updateUserMatchInfo(userId: string, employee: LinkedInEmployeeData) {
    const professionalMirror = await prisma.professionalMirror.findUnique({
      where: { userId }
    })

    if (professionalMirror) {
      await prisma.professionalMirror.update({
        where: { id: professionalMirror.id },
        data: {
          enrichmentData: {
            ...(professionalMirror.enrichmentData as Record<string, unknown> || {}),
            companyScrapeMatch: {
              name: employee.name,
              title: employee.title,
              profileImageUrl: employee.profileImageUrl,
              matchedAt: new Date()
            }
          }
        }
      })
    }
  }
}