import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { prisma } from '@/lib/prisma'
import { getUserQuestNetwork, createOrUpdateUser } from '@/lib/neo4j'

export async function GET(req: NextRequest) {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const searchParams = req.nextUrl.searchParams
    const depth = parseInt(searchParams.get('depth') || '2')

    // Get user data from Prisma
    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
      include: {
        trinity: true,
        professionalMirror: true,
        colleagues: true
      }
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    // Update user in Neo4j
    await createOrUpdateUser(user.id, {
      name: user.name || undefined,
      email: user.email,
      linkedinUrl: user.professionalMirror?.linkedinUrl || undefined,
      isQuestReady: (user.trinity?.clarityScore || 0) >= 30,
      clarityScore: user.trinity?.clarityScore || 0,
      questStatement: user.trinity?.futureQuest || undefined
    })

    // Get network from Neo4j
    const networkData = await getUserQuestNetwork(user.id, depth)

    // For demo purposes, if no network data, create sample data
    if (networkData.nodes.length === 0) {
      // Add current user
      networkData.nodes.push({
        id: user.id,
        label: user.name || user.email,
        type: 'user',
        isQuestReady: (user.trinity?.clarityScore || 0) >= 30,
        clarityScore: user.trinity?.clarityScore || 0,
        company: user.professionalMirror?.enrichmentData?.company || undefined,
        title: user.professionalMirror?.enrichmentData?.title || undefined
      })

      // Add colleagues from database
      if (user.colleagues.length > 0) {
        user.colleagues.forEach(colleague => {
          networkData.nodes.push({
            id: colleague.linkedinUrl,
            label: colleague.name,
            type: 'colleague',
            company: colleague.company?.name || undefined,
            title: colleague.title || undefined
          })

          networkData.links.push({
            source: user.id,
            target: colleague.linkedinUrl,
            type: 'WORKS_WITH'
          })
        })
      }

      // Add some demo Quest-ready users
      const demoUsers = [
        {
          id: 'demo-user-1',
          label: 'Sarah Chen',
          type: 'user' as const,
          isQuestReady: true,
          clarityScore: 85,
          company: 'TechCorp',
          title: 'Product Lead'
        },
        {
          id: 'demo-user-2',
          label: 'Marcus Johnson',
          type: 'user' as const,
          isQuestReady: true,
          clarityScore: 72,
          company: 'InnovateLabs',
          title: 'Engineering Director'
        },
        {
          id: 'demo-user-3',
          label: 'Emily Rodriguez',
          type: 'user' as const,
          isQuestReady: false,
          clarityScore: 25,
          company: 'StartupXYZ',
          title: 'Designer'
        }
      ]

      demoUsers.forEach(demoUser => {
        networkData.nodes.push(demoUser)
        
        // Create random connections
        if (Math.random() > 0.5) {
          networkData.links.push({
            source: user.id,
            target: demoUser.id,
            type: demoUser.isQuestReady ? 'SIMILAR_QUEST' : 'WORKS_WITH',
            strength: Math.random() * 0.5 + 0.5
          })
        }
      })

      // Add second-degree connections if depth > 1
      if (depth > 1) {
        networkData.nodes.push({
          id: 'demo-user-4',
          label: 'Alex Kim',
          type: 'user',
          isQuestReady: true,
          clarityScore: 90,
          company: 'FutureTech',
          title: 'CEO'
        })

        networkData.links.push({
          source: 'demo-user-1',
          target: 'demo-user-4',
          type: 'COMPLEMENTARY_QUEST',
          strength: 0.8
        })
      }
    }

    return NextResponse.json(networkData)
  } catch (error) {
    console.error('Quest network error:', error)
    return NextResponse.json(
      { error: 'Failed to load network data' },
      { status: 500 }
    )
  }
}