# Internal Linking System for SEO Pages

## Overview

The internal linking system is crucial for SEO success. It helps search engines understand the relationship between pages and distributes link equity throughout your site. Our implementation includes both automatic and manual internal linking capabilities.

## Schema Implementation

### 1. Direct Page References
The schema includes an `internalLinks` field that stores direct references to other SEO pages:

```javascript
{
  name: 'internalLinks',
  title: 'Related Pages (Internal Links)',
  type: 'array',
  of: [
    {
      type: 'reference',
      to: [{ type: 'seoPage' }]
    }
  ]
}
```

### 2. Inline Content Links
Within rich text content blocks, we support inline internal links through annotations:

```javascript
annotations: [
  {
    name: 'internalLink',
    type: 'object',
    title: 'Internal Link',
    fields: [
      {
        name: 'reference',
        type: 'reference',
        to: [{ type: 'seoPage' }]
      }
    ]
  }
]
```

## Implementation Strategy

### Automatic Linking Structure

```
Home Page (News)
    ├── Links to all 10 placement agent pages
    │
    └── Each Placement Agent Page
        ├── Links to Home
        ├── Links to other 9 placement agent pages
        └── Contextual links within content
```

### Best Practices for Internal Linking

1. **Link Density**: Include 3-5 internal links per 500 words of content
2. **Anchor Text**: Use keyword-rich anchor text that describes the destination page
3. **Link Placement**: Place important links higher in the content hierarchy
4. **Relevance**: Only link to contextually relevant pages

## Frontend Implementation

### Rendering Internal Links in React/Next.js

```jsx
// Component for rendering portable text with internal links
import { PortableText } from '@portabletext/react'
import Link from 'next/link'

const components = {
  marks: {
    internalLink: ({ children, value }) => {
      const { reference } = value
      const href = `/${reference.slug.current}`
      
      return (
        <Link href={href}>
          <a className="text-blue-600 hover:underline">{children}</a>
        </Link>
      )
    }
  }
}

// Render related pages section
const RelatedPages = ({ internalLinks }) => (
  <section className="related-pages">
    <h3>Related Pages</h3>
    <ul>
      {internalLinks?.map((link) => (
        <li key={link._ref}>
          <Link href={`/${link.slug.current}`}>
            <a>{link.title}</a>
          </Link>
        </li>
      ))}
    </ul>
  </section>
)
```

## SEO Benefits

1. **PageRank Distribution**: Internal links pass PageRank between pages
2. **Crawl Efficiency**: Helps search engines discover all pages
3. **User Experience**: Improves navigation and reduces bounce rate
4. **Topical Authority**: Creates topic clusters around placement agents

## Monitoring Internal Links

### GROQ Query for Link Analysis

```groq
// Find all pages and their internal links
*[_type == "seoPage"] {
  title,
  "url": slug.current,
  "outgoingLinks": count(internalLinks),
  "incomingLinks": count(*[_type == "seoPage" && references(^._id)])
}

// Find orphaned pages (no incoming links)
*[_type == "seoPage" && count(*[_type == "seoPage" && references(^._id)]) == 0] {
  title,
  slug
}
```

## Maintenance Tips

1. **Regular Audits**: Check for broken internal links monthly
2. **Link Distribution**: Ensure all pages have at least 3 incoming links
3. **Update Strategy**: When adding new pages, update existing pages to link to them
4. **Avoid Over-Optimization**: Keep linking natural and user-focused

## Example Link Structure

```
private-equity-news (Home)
  → private-equity-placement-agents-london
  → private-equity-placement-agents-paris
  → private-equity-placement-agents-frankfurt
  → (... all 10 locations)

private-equity-placement-agents-london
  → private-equity-news (Home)
  → private-equity-placement-agents-paris (nearby market)
  → private-equity-placement-agents-frankfurt (nearby market)
  → private-equity-placement-agents-new-york (major market)
  → (... other relevant locations)
```

This creates a robust internal linking structure that supports both SEO goals and user navigation.