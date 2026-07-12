import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { getUserProfile, updateUserProfile } from '../firebase'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Compass, Sparkles, MessageSquare, ListChecks, Loader2, Check,
  Search as SearchIcon, X, ChevronRight, Wand2, Brain, ArrowRight,
} from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import { apiFetch } from '../lib/api'

const MAX_SELECTIONS = 40
const MIN_SELECTIONS = 3

const QUESTIONS = [
  {
    key: 'math',
    label: 'Matematik / sayısal',
    left: 'Çok az matematik',
    right: 'Çok yoğun matematik',
    icon: '🧮',
  },
  {
    key: 'human',
    label: 'İnsan vs nesne',
    left: 'Nesne / kod / sistem',
    right: 'İnsan / hizmet / ilişki',
    icon: '🤝',
  },
  {
    key: 'creative',
    label: 'Yaratıcı vs analitik',
    left: 'Tamamen analitik',
    right: 'Yaratıcı / estetik',
    icon: '🎨',
  },
  {
    key: 'research',
    label: 'Araştırma derinliği',
    left: 'Hızlı uygulamalı sonuç',
    right: 'Uzun teori / araştırma',
    icon: '🔬',
  },
  {
    key: 'field',
    label: 'Saha vs ofis',
    left: 'Sabit ofis / masa',
    right: 'Saha / dışarı / hareketli',
    icon: '🌍',
  },
]

const TABS = [
  { id: 'cards', label: 'İlgilerini Seç', icon: ListChecks, hint: 'Konuları işaretle' },
  { id: 'text', label: 'Soru Sor', icon: MessageSquare, hint: 'Sorguya gönder' },
  { id: 'quiz', label: '5 Soru', icon: Brain, hint: 'Hızlı eşleştirme' },
]

