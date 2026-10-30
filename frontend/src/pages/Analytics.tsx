import { useState, useEffect } from 'react'
import { BarChart3, Users, Eye, Activity, Trash2, Loader2 } from 'lucide-react'
import BackgroundScene from '../components/three/LazyBackgroundScene'
import Seo from '../components/Seo'
import { api } from '@/services/api'
import { useAuth } from '../contexts/AuthContext'

export default function Analytics() {
  const { user, isAuthed } = useAuth()
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isAuthed) return
    setLoading(true)
    api.analyticsSummary()
      .then(setSummary)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [isAuthed])

  const handleClear = async () => {
    if (!confirm('Analytics verisini temizlemek istediğine emin misin?')) return
    try {
      await api.analyticsClear()
      setSummary({ total_events: 0, unique_users: 0, top_pages: [], top_events: [], daily_active: 0 })
    } catch (e: any) {
      setError(e.message)
    }
  }

  if (!isAuthed) {
    return (
      <div className="text-center py-16">
        <p className="text-slate-400">Analytics paneli için giriş yapmalısın.</p>
      </div>
    )
  }

  return (
    <>
      <BackgroundScene />
      <div className="space-y-5">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-3xl font-display font-bold text-white flex items-center gap-2">
              <BarChart3 className="text-accent-400" size={26} /> Analytics
            </h1>
            <p className="text-sm text-slate-400 mt-1">Kullanıcı davranış analizi ve istatistikler</p>
          </div>
          <button
            onClick={handleClear}
            className="btn-ghost text-xs inline-flex items-center gap-2 text-rose-300 hover:text-rose-200"
          >
            <Trash2 size={14} /> Veriyi Temizle
          </button>
        </div>

        {loading ? (
          <div className="text-center py-10">
            <Loader2 className="animate-spin mx-auto text-accent-400" size={24} />
          </div>
        ) : error ? (
          <div className="card text-center text-rose-300">⚠️ {error}</div>
        ) : summary ? (
          <>
            {/* Özet kartları */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="card text-center !py-3">
                <Activity size={16} className="mx-auto text-accent-300" />
                <div className="text-2xl font-bold text-white mt-1">{summary.total_events}</div>
                <div className="text-[11px] text-slate-500">Toplam Olay</div>
              </div>
              <div className="card text-center !py-3">
                <Users size={16} className="mx-auto text-emerald-300" />
                <div className="text-2xl font-bold text-white mt-1">{summary.unique_users}</div>
                <div className="text-[11px] text-slate-500">Benzersiz Kullanıcı</div>
              </div>
              <div className="card text-center !py-3">
                <Eye size={16} className="mx-auto text-amber-300" />
                <div className="text-2xl font-bold text-white mt-1">{summary.daily_active}</div>
                <div className="text-[11px] text-slate-500">Günlük Aktif</div>
              </div>
              <div className="card text-center !py-3">
                <BarChart3 size={16} className="mx-auto text-violet-300" />
                <div className="text-2xl font-bold text-white mt-1">{summary.top_pages?.length || 0}</div>
                <div className="text-[11px] text-slate-500">Takip Edilen Sayfa</div>
              </div>
            </div>

            {/* Top pages */}
            {summary.top_pages?.length > 0 && (
              <div className="card">
                <h3 className="text-sm font-semibold text-white mb-3">En Çok Ziyaret Edilen Sayfalar</h3>
                <div className="space-y-2">
                  {summary.top_pages.map((p: any, i: number) => (
                    <div key={i} className="flex items-center justify-between text-sm">
                      <span className="text-slate-300 truncate">{p.page}</span>
                      <span className="text-accent-300 font-mono shrink-0 ml-2">{p.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Top events */}
            {summary.top_events?.length > 0 && (
              <div className="card">
                <h3 className="text-sm font-semibold text-white mb-3">En Çok Gerçekleşen Olaylar</h3>
                <div className="space-y-2">
                  {summary.top_events.map((e: any, i: number) => (
                    <div key={i} className="flex items-center justify-between text-sm">
                      <span className="text-slate-300 truncate">{e.event}</span>
                      <span className="text-emerald-300 font-mono shrink-0 ml-2">{e.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {summary.not && (
              <div className="text-[11px] text-slate-600 text-center px-2">{summary.not}</div>
            )}
          </>
        ) : (
          <div className="card text-center py-8 text-sm text-slate-400">
            Henüz analytics verisi yok.
          </div>
        )}
      </div>
    </>
  )
}