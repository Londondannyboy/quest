// Sanity Content Generation Script for SEO-Optimized Pages
// This script creates SEO-optimized pages for private equity placement agents

const { createClient } = require('@sanity/client');

// Initialize Sanity client
const client = createClient({
  projectId: process.env.SANITY_PROJECT_ID || 'your-project-id',
  dataset: process.env.SANITY_DATASET || 'production',
  apiVersion: '2024-01-01',
  token: process.env.SANITY_API_TOKEN || process.env.sanity_api_key,
  useCdn: false
});

// Location data for placement agent pages
const locations = [
  { name: 'London', country: 'UK', region: 'Europe' },
  { name: 'Paris', country: 'France', region: 'Europe' },
  { name: 'Frankfurt', country: 'Germany', region: 'Europe' },
  { name: 'Zurich', country: 'Switzerland', region: 'Europe' },
  { name: 'New York', country: 'USA', region: 'Americas' },
  { name: 'Hong Kong', country: 'China', region: 'Asia' },
  { name: 'Singapore', country: 'Singapore', region: 'Asia' },
  { name: 'Dubai', country: 'UAE', region: 'Middle East' },
  { name: 'Tokyo', country: 'Japan', region: 'Asia' },
  { name: 'Sydney', country: 'Australia', region: 'Asia-Pacific' }
];

// Helper function to create SEO-optimized content with keyword repetition
function createSEOContent(keyword, location = null) {
  const boldKeyword = `**${keyword}**`;
  
  if (location) {
    return [
      {
        _type: 'block',
        style: 'normal',
        children: [
          { _type: 'span', text: 'The ' },
          { _type: 'span', text: keyword, marks: ['strong'] },
          { _type: 'span', text: ` market in ${location.name} represents one of the most sophisticated financial ecosystems in ${location.region}. ` },
          { _type: 'span', text: `Understanding how ${keyword} operate in ${location.country} is crucial for investors and fund managers seeking to navigate this complex landscape.` }
        ]
      },
      {
        _type: 'block',
        style: 'normal',
        children: [
          { _type: 'span', text: `When working with ${keyword}, it's essential to understand the regulatory framework specific to ${location.name}. ` },
          { _type: 'span', text: `The role of ${keyword} has evolved significantly over the past decade, adapting to changing market conditions and investor preferences.` }
        ]
      }
    ];
  } else {
    // Home page content
    return [
      {
        _type: 'block',
        style: 'normal',
        children: [
          { _type: 'span', text: 'Welcome to the premier source for ' },
          { _type: 'span', text: keyword, marks: ['strong'] },
          { _type: 'span', text: ' and insights into the global private equity landscape. ' },
          { _type: 'span', text: `Stay updated with the latest ${keyword} affecting placement agents, fund managers, and institutional investors worldwide.` }
        ]
      }
    ];
  }
}

// Create home/news page
async function createHomePage() {
  const keyword = 'private equity news';
  const homePageDoc = {
    _type: 'seoPage',
    pageType: 'home',
    title: 'Private Equity News and Global Market Insights',
    slug: { current: 'private-equity-news' },
    keyword: keyword,
    metaDescription: `Get the latest private equity news, market insights, and placement agent updates. Your trusted source for private equity news and analysis.`,
    h1: `Global Private Equity News Hub`,
    heroImage: {
      _type: 'image',
      alt: `Private equity news dashboard showing latest market updates`
    },
    introduction: {
      h2: `Latest Private Equity News and Market Trends`,
      content: createSEOContent(keyword)
    },
    mainContent: [
      {
        h2: `Breaking Private Equity News This Week`,
        content: [
          {
            _type: 'block',
            style: 'normal',
            children: [
              { _type: 'span', text: `The ${keyword} landscape continues to evolve with major developments in fund formations and exits. ` },
              { _type: 'span', text: `Industry professionals rely on timely ${keyword} to make informed investment decisions.` }
            ]
          }
        ]
      },
      {
        h2: `Analysis: How Private Equity News Shapes Market Strategies`,
        content: [
          {
            _type: 'block',
            style: 'normal',
            children: [
              { _type: 'span', text: `Understanding the impact of ${keyword} on market dynamics is crucial. ` },
              { _type: 'span', text: 'Access to reliable ' },
              { _type: 'span', text: keyword, marks: ['strong'] },
              { _type: 'span', text: ' helps investors identify emerging opportunities and potential risks in the global marketplace.' }
            ]
          }
        ]
      }
    ],
    news: [
      {
        title: 'Major PE Fund Closes at $5 Billion',
        date: new Date().toISOString(),
        summary: 'Leading placement agents facilitate record-breaking fund closure in European markets.'
      },
      {
        title: 'Asian Private Equity Markets Show Strong Growth',
        date: new Date(Date.now() - 86400000).toISOString(),
        summary: 'Placement agents report increased activity across Singapore and Hong Kong markets.'
      },
      {
        title: 'New Regulations Impact Placement Agent Operations',
        date: new Date(Date.now() - 172800000).toISOString(),
        summary: 'Regulatory changes in the US and EU affect how placement agents structure deals.'
      }
    ],
    seoScore: {
      keywordCount: 5,
      hasKeywordInH1: true,
      hasKeywordInH2: true,
      hasBoldKeyword: true,
      hasKeywordInImages: true
    }
  };

  try {
    const result = await client.create(homePageDoc);
    console.log('✅ Created home page:', result._id);
    return result._id;
  } catch (error) {
    console.error('❌ Error creating home page:', error);
    throw error;
  }
}