// === Mod A: İlgi Etiketi Seçimi (bölüm adı YOK) ===
function CardsMode({ onResult }) {
  const { user } = useAuth()
  const [taxonomy, setTaxonomy] = useState(null)
  const [selected, setSelected] = useState(new Set())
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [savedToProfile, setSavedToProfile] = useState(false)
  const [examTrack, setExamTrack] = useState('YKS')  // profil sınav yolu

  // İlgi taksonomisini yükle + login user'ın profile'ından önceki ilgileri al.
  // Taksonomi nadiren değişir → sessionStorage'dan ANINDA göster, arka planda tazele.
  useEffect(() => {
    let cancelled = false
    setError('')

    let cached = null
    try {
      const raw = sessionStorage.getItem('compass_interests')
      if (raw) cached = JSON.parse(raw)
    } catch { /* cache yok/bozuk */ }
    if (cached?.categories?.length) {
      setTaxonomy(cached)
      setLoading(false)
    } else {
      setLoading(true)
    }

    const taxoPromise = apiFetch('/api/v1/compass/interests')
    const profilePromise = user
      ? getUserProfile(user.uid).catch(() => null)
      : Promise.resolve(null)

    Promise.all([taxoPromise, profilePromise])
      .then(([data, profileData]) => {
        if (cancelled) return
        if (data?.categories?.length) {
          setTaxonomy(data)
          try { sessionStorage.setItem('compass_interests', JSON.stringify(data)) } catch { /* kota */ }
        } else if (!cached) {
          throw new Error('İlgi listesi boş döndü')
        }
        const prev = profileData?.profile?.preferredInterests
        if (Array.isArray(prev) && prev.length > 0) {
          setSelected(new Set(prev))
          setSavedToProfile(true)
        }
        if (profileData?.profile?.examTrack) setExamTrack(profileData.profile.examTrack)
      })
      .catch((e) => {
        if (cancelled || cached) return  // cache varsa arka plan hatasını yut
        console.error('[Pusula interests fetch]', e)
        setError(e.message || String(e))
      })
      .finally(() => !cancelled && setLoading(false))
    return () => { cancelled = true }
  }, [user])

  function toggle(id) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else if (next.size < MAX_SELECTIONS) next.add(id)
      return next
    })
  }

  async function submit() {
    if (selected.size < MIN_SELECTIONS) {
      setError(`En az ${MIN_SELECTIONS} ilgi seç`)
      return
    }
    setSubmitting(true)
    setError('')
    try {
      const interests = Array.from(selected)
      const data = await apiFetch('/api/v1/compass/by-interests', {
        method: 'POST',
        body: { interests, top_k: 15 },
      })
      onResult({ ...data, selected: interests })

      // Login user — ilgileri profile'a kaydet (sessizce)
      if (user) {
        try {
          await updateUserProfile(user.uid, { preferredInterests: interests })
          setSavedToProfile(true)
        } catch (e) {
          console.warn('İlgiler profile kaydedilemedi:', e)
        }
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="card flex items-center justify-center py-16">
        <Loader2 className="animate-spin text-accent-400" size={32} />
      </div>
    )
  }
  if (error && !taxonomy) {
    return (
      <div className="card border-rose-500/30 bg-rose-500/10 space-y-3">
        <div className="flex items-start gap-3">
          <X size={20} className="text-rose-300 shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="font-semibold text-rose-200">İlgi listesi yüklenemedi</div>
            <div className="text-sm text-rose-200/80 mt-1">{error}</div>
            <div className="text-xs text-slate-400 mt-3">
              Backend'in <code className="px-1 rounded bg-black/30">localhost:8002</code>
              {' '}üzerinde çalıştığından emin ol; gerekirse <code className="px-1 rounded bg-black/30">start.bat</code>
              {' '}ile yeniden başlat.
            </div>
          </div>
        </div>
        <button
          onClick={() => window.location.reload()}
          className="btn-ghost text-sm"
        >
          Tekrar Dene
        </button>
      </div>
    )
  }
  if (!taxonomy) return null

  // Aramayı kategori bazlı uygula
  const matchSearch = (id) =>
    !search || id.toLocaleLowerCase('tr').includes(search.toLocaleLowerCase('tr'))

  return (
    <div className="space-y-4">
      {/* DGS/KPSS kullanıcısına: Pusula YKS bölüm önerisi içindir (BULGU #17) */}
      {(examTrack === 'DGS' || examTrack === 'KPSS') && (
        <div className="card border-amber-500/30 bg-amber-500/10 text-sm text-amber-200 flex items-start gap-2">
          <span className="shrink-0">💡</span>
          <span>
            İlgi Pusulası <strong>YKS bölüm önerisi</strong> içindir. Sınav yolun{' '}
            <strong>{examTrack}</strong>; {examTrack} tercihlerini{' '}
            <a href="/oneriler" className="text-accent-300 hover:underline">Öneriler</a>{' '}
            sayfasındaki {examTrack} sekmesinden puanınla yapabilirsin. Yine de
            ilgilerini keşfetmek istersen buradan devam edebilirsin.
          </span>
        </div>
      )}
      {/* Sayaç + arama + submit */}
      <div className="card flex flex-col md:flex-row gap-3 items-stretch md:items-center">
        <div className="flex-1 flex items-center gap-3 flex-wrap">
          <div className={`px-3 py-2 rounded-lg font-mono text-sm ${
            selected.size >= MIN_SELECTIONS ? 'bg-emerald-500/20 text-emerald-300' : 'bg-white/5 text-slate-400'
          }`}>
            {selected.size} / {MAX_SELECTIONS} ilgi
          </div>
          {selected.size < MIN_SELECTIONS ? (
            <span className="text-xs text-slate-500">
              min {MIN_SELECTIONS} ilgi seç → bölüm öneri al
            </span>
          ) : (
            <span className="text-xs text-emerald-400">✓ Hazır</span>
          )}
          {savedToProfile && user && (
            <span
              className="text-[10px] px-2 py-0.5 rounded-full bg-accent-500/15 text-accent-300 border border-accent-500/30"
              title="İlgilerin hesabına kaydedildi — sonraki ziyaretinde otomatik gelir"
            >
              ✓ Profile kayıtlı
            </span>
          )}
        </div>

        <div className="relative md:w-64">
          <SearchIcon size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="İlgi ara (örn. yazılım)"
            className="input-glass pl-9 pr-3 py-2 text-sm w-full"
          />
        </div>

        <button
          onClick={submit}
          disabled={selected.size < MIN_SELECTIONS || submitting}
          className="btn-primary inline-flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
        >
          {submitting ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <>
              <Wand2 size={16} />
              Bölüm Öner ({selected.size})
            </>
          )}
        </button>
      </div>

      {/* Yardımcı açıklama */}
      <div className="text-xs text-slate-500 px-1">
        💡 <strong className="text-slate-400">"Tıp"</strong> yerine{' '}
        <strong className="text-accent-300">"hasta bakımı"</strong>,{' '}
        <strong className="text-accent-300">"klinik çalışma"</strong> gibi
        <strong> seni heyecanlandıran konuları</strong> seç. Bunları kapsayan tüm bölümleri çıkartırız.
      </div>

      {/* Seçilenler chip'leri */}
      {selected.size > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-wrap gap-1.5"
        >
          {Array.from(selected).map((id) => (
            <button
              key={id}
              onClick={() => toggle(id)}
              className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-200 border border-emerald-500/30 hover:bg-rose-500/20 hover:text-rose-200 hover:border-rose-500/40 transition flex items-center gap-1"
            >
              <Check size={11} />
              {id}
              <X size={11} />
            </button>
          ))}
        </motion.div>
      )}

      {/* Kategoriler — yatay olarak hepsi açık, her biri kendi pill seti */}
      <div className="space-y-3">
        {taxonomy.categories.map((cat) => {
          const filteredInterests = cat.interests.filter((iv) => matchSearch(iv.id))
          if (search && filteredInterests.length === 0) return null
          const selectedInCat = cat.interests.filter((iv) => selected.has(iv.id)).length
          return (
            <div key={cat.id} className="card !p-4">
              <div className="flex items-center justify-between mb-2.5">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{cat.emoji}</span>
                  <h3 className="font-display font-semibold text-white text-sm">
                    {cat.label}
                  </h3>
                  <span className="text-[10px] text-slate-500">
                    {cat.interests.length} ilgi
                  </span>
                </div>
                {selectedInCat > 0 && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    {selectedInCat} seçildi
                  </span>
                )}
              </div>

              <div className="flex flex-wrap gap-1.5">
                {filteredInterests.map((iv) => {
                  const isSelected = selected.has(iv.id)
                  const disabled = !isSelected && selected.size >= MAX_SELECTIONS
                  return (
                    <button
                      key={iv.id}
                      onClick={() => toggle(iv.id)}
                      disabled={disabled}
                      title={`${iv.department_count} programa uygun`}
                      className={`text-xs px-2.5 py-1.5 rounded-full border transition flex items-center gap-1 ${
                        isSelected
                          ? 'bg-gradient-to-br from-brand-500/30 to-accent-500/30 border-accent-400/50 text-white shadow-lg shadow-accent-500/20'
                          : disabled
                          ? 'border-white/5 bg-white/[0.02] text-slate-500 cursor-not-allowed'
                          : 'bg-white/5 hover:bg-white/10 border-white/10 text-slate-300 hover:border-accent-500/40 hover:text-accent-200'
                      }`}
                    >
                      {isSelected && <Check size={11} className="opacity-80" />}
                      {iv.id}
                      <span className={`text-[9px] ${isSelected ? 'text-white/50' : 'text-slate-500'}`}>
                        ·{iv.department_count}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>

      {error && taxonomy && (
        <div className="text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-3">
          ⚠️ {error}
        </div>
      )}
    </div>
  )
}

// === Mod B: Serbest Metin → Sorgu sayfasına yönlendirir (1 RAG hakkı kullanır) ===
function TextMode() {
  const navigate = useNavigate()
  const [text, setText] = useState('')

  const EXAMPLES = [
    'İskenderun Teknik Üniversitesi hakkında bilgi ver',
    'Boğaziçi Bilgisayar Mühendisliği taban puanları',
    '300.000 sıralamayla hangi mühendislikleri yazabilirim',
    'KKTC tıp fakülteleri ve ücretleri',
    'En iyi 10 vakıf üniversitesi hangisidir',
  ]

  function ask() {
    const t = text.trim()
    if (t.length < 3) return
    navigate(`/arama?q=${encodeURIComponent(t)}`)
  }

  return (
    <div className="space-y-4">
      <div className="card space-y-4">
        {/* Bilgi banner'ı — bu mod artık RAG sorgusu */}
        <div className="text-xs px-3 py-2 rounded-lg bg-accent-500/10 border border-accent-500/30 text-accent-200 flex items-start gap-2">
          <MessageSquare size={14} className="mt-0.5 shrink-0" />
          <div>
            <strong>Bu sorgu, sohbet asistanına gider.</strong> Üniversite/bölüm
            adı yazarsan taban puan, sıralama, kontenjan gibi gerçek verileri
            kaynaklarla birlikte alırsın (1 sohbet hakkı kullanılır).
          </div>
        </div>

        <div>
          <label className="text-sm text-slate-300 mb-2 block">
            Sormak istediğin soruyu yaz:
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) ask()
            }}
            placeholder="Mesela: İskenderun Teknik Üniversitesi'nin Bilgisayar Müh taban puanı kaç?"
            rows={4}
            className="input-glass w-full resize-none"
            maxLength={500}
          />
          <div className="flex justify-between text-xs text-slate-500 mt-1">
            <span>{text.length}/500</span>
            <span className="opacity-60">Ctrl+Enter ile sor</span>
          </div>
        </div>

        <div>
          <div className="text-xs text-slate-500 mb-2">Örnek sorular:</div>
          <div className="flex flex-wrap gap-1.5">
            {EXAMPLES.map((ex, i) => (
              <button
                key={i}
                onClick={() => setText(ex)}
                className="text-xs px-2.5 py-1.5 rounded-lg glass glass-hover text-slate-300"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={ask}
          disabled={text.trim().length < 3}
          className="btn-primary w-full inline-flex items-center justify-center gap-2 disabled:opacity-40"
        >
          <MessageSquare size={16} />
          Sorguya Gönder
          <ArrowRight size={14} />
        </button>

        <div className="text-[11px] text-slate-500 text-center">
          💡 Bölüm <strong>önerisi</strong> almak istiyorsan sol taraftaki{' '}
          <strong className="text-accent-300">"İlgilerini Seç"</strong> veya{' '}
          <strong className="text-accent-300">"5 Soru"</strong> sekmelerini kullan.
        </div>
      </div>
    </div>
  )
}

// === Mod C: 5 Soru ===
function QuizMode({ onResult }) {
  const [answers, setAnswers] = useState({
    math: 3, human: 3, creative: 3, research: 3, field: 3,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function submit() {
    setLoading(true)
    setError('')
    try {
      const data = await apiFetch('/api/v1/compass/by-axes', {
        method: 'POST',
        body: { ...answers, top_k: 15 },
      })
      onResult({ ...data, axes: answers })
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function reset() {
    setAnswers({ math: 3, human: 3, creative: 3, research: 3, field: 3 })
  }

  const isNeutral = Object.values(answers).every((v) => v === 3)

  return (
    <div className="space-y-4">
      <div className="card space-y-5">
        <div className="text-sm text-slate-400">
          Her soru için sana yakın olanı seç (1: tamamen sol, 5: tamamen sağ).
        </div>

        {QUESTIONS.map((q) => (
          <div key={q.key} className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium text-slate-200 flex items-center gap-2">
                <span className="text-xl">{q.icon}</span>
                {q.label}
              </div>
              <div className="text-xs font-mono text-accent-300 bg-accent-500/10 px-2 py-0.5 rounded">
                {answers[q.key]}/5
              </div>
            </div>

            <div className="grid grid-cols-5 gap-1">
              {[1, 2, 3, 4, 5].map((v) => {
                const isActive = answers[q.key] === v
                return (
                  <button
                    key={v}
                    onClick={() => setAnswers((a) => ({ ...a, [q.key]: v }))}
                    className={`py-2.5 rounded-lg text-sm font-medium transition ${
                      isActive
                        ? 'bg-gradient-to-br from-brand-500 to-accent-500 text-white shadow-lg'
                        : 'glass glass-hover text-slate-400'
                    }`}
                  >
                    {v}
                  </button>
                )
              })}
            </div>

            <div className="flex justify-between text-[11px] text-slate-500 px-1">
              <span>← {q.left}</span>
              <span>{q.right} →</span>
            </div>
          </div>
        ))}

        <div className="flex gap-2 pt-2">
          <button
            onClick={reset}
            className="btn-ghost px-4 py-2.5 text-sm"
          >
            Sıfırla
          </button>
          <button
            onClick={submit}
            disabled={loading || isNeutral}
            className="btn-primary flex-1 inline-flex items-center justify-center gap-2 disabled:opacity-40"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Eşleştiriyorum…
              </>
            ) : isNeutral ? (
              'Cevaplar henüz seçilmedi'
            ) : (
              <>
                <Brain size={16} />
                Eşleştir
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-3">
            ⚠️ {error}
          </div>
        )}
      </div>
    </div>
  )
}

// === Sonuç kartları ===
function ResultMatch({ match, index, onRemove }) {
  const hasMatchedInterests = match.matched_interests?.length > 0
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ delay: index * 0.03 }}
      className="card glass-hover p-4 group relative"
    >
      <button
        onClick={onRemove}
        title="Listeden çıkar"
        className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-slate-800 border border-white/10 hover:bg-rose-500 hover:border-rose-400 hover:scale-110 transition-all flex items-center justify-center opacity-70 hover:opacity-100 z-10"
      >
        <X size={12} className="text-slate-300 hover:text-white" />
      </button>
      <div className="flex items-start justify-between gap-3 pr-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">{match.category_emoji}</span>
            <span className="text-[10px] uppercase tracking-wider text-slate-500">
              {match.category_label}
            </span>
          </div>
          <h4 className="font-display font-semibold text-white text-base leading-tight">
            {match.name}
          </h4>

          {hasMatchedInterests ? (
            <>
              <div className="text-[10px] text-emerald-400 mt-2 mb-1 uppercase tracking-wider">
                seçtiğin ilgilerle eşleşen ({match.matched_count})
              </div>
              <div className="flex flex-wrap gap-1">
                {match.matched_interests.map((iv) => (
                  <span
                    key={iv}
                    className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                  >
                    ✓ {iv}
                  </span>
                ))}
              </div>
            </>
          ) : (
            <div className="flex flex-wrap gap-1 mt-2">
              {match.tags?.slice(0, 3).map((tag) => (
                <span
                  key={tag}
                  className="text-[10px] px-1.5 py-0.5 rounded bg-accent-500/10 text-accent-300"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {match.axis_summary && !hasMatchedInterests && (
            <div className="text-[10px] text-slate-500 mt-1.5">
              odak: {match.axis_summary}
            </div>
          )}
        </div>
        <div className="text-right shrink-0">
          <div className="text-[10px] text-slate-500">eşleşme</div>
          <div className="font-display font-bold text-2xl bg-gradient-to-br from-accent-300 to-cyber-cyan bg-clip-text text-transparent">
            %{Math.round(match.match_score)}
          </div>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between gap-2">
        <span className="text-xs text-slate-500">
          {match.program_count} program
        </span>
        <Link
          to={`/arama?q=${encodeURIComponent(match.name)}`}
          className="text-xs px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-accent-500/20 hover:text-accent-200 text-slate-300 transition flex items-center gap-1"
        >
          Detay <ChevronRight size={12} />
        </Link>
      </div>
    </motion.div>
  )
}

function ResultsSection({ result, onClear, onRemoveMatch }) {
  const navigate = useNavigate()
  if (!result) return null
  const { matches, mode } = result

  function goToRecommend() {
    if (!matches?.length) return
    const payload = {
      names: matches.map((m) => m.name),
      mode,
      timestamp: Date.now(),
    }
    try {
      sessionStorage.setItem('pusula_depts', JSON.stringify(payload))
    } catch (e) {
      console.warn('sessionStorage yazılamadı', e)
    }
    navigate('/oneriler')
  }

  const modeLabel =
    mode === 'interests' ? 'İlgilerine göre'
    : mode === 'selection' ? 'Seçtiklerinden hareketle'
    : mode === 'text' ? 'Yazdıklarına göre'
    : mode === 'axes' ? 'Cevaplarına göre'
    : 'Pusula sonucu'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      <div className="card flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-emerald-500/30 bg-emerald-500/5 sticky top-20 z-20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center shrink-0">
            <Sparkles size={18} className="text-white" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">
              {matches.length} bölüm önerisi
            </div>
            <div className="text-xs text-slate-400">
              {modeLabel}
              {' · '}
              <strong className="text-emerald-300">istemediklerini ✕ ile çıkar</strong>
              {', sonra Tercihe Aktar'}
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onClear}
            className="btn-ghost px-3 py-2 text-xs flex items-center gap-1"
          >
            <X size={12} /> Yenile
          </button>
          <button
            onClick={goToRecommend}
            disabled={!matches.length}
            className="btn-primary px-3 py-2 text-xs inline-flex items-center gap-1 disabled:opacity-40"
          >
            Tercihe Aktar ({matches.length}) <ArrowRight size={12} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        <AnimatePresence>
          {matches.map((m, i) => (
            <ResultMatch
              key={m.name}
              match={m}
              index={i}
              onRemove={() => onRemoveMatch?.(m.name)}
            />
          ))}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}

// === Ana sayfa ===
export default function Pusula() {
  const [tab, setTab] = useState('cards')
  const [result, setResult] = useState(null)
  const resultRef = useRef(null)

  function handleResult(data) {
    setResult(data)
    setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100)
  }

  function handleRemoveMatch(name) {
    setResult((prev) => {
      if (!prev) return prev
      const filtered = prev.matches.filter((m) => m.name !== name)
      if (filtered.length === 0) return null
      return { ...prev, matches: filtered }
    })
  }

  return (
    <>
      <BackgroundScene />

      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Hero */}
        <div className="text-center mb-2">
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-16 h-16 mx-auto mb-3 rounded-2xl bg-gradient-to-br from-brand-500 via-accent-500 to-cyber-pink flex items-center justify-center shadow-2xl shadow-accent-500/30"
          >
            <Compass size={32} className="text-white" />
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl md:text-5xl font-display font-bold text-white mb-2"
          >
            <span className="gradient-text">İlgi Pusulası</span>
          </motion.h1>
          <p className="text-slate-400 max-w-2xl mx-auto">
            Hangi bölümün sana uygun olduğunu bilmiyor musun?{' '}
            <strong className="text-accent-300">İlgilerini seç</strong> ya da{' '}
            <strong className="text-accent-300">5 soru</strong> cevapla — sana uygun
            bölümleri öneririz. Spesifik bir soru için{' '}
            <strong className="text-emerald-300">"Soru Sor"</strong> sekmesinden
            sorgu asistanına gönderebilirsin.
          </p>
        </div>

        {/* Tab seçici */}
        <div className="card p-2 flex gap-1">
          {TABS.map((t) => {
            const isActive = tab === t.id
            return (
              <button
                key={t.id}
                onClick={() => { setTab(t.id); setResult(null) }}
                className={`flex-1 px-3 py-3 rounded-xl text-sm font-medium transition flex items-center justify-center gap-2 ${
                  isActive
                    ? 'bg-gradient-to-br from-brand-500/30 to-accent-500/30 text-white border border-accent-500/40 shadow-lg'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                }`}
              >
                <t.icon size={16} />
                <span>{t.label}</span>
                <span className="hidden sm:inline text-[10px] opacity-60">· {t.hint}</span>
              </button>
            )
          })}
        </div>

        {/* Aktif tab içeriği */}
        <AnimatePresence mode="wait">
          <motion.div
            key={tab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {tab === 'cards' && <CardsMode onResult={handleResult} />}
            {tab === 'text' && <TextMode />}
            {tab === 'quiz' && <QuizMode onResult={handleResult} />}
          </motion.div>
        </AnimatePresence>

        {/* Sonuçlar */}
        <div ref={resultRef}>
          <AnimatePresence>
            {result && (
              <ResultsSection
                result={result}
                onClear={() => setResult(null)}
                onRemoveMatch={handleRemoveMatch}
              />
            )}
          </AnimatePresence>
        </div>
      </div>
    </>
  )
}
