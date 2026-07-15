import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Search, ListChecks, Database, Sparkles, GraduationCap,
  Building2, BookOpen, MapPin, Zap, Compass, CalendarDays, ArrowRight,
} from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import { apiFetch } from '../lib/api'

// Yaklaşan sınavlar widget'ı — /takvim'den ilk 3 etkinlik
function UpcomingExams() {
  const [items, setItems] = useState(null)
  useEffect(() => {
    apiFetch('/api/v1/takvim').then((d) => setItems(d.yaklasan?.slice(0, 3) || [])).catch(() => setItems([]))
  }, [])
  if (!items || items.length === 0) return null
  const TUR = { sinav: 'Sınav', sonuc: 'Sonuç', tercih: 'Tercih', yerlestirme: 'Yerleştirme' }
  return (
    <Link to="/takvim" className="card glass-hover block group">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-display font-semibold text-lg text-white flex items-center gap-2">
          <CalendarDays size={18} className="text-accent-300" /> Yaklaşan Sınavlar
        </h2>
        <span className="text-xs text-accent-300 inline-flex items-center gap-1 group-hover:gap-2 transition-all">
          Tüm takvim <ArrowRight size={12} />
        </span>
      </div>
      <div className="grid sm:grid-cols-3 gap-2">
        {items.map((e) => (
          <div key={e.id} className="rounded-xl bg-white/5 border border-white/10 px-3 py-2">
            <div className="flex items-baseline justify-between">
              <span className="font-display font-bold text-white">{e.sinav}</span>
              <span className={`text-xs font-semibold ${e.devam ? 'text-emerald-300' : e.kalan_gun <= 7 ? 'text-rose-300' : 'text-amber-300'}`}>
                {e.devam ? 'Sürüyor' : e.kalan_gun === 0 ? 'Bugün' : `${e.kalan_gun} gün`}
              </span>
            </div>
            <div className="text-[11px] text-slate-400">{TUR[e.tur] || e.tur}</div>
          </div>
        ))}
      </div>
    </Link>
  )
}

const STATS = [
  { value: '227', label: 'Üniversite', icon: Building2, color: 'from-brand-500 to-cyber-cyan' },
  { value: '21.602', label: 'Program', icon: BookOpen, color: 'from-accent-500 to-cyber-pink', sub: 'Lisans + Önlisans' },
  { value: '3.061', label: 'Fakülte / MYO', icon: GraduationCap, color: 'from-cyber-cyan to-emerald-400' },
  { value: '7', label: 'Bölge', icon: MapPin, color: 'from-amber-400 to-orange-500' },
]

const FEATURES = [
  {
    icon: Compass,
    title: 'İlgi Pusulası',
    desc: 'Hangi bölüm sana uygun bilmiyorsan: kart seç, yazı yaz, ya da 5 soru cevapla.',
    accent: 'from-emerald-500 to-cyber-cyan',
    to: '/pusula',
    badge: 'YENİ',
  },
  {
    icon: Search,
    title: 'Doğal Dil Sorgu',
    desc: '"İTÜ Bilgisayar Müh taban puanı?" yaz, anında cevap al.',
    accent: 'from-brand-500 to-accent-500',
    to: '/arama',
  },
  {
    icon: ListChecks,
    title: 'Tercih Önerme',
    desc: 'Puanın ve sıralamana göre güvenli/hedef/üst seviye 30 tercih.',
    accent: 'from-accent-500 to-cyber-pink',
    to: '/oneriler',
  },
  {
    icon: BookOpen,
    title: 'Bölüm Rehberi',
    desc: 'Bölüm ne iş yapar, hangi dersleri okur, mezunu nerede çalışır? 79 bölüm tanıtımı + güncel taban puanları.',
    accent: 'from-cyber-cyan to-brand-500',
    to: '/bolum',
  },
]

const SAMPLE_QUERIES = [
  'Bilgisayar Mühendisliği taban puanları',
  'İskenderun Teknik Üniversitesi bölümleri',
  'Denizcilik fakültesi olan üniversiteler',
  '300.000 sıralamayla hangi üniversiteler',
  'Boğaziçi Üniversitesi tüm bölümler',
  'İngilizce hazırlık olan EA bölümleri',
  'Vakıf üniversitelerinde tıp bursları',
  'KKTC üniversiteleri lisans programları',
]


