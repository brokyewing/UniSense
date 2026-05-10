import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Stars, Sphere, Float, Trail, MeshDistortMaterial } from '@react-three/drei'
import { Suspense, useRef, useMemo } from 'react'
import * as THREE from 'three'

/**
 * Ana 3D sahne — UniSense splash + ana sayfa için
 * - Yıldızlı uzay
 * - Yörüngede dönen küre
 * - Yumuşak distortion + neon ışık
 */

function KnowledgeSphere({ position = [0, 0, 0], color = '#8b5cf6', scale = 1 }) {
  const ref = useRef()
  useFrame((state, delta) => {
    if (ref.current) {
      ref.current.rotation.y += delta * 0.15
      ref.current.rotation.x += delta * 0.05
    }
  })
  return (
    <Float speed={2} rotationIntensity={0.5} floatIntensity={1.5}>
      <Sphere ref={ref} args={[1, 64, 64]} position={position} scale={scale}>
        <MeshDistortMaterial
          color={color}
          attach="material"
          distort={0.45}
          speed={1.5}
          roughness={0.1}
          metalness={0.8}
          emissive={color}
          emissiveIntensity={0.3}
        />
      </Sphere>
    </Float>
  )
}

function OrbitingNode({ radius = 3, speed = 0.5, size = 0.15, color = '#22d3ee', startAngle = 0 }) {
  const ref = useRef()
  useFrame((state) => {
    const t = state.clock.elapsedTime * speed + startAngle
    if (ref.current) {
      ref.current.position.x = Math.cos(t) * radius
      ref.current.position.z = Math.sin(t) * radius
      ref.current.position.y = Math.sin(t * 2) * 0.3
    }
  })
  return (
    <Trail width={0.5} length={8} color={color} attenuation={(t) => t * t}>
      <mesh ref={ref}>
        <sphereGeometry args={[size, 24, 24]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={2}
          toneMapped={false}
        />
      </mesh>
    </Trail>
  )
}

function ParticleField({ count = 800 }) {
  const meshRef = useRef()
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      const r = 8 + Math.random() * 12
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta)
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta)
      pos[i * 3 + 2] = r * Math.cos(phi)
    }
    return pos
  }, [count])

  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.02
    }
  })

  return (
    <points ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={positions.length / 3}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial size={0.04} color="#a78bfa" transparent opacity={0.8} />
    </points>
  )
}

export default function Scene3D({ camera = { position: [0, 0, 6], fov: 50 } }) {
  return (
    <Canvas camera={camera} dpr={[1, 2]}>
      <Suspense fallback={null}>
        <ambientLight intensity={0.3} />
        <pointLight position={[10, 10, 10]} intensity={1.2} color="#3b82f6" />
        <pointLight position={[-10, -10, -10]} intensity={0.8} color="#a855f7" />
        <pointLight position={[0, 5, 0]} intensity={0.5} color="#22d3ee" />

        <Stars radius={50} depth={50} count={2500} factor={3} saturation={0.5} fade speed={0.5} />
        <ParticleField count={400} />

        <KnowledgeSphere position={[0, 0, 0]} color="#6366f1" scale={1.2} />

        <OrbitingNode radius={2.5} speed={0.5} startAngle={0} color="#22d3ee" />
        <OrbitingNode radius={2.8} speed={0.3} startAngle={Math.PI / 2} color="#a855f7" />
        <OrbitingNode radius={2.2} speed={0.7} startAngle={Math.PI} color="#ec4899" />
        <OrbitingNode radius={3.0} speed={0.4} startAngle={Math.PI * 1.5} color="#22d3ee" size={0.1} />

        <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.4} />
      </Suspense>
    </Canvas>
  )
}
