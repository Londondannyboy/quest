import dynamic from 'next/dynamic'

// Dynamically import the component to avoid SSR issues with Clerk
const JourneyEntry = dynamic(() => import('@/components/journey-entry').then(mod => mod.JourneyEntry), {
  ssr: false,
  loading: () => (
    <div className="bg-gray-800 rounded-lg p-8 max-w-2xl mx-auto animate-pulse">
      <div className="h-8 bg-gray-700 rounded w-1/3 mb-6"></div>
      <div className="h-4 bg-gray-700 rounded w-full mb-6"></div>
      <div className="h-12 bg-gray-700 rounded mb-4"></div>
      <div className="h-12 bg-gray-700 rounded"></div>
    </div>
  )
})

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          {/* Hero Section */}
          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
            Quest Core V2
          </h1>
          
          <p className="text-xl md:text-2xl mb-4 text-gray-300">
            You can&apos;t begin your Quest until we understand your story
          </p>
          
          <p className="text-lg mb-12 text-gray-400">
            A revolutionary professional development platform where you must earn your Quest through story
          </p>

          {/* Philosophy */}
          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-2 text-blue-400">Story</h3>
              <p className="text-gray-300">Begin with your authentic professional narrative</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-2 text-purple-400">Trinity</h3>
              <p className="text-gray-300">Discover your Quest, Service, and Pledge through time</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-2 text-green-400">Quest</h3>
              <p className="text-gray-300">Earn your Quest - only 30% achieve readiness</p>
            </div>
          </div>

          {/* Entry Point - Client Component */}
          <JourneyEntry />

          {/* Trust Indicators */}
          <div className="mt-16 text-center">
            <p className="text-gray-400 mb-4">Built on these principles:</p>
            <div className="flex flex-wrap justify-center gap-4 text-sm">
              <span className="px-4 py-2 bg-gray-800 rounded-full">Human dignity over conversion</span>
              <span className="px-4 py-2 bg-gray-800 rounded-full">Earned access creates aspiration</span>
              <span className="px-4 py-2 bg-gray-800 rounded-full">Story as foundation</span>
              <span className="px-4 py-2 bg-gray-800 rounded-full">Continuous evolution</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}