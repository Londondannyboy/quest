import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Minimal middleware for testing - replace middleware.ts with this temporarily
export function middleware(request: NextRequest) {
  // Log environment variable availability
  console.log('=== Middleware Environment Check ===')
  console.log('DATABASE_URL exists:', !!process.env.DATABASE_URL)
  console.log('DIRECT_URL exists:', !!process.env.DIRECT_URL)
  console.log('CLERK_SECRET_KEY exists:', !!process.env.CLERK_SECRET_KEY)
  console.log('Path:', request.nextUrl.pathname)
  
  // Don't do any actual middleware logic, just pass through
  return NextResponse.next()
}

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
}