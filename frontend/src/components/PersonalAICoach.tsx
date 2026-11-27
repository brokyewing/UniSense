import { useState, useEffect, useMemo, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  Sparkles, Target, CheckCircle2, Circle, Plus, Send,
  Loader2, ArrowRight, Zap, Flame, BookOpen, AlertTriangle,
  ListChecks,
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { api } from '@/services/api'
import {
  executeCoachActions,
  getTodayQuestionCount,
  type AppliedActionResult,
} from '../lib/aiActions'
import { getGuestTercih } from '../lib/guestTercih'
import { konuLocal } from '../lib/konu'
import { isoGun, isoHafta, oneriler } from '../lib/planlayici'

const SINAVLAR = ['YKS', 'KPSS', 'DGS', 'LGS'] as const

const QUICK_PROMPTS = [
  'Bana günlük 40 soru hedefi koy',
  'Bugün Matematikten 30 soru 26 doğru çözdüm kaydet',
  '30 günde konuları bitir, günde 40 soru',
  "Boğaziçi Bilgisayar'ı tercihime ekle",
]

export interface PersonalCoachMeta {
  ready: boolean
  isPersonalized: boolean
  firstName: string
  track: string
  hedefBolum: string
}

interface PersonalAICoachProps {
  onPersonalStateChange?: (meta: PersonalCoachMeta) => void
  hideHeaderTitle?: boolean
}

function loadJSON<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

export default function PersonalAICoach({
  onPersonalStateChange,
  hideHeaderTitle = false,
}: PersonalAICoachProps = {}) {
  const { user } = useAuth()
  const bugun = useMemo(() => isoGun(), [])
  const hafta = useMemo(() => isoHafta(new Date()), [])

  const [track, setTrack] = useState<string>('YKS')
  const [config, setConfig] = useState<Record<string, any> | null>(null)
  const [tasks, setTasks] = useState<any[]>([])
  const [soruKayit, setSoruKayit] = useState<any[]>([])
  const [checked, setChecked] = useState<Record<string, boolean>>({})
  const [tercihItems, setTercihItems] = useState<any[]>([])
  const [konuData, setKonuData] = useState<any>(null)
  const [ready, setReady] = useState(false)

  const [cmd, setCmd] = useState('')
  const [cmdLoading, setCmdLoading] = useState(false)
  const [cmdReply, setCmdReply] = useState('')
  const [cmdActions, setCmdActions] = useState<AppliedActionResult[]>([])
  const [quickBusy, setQuickBusy] = useState(false)

  const refreshState = useCallback(async (preferredTrack?: string) => {
    try {
      if (!user) {
        const cfg = loadJSON<Record<string, any> | null>('unisense_plan_cfg', null)
        const activeTrack = preferredTrack || cfg?.track || 'YKS'
        setConfig(cfg)
        if (!preferredTrack && cfg?.track && SINAVLAR.includes(cfg.track)) {
          setTrack(cfg.track)
        }
        setTasks(loadJSON<any[]>(`unisense_plan_${hafta}`, []))
        setSoruKayit(loadJSON<any[]>(`unisense_soru_${activeTrack}`, []))
        setChecked(konuLocal(activeTrack))
        setTercihItems(getGuestTercih())
        setReady(true)
        return
      }

      const [planMod, coreMod] = await Promise.all([
        import('@/services/firestore-plan'),
        import('@/services/firestore-core'),
      ])
      const [cfg, profDoc] = await Promise.all([
        planMod.getPlanConfig(user.uid),
        coreMod.getUserProfile(user.uid).catch(() => null),
      ])
      const profTrack = profDoc?.profile?.examTrack
      const activeTrack = preferredTrack || cfg?.track || (SINAVLAR.includes(profTrack) ? profTrack : 'YKS')
      setConfig(cfg)
      if (!preferredTrack && SINAVLAR.includes(activeTrack)) {
        setTrack(activeTrack)
      }
      const [chk, sorular] = await Promise.all([
        planMod.getKonuChecked(user.uid, activeTrack),
        planMod.getSoruList(user.uid, activeTrack),
      ])
      setChecked(chk || {})
      setSoruKayit(sorular || [])
      setReady(true)
    } catch {
      setReady(true)
    }
  }, [user, hafta])

  useEffect(() => {
    refreshState(track)
  }, [refreshState, track])

  // Girişli kullanıcıda haftalık plan görevlerini ve tercih listesini canlı dinle
  useEffect(() => {
    if (!user) return
    let active = true
    let unsubPlan: (() => void) | null = null
    let unsubPrefs: (() => void) | null = null
    import('@/services/firestore-plan').then((m) => {
      if (!active) return
      unsubPlan = m.watchPlanGorevler(user.uid, hafta, (list: any[]) => {
        if (active) setTasks(list || [])
      })
    }).catch(() => {})
    import('@/services/firestore-prefs').then((m) => {
      if (!active) return
      unsubPrefs = m.watchTercihList(user.uid, (items: any[]) => {
        if (active) setTercihItems(items || [])
      })
    }).catch(() => {})
    return () => {
      active = false
      if (unsubPlan) unsubPlan()
      if (unsubPrefs) unsubPrefs()
    }
  }, [user, hafta])

  // Diğer sayfalardan veya AI komutlarından gelen sistem güncellemelerini yakala
  useEffect(() => {
    const onUpdated = () => {
      refreshState()
    }
    const onGuestTercih = () => {
      if (!user) setTercihItems(getGuestTercih())
    }
    window.addEventListener('unisense:ai-state-updated', onUpdated)
    window.addEventListener('unisense:guest-tercih', onGuestTercih)
    return () => {
      window.removeEventListener('unisense:ai-state-updated', onUpdated)
      window.removeEventListener('unisense:guest-tercih', onGuestTercih)
    }
  }, [refreshState, user])

  // Öncelikli konu önerisi için konu ağacını yükle
  useEffect(() => {
    let cancelled = false
    api.konular(track).then((d) => {
      if (!cancelled) setKonuData(d)
    }).catch(() => {
      if (!cancelled) setKonuData(null)
    })
    return () => { cancelled = true }
  }, [track])

  const bugunCozulen = useMemo(() => getTodayQuestionCount(soruKayit, bugun), [soruKayit, bugun])
  const gunlukHedef = Number(config?.gunlukSoruHedef) > 0 ? Number(config?.gunlukSoruHedef) : 0
  const hedefOran = gunlukHedef > 0 ? Math.min(100, Math.round((bugunCozulen / gunlukHedef) * 100)) : 0
  const hedefBolum = String(config?.hedefBolum || '').trim()

  const bugunGorevler = useMemo(() => {
    const todayOnes = tasks.filter((t) => t.tarih === bugun)
    return (todayOnes.length ? todayOnes : tasks.filter((t) => t.status !== 'done')).slice(0, 3)
  }, [tasks, bugun])

  // Zayıf (<%60 doğruluk) ve sıradaki önerilen konular
  const { zayifPerformans, oncelikliKonular } = useMemo(() => {
    const m = new Map<string, { ders: string; konu: string; cozulen: number; dogru: number }>()
    for (const r of soruKayit || []) {
      const k = r?.konu || r?.ders
      if (!k) continue
      const o = m.get(k) || { ders: r.ders || '', konu: k, cozulen: 0, dogru: 0 }
      o.cozulen += Number(r.cozulen) || 0
      o.dogru += Number(r.dogru) || 0
      m.set(k, o)
    }
    const ozet = [...m.values()]
    const zayif = ozet
      .filter((o) => o.cozulen >= 5 && o.dogru / o.cozulen < 0.6)
      .map((o) => ({ ...o, pct: Math.round((o.dogru / o.cozulen) * 100) }))
      .sort((a, b) => a.pct - b.pct)
      .slice(0, 3)
    const oncelik = konuData ? oneriler(konuData, checked, ozet, 2) : []
    return { zayifPerformans: zayif, oncelikliKonular: oncelik }
  }, [konuData, checked, soruKayit])

  const firstName = user?.displayName ? user.displayName.split(' ')[0] : ''
  const isPersonalized = ready && (
    Boolean(user) ||
    gunlukHedef > 0 ||
    Boolean(config?.kuruldu) ||
    Boolean(hedefBolum) ||
    tasks.length > 0 ||
    soruKayit.length > 0 ||
    tercihItems.length > 0
  )

  useEffect(() => {
    onPersonalStateChange?.({
      ready,
      isPersonalized,
      firstName,
      track,
      hedefBolum,
    })
  }, [onPersonalStateChange, ready, isPersonalized, firstName, track, hedefBolum])

  async function runCoachCommand(commandText: string) {
    const text = commandText.trim()
    if (!text || cmdLoading) return
    setCmdLoading(true)
    setCmdReply('')
    setCmdActions([])
    try {
      const data = await api.ask(text, {
        top_k: 6,
        user_context: {
          exam_track: track,
          ...(gunlukHedef > 0 ? { gunluk_soru_hedef: gunlukHedef } : {}),
          bugun_cozulen_soru: bugunCozulen,
          ...(zayifPerformans.length ? { calisma_zayif: zayifPerformans.map((z) => z.konu) } : {}),
        },
      })
      let applied: AppliedActionResult[] = []
      if (Array.isArray(data?.actions) && data.actions.length > 0) {
        applied = await executeCoachActions(data.actions, { user, defaultTrack: track })
      }
      setCmdActions(applied)
      setCmdReply(data?.text || '')
      setCmd('')
      await refreshState()
    } catch (e: any) {
      setCmdReply(`⚠️ ${e?.message || 'AI koça ulaşılamadı.'}`)
    } finally {
      setCmdLoading(false)
    }
  }

  async function handleQuickLog(count: number) {
    if (quickBusy) return
    setQuickBusy(true)
    try {
      const applied = await executeCoachActions(
        [
          {
            type: 'log_questions',
            label: `${track} · ${count} soru kaydedildi`,
            auto_apply: true,
            payload: { sinav: track, ders: 'Genel', konu: 'Günlük Pratik', cozulen: count, dogru: count },
          },
        ],
        { user, defaultTrack: track }
      )
      setCmdActions(applied)
      await refreshState()
    } finally {
      setQuickBusy(false)
    }
  }

  async function handleMarkWeakDone(konu: string) {
    if (quickBusy) return
    setQuickBusy(true)
    try {
      const applied = await executeCoachActions(
        [
          {
            type: 'mark_topic_done',
            label: `${track} · '${konu}' tamamlandı`,
            auto_apply: true,
            payload: { sinav: track, konu },
          },
        ],
        { user, defaultTrack: track }
      )
      setCmdActions(applied)
      await refreshState()
    } finally {
      setQuickBusy(false)
    }
  }

  async function handleToggleTask(task: any) {
    const nextStatus = task.status === 'done' ? 'planned' : 'done'
    if (user?.uid) {
      const planMod = await import('@/services/firestore-plan')
      await planMod.updatePlanGorev(user.uid, task.id, { status: nextStatus }).catch(() => {})
      if (nextStatus === 'done') {
        await planMod.recordActivity(user.uid).catch(() => {})
      }
    } else {
      const next = tasks.map((t) => (t.id === task.id ? { ...t, status: nextStatus } : t))
      setTasks(next)
      try {
        localStorage.setItem(`unisense_plan_${hafta}`, JSON.stringify(next))
      } catch { /* noop */ }
      if (nextStatus === 'done') {
        const planMod = await import('@/services/firestore-plan')
        await planMod.recordActivity(null).catch(() => {})
      }
    }
  }

  return (
    <div className="card border-accent-500/25 bg-gradient-to-br from-brand-500/10 via-slate-900/60 to-accent-500/10 space-y-5">
      {/* Üst Başlık ve Sınav Seçici */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-accent-300 mb-1">
            <Sparkles size={13} />
            {isPersonalized ? 'Kişiye Özel AI Çalışma & Tercih Panosu' : 'Kişiye Özel AI Sayfanı Oluştur'}
          </div>
          {!hideHeaderTitle && (
            <h2 className="font-display font-bold text-xl text-white">
              {isPersonalized
                ? `${firstName ? `${firstName} için` : 'Senin'} ${track} Çalışma Alanın`
                : `${track} AI Çalışma Planını & Günlük Kotanı Kur`}
            </h2>
          )}
        </div>

        <div className="inline-flex gap-1 p-1 rounded-xl bg-white/5 border border-white/10" role="group" aria-label="Sınav seçimi">
          {SINAVLAR.map((s) => (
            <button
              key={s}
              type="button"
              aria-pressed={track === s}
              onClick={() => setTrack(s)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                track === s
                  ? 'bg-gradient-to-r from-brand-500 to-accent-500 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* 1. Hedef Bölüm & Tercih Listesi Özeti Şeridi */}
      {(hedefBolum || tercihItems.length > 0) && (
        <div className="rounded-xl bg-white/[0.04] border border-white/10 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 flex-wrap">
            <ListChecks size={14} className="text-accent-300 shrink-0" />
            {hedefBolum && (
              <span className="px-2 py-0.5 rounded-full bg-accent-500/20 text-accent-200 border border-accent-500/30 font-medium">
                Hedef: {hedefBolum}
              </span>
            )}
            {tercihItems.length > 0 && (
              <span className="text-slate-300">
                Tercih Listende <strong className="text-white">{tercihItems.length}</strong> bölüm
                {tercihItems[0]?.department_name && (
                  <span className="text-slate-400">
                    {' '}· 1. sıra: {tercihItems[0].department_name} ({tercihItems[0].university_name})
                  </span>
                )}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <Link to="/tercih" className="text-accent-300 hover:underline font-medium">
              Listeye Git →
            </Link>
            <Link to="/oneriler" className="text-slate-400 hover:text-white">
              Öneriler
            </Link>
          </div>
        </div>
      )}

      {/* 2 & 3 & 4: Kişisel Durum Kartları */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* Günlük Soru Kotası + Zayıf Konular */}
        <div className="rounded-xl bg-white/[0.03] border border-white/10 p-4 flex flex-col justify-between gap-3">
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="text-xs text-slate-400 flex items-center gap-1.5">
                <Target size={13} className="text-emerald-400" />
                Bugünkü Soru Kotan
              </div>
              <div className="text-2xl font-display font-bold text-white mt-1">
                {bugunCozulen}{' '}
                <span className="text-sm font-normal text-slate-400">
                  / {gunlukHedef > 0 ? `${gunlukHedef} soru` : 'kota belirle'}
                </span>
              </div>
            </div>
            {gunlukHedef > 0 && (
              <span className={`badge ${hedefOran >= 100 ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' : 'bg-accent-500/15 text-accent-300 border-accent-500/30'} border`}>
                %{hedefOran}
              </span>
            )}
          </div>

          <div className="h-2 rounded-full bg-white/10 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400 transition-all duration-500"
              style={{ width: `${gunlukHedef > 0 ? hedefOran : Math.min(100, bugunCozulen * 2)}%` }}
            />
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-1">
            <button
              type="button"
              disabled={quickBusy}
              onClick={() => handleQuickLog(10)}
              className="px-2.5 py-1 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-200 text-xs font-medium inline-flex items-center gap-1 transition"
            >
              <Plus size={12} /> 10 Soru Ekle
            </button>
            <button
              type="button"
              disabled={quickBusy}
              onClick={() => handleQuickLog(20)}
              className="px-2.5 py-1 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-200 text-xs font-medium inline-flex items-center gap-1 transition"
            >
              <Plus size={12} /> 20 Soru Ekle
            </button>
            {gunlukHedef === 0 && (
              <button
                type="button"
                disabled={cmdLoading}
                onClick={() => runCoachCommand(`${track} günlük 40 soru hedefi koy`)}
                className="px-2.5 py-1 rounded-lg bg-accent-500/20 hover:bg-accent-500/30 border border-accent-500/30 text-accent-200 text-xs font-medium transition"
              >
                40 Soru Kotası Koy
              </button>
            )}
          </div>

          {/* Zayıf Konuların Uyarısı */}
          {zayifPerformans.length > 0 && (
            <div className="pt-2 border-t border-white/5 space-y-1.5">
              <div className="flex items-center justify-between text-[11px] text-amber-300 font-medium">
                <span className="inline-flex items-center gap-1">
                  <AlertTriangle size={11} /> Zayıf Konuların (&lt;%60 doğru)
                </span>
                <Link to="/deneme" className="text-slate-400 hover:text-white">
                  Deneme/Soru →
                </Link>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {zayifPerformans.map((z) => (
                  <button
                    key={z.konu}
                    type="button"
                    disabled={quickBusy}
                    onClick={() => handleMarkWeakDone(z.konu)}
                    title="Tıkla → tamamlandı işaretle"
                    className="text-[11px] px-2 py-0.5 rounded-full bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-200 transition"
                  >
                    {z.konu} · %{z.pct}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Bugünkü AI Görevleri & Sıradaki Eksik Konular */}
        <div className="rounded-xl bg-white/[0.03] border border-white/10 p-4 flex flex-col justify-between gap-3">
          <div className="flex items-center justify-between gap-2">
            <div className="text-xs text-slate-400 flex items-center gap-1.5">
              <Flame size={13} className="text-amber-400" />
              Bugünkü Çalışma Görevlerin
            </div>
            <Link to="/planim" className="text-xs text-accent-300 hover:underline inline-flex items-center gap-1">
              Planım <ArrowRight size={11} />
            </Link>
          </div>

          {bugunGorevler.length > 0 ? (
            <ul className="space-y-1.5">
              {bugunGorevler.map((t) => {
                const done = t.status === 'done'
                return (
                  <li key={t.id}>
                    <button
                      type="button"
                      onClick={() => handleToggleTask(t)}
                      className={`w-full text-left px-2.5 py-1.5 rounded-lg border text-xs flex items-center gap-2 transition ${
                        done
                          ? 'bg-emerald-500/10 border-emerald-500/20 text-slate-400 line-through'
                          : 'bg-white/[0.02] hover:bg-white/[0.06] border-white/10 text-slate-200'
                      }`}
                    >
                      {done
                        ? <CheckCircle2 size={14} className="text-emerald-400 shrink-0" />
                        : <Circle size={14} className="text-slate-500 shrink-0" />}
                      <span className="truncate">{t.title || t.konu}</span>
                    </button>
                  </li>
                )
              })}
            </ul>
          ) : (
            <div className="text-xs text-slate-400 space-y-2">
              <p>Henüz bugüne ait çalışma planın yok — Gemini ile saniyeler içinde oluşturabilirsin.</p>
              <button
                type="button"
                disabled={cmdLoading}
                onClick={() => runCoachCommand(`${track} 30 günde konuları bitir, günde 40 soru`)}
                className="btn-ghost !py-1.5 !px-3 text-xs inline-flex items-center gap-1.5"
              >
                <Sparkles size={12} className="text-accent-300" /> AI ile 30 Günlük Plan Kur
              </button>
            </div>
          )}

          {oncelikliKonular.length > 0 && (
            <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-white/5 text-[11px] text-slate-400">
              <div className="flex flex-wrap items-center gap-1.5">
                <BookOpen size={11} className="text-cyber-cyan shrink-0" />
                <span>Sıradaki:</span>
                {oncelikliKonular.map((z: any) => (
                  <button
                    key={`${z.ders}-${z.konu}`}
                    type="button"
                    disabled={quickBusy}
                    onClick={() => handleMarkWeakDone(z.konu)}
                    title="Tıkla → tamamlandı işaretle"
                    className="px-2 py-0.5 rounded-full bg-white/5 hover:bg-emerald-500/20 border border-white/10 hover:border-emerald-500/30 text-slate-200 transition"
                  >
                    {z.konu}
                  </button>
                ))}
              </div>
              <Link to="/konular" className="text-accent-300 hover:underline">
                Konular →
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Gemini Gerçek Sistem Komut Çubuğu */}
      <div className="space-y-2.5">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            runCoachCommand(cmd)
          }}
          className="flex flex-col sm:flex-row gap-2"
        >
          <input
            value={cmd}
            onChange={(e) => setCmd(e.target.value)}
            aria-label="AI Koça sistem komutu yaz"
            placeholder={`Gemini'ye söyle: örn. "Bana günlük 40 soru hedefi koy" veya "Bugün Matematikten 30 soru 26 doğru çözdüm kaydet"`}
            className="input-glass flex-1 text-sm"
            disabled={cmdLoading}
          />
          <button
            type="submit"
            disabled={cmdLoading || !cmd.trim()}
            className="btn-primary text-sm px-4 py-2.5 shrink-0 inline-flex items-center justify-center gap-1.5 disabled:opacity-50"
          >
            {cmdLoading ? <Loader2 size={15} className="animate-spin" /> : <Send size={14} />}
            Uygula
          </button>
        </form>

        <div className="flex flex-wrap gap-1.5">
          {QUICK_PROMPTS.map((q) => (
            <button
              key={q}
              type="button"
              disabled={cmdLoading}
              onClick={() => runCoachCommand(q)}
              className="text-[11px] px-2.5 py-1 rounded-full bg-white/5 hover:bg-accent-500/15 border border-white/10 hover:border-accent-500/30 text-slate-300 hover:text-white transition"
            >
              ⚡ {q}
            </button>
          ))}
        </div>

        {cmdActions.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-1">
            {cmdActions.map((a, idx) => (
              <span
                key={`${a.type}-${idx}`}
                className={`inline-flex items-center gap-1.5 text-xs px-3 py-1 rounded-lg border ${
                  a.ok
                    ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-200'
                    : 'bg-rose-500/15 border-rose-500/30 text-rose-200'
                }`}
              >
                <Zap size={12} />
                {a.label}
              </span>
            ))}
          </div>
        )}

        {cmdReply && (
          <div className="rounded-xl bg-white/[0.04] border border-white/10 px-4 py-3 text-xs text-slate-200 whitespace-pre-wrap leading-relaxed">
            {cmdReply}
          </div>
        )}
      </div>
    </div>
  )
}
