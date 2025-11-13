# Complete Hume EVI Setup & Deployment Guide

## Why You Need This

Hume EVI requires a **configuration** that tells it:
- How to connect to your custom LLM (Gemini + Zep)
- What voice to use
- What personality/prompt to follow
- How to handle conversations

Without this config, Hume won't know how to route conversations through your AI pipeline.

## Setup Steps (Do in Order!)

### Step 1: Install Dependencies & Create Hume Config

```bash
cd /Users/dankeegan/quest/gateway

# Install dependencies (if not already done)
pip install hume zep-cloud google-generativeai

# Run the Hume configuration setup
python setup_hume_config.py
```

This will:
1. Show you any existing Hume configurations
2. Ask if you want to create a new one
3. Create a configuration that connects to your Gemini + Zep pipeline
4. Give you a `HUME_CONFIG_ID` to save

**Save the config ID** - you'll need it!

### Step 2: Add Config ID to Environment

Add this line to `/Users/dankeegan/quest/.env`:

```env
HUME_CONFIG_ID=<the-id-from-step-1>
```

### Step 3: Deploy Backend to Railway

```bash
cd /Users/dankeegan/quest

# Commit all changes
git add .
git commit -m "Add voice assistant with Hume EVI integration"
git push origin main
```

**In Railway Dashboard:**
1. Go to **quest-gateway-production** service
2. Settings → Variables
3. Add these if not already there:
   ```
   HUME_API_KEY=gzwF7lPBfIshOhve04HLNPs5RluArU7oXQZaqnqYKi6KKQef
   HUME_SECRET_KEY=cN0BYa70A0I6jAkO8Alt8VHaRzdIRVJahWFHaLza7cGfq2tAvuzAGeEmRDGURA3i
   HUME_CONFIG_ID=<from-step-1>
   ```
4. Railway will auto-redeploy

### Step 4: Test Backend

```bash
# Test health
curl https://quest-gateway-production.up.railway.app/voice/health

# Test LLM endpoint (Hume will call this)
curl -X POST https://quest-gateway-production.up.railway.app/voice/llm-endpoint \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Tell me about relocating to Portugal"}]}'

# Test query endpoint
curl -X POST "https://quest-gateway-production.up.railway.app/voice/query?query=What%20are%20digital%20nomad%20visas&user_id=test"
```

### Step 5: Deploy Frontend to Railway

```bash
cd /Users/dankeegan/relocation

# Commit changes
git add .
git commit -m "Add voice assistant floating button"
git push origin main
```

Railway will auto-deploy the relocation site.

### Step 6: See the Button!

Once deployed (takes 2-3 minutes):
1. Visit https://relocation.quest
2. Look for **blue floating button** in bottom-right corner
3. Click it to open the voice assistant
4. Type a question about relocation!

## What Each Endpoint Does

### `/voice/chat` (WebSocket)
- Real-time chat interface
- Connects frontend button to backend
- Currently text-based (voice coming soon)

### `/voice/llm-endpoint` (POST)
- Called by Hume EVI
- Receives conversation from Hume
- Processes through Gemini + Zep
- Returns response to Hume

### `/voice/query` (POST)
- Direct HTTP testing endpoint
- Bypasses Hume, goes straight to Gemini + Zep
- Good for debugging

### `/voice/health` (GET)
- Check if all services are configured
- Shows status of Hume, Zep, Gemini

## Architecture Flow

```
User on relocation.quest
      ↓ (clicks button)
VoiceAssistant Component
      ↓ (WebSocket)
FastAPI /voice/chat
      ↓ (processes query)
┌─────────────────────┐
│  Gemini + Zep       │ ← Called directly for WebSocket
└─────────────────────┘

OR (when using full Hume EVI voice):

User speaks
      ↓
Hume EVI (voice-to-text)
      ↓ (HTTP POST)
FastAPI /voice/llm-endpoint
      ↓
┌─────────────────────┐
│  Gemini + Zep       │
└─────────────────────┘
      ↓
Hume EVI (text-to-voice)
      ↓
User hears response
```

## Current vs Future

**Current Implementation (Text-based):**
- ✅ Floating button on website
- ✅ Text chat interface
- ✅ WebSocket real-time communication
- ✅ Gemini + Zep pipeline working
- ✅ Hume configuration created (ready for voice)

**Future Enhancement (Voice):**
- 🔲 Enable microphone input
- 🔲 Stream audio to Hume EVI
- 🔲 Receive voice responses
- 🔲 Full voice-to-voice conversation

## Troubleshooting

**Can't create Hume config:**
- Check HUME_API_KEY in .env
- Run: `pip install hume`
- Try: `python setup_hume_config.py` again

**Button doesn't appear:**
- Check Railway deployment logs
- Verify frontend deployed successfully
- Clear browser cache
- Check browser console for errors

**WebSocket won't connect:**
- Verify backend is running: `curl https://quest-gateway-production.up.railway.app/voice/health`
- Check Railway logs for errors
- Verify all API keys in Railway dashboard

**No response from assistant:**
- Check Railway logs
- Test directly: `curl -X POST "https://quest-gateway-production.up.railway.app/voice/query?query=test"`
- Verify Gemini API key is valid
- Check Zep connection

## Cost Tracking

- **Current (text-only)**: ~$0.00001 per query (Gemini Flash)
- **With voice**: ~$0.072 per minute (Hume EVI)
- **Zep**: Free tier (knowledge graph searches)

Monitor in Railway dashboard → Metrics → API calls

---

**Ready to deploy?** Start with Step 1! 🚀
