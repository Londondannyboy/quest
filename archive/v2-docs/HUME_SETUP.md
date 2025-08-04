# Hume EVI Configuration Guide for Quest Core

## 1. Hume Dashboard Setup

### Create a New Configuration
1. Go to [Hume Dashboard](https://app.hume.ai)
2. Navigate to "Configurations" section
3. Click "Create New Configuration"
4. Name it: "Quest Core Voice Coach"

### Configure the Custom Language Model (CLM)
1. In the configuration, find the "Language Model" section
2. Select "Custom Language Model"
3. Enter your CLM endpoint URL:
   ```
   https://quest-core.vercel.app/api/hume-clm-sse/chat/completions
   ```
   (Replace `quest-core` with your actual Vercel domain)

### Voice Settings
1. **Voice**: Select your preferred voice (e.g., "Kora" for a warm, empathetic tone)
2. **Speaking Rate**: 1.0 (default)
3. **Emotion Regulation**: Enable for more natural conversations

### System Prompt (Optional)
While our CLM endpoint handles the main prompting, you can add a base system prompt:
```
You are Quest Coach, an empathetic AI career development assistant. 
Engage naturally in voice conversations, listening actively and responding thoughtfully.
```

### Advanced Settings
1. **Interruption Sensitivity**: Medium (allows natural conversation flow)
2. **End of Turn Detection**: Default
3. **VAD (Voice Activity Detection)**: Enable

## 2. Testing in Playground

### Access Playground
1. In your configuration, click "Test in Playground"
2. Or go to: https://app.hume.ai/playground

### Test Your Configuration
1. Select your "Quest Core Voice Coach" configuration
2. Click "Connect"
3. Allow microphone permissions
4. Start speaking to test the voice interaction

### What to Test
- **Connection**: Verify it connects to your CLM endpoint
- **Response Quality**: Check if responses align with Quest coaching
- **Voice Naturalness**: Ensure smooth conversation flow
- **Interruption Handling**: Test interrupting mid-response

## 3. Debugging Tips

### Check CLM Endpoint
1. Monitor your Vercel logs for incoming requests
2. Look for POST requests to `/api/hume-clm-sse/chat/completions`
3. Verify the response format matches OpenAI SSE spec

### Common Issues
- **"Invalid model_resource"**: Ensure URL ends with `/chat/completions`
- **Connection Failed**: Check CORS headers in your endpoint
- **No Response**: Verify your OpenAI API key is set in Vercel
- **Timeout**: Ensure your endpoint responds quickly (<5s)

## 4. Environment Variables

Make sure these are set in your Vercel project:
```env
NEXT_PUBLIC_HUME_API_KEY=your_hume_api_key
NEXT_PUBLIC_HUME_CONFIGURE_ID_QUEST_CORE=671d99bc-1358-4aa7-b92a-d6b762cb18b5
OPENAI_API_KEY=your_openai_api_key
```

## 5. Getting Your Config ID

1. After creating your configuration
2. Click on the configuration name
3. Find the "Configuration ID" in the details
4. Copy this ID for your environment variables

## 6. Production Checklist

- [ ] CLM endpoint deployed and accessible
- [ ] Environment variables set in Vercel
- [ ] Configuration created in Hume Dashboard
- [ ] Config ID added to environment variables
- [ ] Tested in playground successfully
- [ ] Voice coaching page connects properly

## 7. Advanced Features (Future)

### Multi-Agent Support
You can create multiple configurations for different coaching styles:
- "Trinity Discovery Coach" - Focus on purpose exploration
- "Skills Strategy Coach" - Technical skill development
- "Career Navigator" - Career transitions
- "Wellness Coach" - Work-life balance

### Session Memory
Enhance your CLM endpoint to:
- Store conversation history
- Track user progress
- Personalize responses based on past sessions

### Analytics
Use Hume's analytics to track:
- Session duration
- User engagement
- Emotional patterns
- Common topics

## Need Help?

- Hume Documentation: https://docs.hume.ai
- Hume Support: support@hume.ai
- Quest Core Issues: Check your Vercel logs and CLM endpoint