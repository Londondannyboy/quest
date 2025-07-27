import { NextResponse } from 'next/server'

export async function GET() {
  // List all environment variables that might be database-related
  const envKeys = Object.keys(process.env)
  const dbRelated = envKeys.filter(key => 
    key.includes('DATABASE') || 
    key.includes('POSTGRES') || 
    key.includes('NEON') ||
    key.includes('DB') ||
    key.includes('URL') ||
    key.includes('PG')
  )
  
  // Create a safe response without exposing sensitive data
  const envInfo = dbRelated.reduce((acc, key) => {
    const value = process.env[key]
    if (value && value.includes('postgresql://')) {
      acc[key] = '[PostgreSQL URL Found]'
    } else if (value) {
      acc[key] = `[Value exists: ${value.length} chars]`
    } else {
      acc[key] = '[Not set]'
    }
    return acc
  }, {} as Record<string, string>)
  
  return NextResponse.json({
    found: dbRelated.length,
    variables: envInfo,
    expectedVars: {
      DATABASE_URL: process.env.DATABASE_URL ? '[Set]' : '[Missing]',
      DIRECT_URL: process.env.DIRECT_URL ? '[Set]' : '[Missing]',
    },
    allEnvKeys: envKeys.filter(k => !k.includes('npm_') && !k.includes('PATH')).sort()
  })
}