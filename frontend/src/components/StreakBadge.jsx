import { useState, useEffect } from 'react'
import { Flame } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { getStreak } from '../firebase'

// Günlük çalışma serisi rozeti. compact=true → satır içi küçük; yoksa kart.
export default function StreakBadge({ compact = false }) {
  const { user } = useAuth()
  const [s, setS] = useState({ current: 0, longest: 0 })

  useEffect(() => {
    let ok = true
    getStreak(user?.uid).then((r) => { if (ok) setS(r) }).catch(() => {})
    return () => { ok = false }
  }, [user])

  const active = s.current > 0

  if (compact) {
    return (
      <span title={`${s.current} günlük seri${s.longest ? ` · en uzun ${s.longest}` : ''}`}
        className={`inline-flex items-center gap-1 text-xs font-semibold ${active ? 'text-amber-300' : 'text-slate-500'}`}>
        <Flame size={13} className={active ? 'text-amber-400' : 'text-slate-600'} /> {s.current}
      </span>
    )
  }

  return (
    <div className="card !py-3 flex items-center gap-3">
      <div className={`w-11 h-11 rounded-xl grid place-items-center shrink-0 ${active ? 'bg-amber-500/15' : 'bg-white/5'}`}>
        <Flame size={22} className={active ? 'text-amber-400' : 'text-slate-500'} />
      </div>
      <div className="min-w-0">
        <div className="text-2xl font-display font-bold text-white leading-none">
          {s.current} <span className="text-sm font-normal text-slate-400">günlük seri</span>
        </div>
        <div className="text-[11px] text-slate-500 mt-1">
          {active ? 'Bugün çalıştın 🔥 — seriyi koru!' : 'Bir konu işaretle ya da deneme ekle → seri başlasın'}
          {s.longest > 0 && ` · en uzun ${s.longest}`}
        </div>
      </div>
    </div>
  )
}
