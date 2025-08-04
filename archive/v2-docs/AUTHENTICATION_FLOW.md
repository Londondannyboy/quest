# Authentication Flow Documentation

## Current Issue (Discovered July 15, 2025)

**Problem**: Clerk authentication (sign-in) does NOT automatically create a user in our database.

### What Happens Now:
1. User signs in with Clerk (using keegan.dan@gmail.com)
2. Clerk authenticates them successfully
3. User can access the app
4. BUT no user record exists in our PostgreSQL database
5. Any database operations fail with 404 (user not found)

### The Fix We Implemented:
- Added `/api/auth/create-user` endpoint
- Profile page now calls this on load to ensure user exists
- This is a temporary fix!

## Proper Solution Options:

### Option 1: Clerk Webhooks (Recommended)
```typescript
// api/webhooks/clerk/route.ts
// Clerk sends webhook on user.created event
// We create database user automatically
```

### Option 2: Middleware Approach
```typescript
// middleware.ts
// Check if database user exists on each request
// Create if missing
```

### Option 3: Explicit Registration Flow
- Separate registration page
- Collect additional info (company, role, etc.)
- Create complete user profile upfront

## Why This Matters:
- Without a database user, NO features work
- Profile saving fails
- Work experience fails
- Everything that touches the database fails

## Next Steps:
1. Implement Clerk webhooks for automatic user creation
2. Add proper onboarding flow
3. Consider registration vs sign-in UX

## Database Schema Reminder:
```prisma
model User {
  id        String   @id @default(dbgenerated("gen_random_uuid()"))
  clerkId   String   @unique  // This links to Clerk
  email     String   @unique
  name      String?
  // ... all other relations depend on this existing
}
```