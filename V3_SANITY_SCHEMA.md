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

### 6. News Article Schema

```javascript
// schemas/newsArticle.js
export default {
  name: 'newsArticle',
  type: 'document',
  title: 'News Article',
  fields: [
    {
      name: 'headline',
      type: 'string',
      title: 'Headline',
      validation: Rule => Rule.required().max(120)
    },
    {
      name: 'slug',
      type: 'slug',
      options: {
        source: 'headline',
        maxLength: 96
      }
    },
    {
      name: 'subheading',
      type: 'string',
      title: 'Subheading',
      validation: Rule => Rule.max(200)
    },
    {
      name: 'category',
      type: 'string',
      title: 'News Category',
      options: {
        list: [
          {title: 'Funding News', value: 'funding'},
          {title: 'Market Moves', value: 'market-moves'},
          {title: 'People & Leadership', value: 'people'},
          {title: 'Product Launches', value: 'products'},
          {title: 'Industry Analysis', value: 'analysis'},
          {title: 'Deals & Exits', value: 'deals'},
          {title: 'Innovation & Tech', value: 'tech'}
        ]
      }
    },
    {
      name: 'content',
      type: 'array',
      title: 'Article Content',
      of: [
        {type: 'block'},
        {
          type: 'image',
          fields: [
            {name: 'caption', type: 'string'},
            {name: 'alt', type: 'string'}
          ]
        }
      ]
    },
    {
      name: 'excerpt',
      type: 'text',
      title: 'Excerpt',
      rows: 3,
      validation: Rule => Rule.required().max(300)
    },
    {
      name: 'featuredImage',
      type: 'image',
      title: 'Featured Image',
      options: {
        hotspot: true
      }
    },
    {
      name: 'relatedEntities',
      type: 'object',
      title: 'Related Entities',
      fields: [
        {
          name: 'organizations',
          type: 'array',
          of: [{type: 'reference', to: [{type: 'organization'}]}]
        },
        {
          name: 'investors',
          type: 'array',
          of: [{type: 'reference', to: [{type: 'investor'}]}]
        },
        {
          name: 'people',
          type: 'array',
          of: [{type: 'reference', to: [{type: 'user'}]}]
        }
      ]
    },
    {
      name: 'source',
      type: 'object',
      title: 'Source Information',
      fields: [
        {name: 'type', type: 'string', options: {list: ['original', 'curated', 'syndicated']}},
        {name: 'author', type: 'reference', to: [{type: 'user'}, {type: 'journalist'}]},
        {name: 'publication', type: 'string'},
        {name: 'originalUrl', type: 'url'}
      ]
    },
    {
      name: 'publishedAt',
      type: 'datetime',
      title: 'Published Date',
      validation: Rule => Rule.required()
    },
    {
      name: 'status',
      type: 'string',
      title: 'Publication Status',
      options: {
        list: [
          {title: 'Draft', value: 'draft'},
          {title: 'Review', value: 'review'},
          {title: 'Published', value: 'published'},
          {title: 'Archived', value: 'archived'}
        ]
      },
      initialValue: 'draft'
    },
    {
      name: 'seo',
      type: 'object',
      title: 'SEO Settings',
      fields: [
        {name: 'metaTitle', type: 'string'},
        {name: 'metaDescription', type: 'string', validation: Rule => Rule.max(160)},
        {name: 'focusKeywords', type: 'array', of: [{type: 'string'}]}
      ]
    },
    {
      name: 'metrics',
      type: 'object',
      title: 'Article Metrics',
      fields: [
        {name: 'views', type: 'number', readOnly: true},
        {name: 'shares', type: 'number', readOnly: true},
        {name: 'readTime', type: 'number', title: 'Est. Read Time (minutes)'}
      ]
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
      title: 'headline',
      subtitle: 'category',
      media: 'featuredImage',
      status: 'status'
    },
    prepare({title, subtitle, media, status}) {
      return {
        title,
        subtitle: `${subtitle} • ${status}`,
        media
      }
    }
  }
}
```

### 7. Article Schema (SEO Content)

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

### 8. Page Template Schema (Publishing Guide)

