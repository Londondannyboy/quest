# V3 Sanity Schema Definitions

*Last Updated: December 2024*

## Overview

This document defines all Sanity schemas for Quest V3's unified platform. Everything is stored in Sanity with built-in review workflows.

## Core Schemas

### 1. User Schema

```javascript
// schemas/user.js
export default {
  name: 'user',
  type: 'document',
  title: 'User',
  fields: [
    {
      name: 'clerkId',
      type: 'string',
      title: 'Clerk User ID',
      validation: Rule => Rule.required(),
      readOnly: true
    },
    {
      name: 'email',
      type: 'string',
      validation: Rule => Rule.required().email()
    },
    {
      name: 'name',
      type: 'string',
      validation: Rule => Rule.required()
    },
    {
      name: 'primaryRole',
      type: 'string',
      title: 'Primary Role',
      options: {
        list: [
          {title: 'Founder', value: 'founder'},
          {title: 'Investor', value: 'investor'},
          {title: 'Professional', value: 'professional'},
          {title: 'Journalist', value: 'journalist'}
        ]
      }
    },
    {
      name: 'trinity',
      type: 'object',
      title: 'Trinity',
      fields: [
        {
          name: 'quest',
          type: 'text',
          title: 'Quest - What drives you?'
        },
        {
          name: 'service',
          type: 'text',
          title: 'Service - How do you serve?'
        },
        {
          name: 'pledge',
          type: 'text',
          title: 'Pledge - What do you commit to?'
        }
      ]
    },
    {
      name: 'embedding',
      type: 'array',
      of: [{type: 'number'}],
      title: 'Trinity Embedding',
      hidden: true
    },
    {
      name: 'verified',
      type: 'boolean',
      title: 'Verified User',
      initialValue: false
    }
  ],
  preview: {
    select: {
      title: 'name',
      subtitle: 'primaryRole',
      media: 'image'
    }
  }
}
```

### 2. Investor Schema

```javascript
// schemas/investor.js
export default {
  name: 'investor',
  type: 'document',
  title: 'Investor',
  fields: [
    {
      name: 'name',
      type: 'string',
      title: 'Full Name',
      validation: Rule => Rule.required()
    },
    {
      name: 'firm',
      type: 'string',
      title: 'Firm/Fund Name'
    },
    {
      name: 'type',
      type: 'string',
      title: 'Investor Type',
      options: {
        list: [
          {title: 'Venture Capital', value: 'vc'},
          {title: 'Angel Investor', value: 'angel'},
          {title: 'Family Office', value: 'family-office'},
          {title: 'Corporate VC', value: 'corporate-vc'},
          {title: 'Accelerator', value: 'accelerator'}
        ]
      }
    },
    {
      name: 'categories',
      type: 'array',
      title: 'Investment Categories',
      of: [{type: 'string'}],
      options: {
        list: [
          {title: 'AI/ML', value: 'ai-ml'},
          {title: 'B2B SaaS', value: 'b2b-saas'},
          {title: 'Climate Tech', value: 'climate'},
          {title: 'Consumer', value: 'consumer'},
          {title: 'Crypto/Web3', value: 'crypto'},
          {title: 'Developer Tools', value: 'dev-tools'},
          {title: 'EdTech', value: 'edtech'},
          {title: 'Fintech', value: 'fintech'},
          {title: 'Healthcare', value: 'healthcare'},
          {title: 'Marketplace', value: 'marketplace'}
        ]
      }
    },
    {
      name: 'stages',
      type: 'array',
      title: 'Investment Stages',
      of: [{type: 'string'}],
      options: {
        list: [
          {title: 'Pre-seed', value: 'pre-seed'},
          {title: 'Seed', value: 'seed'},
          {title: 'Series A', value: 'series-a'},
          {title: 'Series B', value: 'series-b'},
          {title: 'Series C+', value: 'series-c-plus'}
        ]
      }
    },
    {
      name: 'checkSize',
      type: 'string',
      title: 'Typical Check Size',
      options: {
        list: [
          {title: 'Under $100K', value: '<100k'},
          {title: '$100K - $500K', value: '100k-500k'},
          {title: '$500K - $1M', value: '500k-1m'},
          {title: '$1M - $5M', value: '1m-5m'},
          {title: '$5M - $10M', value: '5m-10m'},
          {title: 'Over $10M', value: '>10m'}
        ]
      }
    },
    {
      name: 'thesis',
      type: 'text',
      title: 'Investment Thesis'
    },
    {
      name: 'portfolio',
      type: 'array',
      title: 'Notable Portfolio Companies',
      of: [{
        type: 'object',
        fields: [
          {name: 'company', type: 'string'},
          {name: 'year', type: 'number'},
          {name: 'stage', type: 'string'}
        ]
      }]
    },
    {
      name: 'location',
      type: 'object',
      fields: [
        {name: 'city', type: 'string'},
        {name: 'country', type: 'string'},
        {name: 'remote', type: 'boolean', title: 'Invests Remotely'}
      ]
    },
    {
      name: 'contact',
      type: 'object',
      fields: [
        {name: 'email', type: 'string'},
        {name: 'linkedin', type: 'url'},
        {name: 'twitter', type: 'string'},
        {name: 'website', type: 'url'}
      ]
    },
    {
      name: 'verified',
      type: 'boolean',
      title: 'Verified by Human Review',
      initialValue: false
    },
    {
      name: 'reviewNotes',
      type: 'text',
      title: 'Review Notes'
    },
    {
      name: 'source',
      type: 'string',
      title: 'Data Source',
      options: {
        list: ['crunchbase', 'linkedin', 'angellist', 'manual', 'pitchbook']
      }
    },
    {
      name: 'lastUpdated',
      type: 'datetime',
      title: 'Last Updated'
    },
    {
      name: 'embedding',
      type: 'array',
      of: [{type: 'number'}],
      hidden: true
    }
  ],
  preview: {
    select: {
      title: 'name',
      subtitle: 'firm',
      verified: 'verified'
    },
    prepare({title, subtitle, verified}) {
      return {
        title,
        subtitle: `${subtitle}${verified ? ' ✓' : ' (unverified)'}`
      }
    }
  }
}
```

