"use client"

import React, { useRef, useMemo } from "react"
import { Canvas, useFrame } from "@react-three/fiber"
import * as THREE from "three"

function mulberry32(seed: number) {
  return () => {
    let t = (seed += 0x6D2B79F5)
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const Particles = ({ count = 2000 }: { count?: number }) => {
  const points = useRef<THREE.Points>(null!)

  // Generate 2,000 random particles in a sphere shape
  const particles = useMemo(() => {
    const rand = mulberry32(1337)
    const positions = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      const r = 20 * Math.pow(rand(), 1 / 3) // Distribute within a sphere
      const theta = rand() * 2 * Math.PI
      const phi = Math.acos(2 * rand() - 1)
      
      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta)
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta)
      positions[i * 3 + 2] = r * Math.cos(phi)
    }
    return positions
  }, [count])

  useFrame((state) => {
    if (!points.current) return
    const time = state.clock.getElapsedTime()
    // Slowly rotate the entire point cloud on Y and X axes
    points.current.rotation.y = time * 0.05
    points.current.rotation.x = time * 0.03
  })

  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          // `react-three/fiber` expects `args` for BufferAttribute: [array, itemSize]
          args={[particles, 3]}
          count={particles.length / 3}
          array={particles}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.15}
        color="#d4af37" // Glowing yellow/gold
        transparent
        opacity={0.8}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
      />
    </points>
  )
}

export const ParticleBackground: React.FC = () => {
  return (
    // Background only: rely on the parent container for z-index/positioning.
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      <Canvas
        camera={{ position: [0, 0, 30], fov: 60 }}
        gl={{ alpha: true, antialias: true, powerPreference: "high-performance" }}
        style={{ background: "transparent", width: "100%", height: "100%" }}
      >
        <ambientLight intensity={1} />
        <Particles />
      </Canvas>
    </div>
  )
}
