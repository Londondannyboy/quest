import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'
import { 
  validateCompanyEntity,
  validateSkillEntity,
  validateEducationEntity
} from '@/services/entities'

export async function POST(req: NextRequest) {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const { entityType, entityId, isValid } = await req.json()

    if (!entityType || !entityId || typeof isValid !== 'boolean') {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      )
    }

    // Get user
    const user = await prisma.user.findUnique({
      where: { clerkId: userId }
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    let result
    switch (entityType) {
      case 'company':
        result = await validateCompanyEntity(entityId, user.id, isValid)
        break
      case 'skill':
        result = await validateSkillEntity(entityId, user.id, isValid)
        break
      case 'education':
        result = await validateEducationEntity(entityId, user.id, isValid)
        break
      default:
        return NextResponse.json(
          { error: 'Invalid entity type' },
          { status: 400 }
        )
    }

    return NextResponse.json({ 
      success: true,
      entity: result
    })
  } catch (error) {
    console.error('Entity validation error:', error)
    return NextResponse.json(
      { error: 'Failed to validate entity' },
      { status: 500 }
    )
  }
}