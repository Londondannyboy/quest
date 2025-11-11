# Chief of Staff Daily Schedule

## Overview
Automated daily execution of ChiefOfStaffWorkflow to generate articles about Chief of Staff appointments and news.

## Schedule Configuration

**Frequency:** Daily at 10:00 PM GMT (22:00 UTC)
**Workflow:** ChiefOfStaffWorkflow
**Search Topic:** "chief of staff OR new chief of staff OR appointed chief of staff"
**Duplicate Check:** Checks last 7 days of articles to avoid duplicates

## Setup via Temporal CLI

### 1. Create the Schedule

```bash
temporal schedule create \
  --schedule-id chief-of-staff-daily \
  --workflow-id "article-chief-of-staff-scheduled-{{.ScheduledTime.Unix}}" \
  --task-queue quest-content-queue \
  --workflow-type ChiefOfStaffWorkflow \
  --cron "0 22 * * *" \
  --input '["chief of staff OR new chief of staff OR appointed chief of staff", 1500, true, true]' \
  --namespace quickstart-quest.zivkb \
  --address europe-west3.gcp.api.temporal.io:7233 \
  --tls-cert-path /path/to/cert.pem \
  --tls-key-path /path/to/key.pem
```

### 2. Verify the Schedule

```bash
temporal schedule describe \
  --schedule-id chief-of-staff-daily \
  --namespace quickstart-quest.zivkb \
  --address europe-west3.gcp.api.temporal.io:7233
```

### 3. List All Schedules

```bash
temporal schedule list \
  --namespace quickstart-quest.zivkb \
  --address europe-west3.gcp.api.temporal.io:7233
```

## Setup via Temporal Cloud UI

1. **Navigate to Schedules**
   - Go to Temporal Cloud Console: https://cloud.temporal.io
   - Select your namespace: `quickstart-quest.zivkb`
   - Click "Schedules" in the sidebar

2. **Create New Schedule**
   - Click "Create Schedule"
   - **Schedule ID:** `chief-of-staff-daily`
   - **Workflow Type:** `ChiefOfStaffWorkflow`
   - **Task Queue:** `quest-content-queue`

3. **Configure Schedule Timing**
   - **Cron Expression:** `0 22 * * *` (10 PM GMT daily)
   - **Timezone:** UTC

4. **Set Workflow Arguments**
   ```json
   [
     "chief of staff OR new chief of staff OR appointed chief of staff",
     1500,
     true,
     true
   ]
   ```
   - Arg 0: Search topic (keywords)
   - Arg 1: Target word count (1500)
   - Arg 2: Auto approve (true)
   - Arg 3: Skip Zep check (true)

5. **Advanced Options**
   - **Workflow ID:** `article-chief-of-staff-scheduled-{{.ScheduledTime.Unix}}`
   - **Overlap Policy:** Skip (don't run if previous execution still running)
   - **Catchup Window:** 0 (don't run missed executions)

## How It Works

### Workflow Stages:
1. **Stage 0: Duplicate Check** ✅
   - Queries Neon database for similar articles in last 7 days
   - Checks title and content for keyword matches
   - Skips generation if duplicate found

2. **Stage 1: News Search**
   - Searches Google News via Serper.dev
   - Location: UK
   - Time range: Last 24 hours
   - Keywords: "chief of staff OR new chief of staff OR appointed chief of staff"

3. **Stage 2-7: Article Generation**
   - Scrapes news articles (captures images from sources)
   - Extracts entities and themes
   - Generates executive-focused article (1500 words)
   - Creates 6 branded images with "Chief of Staff" text

4. **Stage 7.75: Image Insertion**
   - Embeds content images into markdown
   - Adds person photos from articles if available

5. **Stage 8-9: Save & Sync**
   - Saves to Neon database (`app='chief-of-staff'`)
   - Syncs to Zep knowledge graph

## Person Photo Feature

When news articles include photos of people (e.g., executive appointments):
- Photos are scraped during Stage 2
- AI analyzes if photo shows the article's subject
- Photo is inserted into article content with attribution
- Only applies to person-focused articles (appointments, hires, promotions)

## Monitoring

### Check Schedule Status
```bash
temporal schedule describe --schedule-id chief-of-staff-daily
```

### View Recent Executions
Go to Temporal Cloud UI → Workflows → Filter by:
- **Workflow Type:** ChiefOfStaffWorkflow
- **Workflow ID prefix:** article-chief-of-staff-scheduled-

### Check Generated Articles
```sql
SELECT id, title, created_at
FROM articles
WHERE app = 'chief-of-staff'
ORDER BY created_at DESC
LIMIT 10;
```

## Pause/Resume Schedule

### Pause
```bash
temporal schedule toggle \
  --schedule-id chief-of-staff-daily \
  --pause \
  --reason "Maintenance"
```

### Resume
```bash
temporal schedule toggle \
  --schedule-id chief-of-staff-daily \
  --unpause \
  --reason "Ready to resume"
```

## Modify Schedule

### Update Search Keywords
```bash
temporal schedule update \
  --schedule-id chief-of-staff-daily \
  --input '["new search terms", 1500, true, true]'
```

### Change Time (e.g., 6 AM GMT)
```bash
temporal schedule update \
  --schedule-id chief-of-staff-daily \
  --cron "0 6 * * *"
```

## Troubleshooting

### Schedule Not Running?
1. Check schedule status: `temporal schedule describe`
2. Verify worker is running on Railway
3. Check Temporal Cloud UI for errors
4. Verify DATABASE_URL and other env vars are set

### Too Many Duplicates?
Adjust duplicate check window:
- Edit `workflows/chiefofstaff.py` line 73
- Change `args=[topic, app, 7]` to different days (e.g., 3, 14, 30)

### Not Finding News?
Broaden search terms in schedule input:
```json
["chief of staff OR executive assistant OR new appointment", 1500, true, true]
```

## Cost Optimization

**Expected Costs per Execution:**
- Serper API: ~$0.01 (news search)
- Gemini API: ~$0.02 (article generation)
- Replicate API: ~$0.12 (6 images)
- **Total: ~$0.15 per day = $4.50/month**

**If no news found:**
- Duplicate check runs but article generation skipped
- Cost: ~$0.01 (Serper only)
