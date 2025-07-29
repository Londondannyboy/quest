# Zen MCP Server Setup for Quest Core V2

## Overview

Zen MCP (Model Context Protocol) Server enables multiple AI models to collaborate on complex tasks. It allows Claude to orchestrate between Gemini, GPT-4, and other models automatically based on task requirements.

## Benefits for Quest Core V2

1. **Voice Coach Debugging**: Multiple models analyze audio streaming issues from different perspectives
2. **Trinity Discovery**: Combines creative (Claude), analytical (Gemini), and structured (GPT-4) approaches
3. **Code Review**: Comprehensive multi-model code analysis
4. **Quest Planning**: Collaborative session planning with consensus building

## Installation

### 1. Clone Zen MCP Server

```bash
git clone https://github.com/BeehiveInnovations/zen-mcp-server.git
cd zen-mcp-server
```

### 2. Set up Environment Variables

Create `.env` file in zen-mcp-server directory:

```env
# Required API Keys
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key

# Optional for local models
OLLAMA_BASE_URL=http://localhost:11434

# Server Configuration
PORT=3000
API_KEY=your_zen_mcp_api_key
```

### 3. Install and Run

```bash
npm install
./run-server.sh
```

### 4. Configure Quest Core V2

Add to `.env.local`:

```env
# Zen MCP Configuration
ZEN_MCP_BASE_URL=http://localhost:3000
ZEN_MCP_API_KEY=your_zen_mcp_api_key
```

## Usage in Quest Core V2

### 1. Debug Voice Coach Issues

```typescript
import { debugVoiceCoachWithZen } from '@/lib/mcp/zen-mcp-client'

const result = await debugVoiceCoachWithZen({
  events: audioEvents,
  errorLogs: logs,
  codeContext: relevantCode,
})
```

### 2. Plan Trinity Sessions

```typescript
import { planTrinitySessionWithZen } from '@/lib/mcp/zen-mcp-client'

const sessionPlan = await planTrinitySessionWithZen({
  linkedinData: userProfile,
  previousSessions: history,
  goals: userGoals,
})
```

### 3. Review Code Changes

```typescript
import { reviewCodeWithZen } from '@/lib/mcp/zen-mcp-client'

const review = await reviewCodeWithZen(mainCode, relatedFiles, [
  'performance',
  'security',
  'maintainability',
])
```

## Model Selection Strategy

Zen MCP automatically selects models based on capabilities:

- **Gemini Pro**: Large context analysis, code review
- **GPT-4**: Structured planning, reasoning
- **Claude Opus**: Creative solutions, nuanced understanding
- **Ollama**: Fast local debugging, privacy-sensitive tasks

## Workflows

### Debug Workflow

1. Gemini analyzes large context (all session events)
2. GPT-4 identifies patterns and root causes
3. Claude suggests creative solutions
4. Consensus building for high-confidence fix

### Planning Workflow

1. Claude creates empathetic coaching approach
2. GPT-4 structures session flow
3. Gemini analyzes user history patterns
4. Integrated plan with personalized questions

## Monitoring

Check Zen MCP health:

```bash
curl http://localhost:3000/api/health \
  -H "Authorization: Bearer your_zen_mcp_api_key"
```

View orchestration logs:

```bash
tail -f zen-mcp-server/logs/orchestration.log
```

## Troubleshooting

### Connection Issues

- Verify Zen MCP server is running
- Check API key configuration
- Ensure port 3000 is available

### Model Errors

- Verify all API keys are valid
- Check model quotas/limits
- Review orchestration logs

### Fallback Behavior

Quest Core V2 automatically falls back to OpenRouter if Zen MCP is unavailable.

## Cost Optimization

Zen MCP includes cost optimization:

- Model selection based on task complexity
- Caching for repeated queries
- Automatic fallback to cheaper models

## Security

- All API keys stored in environment variables
- Request authentication required
- No sensitive data logged
- Local Ollama option for private data
