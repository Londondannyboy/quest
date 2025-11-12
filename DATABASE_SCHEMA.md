# Quest Database Schema

This document describes the shared Neon PostgreSQL database schema used across all Quest properties (placement.quest, chiefofstaff.quest, relocation.quest, consultancy.quest).

## Companies Table

The `companies` table is the central data structure for all organization profiles across the Quest network.

### Core Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `name` | TEXT | Company name |
| `slug` | TEXT | URL-friendly identifier (unique) |
| `company_type` | TEXT | Type of organization (see Company Types below) |
| `status` | TEXT | Publication status: `published`, `draft`, `archived` |
| `app` | TEXT | Which Quest site this belongs to: `placement`, `chief-of-staff`, `relocation`, `consultancy` |

### Descriptive Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | TEXT | Short company description (1-2 sentences) |
| `overview` | TEXT | Longer company overview/about section |
| `founded_year` | INTEGER | Year company was founded |
| `headquarters` | TEXT | Primary headquarters location |
| `website_url` | TEXT | Company website URL |
| `logo_url` | TEXT | Company logo image URL |
| `header_image_url` | TEXT | Header/banner image URL |

### Categorization Fields (NEW - Added 2025-01-12)

These fields enable advanced filtering and organization of companies by region and specialization.

| Field | Type | Description | Example Values |
|-------|------|-------------|----------------|
| `primary_country` | TEXT | Main country of operation | `"UK"`, `"USA"`, `"France"`, `"Germany"` |
| `primary_region` | TEXT | Primary geographic region | `"Europe"`, `"North America"`, `"Asia Pacific"` |
| `tags` | TEXT[] | Array of specialization tags | `["secondaries", "buyout", "growth-equity"]` |

**Key Differences:**
- **`specializations`** (existing) - Broad areas like "Private Equity", "Real Estate"
- **`tags`** (new) - Specific, searchable attributes for filtering
- **`geographic_focus`** (existing) - Multiple regions they operate in
- **`primary_country/region`** (new) - Their main base for primary filtering

### Professional Data

| Field | Type | Description |
|-------|------|-------------|
| `specializations` | TEXT[] | Array of practice areas |
| `geographic_focus` | TEXT[] | Array of regions where company operates |
| `notable_deals` | JSONB | Array of deal objects with title/description |
| `key_facts` | JSONB | Object with services, achievements, people arrays |

### Metrics

| Field | Type | Description |
|-------|------|-------------|
| `global_rank` | INTEGER | Global ranking (lower = better) |
| `regional_ranks` | JSONB | Object mapping regions to ranks |
| `capital_raised_total` | BIGINT | Total capital raised in dollars |
| `funds_served` | INTEGER | Number of funds served |

### Timestamps

| Field | Type | Description |
|-------|------|-------------|
| `created_at` | TIMESTAMPTZ | When record was created |
| `updated_at` | TIMESTAMPTZ | When record was last updated |

## Company Types

The `company_type` field determines which Quest site displays the company:

- `placement_agent` → placement.quest
- `executive_assistant_recruiters` → chiefofstaff.quest
- `relocation_service` → relocation.quest
- `consultancy` → consultancy.quest

## Using the Tagging System

### Adding Tags to a Company

Tags are stored as PostgreSQL arrays. You can edit them in the Neon Console or via SQL:

```sql
UPDATE companies
SET primary_country = 'UK',
    primary_region = 'Europe',
    tags = ARRAY['secondaries', 'buyout']
WHERE slug = 'campbell-lutyens';
```

### Example Tag Values by Company Type

**Placement Agents:**
- `secondaries`, `buyout`, `growth-equity`, `first-round`, `venture-capital`, `infrastructure`, `real-estate`, `credit`

**Executive Recruiters:**
- `graduate`, `mid-level`, `c-suite`, `software-engineers`, `finance`, `operations`, `marketing`, `sales`

**Relocation Services:**
- `corporate`, `individual`, `international`, `domestic`, `temporary`, `permanent`, `visa-support`

**Consultancies:**
- `strategy`, `operations`, `technology`, `hr`, `finance`, `marketing`, `digital-transformation`

### Querying with Tags

**Find all secondaries placement agents in UK:**
```sql
SELECT * FROM companies
WHERE company_type = 'placement_agent'
  AND primary_country = 'UK'
  AND 'secondaries' = ANY(tags)
  AND status = 'published';
```

**Top 10 European recruiters specializing in software engineers:**
```sql
SELECT * FROM companies
WHERE company_type = 'executive_assistant_recruiters'
  AND primary_region = 'Europe'
  AND 'software-engineers' = ANY(tags)
  AND status = 'published'
ORDER BY global_rank ASC NULLS LAST
LIMIT 10;
```

**All companies with multiple tags:**
```sql
SELECT * FROM companies
WHERE tags && ARRAY['buyout', 'growth-equity']  -- Overlaps with either tag
  AND status = 'published';
```

## Manual Curation

The tagging fields (`primary_country`, `primary_region`, `tags`) are designed for **human curation** to ensure accuracy. They should be:

1. **Manually reviewed** - Even if AI suggests values, they should be verified
2. **Consistently applied** - Use standardized values (e.g., always "UK", not "United Kingdom")
3. **Kept up-to-date** - Review and update as companies evolve

## Migration SQL

To add the new categorization fields to an existing database:

```sql
ALTER TABLE companies
ADD COLUMN IF NOT EXISTS primary_country TEXT,
ADD COLUMN IF NOT EXISTS primary_region TEXT,
ADD COLUMN IF NOT EXISTS tags TEXT[];
```

## Related Documentation

- See `COMPANY_API.md` for API endpoints
- See `RECRUITER_WORKFLOW.md` for SmartCompanyWorkflow usage
- See individual project READMEs for site-specific implementations
