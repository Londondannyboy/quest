# Article Worker

Temporal Python worker for autonomous article generation and publication.

## Overview

The Article Worker is a separate service that handles article creation workflows for the Quest platform. It researches topics, generates comprehensive articles, creates contextual images, and publishes them to the database with company relationships.

## Architecture

- **Service Type**: Temporal Python worker (independent from company-worker)
- **Task Queue**: `quest-article-queue`
- **Deployment**: Separate Railway service
- **Database**: Shared Neon PostgreSQL with company-worker

## Workflow: ArticleCreationWorkflow

### Timeline: 5-12 minutes total

### Phases:

1. **Normalize Topic & Check** (5s)
   - Clean and normalize topic
   - Generate URL-friendly slug
   - Check for duplicate articles

2. **Parallel Research** (60s)
   - `fetch_topic_news()` - Serper.dev news search (2 queries)
   - `exa_research_topic()` - Deep AI research via Exa
   - `crawl_news_sources()` - Crawl news article URLs
   - `crawl_authoritative_sites()` - Crawl authoritative websites

3. **Zep Context Query** (5s)
   - Query Zep knowledge graph for related companies and articles

4. **URL Validation** (30s)
   - Validate all source URLs with Playwright
   - Remove 404s and paywalls

5. **Generate Article Content** (60-120s)
   - Use Gemini 2.5 Flash + Claude Sonnet 4.5
   - Generate title, subtitle, markdown content
   - Create H2 sections with narrative structure
   - Extract company mentions
   - Generate tags and meta description

6. **Analyze Sections** (10s)
   - Sentiment analysis per section
   - Identify narrative arc
   - Recommend image moments

7. **Clean Generated Links** (30s)
   - Remove broken URLs from content

8. **Generate Contextual Images** (5-10min)
   - Featured image (1200x630) - Social sharing
   - Hero image (16:9) - Article header
   - Content images 1-5 (4:3/1:1) - Section images
   - Uses Flux Kontext Max for sequential generation

9. **Extract & Link Companies** (10s)
   - NER-based company extraction
   - Match to database companies
   - Calculate relevance scores

10. **Save to Database** (5s)
    - Insert into `articles` table
    - Create `article_companies` relationships

11. **Sync to Zep** (5s)
    - Add to knowledge graph with company relationships

## Input

```python
ArticleInput(
    topic="The rise of AI in recruitment",
    app="placement",  # placement, relocation, etc.
    target_word_count=1500,
    article_format="article",  # article, listicle, guide, analysis
    jurisdiction="UK",  # Optional geo-targeting
    num_research_sources=10,
    deep_crawl_enabled=True,
    generate_images=True,
    auto_publish=False,
    target_keywords=["AI", "recruitment"],
    author="Quest Editorial Team"
)
```

## Output

```python
{
    "status": "created",
    "article_id": "uuid",
    "slug": "rise-of-ai-recruitment",
    "title": "The Rise of AI in Recruitment...",
    "word_count": 2150,
    "section_count": 5,
    "featured_image_url": "...",
    "hero_image_url": "...",
    "research_cost": 0.25,
    "completeness_score": 92.5,
    "company_mentions": 3,
    "publication_status": "draft",
    "zep_graph_id": "episode_123"
}
```

## Database Schema

### Articles Table

- `id` - UUID primary key
- `slug` - Unique URL slug
- `title` - Article title
- `subtitle` - Optional subtitle
- `content` - Markdown content
- `excerpt` - Short summary
- `word_count` - Word count
- `app` - App context
- `article_format` - Format type
- `article_angle` - Editorial angle
- `primary_category` - Category
- `meta_description` - SEO description
- `tags` - JSONB array
- `status` - draft/published/archived
- `published_at` - Publication timestamp
- `author` - Author name
- **Images**: featured, hero, content_1-5 (with alt, description, title)
- **Sections**: JSONB array with sentiment analysis
- `payload` - JSONB with full ArticlePayload
- `created_at`, `updated_at`

### Article_Companies Junction Table

- `article_id` - Foreign key to articles
- `company_id` - Foreign key to companies
- `relevance_score` - 0-1 relevance
- `created_at`, `updated_at`

## Environment Variables

See `.env.example` for full list. Required:

- `DATABASE_URL` - Neon PostgreSQL
- `TEMPORAL_*` - Temporal Cloud config
- `SERPER_API_KEY` - News search
- `EXA_API_KEY` - Deep research
- `REPLICATE_API_TOKEN` - Image generation
- `ZEP_API_KEY` - Knowledge graph
- AI keys (Google, OpenAI, or Anthropic)

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Copy environment template
cp .env.example .env
# Edit .env with your keys

# Run worker
python worker.py
```

## Deployment (Railway)

1. Create new Railway service: `article-worker`
2. Link to this directory
3. Set environment variables in Railway dashboard
4. Railway will auto-deploy using `railway.json` config

## Cost Estimates

Per article (1500 words):
- Serper news search: $0.04 (2 queries)
- Exa research: $0.04
- Firecrawl (if used): $0.02
- Content generation (Gemini + Claude): $0.05
- Image generation (7 images, Flux Kontext Max): $0.10
- **Total**: ~$0.25 per article

## Activity Status

### ✅ Implemented
- `normalize_article_topic`
- `check_article_exists`
- `fetch_topic_news`
- `exa_research_topic`
- `crawl_news_sources`
- `save_article_to_neon`
- `link_companies_to_article`
- `calculate_article_completeness`

### 🚧 Stub (To Implement)
- `crawl_authoritative_sites`
- `query_zep_for_article_context`
- `generate_article_content` (needs AI implementation)
- `analyze_article_sections` (needs AI implementation)
- `generate_article_contextual_images` (needs Flux integration)
- `extract_company_mentions` (needs NER implementation)
- `playwright_url_cleanse` (needs Playwright)
- `playwright_clean_article_links` (needs Playwright)
- `sync_article_to_zep` (needs Zep integration)

## Next Steps

1. Implement AI content generation with Gemini 2.5 + Claude
2. Integrate Flux Kontext Max for sequential images
3. Add NER for company extraction
4. Implement Playwright URL validation
5. Add Zep knowledge graph integration
6. Test end-to-end article generation
7. Deploy to Railway as separate service
8. Wire up gateway endpoint

## Differences from CompanyCreationWorkflow

✅ **Kept**: Parallel research, URL validation, Zep sync, image generation patterns
❌ **Removed**: Logo extraction, hero stats, company fields, graph visualization
🔄 **Changed**: Input (URL→topic), crawling (site→sources), output (companies→articles)
➕ **Added**: Section sentiment, company NER, multi-image generation, article_companies linking
