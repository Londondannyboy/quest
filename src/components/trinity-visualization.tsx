'use client'

import { useRef, useEffect, useState, useMemo } from 'react'
import dynamic from 'next/dynamic'
import * as THREE from 'three'

// Dynamic import to avoid SSR issues
const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { ssr: false })

interface TrinityNode {
  id: string
  label: string
  group: 'past' | 'present' | 'future'
  type: 'quest' | 'service' | 'pledge'
  value: string
  x?: number
  y?: number
  z?: number
  color?: string
  size?: number
}

interface TrinityLink {
  source: string
  target: string
  type: 'evolution' | 'connection'
  strength?: number
}

interface TrinityVisualizationProps {
  pastTrinity?: {
    quest?: string | null
    service?: string | null
    pledge?: string | null
  }
  presentTrinity?: {
    quest?: string | null
    service?: string | null
    pledge?: string | null
  }
  futureTrinity?: {
    quest?: string | null
    service?: string | null
    pledge?: string | null
  }
  clarityScore?: number
  variant?: 'timeline' | 'spiral' | 'circular' | 'columns'
}

export default function TrinityVisualization({
  pastTrinity,
  presentTrinity,
  futureTrinity,
  clarityScore = 0,
  variant = 'timeline'
}: TrinityVisualizationProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null)
  const mountRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })
  const animationFrameRef = useRef<number>(0)
  const particlesRef = useRef<THREE.Points | null>(null)
  const bgSceneRef = useRef<THREE.Scene | null>(null)
  const bgCameraRef = useRef<THREE.Camera | null>(null)

  // Update dimensions on mount and resize
  useEffect(() => {
    const updateDimensions = () => {
      if (mountRef.current) {
        setDimensions({
          width: mountRef.current.clientWidth,
          height: mountRef.current.clientHeight
        })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  // Generate nodes and links from Trinity data
  const { nodes, links } = useMemo(() => {
    const nodes: TrinityNode[] = []
    const links: TrinityLink[] = []

    // Helper to add nodes
    const addNode = (group: 'past' | 'present' | 'future', type: 'quest' | 'service' | 'pledge', value?: string | null) => {
      if (!value) return null
      
      const id = `${group}-${type}`
      const node: TrinityNode = {
        id,
        label: `${group.charAt(0).toUpperCase() + group.slice(1)} ${type.charAt(0).toUpperCase() + type.slice(1)}`,
        group,
        type,
        value,
        size: type === 'quest' ? 12 : type === 'service' ? 10 : 8
      }

      // Position based on variant
      if (variant === 'timeline') {
        const xOffset = group === 'past' ? -200 : group === 'present' ? 0 : 200
        const yOffset = type === 'quest' ? 50 : type === 'service' ? 0 : -50
        node.x = xOffset
        node.y = yOffset
        node.z = 0
      } else if (variant === 'spiral') {
        const timeIndex = group === 'past' ? 0 : group === 'present' ? 1 : 2
        const typeIndex = type === 'quest' ? 0 : type === 'service' ? 1 : 2
        const angle = (timeIndex * Math.PI * 2) / 3 + (typeIndex * Math.PI / 6)
        const radius = 100 + timeIndex * 50
        node.x = Math.cos(angle) * radius
        node.y = Math.sin(angle) * radius
        node.z = timeIndex * 30
      } else if (variant === 'circular') {
        const angle = (nodes.length * Math.PI * 2) / 9
        const radius = 150
        node.x = Math.cos(angle) * radius
        node.y = Math.sin(angle) * radius
        node.z = group === 'past' ? -50 : group === 'present' ? 0 : 50
      } else if (variant === 'columns') {
        const xOffset = group === 'past' ? -150 : group === 'present' ? 0 : 150
        const yOffset = type === 'quest' ? 100 : type === 'service' ? 0 : -100
        node.x = xOffset
        node.y = yOffset
        node.z = 0
      }

      nodes.push(node)
      return id
    }

    // Add all nodes
    const pastQuestId = addNode('past', 'quest', pastTrinity?.quest)
    const pastServiceId = addNode('past', 'service', pastTrinity?.service)
    const pastPledgeId = addNode('past', 'pledge', pastTrinity?.pledge)

    const presentQuestId = addNode('present', 'quest', presentTrinity?.quest)
    const presentServiceId = addNode('present', 'service', presentTrinity?.service)
    const presentPledgeId = addNode('present', 'pledge', presentTrinity?.pledge)

    const futureQuestId = addNode('future', 'quest', futureTrinity?.quest)
    const futureServiceId = addNode('future', 'service', futureTrinity?.service)
    const futurePledgeId = addNode('future', 'pledge', futureTrinity?.pledge)

    // Add evolution links (past → present → future)
    if (pastQuestId && presentQuestId) {
      links.push({ source: pastQuestId, target: presentQuestId, type: 'evolution' })
    }
    if (presentQuestId && futureQuestId) {
      links.push({ source: presentQuestId, target: futureQuestId, type: 'evolution', strength: clarityScore / 100 })
    }

    if (pastServiceId && presentServiceId) {
      links.push({ source: pastServiceId, target: presentServiceId, type: 'evolution' })
    }
    if (presentServiceId && futureServiceId) {
      links.push({ source: presentServiceId, target: futureServiceId, type: 'evolution', strength: clarityScore / 100 })
    }

    if (pastPledgeId && presentPledgeId) {
      links.push({ source: pastPledgeId, target: presentPledgeId, type: 'evolution' })
    }
    if (presentPledgeId && futurePledgeId) {
      links.push({ source: presentPledgeId, target: futurePledgeId, type: 'evolution', strength: clarityScore / 100 })
    }

    // Add connections within each time period
    const addInternalLinks = (questId: string | null, serviceId: string | null, pledgeId: string | null) => {
      if (questId && serviceId) {
        links.push({ source: questId, target: serviceId, type: 'connection' })
      }
      if (serviceId && pledgeId) {
        links.push({ source: serviceId, target: pledgeId, type: 'connection' })
      }
      if (questId && pledgeId) {
        links.push({ source: questId, target: pledgeId, type: 'connection' })
      }
    }

    addInternalLinks(pastQuestId, pastServiceId, pastPledgeId)
    addInternalLinks(presentQuestId, presentServiceId, presentPledgeId)
    addInternalLinks(futureQuestId, futureServiceId, futurePledgeId)

    return { nodes, links }
  }, [pastTrinity, presentTrinity, futureTrinity, clarityScore, variant])

  // Node appearance
  const getNodeColor = (node: TrinityNode) => {
    const colors = {
      past: { quest: '#4B5563', service: '#6B7280', pledge: '#9CA3AF' },
      present: { quest: '#10B981', service: '#34D399', pledge: '#6EE7B7' },
      future: { quest: '#8B5CF6', service: '#A78BFA', pledge: '#C4B5FD' }
    }
    return colors[node.group][node.type]
  }

  // Link appearance
  const getLinkColor = (link: TrinityLink) => {
    if (link.type === 'evolution') {
      return link.strength && link.strength > 0.7 ? '#FFD700' : '#666666'
    }
    return '#333333'
  }

  const getLinkWidth = (link: TrinityLink) => {
    if (link.type === 'evolution') {
      return 2 + (link.strength || 0.5) * 3
    }
    return 1
  }

  // Create custom node geometry
  const nodeThreeObject = (node: TrinityNode) => {
    const geometry = node.type === 'quest' 
      ? new THREE.OctahedronGeometry(node.size || 10)
      : node.type === 'service'
      ? new THREE.BoxGeometry(node.size || 8, node.size || 8, node.size || 8)
      : new THREE.SphereGeometry(node.size || 6)

    const material = new THREE.MeshPhongMaterial({
      color: getNodeColor(node),
      emissive: getNodeColor(node),
      emissiveIntensity: 0.3,
      shininess: 100
    })

    return new THREE.Mesh(geometry, material)
  }

  // Setup background gradient and particle system
  useEffect(() => {
    if (!graphRef.current) return

    const graph = graphRef.current
    const scene = graph.scene()
    // const camera = graph.camera()
    const renderer = graph.renderer()

    // Create background scene
    bgSceneRef.current = new THREE.Scene()
    bgCameraRef.current = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1)

    // Create gradient background
    const bgGeometry = new THREE.PlaneGeometry(2, 2)
    const bgMaterial = new THREE.ShaderMaterial({
      uniforms: {
        topColor: { value: new THREE.Color('#1a1a2e') },
        bottomColor: { value: new THREE.Color('#16213e') }
      },
      vertexShader: `
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 topColor;
        uniform vec3 bottomColor;
        varying vec2 vUv;
        void main() {
          gl_FragColor = vec4(mix(bottomColor, topColor, vUv.y), 1.0);
        }
      `,
      depthWrite: false
    })
    const bgMesh = new THREE.Mesh(bgGeometry, bgMaterial)
    bgSceneRef.current.add(bgMesh)

    // Create particle system
    const particleCount = 2000
    const positions = new Float32Array(particleCount * 3)
    const colors = new Float32Array(particleCount * 3)
    const sizes = new Float32Array(particleCount)

    for (let i = 0; i < particleCount; i++) {
      const i3 = i * 3
      positions[i3] = (Math.random() - 0.5) * 1000
      positions[i3 + 1] = (Math.random() - 0.5) * 1000
      positions[i3 + 2] = (Math.random() - 0.5) * 1000

      // Color based on z position (temporal)
      const t = (positions[i3 + 2] + 500) / 1000
      colors[i3] = 0.5 + t * 0.5     // R
      colors[i3 + 1] = 0.5           // G
      colors[i3 + 2] = 1 - t * 0.5   // B

      sizes[i] = Math.random() * 2
    }

    const particleGeometry = new THREE.BufferGeometry()
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    particleGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    particleGeometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))

    const particleMaterial = new THREE.PointsMaterial({
      size: 2,
      vertexColors: true,
      blending: THREE.AdditiveBlending,
      transparent: true,
      opacity: 0.6
    })

    particlesRef.current = new THREE.Points(particleGeometry, particleMaterial)
    scene.add(particlesRef.current)

    // Animation loop for particles
    const animate = () => {
      if (particlesRef.current) {
        particlesRef.current.rotation.y += 0.0005
        particlesRef.current.rotation.x += 0.0002
      }
      animationFrameRef.current = requestAnimationFrame(animate)
    }
    animate()

    // Override render to include background
    const originalRender = renderer.render.bind(renderer)
    renderer.render = function(scene: THREE.Scene, camera: THREE.Camera) {
      renderer.autoClear = false
      renderer.clear()
      
      if (bgSceneRef.current && bgCameraRef.current) {
        renderer.render(bgSceneRef.current, bgCameraRef.current)
      }
      
      originalRender(scene, camera)
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (particlesRef.current && scene) {
        scene.remove(particlesRef.current)
      }
    }
  }, [])

  return (
    <div ref={mountRef} className="relative w-full h-full bg-gray-900">
      <ForceGraph3D
        ref={graphRef}
        graphData={{ nodes, links }}
        width={dimensions.width}
        height={dimensions.height}
        backgroundColor="rgba(0,0,0,0)"
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        nodeLabel={(node: any) => `
          <div class="bg-gray-800 p-2 rounded text-white">
            <div class="font-bold">${node.label}</div>
            <div class="text-sm">${node.value?.substring(0, 50) || ''}...</div>
          </div>
        `}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        nodeColor={(node: any) => getNodeColor(node)}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        nodeThreeObject={(node: any) => nodeThreeObject(node)}
        nodeThreeObjectExtend={true}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        linkColor={(link: any) => getLinkColor(link)}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        linkWidth={(link: any) => getLinkWidth(link)}
        linkOpacity={0.8}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        linkDirectionalParticles={(link: any) => link.type === 'evolution' ? 3 : 0}
        linkDirectionalParticleSpeed={0.005}
        linkDirectionalParticleWidth={2}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        linkDirectionalParticleColor={(link: any) => link.strength > 0.7 ? '#FFD700' : '#666666'}
        enableNodeDrag={false}
        enableNavigationControls={true}
        showNavInfo={false}
        cooldownTicks={variant === 'timeline' || variant === 'columns' ? 0 : 100}
      />
      
      {/* Overlay UI */}
      <div className="absolute top-4 left-4 bg-gray-800/80 backdrop-blur p-4 rounded-lg">
        <h3 className="text-white font-bold mb-2">Trinity Evolution</h3>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
            <span className="text-gray-400">Past</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-green-400">Present</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
            <span className="text-purple-400">Future</span>
          </div>
        </div>
        {clarityScore > 0 && (
          <div className="mt-2 text-yellow-400">
            Clarity: {clarityScore}%
          </div>
        )}
      </div>

      {/* Variant selector */}
      <div className="absolute top-4 right-4 bg-gray-800/80 backdrop-blur p-2 rounded-lg">
        <select 
          value={variant}
          onChange={(e) => window.location.href = `?variant=${e.target.value}`}
          className="bg-gray-700 text-white px-3 py-1 rounded"
        >
          <option value="timeline">Timeline</option>
          <option value="spiral">Spiral</option>
          <option value="circular">Circular</option>
          <option value="columns">Columns</option>
        </select>
      </div>
    </div>
  )
}