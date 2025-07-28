// Re-export from the new service modules for backward compatibility
export { 
  LinkedInProfileScraper,
  CompanyEmployeesScraper,
  type LinkedInProfileData,
  type LinkedInEmployeeData,
  type CompanyEmployeesResult 
} from '@/services/scraping'

import { LinkedInProfileScraper, CompanyEmployeesScraper } from '@/services/scraping'

// Legacy functions for backward compatibility
export async function scrapeLinkedInProfile(linkedinUrl: string) {
  const scraper = new LinkedInProfileScraper()
  return scraper.scrapeProfile(linkedinUrl)
}

export async function scrapeCompanyEmployees(companyUrl: string) {
  const scraper = new CompanyEmployeesScraper()
  return scraper.scrapeEmployees(companyUrl)
}