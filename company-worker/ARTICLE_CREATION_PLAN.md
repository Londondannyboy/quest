# Unified Article Creation in Company-Worker

**Status**: In Progress
**Last Updated**: 2025-11-19

---

## Overview

Extend company-worker to create articles alongside companies, triggered from Streamlit.
Single unified content service reusing ALL existing research activities.

---

## Key Strategy: Research → Deep Crawl → Generate → Images

1. **Research the topic**: Serper news + Exa deep research
2. **Crawl discovered URLs**: Crawl4AI + Firecrawl to get FULL content (avoid paywalls)
3. **Generate article**: Gemini 2.5 Flash with rich crawled content
4. **Sequential images**: Kontext Pro for 3-5 contextual images

---

## What Already Exists ✅

### Research Activities
- `fetch_company_news` - Works for any topic/search query
- `exa_research_company` - Deep AI research on any topic
- `serper_httpx_deep_articles` - Deep crawl news URLs

### Crawling Activities
- `crawl4ai_service_crawl` - External service for JavaScript-heavy sites
- `firecrawl_httpx_discover` - Intelligent URL discovery + scraping
- `httpx_crawl` - Fast HTTP scraping

### Image Generation (ALREADY FOR ARTICLES!)
- `analyze_article_sections` - Extracts H2 sections, analyzes sentiment
- `generate_sequential_article_images` - 3-5 contextual images with Kontext Pro

### Validation & Storage
- `playwright_url_cleanse` - URL validation
- `query_zep_for_context` - Query knowledge graph
- Zep sync activities - Works for articles too

---

## What's Needed 🔨

### 1. Models (`src/models/article.py`)

```python
class ArticlePayload(BaseModel):
    # Core
    title: str
    subtitle: Optional[str]
    slug: str
    content: str  # Markdown with H2 sections
    excerpt: str

    # Classification
    app: str  # placement, relocation, etc.
    article_type: str  # news, guide, comparison

    # SEO
    meta_description: str
    tags: List[str]

    # Images (7 total)
    featured_image_url: Optional[str]
    hero_image_url: Optional[str]
    content_image1_url: Optional[str]
    content_image2_url: Optional[str]
    content_image3_url: Optional[str]
    content_image4_url: Optional[str]
    content_image5_url: Optional[str]

    # Company relationships
    mentioned_companies: List[CompanyMention]

    # Metrics
    word_count: int
    reading_time_minutes: int
    research_cost: float
```

### 2. Generation Activity (`src/activities/generation/article_generation.py`)

Copy pattern from `profile_generation_v2.py`:
- Use pydantic-ai Agent with Gemini 2.5 Flash
- System prompt for article types:
  - **News**: "Goldman Sachs acquiring startup X"
  - **Guide**: "Digital Nomad Visa in Greece"
  - **Comparison**: "Top 10 Placement Agents in UK"
- Generate H2 sections, extract company mentions
- Return ArticlePayload

### 3. Workflow (`src/workflows/article_creation.py`)

```python
class ArticleCreationWorkflow:
    """
    Phases:
    1. Research topic (Serper + Exa)
    2. Crawl discovered URLs (ALL sources)
    3. Generate article content
    4. Analyze sections + generate images
    5. Save to database
    6. Sync to Zep
    """
```

### 4. Database

Add to Neon (if not exists):
- `articles` table
- `article_companies` junction table

### 5. Streamlit UI (`dashboard.py`)

**Article Creation Tab**:
```python
st.header("Create Article")
topic = st.text_input("Topic", "Goldman Sachs acquiring startup X")
article_type = st.selectbox("Type", ["news", "guide", "comparison"])
app = st.selectbox("App", ["placement", "relocation"])
word_count = st.slider("Target Word Count", 500, 3000, 1500)
if st.button("Generate Article"):
    # Call gateway API
```

**Article Display Tab**:
- List all articles (table with images)
- Article detail view (rendered markdown + images)

---

## Implementation Steps

### Phase 1: Core Article Generation (1 day)

- [x] Remove article-worker
- [ ] Create ArticlePayload model
- [ ] Create article_generation activity
- [ ] Test generation locally

### Phase 2: Workflow (1 day)

- [ ] Create ArticleCreationWorkflow
- [ ] Wire up research activities
- [ ] Wire up crawling activities
- [ ] Wire up image generation
- [ ] Test end-to-end

### Phase 3: Streamlit UI (1 day)

- [ ] Add article creation form
- [ ] Add article list view
- [ ] Add article detail view
- [ ] Test from UI

### Phase 4: Polish (1 day)

- [ ] Add article templates for different types
- [ ] Test with real topics
- [ ] Deploy to Railway
- [ ] Update gateway endpoint

---

## Article Templates

### News Article Template
```
Topic: "Goldman Sachs acquiring startup X"
Research: Recent news about both companies
Structure:
  - Background on Goldman Sachs
  - Background on startup
  - Deal details (value, terms, date)
  - Market implications
  - Expert commentary
Imagery: Professional/optimistic (handshakes, celebrations)
```

### Country Guide Template
```
Topic: "Digital Nomad Visa Greece"
Research: Visa requirements, costs, lifestyle
Structure:
  - Overview of Greece DN visa
  - Eligibility requirements
  - Application process
  - Costs and benefits
  - Lifestyle and practical tips
Imagery: Optimistic (beaches, work-life balance, Greek scenery)
```

### Comparison Template
```
Topic: "Top 10 Placement Agents in UK"
Research: Companies in category + jurisdiction
Structure:
  - Introduction to placement agents
  - Methodology
  - Top 10 list (with details for each)
  - Comparison criteria
  - How to choose
Imagery: Analytical (charts, professional settings, comparisons)
```

---

## Cost Estimates

Per article (1500 words):
- Serper news search: $0.04
- Exa deep research: $0.04
- Crawl4AI (5 URLs): $0.00 (free via service)
- Firecrawl (if used): $0.02
- Content generation (Gemini): $0.015
- Images (5 images, Kontext Pro): $0.10
- **Total**: ~$0.20 per article

At 100 articles/day: $20/day = $600/month

---

## Technical Details

### Research Strategy for Articles

Instead of company domain, search by **topic**:
```python
# For news articles
serper_query = f"{topic} news {jurisdiction}"

# For guides
serper_query = f"{topic} guide requirements {jurisdiction}"

# For comparisons
serper_query = f"{topic} comparison {jurisdiction}"
```

### Crawling Strategy

**Key difference from companies**: Crawl ALL discovered URLs!
- Serper returns 10-20 news URLs → crawl ALL with Crawl4AI
- Exa returns 5-10 research URLs → crawl ALL
- This ensures rich content without paywalled snippets

### Image Generation

**Already perfect for articles!**
- `analyze_article_sections`: Extracts H2s, analyzes sentiment
- `generate_sequential_article_images`: 3-5 contextual images
- Semi-cartoon illustration style
- Sentiment-aware (somber for layoffs, celebratory for deals)

---

## Next Steps

1. Create ArticlePayload model (30 min)
2. Create article_generation activity (1 hour)
3. Create ArticleCreationWorkflow (2 hours)
4. Add Streamlit article form (1 hour)
5. Test end-to-end with real topic (1 hour)

**Total**: 1 day for MVP

---

## Success Criteria

- [ ] Can create news article from Streamlit
- [ ] Article includes 3-5 sequential images
- [ ] Company mentions are extracted and linked
- [ ] Article saved to database
- [ ] Article synced to Zep knowledge graph
- [ ] Article displays nicely in Streamlit

---

**Ready to implement!**
