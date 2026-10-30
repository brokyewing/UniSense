import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { ListChecks, Loader2, Sparkles, GitCompare, ShieldCheck, Target as TargetIcon, Rocket } from 'lucide-react'
import BackgroundScene from '../components/three/LazyBackgroundScene'
import { useAuth } from '../contexts/AuthContext'
import { apiFetch } from '../lib/api'
import { useTercihList } from '@/services/hooks'
import { yksLevel } from '../lib/riskLevels'

export default function TercihList() {
  const nav = useNavigate()
  const { user, isAuthed, loading: authLoading } = useAuth()
  const { tercihIds } = useTercihList()
  const [mode, setMode] = useState('YKS')
  const [aiOpt, setAiOpt] = useState('')
  const [aiOptLoading, setAiOptLoading] = useState(false)
  const [selected, setSelected] = useState<string[]>([])
  const [riskCounts, setRiskCounts] = useState<{ safe: number; target: number; reach: number; bilinmez: number }>({ safe: 0, target: 0, reach: 0, bilinmez: 0 })
  const [riskLoading, setRiskLoading] = useState(false)

  useEffect(() => {
    if (!authLoading && !isAuthed) nav('/giris')
  }, [authLoading, isAuthed, nav])

  useEffect(() => {
    import('@/services/api').then(m => m.api.analyticsLog('page_view', '/tercih', user?.uid).catch(() => {}))
  }, [])

  // Risk analizi: tercih listesindeki programların güvenli/hedef/riskli dağılımı
  useEffect(() => {
    if (!user || tercihIds.size === 0) { setRiskCounts({ safe: 0, target: 0, reach: 0, bilinmez: 0 }); return }
    setRiskLoading(true)
    import('@/services/firestore-core').then(m => m.getUserProfile(user.uid)).then((p: any) => {
      const userRank = p?.profile?.rank || p?.profile?.yks_sira || null
      const codes = [...tercihIds]
      return apiFetch('/api/v1/programs/lookup', { method: 'POST', body: { codes } }).then((r: any) => {
        const items = r?.items || []
        const counts = { safe: 0, target: 0, reach: 0, bilinmez: 0 }
        for (const it of items) {
          const lvl = yksLevel(userRank, it?.last_year_base_rank)
          if (lvl === 'safe') counts.safe++
          else if (lvl === 'target') counts.target++
          else if (lvl === 'reach') counts.reach++
          else counts.bilinmez++
        }
        setRiskCounts(counts)
      })
    }).catch(() => setRiskCounts({ safe: 0, target: 0, reach: 0, bilinmez: 0 }))
      .finally(() => setRiskLoading(false))
  }, [user, tercihIds])

  async function optimizeOrder() {
    setAiOptLoading(true)
    setAiOpt('')
    try {
      const r = await apiFetch('/api/v1/ask', { method: 'POST', body: { query: 'Tercih sıralaması optimal mi?' } })
      setAiOpt(r?.text || 'Tavsiye üretilemedi.')
    } catch (e: any) {
      setAiOpt('Tavsiye alınamadı: ' + e.message)
    } finally {
      setAiOptLoading(false)
    }
  }

  function toggleSelect(code: string) {
    setSelected(prev => prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code])
  }

  function compareSelected() {
    if (selected.length < 2) return
    nav(`/karsilastir?d=${selected.join(',')}`)
  }

  const total = riskCounts.safe + riskCounts.target + riskCounts.reach + riskCounts.bilinmez

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
          {selected.length >= 2 && (
            <button onClick={compareSelected} className="btn-primary text-sm inline-flex items-center gap-2">
              <GitCompare size={14} /> Karşılaştır ({selected.length})
            </button>
          )}
        </div>
        <div className="card text-center py-8 text-sm text-slate-400">
          Tercih listenizde <strong className="text-white">{tercihIds.size}</strong> program var.
          <div className="mt-3 flex flex-wrap gap-2 justify-center">
            {[...tercihIds].map((code: any) => (
              <button key={code} onClick={() => toggleSelect(String(code))}
                className={`text-xs px-2.5 py-1 rounded-full border transition ${selected.includes(String(code)) ? 'bg-accent-500/20 border-accent-500/50 text-accent-200' : 'border-white/10 text-slate-400 hover:bg-white/5'}`}>
                {code} {selected.includes(String(code)) ? '✓' : ''}
              </button>
            ))}
          </div>
        </div>
        {/* Risk Analizi */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <ShieldCheck size={16} className="text-accent-300" /> Risk Analizi
            </h2>
            {riskLoading && <Loader2 size={14} className="animate-spin text-accent-400" />}
          </div>
          {total === 0 ? (
            <p className="text-xs text-slate-500">Risk dağılımı hesaplanamadı (puan/sıra bilgisi eksik olabilir).</p>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-xs text-emerald-300 w-20">Güvenli</span>
                <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                  <div className="h-full bg-emerald-500" style={{ width: `${(riskCounts.safe / total) * 100}%` }} />
                </div>
                <span className="text-xs text-slate-400 w-8 text-right">{riskCounts.safe}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-amber-300 w-20">Hedef</span>
                <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                  <div className="h-full bg-amber-500" style={{ width: `${(riskCounts.target / total) * 100}%` }} />
                </div>
                <span className="text-xs text-slate-400 w-8 text-right">{riskCounts.target}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-rose-300 w-20">Riskli</span>
                <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                  <div className="h-full bg-rose-500" style={{ width: `${(riskCounts.reach / total) * 100}%` }} />
                </div>
                <span className="text-xs text-slate-400 w-8 text-right">{riskCounts.reach}</span>
              </div>
              {riskCounts.bilinmez > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500 w-20">Bilinmez</span>
                  <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                    <div className="h-full bg-slate-500" style={{ width: `${(riskCounts.bilinmez / total) * 100}%` }} />
                  </div>
                  <span className="text-xs text-slate-400 w-8 text-right">{riskCounts.bilinmez}</span>
                </div>
              )}
              <p className="text-[11px] text-slate-500 mt-2">
                Toplam {total} program · {riskCounts.safe} güvenli, {riskCounts.target} hedef, {riskCounts.reach} riskli
              </p>
            </div>
          )}
        </div>
        {mode === 'YKS' && (
          <div className="card border-accent-500/30 bg-accent-500/5">
            <div className="flex items-center justify-between gap-2 mb-2">
              <div className="text-sm font-semibold text-white flex items-center gap-2">
                <Sparkles size={16} className="text-accent-300" /> Tercih Sırası Optimizasyonu
              </div>
              <button onClick={optimizeOrder} disabled={aiOptLoading} className="btn-primary text-xs inline-flex items-center gap-2 disabled:opacity-50">
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
      </div>
    </>
  )
}