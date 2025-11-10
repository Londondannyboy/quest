# Quest - Content Generation Engine

Clean, minimal content generation system powering multiple frontend sites.

## Overview

Quest is a rebuild of the newsroom content generation backend, extracting only the working 20% of code and rebuilding clean. It powers multiple frontend sites (placement, relocation, etc.) through a hybrid monorepo architecture.

## Architecture

```
quest/
├── gateway/          # FastAPI HTTP API
│   ├── main.py      # App entry point
│   ├── routers/     # API endpoints
│   └── auth.py      # API key validation
│
├── worker/          # Temporal Python worker
│   ├── workflows/   # Content generation workflows
│   ├── agents/      # Pydantic AI agents
│   └── activities/  # Temporal activities
│
└── shared/          # Shared types and utilities
```

## Features

- Multi-app support (placement, relocation, etc.)
- Clean Temporal workflows for content generation
- Pydantic AI agents for editorial and writing
- SuperMemory integration for long-term memory
- Zep integration for article research
- Image generation with Replicate
- Cloudinary image storage
- Neon PostgreSQL database

## Quick Start

See [DEVELOPMENT.md](./DEVELOPMENT.md) for local setup instructions.

## Deployment

Deployed on Railway with two services:
- `quest-gateway` - FastAPI HTTP API (public)
- `quest-worker` - Temporal worker (internal)

## API Documentation

Once deployed, visit `/docs` for interactive API documentation.

## Environment Variables

See [.env.example](./.env.example) for required environment variables.

## License

MIT
