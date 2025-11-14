# Connecting Hume EVI to Your AI Gateway + Zep Knowledge Graph

## What You Have

✅ **Hume EVI Vercel Deployment** - The voice interface starter (https://github.com/Londondannyboy/empathic-voice-interface-starter)
✅ **FastAPI Gateway (Railway)** - Backend with Gemini + Zep integration at `quest-gateway-production.up.railway.app`
✅ **Zep Knowledge Graph** - Your relocation data and knowledge base
✅ **Hume Config ID** - `54f86c53-cfc0-4adc-9af0-0c4b907cadc5`

## The Architecture

```
User speaks into Hume EVI (Vercel deployment)
           ↓
Hume processes voice → text
           ↓
Hume calls YOUR custom LLM endpoint:
   https://quest-gateway-production.up.railway.app/voice/llm-endpoint
           ↓
Your Gateway receives request
           ↓
   ┌──────────────────┐
   │  FastAPI Gateway │
   │  (voice.py)      │
   └────────┬─────────┘
            │
     ┌──────┴──────┐
     ↓             ↓
┌─────────┐   ┌────────┐
│   Zep   │   │ Gemini │
│  Graph  │   │  LLM   │
└─────────┘   └────────┘
     ↓             ↓
     └──────┬──────┘
            ↓
    Response text
            ↓
Hume converts text → voice
            ↓
User hears response
```

## Step-by-Step Setup

### 1. Verify Your Gateway is Running

```bash
# Test the health endpoint
curl https://quest-gateway-production.up.railway.app/voice/health

# Expected response:
# {
#   "hume": {"configured": true, "client_ready": true},
#   "zep": {"configured": true, "client_ready": true},
#   "gemini": {"configured": true, "client_ready": true},
#   "ready": true
# }
```

### 2. Test the LLM Endpoint (What Hume Will Call)

```bash
# Test with a sample request that mimics what Hume sends
curl -X POST https://quest-gateway-production.up.railway.app/voice/llm-endpoint \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What are the visa requirements for Portugal?"}
    ],
    "context": {
      "user_id": "test_user"
    }
  }'

# Expected response:
# {
#   "response": "Portugal offers several visa options..."
# }
```

### 3. Configure Your Hume EVI Deployment

#### Option A: Update Hume Config via Script

If you have the gateway code locally:

```bash
cd /Users/dankeegan/quest/gateway

# Make sure dependencies are installed
pip install hume zep-cloud google-generativeai

# Run the update script
python update_hume_config.py
```

This will:
1. List your existing Hume configs
2. Update config `54f86c53-cfc0-4adc-9af0-0c4b907cadc5`
3. Set the endpoint to: `https://quest-gateway-production.up.railway.app/voice/llm-endpoint`

#### Option B: Update via Hume Dashboard

1. Go to https://platform.hume.ai
2. Navigate to **EVI Configurations**
3. Find config: **Relocation Assistant** (ID: `54f86c53-cfc0-4adc-9af0-0c4b907cadc5`)
4. Click **Edit**
5. Under **Language Model**, set:
   - **Model Provider**: `CUSTOM_LANGUAGE_MODEL`
   - **Endpoint URL**: `https://quest-gateway-production.up.railway.app/voice/llm-endpoint`
   - **Temperature**: `0.7`
6. Save changes

### 4. Configure Your Vercel Deployment

In your Hume Vercel deployment, you need to set environment variables:

1. Go to your Vercel project dashboard
2. Go to **Settings** → **Environment Variables**
3. Add/update these variables:

```env
# Hume credentials
HUME_API_KEY=gzwF7lPBfIshOhve04HLNPs5RluArU7oXQZaqnqYKi6KKQef
HUME_SECRET_KEY=cN0BYa70A0I6jAkO8Alt8VHaRzdIRVJahWFHaLza7cGfq2tAvuzAGeEmRDGURA3i

# The config ID that points to your custom LLM endpoint
HUME_CONFIG_ID=54f86c53-cfc0-4adc-9af0-0c4b907cadc5

# Optional: Your gateway URL (for any direct backend calls)
NEXT_PUBLIC_GATEWAY_URL=https://quest-gateway-production.up.railway.app
```

4. Redeploy your Vercel app

### 5. Update the Hume Starter Code (If Needed)

If your Hume starter uses a different config ID, update it:

**File**: `components/Controls.tsx` (or similar)

```typescript
// Find where the EVI connection is initialized
const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID || '54f86c53-cfc0-4adc-9af0-0c4b907cadc5';
```

### 6. Test End-to-End

1. **Open your Hume EVI deployment** (Vercel URL)
2. **Click the voice button** to start a conversation
3. **Speak or type**: "What are the best countries for digital nomads?"
4. **Expected flow**:
   - Hume captures your voice → converts to text
   - Hume sends text to your gateway endpoint
   - Gateway queries Zep knowledge graph
   - Gateway sends query + context to Gemini
   - Gemini generates response
   - Response sent back to Hume
   - Hume converts to voice → you hear it

## The Custom LLM Endpoint

**URL**: `https://quest-gateway-production.up.railway.app/voice/llm-endpoint`

**What Hume Sends**:
```json
{
  "messages": [
    {"role": "user", "content": "What are visa requirements for Spain?"},
    {"role": "assistant", "content": "Previous response..."}
  ],
  "context": {
    "user_id": "unique_user_id",
    "conversation_id": "conversation_123"
  }
}
```

**What Your Gateway Returns**:
```json
{
  "response": "Spain offers several visa options for relocation..."
}
```

**Behind the Scenes** (in `voice.py:540-573`):
1. Extracts latest user message
2. Searches Zep knowledge graph for relevant facts
3. Sends query + Zep context to Gemini
4. Returns Gemini's response to Hume

## Endpoints Available

Your gateway exposes these endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/voice/health` | GET | Check if all services are ready |
| `/voice/status` | GET | Detailed service diagnostics |
| `/voice/llm-endpoint` | POST | **Main Hume endpoint** (Gemini + Zep) |
| `/voice/chat/completions` | POST | Alias for `/llm-endpoint` |
| `/voice/query` | POST | Direct HTTP testing (bypasses Hume) |
| `/voice/chat` | WebSocket | Text chat interface |

## Troubleshooting

### "Assistant is currently unavailable"

Check Railway logs:
```bash
# If you have Railway CLI
railway logs -s quest-gateway-production

# Or check Railway dashboard → Deployments → Logs
```

Verify environment variables in Railway dashboard:
- `HUME_API_KEY`
- `HUME_SECRET_KEY`
- `ZEP_API_KEY`
- `GEMINI_API_KEY`

### "No response from knowledge graph"

Test Zep directly:
```bash
curl -X POST https://quest-gateway-production.up.railway.app/voice/query \
  -H "Content-Type: application/json" \
  -d "query=What is a digital nomad visa?&user_id=test"
```

Check Zep credentials in Railway.

### "Hume not calling my endpoint"

1. Verify config ID in Hume dashboard
2. Check endpoint URL is correct (no trailing slash)
3. Test endpoint manually (see Step 2)
4. Check Hume logs in dashboard for error messages

## What's Different from Standard Hume Setup

**Standard Hume**: Uses Hume's default LLM (GPT-4, Claude, etc.)

**Your Setup**:
- ✅ Custom LLM endpoint (Gemini 2.0 Flash - cheaper, faster)
- ✅ Zep knowledge graph integration (your relocation data)
- ✅ Personalized responses based on your content
- ✅ Full control over the AI pipeline
- ✅ Cost optimization (~$0.00001 per query vs $0.01+)

## Cost Breakdown

**Per Voice Interaction**:
- Hume EVI: ~$0.072/minute (voice processing)
- Gemini Flash: ~$0.00001/request (LLM)
- Zep: Free tier (knowledge graph)

**Total**: ~$0.072/minute for voice + negligible LLM costs

## Next Steps

1. ✅ Run Step 1 & 2 to verify gateway is working
2. ✅ Update Hume config (Step 3)
3. ✅ Set Vercel environment variables (Step 4)
4. ✅ Test end-to-end (Step 6)
5. 🎉 Deploy to production!

## Support

**Documentation**:
- Hume EVI Docs: https://dev.hume.ai/docs/empathic-voice-interface-evi/overview
- Zep Docs: https://help.getzep.com
- Your Gateway Code: `/Users/dankeegan/quest/gateway/routers/voice.py`

**Need help?** Check Railway logs first, then Hume dashboard logs.

---

**Last Updated**: January 14, 2025
**Your Config ID**: `54f86c53-cfc0-4adc-9af0-0c4b907cadc5`
**Your Gateway**: `https://quest-gateway-production.up.railway.app`
