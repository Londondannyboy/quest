export interface LinkedInProfileData {
  url: string
  name?: string
  headline?: string
  about?: string
  currentPosition?: {
    title: string
    company: string
    duration: string
  }
  experiences?: Array<{
    title: string
    company: string
    duration: string
    description?: string
  }>
  education?: Array<{
    school: string
    degree?: string
    field?: string
    dates?: string
  }>
  skills?: string[]
}

export interface LinkedInEmployeeData {
  url: string
  name: string
  title?: string
  profileImageUrl?: string
  location?: string
  connectionDegree?: string
}

export interface CompanyEmployeesResult {
  companyUrl: string
  employees: LinkedInEmployeeData[]
  totalEmployees?: number
}

export interface ScrapingError extends Error {
  code: 'ACTOR_NOT_FOUND' | 'INSUFFICIENT_CREDITS' | 'INVALID_URL' | 'SCRAPING_FAILED'
  details?: unknown
}