```javascript
// schemas/pageTemplate.js
export default {
  name: 'pageTemplate',
  type: 'document',
  title: 'Page Template',
  fields: [
    {
      name: 'pageName',
      type: 'string',
      title: 'Page Name',
      validation: Rule => Rule.required()
    },
    {
      name: 'url',
      type: 'slug',
      title: 'URL Path',
      options: {
        source: 'pageName',
        maxLength: 200
      },
      validation: Rule => Rule.required()
    },
    {
      name: 'pageType',
      type: 'string',
      title: 'Page Type',
      options: {
        list: [
          {title: 'Landing Page', value: 'landing'},
          {title: 'Article', value: 'article'},
          {title: 'Profile', value: 'profile'},
          {title: 'Directory', value: 'directory'},
          {title: 'Search/Browse', value: 'search'},
          {title: 'Static', value: 'static'}
        ]
      }
    },
    {
      name: 'seoRequirements',
      type: 'object',
      title: 'SEO Requirements',
      fields: [
        {
          name: 'targetKeyword',
          type: 'string',
          title: 'Primary Target Keyword',
          validation: Rule => Rule.required()
        },
        {
          name: 'secondaryKeywords',
          type: 'array',
          title: 'Secondary Keywords',
          of: [{type: 'string'}]
        },
        {
          name: 'wordCountMin',
          type: 'number',
          title: 'Minimum Word Count',
          validation: Rule => Rule.min(300)
        },
        {
          name: 'wordCountMax',
          type: 'number',
          title: 'Maximum Word Count'
        },
        {
          name: 'internalLinksMin',
          type: 'number',
          title: 'Minimum Internal Links',
          initialValue: 5
        },
        {
          name: 'externalLinksMax',
          type: 'number',
          title: 'Maximum External Links',
          initialValue: 5
        }
      ]
    },
    {
      name: 'contentStructure',
      type: 'array',
      title: 'Required Content Sections',
      of: [{
        type: 'object',
        fields: [
          {name: 'sectionName', type: 'string'},
          {name: 'description', type: 'text'},
          {name: 'wordCount', type: 'number'}
        ]
      }]
    },
    {
      name: 'status',
      type: 'string',
      title: 'Implementation Status',
      options: {
        list: [
          {title: 'Planned', value: 'planned'},
          {title: 'In Development', value: 'in-development'},
          {title: 'Review', value: 'review'},
          {title: 'Published', value: 'published'},
          {title: 'Needs Update', value: 'needs-update'}
        ]
      },
      initialValue: 'planned'
    },
    {
      name: 'priority',
      type: 'string',
      title: 'Priority',
      options: {
        list: [
          {title: 'High', value: 'high'},
          {title: 'Medium', value: 'medium'},
          {title: 'Low', value: 'low'}
        ]
      }
    },
    {
      name: 'assignedTo',
      type: 'reference',
      to: [{type: 'user'}],
      title: 'Assigned To'
    },
    {
      name: 'notes',
      type: 'text',
      title: 'Implementation Notes'
    }
  ],
  preview: {
    select: {
      title: 'pageName',
      subtitle: 'url.current',
      status: 'status'
    },
    prepare({title, subtitle, status}) {
      const emoji = {
        'planned': '📋',
        'in-development': '🔨',
        'review': '👀',
        'published': '✅',
        'needs-update': '🔄'
      }
      return {
        title: `${emoji[status] || '📄'} ${title}`,
        subtitle
      }
    }
  }
}
```

### 9. Publishing Calendar Schema

