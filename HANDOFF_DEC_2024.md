# Quest Project Handoff - December 2024

## CRITICAL ISSUES

### 1. Hume EVI Custom Endpoint Mystery
**Status:** PARTIALLY WORKING - needs investigation

**Symptoms:**
- No explicit `chat_completions` logs in Railway
- BUT user reports AI knows about articles/context (suggesting something works)
- Railway shows "rate limit 500 logs/sec reached" - logs may be dropped
- User repo data (destination: Malta, origin: United States) NOT referenced in responses

**Config Verified:**
- Config ID: `54f86c53-cfc0-4adc-9af0-0c4b907cadc5` (Ito, 20/10/2025)
- Version 6: CUSTOM_LANGUAGE_MODEL → `https://quest-gateway-production.up.railway.app/voice/chat/completions`
- Frontend `.env.local` has correct config ID
- Railway has correct HUME_API_KEY and HUME_SECRET_KEY

**Possible Causes:**
1. Logs being dropped due to Railway rate limiting
2. Multiple Hume configs - user may be testing with different one
3. Hume caching at their servers

**Next Steps:**
1. Check Hume dashboard logs for errors
2. Reduce SSE logging verbosity to stay under rate limit
3. Add explicit logging at very start of `/voice/chat/completions` endpoint
4. Verify frontend Vercel deployment has correct env vars

### 2. HITL Cards Not Appearing
**Status:** NOT WORKING

**Root Cause:** Depends on Hume calling our endpoint. If endpoint isn't called, `profile_suggestion` events never emitted.

**Code is Ready:**
- `LiveActivityPanel` added to `/voice` page ✓
- Listens for `profile_suggestion` events ✓
- Yellow confirmation card UI implemented ✓

### 3. AI Not Using Repo Data
**Status:** NOT WORKING

**User's Facts in Neon:**
- destination: Malta
- origin: United States
- work_type: Remote / Digital Nomad
- family: With partner

**Root Cause:** Same as above - our endpoint must be called to include this context.

---

## PENDING FIXES

### 4. FAQs Not Rendering in Articles
**Status:** Code deployed but data missing

**Issue:** Articles have no FAQ data in `payload` field
```bash
curl .../articles/cyprus-relocation-guide | Has FAQ: False
```

**Fix Needed:**
- Check if Astro pipeline populates `payload.faq` in database
- Or generate FAQs during article creation workflow

### 5. Articles Not Showing in Sidebar
**Status:** BROKEN

**Issue:** ArticlesPanel not displaying relevant articles based on conversation

**Check:**
- `ArticlesPanel.tsx` component
- SSE `content_suggestion` events
- `/dashboard/content/articles` endpoint

### 6. Videos/Thumbnails Missing in Articles
**Status:** PARTIAL

**Implemented:**
- `video_playback_id` field returned from API
- Basic Mux player support

**Missing:**
- Mux animated GIFs (like Astro uses)
- Thumbnail generation
- Video segment navigation (4-act framework)

---

## COMPLETED THIS SESSION

1. **Article Content Rendering** - Fixed SQL error, added payload/video_narrative fields
2. **LiveActivityPanel on Voice Page** - Added HITL UI to `/voice`
3. **SSE Event Fixes** - Now listens for `profile_suggestion`
4. **Bridge Expressions** - Added filler phrases during processing
5. **ZEP Sync from Repo** - Auto-sync when facts updated from dashboard

---

## DEPLOYMENT PLAN (NEW)

### Goal: Separate Apps for Different Products

**Current State:**
- Single `app` repo deployed to Vercel
- Serves relocation assistant features

**Target State:**
```
/app (current)
  ├── src/app/
  │   ├── (relocation)/  ← Relocation-specific pages
  │   │   ├── voice/
  │   │   ├── dashboard/
  │   │   └── articles/
  │   └── (placement)/   ← Placement-specific pages (future)
  │       ├── jobs/
  │       └── applications/
```

**Option A: Route Groups (Recommended)**
- Use Next.js route groups `(relocation)` and `(placement)`
- Single deployment, different layouts per product
- Easy to share components

**Option B: Separate Repos**
- `app-relocation` → relocation.quest
- `app-placement` → placement app
- More isolation, more maintenance

**Vercel Setup:**
- Each product gets own Vercel project
- Or use Vercel's multi-project monorepo support

---

## ENVIRONMENT REFERENCE

### Frontend (.env.local)
```
NEXT_PUBLIC_GATEWAY_URL=https://quest-gateway-production.up.railway.app
NEXT_PUBLIC_HUME_CONFIG_ID=54f86c53-cfc0-4adc-9af0-0c4b907cadc5
NEXT_PUBLIC_STACK_PROJECT_ID=...
```

### Backend (Railway - verified correct)
- HUME_API_KEY: gzwF7lPBfI...
- HUME_SECRET_KEY: cN0BYa70A0...
- HUME_CONFIG_ID: 54f86c53-cfc0-4adc-9af0-0c4b907cadc5

### User's Hume Configs (from dashboard)
1. **13/11/2025** - Fastidious Robo-Butler (EVI 3)
2. **20/10/2025** - Ito (EVI 3) ← THIS IS THE ONE WE CONFIGURED
3. **19/09/2025** - Fastidious Robo-Butler (EVI 3)
4. **Quest Core Voice Coach** - Inspiring Man (EVI 3)

**CHECK:** Ensure frontend uses the Ito config (54f86c53...)

---

## KEY FILES

### Voice/HITL Flow
- `gateway/routers/voice.py` - Main voice endpoint, fact extraction, HITL events
- `gateway/services/event_publisher.py` - SSE event emission
- `app/src/components/LiveActivityPanel.tsx` - HITL UI
- `app/src/components/HumeVoiceUI.tsx` - Hume SDK integration

### Context Assembly (process_query)
- Lines 298-400 in voice.py
- Sources: SuperMemory → Neon Profile → ZEP Memory → ZEP KG → Neon Fallback

### Article Rendering
- `app/src/app/articles/[slug]/page.tsx` - Article detail
- `gateway/services/content_service.py` - Article API

---

## IMMEDIATE NEXT SESSION ACTIONS

1. **Reduce SSE logging** - Lower verbosity to avoid rate limit
2. **Add explicit voice endpoint logging** - First line of `/chat/completions`
3. **Check Hume dashboard** - Look for errors/logs there
4. **Verify Vercel env vars** - Ensure production deployment has correct config
5. **Test with curl + user_id** - Simulate what Hume should send
6. **Fix ArticlesPanel** - Debug why articles not showing
7. **Check FAQ data pipeline** - Why payload.faq is empty

---

*Last updated: December 2, 2024 13:35 UTC*
