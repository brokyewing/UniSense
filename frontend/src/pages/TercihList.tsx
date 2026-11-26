import { useEffect, useMemo, useRef, useState, type CSSProperties, type ChangeEvent, type MouseEvent, type ReactNode } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import type { User } from 'firebase/auth'
import {
  ListChecks, Trash2, GripVertical, Building2, MapPin,
  FileDown, Compass, ChevronUp, ChevronDown, Loader2,
  TrendingUp, Hash, ArrowDownUp, ShieldCheck, Target, Mountain,
  Copy, Check as CheckIcon, Plus, X as XIcon, Search as SearchIcon,
  BarChart3, StickyNote, Sparkles, GitCompare,
} from 'lucide-react'
import {
  DndContext,
  closestCenter,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useAuth } from '../contexts/AuthContext'
import {
  watchTercihList,
  addToTercih,
  removeFromTercih,
  reorderTercihList,
  backfillTercihList,
  updateTercihNote,
  watchKpssTercih,
  removeFromKpssTercih,
  MAX_KPSS_TERCIH,
  watchDgsTercih,
  removeFromDgsTercih,
  MAX_DGS_TERCIH,
  watchUzmanlikTercih,
  removeFromUzmanlikTercih,
  MAX_TUS_TERCIH,
  watchLgsTercih,
  removeFromLgsTercih,
  MAX_LGS_TERCIH,
  reorderSubcollection,
} from '@/services/firestore-prefs'
import { getUserProfile } from '@/services/firestore-core'
import BackgroundScene from '../components/three/LazyBackgroundScene'
import { apiFetch } from '../lib/api'
import { yksLevel, dgsLevel, kpssLevel, YKS_SAFE_RATIO } from '../lib/riskLevels'

type ExamMode = 'YKS' | 'DGS' | 'KPSS' | 'TUS' | 'DUS' | 'LGS'
type RiskLevel = 'safe' | 'target' | 'reach'

interface UserProfileData {
  examTrack?: string
  rank?: number | null
  yks_sira?: number | null
  kpss?: { score?: number | null }
  dgs?: { score?: number | null; type?: string | null }
}

interface TercihItem {
  id: string
  department_code?: string
  department_name?: string
  university_code?: string | number
  university_name?: string
  city?: string
  score_type?: string | null
  last_year_base_rank?: number | null
  last_year_base_score?: number | null
  quota?: number | null
  safety_level?: string | null
  note?: string
}

interface KpssItem {
  id: string
  kadro_kodu: string
  kurum?: string
  unvan?: string
  il?: string
  puan_turu?: string
  kontenjan?: number | null
  gecmis_taban?: number | null
  eslesme?: string
  ozel_kosullar?: string[]
}

interface DgsItem {
  id: string
  department_code: string
  program_adi?: string
  university_name?: string
  city?: string
  puan_turu?: string
  kontenjan?: number | null
  min_puan?: number | null
}

interface UzmanlikItem {
  id: string
  kod: string
  dal?: string
  kurum?: string
  kontenjan_turu?: string
  min_puan?: number | null
  kontenjan?: number | null
}

interface LgsItem {
  id: string
  okul?: string
  il?: string
  ilce?: string
  tur?: string
  dil?: string
  yuzdelik?: number | null
}

interface LookupProgram {
  found?: boolean
  department_code: string
  department_name?: string
  university_code?: string | number
  university_name?: string
  city?: string
  score_type?: string | null
  last_year_base_rank?: number | null
  last_year_base_score?: number | null
  quota?: number | null
}

interface CodeAdderResult {
  ok: number
  fail: number
}

const EXAM_MODES: ExamMode[] = ['YKS', 'DGS', 'KPSS', 'TUS', 'DUS', 'LGS']