### 3. Job Schema

```javascript
// schemas/job.js
export default {
  name: 'job',
  type: 'document',
  title: 'Job',
  fields: [
    {
      name: 'title',
      type: 'string',
      validation: Rule => Rule.required()
    },
    {
      name: 'company',
      type: 'reference',
      to: [{type: 'organization'}],
      validation: Rule => Rule.required()
    },
    {
      name: 'description',
      type: 'array',
      of: [{type: 'block'}],
      title: 'Job Description'
    },
    {
      name: 'requirements',
      type: 'array',
      title: 'Requirements',
      of: [{type: 'string'}]
    },
    {
      name: 'skills',
      type: 'array',
      title: 'Required Skills',
      of: [{type: 'string'}]
    },
    {
      name: 'experienceLevel',
      type: 'string',
      options: {
        list: [
          {title: 'Entry Level', value: 'entry'},
          {title: 'Mid Level', value: 'mid'},
          {title: 'Senior', value: 'senior'},
          {title: 'Lead', value: 'lead'},
          {title: 'Executive', value: 'executive'}
        ]
      }
    },
    {
      name: 'type',
      type: 'string',
      options: {
        list: [
          {title: 'Full-time', value: 'full-time'},
          {title: 'Part-time', value: 'part-time'},
          {title: 'Contract', value: 'contract'},
          {title: 'Internship', value: 'internship'}
        ]
      }
    },
    {
      name: 'location',
      type: 'object',
      fields: [
        {name: 'city', type: 'string'},
        {name: 'country', type: 'string'},
        {name: 'remote', type: 'boolean'},
        {name: 'hybrid', type: 'boolean'}
      ]
    },
    {
      name: 'salary',
      type: 'object',
      fields: [
        {name: 'min', type: 'number'},
        {name: 'max', type: 'number'},
        {name: 'currency', type: 'string', initialValue: 'USD'},
        {name: 'equity', type: 'boolean'}
      ]
    },
    {
      name: 'trinityScore',
      type: 'object',
      title: 'Trinity Alignment Scores',
      fields: [
        {name: 'quest', type: 'number', validation: Rule => Rule.min(0).max(1)},
        {name: 'service', type: 'number', validation: Rule => Rule.min(0).max(1)},
        {name: 'pledge', type: 'number', validation: Rule => Rule.min(0).max(1)}
      ]
    },
    {
      name: 'applicationUrl',
      type: 'url',
      title: 'Application URL'
    },
    {
      name: 'applicationEmail',
      type: 'string'
    },
    {
      name: 'approved',
      type: 'boolean',
      title: 'Approved for Display',
      initialValue: false
    },
    {
      name: 'source',
      type: 'string',
      options: {
        list: ['linkedin', 'angellist', 'indeed', 'direct', 'ycombinator']
      }
    },
    {
      name: 'postedDate',
      type: 'datetime'
    },
    {
      name: 'expiryDate',
      type: 'datetime'
    },
    {
      name: 'embedding',
      type: 'array',
      of: [{type: 'number'}],
      hidden: true
    }
  ]
}
```

