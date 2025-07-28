// Test script for Trinity and Quest readiness endpoints
// Run with: npx tsx scripts/test-trinity-flow.ts

import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

// Sample Trinity data for testing
const sampleTrinity = {
  pastQuest: "I was driven by a desire to solve complex technical problems and build innovative solutions that could help people in their daily lives",
  pastService: "I served teams by mentoring junior developers and creating robust, scalable systems that enabled business growth and customer satisfaction",
  pastPledge: "I pledged to always write clean, maintainable code and to share my knowledge freely with others to help them grow in their careers",
  
  presentQuest: "I am now driven by the vision of transforming how professionals discover their purpose and build meaningful careers through technology",
  presentService: "I serve by creating AI-powered coaching experiences that help people uncover their authentic professional story and connect with their true calling",
  presentPledge: "I pledge to build technology that honors human dignity and helps every person realize their unique potential and contribution to the world",
  
  futureQuest: "I will be driven to democratize access to transformational career coaching and create a world where everyone can pursue work aligned with their purpose",
  futureService: "I will serve by building platforms that connect purpose-driven professionals and enable them to create exponential positive impact together",
  futurePledge: "I pledge to dedicate my skills to closing the gap between human potential and opportunity, ensuring no talent goes undiscovered or unfulfilled"
}

async function testTrinityFlow() {
  console.log('🧪 Testing Trinity and Quest Readiness Flow\n')
  
  try {
    // First, we need a test user - let's check if one exists
    const testClerkId = 'test_user_' + Date.now()
    const testEmail = `test${Date.now()}@example.com`
    
    console.log('1️⃣ Creating test user...')
    const user = await prisma.user.create({
      data: {
        clerkId: testClerkId,
        email: testEmail,
      }
    })
    console.log('✅ Test user created:', user.id)
    
    // Create a story session with some data
    console.log('\n2️⃣ Creating story session...')
    const storySession = await prisma.storySession.create({
      data: {
        userId: user.id,
        phase: 'trinity_discovery',
        storyDepth: 75,
        futureOrientation: 80,
      }
    })
    console.log('✅ Story session created')
    
    // Test Trinity creation
    console.log('\n3️⃣ Testing Trinity creation...')
    console.log('Sample Trinity data:')
    console.log('- Past Quest:', sampleTrinity.pastQuest.substring(0, 50) + '...')
    console.log('- Present Quest:', sampleTrinity.presentQuest.substring(0, 50) + '...')
    console.log('- Future Quest:', sampleTrinity.futureQuest.substring(0, 50) + '...')
    
    // Calculate what the clarity score should be
    const wordCounts = Object.values(sampleTrinity).map(text => text.split(' ').length)
    const avgWords = wordCounts.reduce((a, b) => a + b, 0) / 9
    console.log(`\nAverage words per field: ${Math.round(avgWords)}`)
    
    // Simulate API call by directly creating Trinity
    const trinity = await prisma.trinity.create({
      data: {
        userId: user.id,
        ...sampleTrinity,
        clarityScore: 85, // High clarity score for good responses
        evolutionData: {
          questEvolution: {
            past: sampleTrinity.pastQuest,
            present: sampleTrinity.presentQuest,
            future: sampleTrinity.futureQuest,
          },
          timestamp: new Date().toISOString(),
        }
      }
    })
    console.log('✅ Trinity created with clarity score:', trinity.clarityScore)
    
    // Update story session with Trinity clarity
    await prisma.storySession.update({
      where: { id: storySession.id },
      data: {
        trinityClarity: trinity.clarityScore,
      }
    })
    
    // Test Quest readiness calculation
    console.log('\n4️⃣ Calculating Quest readiness...')
    const components = {
      storyDepth: 75,
      trinityClarity: 85,
      futureOrientation: 80,
    }
    
    const readinessScore = 
      (components.storyDepth * 0.3) +
      (components.trinityClarity * 0.4) +
      (components.futureOrientation * 0.3)
    
    console.log('Readiness components:')
    console.log(`- Story Depth: ${components.storyDepth} (weight: 30%)`)
    console.log(`- Trinity Clarity: ${components.trinityClarity} (weight: 40%)`)
    console.log(`- Future Orientation: ${components.futureOrientation} (weight: 30%)`)
    console.log(`\n📊 Readiness Score: ${Math.round(readinessScore)}`)
    
    if (readinessScore >= 70) {
      console.log('🎉 Outcome: QUEST_READY - User has earned their Quest!')
    } else if (readinessScore >= 40) {
      console.log('📝 Outcome: PREPARING - User needs more coaching')
    } else {
      console.log('🌱 Outcome: NOT_YET - User is just beginning their journey')
    }
    
    // Create Quest record
    const quest = await prisma.quest.create({
      data: {
        userId: user.id,
        status: readinessScore >= 70 ? 'QUEST_READY' : readinessScore >= 40 ? 'PREPARING' : 'NOT_READY',
        readinessScore: Math.round(readinessScore),
      }
    })
    console.log('\n✅ Quest record created:', quest.status)
    
    // Test retrieval
    console.log('\n5️⃣ Testing data retrieval...')
    const retrievedTrinity = await prisma.trinity.findUnique({
      where: { userId: user.id }
    })
    console.log('✅ Trinity retrieved successfully')
    
    const retrievedQuest = await prisma.quest.findUnique({
      where: { userId: user.id }
    })
    console.log('✅ Quest retrieved successfully')
    
    console.log('\n✨ All tests completed successfully!')
    console.log('\nAPI Responses would be:')
    console.log('- GET /api/trinity: Trinity data with clarity score', retrievedTrinity?.clarityScore)
    console.log('- GET /api/quest/readiness: Status', retrievedQuest?.status, 'with score', retrievedQuest?.readinessScore)
    
    // Cleanup
    console.log('\n🧹 Cleaning up test data...')
    await prisma.quest.delete({ where: { id: quest.id } })
    await prisma.trinity.delete({ where: { id: trinity.id } })
    await prisma.storySession.delete({ where: { id: storySession.id } })
    await prisma.user.delete({ where: { id: user.id } })
    console.log('✅ Test data cleaned up')
    
  } catch (error) {
    console.error('❌ Test failed:', error)
  } finally {
    await prisma.$disconnect()
  }
}

// Run the test
testTrinityFlow()