'use client'

import { ClerkProvider } from '@clerk/nextjs'
import { ReactNode } from 'react'

export function Providers({ children }: { children: ReactNode }) {
  // Skip Clerk during build if no key is present
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY && typeof window === 'undefined') {
    return <>{children}</>
  }
  
  return (
    <ClerkProvider>
      {children}
    </ClerkProvider>
  )
}