### 4. Organization Schema

```javascript
// schemas/organization.js
export default {
  name: 'organization',
  type: 'document',
  title: 'Organization',
  fields: [
    {
      name: 'name',
      type: 'string',
      validation: Rule => Rule.required()
    },
    {
      name: 'slug',
      type: 'slug',
      options: {
        source: 'name',
        maxLength: 96
      }
    },
    {
      name: 'type',
      type: 'string',
      options: {
        list: [
          {title: 'Startup', value: 'startup'},
          {title: 'Scale-up', value: 'scaleup'},
          {title: 'Enterprise', value: 'enterprise'},
          {title: 'VC Firm', value: 'vc'},
          {title: 'Agency', value: 'agency'}
        ]
      }
    },
    {
      name: 'industry',
      type: 'string'
    },
    {
      name: 'size',
      type: 'string',
      options: {
        list: [
          {title: '1-10', value: '1-10'},
          {title: '11-50', value: '11-50'},
          {title: '51-200', value: '51-200'},
          {title: '201-500', value: '201-500'},
          {title: '500+', value: '500+'}
        ]
      }
    },
    {
      name: 'trinity',
      type: 'object',
      title: 'Organization Trinity',
      fields: [
        {name: 'mission', type: 'text'},
        {name: 'values', type: 'array', of: [{type: 'string'}]},
        {name: 'culture', type: 'text'}
      ]
    },
    {
      name: 'funding',
      type: 'object',
      fields: [
        {name: 'stage', type: 'string'},
        {name: 'totalRaised', type: 'number'},
        {name: 'lastRound', type: 'string'},
        {name: 'investors', type: 'array', of: [{type: 'reference', to: [{type: 'investor'}]}]}
      ]
    },
    {
      name: 'verified',
      type: 'boolean',
      initialValue: false
    }
  ]
}
```

### 5. Journalist Schema

```javascript
// schemas/journalist.js
export default {
  name: 'journalist',
  type: 'document',
  title: 'Journalist',
  fields: [
    {
      name: 'name',
      type: 'string',
      validation: Rule => Rule.required()
    },
    {
      name: 'publication',
      type: 'string',
      title: 'Primary Publication'
    },
    {
      name: 'beats',
      type: 'array',
      title: 'Coverage Areas',
      of: [{type: 'string'}],
      options: {
        list: [
          {title: 'Startups', value: 'startups'},
          {title: 'Funding', value: 'funding'},
          {title: 'AI/Tech', value: 'ai-tech'},
          {title: 'Climate', value: 'climate'},
          {title: 'Healthcare', value: 'healthcare'},
          {title: 'Future of Work', value: 'future-work'},
          {title: 'Profiles', value: 'profiles'}
        ]
      }
    },
    {
      name: 'recentArticles',
      type: 'array',
      of: [{
        type: 'object',
        fields: [
          {name: 'title', type: 'string'},
          {name: 'url', type: 'url'},
          {name: 'date', type: 'date'}
        ]
      }]
    },
    {
      name: 'contact',
      type: 'object',
      fields: [
        {name: 'email', type: 'string'},
        {name: 'twitter', type: 'string'},
        {name: 'linkedin', type: 'url'}
      ]
    },
    {
      name: 'pitchPreferences',
      type: 'text',
      title: 'How They Like to Be Pitched'
    },
    {
      name: 'responseRate',
      type: 'number',
      title: 'Response Rate %',
      validation: Rule => Rule.min(0).max(100)
    },
    {
      name: 'verified',
      type: 'boolean',
      initialValue: false
    },
    {
      name: 'embedding',
      type: 'array',
      of: [{type: 'number'}],
      hidden: true
    }
  ]
}
```

### 6. Article Schema (SEO Content)

