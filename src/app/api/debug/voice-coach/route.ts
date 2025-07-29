import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { 
  debugVoiceCoachSession, 
  analyzeCodeForIssues,
  generateDebugReport 
} from '@/services/ai-debugger'
import { readFileSync } from 'fs'
import { join } from 'path'

export async function POST(req: NextRequest) {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const { action, sessionId, issue } = await req.json()

    switch (action) {
      case 'debug-session': {
        // Debug a specific session
        const result = await debugVoiceCoachSession({
          sessionId,
          issue: issue || 'Duplicate audio streams and no interruption capability'
        })
        
        return NextResponse.json(result)
      }
      
      case 'analyze-code': {
        // Read relevant code files
        const trinityPath = join(process.cwd(), 'src/app/trinity/page.tsx')
        const clmPath = join(process.cwd(), 'src/app/api/hume-clm-sse/chat/completions/route.ts')
        
        const codeFiles = [
          {
            path: 'trinity/page.tsx',
            content: readFileSync(trinityPath, 'utf-8').slice(0, 10000) // Limit size
          },
          {
            path: 'api/hume-clm-sse/route.ts',
            content: readFileSync(clmPath, 'utf-8').slice(0, 5000)
          }
        ]
        
        const result = await analyzeCodeForIssues(
          codeFiles,
          'Duplicate voice streams playing, no interruption capability, user context not working'
        )
        
        return NextResponse.json(result)
      }
      
      case 'generate-report': {
        // Generate full debug report
        const report = await generateDebugReport(sessionId)
        return NextResponse.json({ report })
      }
      
      default:
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
    }
  } catch (error) {
    console.error('Debug API error:', error)
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}

export async function GET() {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Return available debug actions
    return NextResponse.json({
      actions: [
        {
          name: 'debug-session',
          description: 'Debug a specific voice coach session',
          params: ['sessionId', 'issue']
        },
        {
          name: 'analyze-code',
          description: 'Analyze code for potential issues',
          params: ['issue']
        },
        {
          name: 'generate-report',
          description: 'Generate a full debug report for a session',
          params: ['sessionId']
        }
      ]
    })
  } catch (error) {
    console.error('Debug API error:', error)
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}