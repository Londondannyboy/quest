# Placement Agents Platform - Content Strategy & SEO Authority

*Last Updated: December 2024*

## Overview

This document outlines the comprehensive content strategy for dominating the placement agents SEO landscape using Sanity CMS with MCP integration, automated content generation, and strategic authority building.

## Content Architecture

### 1. Content Types in Sanity

```typescript
// Sanity schema structure
const contentSchemas = {
  // Core content types
  placementAgent: {
    name: string,
    slug: string,
    headquarters: string,
    offices: string[],
    sectors: string[],
    fundSizes: string[],
    notableDeals: array,
    teamMembers: array,
    aum: string,
    description: richText,
    seoMeta: seoFields
  },
  
  locationPage: {
    city: string,
    country: string,
    slug: string,
    marketOverview: richText,
    topAgents: reference[],
    marketSize: string,
    regulations: richText,
    seoMeta: seoFields
  },
  
  sectorGuide: {
    sector: string,
    slug: string,
    overview: richText,
    topAgents: reference[],
    trends: richText,
    dealExamples: array,
    seoMeta: seoFields
  },
  
  comparisonArticle: {
    title: string,
    agents: reference[],
    comparisonTable: table,
    analysis: richText,
    recommendations: richText,
    seoMeta: seoFields
  },
  
  glossaryTerm: {
    term: string,
    definition: richText,
    relatedTerms: reference[],
    examples: richText,
    seoMeta: seoFields
  }
}
```

### 2. SEO-First URL Structure

```
placementagents.ai/
├── /placement-agents/
│   ├── /london/
│   │   ├── /campbell-lutyens
│   │   ├── /monument-group
│   │   └── /top-10-london-placement-agents
│   ├── /new-york/
│   ├── /singapore/
│   └── /by-sector/
│       ├── /technology/
│       ├── /healthcare/
│       └── /infrastructure/
├── /guides/
│   ├── /what-are-placement-agents
│   ├── /placement-agent-fees-explained
│   └── /how-to-choose-placement-agent
├── /compare/
│   ├── /placement-agents-vs-investment-banks
│   └── /boutique-vs-bulge-bracket
└── /glossary/
    ├── /carried-interest
    └── /placement-fee
```

## Content Generation Pipeline

### 1. Data Collection & Intelligence

```javascript
// Weekly data collection workflow
const dataCollection = {
  // Scrape placement agent websites
  async scrapeAgentData() {
    const agents = await db.getActiveAgents()
    
    for (const agent of agents) {
      const data = await firecrawl.extract({
        url: agent.website,
        schema: {
          recentDeals: 'array',
          teamUpdates: 'array',
          newsItems: 'array'
        }
      })
      
      await updateAgentProfile(agent.id, data)
    }
  },
  
  // Monitor industry news
  async trackIndustryNews() {
    const sources = [
      'privateequityinternational.com',
      'preqin.com',
      'pitchbook.com'
    ]
    
    const news = await Promise.all(
      sources.map(source => firecrawl.scrape(source))
    )
    
    return extractPlacementAgentMentions(news)
  },
  
  // Social listening
  async socialIntelligence() {
    const keywords = [
      'placement agent',
      'fundraising advisory',
      'LP introduction'
    ]
    
    const tweets = await lobstr.search(keywords)
    const linkedInPosts = await apify.searchLinkedIn(keywords)
    
    return analyzeSentiment(tweets, linkedInPosts)
  }
}
```

### 2. AI-Powered Content Ideation

```javascript
// Content ideation engine
const contentIdeation = {
  // Analyze search trends
  async findContentOpportunities() {
    const searchData = await getSearchConsoleData()
    const competitorContent = await analyzeCompetitors()
    
    // Find gaps
    const gaps = await mcp.create_document({
      type: 'contentAnalysis',
      instruction: `Analyze search data and competitor content to find:
        1. High-volume keywords with no good content
        2. Questions people ask with no answers
        3. Emerging placement agents not covered
        4. Seasonal fundraising trends`
    })
    
    return gaps
  },
  
  // Generate content calendar
  async createContentCalendar() {
    const opportunities = await findContentOpportunities()
    const events = await getIndustryEvents()
    const seasons = await getFundraisingSeasons()
    
    return mcp.create_document({
      type: 'contentCalendar',
      instruction: `Create 3-month content calendar including:
        - Weekly placement agent profiles
        - Bi-weekly sector guides
        - Monthly comparison articles
        - Event-driven content
        - Seasonal fundraising guides`
    })
  }
}
```

