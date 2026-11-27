import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Search, ListChecks, Database, Sparkles,
  BookOpen, Compass, Calculator, CalendarDays, ArrowRight, ShieldCheck,
} from 'lucide-react'
import BackgroundScene from '../components/three/LazyBackgroundScene'
import PersonalAICoach, { type PersonalCoachMeta } from '../components/PersonalAICoach'
import StreakBadge from '../components/StreakBadge'
import { useAuth } from '../contexts/AuthContext'
import { apiFetch } from '../lib/api'
import { TERCIH_YILI } from '../lib/donem'

// Yaklaşan sınavlar widget'ı — /takvim'den ilk 3 etkinlik
function UpcomingExams() {
  const [items, setItems] = useState<any[] | null>(null)
  useEffect(() => {
    let cancelled = false
    apiFetch('/api/v1/takvim')
      .then((d) => { if (!cancelled) setItems(d.yaklasan?.slice(0, 3) || []) })
      .catch(() => { if (!cancelled) setItems([]) })
    return () => { cancelled = true }
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
            <div className="text-[11px] text-slate-400">{(TUR as any)[e.tur] || e.tur}</div>
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
  'Bilgisayar Mühendisliği taban puanları ve sıralamaları',
  '50.000 sayısal sıralamayla hangi üniversiteye girebilirim?',
  'Vakıf üniversitelerinde burslu tıp taban puanları',
  '2 yıllık önlisans bölümlerinden DGS geçiş bölümleri',
  'Boğaziçi ve ODTÜ mühendislik taban sıralamaları',
  'İngilizce eğitim veren eşit ağırlık (EA) bölümleri',
  'KPSS lisans merkezi atama taban puanları ve kadrolar',
  'Devlet üniversiteleri hemşirelik ve hukuk kontenjanları',
]


function FeatureCard({ feat, index }: { feat: any; index: number }) {
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
  const navigate = useNavigate()
  const { user } = useAuth()
  const [quickType, setQuickType] = useState('SAY')
  const [quickRank, setQuickRank] = useState('')
  const [showShowcase, setShowShowcase] = useState(false)
  const [personalMeta, setPersonalMeta] = useState<PersonalCoachMeta>({
    ready: false,
    isPersonalized: false,
    firstName: '',
    track: 'YKS',
    hedefBolum: '',
  })
  const handlePersonalChange = useCallback((meta: PersonalCoachMeta) => {
    setPersonalMeta((prev) => (
      prev.ready === meta.ready &&
      prev.isPersonalized === meta.isPersonalized &&
      prev.firstName === meta.firstName &&
      prev.track === meta.track &&
      prev.hedefBolum === meta.hedefBolum
        ? prev
        : meta
    ))
  }, [])
  const hasLocalStreak = (() => {
    try { return Boolean(localStorage.getItem('unisense_streak')) } catch { return false }
  })()

  function onQuickSearch(e: React.FormEvent) {
    e.preventDefault()
    const cleanRank = quickRank.replace(/[^0-9]/g, '')
    if (!cleanRank) {
      navigate('/oneriler')
      return
    }
    navigate(`/oneriler?tur=${encodeURIComponent(quickType)}&sira=${encodeURIComponent(cleanRank)}`)
  }

  const showPersonalizedHero = personalMeta.isPersonalized && !showShowcase

  return (
    <>
      <BackgroundScene />

      <div className="space-y-12">
        {showPersonalizedHero ? (
          <section className="pt-4 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-500/10 border border-accent-500/30 text-accent-300 text-xs font-medium mb-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  ✨ Kişisel AI Çalışma &amp; Tercih Ekranın · {personalMeta.track}
                  {personalMeta.hedefBolum && <> · Hedef: {personalMeta.hedefBolum}</>}
                </div>
                <h1 className="text-3xl md:text-5xl font-display font-bold tracking-tight text-white text-balance">
                  {personalMeta.firstName ? `${personalMeta.firstName}, ` : ''}Bugünkü{' '}
                  <span className="gradient-text">{personalMeta.track}</span>{' '}
                  AI Alanın
                </h1>
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                <Link to="/arama" className="btn-primary text-xs px-3.5 py-2 inline-flex items-center gap-1.5">
                  <Sparkles size={14} /> AI Sohbet
                </Link>
                <button
                  type="button"
                  onClick={() => setShowShowcase(true)}
                  className="btn-ghost text-xs px-3 py-2"
                >
                  Genel Vitrin
                </button>
              </div>
            </div>
          </section>
        ) : (
          <section className="text-center pt-6">
            <div className="flex justify-center items-center gap-2 flex-wrap mb-6">
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent-500/10 border border-accent-500/30 text-accent-300 text-xs font-medium backdrop-blur-xl">
                <span className="w-2 h-2 rounded-full bg-accent-500 animate-pulse" />
                🎓 {TERCIH_YILI} Tercih Dönemi · YKS · DGS · KPSS · LGS · TUS
              </div>
              {personalMeta.isPersonalized && (
                <button
                  type="button"
                  onClick={() => setShowShowcase(false)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-semibold hover:bg-emerald-500/25 transition"
                >
                  <Sparkles size={12} /> Kişisel AI Ekranıma Dön
                </button>
              )}
            </div>

            <h1 className="text-5xl md:text-7xl font-display font-bold mb-4 tracking-tight text-white text-balance">
              Doğru tercihi{' '}
              <span className="gradient-text">veri</span>{' '}
              ile yap
            </h1>

            <p className="text-lg md:text-xl text-slate-300 max-w-2xl mx-auto mb-6 leading-relaxed pretty">
              Puanını veya sıralamanı gir, yerleşebileceğin yerleri gör. Lise, üniversite, memurluk ve
              uzmanlık tercihlerinin tamamı — <strong className="text-accent-300">tamamen ücretsiz</strong>.
            </p>

            {/* Hero hızlı sıralama aracı — 10 sn içinde değer */}
            <form
              onSubmit={onQuickSearch}
              className="max-w-xl mx-auto mb-5 p-2 rounded-2xl card border-accent-500/25 flex flex-col sm:flex-row gap-2"
            >
              <select
                aria-label="YKS puan türü"
                value={quickType}
                onChange={(e) => setQuickType(e.target.value)}
                className="input-glass sm:w-28 text-sm font-semibold"
              >
                {['SAY', 'EA', 'SÖZ', 'DİL', 'TYT'].map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
              <input
                type="number"
                min={1}
                aria-label="Başarı sıralaman"
                value={quickRank}
                onChange={(e) => setQuickRank(e.target.value)}
                placeholder="Başarı sıralaman (ör: 50000)"
                className="input-glass flex-1 text-sm"
              />
              <button type="submit" className="btn-primary text-sm px-5 py-2.5 shrink-0 inline-flex items-center justify-center gap-1.5">
                Bölümleri Gör <ArrowRight size={15} />
              </button>
            </form>

            <div className="flex justify-center gap-3 flex-wrap mb-4">
              <Link to="/oneriler" className="btn-primary inline-flex items-center gap-2">
                <ListChecks size={18} />
                Tercih Önerisi Al
              </Link>
              <Link to="/hesap" className="btn-ghost inline-flex items-center gap-2">
                <Calculator size={18} />
                Puan Hesapla
              </Link>
            </div>

            {/* Above-the-fold güven şeridi */}
            <div className="inline-flex items-center justify-center gap-2 flex-wrap text-xs text-slate-400">
              <ShieldCheck size={14} className="text-emerald-400 shrink-0" />
              <span className="text-emerald-300 font-medium">%100 Ücretsiz · Üyelik Zorunlu Değil</span>
              <span className="text-slate-700">·</span>
              <span>600+ Bölüm · Resmi YÖK Atlas, ÖSYM &amp; MEB Verisi ({TERCIH_YILI})</span>
            </div>
          </section>
        )}

        {/* Tek sabit PersonalAICoach örneği — mod geçişinde yeniden mount edilmez */}
        <section>
          <PersonalAICoach onPersonalStateChange={handlePersonalChange} hideHeaderTitle={showPersonalizedHero} />
        </section>

        {showPersonalizedHero && (
          <section className="card !p-4">
            <form onSubmit={onQuickSearch} className="flex flex-col sm:flex-row gap-2 items-stretch sm:items-center">
              <span className="text-xs font-semibold text-slate-300 px-1 shrink-0">Hızlı Tercih Robotu:</span>
              <select
                aria-label="YKS puan türü"
                value={quickType}
                onChange={(e) => setQuickType(e.target.value)}
                className="input-glass sm:w-24 text-xs font-semibold"
              >
                {['SAY', 'EA', 'SÖZ', 'DİL', 'TYT'].map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
              <input
                type="number"
                min={1}
                aria-label="Başarı sıralaman"
                value={quickRank}
                onChange={(e) => setQuickRank(e.target.value)}
                placeholder="Başarı sıralaman (ör: 50000)"
                className="input-glass flex-1 text-xs"
              />
              <button type="submit" className="btn-primary text-xs px-4 py-2 shrink-0 inline-flex items-center justify-center gap-1.5">
                Bölümleri Gör <ArrowRight size={14} />
              </button>
            </form>
          </section>
        )}

        {/* Günlük çalışma serisi — yalnızca girişli veya geçmişi olan kullanıcıda göster */}
        {(user || hasLocalStreak) && (
          <section>
            <StreakBadge />
          </section>
        )}

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
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 3xl:grid-cols-4 gap-4">
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

        {/* Güven şeridi — doğrulanabilir resmî kaynak bağlantıları */}
        <section className="text-center text-xs text-slate-500 flex items-center justify-center gap-2 flex-wrap">
          <Database size={12} className="text-cyber-cyan" />
          <span>Resmî kaynaklar ({TERCIH_YILI} dönemi):</span>
          <a href="https://yokatlas.yok.gov.tr" target="_blank" rel="noopener noreferrer" className="text-slate-300 font-semibold hover:text-accent-300 hover:underline">
            YÖK Atlas
          </a>
          <span className="text-slate-700">·</span>
          <a href="https://www.osym.gov.tr" target="_blank" rel="noopener noreferrer" className="text-slate-300 font-semibold hover:text-accent-300 hover:underline">
            ÖSYM
          </a>
          <span className="text-slate-700">·</span>
          <a href="https://www.meb.gov.tr" target="_blank" rel="noopener noreferrer" className="text-slate-300 font-semibold hover:text-accent-300 hover:underline">
            MEB
          </a>
          <span className="text-slate-700">·</span>
          <span className="text-emerald-400 font-medium">%100 ücretsiz — üyelik zorunlu değil</span>
        </section>
      </div>
    </>
  )
}
