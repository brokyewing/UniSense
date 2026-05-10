import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Loader2, ListChecks, Target, ShieldCheck, Mountain,
  TrendingUp, Building2, MapPin, UserCog, Sparkles,
  Compass, X, ArrowRight, Check, Plus,
} from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import { useAuth } from '../contexts/AuthContext'
import { getUserProfile, addToTercih, removeFromTercih, watchTercihList } from '../firebase'

const API_BASE = import.meta.env.VITE_API_URL || ''
const API_URL = `${API_BASE}/api/v1/recommend`

const SCORE_TYPES = [
  { v: 'SAY', label: 'Sayısal', color: 'from-blue-500 to-cyan-400' },
  { v: 'EA', label: 'Eşit Ağırlık', color: 'from-emerald-500 to-teal-400' },
  { v: 'SÖZ', label: 'Sözel', color: 'from-rose-500 to-pink-400' },
  { v: 'DİL', label: 'Yabancı Dil', color: 'from-amber-500 to-orange-400' },
  { v: 'TYT', label: 'TYT', color: 'from-purple-500 to-violet-400' },
]

const CATEGORIES = [
  {
    key: 'safe',
    label: 'Güvenli',
    icon: ShieldCheck,
    color: 'from-emerald-500 to-emerald-700',
    desc: 'Garanti yerleşeceğin tercihler',
  },
  {
    key: 'target',
    label: 'Hedef',
    icon: Target,
    color: 'from-amber-500 to-orange-600',
    desc: 'Puanına en uygun tercihler',
  },
  {
    key: 'reach',
    label: 'Üst Seviye',
    icon: Mountain,
    color: 'from-rose-500 to-fuchsia-600',
    desc: 'Hedef üstü, denemeye değer',
  },
]


function ScoreTypePicker({ value, onChange }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
      {SCORE_TYPES.map((s) => {
        const active = value === s.v
        return (
          <button
            key={s.v}
            type="button"
            onClick={() => onChange(s.v)}
            className={`
              relative px-3 py-3 rounded-xl text-sm font-medium transition-all
              ${active
                ? `bg-gradient-to-br ${s.color} text-white shadow-lg`
                : 'glass glass-hover text-slate-300'
              }
            `}
          >
            <div className="font-display font-bold text-lg">{s.v}</div>
            <div className={`text-[10px] ${active ? 'text-white/80' : 'text-slate-500'}`}>
              {s.label}
            </div>
          </button>
        )
      })}
    </div>
  )
}

function ItemCard({ item, isInTercih, onAdd, onRemove, busyCode }) {
  const code = String(item.department_code)
  const busy = busyCode === code
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="card glass-hover p-4 group"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-white text-base truncate">
            {item.department_name}
          </h4>
          <div className="flex items-center gap-2 mt-1 text-xs text-slate-400 flex-wrap">
            <span className="flex items-center gap-1">
              <Building2 size={11} />
              {item.university_name}
            </span>
            {item.city && (
              <span className="flex items-center gap-1">
                <MapPin size={11} /> {item.city}
              </span>
            )}
          </div>
        </div>
        {item.fit_score != null && (
          <div className="text-right shrink-0">
            <div className="text-xs text-slate-500">Uygunluk</div>
            <div className="font-display font-bold text-lg text-accent-300">
              %{item.fit_score.toFixed(0)}
            </div>
          </div>
        )}
      </div>

      {(item.last_year_base_rank || item.last_year_base_score) && (
        <div className="mt-3 pt-3 border-t border-white/5 flex items-center gap-4 text-xs">
          {item.last_year_base_rank && (
            <div>
              <div className="text-slate-500">Sıra</div>
              <div className="font-mono text-cyber-cyan">
                {item.last_year_base_rank.toLocaleString('tr')}
              </div>
            </div>
          )}
          {item.last_year_base_score && (
            <div>
              <div className="text-slate-500">Taban</div>
              <div className="font-mono text-accent-300">
                {item.last_year_base_score.toFixed(2)}
              </div>
            </div>
          )}
        </div>
      )}

      {item.reason && (
        <p className="mt-2 text-xs text-slate-400 italic">{item.reason}</p>
      )}

      {(onAdd || onRemove) && (
        <div className="mt-3 pt-3 border-t border-white/5">
          {isInTercih ? (
            <button
              onClick={() => onRemove?.(item)}
              disabled={busy}
              title="Tercih listesinden çıkar"
              className="group/btn text-xs px-2.5 py-1.5 rounded-lg bg-emerald-500/15 hover:bg-rose-500/20 text-emerald-300 hover:text-rose-200 border border-emerald-500/30 hover:border-rose-500/40 transition inline-flex items-center gap-1 disabled:opacity-40"
            >
              {busy ? (
                <>
                  <Loader2 size={11} className="animate-spin" /> çıkartılıyor…
                </>
              ) : (
                <>
                  <Check size={12} className="group-hover/btn:hidden" />
                  <X size={12} className="hidden group-hover/btn:inline" />
                  <span className="group-hover/btn:hidden">Tercih Listemde</span>
                  <span className="hidden group-hover/btn:inline">Listeden Çıkar</span>
                </>
              )}
            </button>
          ) : (
            <button
              onClick={() => onAdd?.(item)}
              disabled={busy}
              className="text-xs px-2.5 py-1.5 rounded-lg bg-accent-500/20 hover:bg-accent-500/40 text-accent-200 hover:text-white border border-accent-500/30 transition inline-flex items-center gap-1 disabled:opacity-40"
            >
              {busy ? <Loader2 size={11} className="animate-spin" /> : <Plus size={12} />}
              Tercih Listeme Ekle
            </button>
          )}
        </div>
      )}
    </motion.div>
  )
}

