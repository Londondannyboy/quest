# Quest Core V2 - Compact Summary

## Current Status

Working on Hume AI EVI 3 voice coach integration for Trinity discovery interface.

## Key Issues to Resolve

1. **Voice Coach Not Hearing** - Continuous listening implemented but microphone input not being received
2. **Duplicate Voice/Echo** - Two voice streams playing, interrupting each other
3. **User Context** - CLM endpoint needs to identify actual user (temporary fix in place)

## Recent Changes

- Implemented continuous listening (auto-starts after connection)
- Removed button-based recording
- Added sequence-based audio duplicate prevention
- Fixed environment variables on Vercel
- Added debug pages (/hume-diagnostic, /hume-ws-test)

## Technical Context

- **Hume EVI 3** WebSocket connection at `wss://api.hume.ai/v0/evi/chat`
- **CLM Endpoint** at `/api/hume-clm-sse/chat/completions` using SSE format
- **Config ID**: `671d99bc-1358-4aa7-b92a-d6b762cb18b5`
- Using `@humeai/voice-react` package
- Previous success with EVI 2 used SSE and continuous listening

## Files to Focus On

- `/src/app/trinity/page.tsx` - Main voice interface
- `/src/app/api/hume-clm-sse/chat/completions/route.ts` - Custom language model
- `/src/lib/hume-config.ts` - Coach personalities
- Previous success doc: https://github.com/Londondannyboy/ai-career-platform/blob/main/QUEST_HUME_EVI_SUCCESS_DOCUMENTATION.md

## Next Steps

1. Debug why continuous listening isn't capturing audio
2. Fix duplicate voice streams
3. Consider integrating Zep memory system for better context
4. Implement proper user identification in CLM

## Environment

- Next.js 15.4.4 with App Router
- Vercel deployment
- PostgreSQL (Neon) with Prisma
- Clerk authentication
