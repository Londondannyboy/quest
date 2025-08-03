/**
 * Quest Core - Arcade.dev Job Application Example
 * 
 * This example demonstrates how to use Arcade.dev to automatically
 * apply to jobs on behalf of users with Trinity-aligned cover letters
 */

import { ArcadeClient } from '@arcade-ai/sdk'
import { ChatOpenAI } from '@langchain/openai'
import { StateGraph, END } from '@langchain/langgraph'
import { BaseMessage, HumanMessage, AIMessage } from '@langchain/core/messages'
import { z } from 'zod'

// Types
interface UserProfile {
  id: string
  name: string
  email: string
  trinity: {
    quest: string
    service: string
    pledge: string
  }
  experience: string[]
  skills: string[]
  resumeUrl: string
}

interface JobPosting {
  id: string
  title: string
  company: string
  description: string
  requirements: string[]
  applicationEmail: string
  source: string
  postedDate: Date
}

interface ApplicationResult {
  success: boolean
  jobId: string
  emailId?: string
  coverLetter?: string
  error?: string
  followUpScheduled?: boolean
}

// Initialize Arcade client
const arcade = new ArcadeClient({
  apiKey: process.env.ARCADE_API_KEY!
})

// Initialize OpenAI for cover letter generation
const openai = new ChatOpenAI({
  modelName: 'gpt-4-turbo-preview',
  temperature: 0.7
})

/**
 * Calculate Trinity alignment score between job and user profile
 */
async function calculateTrinityAlignment(
  job: JobPosting, 
  profile: UserProfile
): Promise<number> {
  const prompt = `
    Analyze the alignment between this job posting and the user's Trinity.
    
    Job Details:
    Title: ${job.title}
    Company: ${job.company}
    Description: ${job.description}
    Requirements: ${job.requirements.join(', ')}
    
    User's Trinity:
    Quest (Life Purpose): ${profile.trinity.quest}
    Service (How They Contribute): ${profile.trinity.service}
    Pledge (Core Commitment): ${profile.trinity.pledge}
    
    Score the alignment from 0.0 to 1.0 based on:
    1. How well the role aligns with their Quest (40%)
    2. How the job enables their Service (30%)
    3. How the company values match their Pledge (30%)
    
    Return only the numerical score.
  `
  
  const response = await openai.invoke([new HumanMessage(prompt)])
  return parseFloat(response.content.toString())
}

/**
 * Generate a Trinity-aligned cover letter
 */
async function generateTrinityAlignedCoverLetter(
  job: JobPosting,
  profile: UserProfile
): Promise<string> {
  const prompt = `
    Write a compelling cover letter for ${profile.name} applying to the ${job.title} position at ${job.company}.
    
    User's Trinity Foundation:
    - Quest: ${profile.trinity.quest}
    - Service: ${profile.trinity.service}
    - Pledge: ${profile.trinity.pledge}
    
    User's Background:
    - Experience: ${profile.experience.join('; ')}
    - Key Skills: ${profile.skills.join(', ')}
    
    Job Description:
    ${job.description}
    
    Requirements:
    ${job.requirements.join('\n')}
    
    Guidelines:
    1. Open with a compelling hook that connects their Quest to the company's mission
    2. Demonstrate how their Service aligns with the role's impact
    3. Show how their Pledge resonates with company values
    4. Include 2-3 specific examples from their experience
    5. Maintain authentic voice while being professional
    6. Close with enthusiasm and clear next steps
    7. Keep it under 400 words
    
    Format as a professional email ready to send.
  `
  
  const response = await openai.invoke([new HumanMessage(prompt)])
  return response.content.toString()
}

/**
 * Main job application workflow using Arcade
 */
export class TrinityJobApplicationWorkflow {
  private toolManager: any
  
  async initialize(userId: string) {
    this.toolManager = await arcade.createToolManager({
      userId,
      userIdField: 'quest_user_id'
    })
  }
  
