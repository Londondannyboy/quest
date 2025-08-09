// Sanity Schema for SEO-Optimized Pages
// This schema supports both news/home pages and location-specific placement agent pages

export const seoPage = {
  name: 'seoPage',
  title: 'SEO Page',
  type: 'document',
  fields: [
    {
      name: 'pageType',
      title: 'Page Type',
      type: 'string',
      options: {
        list: [
          { title: 'Home/News Page', value: 'home' },
          { title: 'Placement Agent Page', value: 'placement-agent' }
        ]
      },
      validation: (Rule: any) => Rule.required()
    },
    {
      name: 'title',
      title: 'Page Title',
      type: 'string',
      description: 'SEO-optimized title containing the target keyword',
      validation: (Rule: any) => Rule.required().max(60)
    },
    {
      name: 'slug',
      title: 'Slug',
      type: 'slug',
      options: {
        source: 'title',
        maxLength: 96
      },
      validation: (Rule: any) => Rule.required()
    },
    {
      name: 'keyword',
      title: 'Target Keyword',
      type: 'string',
      description: 'Primary keyword for SEO optimization (e.g., "private equity placement agents London")',
      validation: (Rule: any) => Rule.required()
    },
    {
      name: 'location',
      title: 'Location',
      type: 'string',
      description: 'Location for placement agent pages (e.g., London, UK, France, Germany)',
      hidden: ({ document }: any) => document?.pageType !== 'placement-agent'
    },
    {
      name: 'metaDescription',
      title: 'Meta Description',
      type: 'text',
      rows: 3,
      description: 'SEO meta description (150-160 characters)',
      validation: (Rule: any) => Rule.required().max(160)
    },
    {
      name: 'h1',
      title: 'H1 Heading',
      type: 'string',
      description: 'Main heading - must contain the keyword',
      validation: (Rule: any) => Rule.required()
    },
    {
      name: 'heroImage',
      title: 'Hero Image',
      type: 'image',
      options: {
        hotspot: true
      },
      fields: [
        {
          name: 'alt',
          title: 'Alt Text',
          type: 'string',
          description: 'Alt text must contain the keyword',
          validation: (Rule: any) => Rule.required()
        }
      ]
    },
    {
      name: 'introduction',
      title: 'Introduction Section',
      type: 'object',
      fields: [
        {
          name: 'h2',
          title: 'H2 Heading',
          type: 'string',
          description: 'Section heading - should contain the keyword'
        },
        {
          name: 'content',
          title: 'Content',
          type: 'array',
          of: [
            {
              type: 'block',
              styles: [
                { title: 'Normal', value: 'normal' },
                { title: 'H3', value: 'h3' },
                { title: 'H4', value: 'h4' }
              ],
              marks: {
                decorators: [
                  { title: 'Strong', value: 'strong' },
                  { title: 'Emphasis', value: 'em' }
                ]
              }
            }
          ]
        }
      ]
    },
    {
      name: 'mainContent',
      title: 'Main Content Sections',
      type: 'array',
      of: [
        {
          type: 'object',
          name: 'contentSection',
          fields: [
            {
              name: 'h2',
              title: 'H2 Heading',
              type: 'string',
              validation: (Rule: any) => Rule.required()
            },
            {
              name: 'content',
              title: 'Content',
              type: 'array',
              of: [
                {
                  type: 'block',
                  styles: [
                    { title: 'Normal', value: 'normal' },
                    { title: 'H3', value: 'h3' },
                    { title: 'H4', value: 'h4' }
                  ],
                  marks: {
                    decorators: [
                      { title: 'Strong', value: 'strong' },
                      { title: 'Emphasis', value: 'em' }
                    ],
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
                  }
                }
              ]
            },
            {
              name: 'image',
              title: 'Section Image',
              type: 'image',
              options: {
                hotspot: true
              },
              fields: [
                {
                  name: 'alt',
                  title: 'Alt Text',
                  type: 'string',
                  description: 'Alt text must contain the keyword'
                }
              ]
            }
          ]
        }
      ]
    },
    {
      name: 'news',
      title: 'News Items',
      type: 'array',
      hidden: ({ document }: any) => document?.pageType !== 'home',
      of: [
        {
          type: 'object',
          name: 'newsItem',
          fields: [
            {
              name: 'title',
              title: 'News Title',
              type: 'string',
              validation: (Rule: any) => Rule.required()
            },
            {
              name: 'date',
              title: 'Date',
              type: 'datetime',
              validation: (Rule: any) => Rule.required()
            },
            {
              name: 'summary',
              title: 'Summary',
              type: 'text',
              rows: 3
            },
            {
              name: 'link',
              title: 'Read More Link',
              type: 'reference',
              to: [{ type: 'seoPage' }]
            }
          ]
        }
      ]
    },
    {
      name: 'internalLinks',
      title: 'Related Pages (Internal Links)',
      type: 'array',
      of: [
        {
          type: 'reference',
          to: [{ type: 'seoPage' }]
        }
      ],
      description: 'Links to other SEO pages for internal linking'
    },
    {
      name: 'seoScore',
      title: 'SEO Score',
      type: 'object',
      fields: [
        {
          name: 'keywordCount',
          title: 'Keyword Count',
          type: 'number',
          description: 'Number of times the keyword appears in the content'
        },
        {
          name: 'hasKeywordInH1',
          title: 'Keyword in H1',
          type: 'boolean'
        },
        {
          name: 'hasKeywordInH2',
          title: 'Keyword in H2',
          type: 'boolean'
        },
        {
          name: 'hasBoldKeyword',
          title: 'Bold Keyword',
          type: 'boolean'
        },
        {
          name: 'hasKeywordInImages',
          title: 'Keyword in Image Alt Text',
          type: 'boolean'
        }
      ]
    }
  ],
  preview: {
    select: {
      title: 'title',
      pageType: 'pageType',
      location: 'location'
    },
    prepare({ title, pageType, location }: any) {
      return {
        title,
        subtitle: pageType === 'home' ? 'Home/News Page' : `Placement Agents - ${location}`
      }
    }
  }
}

// Export schema
export default [seoPage]