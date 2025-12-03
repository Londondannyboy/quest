# Video Worker

Temporal Python Worker for Video Enrichment workflows.

## Purpose

Executes `VideoEnrichmentWorkflow` for adding videos to existing articles:
- Hero video generation (12-second 4-act format)
- Video upload to MUX with proper naming
- Section video cutting via MUX time-based access
- Article updates with video playback IDs

## Architecture

This worker is deployed as a **separate Railway service** from content-worker to:
- Allow independent scaling of video generation workloads
- Isolate video-specific dependencies (Replicate, MUX)
- Enable targeted monitoring and error handling for video operations

It reuses activities from content-worker via Python path imports.

## Deployment

### Railway

Deploy as a new service on Railway:

```bash
# Initialize git (if not already)
git init
git add .
git commit -m "feat: Create video-worker service"

# Deploy via Railway CLI
railway link
railway up
```

### Environment Variables

Required (set in Railway dashboard):
- `TEMPORAL_ADDRESS`
- `TEMPORAL_NAMESPACE`
- `TEMPORAL_TASK_QUEUE`
- `TEMPORAL_API_KEY`
- `NEON_CONNECTION_STRING`
- `REPLICATE_API_TOKEN`
- `MUX_TOKEN_ID`
- `MUX_TOKEN_SECRET`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_GENERATIVEAI_API_KEY`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your credentials

# Run worker
python worker.py
```

## Workflows

### VideoEnrichmentWorkflow

**Triggered from**: Dashboard or Gateway API endpoint
**Task Queue**: `quest-content-queue`
**Duration**: 2-5 minutes

**Parameters**:
- `slug` (required): Article slug
- `app` (required): Application context (relocation, placement, newsroom)
- `video_model` (optional): cdream (default) or seedance
- `min_sections` (optional): Minimum sections to have videos (default: 4)
- `force_regenerate` (optional): Force regeneration even if video exists (default: false)

**Steps**:
1. Fetch article by slug from database
2. Check if video regeneration is needed
3. Generate 4-act video prompt briefs from article content
4. Assemble full video prompt for Replicate
5. Generate 12-second 4-act video using specified model
6. Upload video to MUX with metadata (article_id, slug, title, app)
7. Update article with `video_playback_id` and `video_prompt`

**Video Format**:
- Duration: 12 seconds
- Acts: 4 (3 seconds each)
- Resolution: 480p (cdream) or higher (seedance)
- Format: MP4, uploaded to MUX

## Activities

The worker registers these activities (imported from content-worker):

### Database
- `get_article_by_slug` - Fetch article by slug
- `update_article_four_act_content` - Update article with video data

### Video Prompt Generation
- `generate_four_act_video_prompt_brief` - Generate act descriptions from article
- `generate_four_act_video_prompt` - Assemble full Replicate prompt

### Video Generation
- `generate_four_act_video` - Generate video via Replicate (Cdream/Seedance)

### MUX Upload
- `upload_video_to_mux` - Upload video with metadata

## Monitoring

Check worker status:
```bash
railway logs -s video-worker
```

Look for:
- `✅ Connected to Temporal successfully`
- `🚀 Video Worker Started Successfully!`
- `✅ Worker is ready to process video enrichment workflows`

## Troubleshooting

### Worker not picking up workflows

1. Check task queue matches: `quest-content-queue`
2. Verify Temporal connection in logs
3. Check all activities are registered

### Video generation failing

1. Check Replicate API token is valid
2. Verify model name: `cdream` or `seedance`
3. Check video prompt is valid (not empty)

### MUX upload failing

1. Verify MUX credentials (TOKEN_ID and TOKEN_SECRET)
2. Check video URL is accessible
3. Review MUX dashboard for errors

## Related Services

- **content-worker**: Main article generation worker
- **dashboard**: Streamlit UI for triggering workflows
- **gateway**: FastAPI endpoint for workflow triggers
