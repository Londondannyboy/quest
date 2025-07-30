# OpenRouter BYOK (Bring Your Own Key) Setup

## Overview

Instead of managing multiple API keys in your codebase, OpenRouter's BYOK feature lets you configure all model providers in one place. This is more elegant, secure, and maintainable.

## Benefits

1. **Single API Key** - Only need `OPENROUTER_API_KEY` in your environment
2. **Centralized Management** - Add/remove providers without code changes
3. **Cost Transparency** - See all AI costs in one dashboard
4. **Better Security** - Fewer keys to rotate and manage
5. **Instant Access** - Use new models immediately without deployment

## Setup Instructions

### 1. Access OpenRouter Dashboard

1. Log in to [OpenRouter](https://openrouter.ai)
2. Navigate to Settings → API Keys

### 2. Configure BYOK Providers

Add your API keys for each provider:

#### OpenAI

- Click "Add Provider Key"
- Select "OpenAI"
- Enter your OpenAI API key
- Models available: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo

#### Google AI (Gemini)

- Click "Add Provider Key"
- Select "Google"
- Enter your Google AI API key
- Models available: Gemini Pro 1.5, Gemini Flash 1.5

#### Anthropic (if using your own key)

- Click "Add Provider Key"
- Select "Anthropic"
- Enter your Anthropic API key
- Models available: Claude 3 Opus, Sonnet, Haiku

### 3. Cost Structure with BYOK

When using BYOK:

- **Model costs**: Charged by the original provider (OpenAI, Google, etc.)
- **OpenRouter fee**: ~$0.001 per request for routing
- **Total cost**: Provider cost + minimal routing fee

Example:

- GPT-4 Turbo: $0.01/1K tokens (OpenAI) + $0.001 (routing)
- Gemini Pro: $0.00025/1K tokens (Google) + $0.001 (routing)

## Available Models in Quest Core V2

With BYOK configured, these models are automatically available:

### Claude Models (Anthropic)

- `anthropic/claude-3-haiku` - Fast, cost-effective
- `anthropic/claude-3-sonnet` - Balanced performance
- `anthropic/claude-3-opus` - High quality reasoning

### Gemini Models (Google)

- `google/gemini-flash-1.5` - Ultra-fast, 1M context
- `google/gemini-pro-1.5` - Large context (2M), great for analysis

### OpenAI Models

- `openai/gpt-3.5-turbo` - Fast, affordable
- `openai/gpt-4` - High quality, consistent
- `openai/gpt-4-turbo` - Large context (128K), good for code

## Usage in Code

The application automatically selects the best model based on task:

```typescript
// Automatic model selection based on context
import { selectModelWithFallback } from '@/lib/model-selector'

const model = selectModelWithFallback(text, 'analysis')
// Will use Gemini for large contexts, Claude for general tasks
```

## Model Selection Logic

1. **Large Context (>100K tokens)**: Gemini Pro 1.5
2. **Code Review**: GPT-4 Turbo
3. **Code Generation**: Claude 3 Sonnet
4. **General Chat**: Claude 3 Haiku
5. **Complex Reasoning**: Claude 3 Opus

## Monitoring Usage

View usage across all providers:

1. OpenRouter Dashboard → Usage
2. See breakdown by model and provider
3. Set spending limits if needed

## Troubleshooting

### "Model not available"

- Verify API key is added in OpenRouter
- Check if model is enabled for your account
- Ensure billing is set up with provider

### "Rate limit exceeded"

- Check limits with original provider
- OpenRouter respects provider rate limits
- Consider upgrading provider plan

### "Invalid API key"

- Re-add key in OpenRouter dashboard
- Verify key works with provider directly
- Check key permissions/scopes

## Best Practices

1. **Start with one provider** - Add others as needed
2. **Monitor costs** - Set alerts in OpenRouter
3. **Use appropriate models** - Don't use GPT-4 for simple tasks
4. **Leverage Gemini** - Great for large context at low cost
5. **Test fallbacks** - Ensure graceful degradation
