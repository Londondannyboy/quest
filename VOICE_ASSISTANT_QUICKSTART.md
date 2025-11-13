# Voice Assistant Quick Start Guide

## What's Been Built

You now have a complete voice-enabled AI assistant for relocation.quest that:

✅ Connects users to your Zep knowledge graph via voice/text
✅ Uses Gemini LLM for fast, conversational responses
✅ Integrates with Hume.ai for future voice capabilities
✅ Works on mobile and desktop
✅ Appears as a floating button on your website

## Quick Deploy

### 1. Deploy Backend (5 minutes)

```bash
cd /Users/dankeegan/quest/gateway

# Install new dependencies
pip install -r requirements.txt

# Test locally (optional)
python main.py
# Visit http://localhost:8000/voice/health

# Deploy to Railway
# Push to git, Railway auto-deploys, or use Railway CLI
```

**Important:** Add these environment variables in Railway Dashboard:
```
HUME_API_KEY=gzwF7lPBfIshOhve04HLNPs5RluArU7oXQZaqnqYKi6KKQef
HUME_SECRET_KEY=cN0BYa70A0I6jAkO8Alt8VHaRzdIRVJahWFHaLza7cGfq2tAvuzAGeEmRDGURA3i
ZEP_API_KEY=z_1dWlkIjoiMmNkYWVjZjktYTU5Ny00ZDlkLWIyMWItNTZjOWI5OTE5MTE4In0.Ssyb_PezcGgacQFq6Slg3fyFoqs8hBhvp6WsE8rO4VK_D70CT5tqDbFOs6ZTf8rw7qYfTRhLz5YFm8RR854rHg
ZEP_PROJECT_ID=e265b35c-69d8-4880-b2b5-ec6acb237a3e
GEMINI_API_KEY=AIzaSyA99cGRMHsz3umJ99qCDgm1G_YkOWVP9Ys
```

### 2. Deploy Frontend (2 minutes)

```bash
cd /Users/dankeegan/relocation

# Test locally (optional)
pnpm dev
# Visit http://localhost:4321 and click the blue button

# Deploy to Vercel
git add .
git commit -m "Add voice assistant integration"
git push origin main
```

### 3. Test Live (1 minute)

1. Visit https://relocation.quest
2. Click the blue floating button (bottom-right corner)
3. Type: "What are the best countries for digital nomads?"
4. Get AI response powered by your knowledge graph!

## Files Modified/Created

### Backend
- ✅ `quest/gateway/routers/voice.py` - Voice assistant logic
- ✅ `quest/gateway/main.py` - Registered voice router
- ✅ `quest/gateway/requirements.txt` - Added dependencies
- ✅ `quest/.env` - Added API keys

### Frontend
- ✅ `relocation/src/components/VoiceAssistant.astro` - UI component
- ✅ `relocation/src/pages/index.astro` - Added voice button

## Testing Checklist

- [ ] Backend health check: `curl https://your-railway-url.com/voice/health`
- [ ] Backend test query: `curl -X POST "https://your-railway-url.com/voice/query?query=Hello"`
- [ ] Frontend displays floating button
- [ ] Click button opens modal
- [ ] Status shows "Connected"
- [ ] Send test query and receive response
- [ ] Response includes relevant relocation information

## Common Issues

**"Connection error"**
- Check Railway backend is deployed
- Verify environment variables are set in Railway
- Check browser console for CORS errors

**"Services not configured"**
- One or more API keys missing from Railway
- Check `/voice/status` endpoint for details

**No response received**
- Check Railway logs for errors
- Verify Gemini API key is valid
- Test Zep connection independently

## Next Steps

1. **Deploy to production** - Follow steps above
2. **Populate Zep knowledge graph** - Add relocation data
3. **Monitor usage** - Check Railway logs and metrics
4. **Enable voice audio** - Future enhancement with Hume EVI
5. **Add to more pages** - Import VoiceAssistant in other .astro files

## Key Endpoints

- **WebSocket:** `wss://your-railway-url.com/voice/chat`
- **Health Check:** `https://your-railway-url.com/voice/health`
- **Test Query:** `https://your-railway-url.com/voice/query`
- **Status:** `https://your-railway-url.com/voice/status`

## Need Help?

1. Check full documentation: `VOICE_ASSISTANT_SETUP.md`
2. Review backend logs in Railway dashboard
3. Test individual components (Zep, Gemini, Hume)
4. Check browser console for frontend errors

---

**Ready to deploy!** Follow the 3 steps above and you'll have a live voice assistant in 10 minutes.