function StatCard({ stat, index }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 * index }}
      className="card relative overflow-hidden group"
    >
      <div
        className={`absolute -top-10 -right-10 w-32 h-32 rounded-full opacity-30
                    blur-2xl bg-gradient-to-br ${stat.color} group-hover:opacity-50 transition-opacity`}
      />
      <div className="relative">
        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center mb-3 shadow-lg`}>
          <stat.icon size={20} className="text-white" />
        </div>
        <div className="text-3xl font-display font-bold text-white">{stat.value}</div>
        <div className="text-sm text-slate-400 mt-1">{stat.label}</div>
        {stat.sub && (
          <div className="text-[10px] text-slate-500 mt-0.5">{stat.sub}</div>
        )}
      </div>
    </motion.div>
  )
}

function FeatureCard({ feat, index }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.15 * index }}
    >
      <Link
        to={feat.to}
        className="card glass-hover relative overflow-hidden group block h-full"
      >
        <div
          className={`absolute -top-16 -right-16 w-48 h-48 rounded-full opacity-20
                      blur-3xl bg-gradient-to-br ${feat.accent} group-hover:opacity-40 transition-opacity duration-500`}
        />
        <div className="relative">
          <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${feat.accent} flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 transition-transform`}>
            <feat.icon size={22} className="text-white" />
          </div>
          <div className="flex items-center gap-2 mb-2">
            <h3 className="font-display font-semibold text-xl text-white">
              {feat.title}
            </h3>
            {feat.badge && (
              <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold tracking-wider">
                {feat.badge}
              </span>
            )}
          </div>
          <p className="text-slate-400 text-sm leading-relaxed">{feat.desc}</p>
          <div className="mt-4 flex items-center gap-1 text-xs text-accent-300 group-hover:gap-2 transition-all">
            Devam et <span className="group-hover:translate-x-1 transition-transform inline-block">→</span>
          </div>
        </div>
      </Link>
    </motion.div>
  )
}

export default function Home() {
  return (
    <>
      <BackgroundScene />

      <div className="space-y-12">
        {/* Hero */}
        <section className="text-center pt-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent-500/10 border border-accent-500/30 text-accent-300 text-xs font-medium mb-6 backdrop-blur-xl"
          >
            <span className="w-2 h-2 rounded-full bg-accent-500 animate-pulse" />
            🎓 2026 Tercih Dönemi · YKS · DGS · KPSS
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="text-5xl md:text-7xl font-display font-bold mb-4 tracking-tight text-white text-balance"
          >
            Doğru tercihi{' '}
            <span className="gradient-text">veri</span>{' '}
            ile yap
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="text-lg md:text-xl text-slate-300 max-w-2xl mx-auto mb-8 leading-relaxed pretty"
          >
            Türkiye'nin tüm üniversite ve bölümlerine ait sıralama, taban puan,
            kontenjan bilgilerini sor; AI destekli öneri al.
          </motion.p>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="flex justify-center gap-3 flex-wrap"
          >
            <Link to="/arama" className="btn-primary inline-flex items-center gap-2">
              <Search size={18} />
              Sorgu Başlat
            </Link>
            <Link to="/oneriler" className="btn-ghost inline-flex items-center gap-2">
              <ListChecks size={18} />
              Tercih Önerisi
            </Link>
          </motion.div>
        </section>

        {/* İstatistikler */}
        <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {STATS.map((s, i) => (
            <StatCard key={i} stat={s} index={i} />
          ))}
        </section>

        {/* Yaklaşan sınavlar */}
        <section>
          <UpcomingExams />
        </section>

        {/* Özellikler */}
        <section>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-2xl font-display font-semibold text-white mb-4"
          >
            Ne yapabilirim?
          </motion.h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {FEATURES.map((f, i) => (
              <FeatureCard key={i} feat={f} index={i} />
            ))}
          </div>
        </section>

        {/* Örnek sorgular */}
        <section className="card">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles size={18} className="text-amber-400" />
            <h2 className="font-display font-semibold text-lg text-white">Örnek Sorgular</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-2">
            {SAMPLE_QUERIES.map((q, i) => (
              <Link
                key={i}
                to={`/arama?q=${encodeURIComponent(q)}`}
                className="group px-4 py-3 rounded-xl bg-white/[0.02] hover:bg-accent-500/10 hover:border-accent-500/30 border border-white/5 text-sm text-slate-300 hover:text-white transition-all flex items-center gap-3"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-accent-500/50 group-hover:bg-accent-400 group-hover:scale-150 transition-all" />
                {q}
              </Link>
            ))}
          </div>
        </section>

        {/* Veri kaynakları */}
        <section className="card">
          <div className="flex items-center gap-2 mb-3">
            <Database size={18} className="text-cyber-cyan" />
            <h2 className="font-display font-semibold text-lg text-white">Veri Kaynaklarımız</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-3 text-sm">
            <div className="flex items-center gap-2 text-slate-300">
              <Zap size={14} className="text-amber-400" />
              <strong>YÖK Atlas</strong>
              <span className="text-slate-500">— 12.265 program</span>
            </div>
            <div className="flex items-center gap-2 text-slate-300">
              <Zap size={14} className="text-emerald-400" />
              <strong>Wikipedia TR</strong>
              <span className="text-slate-500">— 200+ üni tanımı</span>
            </div>
            <div className="flex items-center gap-2 text-slate-300">
              <Zap size={14} className="text-pink-400" />
              <strong>ÖSYM 2025</strong>
              <span className="text-slate-500">— resmi yerleştirme</span>
            </div>
          </div>
        </section>
      </div>
    </>
  )
}
