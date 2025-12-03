# Gateway API Endpoint for Video Enrichment

## Overview
The Gateway needs a new endpoint to trigger the `VideoEnrichmentWorkflow` from the dashboard.

## Endpoint Specification

### POST `/v1/workflows/video-enrichment`

**Description**: Triggers video enrichment for an existing article

**Headers**:
```
Content-Type: application/json
X-API-Key: {API_KEY}
```

**Request Body**:
```json
{
  "slug": "moving-to-portugal",
  "app": "relocation",
  "video_model": "cdream",
  "min_sections": 4,
  "force_regenerate": false
}
```

**Request Parameters**:
- `slug` (required, string): Article slug to enrich
- `app` (required, string): Application context - one of: `relocation`, `placement`, `newsroom`
- `video_model` (optional, string): Video model to use - `cdream` (default) or `seedance`
- `min_sections` (optional, int): Minimum number of sections to have videos (default: 4)
- `force_regenerate` (optional, bool): Force video regeneration even if one exists (default: false)

**Response (200 OK)**:
```json
{
  "workflow_id": "video-enrichment-moving-to-portugal-abc123",
  "article_title": "Moving to Portugal: Complete Guide 2025",
  "status": "started",
  "message": "Video enrichment workflow started successfully"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid parameters or missing slug
- `401 Unauthorized`: Invalid or missing API key
- `404 Not Found`: Article not found with given slug
- `500 Internal Server Error`: Temporal workflow start failed

## Implementation Guide

### Python (FastAPI) Example:

```python
from fastapi import APIRouter, HTTPException, Header
from temporalio.client import Client
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class VideoEnrichmentRequest(BaseModel):
    slug: str
    app: str = "relocation"
    video_model: str = "cdream"
    min_sections: int = 4
    force_regenerate: bool = False

@router.post("/v1/workflows/video-enrichment")
async def trigger_video_enrichment(
    request: VideoEnrichmentRequest,
    x_api_key: str = Header(None),
    temporal_client: Client = Depends(get_temporal_client)
):
    """Trigger video enrichment workflow for an article."""

    # Validate API key
    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Validate app
    if request.app not in ["relocation", "placement", "newsroom"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid app. Must be: relocation, placement, or newsroom"
        )

    # Generate workflow ID
    workflow_id = f"video-enrichment-{request.slug}-{generate_short_id()}"

    try:
        # Start Temporal workflow
        handle = await temporal_client.start_workflow(
            "VideoEnrichmentWorkflow",
            args=[
                request.slug,
                request.app,
                request.video_model,
                request.min_sections,
                request.force_regenerate
            ],
            id=workflow_id,
            task_queue="quest-content-queue"
        )

        return {
            "workflow_id": workflow_id,
            "article_title": f"Article: {request.slug}",
            "status": "started",
            "message": "Video enrichment workflow started successfully"
        }

    except Exception as e:
        logger.error(f"Failed to start video enrichment workflow: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start workflow: {str(e)}"
        )
```

## Workflow Details

**Workflow Name**: `VideoEnrichmentWorkflow`
**Task Queue**: `quest-content-queue`
**Namespace**: `quickstart-quest.zivkb`
**Duration**: 2-5 minutes

**Workflow Steps**:
1. Fetch article by slug from database
2. Check if video regeneration is needed
3. Generate 4-act video prompt briefs from article content
4. Assemble full video prompt for Replicate
5. Generate 12-second 4-act video using specified model (cdream/seedance)
6. Upload video to MUX with metadata
7. Update article with `video_playback_id` and `video_prompt`

**Video Format**:
- Duration: 12 seconds
- Acts: 4 (3 seconds each)
- Resolution: 480p (cdream) or higher (seedance)
- Format: MP4, uploaded to MUX

**MUX Integration**:
- Video is uploaded with metadata (article_id, slug, title, app)
- MUX automatically provides time-based access to video sections
- Playback URL: `https://stream.mux.com/{playback_id}.m3u8`
- Section access: Use time parameters `?start=0&end=3` for Act 1, `?start=3&end=6` for Act 2, etc.

## Testing

### Test with curl:
```bash
curl -X POST https://quest-gateway-production.up.railway.app/v1/workflows/video-enrichment \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "slug": "moving-to-portugal",
    "app": "relocation",
    "video_model": "cdream",
    "min_sections": 4,
    "force_regenerate": false
  }'
```

### Test from Dashboard:
1. Navigate to https://dashboard-production-087b.up.railway.app/
2. Click "🎬 Video Enrichment" tab
3. Enter article slug (e.g., "moving-to-portugal")
4. Select app context
5. Click "🎬 Enrich with Videos"

## Notes

- The workflow reuses existing video generation activities from `ArticleCreationWorkflow`
- Video prompts follow the same 4-act structure used for country guides
- Videos are optimized for mobile viewing (vertical/square)
- MUX handles video processing, thumbnails, and adaptive streaming
- Articles with existing videos can be regenerated by setting `force_regenerate: true`
