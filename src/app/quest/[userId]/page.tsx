import { notFound } from 'next/navigation'
import { Metadata } from 'next'
import { prisma } from '@/lib/prisma'
import { Shield, Target, Heart, Building2, Briefcase, Globe } from 'lucide-react'

interface PageProps {
  params: Promise<{
    userId: string
  }>
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { userId } = await params
  
  const user = await prisma.user.findUnique({
    where: { id: userId },
    include: {
      trinity: true,
      professionalMirror: true
    }
  })

  if (!user || !user.trinity || (user.trinity.clarityScore || 0) < 30) {
    return {
      title: 'Quest Profile Not Found',
      description: 'This Quest profile is not available.'
    }
  }

  const name = user.name || 'Quest User'
  const quest = user.trinity.futureQuest || ''
  
  return {
    title: `${name}'s Quest - Quest Core`,
    description: quest.substring(0, 160),
    openGraph: {
      title: `${name}'s Professional Quest`,
      description: quest,
      type: 'profile',
      siteName: 'Quest Core',
      images: [
        {
          url: `/api/og?name=${encodeURIComponent(name)}&quest=${encodeURIComponent(quest.substring(0, 100))}`,
          width: 1200,
          height: 630,
          alt: `${name}'s Quest`
        }
      ]
    },
    twitter: {
      card: 'summary_large_image',
      title: `${name}'s Quest`,
      description: quest.substring(0, 200)
    }
  }
}

export default async function PublicQuestPage({ params }: PageProps) {
  const { userId } = await params
  
  const user = await prisma.user.findUnique({
    where: { id: userId },
    include: {
      trinity: true,
      professionalMirror: true
    }
  })

  // Check if user exists and is quest-ready
  if (!user || !user.trinity || (user.trinity.clarityScore || 0) < 30) {
    notFound()
  }

  const trinity = user.trinity
  const professionalMirror = user.professionalMirror
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const enrichmentData = professionalMirror?.enrichmentData as any

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Hero Section */}
      <div className="relative bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
        <div className="absolute inset-0 bg-black opacity-10"></div>
        <div className="relative max-w-6xl mx-auto px-4 py-16 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl font-bold mb-4">
              {user.name || 'Quest Explorer'}
            </h1>
            {(enrichmentData?.title || enrichmentData?.company) && (
              <div className="flex items-center justify-center gap-4 text-indigo-100 mb-8">
                {enrichmentData?.title && (
                  <div className="flex items-center gap-2">
                    <Briefcase className="w-4 h-4" />
                    <span>{enrichmentData.title}</span>
                  </div>
                )}
                {enrichmentData?.company && (
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4" />
                    <span>{enrichmentData.company}</span>
                  </div>
                )}
              </div>
            )}
            <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm px-6 py-3 rounded-full">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              <span className="font-semibold">Quest Ready</span>
              <span className="text-indigo-100">•</span>
              <span>{trinity.clarityScore}% Clarity</span>
            </div>
          </div>
        </div>
      </div>

      {/* Trinity Display */}
      <div className="max-w-4xl mx-auto px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid gap-8">
          {/* Future Trinity - Primary Focus */}
          <div className="bg-white rounded-2xl shadow-xl p-8 border-2 border-indigo-500">
            <div className="flex items-center gap-3 mb-6">
              <Globe className="w-8 h-8 text-indigo-600" />
              <h2 className="text-2xl font-bold text-gray-900">My Quest</h2>
              <span className="bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-sm font-medium">
                Future Vision
              </span>
            </div>
            
            <div className="space-y-6">
              <div>
                <div className="flex items-center gap-2 text-gray-600 mb-2">
                  <Target className="w-5 h-5" />
                  <h3 className="font-semibold">Quest</h3>
                </div>
                <p className="text-lg text-gray-800 leading-relaxed">
                  {trinity.futureQuest}
                </p>
              </div>

              <div>
                <div className="flex items-center gap-2 text-gray-600 mb-2">
                  <Shield className="w-5 h-5" />
                  <h3 className="font-semibold">Service</h3>
                </div>
                <p className="text-lg text-gray-800 leading-relaxed">
                  {trinity.futureService}
                </p>
              </div>

              <div>
                <div className="flex items-center gap-2 text-gray-600 mb-2">
                  <Heart className="w-5 h-5" />
                  <h3 className="font-semibold">Pledge</h3>
                </div>
                <p className="text-lg text-gray-800 leading-relaxed">
                  {trinity.futurePledge}
                </p>
              </div>
            </div>
          </div>

          {/* Journey Context */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Past Trinity */}
            <div className="bg-gray-50 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
                <span className="text-2xl">📚</span> Where I&apos;ve Been
              </h3>
              <div className="space-y-3 text-sm">
                <div>
                  <span className="font-medium text-gray-600">Past Quest:</span>
                  <p className="text-gray-700 mt-1">{trinity.pastQuest}</p>
                </div>
                {trinity.pastService && (
                  <div>
                    <span className="font-medium text-gray-600">Past Service:</span>
                    <p className="text-gray-700 mt-1">{trinity.pastService}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Present Trinity */}
            <div className="bg-gray-50 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
                <span className="text-2xl">🎯</span> Where I Am Now
              </h3>
              <div className="space-y-3 text-sm">
                <div>
                  <span className="font-medium text-gray-600">Current Quest:</span>
                  <p className="text-gray-700 mt-1">{trinity.presentQuest}</p>
                </div>
                {trinity.presentService && (
                  <div>
                    <span className="font-medium text-gray-600">Current Service:</span>
                    <p className="text-gray-700 mt-1">{trinity.presentService}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <div className="mt-12 text-center">
          <p className="text-gray-600 mb-6">
            Inspired by this Quest? Create your own professional journey.
          </p>
          <a
            href="/trinity"
            className="inline-flex items-center gap-2 bg-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
          >
            Discover Your Quest
          </a>
        </div>
      </div>
    </div>
  )
}