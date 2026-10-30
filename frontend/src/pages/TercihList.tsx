import { useState, useEffect, useNavigate } from 'react'
import { ListChecks, Loader2, Sparkles } from 'lucide-react'
import BackgroundScene from '../components/three/LazyBackgroundScene'
import { useAuth } from '../contexts/AuthContext'
import { apiFetch } from '../lib/api'

export default function TercihList() {
  const nav = useNavigate()
  const { user, isAuthed, loading: authLoading } = useAuth()
  const [mode, setMode] = useState('YKS')
  const [aiOpt, setAiOpt] = useState('')
  const [aiOptLoading, setAiOptLoading] = useState(false)

  useEffect(() => {
    if (!authLoading && !isAuthed) nav('/giris')
  }, [authLoading, isAuthed, nav])

  useEffect(() => {
    import('@/services/api').then(m => m.api.analyticsLog('page_view', '/tercih', user?.uid).catch(() => {}))
  }, [])

  async function optimizeOrder() {
    setAiOptLoading(true)
    setAiOpt('')
    try {
      const r = await apiFetch('/api/v1/ask', { method: 'POST', body: { query: 'Tercih sıralaması optimal mi?' } })
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
        {mode === 'YKS' && (
          <div className="card border-accent-500/30 bg-accent-500/5">
            <div className="flex items-center justify-between gap-2 mb-2">
              <div className="text-sm font-semibold text-white flex items-center gap-2">
                <Sparkles size={16} className="text-accent-300" /> Tercih Sırası Optimizasyonu
              </div>
              <button onClick={optimizeOrder} disabled={aiOptLoading} className="btn-primary text-xs inline-flex items-center gap-1.5 disabled:opacity-50">
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