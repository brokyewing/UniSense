import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import BackgroundScene from '../components/three/LazyBackgroundScene'

export default function Splash() {
  const nav = useNavigate()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setReady(true), 1200)
    return () => clearTimeout(t)
  }, [])

  useEffect(() => {
    if (ready) {
      const t = setTimeout(() => nav('/anasayfa'), 800)
      return () => clearTimeout(t)
    }
  }, [ready, nav])

  return (
    <>
      <BackgroundScene />
      <div className="min-h-screen flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          className="text-center"
        >
          <h1 className="text-4xl font-display font-bold gradient-text">UniSense</h1>
          <p className="text-slate-400 text-sm mt-2">Yükleniyor…</p>
        </motion.div>
      </div>
    </>
  )
}