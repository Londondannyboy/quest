import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import {
  findCompaniesByName,
  findSimilarSkills,
  findEducationByName
} from '@/services/entities'

export async function GET(req: NextRequest) {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const searchParams = req.nextUrl.searchParams
    const entityType = searchParams.get('type')
    const query = searchParams.get('q')
    const limit = parseInt(searchParams.get('limit') || '10')

    if (!entityType || !query) {
      return NextResponse.json(
        { error: 'Missing type or query parameter' },
        { status: 400 }
      )
    }

    let results
    switch (entityType) {
      case 'company':
        results = await findCompaniesByName(query, limit)
        break
      case 'skill':
        results = await findSimilarSkills(query, limit)
        break
      case 'education':
        const educationType = searchParams.get('educationType')
        results = await findEducationByName(query, educationType || undefined, limit)
        break
      default:
        return NextResponse.json(
          { error: 'Invalid entity type' },
          { status: 400 }
        )
    }

    return NextResponse.json({ results })
  } catch (error) {
    console.error('Entity search error:', error)
    return NextResponse.json(
      { error: 'Failed to search entities' },
      { status: 500 }
    )
  }
}