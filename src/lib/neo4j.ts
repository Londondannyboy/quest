/* eslint-disable @typescript-eslint/no-explicit-any */
import neo4j, { Driver } from 'neo4j-driver'

// Neo4j configuration
const NEO4J_URI = process.env.NEO4J_URI || ''
const NEO4J_USER = process.env.NEO4J_USER || 'neo4j'
const NEO4J_PASSWORD = process.env.NEO4J_PASSWORD || ''

let driver: Driver | null = null

function getDriver(): Driver {
  if (!driver) {
    if (!NEO4J_URI || !NEO4J_PASSWORD) {
      throw new Error('Neo4j credentials not configured')
    }
    driver = neo4j.driver(
      NEO4J_URI,
      neo4j.auth.basic(NEO4J_USER, NEO4J_PASSWORD)
    )
  }
  return driver
}

/**
 * Create or update a user node in the graph
 */
export async function createOrUpdateUser(
  userId: string,
  userData: {
    name?: string
    email: string
    linkedinUrl?: string
    company?: string
    title?: string
    isQuestReady?: boolean
    clarityScore?: number
    questStatement?: string
  }
): Promise<void> {
  const driver = getDriver()
  const session = driver.session()
  
  try {
    await session.run(
      `
      MERGE (u:User {userId: $userId})
      SET u += $userData
      SET u.lastUpdated = datetime()
      `,
      { userId, userData }
    )
  } finally {
    await session.close()
  }
}

/**
 * Create colleague relationships from company data
 */
export async function createColleagueRelationships(
  userId: string,
  colleagues: Array<{
    linkedinUrl: string
    name: string
    title?: string
    company?: string
  }>
): Promise<void> {
  const driver = getDriver()
  const session = driver.session()
  
  try {
    // Create colleague nodes and relationships
    for (const colleague of colleagues) {
      await session.run(
        `
        MATCH (u:User {userId: $userId})
        MERGE (c:Colleague {linkedinUrl: $linkedinUrl})
        SET c.name = $name
        SET c.title = $title
        SET c.company = $company
        SET c.lastUpdated = datetime()
        MERGE (u)-[r:WORKS_WITH]->(c)
        SET r.discoveredAt = datetime()
        `,
        {
          userId,
          linkedinUrl: colleague.linkedinUrl,
          name: colleague.name,
          title: colleague.title,
          company: colleague.company
        }
      )
    }
  } finally {
    await session.close()
  }
}

/**
 * Create Quest connections between users
 */
export async function createQuestConnection(
  userId1: string,
  userId2: string,
  connectionType: 'SIMILAR_QUEST' | 'COMPLEMENTARY_QUEST' | 'SHARED_VISION',
  strength: number = 1.0
): Promise<void> {
  const driver = getDriver()
  const session = driver.session()
  
  try {
    await session.run(
      `
      MATCH (u1:User {userId: $userId1})
      MATCH (u2:User {userId: $userId2})
      MERGE (u1)-[r:QUEST_CONNECTION {type: $connectionType}]->(u2)
      SET r.strength = $strength
      SET r.createdAt = datetime()
      `,
      { userId1, userId2, connectionType, strength }
    )
  } finally {
    await session.close()
  }
}

/**
 * Get user's Quest network for visualization
 */
export async function getUserQuestNetwork(
  userId: string,
  depth: number = 2
): Promise<{
  nodes: Array<{
    id: string
    label: string
    type: 'user' | 'colleague'
    isQuestReady?: boolean
    clarityScore?: number
    company?: string
    title?: string
  }>
  links: Array<{
    source: string
    target: string
    type: string
    strength?: number
  }>
}> {
  const driver = getDriver()
  const session = driver.session()
  
  try {
    // Get user and their network
    const result = await session.run(
      `
      MATCH (u:User {userId: $userId})
      OPTIONAL MATCH (u)-[r1:WORKS_WITH]-(c:Colleague)
      OPTIONAL MATCH (u)-[r2:QUEST_CONNECTION]-(other:User)
      WITH u, collect(DISTINCT c) as colleagues, collect(DISTINCT {user: other, rel: r2}) as connections
      
      // Get second degree connections if depth > 1
      OPTIONAL MATCH (other:User)-[r3:QUEST_CONNECTION]-(second:User)
      WHERE other IN [c IN connections | c.user] AND $depth > 1
      WITH u, colleagues, connections, collect(DISTINCT {user: second, rel: r3}) as secondDegree
      
      RETURN u, colleagues, connections, secondDegree
      `,
      { userId, depth }
    )
    
    const nodes: Array<{
      id: string
      label: string
      type: 'user' | 'colleague'
      isQuestReady?: boolean
      clarityScore?: number
      company?: string
      title?: string
    }> = []
    const links: Array<{
      source: string
      target: string
      type: string
      strength?: number
    }> = []
    const nodeIds = new Set<string>()
    
    if (result.records.length > 0) {
      const record = result.records[0]
      const user = record.get('u')
      const colleagues = record.get('colleagues')
      const connections = record.get('connections')
      const secondDegree = record.get('secondDegree')
      
      // Add main user node
      nodes.push({
        id: user.properties.userId,
        label: user.properties.name || user.properties.email,
        type: 'user',
        isQuestReady: user.properties.isQuestReady,
        clarityScore: user.properties.clarityScore,
        company: user.properties.company,
        title: user.properties.title
      })
      nodeIds.add(user.properties.userId)
      
      // Add colleague nodes
      colleagues.forEach((colleague: unknown) => {
        const colleagueNode = colleague as { properties: Record<string, any> }
        const id = colleagueNode.properties.linkedinUrl
        if (!nodeIds.has(id)) {
          nodes.push({
            id,
            label: colleagueNode.properties.name,
            type: 'colleague',
            company: colleagueNode.properties.company,
            title: colleagueNode.properties.title
          })
          nodeIds.add(id)
          
          // Add link
          links.push({
            source: user.properties.userId,
            target: id,
            type: 'WORKS_WITH'
          })
        }
      })
      
      // Add connected users
      connections.forEach((conn: unknown) => {
        const connection = conn as { user: any; rel: any }
        const otherUser = connection.user
        const rel = connection.rel
        
        if (otherUser && !nodeIds.has(otherUser.properties.userId)) {
          nodes.push({
            id: otherUser.properties.userId,
            label: otherUser.properties.name || otherUser.properties.email,
            type: 'user',
            isQuestReady: otherUser.properties.isQuestReady,
            clarityScore: otherUser.properties.clarityScore,
            company: otherUser.properties.company,
            title: otherUser.properties.title
          })
          nodeIds.add(otherUser.properties.userId)
        }
        
        if (rel) {
          links.push({
            source: user.properties.userId,
            target: otherUser.properties.userId,
            type: rel.properties.type,
            strength: rel.properties.strength
          })
        }
      })
      
      // Add second degree connections if requested
      if (depth > 1) {
        secondDegree.forEach((conn: unknown) => {
          const secondConn = conn as { user: any; rel: any }
          const secondUser = secondConn.user
          // const rel = conn.rel // TODO: Use for relationship properties
          
          if (secondUser && !nodeIds.has(secondUser.properties.userId)) {
            nodes.push({
              id: secondUser.properties.userId,
              label: secondUser.properties.name || secondUser.properties.email,
              type: 'user',
              isQuestReady: secondUser.properties.isQuestReady,
              clarityScore: secondUser.properties.clarityScore,
              company: secondUser.properties.company,
              title: secondUser.properties.title
            })
            nodeIds.add(secondUser.properties.userId)
          }
        })
      }
    }
    
    return { nodes, links }
  } finally {
    await session.close()
  }
}

