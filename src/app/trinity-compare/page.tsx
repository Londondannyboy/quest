'use client'

import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

const implementations = [
  {
    name: 'Trinity Original',
    path: '/trinity',
    description: 'Raw WebSocket implementation with manual audio handling',
    status: 'Issues with audio duplication',
    stack: ['WebSocket API', 'Web Audio API', 'Manual buffering'],
    color: 'red'
  },
  {
    name: 'Trinity Fixed',
    path: '/trinity-fixed',
    description: 'Uses HumeAudioProcessor for proper buffering',
    status: 'Better audio handling',
    stack: ['WebSocket API', 'HumeAudioProcessor', 'Audio buffering'],
    color: 'yellow'
  },
  {
    name: 'Trinity Clean',
    path: '/trinity-clean',
    description: 'Simplified implementation, plays chunks immediately',
    status: 'Minimal approach',
    stack: ['WebSocket API', 'Immediate playback'],
    color: 'yellow'
  },
  {
    name: 'Trinity SDK',
    path: '/trinity-sdk',
    description: 'Official Hume TypeScript SDK implementation',
    status: 'Follows Hume recommendations',
    stack: ['HumeClient', 'EVIWebAudioPlayer', 'SDK utilities'],
    color: 'green'
  },
  {
    name: 'Trinity Native',
    path: '/trinity-native',
    description: 'React SDK with VoiceProvider component',
    status: 'Native React integration',
    stack: ['@humeai/voice-react', 'VoiceProvider', 'useVoice hook'],
    color: 'green'
  },
  {
    name: 'Trinity Ultimate',
    path: '/trinity-ultimate',
    description: 'Full integration with all SDKs and services',
    status: 'Production ready',
    stack: ['React SDK', 'Zep Memory', 'MCP Integration', 'Enhanced debugging'],
    color: 'purple'
  }
]

export default function TrinityComparePage() {
  const { isSignedIn } = useUser()
  const router = useRouter()
  
  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
    }
  }, [isSignedIn, router])
  
  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-4 text-center">Trinity Implementations</h1>
        <p className="text-center text-gray-400 mb-12">
          Compare different approaches to implementing Hume AI voice interactions
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {implementations.map((impl) => (
            <div
              key={impl.path}
              className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition-colors"
            >
              <div className="flex items-start justify-between mb-4">
                <h2 className="text-xl font-semibold">{impl.name}</h2>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  impl.color === 'green' ? 'bg-green-900 text-green-300' :
                  impl.color === 'yellow' ? 'bg-yellow-900 text-yellow-300' :
                  impl.color === 'red' ? 'bg-red-900 text-red-300' :
                  'bg-purple-900 text-purple-300'
                }`}>
                  {impl.status}
                </span>
              </div>
              
              <p className="text-gray-400 mb-4 text-sm">{impl.description}</p>
              
              <div className="mb-4">
                <h3 className="text-sm font-medium text-gray-500 mb-2">Tech Stack:</h3>
                <div className="flex flex-wrap gap-2">
                  {impl.stack.map((tech) => (
                    <span
                      key={tech}
                      className="px-2 py-1 bg-gray-700 rounded text-xs"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
              
              <a
                href={impl.path}
                className={`block w-full text-center px-4 py-2 rounded font-medium transition-colors ${
                  impl.color === 'purple' 
                    ? 'bg-purple-600 hover:bg-purple-700 text-white'
                    : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                }`}
              >
                {impl.color === 'purple' ? 'Try Ultimate' : 'View Implementation'}
              </a>
            </div>
          ))}
        </div>
        
        <div className="mt-12 bg-gray-800 rounded-lg p-8">
          <h2 className="text-2xl font-bold mb-4">Recommendation</h2>
          <div className="prose prose-invert max-w-none">
            <p className="text-gray-300 mb-4">
              Based on Hume&apos;s official recommendations and our testing:
            </p>
            <ul className="list-disc list-inside space-y-2 text-gray-400">
              <li>
                <strong className="text-white">For production:</strong> Use <strong>Trinity Ultimate</strong> - 
                it leverages all native SDKs, includes memory management, and has multi-model debugging
              </li>
              <li>
                <strong className="text-white">For simplicity:</strong> Use <strong>Trinity Native</strong> - 
                the React SDK handles all the complexity
              </li>
              <li>
                <strong className="text-white">For learning:</strong> Compare the implementations to understand 
                the evolution from raw WebSocket to full SDK integration
              </li>
            </ul>
            
            <div className="mt-6 p-4 bg-purple-900/20 border border-purple-700 rounded">
              <p className="text-purple-300">
                <strong>Trinity Ultimate</strong> includes:
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1 text-purple-400 text-sm">
                <li>@humeai/voice-react for native React components</li>
                <li>Zep for conversation memory and context</li>
                <li>MCP for multi-model AI collaboration</li>
                <li>Enhanced debugging and session tracking</li>
                <li>Production-ready error handling</li>
              </ul>
            </div>
          </div>
        </div>
        
        <div className="mt-8 text-center">
          <a
            href="/trinity-ultimate"
            className="inline-block px-8 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold text-lg"
          >
            Launch Trinity Ultimate
          </a>
        </div>
      </div>
    </main>
  )
}