// Create placement agent pages for each location
async function createPlacementAgentPage(location, existingPageIds) {
  const keyword = `private equity placement agents ${location.name}`;
  const slug = `private-equity-placement-agents-${location.name.toLowerCase().replace(/\s+/g, '-')}`;
  
  const pageDoc = {
    _type: 'seoPage',
    pageType: 'placement-agent',
    title: `Private Equity Placement Agents ${location.name} - Expert Fund Raising Services`,
    slug: { current: slug },
    keyword: keyword,
    location: `${location.name}, ${location.country}`,
    metaDescription: `Leading private equity placement agents ${location.name} connecting funds with institutional investors. Expert placement agents in ${location.country}.`,
    h1: `Private Equity Placement Agents ${location.name}`,
    heroImage: {
      _type: 'image',
      alt: `Private equity placement agents ${location.name} financial district`
    },
    introduction: {
      h2: `Why Choose Private Equity Placement Agents ${location.name}`,
      content: createSEOContent(keyword, location)
    },
    mainContent: [
      {
        h2: `Services Offered by Private Equity Placement Agents ${location.name}`,
        content: [
          {
            _type: 'block',
            style: 'normal',
            children: [
              { _type: 'span', text: 'The leading ' },
              { _type: 'span', text: keyword, marks: ['strong'] },
              { _type: 'span', text: ` provide comprehensive fundraising services tailored to the ${location.region} market. ` },
              { _type: 'span', text: `These ${keyword} leverage deep relationships with institutional investors, family offices, and sovereign wealth funds.` }
            ]
          },
          {
            _type: 'block',
            style: 'h3',
            children: [{ _type: 'span', text: 'Key Services Include:' }]
          },
          {
            _type: 'block',
            style: 'normal',
            children: [
              { _type: 'span', text: `• Fund structuring and positioning\n• Investor targeting and outreach\n• Due diligence coordination\n• Closing support and documentation` }
            ]
          }
        ],
        image: {
          _type: 'image',
          alt: `Private equity placement agents ${location.name} team meeting`
        }
      },
      {
        h2: `Market Insights: Private Equity Placement Agents ${location.name}`,
        content: [
          {
            _type: 'block',
            style: 'normal',
            children: [
              { _type: 'span', text: `The ${keyword} market has seen significant growth, with fund sizes increasing by 40% over the past five years. ` },
              { _type: 'span', text: `Understanding how ${keyword} navigate local regulations and investor preferences is key to successful fundraising.` }
            ]
          }
        ]
      },
      {
        h2: `Selecting the Right Private Equity Placement Agents ${location.name}`,
        content: [
          {
            _type: 'block',
            style: 'normal',
            children: [
              { _type: 'span', text: `When choosing among ${keyword}, consider their track record, investor network, and sector expertise. ` },
              { _type: 'span', text: 'The best ' },
              { _type: 'span', text: keyword, marks: ['strong'] },
              { _type: 'span', text: ` combine global reach with local market knowledge, ensuring optimal fundraising outcomes.` }
            ]
          }
        ],
        image: {
          _type: 'image',
          alt: `Private equity placement agents ${location.name} office building`
        }
      }
    ],
    internalLinks: existingPageIds.map(id => ({ _type: 'reference', _ref: id })),
    seoScore: {
      keywordCount: 5,
      hasKeywordInH1: true,
      hasKeywordInH2: true,
      hasBoldKeyword: true,
      hasKeywordInImages: true
    }
  };

  try {
    const result = await client.create(pageDoc);
    console.log(`✅ Created placement agent page for ${location.name}:`, result._id);
    return result._id;
  } catch (error) {
    console.error(`❌ Error creating page for ${location.name}:`, error);
    throw error;
  }
}

// Main execution function
async function generateAllContent() {
  console.log('🚀 Starting content generation...\n');
  
  const allPageIds = [];
  
  try {
    // Create home page first
    console.log('📄 Creating home page...');
    const homePageId = await createHomePage();
    allPageIds.push(homePageId);
    
    // Create placement agent pages
    console.log('\n📄 Creating placement agent pages...');
    for (const location of locations) {
      const pageId = await createPlacementAgentPage(location, allPageIds);
      allPageIds.push(pageId);
      
      // Add delay to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // Update all pages with complete internal links
    console.log('\n🔗 Updating internal links...');
    for (const pageId of allPageIds) {
      const otherPageIds = allPageIds.filter(id => id !== pageId);
      await client
        .patch(pageId)
        .set({
          internalLinks: otherPageIds.map(id => ({ _type: 'reference', _ref: id }))
        })
        .commit();
      
      console.log(`✅ Updated internal links for ${pageId}`);
    }
    
    console.log('\n✨ Content generation complete!');
    console.log(`Created ${allPageIds.length} SEO-optimized pages with internal linking.`);
    
  } catch (error) {
    console.error('\n❌ Error during content generation:', error);
  }
}

// Run the script
if (require.main === module) {
  generateAllContent();
}

module.exports = { createHomePage, createPlacementAgentPage, generateAllContent };