/**
 * Find potential Quest connections based on Trinity similarity
 */
export async function findPotentialQuestConnections(
  userId: string,
  trinity: {
    quest?: string
    service?: string
    pledge?: string
  }
): Promise<Array<{
  userId: string
  name: string
  similarity: number
  matchType: string
}>> {
  const driver = getDriver()
  const session = driver.session()
  
  try {
    // Find users with similar Quests using text similarity
    const result = await session.run(
      `
      MATCH (u:User {userId: $userId})
      MATCH (other:User)
      WHERE other.userId <> $userId 
        AND other.isQuestReady = true
        AND NOT EXISTS((u)-[:QUEST_CONNECTION]-(other))
      WITH other, 
        CASE 
          WHEN other.questStatement CONTAINS $questKeyword THEN 0.5
          ELSE 0
        END +
        CASE
          WHEN other.company = u.company THEN 0.3
          ELSE 0
        END +
        CASE
          WHEN other.clarityScore > 50 THEN 0.2
          ELSE 0
        END as similarity
      WHERE similarity > 0.3
      RETURN other.userId as userId, 
             other.name as name,
             similarity,
             CASE
               WHEN other.questStatement CONTAINS $questKeyword THEN 'Similar Quest'
               WHEN other.company = u.company THEN 'Same Company'
               ELSE 'High Clarity'
             END as matchType
      ORDER BY similarity DESC
      LIMIT 10
      `,
      {
        userId,
        questKeyword: trinity.quest?.split(' ')[0] || '' // Simple keyword matching
      }
    )
    
    return result.records.map(record => ({
      userId: record.get('userId'),
      name: record.get('name'),
      similarity: record.get('similarity'),
      matchType: record.get('matchType')
    }))
  } finally {
    await session.close()
  }
}

/**
 * Get Quest network statistics
 */
export async function getNetworkStats(userId: string): Promise<{
  totalConnections: number
  questReadyConnections: number
  averageClarityScore: number
  companiesRepresented: number
}> {
  const driver = getDriver()
  const session = driver.session()
  
  try {
    const result = await session.run(
      `
      MATCH (u:User {userId: $userId})
      OPTIONAL MATCH (u)-[:WORKS_WITH|QUEST_CONNECTION]-(connected)
      WITH u, collect(DISTINCT connected) as connections
      RETURN 
        size(connections) as totalConnections,
        size([c IN connections WHERE c:User AND c.isQuestReady = true]) as questReadyConnections,
        avg([c IN connections WHERE c:User | c.clarityScore]) as averageClarityScore,
        size(collect(DISTINCT [c IN connections | c.company])) as companiesRepresented
      `,
      { userId }
    )
    
    if (result.records.length > 0) {
      const record = result.records[0]
      return {
        totalConnections: record.get('totalConnections').toNumber(),
        questReadyConnections: record.get('questReadyConnections').toNumber(),
        averageClarityScore: record.get('averageClarityScore') || 0,
        companiesRepresented: record.get('companiesRepresented').toNumber()
      }
    }
    
    return {
      totalConnections: 0,
      questReadyConnections: 0,
      averageClarityScore: 0,
      companiesRepresented: 0
    }
  } finally {
    await session.close()
  }
}

/**
 * Close the Neo4j driver connection
 */
export async function closeConnection(): Promise<void> {
  if (driver) {
    await driver.close()
    driver = null
  }
}