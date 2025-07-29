import { NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'
import { getNetworkStats } from '@/lib/neo4j'

export async function GET() {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Get user from database
    const user = await prisma.user.findUnique({
      where: { clerkId: userId }
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    // Get network stats from Neo4j
    let stats = await getNetworkStats(user.id)

    // If no stats in Neo4j, calculate from Prisma data
    if (stats.totalConnections === 0) {
      const colleagueCount = await prisma.colleague.count({
        where: { userId: user.id }
      })

      // Get other Quest-ready users
      const questReadyUsers = await prisma.user.count({
        where: {
          id: { not: user.id },
          trinity: {
            clarityScore: { gte: 30 }
          }
        }
      })

      // Calculate average clarity score
      const avgClarity = await prisma.trinity.aggregate({
        _avg: {
          clarityScore: true
        },
        where: {
          clarityScore: { gt: 0 }
        }
      })

      // Count unique companies
      const companies = await prisma.colleague.groupBy({
        by: ['companyId'],
        where: {
          userId: user.id,
          companyId: { not: null }
        }
      })

      stats = {
        totalConnections: colleagueCount + questReadyUsers,
        questReadyConnections: questReadyUsers,
        averageClarityScore: avgClarity._avg.clarityScore || 0,
        companiesRepresented: companies.length
      }
    }

    return NextResponse.json(stats)
  } catch (error) {
    console.error('Network stats error:', error)
    return NextResponse.json(
      { error: 'Failed to load network statistics' },
      { status: 500 }
    )
  }
}