/** Tercih listesini .txt olarak indir (YKS/DGS/KPSS/TUS/DUS/LGS ortak). */
function downloadTxt(fileBase: string, baslik: string, lines: string[], codes: string[]): void {
  const kodListe = codes
    .map((c, idx) => `${(idx + 1).toString().padStart(2, '0')}: ${c}`)
    .join('\n')
  const text =
    `${baslik}\n${'='.repeat(50)}\n\n` +
    `${lines.join('\n\n')}\n\n` +
    `${'-'.repeat(50)}\nÖSYM TERCİH KODLARI (sırasıyla):\n${kodListe}\n\n` +
    `${new Date().toLocaleDateString('tr-TR')}\n`
  const url = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }))
  const a = document.createElement('a')
  a.href = url
  a.download = `${fileBase}-${new Date().toISOString().split('T')[0]}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

/** Backend AskRequest.query max 500 krk sınırı için <= 480 krk tercih sırası özeti. */
function buildOptimizeQuery(items: TercihItem[], userRank: number | null | undefined): string {
  const rankPart = userRank
    ? `Sıralamam: ${Number(userRank).toLocaleString('tr-TR')}.`
    : 'Sıralamam belirtilmedi.'
  const header = `${rankPart} YKS tercih sıram optimal mi?\n`
  const maxLen = 480
  const lines: string[] = []
  let currentLen = header.length

  for (let i = 0; i < items.length; i++) {
    const it = items[i]
    const code = String(it.department_code || it.id)
    const name = (it.department_name || code).slice(0, 32)
    const taban = it.last_year_base_rank != null
      ? Number(it.last_year_base_rank).toLocaleString('tr-TR')
      : '?'
    const line = `${i + 1}. [${code}] ${name} (${taban})`
    const addedLen = (lines.length > 0 ? 1 : 0) + line.length
    if (currentLen + addedLen > maxLen - 16) {
      const rest = items.length - i
      if (rest > 0 && currentLen + 16 <= maxLen) {
        lines.push(`+${rest} tercih daha`)
      }
      break
    }
    lines.push(line)
    currentLen += addedLen
  }

  return (header + lines.join('\n')).slice(0, maxLen)
}

/** ÖSYM kodu rozeti — tıklayınca kopyalar */
function CodeChip({ code }: { code?: string }) {
  const [copied, setCopied] = useState(false)
  if (!code) return null
  async function copy(e: MouseEvent<HTMLButtonElement>) {
    e.stopPropagation()
    try {
      await navigator.clipboard.writeText(String(code))
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* noop */
    }
  }
  return (
    <button
      onClick={copy}
      title="ÖSYM tercih kodu — tıkla, panoya kopyala"
      className={`text-[10px] px-2 py-0.5 rounded font-mono inline-flex items-center gap-1 transition border ${
        copied
          ? 'bg-emerald-500/25 text-emerald-200 border-emerald-500/40'
          : 'bg-white/5 hover:bg-accent-500/20 text-slate-300 hover:text-accent-200 border-white/10'
      }`}
    >
      {copied ? <CheckIcon size={10} /> : <Copy size={10} className="opacity-60" />}
      {copied ? 'kopyalandı' : code}
    </button>
  )
}

// === Kod ile Ekleme widget'ı ===
function CodeAdder({
  onSubmit,
  disabled,
}: {
  onSubmit: (raw: string) => Promise<CodeAdderResult>
  disabled: boolean
}) {
  const [open, setOpen] = useState(false)
  const [text, setText] = useState('')
  const [working, setWorking] = useState(false)
  const [result, setResult] = useState<CodeAdderResult | null>(null)

  async function handle() {
    if (!text.trim() || working) return
    setWorking(true)
    const res = await onSubmit(text)
    setResult(res)
    setText('')
    setWorking(false)
    setTimeout(() => setResult(null), 3500)
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        disabled={disabled}
        className="btn-ghost inline-flex items-center gap-2 text-sm disabled:opacity-40"
        title="9 haneli ÖSYM kodu yapıştırarak ekle"
      >
        <Plus size={14} /> Kod ile Ekle
      </button>
    )
  }

  return (
    <div className="card !p-3 border-accent-500/30 bg-accent-500/5 w-full md:w-[420px]">
      <div className="flex items-center justify-between mb-2">
        <div className="text-xs font-semibold text-accent-200 flex items-center gap-1">
          <Plus size={12} /> ÖSYM Kodu / Kodları Yapıştır
        </div>
        <button
          onClick={() => { setOpen(false); setText(''); setResult(null) }}
          className="text-slate-500 hover:text-white"
        >
          <XIcon size={14} />
        </button>
      </div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={'örn:\n101410163\n203910363, 105610081\nveya tek tek...'}
        rows={3}
        className="input-glass w-full resize-none text-sm font-mono"
        disabled={working}
      />
      <div className="flex items-center justify-between mt-2 gap-2">
        <div className="text-[10px] text-slate-500">
          Birden fazla kod (virgül/boşluk/satır ayırıcı)
        </div>
        <button
          onClick={handle}
          disabled={!text.trim() || working}
          className="btn-primary px-3 py-1.5 text-xs inline-flex items-center gap-1 disabled:opacity-40"
        >
          {working ? (
            <><Loader2 size={11} className="animate-spin" /> Ekleniyor…</>
          ) : (
            <><SearchIcon size={11} /> Bul ve Ekle</>
          )}
        </button>
      </div>
      {result && (
        <div className={`mt-2 text-xs px-2 py-1.5 rounded ${
          result.ok > 0
            ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
            : 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
        }`}>
          {result.ok > 0 && <>✓ {result.ok} program eklendi </>}
          {result.fail > 0 && <span className="text-rose-300">· {result.fail} eklenemedi (mevcut/geçersiz)</span>}
        </div>
      )}
    </div>
  )
}

function SafetyBadge({ level }: { level?: string | null }) {
  const map: Record<RiskLevel, { Icon: typeof ShieldCheck; label: string; cls: string }> = {
    safe:   { Icon: ShieldCheck, label: 'Güvenli', cls: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' },
    target: { Icon: Target,      label: 'Hedef',   cls: 'bg-amber-500/20 text-amber-200 border-amber-500/30' },
    reach:  { Icon: Mountain,    label: 'Risk',    cls: 'bg-rose-500/20 text-rose-200 border-rose-500/30' },
  }
  if (!level || !(level in map)) return null
  const m = map[level as RiskLevel]
  return (
    <span className={`text-[9px] px-1.5 py-0.5 rounded-full border inline-flex items-center gap-0.5 ${m.cls}`}>
      <m.Icon size={9} />{m.label}
    </span>
  )
}

// === Sürüklenebilir tek satır ===
function SortableRow({
  item,
  idx,
  onRemove,
  onMove,
  onSaveNote,
  isLast,
  effectiveSafetyLevel,
  isSelected,
  canSelectMore,
  onToggleSelect,
}: {
  item: TercihItem
  idx: number
  onRemove: (id: string) => void
  onMove: (fromIdx: number, toIdx: number) => void
  onSaveNote: (code: string, note: string) => Promise<void>
  isLast: boolean
  effectiveSafetyLevel?: string | null
  isSelected: boolean
  canSelectMore: boolean
  onToggleSelect: (code: string) => void
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: item.id })

  const style: CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 50 : 'auto',
    opacity: isDragging ? 0.85 : 1,
  }

  const code = String(item.department_code || item.id)
  const hasNote = !!(item.note && item.note.trim())
  const [noteOpen, setNoteOpen] = useState(false)
  const [noteValue, setNoteValue] = useState(item.note || '')
  const [savingNote, setSavingNote] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Firestore'dan gelen item.note değişirse local state'i senkronla
  useEffect(() => {
    setNoteValue(item.note || '')
  }, [item.note, item.id])

  function handleNoteChange(e: ChangeEvent<HTMLTextAreaElement>) {
    const next = e.target.value.slice(0, 500)
    setNoteValue(next)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      setSavingNote(true)
      try {
        await onSaveNote(code, next)
      } finally {
        setSavingNote(false)
      }
    }, 700)
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex flex-col rounded-xl transition group ${
        isDragging
          ? 'bg-accent-500/15 ring-2 ring-accent-500/50 shadow-2xl shadow-accent-500/30'
          : isSelected
            ? 'bg-accent-500/10 ring-1 ring-accent-500/30'
            : 'hover:bg-white/[0.03]'
      }`}
    >
      <div className="flex items-center gap-3 px-3 py-3">
        {/* Karşılaştırma seçimi (2-5 program) */}
        <button
          type="button"
          onClick={() => onToggleSelect(code)}
          disabled={!isSelected && !canSelectMore}
          aria-label="Karşılaştırma için seç"
          title={
            isSelected
              ? 'Karşılaştırma seçiminden çıkar'
              : canSelectMore
                ? 'Karşılaştırmak için seç (2-5 program)'
                : 'En fazla 5 program seçebilirsin'
          }
          className={`w-5 h-5 rounded border flex items-center justify-center shrink-0 transition ${
            isSelected
              ? 'bg-accent-500 border-accent-400 text-white'
              : 'border-white/20 text-transparent hover:border-accent-400/60 disabled:opacity-30 disabled:cursor-not-allowed'
          }`}
        >
          <CheckIcon size={12} />
        </button>

        {/* Drag tutamacı */}
        <button
          {...attributes}
          {...listeners}
          className="touch-none p-1 -ml-1 text-slate-600 hover:text-accent-300 cursor-grab active:cursor-grabbing transition shrink-0"
          title="Sürükle (veya ↑↓ butonlarını kullan)"
          aria-label="Sürükle"
        >
          <GripVertical size={18} />
        </button>

        {/* Sıra rozeti */}
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-brand-600 to-accent-600 flex items-center justify-center font-display font-bold text-white text-sm shrink-0">
          {idx + 1}
        </div>

        {/* İçerik */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <div className="font-medium text-white truncate">{item.department_name}</div>
            {effectiveSafetyLevel && <SafetyBadge level={effectiveSafetyLevel} />}
            <CodeChip code={code} />
          </div>
          <div className="flex items-center gap-3 mt-0.5 text-xs text-slate-400 flex-wrap">
            <span className="flex items-center gap-1">
              <Building2 size={10} /> {item.university_name}
            </span>
            {item.city && (
              <span className="flex items-center gap-1">
                <MapPin size={10} /> {item.city}
              </span>
            )}
            {item.score_type && (
              <span className="px-1.5 py-0.5 rounded bg-white/5 text-[10px] font-mono">
                {item.score_type}
              </span>
            )}
          </div>
          {/* Taban + Sıra (varsa) */}
          {(item.last_year_base_rank != null || item.last_year_base_score != null || item.quota != null) && (
            <div className="flex items-center gap-3 mt-1 text-[11px] flex-wrap">
              {item.last_year_base_rank != null && (
                <span className="flex items-center gap-1 text-cyber-cyan font-mono" title="Geçen yıl en düşük başarı sırası">
                  <Hash size={10} className="opacity-60" />
                  {Number(item.last_year_base_rank).toLocaleString('tr')}
                  <span className="text-slate-500 font-sans text-[10px]">sıra</span>
                </span>
              )}
              {item.last_year_base_score != null && (
                <span className="flex items-center gap-1 text-accent-300 font-mono" title="Geçen yıl taban puan">
                  <TrendingUp size={10} className="opacity-60" />
                  {Number(item.last_year_base_score).toFixed(2)}
                  <span className="text-slate-500 font-sans text-[10px]">taban</span>
                </span>
              )}
              {item.quota != null && (
                <span className="flex items-center gap-1 text-slate-400 font-mono" title="Kontenjan">
                  {Number(item.quota).toLocaleString('tr')}
                  <span className="text-slate-500 font-sans text-[10px]">kontenjan</span>
                </span>
              )}
            </div>
          )}
        </div>

        {/* ↑↓ yedek butonlar (touch + accessibility) */}
        <div className="flex items-center gap-0.5 shrink-0">
          <button
            onClick={() => onMove(idx, idx - 1)}
            disabled={idx === 0}
            title="Yukarı taşı"
            className="w-7 h-7 rounded-md text-slate-500 hover:bg-white/10 hover:text-accent-300 disabled:opacity-20 disabled:cursor-not-allowed transition flex items-center justify-center"
          >
            <ChevronUp size={14} />
          </button>
          <button
            onClick={() => onMove(idx, idx + 1)}
            disabled={isLast}
            title="Aşağı taşı"
            className="w-7 h-7 rounded-md text-slate-500 hover:bg-white/10 hover:text-accent-300 disabled:opacity-20 disabled:cursor-not-allowed transition flex items-center justify-center"
          >
            <ChevronDown size={14} />
          </button>
        </div>

        {/* Not toggle */}
        <button
          onClick={() => setNoteOpen((o) => !o)}
          title={hasNote ? 'Notu düzenle' : 'Kişisel not ekle'}
          className={`p-1 rounded transition ml-1 ${
            hasNote || noteOpen
              ? 'text-amber-300 hover:text-amber-200'
              : 'text-slate-500 hover:text-amber-300 opacity-0 group-hover:opacity-100'
          }`}
        >
          <StickyNote size={14} />
        </button>

        {/* Sil */}
        <button
          onClick={() => onRemove(item.id)}
          title="Listeden çıkar"
          className="text-slate-500 hover:text-rose-400 transition opacity-0 group-hover:opacity-100 ml-1"
        >
          <Trash2 size={14} />
        </button>
      </div>

      {/* Kişisel not — expandable */}
      <AnimatePresence initial={false}>
        {(noteOpen || hasNote) && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-3 pt-1 ml-12">
              <div className="flex items-center gap-2 mb-1">
                <StickyNote size={11} className="text-amber-300" />
                <span className="text-[10px] text-slate-500 font-medium">KİŞİSEL NOT</span>
                {savingNote && (
                  <span className="text-[10px] text-accent-400 inline-flex items-center gap-0.5">
                    <Loader2 size={9} className="animate-spin" /> kaydediliyor
                  </span>
                )}
                <span className="text-[10px] text-slate-600 ml-auto">{noteValue.length}/500</span>
              </div>
              <textarea
                value={noteValue}
                onChange={handleNoteChange}
                placeholder="Bu tercih hakkında not yaz… (ör. burs miktarı, ulaşım, akrabalık, ÖSYM puanın uygunluğu…)"
                maxLength={500}
                rows={2}
                className="w-full text-xs rounded-lg bg-white/[0.03] border border-white/10 focus:border-amber-500/40 focus:outline-none focus:ring-1 focus:ring-amber-500/40 px-3 py-2 text-slate-200 placeholder-slate-600 resize-y min-h-[44px]"
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/** Liste değerlendirme — sınava göre risk analizi (tamamen client-side).
 *  YKS: profil sırası vs taban sıra | KPSS: puan vs geçmiş taban | DGS: puan vs taban */
function AnalizPanel({
  mode,
  items,
  profile,
}: {
  mode: 'YKS' | 'KPSS' | 'DGS'
  items: Array<TercihItem | KpssItem | DgsItem>
  profile: UserProfileData | null
}) {
  const rows: Array<{ ad: string; alt: string; durum: string; sira: number }> = []
  const uyarilar: string[] = []
  let guvenli = 0, hedef = 0, riskli = 0, verisiz = 0

  const YKS_ETIKET: Record<RiskLevel, string> = { safe: 'güvenli', target: 'hedef', reach: 'riskli' }
  const PUAN_ETIKET: Record<RiskLevel, string> = { safe: 'yüksek şans', target: 'sınırda', reach: 'riskli' }
  const say = (lvl: string | null) => {
    if (lvl === 'safe') guvenli++
    else if (lvl === 'target') hedef++
    else if (lvl === 'reach') riskli++
  }

  if (mode === 'YKS') {
    const yksItems = items as TercihItem[]
    const rank = profile?.rank ?? profile?.yks_sira ?? null
    if (!rank) {
      uyarilar.push("Profilinde başarı sıralaman yok — Profil → Sınav Profilim'den ekle, analiz kişiselleşsin.")
    }
    yksItems.forEach((it, idx) => {
      const taban = it.last_year_base_rank
      const lvl = yksLevel(rank, taban)
      const durum = lvl && lvl in YKS_ETIKET ? YKS_ETIKET[lvl as RiskLevel] : 'veri yok'
      if (lvl === 'safe' || lvl === 'target' || lvl === 'reach') say(lvl)
      else if (!taban) verisiz++
      rows.push({ ad: it.department_name || it.id, alt: it.university_name || '', durum, sira: idx + 1 })
    })
    for (let i = 0; i < yksItems.length - 1; i++) {
      const a = yksItems[i]?.last_year_base_rank
      const b = yksItems[i + 1]?.last_year_base_rank
      if (a && b && a > b * 1.5) {
        uyarilar.push(`${i + 1}. tercihin (taban sıra ${a.toLocaleString('tr-TR')}) ${i + 2}.'den belirgin kolay — oraya yerleşirsen alttaki daha çok istediğin programlar hiç değerlendirilmez. Sırayı isteğine göre gözden geçir.`)
        break
      }
    }
    if (rank && guvenli === 0 && yksItems.length > 0) {
      uyarilar.push(`Listende GÜVENLİ tercih yok — açıkta kalma riskine karşı sıralamanın ${YKS_SAFE_RATIO} katı ve üzeri tabanlı birkaç program ekle.`)
    }
  } else if (mode === 'KPSS') {
    const kpssItems = items as KpssItem[]
    const puan = profile?.kpss?.score ?? null
    if (!puan) uyarilar.push("Profilinde KPSS puanın yok — Hesap → KPSS'den hesaplayıp kaydet.")
    kpssItems.forEach((it, idx) => {
      const taban = it.gecmis_taban
      const lvl = taban != null && puan ? kpssLevel(puan, taban) : null
      const durum = lvl && lvl in PUAN_ETIKET ? PUAN_ETIKET[lvl as RiskLevel] : 'geçmiş veri yok'
      if (lvl === 'safe' || lvl === 'target' || lvl === 'reach') say(lvl)
      else if (taban == null) verisiz++
      rows.push({ ad: `${it.unvan || ''} · ${it.il || ''}`, alt: it.kurum || '', durum, sira: idx + 1 })
    })
    if (kpssItems.length > 0) {
      uyarilar.push('Tabanlar geçmiş dönemden — kontenjan/talep değişebilir. ⚠️ işaretli kadroların özel koşullarını kılavuzdan doğrula.')
    }
  } else {
    const dgsItems = items as DgsItem[]
    const puan = profile?.dgs?.score ?? null
    const tur = profile?.dgs?.type ?? null
    if (!puan) uyarilar.push("Profilinde DGS puanın yok — Hesap → DGS'den hesaplayıp kaydet.")
    dgsItems.forEach((it, idx) => {
      const taban = it.min_puan
      let durum = 'taban yok (geçen yıl boş)'
      if (tur && it.puan_turu && it.puan_turu !== tur) {
        durum = `puan türü farklı (${it.puan_turu})`
        verisiz++
      } else if (taban != null && puan != null) {
        const lvl = dgsLevel(puan, taban)
        if (lvl && lvl in PUAN_ETIKET) {
          durum = PUAN_ETIKET[lvl as RiskLevel]
          say(lvl)
        }
      } else if (taban != null && puan == null) {
        durum = 'veri yok'
      }
      rows.push({ ad: it.program_adi || it.department_code, alt: it.city || '', durum, sira: idx + 1 })
    })
  }

  const renk = (d: string) =>
    d.includes('güvenli') || d.includes('yüksek') ? 'text-emerald-300'
    : d.includes('hedef') || d.includes('sınırda') ? 'text-amber-300'
    : d.includes('riskli') || d.includes('farklı') ? 'text-rose-400'
    : 'text-slate-500'

  return (
    <div className="card space-y-3">
      <div className="flex flex-wrap gap-3 text-xs">
        <span className="text-emerald-300">● {guvenli} güvenli/yüksek şans</span>
        <span className="text-amber-300">● {hedef} hedef/sınırda</span>
        <span className="text-rose-400">● {riskli} riskli</span>
        {verisiz > 0 && <span className="text-slate-500">● {verisiz} veri yok</span>}
      </div>
      {uyarilar.map((u, i) => (
        <div key={i} className="text-xs text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
          💡 {u}
        </div>
      ))}
      <div className="max-h-56 overflow-y-auto space-y-1 pr-1">
        {rows.map((r) => (
          <div key={r.sira} className="flex items-center gap-2 text-xs">
            <span className="w-5 text-slate-500">{r.sira}.</span>
            <span className="flex-1 min-w-0 truncate text-slate-300" title={r.alt}>{r.ad}</span>
            <span className={renk(r.durum)}>{r.durum}</span>
          </div>
        ))}
      </div>
      <div className="text-[10px] text-slate-600">
        ⓘ Analiz geçen yıl verilerine dayalı kaba bir rehberdir; kesin karar için resmi kılavuzları esas al.
      </div>
    </div>
  )
}

/** KPSS/DGS/TUS/DUS/LGS listeleri için basit sürüklenebilir satır */
function SimpleSortableRow({
  id,
  children,
}: {
  id: string
  children: (grip: ReactNode) => ReactNode
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id })
  return (
    <div
      ref={setNodeRef}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
        zIndex: isDragging ? 50 : 'auto',
        opacity: isDragging ? 0.85 : 1,
      }}
      className={isDragging ? 'ring-2 ring-accent-500/50 rounded-2xl' : ''}
    >
      {children(
        <button
          {...attributes}
          {...listeners}
          className="touch-none p-1 text-slate-600 hover:text-accent-300 cursor-grab active:cursor-grabbing shrink-0"
          title="Sürükle"
        >
          <GripVertical size={14} />
        </button>
      )}
    </div>
  )
}

