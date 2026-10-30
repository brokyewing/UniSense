import { useState, useEffect, useRef, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send, Loader2, BookOpen, ExternalLink, Sparkles, Bot, User,
  TrendingUp, Building2, MapPin, GraduationCap, Menu,
  ChevronDown, ChevronUp, Compass, Plus, Check, Hash,
  ShieldCheck, Target, Mountain,
} from 'lucide-react'
import BackgroundScene from '../components/three/LazyBackgroundScene'
import ChatSidebar from '../components/ChatSidebar'
import { useAuth } from '../contexts/AuthContext'
import {
  useTercihList, useSessionMessages, useToast,
} from '@/services/hooks'
import {
  createSession, addSessionMessage, updateSessionTitle,
} from '@/services/firestore-push'
import { getUserProfile } from '@/services/firestore-core'
import { api } from '@/services/api'
import { eksikKonular } from '../lib/konu'
import { TERCIH_LIMITS, MAX_SESSIONS_PER_USER } from '@/services/constants'

// --- UI Components ---

function Avatar({ kind, photoURL }) {
  if (kind === 'user') {
    return photoURL ? (
      <img src={photoURL} alt="" className="w-9 h-9 shrink-0 rounded-full ring-2 ring-white/10" />
    ) : (
      <div className="w-9 h-9 shrink-0 rounded-full bg-gradient-to-br from-slate-600 to-slate-800 flex items-center justify-center shadow-lg">
        <User size={16} className="text-slate-200" />
      </div>
    )
  }
  return (
    <div className="w-9 h-9 shrink-0 rounded-full bg-gradient-to-br from-brand-500 to-accent-600 flex items-center justify-center shadow-lg shadow-accent-500/30">
      <Bot size={16} className="text-white" />
    </div>
  )
}