  /**
   * Apply to a single job with Trinity alignment
   */
  async applyToJob(
    job: JobPosting,
    profile: UserProfile
  ): Promise<ApplicationResult> {
    try {
      // Step 1: Check Trinity alignment
      const alignmentScore = await calculateTrinityAlignment(job, profile)
      
      if (alignmentScore < 0.75) {
        return {
          success: false,
          jobId: job.id,
          error: `Trinity alignment too low: ${(alignmentScore * 100).toFixed(0)}%`
        }
      }
      
      console.log(`✨ Trinity alignment: ${(alignmentScore * 100).toFixed(0)}%`)
      
      // Step 2: Generate cover letter
      const coverLetter = await generateTrinityAlignedCoverLetter(job, profile)
      console.log('📝 Cover letter generated')
      
      // Step 3: Get Gmail tool (will trigger OAuth if needed)
      const tools = await this.toolManager.getTools(['gmail'])
      const gmailTool = tools.find(t => t.name === 'gmail_send_email')
      
      if (!gmailTool) {
        throw new Error('Gmail tool not available')
      }
      
      // Step 4: Prepare email content
      const emailContent = {
        to: job.applicationEmail,
        subject: `${profile.name} - ${job.title} Application`,
        body: coverLetter,
        attachments: [{
          url: profile.resumeUrl,
          filename: `${profile.name.replace(' ', '_')}_Resume.pdf`
        }]
      }
      
      // Step 5: Send application email
      console.log('📧 Sending application...')
      const emailResult = await gmailTool.invoke(emailContent)
      
      // Step 6: Schedule follow-up
      const followUpScheduled = await this.scheduleFollowUp(job, profile)
      
      // Step 7: Log application in database
      await this.logApplication({
        jobId: job.id,
        userId: profile.id,
        alignmentScore,
        appliedAt: new Date(),
        coverLetter,
        emailId: emailResult.messageId
      })
      
      return {
        success: true,
        jobId: job.id,
        emailId: emailResult.messageId,
        coverLetter,
        followUpScheduled
      }
      
    } catch (error) {
      console.error('Application failed:', error)
      
      // Check if it's an auth error
      if (error.message?.includes('authorization required')) {
        // Return auth URL for user to complete OAuth
        const authUrl = await this.toolManager.getAuthorizationUrl('gmail')
        return {
          success: false,
          jobId: job.id,
          error: `Authorization required. Please visit: ${authUrl}`
        }
      }
      
      return {
        success: false,
        jobId: job.id,
        error: error.message || 'Unknown error occurred'
      }
    }
  }
  
  /**
   * Schedule a follow-up reminder
   */
  private async scheduleFollowUp(
    job: JobPosting,
    profile: UserProfile
  ): Promise<boolean> {
    try {
      const tools = await this.toolManager.getTools(['google_calendar'])
      const calendarTool = tools.find(t => t.name === 'calendar_create_event')
      
      if (!calendarTool) {
        console.log('📅 Calendar tool not available for follow-up')
        return false
      }
      
      const followUpDate = new Date()
      followUpDate.setDate(followUpDate.getDate() + 7) // 1 week later
      
      await calendarTool.invoke({
        summary: `Follow up: ${job.company} - ${job.title}`,
        description: `Follow up on your application for ${job.title} at ${job.company}.
        
Tips for following up:
- Reference your application date
- Reiterate your interest and Trinity alignment
- Ask about next steps in the process
- Keep it brief and professional`,
        start: {
          dateTime: followUpDate.toISOString(),
          timeZone: 'America/New_York'
        },
        end: {
          dateTime: new Date(followUpDate.getTime() + 30 * 60000).toISOString(), // 30 min
          timeZone: 'America/New_York'
        },
        reminders: {
          useDefault: false,
          overrides: [
            { method: 'email', minutes: 60 },
            { method: 'popup', minutes: 10 }
          ]
        }
      })
      
      console.log('📅 Follow-up reminder scheduled')
      return true
    } catch (error) {
      console.error('Failed to schedule follow-up:', error)
      return false
    }
  }
  
  /**
   * Log application to database
   */
  private async logApplication(data: any): Promise<void> {
    // This would save to your database
    // For now, just log it
    console.log('💾 Application logged:', {
      jobId: data.jobId,
      alignmentScore: data.alignmentScore,
      appliedAt: data.appliedAt
    })
  }
  
