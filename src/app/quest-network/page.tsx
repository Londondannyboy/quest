'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import dynamic from 'next/dynamic'

// Dynamically import the 3D graph to avoid SSR issues
const QuestNetworkGraph = dynamic(
  () => import('@/components/quest-network-graph'),
  { ssr: false }
)

interface NetworkNode {
  id: string
  label: string
  type: 'user' | 'colleague'
  isQuestReady?: boolean
  clarityScore?: number
  company?: string
  title?: string
}

interface NetworkLink {
  source: string
  target: string
  type: string
  strength?: number
}

interface NetworkStats {
  totalConnections: number
  questReadyConnections: number
  averageClarityScore: number
  companiesRepresented: number
}

export default function QuestNetworkPage() {
  const { user, isSignedIn } = useUser()
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true)
  const [nodes, setNodes] = useState<NetworkNode[]>([])
  const [links, setLinks] = useState<NetworkLink[]>([])
  const [stats, setStats] = useState<NetworkStats | null>(null)
  const [selectedNode, setSelectedNode] = useState<NetworkNode | null>(null)
  const [viewDepth, setViewDepth] = useState(2)
  const [filterType, setFilterType] = useState<'all' | 'quest-ready' | 'colleagues'>('all')

  useEffect(() => {
    if (!isSignedIn) {
      router.push('/')
      return
    }
    loadNetworkData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSignedIn, router, viewDepth])

  const loadNetworkData = async () => {
    try {
      setIsLoading(true)
      
      // Load network graph data
      const graphResponse = await fetch(`/api/quest-network/graph?depth=${viewDepth}`)
      if (graphResponse.ok) {
        const graphData = await graphResponse.json()
        
        // Apply filters
        let filteredNodes = graphData.nodes
        let filteredLinks = graphData.links
        
        if (filterType === 'quest-ready') {
          filteredNodes = graphData.nodes.filter((n: NetworkNode) => 
            n.id === user?.id || (n.type === 'user' && n.isQuestReady)
          )
          const nodeIds = new Set(filteredNodes.map((n: NetworkNode) => n.id))
          filteredLinks = graphData.links.filter((l: NetworkLink) =>
            nodeIds.has(l.source) && nodeIds.has(l.target)
          )
        } else if (filterType === 'colleagues') {
          filteredNodes = graphData.nodes.filter((n: NetworkNode) =>
            n.id === user?.id || n.type === 'colleague'
          )
          const nodeIds = new Set(filteredNodes.map((n: NetworkNode) => n.id))
          filteredLinks = graphData.links.filter((l: NetworkLink) =>
            nodeIds.has(l.source) && nodeIds.has(l.target) && l.type === 'WORKS_WITH'
          )
        }
        
        setNodes(filteredNodes)
        setLinks(filteredLinks)
      }
      
      // Load network statistics
      const statsResponse = await fetch('/api/quest-network/stats')
      if (statsResponse.ok) {
        const statsData = await statsResponse.json()
        setStats(statsData)
      }
    } catch (error) {
      console.error('Failed to load network data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleNodeClick = (node: NetworkNode) => {
    setSelectedNode(node)
    
    // If it's a user node, potentially navigate to their profile
    if (node.type === 'user' && node.id !== user?.id) {
      // Could implement profile viewing here
      console.log('View profile:', node)
    }
  }

  const handleConnect = async (targetUserId: string) => {
    try {
      const response = await fetch('/api/quest-network/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ targetUserId })
      })
      
      if (response.ok) {
        // Reload network data
        loadNetworkData()
      }
    } catch (error) {
      console.error('Failed to create connection:', error)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p>Loading your Quest network...</p>
        </div>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white">
      <div className="flex h-screen">
        {/* Left Panel - Controls and Stats */}
        <div className="w-96 bg-gray-900 p-6 overflow-y-auto">
          <h1 className="text-2xl font-bold mb-6">Quest Network</h1>
          
          {/* Network Stats */}
          {stats && (
            <div className="bg-gray-800 p-4 rounded-lg mb-6">
              <h2 className="text-lg font-semibold mb-3">Your Network</h2>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-400">Total Connections</p>
                  <p className="text-2xl font-bold">{stats.totalConnections}</p>
                </div>
                <div>
                  <p className="text-gray-400">Quest Ready</p>
                  <p className="text-2xl font-bold text-green-400">
                    {stats.questReadyConnections}
                  </p>
                </div>
                <div>
                  <p className="text-gray-400">Avg Clarity</p>
                  <p className="text-2xl font-bold">
                    {Math.round(stats.averageClarityScore)}%
                  </p>
                </div>
                <div>
                  <p className="text-gray-400">Companies</p>
                  <p className="text-2xl font-bold">{stats.companiesRepresented}</p>
                </div>
              </div>
            </div>
          )}
          
          {/* View Controls */}
          <div className="bg-gray-800 p-4 rounded-lg mb-6">
            <h3 className="font-semibold mb-3">View Options</h3>
            
            {/* Depth Control */}
            <div className="mb-4">
              <label className="text-sm text-gray-400 block mb-1">
                Connection Depth
              </label>
              <div className="flex gap-2">
                {[1, 2, 3].map(depth => (
                  <button
                    key={depth}
                    onClick={() => setViewDepth(depth)}
                    className={`px-3 py-1 rounded ${
                      viewDepth === depth
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {depth}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Filter Controls */}
            <div>
              <label className="text-sm text-gray-400 block mb-1">Filter</label>
              <div className="space-y-2">
                {[
                  { value: 'all', label: 'All Connections' },
                  { value: 'quest-ready', label: 'Quest Ready Only' },
                  { value: 'colleagues', label: 'Colleagues Only' }
                ].map(filter => (
                  <button
                    key={filter.value}
                    onClick={() => setFilterType(filter.value as 'all' | 'quest-ready' | 'colleagues')}
                    className={`w-full text-left px-3 py-2 rounded ${
                      filterType === filter.value
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
          
          {/* Selected Node Details */}
          {selectedNode && (
            <div className="bg-gray-800 p-4 rounded-lg">
              <h3 className="font-semibold mb-3">Selected</h3>
              <div className="space-y-2 text-sm">
                <p className="font-medium">{selectedNode.label}</p>
                {selectedNode.title && (
                  <p className="text-gray-400">{selectedNode.title}</p>
                )}
                {selectedNode.company && (
                  <p className="text-gray-400">{selectedNode.company}</p>
                )}
                {selectedNode.type === 'user' && selectedNode.clarityScore !== undefined && (
                  <p>
                    Trinity Clarity:{' '}
                    <span className="font-semibold">{selectedNode.clarityScore}%</span>
                  </p>
                )}
                
                {/* Action Buttons */}
                {selectedNode.type === 'user' && selectedNode.id !== user?.id && (
                  <div className="pt-3 space-y-2">
                    <button
                      onClick={() => handleConnect(selectedNode.id)}
                      className="w-full px-3 py-2 bg-blue-600 rounded hover:bg-blue-700"
                    >
                      Connect on Quest
                    </button>
                    <button className="w-full px-3 py-2 bg-gray-700 rounded hover:bg-gray-600">
                      View Profile
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Suggested Connections */}
          <div className="mt-6">
            <h3 className="font-semibold mb-3">Suggested Connections</h3>
            <div className="space-y-2">
              <p className="text-sm text-gray-400">
                Finding Quest-aligned connections...
              </p>
            </div>
          </div>
        </div>
        
        {/* Right Panel - 3D Graph */}
        <div className="flex-1 relative">
          {nodes.length > 0 ? (
            <QuestNetworkGraph
              nodes={nodes}
              links={links}
              currentUserId={user?.id || ''}
              onNodeClick={handleNodeClick}
              onNodeHover={() => {}}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">
              <div className="text-center">
                <p className="text-xl mb-4">No network data yet</p>
                <p>Start by completing your Trinity to build connections</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}