function SafetyBadge({ level }) {
  const config = {
    safe: { label: 'Güvenli', icon: ShieldCheck, color: 'from-emerald-500 to-emerald-700', bg: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
    target: { label: 'Hedef', icon: Target, color: 'from-amber-500 to-orange-600', bg: 'bg-amber-500/15 text-amber-300 border-amber-500/30' },
    reach: { label: 'Üst Seviye', icon: Mountain, color: 'from-rose-500 to-fuchsia-600', bg: 'bg-rose-500/15 text-rose-300 border-rose-500/30' },
  }
  const c = config[level] || config.target
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${c.bg} border`}>
      <c.icon size={9} /> {c.label}
    </span>
  )
}

function Message({ msg, userPhoto, tercihIds, onAddToTercih, onAddToPusula, onBulkAddCodes, busyCode }) {
  const isUser = msg.role === 'user'
  const [sourcesOpen, setSourcesOpen] = useState(false)
  const hasDocs = !isUser && msg.docs && msg.docs.length > 0

  // Cevaptan ÖSYM kodlarını parse et
  const codesInText = !isUser && msg.text ? Array.from(new Set(
    [...(msg.text.matchAll(/\b(\d{9})\b/g))].map(m => m[1])
  )) : []

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      <Avatar kind={isUser ? 'user' : 'bot'} photoURL={userPhoto} />
      <div className={`flex-1 max-w-[85%] ${isUser ? 'flex justify-end' : ''}`}>
        <div
          className={`
            rounded-2xl px-4 py-3 text-sm leading-relaxed pretty
            ${isUser
              ? 'bg-gradient-to-br from-brand-600 to-accent-600 text-white shadow-lg shadow-brand-500/20'
              : 'glass text-slate-100'
            }
          `}
        >
          {msg.role === 'bot' && msg.loading ? (
            <div className="flex items-center gap-2 text-slate-400">
              <Loader2 size={14} className="animate-spin" />
              <span>UniSense düşünüyor…</span>
            </div>
          ) : (
            <div className="whitespace-pre-wrap">{msg.text}</div>
          )}
        </div>

        {/* Cevap içinde geçen kodlar — hızlı toplu ekleme */}
        {codesInText.length > 0 && onBulkAddCodes && !msg.loading && (
          <div className="mt-2 inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg bg-accent-500/10 border border-accent-500/30 text-accent-200">
            <Sparkles size={12} className="text-accent-300" />
            <span>
              Bu cevapta <strong>{codesInText.length}</strong> ÖSYM kodu var
            </span>
            <button
              onClick={() => onBulkAddCodes(codesInText)}
              className="ml-1 px-2 py-0.5 rounded-md bg-accent-500/30 hover:bg-accent-500/50 text-white transition flex items-center gap-1"
              title="Hepsini Tercih Listene ekle"
            >
              <Plus size={11} /> Tümünü Ekle
            </button>
          </div>
        )}

        {/* Kaynaklar — collapsible */}
        {hasDocs && (
          <div className="mt-2">
            <button
              onClick={() => setSourcesOpen((o) => !o)}
              className={`group flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition border ${
                sourcesOpen
                  ? 'bg-cyber-cyan/10 text-cyber-cyan border-cyber-cyan/30'
                  : 'bg-white/5 hover:bg-white/10 text-slate-400 hover:text-slate-200 border-white/10'
              }`}
            >
              <BookOpen size={12} />
              <span>{msg.docs.length} kaynak</span>
              {sourcesOpen
                ? <ChevronUp size={11} className="opacity-70" />
                : <ChevronDown size={11} className="opacity-70" />}
              {!sourcesOpen && (
                <span className="opacity-50 ml-1">göster</span>
              )}
            </button>
            <AnimatePresence initial={false}>
              {sourcesOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="grid sm:grid-cols-2 gap-2 mt-2 pt-2">
                    {msg.docs.slice(0, 8).map((d, i) => (
                      <DocCard
                        key={i}
                        doc={d}
                        isInTercih={d.department_code && tercihIds?.has(String(d.department_code))}
                        onAddToTercih={onAddToTercih}
                        onAddToPusula={onAddToPusula}
                        busyCode={busyCode}
                      />
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {msg.latency != null && !isUser && !msg.loading && (
          <div className="mt-2 text-[10px] text-slate-500 flex items-center gap-2">
            ⏱ {msg.latency} ms
            {msg.docs && <>· 📚 {msg.docs.length} chunk</>}
          </div>
        )}
      </div>
    </motion.div>
  )
}

function DocCard({ doc, isInTercih, onAddToTercih, onAddToPusula, busyCode }) {
  const isProgram = !!doc.department_code
  const code = String(doc.department_code || '')
  const busy = busyCode === code
  const safety = doc.safety_level || (doc.placement_probability != null
    ? doc.placement_probability >= 0.75 ? 'safe' : doc.placement_probability >= 0.4 ? 'target' : 'reach'
    : null)

  return (
    <div className="group p-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.06] border border-white/5 hover:border-accent-500/30 transition-all">
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <span className="badge bg-brand-500/15 text-brand-300 border border-brand-500/30">
          {doc.source}
        </span>
        {doc.source_url && (
          <a href={doc.source_url} target="_blank" rel="noreferrer">
            <ExternalLink size={12} className="text-slate-500 hover:text-accent-400" />
          </a>
        )}
      </div>

      {/* Program ise: ad + üni + sıra/taban özeti */}
      {isProgram && doc.department_name && (
        <div className="mb-2 pb-2 border-b border-white/5">
          <div className="text-xs font-semibold text-white leading-tight">
            {doc.department_name}
          </div>
          {doc.university_name && (
            <div className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1">
              <Building2 size={10} /> {doc.university_name}
              {doc.city && <span className="text-slate-500">· {doc.city}</span>}
            </div>
          )}
          {(doc.last_year_base_rank != null || doc.last_year_base_score != null) && (
            <div className="flex items-center gap-3 mt-1 text-[10px]">
              {doc.last_year_base_rank != null && (
                <span className="font-mono text-cyber-cyan flex items-center gap-0.5">
                  <Hash size={9} className="opacity-60" />
                  {Number(doc.last_year_base_rank).toLocaleString('tr')}
                </span>
              )}
              {doc.last_year_base_score != null && (
                <span className="font-mono text-accent-300 flex items-center gap-0.5">
                  <TrendingUp size={9} className="opacity-60" />
                  {Number(doc.last_year_base_score).toFixed(2)}
                </span>
              )}
              {doc.quota != null && (
                <span className="text-slate-500">{doc.quota} kontenjan</span>
              )}
              {safety && <SafetyBadge level={safety} />}
            </div>
          )}
        </div>
      )}

      <p className="text-xs text-slate-300 line-clamp-4 leading-relaxed whitespace-pre-line">
        {doc.content.slice(0, 320)}
        {doc.content.length > 320 && '…'}
      </p>

      <div className="flex items-center gap-2 mt-2 text-[10px] text-slate-500 flex-wrap">
        {doc.university_code && !doc.university_name && (
          <span className="flex items-center gap-1">
            <Building2 size={10} /> {doc.university_code}
          </span>
        )}
        {doc.department_code && (
          <span className="flex items-center gap-1 font-mono">
            <GraduationCap size={10} /> {doc.department_code}
          </span>
        )}
        {doc.year && (
          <span className="flex items-center gap-1">
            <TrendingUp size={10} /> {doc.year}
          </span>
        )}
        {doc.distance != null && (
          <span className="ml-auto opacity-60">📏 {doc.distance.toFixed(2)}</span>
        )}
      </div>

      {/* Aksiyon butonları (yalnız program chunk'ları) */}
      {isProgram && (onAddToTercih || onAddToPusula) && (
        <div className="flex items-center gap-1.5 mt-2 pt-2 border-t border-white/5">
          {onAddToPusula && doc.department_group_name && (
            <button
              onClick={() => onAddToPusula(doc)}
              title="Bu bölümü Pusula listesine ekle (sonra Recommend'da filtrelenir)"
              className="text-[10px] px-2 py-1 rounded-md bg-emerald-500/15 hover:bg-emerald-500/30 text-emerald-300 hover:text-white border border-emerald-500/30 transition inline-flex items-center gap-1"
            >
              <Compass size={10} /> Pusulaya Ekle
            </button>
          )}
          {onAddToTercih && (
            isInTercih ? (
              <span className="text-[10px] px-2 py-1 rounded-md bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 inline-flex items-center gap-1">
                <Check size={10} /> Tercih Listemde
              </span>
            ) : (
              <button
                onClick={() => onAddToTercih(doc)}
                disabled={busy}
                title="Bu programı tercih listesine ekle"
                className="text-[10px] px-2 py-1 rounded-md bg-accent-500/15 hover:bg-accent-500/30 text-accent-300 hover:text-white border border-accent-500/30 transition inline-flex items-center gap-1 disabled:opacity-40"
              >
                {busy ? <Loader2 size={10} className="animate-spin" /> : <Plus size={10} />}
                Tercihe Ekle
              </button>
            )
          )}
        </div>
      )}
    </div>
  )
}

// --- Main Search Component ---

export default function Search() {
  const [params, setParams] = useSearchParams()
  const [input, setInput] = useState(params.get('q') || '')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [activeSessionId, setActiveSessionId] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [busyCode, setBusyCode] = useState(null)
  const endRef = useRef(null)
  const { user, isAuthed } = useAuth()
  const [examCtx, setExamCtx] = useState(null)

  // Analytics: sayfa görüntüleme
  useEffect(() => {
    import('@/services/api').then(m => m.api.analyticsLog('page_view', '/arama', user?.uid).catch(() => {}))
  }, [])

  // Hooks
  const { tercihIds, busyCode: hookBusyCode, setBusyCode: setHookBusyCode } = useTercihList()
  const { messages: sessionMessages, loading: sessionLoading } = useSessionMessages(activeSessionId)
  const { toasts, show: showToast, dismiss } = useToast()

  // Sync busyCode from hook
  useEffect(() => {
    if (hookBusyCode !== busyCode) setBusyCode(hookBusyCode)
  }, [hookBusyCode])

  // Profildeki sınav puanları — user_context için
  useEffect(() => {
    if (!user) { setExamCtx(null); return }
    getUserProfile(user.uid).then(async (p) => {
      const prof: any = p?.profile || {}
      const ctx: any = {}
      if (prof.examTrack) ctx.exam_track = prof.examTrack
      if (prof.score) { ctx.yks_puan = prof.score; if (prof.scoreType) ctx.yks_turu = prof.scoreType }
      if (prof.rank) ctx.yks_sira = prof.rank
      if (prof.kpss?.score) { ctx.kpss_puan = prof.kpss.score; if (prof.kpss.duzey) ctx.kpss_duzey = prof.kpss.duzey }
      if (prof.dgs?.score) { ctx.dgs_puan = prof.dgs.score; if (prof.dgs.type) ctx.dgs_turu = prof.dgs.type }
      if (prof.tus?.score) ctx.tus_puan = prof.tus.score
      if (prof.dus?.score) ctx.dus_puan = prof.dus.score
      if (prof.lgs?.yuzdelik != null) ctx.lgs_yuzdelik = prof.lgs.yuzdelik
      if (prof.ags?.net != null) ctx.ags_net = prof.ags.net
      if (prof.preferredCities?.length) ctx.tercih_sehirler = prof.preferredCities.slice(0, 10)
      if (prof.preferredUniType && prof.preferredUniType !== 'all') ctx.tercih_uni_turu = prof.preferredUniType
      // Çalışma ilerlemesi
      const track = prof.examTrack
      if (track && ['YKS', 'DGS', 'KPSS', 'LGS'].includes(track)) {
        try {
          const checked = JSON.parse(localStorage.getItem('unisense_konu_v1_' + track) || '{}')
          const konuData = await api.konular(track)
          const { toplam, eksik } = eksikKonular(konuData, checked)
          if (toplam) { ctx.calisma_toplam_konu = toplam; ctx.calisma_kalan_konu = eksik.length }
        } catch { /* konu verisi alınamadı */ }
        try {
          const m = new Map()
          for (const r of JSON.parse(localStorage.getItem('unisense_soru_' + track) || '[]')) {
            const k = r.konu || r.ders; if (!k) continue
            const o = m.get(k) || { konu: k, c: 0, d: 0 }
            o.c += r.cozulen || 0; o.d += r.dogru || 0; m.set(k, o)
          }
          const zayif = [...m.values()].filter((o) => o.c >= 5 && o.d / o.c < 0.6).slice(0, 6).map((o) => o.konu)
          if (zayif.length) ctx.calisma_zayif = zayif
        } catch { /* noop */ }
      }
      setExamCtx(Object.keys(ctx).length ? ctx : null)
    }).catch(() => {})
  }, [user])

  // Sync session messages to local state
  useEffect(() => {
    if (sessionMessages.length > 0 || sessionLoading) {
      setMessages(sessionMessages)
    }
  }, [sessionMessages, sessionLoading])

  // Scroll to bottom only on user message
  useEffect(() => {
    if (messages.length === 0) return
    const last = messages[messages.length - 1]
    if (last.role === 'user') {
      endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [messages])

  // Auto-ask from URL param
  useEffect(() => {
    const q = params.get('q')
    if (q && messages.length === 0 && !activeSessionId && !loading) {
      setInput(q)
      ask(q)
    }
  }, [])

  async function newChat() {
    setActiveSessionId(null)
    setMessages([])
    setInput('')
    setParams({})
    setSidebarOpen(false)
  }

  async function ask(text) {
    if (!text.trim() || loading) return

    let sid = activeSessionId

    // Kullanıcı login + session yok → yeni session oluştur
    if (isAuthed && !sid) {
      try {
        sid = await createSession(user.uid, text)
        setActiveSessionId(sid)
      } catch (e) {
        console.warn('Session oluşturulamadı:', e)
      }
    }

    // Kullanıcı mesajını Firestore'a yaz (varsa)
    if (sid && user) {
      await addSessionMessage(user.uid, sid, { role: 'user', text }).catch((e) => console.warn('Mesaj yazılamadı:', e))
    } else {
      // Anonim kullanıcı: sadece local state
      setMessages((m) => [...m, { role: 'user', text }, { role: 'bot', loading: true }])
    }

    setLoading(true)
    setInput('')
    setParams({ q: text })

    if (sid && user) {
      setMessages((m) => [...m, { role: 'bot', loading: true, _temp: true }])
    }

    // Multi-turn history
    const recentHistory = messages
      .filter((m) => !m._temp && !m.loading && m.text)
      .slice(-8)
      .map((m) => ({ role: m.role === 'bot' ? 'bot' : 'user', text: m.text }))

    try {
      const data = await api.ask(text, {
        top_k: 12,
        history: recentHistory,
        user_context: examCtx,
      })

      const botMsg = {
        role: 'bot',
        text: data.text || '(boş cevap)',
        docs: data.docs || [],
        latency_ms: data.total_latency_ms,
      }

      if (sid && user) {
        try {
          await addSessionMessage(user.uid, sid, { ...botMsg, text: String(botMsg.text).slice(0, 10000) })
          setMessages((m) => m.filter((x) => !x._temp))
          if (messages.length === 0) {
            await updateSessionTitle(user.uid, sid, text).catch(() => {})
          }
        } catch {
          setMessages((m) => [
            ...m.filter((x) => !x._temp),
            { role: 'bot', text: botMsg.text, docs: botMsg.docs, latency: botMsg.latency_ms },
          ])
        }
      } else {
        setMessages((m) => [
          ...m.slice(0, -1),
          { role: 'bot', text: botMsg.text, docs: botMsg.docs, latency: botMsg.latency_ms },
        ])
      }
    } catch (e) {
      const errorMsg = e.name === 'ApiError'
        ? `⚠️ ${e.message}`
        : `⚠️ Sunucuya ulaşılamadı: ${e.message}\n\nBackend ayakta mı? (port 8002)`
      if (sid && user) {
        await addSessionMessage(user.uid, sid, { role: 'bot', text: errorMsg, docs: [] })
        setMessages((m) => m.filter((x) => !x._temp))
      } else {
        setMessages((m) => [
          ...m.slice(0, -1),
          { role: 'bot', text: errorMsg, docs: [] },
        ])
      }
    } finally {
      setLoading(false)
    }
  }

  // Handlers using hooks
  function handleAddToPusula(doc) {
    const groupName = doc.department_group_name || doc.department_name
    if (!groupName) return
    let payload
    try {
      const raw = sessionStorage.getItem('pusula_depts')
      payload = raw ? JSON.parse(raw) : null
    } catch { payload = null }
    const names = new Set(payload?.names || [])
    if (names.has(groupName)) {
      showToast(`"${groupName}" zaten Pusulada`, { type: 'info' })
    } else {
      names.add(groupName)
      const next = { names: Array.from(names), mode: payload?.mode || 'manual', timestamp: Date.now() }
      sessionStorage.setItem('pusula_depts', JSON.stringify(next))
      showToast(`✓ "${groupName}" Pusulaya eklendi (${next.names.length} bölüm)`, { type: 'success' })
    }
  }

  async function handleBulkAddCodes(codes) {
    if (!user) { showToast('Giriş yapman gerek', { type: 'error' }); return }
    const remaining = TERCIH_LIMITS.YKS - tercihIds.size
    if (codes.length > remaining) {
      showToast(`${codes.length} kod var ama listede yer ${remaining}`, { type: 'warning' })
      return
    }
    try {
      const data = await api.programsLookup(codes)
      const found = (data.programs || []).filter((p) => p.found)
      let nextOrder = tercihIds.size + 1
      let added = 0, skipped = 0
      for (const p of found) {
        if (tercihIds.has(String(p.department_code))) { skipped++; continue }
        try {
          await import('@/services/firestore-prefs').then(m => m.addToTercih(user.uid, {
            department_code: p.department_code,
            department_name: p.department_name,
            university_code: p.university_code,
            university_name: p.university_name,
            city: p.city,
            score_type: p.score_type || null,
            last_year_base_rank: p.last_year_base_rank ?? null,
            last_year_base_score: p.last_year_base_score ?? null,
            quota: p.quota ?? null,
          }, nextOrder++))
          added++
        } catch { skipped++ }
      }
      showToast(`✓ ${added} program tercih listene eklendi${skipped > 0 ? ` (${skipped} atlandı)` : ''}`, { type: 'success' })
    } catch (e) {
      showToast(`Hata: ${e.message || 'eklenemedi'}`, { type: 'error' })
    }
  }

  async function handleAddToTercih(doc) {
    if (!user) { showToast('Giriş yapman gerek', { type: 'error' }); return }
    if (tercihIds.size >= TERCIH_LIMITS.YKS) {
      showToast('Tercih listesi 24 dolu', { type: 'warning' })
      return
    }
    const code = String(doc.department_code)
    setHookBusyCode(code)
    try {
      await import('@/services/firestore-prefs').then(m => m.addToTercih(user.uid, {
        department_code: code,
        department_name: doc.department_name || 'Bölüm',
        university_code: doc.university_code,
        university_name: doc.university_name || '',
        city: doc.city || '',
        score_type: doc.score_type || null,
        last_year_base_rank: doc.last_year_base_rank ?? null,
        last_year_base_score: doc.last_year_base_score ?? null,
        quota: doc.quota ?? null,
      }, tercihIds.size + 1))
      showToast(`✓ "${doc.department_name}" tercih listene eklendi`, { type: 'success' })
    } catch (e) {
      showToast(`Hata: ${e.message || 'eklenemedi'}`, { type: 'error' })
    } finally {
      setHookBusyCode(null)
    }
  }

  function onSubmit(e) {
    e.preventDefault()
    ask(input)
  }

  return (
    <>
      <BackgroundScene />

      {/* Toast'lar — sağ üst */}
      <AnimatePresence>
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, x: 50, y: -20 }}
            animate={{ opacity: 1, x: 0, y: 0 }}
            exit={{ opacity: 0, x: 50 }}
            className="fixed top-24 right-6 z-[100] card border-emerald-500/40 bg-emerald-500/10 backdrop-blur-xl text-sm text-emerald-200 max-w-xs"
          >
            <div className="flex items-center gap-2">
              <Check size={14} className="text-emerald-300" />
              {t.message}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      <div className="flex gap-4 h-[calc(100vh-80px)]">
        {/* Sidebar — sol */}
        <ChatSidebar
          activeSessionId={activeSessionId}
          onSelectSession={(sid) => { setActiveSessionId(sid); setSidebarOpen(false) }}
          onNewChat={newChat}
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        {/* Ana Chat — sağ */}
        <div className="flex-1 flex flex-col h-full min-w-0">
          {/* Üst bar — mobile menu */}
          {isAuthed && (
            <div className="flex items-center justify-between gap-2 mb-3 px-2">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden btn-ghost inline-flex items-center gap-2 text-sm"
              >
                <Menu size={14} />
                Geçmiş Sohbetler
              </button>
              {/* Ücretsiz — premium upsell kaldırıldı */}
            </div>
          )}

          {/* Sohbet alanı */}
          <div className="flex-1 overflow-y-auto pr-2 space-y-4 pb-6">
            {messages.length === 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center justify-center h-full text-center py-20"
              >
                <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-brand-500 to-accent-600 flex items-center justify-center shadow-2xl shadow-accent-500/40 mb-4 animate-pulse-glow">
                  <Sparkles size={28} className="text-white" />
                </div>
                <h2 className="text-3xl font-display font-bold text-white mb-2">
                  Ne öğrenmek istersin?
                </h2>
                <p className="text-slate-400 max-w-lg mx-auto mb-2 pretty">
                  Bölüm, üniversite, taban puan, sıralama veya karşılaştırma —
                  doğal Türkçe ile sor.
                </p>
                {isAuthed && (
                  <p className="text-xs text-slate-500 mb-6">
                    💡 Sohbetlerin otomatik kaydediliyor (max {MAX_SESSIONS_PER_USER} oturum)
                  </p>
                )}
                <div className="grid sm:grid-cols-2 gap-2 max-w-2xl">
                  {[
                    'Bilgisayar Mühendisliği taban puanı',
                    'İTÜ tüm bölümleri',
                    '300.000 sırayla devlet üniversiteleri',
                    'Tıp burslu vakıf üniversiteleri',
                  ].map((q) => (
                    <button
                      key={q}
                      onClick={() => ask(q)}
                      className="px-4 py-3 rounded-xl glass glass-hover text-sm text-slate-300 text-left hover:text-white"
                    >
                      💡 {q}
                    </button>
                  ))}
                </div>
                {/* Ücretsiz — premium upsell kaldırıldı */}
              </motion.div>
            )}

            <AnimatePresence>
              {messages.map((m, i) => (
                <Message
                  key={`${activeSessionId || 'local'}-${i}`}
                  msg={m}
                  userPhoto={user?.photoURL}
                  tercihIds={tercihIds}
                  onAddToTercih={handleAddToTercih}
                  onAddToPusula={handleAddToPusula}
                  onBulkAddCodes={handleBulkAddCodes}
                  busyCode={busyCode}
                />
              ))}
            </AnimatePresence>
            <div ref={endRef} />
          </div>

          {/* Input */}
          <form onSubmit={onSubmit} className="sticky bottom-0 p-2">
            <div className="relative max-w-4xl mx-auto">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Sorunu yaz... (örn: Boğaziçi Bilgisayar taban puanı)"
                className="input-glass pr-14 text-base w-full"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-accent-600 hover:shadow-lg hover:shadow-accent-500/40 transition-all disabled:opacity-40 flex items-center justify-center text-white"
              >
                {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={16} />}
              </button>
            </div>
            <p className="text-[11px] text-slate-500 text-center mt-2">
              ⓘ Cevaplar YÖK Atlas ve Wikipedia verilerine dayanır.
            </p>
          </form>
        </div>
      </div>
    </>
  )
}