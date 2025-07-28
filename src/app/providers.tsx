'use client'

import { useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import { initHyperDX, setUser } from '@/lib/monitoring/hyperdx'

export function MonitoringProvider({ children }: { children: React.ReactNode }) {
  const { user } = useUser()

  useEffect(() => {
    // Initialize HyperDX monitoring
    initHyperDX()
  }, [])

  useEffect(() => {
    // Set user context for monitoring
    if (user) {
      setUser(user.id, user.emailAddresses?.[0]?.emailAddress)
    }
  }, [user])

  return <>{children}</>
}