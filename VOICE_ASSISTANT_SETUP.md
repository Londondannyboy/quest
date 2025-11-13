# Voice Assistant Integration for relocation.quest

## Overview

This integration connects relocation.quest with a voice-enabled AI assistant powered by:
- **Hume.ai EVI**: Empathic Voice Interface for natural voice interactions
- **Zep Knowledge Graph**: Contextual knowledge about relocation and corporate mobility
- **Gemini LLM**: Google's fast, cost-effective language model for query processing

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  relocation.quest (Astro Frontend)                          │
│  - VoiceAssistant.astro component                           │
│  - Floating button on all pages                             │
│  - WebSocket connection to backend                          │
└─────────────────┬───────────────────────────────────────────┘
                  │ WebSocket (wss://)
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Gateway (Railway)                                  │
│  - /voice/chat WebSocket endpoint                           │
│  - /voice/query HTTP endpoint (testing)                     │
│  - /voice/health status check                               │
│  - /voice/status detailed diagnostics                       │
└───┬──────────────────┬──────────────────────────────────────┘
    │                  │
    ▼                  ▼
┌─────────┐     ┌──────────┐
│ Hume.ai │     │   Zep    │
│   EVI   │     │  Graph   │
└─────────┘     └────┬─────┘
                     │
                ┌────▼────┐
                │ Gemini  │
                │   LLM   │
                └─────────┘
```

## Component Files

### Backend (FastAPI Gateway)

```
quest/gateway/
├── routers/
│   └── voice.py          # Voice assistant router with WebSocket endpoint
├── main.py               # Main FastAPI app (voice router registered)
├── requirements.txt      # Updated with hume, zep-cloud, google-generativeai
└── .env                  # API keys configuration
```

### Frontend (Astro/relocation.quest)

```
relocation/src/
├── components/
│   └── VoiceAssistant.astro   # Voice assistant UI component
└── pages/
    └── index.astro            # Homepage (component added)
```

## API Keys Configuration

All API keys are stored in `/Users/dankeegan/quest/.env`:

```env
# Hume Voice AI
HUME_API_KEY=gzwF7lPBfIshOhve04HLNPs5RluArU7oXQZaqnqYKi6KKQef
HUME_SECRET_KEY=cN0BYa70A0I6jAkO8Alt8VHaRzdIRVJahWFHaLza7cGfq2tAvuzAGeEmRDGURA3i

# Zep Knowledge Base
ZEP_API_KEY=z_1dWlkIjoiMmNkYWVjZjktYTU5Ny00ZDlkLWIyMWItNTZjOWI5OTE5MTE4In0.Ssyb_PezcGgacQFq6Slg3fyFoqs8hBhvp6WsE8rO4VK_D70CT5tqDbFOs6ZTf8rw7qYfTRhLz5YFm8RR854rHg
ZEP_PROJECT_ID=e265b35c-69d8-4880-b2b5-ec6acb237a3e

# Gemini LLM
GEMINI_API_KEY=AIzaSyA99cGRMHsz3umJ99qCDgm1G_YkOWVP9Ys
```

## Deployment

### 1. Deploy Backend to Railway

```bash
cd /Users/dankeegan/quest/gateway

# Install dependencies
pip install -r requirements.txt

# Test locally
python main.py

# Deploy to Railway
# Railway will automatically detect and deploy the gateway service
# Make sure environment variables are set in Railway dashboard
```

**Railway Environment Variables:**
Go to Railway dashboard → quest-gateway service → Variables
Add all the API keys from .env file.

### 2. Update Frontend Configuration

The VoiceAssistant component is configured to connect to:
```
https://quest-gateway.railway.app
```

If your Railway URL is different, update in `VoiceAssistant.astro`:
```astro
const { apiUrl = 'https://your-gateway-url.railway.app' } = Astro.props;
```

### 3. Deploy Frontend to Vercel

```bash
cd /Users/dankeegan/relocation

# Test locally
pnpm dev

# Deploy
git push origin main  # Vercel auto-deploys
```

## API Endpoints

### WebSocket Endpoint

**URL:** `wss://quest-gateway.railway.app/voice/chat`

**Query Parameters:**
- `user_id` (optional): User identifier for personalization

**Messages:**

Request (from frontend):
```json
{
  "type": "query",
  "text": "What are the visa requirements for moving to Portugal?"
}
```

Response (from backend):
```json
{
  "type": "response",
  "text": "Portugal offers several visa options for relocation...",
  "query": "What are the visa requirements for moving to Portugal?",
  "timestamp": "2025-01-13T10:30:00Z"
}
```

### HTTP Endpoints

#### Health Check
```bash
curl https://quest-gateway.railway.app/voice/health
```

Response:
```json
{
  "hume": {
    "configured": true,
    "client_ready": true
  },
  "zep": {
    "configured": true,
    "client_ready": true
  },
  "gemini": {
    "configured": true,
    "client_ready": true
  },
  "ready": true
}
```

#### Text Query (Testing)
```bash
curl -X POST "https://quest-gateway.railway.app/voice/query?query=Tell%20me%20about%20relocating%20to%20Spain&user_id=test-user"
```

#### Detailed Status
```bash
curl https://quest-gateway.railway.app/voice/status
```

## Testing

### 1. Test Backend Locally

```bash
cd /Users/dankeegan/quest/gateway

# Start server
python main.py

# In another terminal, test endpoints
curl http://localhost:8000/voice/health
curl -X POST "http://localhost:8000/voice/query?query=Hello&user_id=test"
```

### 2. Test Frontend Integration

```bash
cd /Users/dankeegan/relocation

# Start dev server
pnpm dev

# Open http://localhost:4321
# Click the blue floating voice button in bottom-right corner
# Type a question about relocation
```

### 3. Test End-to-End

1. Deploy backend to Railway
2. Update frontend API URL if needed
3. Deploy frontend to Vercel
4. Visit https://relocation.quest
5. Click voice assistant button
6. Ask: "What are the best countries for digital nomads?"

## How It Works

### Voice Query Flow

1. **User Interaction**
   - User clicks floating voice button on relocation.quest
   - Modal opens with chat interface
   - WebSocket connects to FastAPI backend

2. **Query Processing**
   - User types question and clicks send
   - Frontend sends WebSocket message: `{"type": "query", "text": "..."}`
   - Backend receives query

3. **Knowledge Retrieval**
   - Backend queries Zep knowledge graph with user's question
   - Zep returns top 5 relevant facts about relocation

4. **LLM Response Generation**
   - Backend sends query + Zep facts to Gemini
   - Gemini generates conversational, concise response
   - Response optimized for voice (< 100 words)

5. **Response Delivery**
   - Backend sends WebSocket message back to frontend
   - Frontend displays response in chat UI
   - User can ask follow-up questions

### Zep Knowledge Graph

The Zep integration searches for relevant relocation knowledge:
- Visa requirements
- Cost of living information
- Country-specific relocation details
- Corporate mobility services
- Digital nomad resources

Scope: Searches "edges" (relationships) for rich contextual information.

### Gemini LLM

System prompt optimizes responses for:
- **Brevity**: < 100 words for voice interaction
- **Conversational tone**: Friendly and natural
- **Actionable advice**: Specific, helpful information
- **Knowledge base**: Uses Zep facts when available

Model: `gemini-2.0-flash-exp` (fast, cost-effective)

## Troubleshooting

### WebSocket Connection Fails

**Symptoms:** Status shows "Connection error" or "Disconnected"

**Solutions:**
1. Check Railway backend is running: `curl https://quest-gateway.railway.app/voice/health`
2. Verify environment variables in Railway dashboard
3. Check browser console for errors
4. Ensure URL in VoiceAssistant.astro matches Railway URL

### No Response from Assistant

**Symptoms:** Query sends but no response received

**Solutions:**
1. Check backend logs in Railway dashboard
2. Test HTTP endpoint: `curl -X POST "https://quest-gateway.railway.app/voice/query?query=test"`
3. Verify API keys are set correctly in Railway
4. Check `/voice/status` endpoint for service readiness

### Zep Knowledge Graph Returns No Results

**Symptoms:** Responses don't include knowledge base information

**Solutions:**
1. Verify ZEP_API_KEY is correct
2. Check if Zep project has data: Use Zep dashboard
3. Ensure ZEP_PROJECT_ID is set (if required by your setup)
4. Test Zep directly using `zep_cloud.client` in Python

### Gemini API Errors

**Symptoms:** "Assistant is currently unavailable" responses

**Solutions:**
1. Verify GEMINI_API_KEY is valid
2. Check Google Cloud Console for API quota limits
3. Ensure Gemini API is enabled in Google Cloud project
4. Check backend logs for specific error messages

## Future Enhancements

### Phase 1: Audio Support (Hume EVI)
- Implement real audio streaming through Hume EVI
- Voice-to-voice conversations
- Emotional intelligence features

### Phase 2: Advanced Features
- Multi-turn conversation memory
- Personalized recommendations based on user history
- Integration with relocation.quest article database
- Voice-triggered search and navigation

### Phase 3: Mobile App
- React Native mobile app
- Native voice integration
- Offline knowledge base

## Cost Estimates

Based on current pricing:

- **Hume EVI**: $0.072/minute of voice interaction
- **Zep Cloud**: Free tier for knowledge graph searches
- **Gemini Flash**: ~$0.00001 per request (extremely cheap)
- **Railway Backend**: ~$5-20/month depending on usage

**Expected Monthly Cost:** $10-50 for moderate usage (100-500 queries/day)

## Support

### Documentation
- Hume API Docs: https://dev.hume.ai
- Zep Docs: https://help.getzep.com
- Gemini API: https://ai.google.dev/gemini-api/docs

### Issues
For bugs or feature requests, contact the development team.

---

**Last Updated:** January 13, 2025
**Version:** 1.0.0
**Status:** Production Ready
