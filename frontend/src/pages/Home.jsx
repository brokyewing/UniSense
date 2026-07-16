import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Search, ListChecks, Database, Sparkles,
  BookOpen, Compass, Calculator, CalendarDays, ArrowRight,
} from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import { apiFetch } from '../lib/api'
import { TERCIH_YILI } from '../lib/donem'

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

// Ürün özellikleri — sitenin sattığı 6 çekirdek değer
const FEATURES = [
  {
    icon: ListChecks,
    title: 'Tercih Robotları',
    desc: 'Puanını gir → yerleşebileceğin yerler güvenli/hedef/riskli kovalarında. YKS, DGS, KPSS, LGS ve TUS/DUS için ayrı robot.',
    accent: 'from-accent-500 to-cyber-pink',
    to: '/oneriler',
  },
  {
    icon: Calculator,
    title: 'Puan Hesaplama',
    desc: 'Netlerini yaz, yaklaşık puanını anında gör: YKS, DGS, KPSS, ALES, LGS, AGS — resmî kılavuz formüllerine göre.',
    accent: 'from-amber-500 to-orange-500',
    to: '/hesap',
  },
  {
    icon: Compass,
    title: 'İlgi Pusulası',
    desc: 'Ne okuyacağına karar veremiyorsan: ilgilerini seç, yapay zekâ sana uygun bölümleri çıkarsın.',
    accent: 'from-emerald-500 to-cyber-cyan',
    to: '/pusula',
  },
  {
    icon: Search,
    title: 'Akıllı Sorgu',
    desc: '"İTÜ Bilgisayar taban puanı?" yaz, kaynak gösterimli cevabı anında al.',
    accent: 'from-brand-500 to-accent-500',
    to: '/arama',
  },
  {
    icon: BookOpen,
    title: 'Bölüm Rehberi',
    desc: 'Bölüm ne iş yapar, mezunu nerede çalışır? Tanıtımlar + güncel taban puanları.',
    accent: 'from-cyber-cyan to-brand-500',
    to: '/bolum',
  },
  {
    icon: CalendarDays,
    title: 'Sınav Takvimi',
    desc: `Tüm ${TERCIH_YILI} sınav, sonuç ve tercih tarihleri — kaç gün kaldığıyla.`,
    accent: 'from-green-500 to-emerald-500',
    to: '/takvim',
  },
]

// Nasıl çalışır — 3 adım (ürün akışı)
const ADIMLAR = [
  { n: 1, t: 'Puanını veya ilgini gir', d: 'Net hesapla, puanını yaz ya da Pusula ile ilgilerini seç' },
  { n: 2, t: 'Sana uygun listeyi al', d: 'Güvenli / hedef / riskli kovalarında kişisel öneriler' },
  { n: 3, t: 'Tercih listeni kur', d: 'Beğendiklerini kaydet, sırala, indir — tercih gününe hazır ol' },
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
            🎓 {TERCIH_YILI} Tercih Dönemi · YKS · DGS · KPSS · LGS · TUS
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
            Puanını gir, yerleşebileceğin yerleri gör. Lise, üniversite, memurluk ve
            uzmanlık tercihlerinin tamamı — <strong className="text-accent-300">tamamen ücretsiz</strong>.
          </motion.p>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="flex justify-center gap-3 flex-wrap"
          >
            <Link to="/oneriler" className="btn-primary inline-flex items-center gap-2">
              <ListChecks size={18} />
              Tercih Önerisi Al
            </Link>
            <Link to="/hesap" className="btn-ghost inline-flex items-center gap-2">
              <Calculator size={18} />
              Puan Hesapla
            </Link>
          </motion.div>
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
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map((f, i) => (
              <FeatureCard key={i} feat={f} index={i} />
            ))}
          </div>
        </section>

        {/* Nasıl çalışır — 3 adım */}
        <section className="card">
          <h2 className="font-display font-semibold text-lg text-white mb-4 text-center">
            Nasıl çalışır?
          </h2>
          <div className="grid sm:grid-cols-3 gap-4">
            {ADIMLAR.map((a) => (
              <div key={a.n} className="flex gap-3">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-accent-500 text-white flex items-center justify-center text-sm font-display font-bold shrink-0">
                  {a.n}
                </div>
                <div>
                  <div className="text-sm font-semibold text-white">{a.t}</div>
                  <div className="text-xs text-slate-400 mt-0.5">{a.d}</div>
                </div>
              </div>
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

        {/* Güven şeridi — kaynaklar tek satır */}
        <section className="text-center text-xs text-slate-500 flex items-center justify-center gap-2 flex-wrap">
          <Database size={12} className="text-cyber-cyan" />
          <span>Veriler resmî kaynaklardan:</span>
          <strong className="text-slate-300">YÖK Atlas</strong>
          <span className="text-slate-700">·</span>
          <strong className="text-slate-300">ÖSYM</strong>
          <span className="text-slate-700">·</span>
          <strong className="text-slate-300">MEB</strong>
          <span className="text-slate-700">·</span>
          <span className="text-emerald-400 font-medium">%100 ücretsiz — üyelik zorunlu değil</span>
        </section>
      </div>
    </>
  )
}
