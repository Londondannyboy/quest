# V3 Sanity Testing Guide

*Last Updated: December 2024*

## Quick Start Testing

### 1. Create a Free Sanity Project

```bash
# Install Sanity CLI globally
npm install -g @sanity/cli

# Create new project (in a test directory first!)
mkdir quest-sanity-test && cd quest-sanity-test
sanity init

# Choose:
# - Create new project
# - Public dataset name: "development"
# - Use default dataset configuration
# - Template: Clean project with no predefined schemas
```

### 2. Add Test Schemas

Copy the schemas from `V3_SANITY_SCHEMA.md` into your `schemas/` directory:

```bash
# Essential schemas to test
- user.js
- investor.js
- newsArticle.js
- pageTemplate.js
- publishingCalendar.js
```

### 3. Start Sanity Studio

```bash
# In your test directory
npm run dev

# Opens at http://localhost:3333
# You can now create test content!
```

## Testing Workflows

### Test 1: Content Creation Flow
1. Create a test investor profile
2. Set verified = false
3. Check it appears in "Review Queues"
4. Set verified = true
5. Confirm it moves to "Verified Content"

### Test 2: Publishing Calendar
1. Create a page template for "Founders Landing"
2. Set SEO requirements (1500 words, 15 internal links)
3. Create a publishing calendar item
4. Link it to your page template
5. Set publish date for next week

### Test 3: News Article with Voice
1. Create a news article
2. Add related investors/organizations
3. Preview how voice UI would interact
4. Test the excerpt for voice summaries

## Key Things to Validate

### Schema Design
- [ ] Field types work as expected
- [ ] Validation rules are appropriate
- [ ] References connect properly
- [ ] Preview formatting looks good

### Workflow Testing
- [ ] Review queues filter correctly
- [ ] Status transitions work
- [ ] Publishing calendar date filters work
- [ ] Content relationships display properly

### SEO Features
- [ ] Character counters work
- [ ] SEO guidelines are helpful
- [ ] Schema markup fields sufficient

## Multi-Dataset Testing

### Create Test Datasets

```bash
# Create datasets for different environments
sanity dataset create staging
sanity dataset create content-team

# Switch between datasets
sanity dataset list
```

### Test Data Migration

```bash
# Export from development
sanity dataset export development backup.tar.gz

# Import to staging
sanity dataset import backup.tar.gz staging --replace

# Now test changes in staging without affecting development
```

## Integration Testing

### Test with Next.js

```javascript
// lib/sanity.js
import { createClient } from '@sanity/client'

export const sanityClient = createClient({
  projectId: 'your-project-id',
  dataset: process.env.SANITY_DATASET || 'development',
  apiVersion: '2024-01-01',
  useCdn: false
})

// Test query
const testQuery = async () => {
  const investors = await sanityClient.fetch(
    `*[_type == "investor" && verified == true] | order(_createdAt desc)[0...10]`
  )
  console.log(investors)
}
```

### Test Real-Time Preview

```javascript
// Enable preview mode
export const previewClient = createClient({
  ...clientConfig,
  useCdn: false,
  token: process.env.SANITY_READ_TOKEN,
  withCredentials: true
})
```

## Performance Testing

### Query Performance

```groq
// Test complex queries
*[_type == "newsArticle" && status == "published"] {
  ...,
  "relatedInvestors": relatedEntities.investors[]-> {
    name,
    firm,
    categories
  },
  "author": source.author-> {
    name,
    email
  }
} | order(publishedAt desc)[0...20]
```

### Measure Response Times
- Simple queries: <100ms
- Complex joins: <300ms
- Full page data: <500ms

## Content Team Testing

### Create Test Users
1. Content Editor role
2. Reviewer role
3. Admin role

### Test Permissions
- Editors can create drafts
- Reviewers can approve/reject
- Only admins can delete

### Test Collaborative Features
- Real-time collaboration
- Presence indicators
- Change history

## Common Issues & Solutions

### Issue: Schema Changes Not Showing
```bash
# Restart the development server
ctrl+c
npm run dev
```

### Issue: Reference Fields Empty
- Ensure referenced document type exists
- Check `to: [{type: 'documentType'}]` array

### Issue: Validation Too Strict
- Adjust validation rules
- Use `.warning()` instead of `.error()`

### Issue: Query Returns Empty
- Check dataset name
- Verify document `_type` matches
- Use Vision plugin to test queries

## Sanity Studio Customization

### Add Desk Structure
```javascript
// sanity.config.js
import {deskStructure} from './deskStructure'

export default defineConfig({
  // ... other config
  plugins: [
    deskTool({
      structure: deskStructure
    })
  ]
})
```

### Test Custom Views
- Review queues working
- Publishing calendar filtering
- Status-based grouping

## Production Readiness Checklist

Before moving to production:

- [ ] All schemas finalized and tested
- [ ] Validation rules appropriate
- [ ] Desk structure intuitive
- [ ] Query performance acceptable
- [ ] Backup/restore process tested
- [ ] Team permissions configured
- [ ] Webhook endpoints ready
- [ ] CDN/caching strategy defined

## Next Steps

1. **Local Testing**: Complete all test scenarios above
2. **Team Testing**: Invite 1-2 team members to test
3. **Content Seeding**: Create initial high-quality content
4. **Integration**: Connect to Next.js frontend
5. **Launch**: Deploy with production dataset

---

*Remember: Sanity's free tier is generous (100K API requests/month, 3 users, 500K CDN requests). Perfect for testing and small teams!*