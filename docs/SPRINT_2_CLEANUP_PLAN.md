# Sprint 2: Code Cleanup & Modularization Plan

## 🧹 Phase 1: Remove Test/Debug Code

### Pages to Remove

- [x] `/hume-diagnostic` - Replaced by trinity-debug
- [x] `/hume-sdk-test` - No longer needed
- [x] `/hume-simple` - Superseded by trinity
- [x] `/hume-test` - Redundant test page
- [x] `/hume-ws-test` - WebSocket testing done
- [x] `/test-evi3` - EVI 3 integration complete
- [x] `/trinity-test` - Keep trinity-debug only
- [ ] Keep `/trinity-debug` - Useful for production debugging
- [ ] Keep `/debug/voice-coach` - Simplified debug UI

### API Routes to Remove

- [x] `/api/test/*` - Remove all test endpoints
- [x] `/api/hume/test-connection` - Testing complete
- [x] `/api/hume/debug` - Old debug endpoint
- [x] `/api/hume/debug-ws` - WebSocket debug done
- [ ] Keep `/api/hume/verify-config` - Useful for production
- [ ] Keep `/api/debug/zen-analyze` - Multi-LLM debugging

## 🏗️ Phase 2: Modularize Trinity Page

### Component Breakdown

```
/trinity
├── components/
│   ├── TrinityCoachCircle.tsx     # Visual coach interface
│   ├── TrinityAudioPlayer.tsx     # Audio handling logic
│   ├── TrinityWebSocket.tsx       # WebSocket connection
│   ├── TrinityTranscript.tsx      # Conversation display
│   └── TrinityControls.tsx        # Start/pause buttons
├── hooks/
│   ├── useHumeConnection.ts       # WebSocket hook
│   ├── useAudioContext.ts         # Audio management
│   └── useCoachSession.ts         # Session state
└── utils/
    ├── audio-processor.ts         # Audio utilities
    └── coach-helpers.ts           # Coach switching logic
```

## 🔧 Phase 3: Create Shared Utilities

### 1. WebSocket Manager (`/lib/websocket/`)

- Singleton connection manager
- Automatic reconnection
- Event emitter pattern
- Connection state management

### 2. Audio Utilities (`/lib/audio/`)

- Audio context management
- Chunk processing
- Fingerprinting
- Playback queue

### 3. Logging System (`/lib/logging/`)

- Replace console.log with proper logger
- Environment-based log levels
- Structured logging
- Performance monitoring

## 📋 Phase 4: Next Sprint Features

### Priority 1: Core Improvements

1. **Quest Generation Enhancement**
   - Integrate GPT-4 for better quest generation
   - Add quest templates
   - Improve clarity scoring algorithm

2. **Professional Mirror Automation**
   - Auto-sync LinkedIn data weekly
   - Company data enrichment
   - Colleague network mapping

3. **Voice Coach Intelligence**
   - Context-aware responses
   - Progress tracking
   - Personalized coaching style

### Priority 2: New Features

1. **Quest Marketplace**
   - Browse public quests
   - Quest templates
   - Success stories

2. **Team Features**
   - Company quest alignment
   - Team collaboration
   - Shared objectives

3. **Analytics Dashboard**
   - Progress visualization
   - Engagement metrics
   - ROI tracking

### Priority 3: Infrastructure

1. **Performance Optimization**
   - Implement caching (Redis)
   - Database query optimization
   - CDN for static assets

2. **Security Enhancements**
   - Rate limiting
   - API key rotation
   - Audit logging

3. **Monitoring & Alerts**
   - Set up Datadog/NewRelic
   - Error tracking (Sentry)
   - Uptime monitoring

## 🎯 Success Metrics

### Code Quality

- [ ] Remove 50% of test code
- [ ] Reduce Trinity page by 40%
- [ ] Extract 5+ reusable hooks
- [ ] Zero console.log in production

### Performance

- [ ] Page load < 2s
- [ ] WebSocket connection < 500ms
- [ ] Audio latency < 100ms

### Developer Experience

- [ ] Clear component structure
- [ ] Comprehensive documentation
- [ ] Type safety throughout
- [ ] Easy local development

## 🚀 Implementation Order

1. **Week 1**: Clean up test code
2. **Week 2**: Modularize Trinity
3. **Week 3**: Create shared utilities
4. **Week 4**: Implement new features

## 📝 Notes for `/clear` Command

When using `/clear`, the new todo list should include:

1. Quest generation improvements
2. Professional mirror automation
3. Voice coach enhancements
4. Team collaboration features
5. Performance optimization
6. Security hardening
7. Monitoring setup
