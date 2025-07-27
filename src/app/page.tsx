export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
            Quest Core V2
          </h1>
          
          <p className="text-xl md:text-2xl mb-4 text-gray-300">
            You can&apos;t begin your Quest until we understand your story
          </p>
          
          <p className="text-lg mb-12 text-gray-400">
            A revolutionary professional development platform
          </p>

          <div className="bg-gray-800 rounded-lg p-8 max-w-2xl mx-auto">
            <h2 className="text-2xl font-semibold mb-6">Coming Soon</h2>
            <p className="text-gray-300">
              We&apos;re building something amazing. Check back soon!
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}