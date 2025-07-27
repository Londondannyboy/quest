export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    // Import dynamically to avoid any caching issues
    const { currentUser } = await import('@clerk/nextjs/server')
    
    const user = await currentUser()
    
    return Response.json({
      success: true,
      hasUser: !!user,
      userId: user?.id || null,
      email: user?.emailAddresses?.[0]?.emailAddress || null,
    })
  } catch (error) {
    return Response.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    })
  }
}