# Narrative-First Company Profile Model

## Problem with Current Approach

**Current: 60+ Structured Fields**
```python
{
  "legal_name": "Thrive Alternative Investments",
  "tagline": null,           # ❌ NULL
  "description": null,        # ❌ NULL
  "headquarters": null,       # ❌ NULL
  "founded_year": null,       # ❌ NULL
  "employees": null,          # ❌ NULL
  "executives": [],           # ❌ Empty
  "services": [],             # ❌ Empty
  # ... 50+ more fields, mostly NULL
  "data_completeness_score": 29.4%  # ❌ Low score
}
```

**Issues:**
- Forces structure where data doesn't exist
- Low completeness scores (lots of NULLs)
- Rigid extraction when content is dynamic
- Frontend has to handle all the NULL fields

## New Approach: Narrative-First

**Store:**
1. **Essential structured data** (for search/filtering)
2. **Dynamic narrative sections** (only exist if data supports them)

```python
{
  # ===== ESSENTIAL STRUCTURED (always present) =====
  "legal_name": "Thrive Alternative Investments",
  "website": "https://www.thrivealts.com",
  "domain": "thrivealts.com",
  "slug": "thrivealts",
  "company_type": "placement_agent",
  "industry": "Financial Services",

  # Optional structured (only if available)
  "headquarters_city": "New York",
  "headquarters_country": "United States",
  "founded_year": 2015,
  "employee_range": "10-50",

  # ===== NARRATIVE CONTENT (flexible sections) =====
  "profile_sections": {
    "overview": {
      "title": "Overview",
      "content": "Thrive Alternative Investments is a specialized placement agent...",
      "confidence": 0.9
    },
    "services": {
      "title": "Services",
      "content": "Thrive provides capital raising services for...",
      "confidence": 0.8
    },
    "team": {
      "title": "Team",
      "content": "Led by industry veterans with decades of experience...",
      "confidence": 0.6
    }
    # Only sections where we have data!
  },

  # ===== METADATA =====
  "research_date": "2025-11-17T...",
  "confidence_score": 0.85,
  "data_sources": {...}
}
```

## Benefits

1. **No NULL Fields on Display** - Sections only exist if data supports them
2. **Higher Completeness** - We show everything we have naturally
3. **Flexible & Natural** - AI writes naturally, not forced extraction
4. **Better User Experience** - Rich, readable profiles
5. **Easier Frontend** - No NULL handling, just render what exists

## Implementation

### 1. New Payload Model

```python
class ProfileSection(BaseModel):
    """A narrative section of the company profile"""
    title: str
    content: str  # Markdown or HTML
    confidence: float = 1.0
    sources: list[str] = []

class CompanyPayload(BaseModel):
    """Simplified, flexible company profile"""

    # ===== ESSENTIAL (Always present) =====
    legal_name: str
    website: str
    domain: str
    slug: str
    company_type: str  # placement_agent, relocation, etc.

    # ===== OPTIONAL STRUCTURED (Only if available) =====
    industry: str | None = None
    headquarters_city: str | None = None
    headquarters_country: str | None = None
    founded_year: int | None = None
    employee_range: str | None = None  # "10-50", "100-500", etc.

    # ===== NARRATIVE SECTIONS (Dynamic) =====
    profile_sections: dict[str, ProfileSection] = {}
    # Possible sections: overview, services, team, deals,
    # locations, clients, technology, news, awards, etc.

    # ===== METADATA =====
    research_date: str
    confidence_score: float = 1.0
    research_cost: float = 0.0
    data_sources: dict[str, Any] = {}
    zep_graph_id: str | None = None
```

### 2. Updated AI Prompt

```
You are an expert company profiler. Generate rich, narrative company profiles.

STRUCTURED DATA (extract if clearly available):
- legal_name, industry, headquarters_city, headquarters_country
- founded_year, employee_range (only if explicitly mentioned)

NARRATIVE SECTIONS (only create if you have substantial information):

1. **overview** (ALWAYS create):
   - 2-4 paragraphs about what the company does
   - Synthesize from website, news, research
   - Professional, comprehensive tone

2. **services** (if services are described):
   - What services/products they offer
   - Who they serve
   - How they differentiate

3. **team** (if executive/founder info available):
   - Key executives and their backgrounds
   - Founder story
   - Team expertise

4. **track_record** (if deals/clients/results mentioned):
   - Notable deals or engagements
   - Key clients
   - Results and metrics

5. **locations** (if multiple locations mentioned):
   - Office locations and presence
   - Geographic coverage

6. **technology** (if tech stack/platform mentioned):
   - Technology approach
   - Platforms and tools

7. **news** (if recent news/activity found):
   - Recent developments
   - Company updates

RULES:
- Only create sections where you have meaningful content (2+ sentences)
- Write naturally, don't force structure
- Synthesize from all sources
- Be specific, use details from research
- Professional tone
- Markdown formatting

OUTPUT: CompanyPayload with essential structured data + rich narrative sections
```

### 3. Frontend Rendering (Pseudo-code)

```jsx
// Simple, dynamic rendering
<CompanyPage company={payload}>
  <Header>
    <h1>{payload.legal_name}</h1>
    {payload.headquarters_city && <Location>{payload.headquarters_city}, {payload.headquarters_country}</Location>}
    {payload.founded_year && <Founded>Founded {payload.founded_year}</Founded>}
  </Header>

  {/* Render only sections that exist */}
  {Object.entries(payload.profile_sections).map(([key, section]) => (
    <Section key={key}>
      <h2>{section.title}</h2>
      <Markdown>{section.content}</Markdown>
    </Section>
  ))}
</CompanyPage>
```

## Expected Results

### Before (Structured Extraction):
- Data Completeness: 29.4%
- 50+ NULL fields
- Rigid structure
- Missing critical info (description, tagline, etc.)

### After (Narrative Sections):
- Data Completeness: N/A (or 100% - everything shown exists!)
- Only populated sections displayed
- Flexible, natural content
- Rich, readable profiles

## Migration

1. Update CompanyPayload model
2. Update AI prompt for narrative generation
3. Update database schema (JSONB works as-is)
4. Update frontend to render sections dynamically
5. Regenerate existing companies (or lazy migration)

---

**Key Insight:** Stop forcing structured extraction. Let AI write naturally using whatever information is available. Only show what exists. Much better UX!
