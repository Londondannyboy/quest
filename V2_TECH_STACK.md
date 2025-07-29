# Quest Core V2 Tech Stack

## Core Framework

- **Next.js 15.4.4** - React framework with App Router
- **TypeScript 5.x** - Type safety
- **React 19.1.0** - UI library
- **Tailwind CSS 4** - Styling

## Database & ORM

- **PostgreSQL** - Primary database (via Neon)
- **Prisma 6.12.0** - ORM with entity-first design
- **Neo4j** - Graph database for network relationships

## Authentication & Security

- **Clerk** - Authentication and user management
- **Svix** - Webhook security

## AI & Language Models

- **OpenRouter** - Multi-model routing (Claude, GPT, Gemini)
- **Hume AI EVI 3** - Voice coaching with emotional intelligence
- **Zep** - Memory management for conversations
- **Kimi K2** (Planned) - Moonshot AI integration

## MCP (Model Context Protocol) Servers

- **Zen MCP Server** - Multi-LLM collaboration orchestration
- **REF MCP** (Planned) - Reference management
- **Playwright MCP** (Planned) - Browser automation
- **Semgrep MCP** (Planned) - Code analysis
- **Apify MCP** (Planned) - Web scraping enhancement
- **n8n MCP** (Planned) - Workflow automation
- **Pieces MCP** (Planned) - Code snippet management
- **Sequential Thinking MCP** (Planned) - Complex reasoning

## Data Scraping & Enrichment

- **Apify Client** - LinkedIn scraping via HarvestAPI
- **Company enrichment** - Via custom entity system

## Visualization

- **React Three Fiber** - 3D Trinity visualization
- **React Force Graph 3D** - Network visualization
- **Three.js** - 3D graphics

## Monitoring & Observability

- **HyperDX** - Unified observability platform
- **Checkly** - Synthetic monitoring and testing
- **OpenTelemetry** (Future) - Observability framework

## Development Tools

- **Husky** - Git hooks
- **ESLint** - Code linting
- **Prettier** - Code formatting
- **Playwright** - E2E testing

## Deployment & Infrastructure

- **Vercel** - Hosting and deployment
- **GitHub Actions** - CI/CD pipelines

## Future Integrations

- **PocketFlow** - Multi-agent debate system
- **Vector Database** - For semantic search
- **Temporal** - Workflow orchestration

## Cost Optimization Strategy

- Model routing based on task complexity
- Fallback strategies for availability
- Target: <$0.50/user/month

## Architecture Principles

1. **Entity-First Design** - No raw strings, everything is an entity
2. **Provisional → Validated** - Data validation workflow
3. **6-Month Cache** - Intelligent data refresh
4. **Multi-Model Collaboration** - Use best model for each task
5. **Memory Persistence** - Context across sessions
