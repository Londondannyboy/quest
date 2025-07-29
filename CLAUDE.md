# Claude AI Assistant Guidelines

This document contains specific instructions and preferences for Claude when working on this project.

## Git Workflow

- **Auto-push enabled**: You can push changes when you feel ready without asking for permission
- **No users in production**: Feel free to push directly to main/master branch
- **Commit frequently**: Make commits when completing significant features or fixes
- **Push after commits**: Always push after creating commits

## Testing Commands

When code changes are made, run these commands before committing:

- `npm run build` - Ensure TypeScript compilation succeeds
- `npm run lint` - Check for linting issues
- `npm run typecheck` - Verify type safety

## Project Context

This is Quest Core V2, a career development platform with:

- Voice-first Trinity discovery using Hume AI EVI 3
- Professional mirror data from LinkedIn/company sources
- Quest readiness assessment and coaching system
- Three AI coaches: Story Coach, Quest Coach, and Delivery Coach

## Development Preferences

- Prefer editing existing files over creating new ones
- Don't create documentation files unless explicitly requested
- Use TypeScript strictly with proper type safety
- Follow existing code patterns and conventions
- Keep responses concise and action-focused

## Environment Variables

Critical environment variables that must be set:

- `NEXT_PUBLIC_HUME_API_KEY` - Hume AI API key
- `NEXT_PUBLIC_HUME_SECRET_KEY` - Hume AI secret key
- `NEXT_PUBLIC_HUME_CONFIG_ID` - Hume AI EVI 3 config ID
- `DATABASE_URL` - PostgreSQL connection string
- Clerk authentication keys
- Other service keys as documented in `.env.local`
