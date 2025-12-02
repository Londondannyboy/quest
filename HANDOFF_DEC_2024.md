# Quest Project Handoff - December 2024

## Project Overview

Quest is an AI-powered relocation assistant with voice and text chat capabilities. The system consists of:

- **Frontend (Next.js 15)**: `/Users/dankeegan/app` - Dashboard, voice interface, articles
- **Backend (FastAPI)**: `/Users/dankeegan/quest/gateway` - API gateway with Hume EVI, Gemini, ZEP
- **Content Site (Astro)**: `/Users/dankeegan/relocation` - Static relocation guides

---

## Recent Session Progress (Dec 2, 2024)

### Completed Tasks

#### 1. Article Content Rendering Fix
**Files Modified:**
- `gateway/services/content_service.py` - Fixed SQL query (removed non-existent `author` column)
- `app/src/app/articles/[slug]/page.tsx` - Added structured content components

**Changes:**
- Fixed "Article not found" error caused by `a.author` column not existing
- Added JSON parsing for `payload` and `video_narrative` fields
- Added rendering for: FAQ accordion, callout boxes, stat highlights, timeline, sources

#### 2. LiveActivityPanel Added to Voice Page
**Files Modified:**
- `app/src/app/voice/page.tsx` - Added LiveActivityPanel import and rendering
- `app/src/components/LiveActivityPanel.tsx` - Fixed SSE event listeners

**Changes:**
- LiveActivityPanel now shows on `/voice` page (was only on `/chat`)
- Shows human-in-the-loop confirmation cards (yellow)
- Displays tool activity, ZEP graph visualization

#### 3. SSE Event Name Fix
**Files Modified:**
- `app/src/components/LiveActivityPanel.tsx`

**Changes:**
- Now listens for `profile_suggestion` (what backend sends)
- Also listens for legacy `profile_change_pending` for compatibility
- Added listeners for `fact_extracted` and `content_suggestion`
- Added console logging for SSE debugging

#### 4. Hume Configuration Verified
**Config Details:**
- Config ID: `54f86c53-cfc0-4adc-9af0-0c4b907cadc5`
- Version: 6 (latest)
- Model Provider: `CUSTOM_LANGUAGE_MODEL`
- Endpoint: `https://quest-gateway-production.up.railway.app/voice/chat/completions`

**Script to verify:** `gateway/create_hume_config_version.py`

#### 5. Bridge Expressions Added
**Files Modified:**
- `gateway/routers/voice.py` (lines ~1496-1528)

**Changes:**
- Added filler phrases for complex queries to hide processing latency
- Phrases: "Let me think about that...", "Hmm, that's a great question...", etc.
- Triggered when query > 50 chars or contains keywords like "compare", "explain", "tell me about"

#### 6. ZEP Sync from Repo Updates
**Files Modified:**
- `gateway/routers/user_profile.py` (lines ~418-500)

**Changes:**
- Auto-syncs user facts to ZEP graph when updated from dashboard/repo
- Syncs after: fact updates, fact updates by type, new fact creation
- Returns `zep_synced: true` in API response

---

## Pending/Testing Required

### Human-in-the-Loop (HITL) Testing
**Status:** Configuration is correct but needs testing with fresh session

**To Test:**
1. Close ALL browser tabs with voice page
2. Hard refresh (Cmd+Shift+R) or use incognito
3. Start fresh voice session on `/voice`
4. Say "I want to move to Spain" (when you already have a destination set)
5. Yellow confirmation card should appear in LiveActivityPanel

**Why fresh session needed:** Hume SDK caches config per session. Old sessions use old config.

### Bridge Expressions Testing
- Ask complex questions like "Tell me about the difference between Malta and Cyprus visas"
- Should hear filler phrase before main response

---

## Architecture Overview

### Frontend Routes
```
/                    - Home (auth buttons, navigation)
/voice               - Voice interface with VoiceWidget + sidebar panels
/chat                - Text chat interface
/dashboard           - Full dashboard with profile, repo, graph, articles
/articles            - Article listing
/articles/[slug]     - Article detail page
```

