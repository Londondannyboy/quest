# Voice Coach Debugging Strategy

## Critical Issues

### 1. Duplicate Voices

- **Symptom**: Two voices speaking at different times, interrupting each other
- **Possible Causes**:
  - Multiple WebSocket connections
  - Audio chunks being played twice
  - Both WebSocket and SSE somehow active
  - React re-renders causing duplicate connections
  - Browser tab duplication

### 2. No User Context

- **Symptom**: Voice coach doesn't know user's name, thinks user is "David Hume"
- **Possible Causes**:
  - User ID not being passed to Hume
  - CLM endpoint not receiving user context
  - Hume not forwarding headers to CLM
  - Session not linked to authenticated user

## Debug Tools Created

### 1. Trinity Debug Page (`/trinity-debug`)

- Real-time event logging
- Connection counter
- Audio chunk tracking
- CLM call monitoring
- User context display

### 2. Audio Fingerprinting (`/src/lib/audio-fingerprint.ts`)

- Detects duplicate audio streams
- Tracks audio chunk patterns
- Provides duplicate statistics

### 3. Enhanced CLM Logging

- Logs all incoming requests with unique IDs
- Tracks user identification source
- Shows all headers received

### 4. Config Verification (`/api/hume/verify-config`)

- Checks Hume configuration
- Verifies CLM endpoint setup
- Tests CLM reachability

## Testing Steps

### Step 1: Verify Single Connection

1. Open `/trinity-debug`
2. Click "Get Token"
3. Click "Connect WS" once
4. Monitor connection count - should be 1
5. Check for multiple "WebSocket connected" events

### Step 2: Track Audio Sources

1. Start speaking to trigger audio
2. Monitor "Audio Chunks" counter
3. Check "Audio Sources" section
4. Look for multiple sources or high chunk counts

### Step 3: Test CLM Integration

1. Click "Test CLM" button
2. Check if CLM endpoint is called
3. Review headers sent to CLM
4. Verify user context in response

### Step 4: Production Testing

1. Deploy changes
2. Open browser console
3. Look for:
   - `[CLM xyz] ========== NEW CLM REQUEST ==========`
   - `[AudioFingerprint] Duplicate detected!`
   - WebSocket connection logs

## Immediate Actions

### 1. Add User ID to WebSocket URL

```typescript
// In trinity/page.tsx
const params = new URLSearchParams({
  access_token: accessToken,
  config_id: configId,
  user_id: user?.id || '',
  user_name: user?.fullName || '',
})
const ws = new WebSocket(`wss://api.hume.ai/v0/evi/chat?${params}`)
```

### 2. Configure Hume Dashboard

1. Go to Hume dashboard
2. Edit your config (671d99bc-1358-4aa7-b92a-d6b762cb18b5)
3. Set Custom LLM URL to: `https://quest-core-v2.vercel.app/api/hume-clm-sse/chat/completions`
4. Add custom headers if possible

### 3. Implement Strict Singleton

```typescript
// Global connection manager
const connectionManager = {
  ws: null,
  isConnecting: false,
  connect() {
    if (this.ws || this.isConnecting) return
    // ... connection logic
  },
}
```

## Debugging Checklist

- [ ] Only one WebSocket connection active
- [ ] Audio fingerprinting shows no duplicates
- [ ] CLM endpoint receives user context
- [ ] No multiple connection attempts
- [ ] User's actual name appears in responses
- [ ] Voice doesn't interrupt itself
- [ ] Can interrupt voice by speaking

## Hypotheses to Test

### H1: React StrictMode causing double connection

- Test: Deploy to production (StrictMode off)
- Evidence: Connection count = 2 in dev, 1 in prod

### H2: Hume sending audio twice

- Test: Log raw WebSocket messages
- Evidence: Same audio_output event received twice

### H3: CLM not configured in Hume

- Test: Check `/api/hume/verify-config`
- Evidence: `hasCustomLLM: false`

### H4: Browser playing cached audio

- Test: Add timestamp to audio chunks
- Evidence: Old audio plays after new

## Solution Paths

### If Multiple Connections:

1. Implement global connection manager
2. Add connection mutex/lock
3. Check for existing WS before creating

### If CLM Not Working:

1. Update Hume config with correct URL
2. Add user context to system prompt
3. Use webhook to pass user data

### If Audio Duplicated:

1. Stronger fingerprinting
2. Audio queue with deduplication
3. Single audio context instance

## Monitoring

After fixes, monitor for:

- Zero duplicate audio events in Zep
- Single WebSocket connection
- User name in coach responses
- Smooth conversation flow

## Rollback Plan

If issues persist:

1. Revert to simple implementation
2. Remove all debugging code
3. Use minimal WebSocket connection
4. Add features incrementally
