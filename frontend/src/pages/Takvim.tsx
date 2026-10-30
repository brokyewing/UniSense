import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Calendar, Loader2, ArrowRight } from 'lucide-react'
import BackgroundScene from '../components/three/LazyBackgroundScene'
import Seo from '../components/Seo'
import { apiFetch } from '../lib/api'

interface TakvimEvent {
  id: string
  sinav: string
  tam_ad: string
  tur: string
  tarih: string
  bitis?: string
  devam: boolean
  aciklama: string
  kaynak: string
  tahmini: boolean
  kalan_gun: number
}

export default function Takvim() {
  const [events, setEvents] = useState<TakvimEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    apiFetch('/api/v1/takvim')
      .then((d) => setEvents(d.yaklasan || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <>
      <BackgroundScene />
      <Seo title="Takvim | UniSense" description="Sınav takvimi" path="/takvim" />
      <div className="space-y-5">
        <h1 className="text-3xl font-display font-bold text-white flex items-center gap-2">
          <Calendar className="text-accent-400" size={26} /> Sınav Takvimi
        </h1>
        {loading ? (
          <div className="text-center py-10"><Loader2 className="animate-spin mx-auto text-accent-400" /></div>
        ) : error ? (
          <div className="card text-center text-rose-300">⚠️ {error}</div>
        ) : (
          <div className="space-y-2">
            {events.map((e) => (
              <div key={e.id} className="card !py-2.5 flex items-center gap-3">
                <div className="text-[11px] text-slate-500 font-mono w-24 shrink-0">{e.tarih}</div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-white truncate">{e.tam_ad}</div>
                  <div className="text-[10px] text-slate-500">{e.sinav} · {e.tur}</div>
                </div>
                {e.kalan_gun >= 0 && (
                  <div className="text-xs text-accent-300 font-mono shrink-0">{e.kalan_gun} gün</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  )
}