### Key Components

**Voice Page Sidebar:**
1. `LiveActivityPanel` - Shows HITL cards, tool activity, ZEP graph
2. `UserFactsPanel` - User facts with edit capability (validated dropdowns)
3. `ZepGraphPanel` - Knowledge graph visualization
4. `ArticlesPanel` - Related articles

**Dashboard Sections:**
- `ProfileSection` - User profile overview
- `RepoSection` - Fact repository with edit capability
- `TranscriptSection` - Voice session transcripts
- `SummarySection` - AI-generated summaries
- `ArticlesSection` - Article suggestions

### Backend Services

**Gateway (`/voice/chat/completions`):**
- Receives requests from Hume EVI
- Processes through Gemini 2.0 Flash
- Queries ZEP for user context
- Extracts facts and stores in Neon
- Emits SSE events for dashboard updates
- Triggers HITL for fact changes

**SSE Events Emitted:**
- `tool_start` / `tool_end` - Tool execution
- `profile_suggestion` - HITL fact change request
- `fact_extracted` - New fact detected
- `content_suggestion` - Relevant content found
- `fact_updated` - Fact changed

---

## Environment Variables

### Frontend (`.env.local`):
```
NEXT_PUBLIC_GATEWAY_URL=https://quest-gateway-production.up.railway.app
NEXT_PUBLIC_HUME_CONFIG_ID=54f86c53-cfc0-4adc-9af0-0c4b907cadc5
NEXT_PUBLIC_STACK_PROJECT_ID=...
NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY=...
STACK_SECRET_SERVER_KEY=...
```

### Backend (Railway):
```
HUME_API_KEY=...
HUME_SECRET_KEY=...
GEMINI_API_KEY=...
ZEP_API_KEY=...
DATABASE_URL=... (Neon)
SUPERMEMORY_API_KEY=...
```

---

## Database Schema (Neon)

### Key Tables:
- `user_profiles` - User profile metadata
- `user_facts` - Individual facts (destination, budget, timeline, etc.)
- `voice_sessions` - Voice conversation sessions
- `articles` - Article content with payload JSON
- `countries` - Country guides

### Fact Types:
- `destination`, `origin`, `budget`, `timeline`
- `family`, `work_type`, `visa_interest`
- `nationality`, `profession`

---

## Deployment

### Frontend (Vercel)
- Auto-deploys from `app` repo main branch
- Build command: `npm run build`

### Backend (Railway)
- Auto-deploys from `quest/gateway` on push
- Python FastAPI with uvicorn
- Check logs: `railway logs` or Railway dashboard

### Useful Commands
```bash
# Check Railway logs
cd /Users/dankeegan/quest/gateway
railway logs

# Verify Hume config
python3 create_hume_config_version.py

# Check service status
curl https://quest-gateway-production.up.railway.app/voice/status
```

---

## Known Issues & Limitations

1. **SSE Reconnection Loop** - Dashboard shows rapid subscribe/unsubscribe (cosmetic, doesn't affect functionality)

2. **Hume Session Caching** - Config changes require fresh browser session

3. **Voice Widget Loading** - May take a few seconds to initialize on first load

---

## Next Steps / Future Work

1. **Test HITL Flow** - Verify yellow confirmation cards appear for fact changes

2. **Add More Bridge Expressions** - Consider context-aware fillers based on query type

3. **Mux Video Components** - Full video player support in articles (currently basic)

4. **Real-time ZEP Graph Updates** - Show graph changes as facts are added in voice

5. **Conversation Memory** - Better context retention across sessions

---

## Quick Reference

### Git Repos
- Frontend: `https://github.com/Londondannyboy/app.git`
- Backend: `https://github.com/Londondannyboy/quest.git`

### Production URLs
- App: `https://app.relocation.quest` (or Vercel URL)
- Gateway: `https://quest-gateway-production.up.railway.app`

### Recent Commits
- Frontend: `feat: Add LiveActivityPanel to voice page for HITL visibility`
- Backend: `feat: Add bridge expressions and ZEP sync for repo updates`

---

*Last updated: December 2, 2024*
