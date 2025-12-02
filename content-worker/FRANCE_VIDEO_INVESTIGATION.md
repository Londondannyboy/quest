# France Video Generation Investigation

## Summary

France country guide (all 5 modes) was created on **Dec 2, 2025** but has **NO VIDEOS** despite Temporal workflow completing successfully. Slovenia (created Dec 1) worked perfectly.

---

## Findings

### ✅ What Works (Slovenia - Dec 1)
- All 5 Slovenia articles have videos:
  - `slovenia-relocation-guide` (story) - ✅ Has video
  - `slovenia-relocation-guide-guide` (guide) - ✅ Has video
  - `slovenia-relocation-guide-yolo` (yolo) - ✅ Has video
  - `slovenia-relocation-guide-voices` (voices) - ✅ Has video
  - `slovenia-relocation-guide-nomad` (nomad) - ✅ Has video

### ❌ What's Broken (France - Dec 2)
- All 5 France articles have `video_playback_id: null` and `video_asset_id: null`:
  - `france-relocation-guide` (story) - ❌ No video
  - `france-relocation-guide-guide` (guide) - ❌ No video
  - `france-relocation-guide-yolo` (yolo) - ❌ No video
  - `france-relocation-guide-voices` (voices) - ❌ No video
  - `france-relocation-guide-nomad` (nomad) - ❌ No video

---

## Timeline & Suspect Commit

**Working:** Slovenia (Dec 1, 00:02-00:08 UTC)
**Breaking Change:** Commit `25e3ae4` - "feat: Add Mux MCP server integration" (Dec 2, 16:11 UTC)
**Broken:** France (Dec 2, 14:51 UTC)

**Wait...** France was created at 14:51 UTC, but the MUX MCP commit was at 16:11 UTC. So the MUX MCP commit **didn't break France** - it was committed AFTER France failed.

---

## Root Cause Theories

### Theory 1: `video_quality` Not Set ❓
- Country guide workflow requires `video_quality` parameter
- Dashboard doesn't have country guide UI (only company/article tabs)
- User likely used `scripts/test_country_guide.py` or Gateway API directly
- Script defaults to `video_quality: "medium"`
- **BUT**: User says they used dashboard with 4 quality settings
- **CONFLICT**: Dashboard doesn't have country guide creation UI!

### Theory 2: Workflow Parameter Passing Bug 🎯 **MOST LIKELY**
- `video_quality` parameter might not be passed through correctly
- Check Gateway API `/v1/workflows/country-guide` endpoint
- Check if there was a recent change to parameter handling
- Workflow might default to `None` if parameter is missing

### Theory 3: Silent Failure in Video Generation ⚠️
- Video generation phase completed but didn't save to database
- Check if there's error handling that swallows exceptions
- Check workflow logs in Temporal UI for France workflow

---

## Action Items

### 1. Investigate Gateway Parameter Passing
Check `quest-gateway` repository:
```bash
# Check if video_quality is passed correctly
grep -r "video_quality" gateway/
```

### 2. Check Temporal Workflow Logs
- Get France workflow ID from database or Temporal UI
- Check for errors or warnings in video generation phase
- Look for "video skipped" or "quality not set" messages

### 3. Run Test Script
Execute the newly created test script:
```bash
python test_mux_naming_full.py
```

This will:
- Generate 1 video with NEW 'Q' branding (not 'QUEST')
- Upload to MUX with human-readable naming
- Verify passthrough metadata format
- Cost: ~$0.30, Time: ~3-6 minutes

### 4. Re-run France with Explicit Parameters
```bash
# Via test script
python scripts/test_country_guide.py France FR medium

# Via Gateway API
curl -X POST https://gateway.../v1/workflows/country-guide \
  -H "Content-Type: application/json" \
  -d '{
    "country_name": "France",
    "country_code": "FR",
    "app": "relocation",
    "video_quality": "medium",
    "use_cluster_architecture": true
  }'
```

---

## Fixes Applied

### ✅ Fixed: T-Shirt Branding
**File:** `src/activities/generation/country_guide_generation.py:1723,1728,1732`

**Before:**
```python
ACT 1: Quest t-shirt with 'QUEST' in WHITE letters clearly visible on chest.
```

**After:**
```python
ACT 1: Quest t-shirt with single letter 'Q' in WHITE clearly visible on chest.
```

**Reason:** AI models render single letters more reliably than full words.

### ✅ Confirmed: MUX Naming Already Implemented
**File:** `src/activities/media/mux_client.py:66-89`

**Format:**
```
"Title | Mode | Country | App | cluster:xxx | id:123"
```

**Example:**
```
"France Relocation Guide 2025 | STORY | France | app:relocation | cluster:abc12345 | id:160"
```

This is working correctly - just needs videos to be generated!

---

## Questions for User

1. **How did you trigger France country guide creation?**
   - Dashboard? (but dashboard doesn't have country guide UI)
   - Test script? (`scripts/test_country_guide.py`)
   - Gateway API directly?
   - Temporal UI directly?

2. **Do you have the Temporal workflow ID for France?**
   - Can check logs to see if video_quality was set
   - Can see exact failure point

3. **Should we re-run France now?**
   - With explicit `video_quality: "medium"`
   - Will overwrite existing articles (IDs 160-164)
   - Or create new articles with different IDs?

---

## Next Steps

1. **Run test script** to validate 'Q' branding and MUX naming
2. **Check Temporal logs** for France workflow
3. **Investigate Gateway** parameter passing
4. **Re-run France** with explicit parameters
5. **Add dashboard UI** for country guides (if needed)

---

## Cost Estimates

**Test Script:** ~$0.30 (1 video)
**Re-run France:** ~$7.50 (5 modes × 5 videos each × $0.30)

