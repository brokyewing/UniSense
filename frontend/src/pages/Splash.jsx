import { lazy, Suspense } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, Sparkles } from 'lucide-react'
import ThemeToggle from '../components/ThemeToggle'
import Logo from '../components/Logo'
import { TERCIH_YILI } from '../lib/donem'

// 3D sahne büyük — Three.js bundle'ı ayrı chunk'tan lazy yükle (ilk paint hızlansın)
const Scene3D = lazy(() => import('../components/three/Scene3D'))

/**
 * Splash / Giriş ekranı
 * - Tam ekran 3D dönen küre + yıldızlar + yörünge nodes
 * - Logo + slogan + giriş butonu
 * - Glassmorphism overlay
 */
export default function Splash() {
  const nav = useNavigate()

  return (
    <div className="fixed inset-0 overflow-hidden bg-gradient-cyber">
      {/* 3D arkaplan — lazy, ilk paint'i bloklamasın */}
      <div className="absolute inset-0">
        <Suspense fallback={<div className="w-full h-full bg-gradient-cyber" />}>
          <Scene3D />
        </Suspense>
      </div>

      {/* Grid overlay */}
      <div className="absolute inset-0 grid-bg opacity-40 pointer-events-none" />

      {/* Vinyetleme */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/30 pointer-events-none" />

      {/* Sağ üst — logo + tema toggle yan yana */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.5, duration: 0.6 }}
        className="absolute top-6 right-6 z-20 flex items-center gap-3"
      >
        <Logo size={48} rounded="rounded-none" />
        <ThemeToggle />
      </motion.div>

      {/* İçerik */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-6 text-center">
        {/* Başlık */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.4 }}
          className="text-6xl md:text-8xl font-display font-bold mb-3 tracking-tight"
        >
          <span className="gradient-text">UniSense</span>
        </motion.h1>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.6 }}
          className="badge bg-accent-500/20 text-accent-300 border border-accent-500/30 mb-6"
        >
          <Sparkles size={10} />
          {TERCIH_YILI} Tercih Asistanı
        </motion.div>

        {/* Slogan */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.8 }}
          className="text-xl md:text-2xl text-slate-300 max-w-2xl mb-2 leading-relaxed pretty"
        >
          Türkiye'nin tüm üniversitelerinin bilgisi<br className="hidden md:block" />
          <span className="text-cyber-cyan">tek dilde, tek tıkla.</span>
        </motion.p>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1 }}
          className="text-sm text-slate-400 mb-10"
        >
          21.602 program · 227 üniversite · YKS · DGS · KPSS · Güncel resmi veriler
        </motion.p>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 1.2 }}
          className="flex flex-col sm:flex-row gap-3 items-center"
        >
          <button
            onClick={() => nav('/anasayfa')}
            className="btn-primary text-lg px-8 py-4 group flex items-center gap-2"
          >
            Başla
            <ArrowRight
              size={20}
              className="group-hover:translate-x-1 transition-transform"
            />
          </button>
          <button
            onClick={() => nav('/arama')}
            className="btn-ghost text-lg px-8 py-4"
          >
            Direkt Sor →
          </button>
        </motion.div>

        {/* Alt info */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1.2, delay: 1.6 }}
          className="absolute bottom-6 text-xs text-slate-500 flex items-center gap-2"
        >
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          YÖK Atlas + Wikipedia + RAG ile destekleniyor
        </motion.div>
      </div>
    </div>
  )
}