```javascript
// schemas/article.js
export default {
  name: 'article',
  type: 'document',
  title: 'Article',
  fields: [
    {
      name: 'title',
      type: 'string',
      validation: Rule => Rule.required()
    },
    {
      name: 'slug',
      type: 'slug',
      options: {
        source: 'title',
        maxLength: 96
      }
    },
    {
      name: 'category',
      type: 'string',
      options: {
        list: [
          {title: 'Investor Profiles', value: 'investor-profiles'},
          {title: 'Startup Guides', value: 'startup-guides'},
          {title: 'Funding Advice', value: 'funding-advice'},
          {title: 'Career Development', value: 'career'},
          {title: 'PR & Media', value: 'pr-media'}
        ]
      }
    },
    {
      name: 'content',
      type: 'array',
      of: [{type: 'block'}]
    },
    {
      name: 'excerpt',
      type: 'text',
      rows: 3
    },
    {
      name: 'seo',
      type: 'object',
      fields: [
        {name: 'metaTitle', type: 'string'},
        {name: 'metaDescription', type: 'string', validation: Rule => Rule.max(160)},
        {name: 'focusKeyword', type: 'string'},
        {name: 'keywords', type: 'array', of: [{type: 'string'}]}
      ]
    },
    {
      name: 'author',
      type: 'reference',
      to: [{type: 'user'}]
    },
    {
      name: 'publishedAt',
      type: 'datetime'
    },
    {
      name: 'aiGenerated',
      type: 'boolean',
      title: 'AI Generated',
      readOnly: true
    },
    {
      name: 'campaign',
      type: 'string',
      title: 'Content Campaign'
    }
  ]
}
```

## Custom Desk Structure

```javascript
// sanity/desk-structure.js
import S from '@sanity/desk-tool/structure-builder'

export default () =>
  S.list()
    .title('Quest Content')
    .items([
      // Review Queues
      S.listItem()
        .title('Review Queues')
        .icon(() => '🔍')
        .child(
          S.list()
            .title('Pending Review')
            .items([
              S.listItem()
                .title('Unverified Investors')
                .child(
                  S.documentList()
                    .title('Investors to Review')
                    .filter('_type == "investor" && !verified')
                    .defaultOrdering([{field: '_createdAt', direction: 'desc'}])
                ),
              S.listItem()
                .title('Unapproved Jobs')
                .child(
                  S.documentList()
                    .title('Jobs to Review')
                    .filter('_type == "job" && !approved')
                ),
              S.listItem()
                .title('Unverified Journalists')
                .child(
                  S.documentList()
                    .title('Journalists to Review')
                    .filter('_type == "journalist" && !verified')
                ),
              S.listItem()
                .title('New Organizations')
                .child(
                  S.documentList()
                    .title('Organizations to Verify')
                    .filter('_type == "organization" && !verified')
                )
            ])
        ),
      
      S.divider(),
      
      // Verified Content
      S.listItem()
        .title('Verified Content')
        .icon(() => '✓')
        .child(
          S.list()
            .title('Approved Items')
            .items([
              S.listItem()
                .title('Active Investors')
                .child(
                  S.documentList()
                    .title('Verified Investors')
                    .filter('_type == "investor" && verified')
                ),
              S.listItem()
                .title('Live Jobs')
                .child(
                  S.documentList()
                    .title('Approved Jobs')
                    .filter('_type == "job" && approved')
                )
            ])
        ),
      
      S.divider(),
      
      // Content Management
      S.listItem()
        .title('Articles')
        .schemaType('article')
        .child(
          S.documentTypeList('article')
        ),
      
      S.divider(),
      
      // All Document Types
      ...S.documentTypeListItems().filter(listItem => 
        !['investor', 'job', 'journalist', 'organization', 'article'].includes(listItem.getId())
      )
    ])
```

## Webhooks for Vector Sync

```javascript
// api/sanity-webhook.js
export default async function handler(req, res) {
  const { _type, _id, verified, approved } = req.body
  
  // Only sync verified/approved content to PG Vector
  if (
    (_type === 'investor' && verified) ||
    (_type === 'job' && approved) ||
    (_type === 'journalist' && verified)
  ) {
    await syncToPGVector(req.body)
  }
  
  res.status(200).json({ success: true })
}

async function syncToPGVector(document) {
  // Generate embedding based on document type
  const embedding = await generateEmbedding(document)
  
  // Upsert to PG Vector
  await pgVector.upsert({
    id: document._id,
    type: document._type,
    embedding: embedding,
    metadata: document
  })
}
```

## Migration Notes

1. **Start Fresh**: Don't migrate old data, begin with clean schemas
2. **Manual Seed**: Hand-curate first 100 investors for quality
3. **Gradual Build**: Add data as you verify quality
4. **Version Control**: Sanity tracks all changes automatically

---

*These schemas provide the foundation for Quest V3's unified data platform with built-in review workflows.*