/** KPSS tercih listesi — YKS listesinden AYRI alan (merkezi yerleştirme, max 30) */
function KpssTercihPanel({ user, profile }: { user: User; profile: UserProfileData | null }) {
  const [items, setItems] = useState<KpssItem[]>([])
  const [analiz, setAnaliz] = useState(false)
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  )

  useEffect(() => {
    return watchKpssTercih(user.uid, (docs) => setItems(docs as KpssItem[]))
  }, [user])

  async function remove(code: string) {
    try { await removeFromKpssTercih(user.uid, code) } catch { /* noop */ }
  }

  function copyAll() {
    navigator.clipboard?.writeText(items.map((i) => i.kadro_kodu).join('\n'))
  }

  function exportText() {
    const lines = items.map((k, idx) => {
      const meta = [`kontenjan ${k.kontenjan ?? '?'}`, k.puan_turu]
      if (k.gecmis_taban != null) meta.push(`geçen dönem taban ${Number(k.gecmis_taban).toFixed(2)}`)
      const kosul = k.ozel_kosullar?.length ? `\n      ⚠️ ${k.ozel_kosullar.join(' | ')}` : ''
      return `${(idx + 1).toString().padStart(2, '0')}. [${k.kadro_kodu}] ${k.unvan} — ${k.il}\n` +
             `      ${k.kurum}\n      ${meta.filter(Boolean).join(' · ')}${kosul}`
    })
    downloadTxt('unisense-kpss-tercih', 'UniSense KPSS Tercih Listesi', lines,
      items.map((k) => k.kadro_kodu))
  }

  async function onDragEnd(e: DragEndEvent) {
    const { active, over } = e
    if (!over || active.id === over.id) return
    const oldI = items.findIndex((x) => x.kadro_kodu === active.id)
    const newI = items.findIndex((x) => x.kadro_kodu === over.id)
    if (oldI < 0 || newI < 0) return
    const next = arrayMove(items, oldI, newI)
    setItems(next)
    try { await reorderSubcollection(user.uid, 'kpss_tercih', next.map((x) => x.kadro_kodu)) } catch { /* noop */ }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-sm text-slate-400">
          {items.length} / {MAX_KPSS_TERCIH} kadro — KPSS tercihleri ÖSYM takvimindeki dönemde
          <a href="https://ais.osym.gov.tr" target="_blank" rel="noreferrer"
            className="text-accent-300 hover:underline ml-1">ais.osym.gov.tr</a>'de yapılır
        </p>
        <div className="flex gap-2">
          {items.length > 0 && (
            <button onClick={() => setAnaliz((a) => !a)}
              className={`btn-ghost text-xs inline-flex items-center gap-1 ${analiz ? '!text-accent-300' : ''}`}>
              <BarChart3 size={12} /> {analiz ? 'Analizi kapat' : 'Listemi Değerlendir'}
            </button>
          )}
          {items.length > 0 && (
            <button onClick={exportText} className="btn-ghost text-xs inline-flex items-center gap-1">
              <FileDown size={12} /> Listeyi İndir
            </button>
          )}
          {items.length > 0 && (
            <button onClick={copyAll} className="btn-ghost text-xs inline-flex items-center gap-1">
              <Copy size={12} /> Kadro kodlarını kopyala
            </button>
          )}
        </div>
      </div>
      {analiz && items.length > 0 && (
        <AnalizPanel mode="KPSS" items={items} profile={profile} />
      )}
      {items.length === 0 ? (
        <div className="card text-center py-10 text-slate-400 text-sm">
          KPSS tercih listen boş. <br />
          <span className="text-slate-500 text-xs">
            Hesap → KPSS sekmesinde bölümünle kadro arayıp "+ Tercih" ile ekleyebilirsin.
          </span>
        </div>
      ) : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
          <SortableContext items={items.map((k) => k.kadro_kodu)} strategy={verticalListSortingStrategy}>
            <div className="space-y-2">
              {items.map((k, idx) => (
                <SimpleSortableRow key={k.kadro_kodu} id={k.kadro_kodu}>
                  {(grip) => (
                    <div className="card !py-3 flex items-center gap-2">
                      {grip}
                      <div className="w-7 h-7 rounded-lg bg-accent-500/20 text-accent-300 text-xs font-bold flex items-center justify-center shrink-0">
                        {idx + 1}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm text-slate-200 font-medium truncate">
                          {k.unvan} · {k.il}
                        </div>
                        <div className="text-xs text-slate-400 truncate">{k.kurum}</div>
                        <div className="text-[10px] text-slate-500 flex gap-3 mt-0.5 flex-wrap">
                          <span className="font-mono">{k.kadro_kodu}</span>
                          <span>Kontenjan: {k.kontenjan ?? '?'}</span>
                          {k.gecmis_taban && (
                            <span className="text-amber-300">Geçen dönem: {Number(k.gecmis_taban).toFixed(2)}</span>
                          )}
                          {k.eslesme?.includes('✓') && (
                            <span className="text-emerald-300">bölüme özel ✓</span>
                          )}
                        </div>
                        {k.ozel_kosullar && k.ozel_kosullar.length > 0 && (
                          <div className="mt-1 space-y-0.5">
                            {k.ozel_kosullar.map((o, i) => (
                              <div key={i} className="text-[10px] text-amber-300 flex items-start gap-1">
                                <span className="shrink-0">⚠️</span>
                                <span className="line-clamp-1">{o}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                      <button onClick={() => remove(k.kadro_kodu)}
                        className="text-slate-500 hover:text-rose-400 text-xs shrink-0">
                        Kaldır
                      </button>
                    </div>
                  )}
                </SimpleSortableRow>
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}
    </div>
  )
}

/** DGS tercih listesi — üçüncü ayrı alan (max 30) */
function DgsTercihPanel({ user, profile }: { user: User; profile: UserProfileData | null }) {
  const [items, setItems] = useState<DgsItem[]>([])
  const [analiz, setAnaliz] = useState(false)
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  )

  useEffect(() => {
    return watchDgsTercih(user.uid, (docs) => setItems(docs as DgsItem[]))
  }, [user])

  function copyAll() {
    navigator.clipboard?.writeText(items.map((i) => i.department_code).join('\n'))
  }

  function exportText() {
    const lines = items.map((p, idx) => {
      const meta = [`kontenjan ${p.kontenjan ?? '?'}`, p.puan_turu]
      if (p.min_puan != null) meta.push(`taban ${Number(p.min_puan).toFixed(2)}`)
      return `${(idx + 1).toString().padStart(2, '0')}. [${p.department_code}] ${p.program_adi}\n` +
             `      ${p.university_name}${p.city ? ' — ' + p.city : ''}\n      ${meta.filter(Boolean).join(' · ')}`
    })
    downloadTxt('unisense-dgs-tercih', 'UniSense DGS Tercih Listesi', lines,
      items.map((p) => p.department_code))
  }

  async function onDragEnd(e: DragEndEvent) {
    const { active, over } = e
    if (!over || active.id === over.id) return
    const oldI = items.findIndex((x) => x.department_code === active.id)
    const newI = items.findIndex((x) => x.department_code === over.id)
    if (oldI < 0 || newI < 0) return
    const next = arrayMove(items, oldI, newI)
    setItems(next)
    try { await reorderSubcollection(user.uid, 'dgs_tercih', next.map((x) => x.department_code)) } catch { /* noop */ }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-sm text-slate-400">
          {items.length} / {MAX_DGS_TERCIH} program — DGS tercihleri ÖSYM takvimindeki
          dönemde <a href="https://ais.osym.gov.tr" target="_blank" rel="noreferrer"
            className="text-accent-300 hover:underline">ais.osym.gov.tr</a>'de yapılır
        </p>
        <div className="flex gap-2">
          {items.length > 0 && (
            <button onClick={() => setAnaliz((a) => !a)}
              className={`btn-ghost text-xs inline-flex items-center gap-1 ${analiz ? '!text-accent-300' : ''}`}>
              <BarChart3 size={12} /> {analiz ? 'Analizi kapat' : 'Listemi Değerlendir'}
            </button>
          )}
          {items.length > 0 && (
            <button onClick={exportText} className="btn-ghost text-xs inline-flex items-center gap-1">
              <FileDown size={12} /> Listeyi İndir
            </button>
          )}
          {items.length > 0 && (
            <button onClick={copyAll} className="btn-ghost text-xs inline-flex items-center gap-1">
              <Copy size={12} /> Program kodlarını kopyala
            </button>
          )}
        </div>
      </div>
      {analiz && items.length > 0 && (
        <AnalizPanel mode="DGS" items={items} profile={profile} />
      )}
      {items.length === 0 ? (
        <div className="card text-center py-10 text-slate-400 text-sm">
          DGS tercih listen boş. <br />
          <span className="text-slate-500 text-xs">
            Hesap → DGS sekmesinde puanını hesaplayıp "+ Tercih" ile program ekleyebilirsin.
          </span>
        </div>
      ) : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
          <SortableContext items={items.map((p) => p.department_code)} strategy={verticalListSortingStrategy}>
            <div className="space-y-2">
              {items.map((p, idx) => (
                <SimpleSortableRow key={p.department_code} id={p.department_code}>
                  {(grip) => (
                    <div className="card !py-3 flex items-center gap-2">
                      {grip}
                      <div className="w-7 h-7 rounded-lg bg-accent-500/20 text-accent-300 text-xs font-bold flex items-center justify-center shrink-0">
                        {idx + 1}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm text-slate-200 font-medium truncate">{p.program_adi}</div>
                        <div className="text-[10px] text-slate-500 flex gap-3 mt-0.5">
                          <span className="font-mono">{p.department_code}</span>
                          <span>{p.city || '—'}</span>
                          <span>{p.puan_turu}</span>
                          {p.min_puan && <span className="text-amber-300">Taban: {Number(p.min_puan).toFixed(2)}</span>}
                          <span>Kontenjan: {p.kontenjan ?? '?'}</span>
                        </div>
                      </div>
                      <button onClick={() => removeFromDgsTercih(user.uid, p.department_code)}
                        className="text-slate-500 hover:text-rose-400 text-xs shrink-0">
                        Kaldır
                      </button>
                    </div>
                  )}
                </SimpleSortableRow>
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}
    </div>
  )
}

/** TUS/DUS uzmanlık tercih listesi — tus_tercih / dus_tercih (max 30). Kişisel kısa liste. */
function UzmanlikTercihPanel({ user, sinav }: { user: User; sinav: 'TUS' | 'DUS' }) {
  const [items, setItems] = useState<UzmanlikItem[]>([])
  const sub = sinav === 'DUS' ? 'dus_tercih' : 'tus_tercih'
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))

  useEffect(() => {
    return watchUzmanlikTercih(user.uid, sinav, (docs) => setItems(docs as UzmanlikItem[]))
  }, [user, sinav])

  function copyAll() {
    navigator.clipboard?.writeText(items.map((i) => i.kod).join('\n'))
  }

  function exportText() {
    const lines = items.map((p, idx) => {
      const meta = [`kontenjan ${p.kontenjan ?? '?'}`, p.kontenjan_turu]
      if (p.min_puan != null) meta.push(`taban ${Number(p.min_puan).toFixed(2)}`)
      return `${(idx + 1).toString().padStart(2, '0')}. [${p.kod}] ${p.dal}\n` +
             `      ${p.kurum || '—'}\n      ${meta.filter(Boolean).join(' · ')}`
    })
    downloadTxt(`unisense-${sinav.toLowerCase()}-tercih`, `UniSense ${sinav} Tercih Listesi`, lines,
      items.map((p) => p.kod))
  }

  async function onDragEnd(e: DragEndEvent) {
    const { active, over } = e
    if (!over || active.id === over.id) return
    const oldI = items.findIndex((x) => x.kod === active.id)
    const newI = items.findIndex((x) => x.kod === over.id)
    if (oldI < 0 || newI < 0) return
    const next = arrayMove(items, oldI, newI)
    setItems(next)
    try { await reorderSubcollection(user.uid, sub, next.map((x) => x.kod)) } catch { /* noop */ }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-sm text-slate-400">
          {items.length} / {MAX_TUS_TERCIH} program — {sinav} tercihleri ÖSYM takvimindeki dönemde
          <a href="https://ais.osym.gov.tr" target="_blank" rel="noreferrer"
            className="text-accent-300 hover:underline ml-1">ais.osym.gov.tr</a>'de yapılır
        </p>
        {items.length > 0 && (
          <div className="flex gap-2">
            <button onClick={exportText} className="btn-ghost text-xs inline-flex items-center gap-1">
              <FileDown size={12} /> İndir
            </button>
            <button onClick={copyAll} className="btn-ghost text-xs inline-flex items-center gap-1">
              <Copy size={12} /> Kodları kopyala
            </button>
          </div>
        )}
      </div>
      {items.length === 0 ? (
        <div className="card text-center py-10 text-slate-400 text-sm">
          {sinav} tercih listen boş. <br />
          <span className="text-slate-500 text-xs">
            {sinav} robotunda puanını girip "+ Tercih" ile program ekleyebilirsin.
          </span>
        </div>
      ) : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
          <SortableContext items={items.map((p) => p.kod)} strategy={verticalListSortingStrategy}>
            <div className="space-y-2">
              {items.map((p, idx) => (
                <SimpleSortableRow key={p.kod} id={p.kod}>
                  {(grip) => (
                    <div className="card !py-3 flex items-center gap-2">
                      {grip}
                      <div className="w-7 h-7 rounded-lg bg-accent-500/20 text-accent-300 text-xs font-bold flex items-center justify-center shrink-0">
                        {idx + 1}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm text-slate-200 font-medium truncate">{p.dal}</div>
                        <div className="text-xs text-slate-400 truncate">{p.kurum || '—'}</div>
                        <div className="text-[10px] text-slate-500 flex gap-3 mt-0.5 flex-wrap">
                          <span className="font-mono">{p.kod}</span>
                          {p.min_puan != null && <span className="text-amber-300">Taban: {Number(p.min_puan).toFixed(2)}</span>}
                          <span>Kontenjan: {p.kontenjan ?? '?'}</span>
                          {p.kontenjan_turu && p.kontenjan_turu !== 'Genel' && <span className="text-fuchsia-300">{p.kontenjan_turu}</span>}
                        </div>
                      </div>
                      <button onClick={() => removeFromUzmanlikTercih(user.uid, sinav, p.kod)}
                        className="text-slate-500 hover:text-rose-400 text-xs shrink-0">
                        Kaldır
                      </button>
                    </div>
                  )}
                </SimpleSortableRow>
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}
    </div>
  )
}

/** LGS lise tercih listesi — lgs_tercih (max 25). Kişisel kısa liste (resmi tercih MEB e-Okul'da). */
function LgsTercihPanel({ user }: { user: User }) {
  const [items, setItems] = useState<LgsItem[]>([])
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))

  useEffect(() => {
    return watchLgsTercih(user.uid, (docs) => setItems(docs as LgsItem[]))
  }, [user])

  function exportText() {
    const lines = items.map((l, idx) => {
      const meta = [`yüzdelik ${l.yuzdelik ?? '?'}`, l.tur, l.dil]
      return `${(idx + 1).toString().padStart(2, '0')}. ${l.okul}\n` +
             `      ${l.ilce ? l.ilce + ' / ' : ''}${l.il}\n      ${meta.filter(Boolean).join(' · ')}`
    })
    downloadTxt('unisense-lgs-tercih', 'UniSense LGS Lise Tercih Listesi', lines,
      items.map((l) => l.okul || l.id))
  }

  async function onDragEnd(e: DragEndEvent) {
    const { active, over } = e
    if (!over || active.id === over.id) return
    const oldI = items.findIndex((x) => x.id === active.id)
    const newI = items.findIndex((x) => x.id === over.id)
    if (oldI < 0 || newI < 0) return
    const next = arrayMove(items, oldI, newI)
    setItems(next)
    try { await reorderSubcollection(user.uid, 'lgs_tercih', next.map((x) => x.id)) } catch { /* noop */ }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-sm text-slate-400">
          {items.length} / {MAX_LGS_TERCIH} lise — resmî LGS tercihi
          <a href="https://www.meb.gov.tr" target="_blank" rel="noreferrer"
            className="text-accent-300 hover:underline ml-1">e-Okul / MEB</a>'de yapılır
        </p>
        {items.length > 0 && (
          <button onClick={exportText} className="btn-ghost text-xs inline-flex items-center gap-1">
            <FileDown size={12} /> Listeyi İndir
          </button>
        )}
      </div>
      {items.length === 0 ? (
        <div className="card text-center py-10 text-slate-400 text-sm">
          LGS tercih listen boş. <br />
          <span className="text-slate-500 text-xs">
            LGS robotunda yüzdeliğini girip "+ Tercih" ile lise ekleyebilirsin.
          </span>
        </div>
      ) : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
          <SortableContext items={items.map((l) => l.id)} strategy={verticalListSortingStrategy}>
            <div className="space-y-2">
              {items.map((l, idx) => (
                <SimpleSortableRow key={l.id} id={l.id}>
                  {(grip) => (
                    <div className="card !py-3 flex items-center gap-2">
                      {grip}
                      <div className="w-7 h-7 rounded-lg bg-accent-500/20 text-accent-300 text-xs font-bold flex items-center justify-center shrink-0">
                        {idx + 1}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm text-slate-200 font-medium truncate">{l.okul}</div>
                        <div className="text-xs text-slate-400 truncate">{l.ilce ? `${l.ilce} / ` : ''}{l.il}</div>
                        <div className="text-[10px] text-slate-500 flex gap-3 mt-0.5 flex-wrap">
                          {l.yuzdelik != null && <span className="text-amber-300">Yüzdelik: %{l.yuzdelik}</span>}
                          <span>{l.tur}</span>
                          <span>{l.dil}</span>
                        </div>
                      </div>
                      <button onClick={() => removeFromLgsTercih(user.uid, l.id)}
                        className="text-slate-500 hover:text-rose-400 text-xs shrink-0">
                        Kaldır
                      </button>
                    </div>
                  )}
                </SimpleSortableRow>
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}
    </div>
  )
}

export default function TercihList() {
  const nav = useNavigate()
  const { user, isAuthed, loading } = useAuth()
  const [items, setItems] = useState<TercihItem[]>([])
  const [mode, setMode] = useState<ExamMode>('YKS')
  const [profile, setProfile] = useState<UserProfileData | null>(null)
  const [yksAnaliz, setYksAnaliz] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [copiedAll, setCopiedAll] = useState(false)
  const [selected, setSelected] = useState<string[]>([])
  const [aiOpt, setAiOpt] = useState('')
  const [aiOptLoading, setAiOptLoading] = useState(false)

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  useEffect(() => {
    if (!loading && !isAuthed) nav('/giris')
  }, [loading, isAuthed, nav])

  useEffect(() => {
    if (!user) return
    return watchTercihList(user.uid, (docs) => setItems(docs as TercihItem[]))
  }, [user])

  // Silinen öğeleri karşılaştırma seçiminden düşür
  useEffect(() => {
    const validCodes = new Set(items.map((i) => String(i.department_code || i.id)))
    setSelected((prev) => prev.filter((c) => validCodes.has(c)))
  }, [items])

  // İlk açılış sekmesi: profildeki sınav yolu + analiz panelleri için profil
  useEffect(() => {
    if (!user) return
    getUserProfile(user.uid).then((p) => {
      const prof = (p?.profile || null) as UserProfileData | null
      setProfile(prof)
      const t = prof?.examTrack
      if (t && (['DGS', 'KPSS', 'TUS', 'DUS', 'LGS'] as string[]).includes(t)) {
        setMode(t as ExamMode)
      }
    }).catch(() => {})
  }, [user])

  // Eksik bilgileri (rank/score/quota) backend'den çek + Firestore'a backfill et
  useEffect(() => {
    if (!user || items.length === 0) return
    const missing = items.filter(
      (it) => it.last_year_base_rank == null || it.last_year_base_score == null
    )
    if (missing.length === 0) return

    const codes = missing.map((it) => String(it.department_code || it.id))
    let cancelled = false
    ;(async () => {
      try {
        const data = await apiFetch('/api/v1/programs/lookup', {
          method: 'POST',
          body: { codes },
        })
        if (cancelled) return

        const codeToData: Record<string, LookupProgram> = {}
        for (const p of (data?.programs || []) as LookupProgram[]) {
          if (p.found) codeToData[p.department_code] = p
        }
        if (Object.keys(codeToData).length === 0) return

        try {
          await backfillTercihList(user.uid, codeToData)
        } catch (e) {
          console.warn('Backfill yazılamadı:', e)
        }

        if (!cancelled) {
          setItems((prev) =>
            prev.map((it) => {
              const code = String(it.department_code || it.id)
              const fresh = codeToData[code]
              if (!fresh) return it
              return {
                ...it,
                last_year_base_rank: fresh.last_year_base_rank ?? it.last_year_base_rank,
                last_year_base_score: fresh.last_year_base_score ?? it.last_year_base_score,
                quota: fresh.quota ?? it.quota,
                score_type: it.score_type || fresh.score_type,
                city: it.city || fresh.city,
                university_name: it.university_name || fresh.university_name,
                department_name: it.department_name || fresh.department_name,
              }
            })
          )
        }
      } catch (e) {
        console.warn('Lookup başarısız:', e)
      }
    })()
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, items.length])

  const userRank = profile?.rank ?? profile?.yks_sira ?? null

  const riskCounts = useMemo(() => {
    const counts = { safe: 0, target: 0, reach: 0, bilinmez: 0 }
    for (const it of items) {
      const lvl = yksLevel(userRank, it.last_year_base_rank)
      if (lvl === 'safe') counts.safe++
      else if (lvl === 'target') counts.target++
      else if (lvl === 'reach') counts.reach++
      else counts.bilinmez++
    }
    return counts
  }, [items, userRank])

  async function handleRemove(code: string) {
    if (!user) return
    try {
      await removeFromTercih(user.uid, code)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  async function handleSaveNote(code: string, note: string) {
    if (!user) return
    try {
      await updateTercihNote(user.uid, code, note)
    } catch (e: unknown) {
      setError('Not kaydedilemedi: ' + (e instanceof Error ? e.message : String(e)))
    }
  }

  async function persistOrder(newItems: TercihItem[]) {
    if (!user) return
    setSaving(true)
    setError('')
    try {
      await reorderTercihList(user.uid, newItems)
    } catch (e: unknown) {
      setError('Sıralama kaydedilemedi: ' + (e instanceof Error ? e.message : String(e)))
    } finally {
      setSaving(false)
    }
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return
    const oldIdx = items.findIndex((i) => i.id === active.id)
    const newIdx = items.findIndex((i) => i.id === over.id)
    if (oldIdx < 0 || newIdx < 0) return
    const next = arrayMove(items, oldIdx, newIdx)
    setItems(next)
    persistOrder(next)
  }

  function handleMove(fromIdx: number, toIdx: number) {
    if (toIdx < 0 || toIdx >= items.length) return
    const next = arrayMove(items, fromIdx, toIdx)
    setItems(next)
    persistOrder(next)
  }

  /** Taban sırasına göre küçükten büyüğe (en iyiden başla) */
  function sortByRank() {
    const next = [...items].sort((a, b) => {
      const ra = a.last_year_base_rank ?? Number.MAX_SAFE_INTEGER
      const rb = b.last_year_base_rank ?? Number.MAX_SAFE_INTEGER
      return ra - rb
    })
    setItems(next)
    persistOrder(next)
  }

  function exportText() {
    const lines = items.map((i, idx) => {
      const code = i.department_code || i.id
      const head = `${(idx + 1).toString().padStart(2, '0')}. [${code}] ${i.department_name}`
      const sub = `      ${i.university_name}${i.city ? ' — ' + i.city : ''}`
      const meta: string[] = []
      if (i.score_type) meta.push(i.score_type)
      if (i.last_year_base_rank != null) meta.push(`sıra ${Number(i.last_year_base_rank).toLocaleString('tr')}`)
      if (i.last_year_base_score != null) meta.push(`taban ${Number(i.last_year_base_score).toFixed(2)}`)
      if (i.quota != null) meta.push(`kontenjan ${i.quota}`)
      const metaLine = meta.length > 0 ? `\n      ${meta.join(' · ')}` : ''
      return `${head}\n${sub}${metaLine}`
    })
    downloadTxt(
      'unisense-tercih',
      'UniSense Tercih Listesi',
      lines,
      items.map((i) => String(i.department_code || i.id))
    )
  }

  // === Kod ile Ekleme ===
  async function addByCodes(rawInput: string): Promise<CodeAdderResult> {
    if (!user) {
      setError('Giriş yapman gerek')
      return { ok: 0, fail: 0 }
    }
    const codes = rawInput
      .split(/[\s,;\n]+/)
      .map((c) => c.trim().replace(/[^0-9]/g, ''))
      .filter((c) => c.length >= 6 && c.length <= 12)
    if (codes.length === 0) {
      setError('Geçerli kod yazılmadı (9 haneli kod bekleniyor)')
      return { ok: 0, fail: 0 }
    }
    if (items.length + codes.length > 24) {
      setError(`Tercih listesi 24 sınırını aşacak (${items.length}+${codes.length}). Önce yer aç.`)
      return { ok: 0, fail: 0 }
    }
    setSaving(true)
    setError('')
    let ok = 0, fail = 0
    try {
      const data = await apiFetch('/api/v1/programs/lookup', {
        method: 'POST',
        body: { codes },
      })
      const found = ((data?.programs || []) as LookupProgram[]).filter((p) => p.found)
      const existing = new Set(items.map((i) => String(i.department_code || i.id)))
      let nextOrder = items.length + 1
      for (const p of found) {
        if (existing.has(String(p.department_code))) {
          fail++
          continue
        }
        try {
          await addToTercih(user.uid, {
            department_code: p.department_code,
            department_name: p.department_name,
            university_code: p.university_code,
            university_name: p.university_name,
            city: p.city,
            score_type: p.score_type || null,
            last_year_base_rank: p.last_year_base_rank ?? null,
            last_year_base_score: p.last_year_base_score ?? null,
            quota: p.quota ?? null,
          }, nextOrder++)
          existing.add(String(p.department_code))
          ok++
        } catch {
          fail++
        }
      }
      const notFound = codes.length - found.length
      if (notFound > 0) {
        setError(`${notFound} kod bulunamadı (geçerli ÖSYM kodu olduğunu kontrol et)`)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
      fail = codes.length
    } finally {
      setSaving(false)
    }
    return { ok, fail }
  }

  async function copyAllCodes() {
    const text = items
      .map((i, idx) => `${(idx + 1).toString().padStart(2, '0')}\t${i.department_code || i.id}`)
      .join('\n')
    try {
      await navigator.clipboard.writeText(text)
      setCopiedAll(true)
      setTimeout(() => setCopiedAll(false), 2000)
    } catch {
      setError('Panoya kopyalanamadı (tarayıcı izni?)')
    }
  }

  function toggleSelect(code: string) {
    setSelected((prev) => {
      if (prev.includes(code)) return prev.filter((c) => c !== code)
      if (prev.length >= 5) return prev
      return [...prev, code]
    })
  }

  function compareSelected() {
    if (selected.length < 2) return
    nav(`/karsilastir?d=${selected.slice(0, 5).join(',')}`)
  }

  async function optimizeOrder() {
    if (items.length === 0) return
    setAiOptLoading(true)
    setAiOpt('')
    try {
      const query = buildOptimizeQuery(items, userRank)
      const r = await apiFetch('/api/v1/ask', {
        method: 'POST',
        body: { query },
      })
      setAiOpt(r?.text || 'Tavsiye üretilemedi.')
    } catch (e: unknown) {
      setAiOpt('Tavsiye alınamadı: ' + (e instanceof Error ? e.message : String(e)))
    } finally {
      setAiOptLoading(false)
    }
  }

  if (!isAuthed) return null

  const remaining = 24 - items.length
  const totalRisk = riskCounts.safe + riskCounts.target + riskCounts.reach + riskCounts.bilinmez

  return (
    <>
      <BackgroundScene />

      <div className="space-y-5">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-display font-bold text-white flex items-center gap-2">
              <ListChecks className="text-accent-400" size={26} />
              Tercih Listen
            </h1>
            {/* Her sınav ayrı liste */}
            <div className="flex flex-wrap gap-1 mt-2">
              {EXAM_MODES.map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium border ${
                    mode === m
                      ? 'border-accent-500/50 bg-accent-500/15 text-accent-200'
                      : 'border-white/10 text-slate-400 hover:bg-white/5'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
            {mode === 'YKS' && (
              <p className="text-sm text-slate-400 mt-1 flex items-center gap-2">
                <span>{items.length} / 24 tercih • {remaining > 0 ? `${remaining} ekleyebilirsin` : 'Liste dolu'}</span>
                {saving && (
                  <span className="text-accent-400 flex items-center gap-1">
                    <Loader2 size={11} className="animate-spin" /> kaydediliyor
                  </span>
                )}
              </p>
            )}
          </div>
          {mode === 'YKS' && (
            <div className="flex gap-2 flex-wrap items-start">
              <CodeAdder
                onSubmit={addByCodes}
                disabled={items.length >= 24}
              />
              {items.length > 0 && (
                <button
                  onClick={copyAllCodes}
                  title="Tüm tercih kodlarını sırayla panoya kopyala"
                  className={`btn-ghost inline-flex items-center gap-2 text-sm ${
                    copiedAll ? '!text-emerald-300' : ''
                  }`}
                >
                  {copiedAll ? <CheckIcon size={14} /> : <Copy size={14} />}
                  {copiedAll ? 'Kopyalandı' : 'Kodları Kopyala'}
                </button>
              )}
              {items.length > 1 && (
                <button
                  onClick={sortByRank}
                  title="Taban sırasına göre yeniden sırala (en iyiden başla)"
                  className="btn-ghost inline-flex items-center gap-2 text-sm"
                >
                  <ArrowDownUp size={14} /> Sıraya Göre Diz
                </button>
              )}
              {items.length > 0 && (
                <button
                  onClick={() => setYksAnaliz((a) => !a)}
                  title="Profilindeki sıralamana göre güvenli/hedef/riskli analizi"
                  className={`btn-ghost inline-flex items-center gap-2 text-sm ${yksAnaliz ? '!text-accent-300' : ''}`}
                >
                  <BarChart3 size={14} /> {yksAnaliz ? 'Analizi Kapat' : 'Listemi Değerlendir'}
                </button>
              )}
              {selected.length >= 2 ? (
                <button
                  onClick={compareSelected}
                  className="btn-primary inline-flex items-center gap-2 text-sm"
                >
                  <GitCompare size={14} /> Karşılaştır ({selected.length})
                </button>
              ) : (
                items.length >= 2 && (
                  <Link
                    to={`/karsilastir?d=${items.slice(0, 5).map((i) => i.department_code || i.id).filter(Boolean).join(',')}`}
                    title="İlk 5 tercihini yan yana karşılaştır (veya satırlardan 2-5 program seç)"
                    className="btn-ghost inline-flex items-center gap-2 text-sm"
                  >
                    <GitCompare size={14} /> Karşılaştır
                  </Link>
                )
              )}
              <Link to="/pusula" className="btn-ghost inline-flex items-center gap-2 text-sm">
                <Compass size={14} /> Pusula
              </Link>
              {items.length > 0 && (
                <button
                  onClick={exportText}
                  className="btn-primary inline-flex items-center gap-2 text-sm"
                >
                  <FileDown size={14} /> Listeyi İndir
                </button>
              )}
            </div>
          )}
        </div>

        {mode === 'KPSS' && user && <KpssTercihPanel user={user} profile={profile} />}
        {mode === 'DGS' && user && <DgsTercihPanel user={user} profile={profile} />}
        {mode === 'TUS' && user && <UzmanlikTercihPanel user={user} sinav="TUS" />}
        {mode === 'DUS' && user && <UzmanlikTercihPanel user={user} sinav="DUS" />}
        {mode === 'LGS' && user && <LgsTercihPanel user={user} />}

        {mode === 'YKS' && yksAnaliz && items.length > 0 && (
          <AnalizPanel mode="YKS" items={items} profile={profile} />
        )}

        {mode === 'YKS' && (
          <>
            {error && (
              <div className="text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-3">
                ⚠️ {error}
              </div>
            )}

            {items.length === 0 ? (
              <div className="card text-center py-12">
                <ListChecks size={40} className="mx-auto text-slate-600 mb-3" />
                <h3 className="font-semibold text-white mb-1">Tercih listen boş</h3>
                <p className="text-sm text-slate-400 mb-4">
                  Önce ilgilerini Pusula'da seç, sonra Tercih sayfasından önerilen programları buraya ekle.
                </p>
                <div className="flex gap-2 justify-center flex-wrap">
                  <Link to="/pusula" className="btn-primary inline-flex items-center gap-2">
                    <Compass size={16} /> Pusulaya Git
                  </Link>
                  <Link to="/oneriler" className="btn-ghost inline-flex items-center gap-2">
                    <ListChecks size={16} /> Tercih Sayfası
                  </Link>
                </div>
              </div>
            ) : (
              <>
                <div className="text-xs text-slate-500 px-1 flex items-center justify-between flex-wrap gap-2">
                  <span>
                    💡 <strong className="text-slate-400">Sürükle</strong> ya da{' '}
                    <ChevronUp size={11} className="inline" /><ChevronDown size={11} className="inline" />{' '}
                    butonlarıyla sıralamayı değiştir. Otomatik kaydedilir.
                  </span>
                  {selected.length > 0 && (
                    <span className="text-accent-300">
                      Karşılaştırma için {selected.length}/5 seçildi {selected.length < 2 && '(en az 2 seç)'}
                    </span>
                  )}
                </div>

                <div className="card p-2">
                  <DndContext
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragEnd={handleDragEnd}
                  >
                    <SortableContext
                      items={items.map((i) => i.id)}
                      strategy={verticalListSortingStrategy}
                    >
                      <AnimatePresence>
                        {items.map((it, idx) => {
                          const code = String(it.department_code || it.id)
                          const effectiveLvl = it.safety_level || yksLevel(userRank, it.last_year_base_rank)
                          return (
                            <motion.div
                              key={it.id}
                              layout
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              exit={{ opacity: 0, scale: 0.95 }}
                            >
                              <SortableRow
                                item={it}
                                idx={idx}
                                isLast={idx === items.length - 1}
                                effectiveSafetyLevel={effectiveLvl}
                                isSelected={selected.includes(code)}
                                canSelectMore={selected.length < 5}
                                onToggleSelect={toggleSelect}
                                onRemove={handleRemove}
                                onMove={handleMove}
                                onSaveNote={handleSaveNote}
                              />
                            </motion.div>
                          )
                        })}
                      </AnimatePresence>
                    </SortableContext>
                  </DndContext>
                </div>

                {/* Risk Analizi özeti */}
                <div className="card">
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                      <ShieldCheck size={16} className="text-accent-300" /> Risk Analizi
                    </h2>
                    {!userRank && (
                      <span className="text-[11px] text-amber-300">Sıralaman profilde yok</span>
                    )}
                  </div>
                  {totalRisk === 0 ? (
                    <p className="text-xs text-slate-500">Risk dağılımı hesaplanamadı (puan/sıra bilgisi eksik olabilir).</p>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-emerald-300 w-20">Güvenli</span>
                        <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                          <div className="h-full bg-emerald-500" style={{ width: `${(riskCounts.safe / totalRisk) * 100}%` }} />
                        </div>
                        <span className="text-xs text-slate-400 w-8 text-right">{riskCounts.safe}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-amber-300 w-20">Hedef</span>
                        <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                          <div className="h-full bg-amber-500" style={{ width: `${(riskCounts.target / totalRisk) * 100}%` }} />
                        </div>
                        <span className="text-xs text-slate-400 w-8 text-right">{riskCounts.target}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-rose-300 w-20">Riskli</span>
                        <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                          <div className="h-full bg-rose-500" style={{ width: `${(riskCounts.reach / totalRisk) * 100}%` }} />
                        </div>
                        <span className="text-xs text-slate-400 w-8 text-right">{riskCounts.reach}</span>
                      </div>
                      {riskCounts.bilinmez > 0 && (
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-500 w-20">Bilinmez</span>
                          <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                            <div className="h-full bg-slate-500" style={{ width: `${(riskCounts.bilinmez / totalRisk) * 100}%` }} />
                          </div>
                          <span className="text-xs text-slate-400 w-8 text-right">{riskCounts.bilinmez}</span>
                        </div>
                      )}
                      <p className="text-[11px] text-slate-500 mt-2">
                        Toplam {totalRisk} program · {riskCounts.safe} güvenli, {riskCounts.target} hedef, {riskCounts.reach} riskli
                      </p>
                    </div>
                  )}
                </div>

                {/* AI Sıralama Optimizasyonu */}
                <div className="card border-accent-500/30 bg-accent-500/5">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="text-sm font-semibold text-white flex items-center gap-2">
                      <Sparkles size={16} className="text-accent-300" /> Tercih Sırası Optimizasyonu
                    </div>
                    <button
                      onClick={optimizeOrder}
                      disabled={aiOptLoading || items.length === 0}
                      className="btn-primary text-xs inline-flex items-center gap-2 disabled:opacity-50"
                    >
                      {aiOptLoading ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />} Analiz Et
                    </button>
                  </div>
                  {aiOpt ? (
                    <p className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">{aiOpt}</p>
                  ) : (
                    <p className="text-xs text-slate-500">
                      Sıralaman ve mevcut YKS tercih sıranla AI değerlendirmesi al.
                    </p>
                  )}
                </div>
              </>
            )}

            {items.length > 0 && (
              <div className="text-center text-xs text-slate-500">
                ⓘ Bu liste cihazına indirilir, ÖSYM'ye otomatik gönderilmez.<br />
                Kesin tercih için: <a href="https://aday.osym.gov.tr/" target="_blank" rel="noreferrer" className="text-accent-400 hover:underline">ÖSYM Aday İşlemleri Sistemi</a>
              </div>
            )}
          </>
        )}
      </div>
    </>
  )
}