```javascript
// schemas/publishingCalendar.js
export default {
  name: 'publishingCalendar',
  type: 'document',
  title: 'Publishing Calendar',
  fields: [
    {
      name: 'title',
      type: 'string',
      title: 'Content Title',
      validation: Rule => Rule.required()
    },
    {
      name: 'contentType',
      type: 'string',
      title: 'Content Type',
      options: {
        list: [
          {title: 'News Article', value: 'news'},
          {title: 'Blog Post', value: 'blog'},
          {title: 'Guide', value: 'guide'},
          {title: 'Profile', value: 'profile'},
          {title: 'Landing Page', value: 'landing'}
        ]
      }
    },
    {
      name: 'contentReference',
      type: 'reference',
      title: 'Content Item',
      to: [
        {type: 'newsArticle'},
        {type: 'article'},
        {type: 'investor'},
        {type: 'pageTemplate'}
      ]
    },
    {
      name: 'publishDate',
      type: 'datetime',
      title: 'Scheduled Publish Date',
      validation: Rule => Rule.required()
    },
    {
      name: 'author',
      type: 'reference',
      to: [{type: 'user'}, {type: 'journalist'}],
      title: 'Author/Creator'
    },
    {
      name: 'campaign',
      type: 'string',
      title: 'Marketing Campaign',
      options: {
        list: [
          {title: 'Organic Growth', value: 'organic'},
          {title: 'Product Launch', value: 'launch'},
          {title: 'Thought Leadership', value: 'thought-leadership'},
          {title: 'SEO Sprint', value: 'seo-sprint'},
          {title: 'User Education', value: 'education'}
        ]
      }
    },
    {
      name: 'targetAudience',
      type: 'string',
      title: 'Target Audience',
      options: {
        list: [
          {title: 'Founders', value: 'founders'},
          {title: 'Investors', value: 'investors'},
          {title: 'Professionals', value: 'professionals'},
          {title: 'Journalists', value: 'journalists'},
          {title: 'All Users', value: 'all'}
        ]
      }
    },
    {
      name: 'distribution',
      type: 'array',
      title: 'Distribution Channels',
      of: [{type: 'string'}],
      options: {
        list: [
          {title: 'Website', value: 'website'},
          {title: 'Newsletter', value: 'newsletter'},
          {title: 'Social Media', value: 'social'},
          {title: 'Partner Sites', value: 'partners'},
          {title: 'PR Outreach', value: 'pr'}
        ]
      }
    },
    {
      name: 'status',
      type: 'string',
      title: 'Status',
      options: {
        list: [
          {title: 'Idea', value: 'idea'},
          {title: 'Assigned', value: 'assigned'},
          {title: 'Writing', value: 'writing'},
          {title: 'Editing', value: 'editing'},
          {title: 'Scheduled', value: 'scheduled'},
          {title: 'Published', value: 'published'}
        ]
      },
      initialValue: 'idea'
    },
    {
      name: 'performance',
      type: 'object',
      title: 'Performance Metrics',
      fields: [
        {name: 'views', type: 'number', readOnly: true},
        {name: 'shares', type: 'number', readOnly: true},
        {name: 'conversions', type: 'number', readOnly: true},
        {name: 'avgTimeOnPage', type: 'number', readOnly: true}
      ]
    }
  ],
  preview: {
    select: {
      title: 'title',
      date: 'publishDate',
      status: 'status'
    },
    prepare({title, date, status}) {
      const dateStr = new Date(date).toLocaleDateString()
      return {
        title,
        subtitle: `${dateStr} • ${status}`
      }
    }
  }
}
```

### 10. SEO Guidelines Schema

