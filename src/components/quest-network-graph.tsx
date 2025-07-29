'use client'

import { useRef, useEffect, useState } from 'react'
import ForceGraph3D from 'react-force-graph-3d'
import * as THREE from 'three'

interface GraphNode {
  id: string
  label: string
  type: 'user' | 'colleague'
  isQuestReady?: boolean
  clarityScore?: number
  company?: string
  title?: string
  x?: number
  y?: number
  z?: number
  color?: string
  size?: number
}

interface GraphLink {
  source: string
  target: string
  type: string
  strength?: number
  color?: string
}

interface QuestNetworkGraphProps {
  nodes: GraphNode[]
  links: GraphLink[]
  currentUserId: string
  onNodeClick?: (node: GraphNode) => void
  onNodeHover?: (node: GraphNode | null) => void
}

export default function QuestNetworkGraph({
  nodes,
  links,
  currentUserId,
  onNodeClick,
  onNodeHover
}: QuestNetworkGraphProps) {
  const graphRef = useRef<typeof ForceGraph3D>()
  const [highlightNodes, setHighlightNodes] = useState(new Set())
  const [highlightLinks, setHighlightLinks] = useState(new Set())
  const [hoverNode, setHoverNode] = useState<GraphNode | null>(null)

  // Configure node appearance
  const getNodeColor = (node: GraphNode) => {
    if (node.id === currentUserId) return '#FFD700' // Gold for current user
    if (node.type === 'user') {
      if (node.isQuestReady) return '#00FF00' // Green for quest-ready users
      return '#00BFFF' // Blue for regular users
    }
    return '#808080' // Gray for colleagues
  }

  const getNodeSize = (node: GraphNode) => {
    if (node.id === currentUserId) return 8
    if (node.type === 'user' && node.isQuestReady) return 6
    return 4
  }

  // Configure link appearance
  const getLinkColor = (link: GraphLink) => {
    switch (link.type) {
      case 'SIMILAR_QUEST':
        return '#00FF00' // Green for similar quests
      case 'COMPLEMENTARY_QUEST':
        return '#FFA500' // Orange for complementary
      case 'SHARED_VISION':
        return '#FF00FF' // Purple for shared vision
      case 'WORKS_WITH':
        return '#606060' // Dark gray for colleagues
      default:
        return '#404040'
    }
  }

  const getLinkWidth = (link: GraphLink) => {
    return (link.strength || 0.5) * 2
  }

  // Handle node interactions
  const handleNodeHover = (node: GraphNode | null) => {
    if (!node) {
      setHighlightNodes(new Set())
      setHighlightLinks(new Set())
      setHoverNode(null)
      onNodeHover?.(null)
      return
    }

    // Highlight connected nodes and links
    const connectedNodes = new Set()
    const connectedLinks = new Set()
    
    links.forEach(link => {
      if (link.source === node.id || link.target === node.id) {
        connectedLinks.add(link)
        connectedNodes.add(link.source === node.id ? link.target : link.source)
      }
    })
    
    connectedNodes.add(node.id)
    
    setHighlightNodes(connectedNodes)
    setHighlightLinks(connectedLinks)
    setHoverNode(node)
    onNodeHover?.(node)
  }

  const handleNodeClick = (node: GraphNode) => {
    onNodeClick?.(node)
  }

  // Create custom node geometry
  const nodeThreeObject = (node: GraphNode) => {
    const geometry = node.id === currentUserId
      ? new THREE.OctahedronGeometry(getNodeSize(node))
      : new THREE.SphereGeometry(getNodeSize(node))
    
    const material = new THREE.MeshLambertMaterial({
      color: getNodeColor(node),
      emissive: highlightNodes.has(node.id) ? getNodeColor(node) : '#000000',
      emissiveIntensity: highlightNodes.has(node.id) ? 0.3 : 0
    })
    
    const mesh = new THREE.Mesh(geometry, material)
    
    // Add label sprite
    if (node.type === 'user' || node.id === currentUserId) {
      const sprite = new THREE.Sprite(
        new THREE.SpriteMaterial({
          map: createTextTexture(node.label),
          transparent: true
        })
      )
      sprite.scale.set(40, 10, 1)
      sprite.position.set(0, getNodeSize(node) + 5, 0)
      mesh.add(sprite)
    }
    
    return mesh
  }

  // Create text texture for labels
  const createTextTexture = (text: string) => {
    const canvas = document.createElement('canvas')
    const context = canvas.getContext('2d')!
    canvas.width = 256
    canvas.height = 64
    
    context.fillStyle = 'rgba(255, 255, 255, 0.9)'
    context.font = '24px Arial'
    context.textAlign = 'center'
    context.textBaseline = 'middle'
    context.fillText(text, 128, 32)
    
    const texture = new THREE.CanvasTexture(canvas)
    texture.needsUpdate = true
    
    return texture
  }

  // Auto-rotate camera
  useEffect(() => {
    const graph = graphRef.current
    if (!graph) return

    // Center camera on current user node
    const currentNode = nodes.find(n => n.id === currentUserId)
    if (currentNode) {
      graph.cameraPosition(
        { x: currentNode.x || 0, y: currentNode.y || 0, z: 100 },
        { x: currentNode.x || 0, y: currentNode.y || 0, z: 0 },
        1000
      )
    }
  }, [nodes, currentUserId])

  return (
    <div className="relative w-full h-full bg-gray-900 rounded-lg overflow-hidden">
      <ForceGraph3D
        ref={graphRef}
        graphData={{ nodes, links }}
        nodeId="id"
        nodeLabel="label"
        nodeColor={getNodeColor}
        nodeVal={getNodeSize}
        nodeThreeObject={nodeThreeObject}
        nodeThreeObjectExtend={true}
        linkColor={getLinkColor}
        linkWidth={getLinkWidth}
        linkDirectionalParticles={link => highlightLinks.has(link) ? 2 : 0}
        linkDirectionalParticleSpeed={0.005}
        onNodeHover={handleNodeHover}
        onNodeClick={handleNodeClick}
        backgroundColor="#111111"
        showNavInfo={false}
      />
      
      {/* Hover tooltip */}
      {hoverNode && (
        <div className="absolute top-4 left-4 bg-gray-800 text-white p-4 rounded-lg shadow-lg max-w-sm">
          <h3 className="font-bold text-lg">{hoverNode.label}</h3>
          {hoverNode.title && <p className="text-sm text-gray-400">{hoverNode.title}</p>}
          {hoverNode.company && <p className="text-sm text-gray-400">{hoverNode.company}</p>}
          {hoverNode.type === 'user' && hoverNode.clarityScore !== undefined && (
            <p className="text-sm mt-2">
              Trinity Clarity: <span className="font-semibold">{hoverNode.clarityScore}%</span>
            </p>
          )}
          {hoverNode.type === 'user' && hoverNode.isQuestReady && (
            <span className="inline-block mt-2 px-2 py-1 bg-green-600 text-xs rounded">
              Quest Ready
            </span>
          )}
        </div>
      )}
      
      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-gray-800 text-white p-4 rounded-lg text-sm">
        <h4 className="font-semibold mb-2">Legend</h4>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <span>You</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span>Quest Ready</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span>User</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
            <span>Colleague</span>
          </div>
        </div>
      </div>
    </div>
  )
}