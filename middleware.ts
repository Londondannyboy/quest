import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isProtectedRoute = createRouteMatcher([
  '/api/colleagues(.*)',
  '/api/company(.*)',
  '/api/professional-mirror(.*)',
  '/api/trinity(.*)',
  '/api/user(.*)',
  '/colleagues(.*)',
  '/professional-mirror(.*)',
  '/trinity(.*)'
])

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) {
    await auth.protect()
  }
})

export const config = {
  matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)'],
}