// === Pusula yapılmamışsa engel ekran ===
function PusulaGate() {
  const navigate = useNavigate()
  return (
    <>
      <BackgroundScene />
      <div className="max-w-2xl mx-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          className="card text-center py-10 px-6 border-accent-500/30 bg-gradient-to-br from-accent-500/5 to-emerald-500/5"
        >
          <motion.div
            initial={{ rotate: -10, scale: 0.8 }}
            animate={{ rotate: 0, scale: 1 }}
            transition={{ type: 'spring', stiffness: 200 }}
            className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-brand-500 via-accent-500 to-cyber-pink flex items-center justify-center shadow-2xl shadow-accent-500/30"
          >
            <Compass size={40} className="text-white" />
          </motion.div>

          <h2 className="text-2xl md:text-3xl font-display font-bold text-white mb-3">
            Önce <span className="gradient-text">İlgilerini Seç</span>
          </h2>

          <p className="text-slate-300 mb-2 max-w-lg mx-auto leading-relaxed">
            Tercih önerisi alabilmek için önce <strong className="text-accent-300">İlgi Pusulası</strong>'ndan
            ilgilendiğin alanları belirlemelisin.
          </p>
          <p className="text-sm text-slate-400 mb-8 max-w-lg mx-auto">
            Sadece puanla değil, <strong className="text-emerald-300">karakterine ve ilgilerine uyan</strong> bölümleri öneriyoruz.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => navigate('/pusula')}
              className="btn-primary px-6 py-3 inline-flex items-center justify-center gap-2"
            >
              <Compass size={18} />
              Pusulaya Git
              <ArrowRight size={16} />
            </button>
            <Link to="/search" className="btn-ghost px-6 py-3">
              Yine de aramak istiyorum →
            </Link>
          </div>

          {/* Nasıl çalışır mini özet */}
          <div className="mt-10 pt-6 border-t border-white/5 text-left grid sm:grid-cols-3 gap-4">
            {[
              { n: 1, t: 'İlgilerini seç', d: 'Hasta bakımı, yazılım, tasarım gibi konuları işaretle' },
              { n: 2, t: 'Bölüm öneri al', d: 'Sana uygun 15 bölüm listesi otomatik çıkar' },
              { n: 3, t: 'Tercihi yap', d: 'Puanına uygun program kovaları (güvenli/hedef/üst)' },
            ].map((step) => (
              <div key={step.n} className="flex gap-2">
                <div className="w-7 h-7 rounded-full bg-accent-500/20 text-accent-300 flex items-center justify-center text-xs font-bold shrink-0">
                  {step.n}
                </div>
                <div>
                  <div className="text-sm font-medium text-white">{step.t}</div>
                  <div className="text-xs text-slate-400 mt-0.5 leading-relaxed">{step.d}</div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </>
  )
}


export default function Recommend() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [scoreType, setScoreType] = useState('SAY')
  const [score, setScore] = useState('')
  const [rank, setRank] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [profileLoaded, setProfileLoaded] = useState(false)
  const [autofilled, setAutofilled] = useState(false)
  const [pusulaState, setPusulaState] = useState(null)  // {names, mode, timestamp}
  const [tercihIds, setTercihIds] = useState(new Set())
  const [busyCode, setBusyCode] = useState(null)
  const [tercihError, setTercihError] = useState('')
  const [uniType, setUniType] = useState('all')  // 'all' | 'Devlet' | 'Vakıf'

  // Pusula sonucunu sessionStorage'tan oku
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem('pusula_depts')
      if (raw) {
        const parsed = JSON.parse(raw)
        if (parsed?.names?.length) {
          setPusulaState(parsed)
        }
      }
    } catch (e) {
      console.warn('Pusula state okunamadı:', e)
    }
  }, [])

  // Tercih listesini canlı izle (hangi programlar zaten ekli?)
  useEffect(() => {
    if (!user) {
      setTercihIds(new Set())
      return
    }
    const unsub = watchTercihList(user.uid, (items) => {
      setTercihIds(new Set(items.map((i) => String(i.department_code || i.id))))
    })
    return unsub
  }, [user])

  async function handleAddToTercih(item) {
    if (!user) {
      setTercihError('Tercih listesine eklemek için giriş yap')
      return
    }
    if (tercihIds.size >= 24) {
      setTercihError('Tercih listesi 24 dolu — önce birkaç tane çıkar')
      return
    }
    const code = String(item.department_code)
    setBusyCode(code)
    setTercihError('')
    try {
      await addToTercih(user.uid, item, tercihIds.size + 1)
    } catch (e) {
      setTercihError(e.message || 'Eklenemedi')
    } finally {
      setBusyCode(null)
    }
  }

  async function handleRemoveFromTercih(item) {
    if (!user) return
    const code = String(item.department_code)
    setBusyCode(code)
    setTercihError('')
    try {
      await removeFromTercih(user.uid, code)
    } catch (e) {
      setTercihError(e.message || 'Listeden çıkartılamadı')
    } finally {
      setBusyCode(null)
    }
  }

  // Profilden puan/sıra otomatik doldur
  useEffect(() => {
    let cancelled = false
    if (!user) {
      setProfileLoaded(true)
      return
    }
    ;(async () => {
      try {
        const data = await getUserProfile(user.uid)
        if (cancelled) return
        const p = data?.profile
        if (p) {
          let filled = false
          if (p.scoreType) {
            setScoreType(p.scoreType)
            filled = true
          }
          if (p.score != null && p.score !== '') {
            setScore(String(p.score))
            filled = true
          }
          if (p.rank != null && p.rank !== '') {
            setRank(String(p.rank))
            filled = true
          }
          if (p.preferredUniType) {
            setUniType(p.preferredUniType)
            filled = true
          }
          setAutofilled(filled)
        }
      } catch (err) {
        console.warn('Profil yüklenemedi:', err)
      } finally {
        if (!cancelled) setProfileLoaded(true)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [user])

  function clearPusula() {
    sessionStorage.removeItem('pusula_depts')
    setPusulaState(null)
    setResult(null)
  }

  function removeDept(name) {
    if (!pusulaState) return
    const next = {
      ...pusulaState,
      names: pusulaState.names.filter((n) => n !== name),
    }
    if (next.names.length === 0) {
      clearPusula()
      return
    }
    setPusulaState(next)
    sessionStorage.setItem('pusula_depts', JSON.stringify(next))
  }

  async function onSubmit(e) {
    e.preventDefault()
    if (!score && !rank) {
      setError('Lütfen puan veya sıralama gir')
      return
    }
    if (!pusulaState?.names?.length) {
      setError('Önce Pusula\'dan ilgilerini seç')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          score_type: scoreType,
          score: score ? parseFloat(score) : null,
          rank: rank ? parseInt(rank, 10) : null,
          preferred_departments: pusulaState.names,
          preferred_uni_types: uniType === 'all' ? [] : [uniType],
        }),
      })
      if (!res.ok) throw new Error(`API ${res.status}`)
      setResult(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // Pusula yapılmamışsa engel ekranı göster
  if (!pusulaState?.names?.length) {
    return <PusulaGate />
  }

  const modeLabel =
    pusulaState.mode === 'interests' ? 'İlgilerine göre'
    : pusulaState.mode === 'text' ? 'Yazdığın metne göre'
    : pusulaState.mode === 'axes' ? '5 sorulu testin sonucuna göre'
    : 'Pusula sonucu'

  return (
    <>
      <BackgroundScene />

      <div className="space-y-6 max-w-5xl mx-auto">
        {/* Hero */}
        <div className="text-center mb-2">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl md:text-5xl font-display font-bold text-white mb-2"
          >
            Tercih <span className="gradient-text">Asistanın</span>
          </motion.h1>
          <p className="text-slate-400 max-w-xl mx-auto">
            Pusula'dan seçtiğin <strong className="text-emerald-300">{pusulaState.names.length} bölüm</strong>
            {uniType === 'Devlet' && <> içinde <strong className="text-emerald-400">sadece devlet</strong></>}
            {uniType === 'Vakıf'  && <> içinde <strong className="text-rose-400">sadece vakıf</strong></>}
            {uniType === 'all'    && <> içinde <strong className="text-slate-300">tüm üniversitelerden</strong></>},
            puanına uygun <strong className="text-emerald-400">güvenli</strong>,{' '}
            <strong className="text-amber-400">hedef</strong> ve{' '}
            <strong className="text-rose-400">üst seviye</strong> tercihler.
          </p>
        </div>

        {/* Pusula sonucu — bölüm chip'leri */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="card border-emerald-500/30 bg-emerald-500/5"
        >
          <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center shrink-0">
                <Compass size={16} className="text-white" />
              </div>
              <div>
                <div className="text-sm font-semibold text-white">Pusula Bölümlerin</div>
                <div className="text-xs text-slate-400">{modeLabel} · {pusulaState.names.length} bölüm</div>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => navigate('/pusula')}
                className="text-xs px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-accent-500/20 text-slate-300 hover:text-accent-200 transition flex items-center gap-1"
              >
                <Compass size={12} /> Pusulaya Dön
              </button>
              <button
                onClick={clearPusula}
                className="text-xs px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-rose-500/20 text-slate-400 hover:text-rose-200 transition flex items-center gap-1"
              >
                <X size={12} /> Temizle
              </button>
            </div>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {pusulaState.names.map((n) => (
              <span
                key={n}
                className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-200 border border-emerald-500/25 flex items-center gap-1 group"
              >
                <Check size={11} className="opacity-70" />
                {n}
                <button
                  onClick={() => removeDept(n)}
                  title="Listeden çıkar"
                  className="opacity-50 hover:opacity-100 hover:text-rose-300 transition"
                >
                  <X size={11} />
                </button>
              </span>
            ))}
          </div>
        </motion.div>

        {/* Profil bilgi banner'ı */}
        {user && profileLoaded && (
          autofilled ? (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="card border-accent-500/30 bg-accent-500/10 flex items-center gap-3 text-sm"
            >
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-accent-500 flex items-center justify-center shrink-0">
                <Sparkles size={14} className="text-white" />
              </div>
              <div className="flex-1 text-accent-100">
                Puan/sıra bilgilerin <strong>profilden geldi</strong>.
              </div>
              <Link
                to="/profile"
                className="text-xs px-2.5 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-accent-200 transition flex items-center gap-1 shrink-0"
              >
                <UserCog size={12} /> Düzenle
              </Link>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="card border-slate-500/30 bg-white/5 flex items-center gap-3 text-sm"
            >
              <UserCog size={16} className="text-slate-400 shrink-0" />
              <div className="flex-1 text-slate-300">
                Puan/sıra bilgini profiline kaydedersen bir dahaki sefere otomatik dolar.
              </div>
              <Link
                to="/profile"
                className="text-xs px-2.5 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-slate-200 transition shrink-0"
              >
                Profile Git →
              </Link>
            </motion.div>
          )
        )}

        {/* Form */}
        <form onSubmit={onSubmit} className="card space-y-5">
          <div>
            <label className="text-sm text-slate-300 mb-2 block">Puan Türü</label>
            <ScoreTypePicker value={scoreType} onChange={setScoreType} />
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-slate-300 mb-2 block">YKS Puanı</label>
              <input
                type="number"
                step="0.01"
                value={score}
                onChange={(e) => setScore(e.target.value)}
                placeholder="örn: 480.50"
                className="input-glass"
              />
            </div>
            <div>
              <label className="text-sm text-slate-300 mb-2 block">Başarı Sırası</label>
              <input
                type="number"
                value={rank}
                onChange={(e) => setRank(e.target.value)}
                placeholder="örn: 5000"
                className="input-glass"
              />
            </div>
          </div>

          {/* Üniversite Tipi Toggle */}
          <div>
            <label className="text-sm text-slate-300 mb-2 block">
              Üniversite Tipi
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { v: 'all',    label: 'Hepsi',         emoji: '🎓', desc: 'Devlet + Vakıf', color: 'from-slate-500 to-slate-700' },
                { v: 'Devlet', label: 'Devlet',        emoji: '🏛',  desc: 'Ücretsiz',       color: 'from-emerald-500 to-teal-600' },
                { v: 'Vakıf',  label: 'Vakıf (Özel)',  emoji: '🏢',  desc: 'Özel/burslu',    color: 'from-rose-500 to-pink-600' },
              ].map((u) => {
                const active = uniType === u.v
                return (
                  <button
                    key={u.v}
                    type="button"
                    onClick={() => setUniType(u.v)}
                    className={`
                      px-3 py-3 rounded-xl text-sm font-medium transition-all text-left
                      ${active
                        ? `bg-gradient-to-br ${u.color} text-white shadow-lg`
                        : 'glass glass-hover text-slate-300'
                      }
                    `}
                  >
                    <div className="flex items-center gap-1.5 font-semibold">
                      <span>{u.emoji}</span> {u.label}
                    </div>
                    <div className={`text-[10px] mt-0.5 ${active ? 'text-white/80' : 'text-slate-500'}`}>
                      {u.desc}
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

          {error && (
            <div className="text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-3">
              ⚠️ {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full inline-flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Tercihler hesaplanıyor…
              </>
            ) : (
              <>
                <ListChecks size={18} />
                Pusula + Puanla Tercih Öner
              </>
            )}
          </button>
        </form>

        {/* Sonuç */}
        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              {/* Tercih listesi sayacı */}
              {user && (
                <div className="flex items-center justify-between gap-3 px-1 text-xs">
                  <span className="text-slate-400">
                    Tercih Listende:{' '}
                    <strong className={tercihIds.size >= 24 ? 'text-rose-400' : 'text-emerald-400'}>
                      {tercihIds.size}/24
                    </strong>
                  </span>
                  <Link
                    to="/tercih"
                    className="text-accent-300 hover:text-accent-200 transition flex items-center gap-1"
                  >
                    Tercih Listemi Gör <ArrowRight size={11} />
                  </Link>
                </div>
              )}
              {tercihError && (
                <div className="text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-3">
                  ⚠️ {tercihError}
                </div>
              )}
              {result.notes && (
                <div className="card border-amber-500/30 bg-amber-500/10 text-amber-200 text-sm">
                  💡 {result.notes}
                </div>
              )}

              {result.safe?.length === 0 && result.target?.length === 0 && result.reach?.length === 0 && (
                <div className="card border-rose-500/30 bg-rose-500/10 text-center py-8">
                  <div className="text-rose-200 font-medium mb-2">
                    Pusula seçimlerin + puanına uygun program bulunamadı
                  </div>
                  <div className="text-sm text-rose-200/70 mb-4">
                    Pusula bölümlerinden bazılarını çıkar veya farklı ilgi seç.
                  </div>
                  <button
                    onClick={() => navigate('/pusula')}
                    className="btn-ghost text-sm"
                  >
                    Pusulayı Yenile
                  </button>
                </div>
              )}

              {CATEGORIES.map((cat) => {
                const items = result[cat.key] || []
                if (items.length === 0) return null
                return (
                  <div key={cat.key} className="card">
                    <div className="flex items-center gap-3 mb-4">
                      <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${cat.color} flex items-center justify-center shadow-lg`}>
                        <cat.icon size={18} className="text-white" />
                      </div>
                      <div>
                        <h3 className="font-display font-semibold text-lg text-white">
                          {cat.label} <span className="text-slate-500 text-sm">({items.length})</span>
                        </h3>
                        <p className="text-xs text-slate-400">{cat.desc}</p>
                      </div>
                    </div>
                    <div className="grid md:grid-cols-2 gap-3">
                      {items.map((it, i) => (
                        <ItemCard
                          key={i}
                          item={it}
                          isInTercih={tercihIds.has(String(it.department_code))}
                          onAdd={user ? handleAddToTercih : undefined}
                          onRemove={user ? handleRemoveFromTercih : undefined}
                          busyCode={busyCode}
                        />
                      ))}
                    </div>
                  </div>
                )
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  )
}