### 3. Automated Content Creation with Sanity MCP

```javascript
// Automated content generation workflows
const contentGeneration = {
  // Generate placement agent profiles
  async createAgentProfile(agentData) {
    // Create main profile
    const profile = await sanityMCP.create_document({
      type: 'placementAgent',
      instruction: `Create comprehensive profile for ${agentData.name} including:
        - Company overview and history
        - Sector specializations with examples
        - Notable transactions (last 3 years)
        - Team bios focusing on expertise
        - Why choose them section
        - Contact information
        
        Optimize for keywords: "${agentData.name} placement agent", 
        "${agentData.name} fundraising", "${agentData.location} placement agent"`
    })
    
    // Generate related content
    await this.createRelatedContent(profile.id, agentData)
    
    return profile
  },
  
  // Create location landing pages
  async createLocationPage(city) {
    const agents = await getAgentsByCity(city)
    
    return sanityMCP.create_document({
      type: 'locationPage',
      instruction: `Create SEO-optimized landing page for "${city} placement agents":
        - Market overview with statistics
        - Top 10 placement agents with brief descriptions
        - Regulatory environment summary
        - Average fees and terms
        - How to choose an agent in ${city}
        
        Target keywords: "placement agents ${city}", 
        "private equity placement agents ${city}",
        "fundraising advisors ${city}"`
    })
  },
  
  // Generate comparison content
  async createComparisonArticle(agents) {
    return sanityMCP.create_document({
      type: 'comparisonArticle',
      instruction: `Create detailed comparison of ${agents.map(a => a.name).join(' vs ')}:
        - Side-by-side comparison table
        - Strengths and weaknesses
        - Ideal client profile for each
        - Fee structure comparison
        - Track record analysis
        - Recommendations by fund size`
    })
  }
}
```

### 4. Content Optimization & Interlinking

```javascript
// SEO optimization workflows
const contentOptimization = {
  // Semantic interlinking
  async addInternalLinks(documentId) {
    // Find related content
    const document = await sanityMCP.getDocument(documentId)
    const related = await sanityMCP.semantic_search({
      query: document.content,
      limit: 10
    })
    
    // Add contextual links
    await sanityMCP.update_document({
      documentId,
      instruction: `Add internal links to these related pages:
        ${related.map(r => `- ${r.title}: ${r.url}`).join('\n')}
        
        Rules:
        - Use natural anchor text
        - Maximum 5 links per article
        - Vary anchor text
        - Link to different content types`
    })
  },
  
  // Meta optimization
  async optimizeMeta(documentId) {
    const document = await sanityMCP.getDocument(documentId)
    
    await sanityMCP.patch_document({
      documentId,
      operation: {
        op: 'set',
        path: 'seoMeta',
        value: await generateOptimizedMeta(document)
      }
    })
  },
  
  // Content clustering
  async createContentCluster(topic) {
    // Pillar page
    const pillar = await sanityMCP.create_document({
      type: 'guide',
      instruction: `Create comprehensive guide on "${topic}"`
    })
    
    // Supporting content
    const subtopics = await identifySubtopics(topic)
    
    for (const subtopic of subtopics) {
      const support = await sanityMCP.create_document({
        type: 'article',
        instruction: `Create article on "${subtopic}" linking back to ${pillar.slug}`
      })
      
      await addInternalLinks(support.id)
    }
  }
}
```

## Authority Building Strategy

### 1. Content Pillars

