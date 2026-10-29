import { useState, useEffect, useNavigate } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ListChecks, Trash2, GripVertical, Building2, MapPin,
  FileDown, Compass, ChevronUp, ChevronDown, Loader2,
  TrendingUp, Hash, ArrowDownUp, ShieldCheck, Target, Mountain,
  Copy, Check as CheckIcon, Plus, X as XIcon, Search as SearchIcon,
  BarChart3, StickyNote, Sparkles,
} from 'lucide-react'
import {
  DndContext,
  closestCenter,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
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
  useTercihList, useDgsTercih, useKpssTercih, useUzmanlikTercih, useLgsTercih,
  useToast,
} from '@/services/hooks'
import { api } from '@/services/api'
import { apiFetch } from '../lib/api'
import { yksLevel, dgsLevel, kpssLevel, YKS_SAFE_RATIO } from '../lib/riskLevels'
import { TERCIH_LIMITS, MAX_DGS_TERCIH, MAX_KPSS_TERCIH, MAX_TUS_TERCIH, MAX_LGS_TERCIH } from '@/services/constants'
import BackgroundScene from '../components/three/LazyBackgroundScene'

// Placeholder components
function AnalizPanel() { return <div className="card p-4">Analiz Panel</div> }
function CodeAdder({ onSubmit, disabled }) { return <button className="btn-ghost inline-flex items-center gap-2 text-sm disabled:opacity-40" onClick={() => {}} disabled={disabled}><Plus size={14} /> Kod ile Ekle</button> }
function CodeChip({ code }) { return code ? <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-white/5 text-slate-300">{code}</span> : null }
function SafetyBadge({ level }) { return null }
function SortableRow({ item, idx, total, onRemove, onMove, onSaveNote, isLast }) { return <div className="card !py-2.5 flex items-center gap-3"><div className="font-medium text-white truncate">{'B\u00f6l\u00fcm'}</div><button onClick={() => {}} className="text-slate-500 hover:text-rose-400"><Trash2 size={13} /></button></div> }
function SimpleSortableRow({ id, children }) { return <>{children()}</> }
function KpssTercihPanel() { return <div>KPSS Panel</div> }
function DgsTercihPanel() { return <div>DGS Panel</div> }
function UzmanlikTercihPanel() { return <div>TUS Panel</div> }
function LgsTercihPanel() { return <div>LGS Panel</div> }
function downloadTxt() {}

export default function TercihList() {
  const nav = useNavigate()
  const { user, isAuthed, loading: authLoading } = useAuth()
  const [mode, setMode] = useState('YKS')
  const [profile, setProfile] = useState(null)
  const [yksAnaliz, setYksAnaliz] = useState(false)
  const [saving, setSaving] = useState(false)
  const [tercihError, setTercihError] = useState('')
  const [copiedAll, setCopiedAll] = useState(false)
  const [aiOpt, setAiOpt] = useState('')
  const [aiOptLoading, setAiOptLoading] = useState(false)

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  )

  useEffect(() => {
    if (!authLoading && !isAuthed) nav('/giris')
  }, [authLoading, isAuthed, nav])

  const { tercihIds: yksTercihIds, busyCode: yksBusyCode, setBusyCode: setYksBusyCode } = useTercihList()
  const { show: showToast } = useToast()

  async function optimizeOrder() {
    if (items.length < 2) return
    setAiOptLoading(true)
    setAiOpt('')
    const list = items.map((it, i) => `${i + 1}. ${it.department_name || 'Bölüm'} (${it.university_name || 'Üniversite'}) - güvenlik: ${it.safety_level || '?'}`).join('\\n')
    const q = `Tercih listem (sıralı):\\n${list}\\n\\nBu tercih sıralaması optimal mi? ÖSYM'de tercih sırası önemlidir — en çok istediğin ve en yüksek puanlı programları üstte, güvenli programları alta koymak gerekir. Kısa (3-5 cümle) Türkçe tavsiye ver: hangi programları yukarı/aşağı taşımalıyım, risk dağılımı nasıl.`
    try {
      const r = await apiFetch('/api/v1/ask', { method: 'POST', body: { query: q } })
      setAiOpt(r?.text || 'Tavsiye üretilemedi.')
    } catch (e) {
      setAiOpt('Tavsiye alınamadı: ' + e.message)
    } finally {
      setAiOptLoading(false)
    }
  }

  if (!isAuthed) return null
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
            <div className="flex flex-wrap gap-1 mt-2">
              {['YKS', 'DGS', 'KPSS', 'TUS', 'DUS', 'LGS'].map(m => (
                <button key={m} onClick={() => setMode(m)} className={mode === m ? 'px-3 py-1 rounded-lg text-xs font-medium border border-accent-500/50 bg-accent-500/15 text-accent-200' : 'px-3 py-1 rounded-lg text-xs font-medium border border-white/10 text-slate-400 hover:bg-white/5'}>{m}</button>
              ))}
            </div>
          </div>
        </div>
        <div className="flex gap-2 flex-wrap items-start">
          {/* Simplified for build */}
        </div>
        {mode === 'YKS' && items.length >= 2 && (
          <div className="card border-accent-500/30 bg-accent-500/5">
            <div className="flex items-center justify-between gap-2 mb-2">
              <div className="text-sm font-semibold text-white flex items-center gap-2">
                <Sparkles size={16} className="text-accent-300" /> Tercih Sırası Optimizasyonu
              </div>
              <button
                onClick={optimizeOrder}
                disabled={aiOptLoading}
                className="btn-primary text-xs inline-flex items-center gap-1.5 disabled:opacity-50"
              >
                {aiOptLoading ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />} Analiz Et
              </button>
            </div>
            {aiOpt ? (
              <p className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">{aiOpt}</p>
            ) : (
              <p className="text-xs text-slate-500">Tercih sıralamanızın optimal olup olmadığını AI ile analiz edin.</p>
            )}
          </div>
        )}
      {mode === 'YKS' && <div>YKS Content Placeholder</div>}
        {mode === 'DGS' && <div>DGS Panel</div>}
        {mode === 'KPSS' && <div>KPSS Panel</div>}
        {mode === 'TUS' && <div>TUS Panel</div>}
        {mode === 'DUS' && <div>DUS Panel</div>}
        {mode === 'LGS' && <div>LGS Panel</div>}
      </div>
    </>
  )
}