  /**
   * Batch apply to multiple jobs
   */
  async batchApply(
    jobs: JobPosting[],
    profile: UserProfile,
    options: {
      maxApplications?: number
      minAlignment?: number
      delayBetween?: number
    } = {}
  ): Promise<ApplicationResult[]> {
    const {
      maxApplications = 10,
      minAlignment = 0.75,
      delayBetween = 5000 // 5 seconds
    } = options
    
    // Initialize workflow
    await this.initialize(profile.id)
    
    // Sort jobs by Trinity alignment
    const jobsWithAlignment = await Promise.all(
      jobs.map(async (job) => ({
        job,
        alignment: await calculateTrinityAlignment(job, profile)
      }))
    )
    
    const qualifiedJobs = jobsWithAlignment
      .filter(({ alignment }) => alignment >= minAlignment)
      .sort((a, b) => b.alignment - a.alignment)
      .slice(0, maxApplications)
    
    console.log(`🎯 Found ${qualifiedJobs.length} Trinity-aligned jobs`)
    
    const results: ApplicationResult[] = []
    
    for (const { job, alignment } of qualifiedJobs) {
      console.log(`\n📋 Applying to: ${job.title} at ${job.company}`)
      console.log(`   Trinity Score: ${(alignment * 100).toFixed(0)}%`)
      
      const result = await this.applyToJob(job, profile)
      results.push(result)
      
      if (result.success) {
        console.log(`   ✅ Application sent!`)
      } else {
        console.log(`   ❌ Failed: ${result.error}`)
      }
      
      // Rate limiting
      if (delayBetween > 0) {
        await new Promise(resolve => setTimeout(resolve, delayBetween))
      }
    }
    
    // Summary
    const successful = results.filter(r => r.success).length
    console.log(`\n📊 Summary: ${successful}/${results.length} applications sent`)
    
    return results
  }
}

/**
 * Example usage
 */
async function main() {
  // Example user profile
  const userProfile: UserProfile = {
    id: 'user_123',
    name: 'Sarah Chen',
    email: 'sarah@example.com',
    trinity: {
      quest: 'Democratize AI to empower small businesses',
      service: 'Build intuitive AI tools that non-technical users can master',
      pledge: 'Always prioritize user privacy and ethical AI practices'
    },
    experience: [
      'Senior Software Engineer at TechCorp (3 years)',
      'AI Product Manager at StartupAI (2 years)',
      'Founded AI literacy nonprofit'
    ],
    skills: ['TypeScript', 'Python', 'Machine Learning', 'Product Management', 'User Research'],
    resumeUrl: 'https://example.com/sarah-chen-resume.pdf'
  }
  
  // Example job postings
  const jobs: JobPosting[] = [
    {
      id: 'job_001',
      title: 'AI Product Lead',
      company: 'EthicalAI Inc',
      description: 'Lead our mission to build responsible AI products for SMBs...',
      requirements: ['5+ years in AI/ML', 'Product management experience', 'Passion for ethical AI'],
      applicationEmail: 'careers@ethicalai.com',
      source: 'LinkedIn',
      postedDate: new Date()
    },
    {
      id: 'job_002',
      title: 'Senior Backend Engineer',
      company: 'BigTech Corp',
      description: 'Build scalable systems for our advertising platform...',
      requirements: ['10+ years experience', 'Java expertise', 'Ad tech background'],
      applicationEmail: 'jobs@bigtech.com',
      source: 'Indeed',
      postedDate: new Date()
    }
  ]
  
  // Create workflow instance
  const workflow = new TrinityJobApplicationWorkflow()
  
  // Apply to jobs
  const results = await workflow.batchApply(jobs, userProfile, {
    maxApplications: 5,
    minAlignment: 0.75,
    delayBetween: 3000
  })
  
  // Process results
  for (const result of results) {
    if (result.success) {
      console.log(`✅ Successfully applied to job ${result.jobId}`)
      // Could send notification, update UI, etc.
    } else if (result.error?.includes('Authorization required')) {
      console.log(`🔐 Need authorization: ${result.error}`)
      // Show auth UI to user
    }
  }
}

// Run example if called directly
if (require.main === module) {
  main().catch(console.error)
}