```javascript
const contentPillars = {
  // Educational pillar
  education: {
    topics: [
      "What are placement agents",
      "How placement agents work",
      "Placement agent fees",
      "Choosing a placement agent"
    ],
    goal: "Establish as educational authority"
  },
  
  // Data pillar
  data: {
    topics: [
      "Placement agent rankings",
      "Fee benchmarks",
      "Success rate statistics",
      "Market size analysis"
    ],
    goal: "Become go-to source for data"
  },
  
  // News pillar
  news: {
    topics: [
      "Latest placement agent moves",
      "New fund launches",
      "Regulatory updates",
      "Market trends"
    ],
    goal: "Timely, relevant updates"
  },
  
  // Tools pillar
  tools: {
    topics: [
      "Placement agent matcher",
      "Fee calculator",
      "Timeline planner",
      "Document checklist"
    ],
    goal: "Practical value for users"
  }
}
```

### 2. Link Building Strategy

```javascript
const linkBuilding = {
  // Create linkable assets
  async createLinkableAssets() {
    // Annual industry report
    await sanityMCP.create_document({
      type: 'report',
      instruction: 'Create "State of Placement Agents 2024" report with unique data'
    })
    
    // Interactive tools
    await createPlacementAgentCalculator()
    await createInteractiveMap()
  },
  
  // Outreach automation
  async conductOutreach() {
    // Find link opportunities
    const opportunities = await findBrokenLinks()
    const mentions = await findUnlinkedMentions()
    
    // Generate outreach emails
    for (const opp of opportunities) {
      await generateOutreachEmail(opp)
    }
  }
}
```

### 3. Content Distribution

```javascript
const distribution = {
  // Multi-channel distribution
  channels: {
    website: "Primary - SEO optimized",
    linkedin: "B2B audience engagement",
    twitter: "Real-time updates",
    newsletter: "Direct audience",
    podcast: "Long-form interviews"
  },
  
  // Automated distribution
  async distributeContent(contentId) {
    const content = await sanityMCP.getDocument(contentId)
    
    // Create variations
    const linkedin = await createLinkedInPost(content)
    const twitter = await createTwitterThread(content)
    const newsletter = await createNewsletterSection(content)
    
    // Schedule distribution
    await scheduleDistribution({
      linkedin,
      twitter,
      newsletter
    })
  }
}
```

## Measurement & Optimization

### KPIs and Tracking

```javascript
const metrics = {
  // SEO metrics
  seo: {
    organicTraffic: "Track growth month-over-month",
    keywordRankings: "Monitor top 100 keywords",
    backlinks: "Quality and quantity",
    domainAuthority: "Track improvement"
  },
  
  // Engagement metrics
  engagement: {
    timeOnSite: "Target 3+ minutes",
    pagesPerSession: "Target 2.5+",
    bounceRate: "Target <40%",
    socialShares: "Track viral content"
  },
  
  // Business metrics
  business: {
    leadGeneration: "Form submissions",
    emailSignups: "Newsletter growth",
    toolUsage: "Calculator engagement",
    apiCalls: "Developer adoption"
  }
}
```

### Continuous Improvement

```javascript
const optimization = {
  // A/B testing
  async testContentVariations() {
    const variations = await createTitleVariations()
    const winner = await runABTest(variations)
    await updateAllSimilarContent(winner)
  },
  
  // Content refresh
  async refreshOldContent() {
    const oldContent = await findContentOlderThan(6, 'months')
    
    for (const content of oldContent) {
      await sanityMCP.update_document({
        documentId: content.id,
        instruction: 'Update statistics, add recent examples, refresh meta'
      })
    }
  }
}
```

## Implementation Timeline

### Month 1: Foundation
- Set up Sanity with MCP
- Create content schemas
- Generate first 50 agent profiles
- Launch 10 city landing pages

### Month 2: Scale
- 200+ agent profiles
- All major city pages
- 20+ sector guides
- Begin comparison content

### Month 3: Authority
- Launch industry report
- Create interactive tools
- Start link building
- Implement distribution

### Month 6: Domination
- 1000+ pieces of content
- Top rankings for major keywords
- Established thought leadership
- Multiple revenue streams

---

*"Dominate placement agents SEO through AI-powered content at scale."*