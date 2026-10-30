import { Canvas, useFrame } from '@react-three/fiber'
import { Stars } from '@react-three/drei'
import { useRef, useMemo, Suspense, useEffect, useState } from 'react'

function useThemeWatcher() {
  const [isLight, setIsLight] = useState(
    () => typeof document !== 'undefined' && document.documentElement.classList.contains('light-theme')
  )
  useEffect(() => {
    const observer = new MutationObserver(() => {
      setIsLight(document.documentElement.classList.contains('light-theme'))
    })
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    return () => observer.disconnect()
  }, [])
  return isLight
}

function FloatingShapes() {
  const ref = useRef()
  const shapes = useMemo(() => {
    return [...Array(15)].map((_, i) => ({
      pos: [
        (Math.random() - 0.5) * 20,
        (Math.random() - 0.5) * 12,
        (Math.random() - 0.5) * 10 - 5,
      ],
      scale: 0.2 + Math.random() * 0.6,
      rotSpeed: 0.1 + Math.random() * 0.4,
      color: ['#3b82f6', '#8b5cf6', '#22d3ee', '#a855f7', '#ec4899'][i % 5],
      kind: i % 3,
    }))
  }, [])

  useFrame((state, delta) => {
    if (ref.current) {
      ref.current.rotation.y += delta * 0.03
    }
  })

  return (
    <group ref={ref}>
      {shapes.map((s, i) => (
        <mesh key={i} position={s.pos} scale={s.scale}>
          {s.kind === 0 && <icosahedronGeometry args={[1, 0]} />}
          {s.kind === 1 && <octahedronGeometry args={[1, 0]} />}
          {s.kind === 2 && <tetrahedronGeometry args={[1, 0]} />}
          <meshStandardMaterial
            color={s.color}
            emissive={s.color}
            emissiveIntensity={0.3}
            wireframe={true}
            transparent
            opacity={0.6}
          />
        </mesh>
      ))}
    </group>
  )
}

export default function BackgroundScene() {
  const isLight = useThemeWatcher()
  return (
    <div
      className="fixed inset-0 -z-10 pointer-events-none transition-opacity duration-500"
      style={{ opacity: isLight ? 0.5 : 1 }}
    >
      <Canvas camera={{ position: [0, 0, 8], fov: 60 }} dpr={[1, 1.5]}>
        <Suspense fallback={null}>
          <ambientLight intensity={isLight ? 0.5 : 0.2} />
          <pointLight position={[10, 10, 10]} intensity={isLight ? 1.2 : 0.8} color="#6366f1" />
          <pointLight position={[-10, -10, -10]} intensity={isLight ? 0.9 : 0.6} color="#a855f7" />
          <Stars
            radius={50}
            depth={50}
            count={isLight ? 600 : 1500}
            factor={isLight ? 1 : 2}
            saturation={0.5}
            fade
            speed={0.3}
          />
          <FloatingShapes />
        </Suspense>
      </Canvas>
    </div>
  )
}