```javascript
// schemas/seoGuideline.js
export default {
  name: 'seoGuideline',
  type: 'document',
  title: 'SEO Guideline',
  fields: [
    {
      name: 'contentType',
      type: 'string',
      title: 'Content Type',
      validation: Rule => Rule.required(),
      options: {
        list: [
          {title: 'Landing Page', value: 'landing'},
          {title: 'Article', value: 'article'},
          {title: 'Profile Page', value: 'profile'},
          {title: 'Directory Page', value: 'directory'},
          {title: 'News Article', value: 'news'}
        ]
      }
    },
    {
      name: 'guidelines',
      type: 'object',
      title: 'SEO Requirements',
      fields: [
        {
          name: 'titleFormat',
          type: 'string',
          title: 'Title Tag Format',
          description: 'Use {keyword} as placeholder'
        },
        {
          name: 'titleLength',
          type: 'object',
          fields: [
            {name: 'min', type: 'number', initialValue: 30},
            {name: 'max', type: 'number', initialValue: 60}
          ]
        },
        {
          name: 'metaDescriptionLength',
          type: 'object',
          fields: [
            {name: 'min', type: 'number', initialValue: 120},
            {name: 'max', type: 'number', initialValue: 160}
          ]
        },
        {
          name: 'wordCount',
          type: 'object',
          fields: [
            {name: 'min', type: 'number'},
            {name: 'ideal', type: 'number'},
            {name: 'max', type: 'number'}
          ]
        },
        {
          name: 'internalLinks',
          type: 'object',
          fields: [
            {name: 'min', type: 'number'},
            {name: 'ideal', type: 'number'}
          ]
        },
        {
          name: 'headingStructure',
          type: 'array',
          of: [{
            type: 'object',
            fields: [
              {name: 'level', type: 'string'},
              {name: 'purpose', type: 'string'},
              {name: 'includeKeyword', type: 'boolean'}
            ]
          }]
        }
      ]
    },
    {
      name: 'schemaMarkup',
      type: 'array',
      title: 'Required Schema Markup',
      of: [{type: 'string'}],
      options: {
        list: [
          {title: 'Article', value: 'article'},
          {title: 'Organization', value: 'organization'},
          {title: 'Person', value: 'person'},
          {title: 'JobPosting', value: 'jobPosting'},
          {title: 'BreadcrumbList', value: 'breadcrumb'},
          {title: 'FAQ', value: 'faq'}
        ]
      }
    },
    {
      name: 'examples',
      type: 'array',
      title: 'Good Examples',
      of: [{
        type: 'object',
        fields: [
          {name: 'url', type: 'url'},
          {name: 'description', type: 'text'}
        ]
      }]
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
        .title('News & Content')
        .icon(() => '📰')
        .child(
          S.list()
            .title('Content Management')
            .items([
              S.listItem()
                .title('News Articles')
                .child(
                  S.list()
                    .title('News')
                    .items([
                      S.listItem()
                        .title('Draft News')
                        .child(
                          S.documentList()
                            .title('Drafts')
                            .filter('_type == "newsArticle" && status == "draft"')
                        ),
                      S.listItem()
                        .title('News in Review')
                        .child(
                          S.documentList()
                            .title('Pending Review')
                            .filter('_type == "newsArticle" && status == "review"')
                        ),
                      S.listItem()
                        .title('Published News')
                        .child(
                          S.documentList()
                            .title('Live Articles')
                            .filter('_type == "newsArticle" && status == "published"')
                            .defaultOrdering([{field: 'publishedAt', direction: 'desc'}])
                        ),
                      S.listItem()
                        .title('All News')
                        .child(S.documentTypeList('newsArticle'))
                    ])
                ),
              S.listItem()
                .title('SEO Articles')
                .child(S.documentTypeList('article'))
            ])
        ),
      
      S.divider(),
      
      // Publishing Management
      S.listItem()
        .title('Publishing Management')
        .icon(() => '📝')
        .child(
          S.list()
            .title('Publishing Tools')
            .items([
              S.listItem()
                .title('Page Templates')
                .child(
                  S.list()
                    .title('Page Status')
                    .items([
                      S.listItem()
                        .title('⏳ Planned Pages')
                        .child(
                          S.documentList()
                            .title('Planned')
                            .filter('_type == "pageTemplate" && status == "planned"')
                            .defaultOrdering([{field: 'priority', direction: 'desc'}])
                        ),
                      S.listItem()
                        .title('🔨 In Development')
                        .child(
                          S.documentList()
                            .title('Being Built')
                            .filter('_type == "pageTemplate" && status == "in-development"')
                        ),
                      S.listItem()
                        .title('✅ Published Pages')
                        .child(
                          S.documentList()
                            .title('Live')
                            .filter('_type == "pageTemplate" && status == "published"')
                        ),
                      S.listItem()
                        .title('All Page Templates')
                        .child(S.documentTypeList('pageTemplate'))
                    ])
                ),
              S.listItem()
                .title('Publishing Calendar')
                .child(
                  S.list()
                    .title('Calendar Views')
                    .items([
                      S.listItem()
                        .title('📅 This Week')
                        .child(
                          S.documentList()
                            .title('Publishing This Week')
                            .filter('_type == "publishingCalendar" && publishDate > now() - 60*60*24*7 && publishDate < now() + 60*60*24*7')
                            .defaultOrdering([{field: 'publishDate', direction: 'asc'}])
                        ),
                      S.listItem()
                        .title('📆 This Month')
                        .child(
                          S.documentList()
                            .title('Publishing This Month')
                            .filter('_type == "publishingCalendar" && publishDate > now() - 60*60*24*30 && publishDate < now() + 60*60*24*30')
                            .defaultOrdering([{field: 'publishDate', direction: 'asc'}])
                        ),
                      S.listItem()
                        .title('All Calendar Items')
                        .child(S.documentTypeList('publishingCalendar'))
                    ])
                ),
              S.listItem()
                .title('SEO Guidelines')
                .child(S.documentTypeList('seoGuideline'))
            ])
        ),
      
      S.divider(),
      
      // All Document Types
      ...S.documentTypeListItems().filter(listItem => 
        !['investor', 'job', 'journalist', 'organization', 'article', 'newsArticle', 'pageTemplate', 'publishingCalendar', 'seoGuideline'].includes(listItem.getId())
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