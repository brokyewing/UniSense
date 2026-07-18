import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { BookMarked, Search, Loader2, ArrowUpRight } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { apiFetch } from '../lib/api'

// Formül / konu özeti kartları — ders bazlı, aranabilir. Her kartın kalıcı SEO
// sayfası var (/ozet/:slug). Veri: backend /api/v1/ozet-kartlar (statik JSON).
export default function Ozetler({ embedded = false }) {
  const [kartlar, setKartlar] = useState([])
  const [notLine, setNotLine] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [q, setQ] = useState('')

  useEffect(() => {
    apiFetch('/api/v1/ozet-kartlar')
      .then((d) => { setKartlar(d.kartlar || []); setNotLine(d.not || '') })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    const t = q.trim().toLowerCase()
    if (!t) return kartlar
    return kartlar.filter((k) =>
      [k.baslik, k.ders, k.konu, ...(k.maddeler || [])].join(' ').toLowerCase().includes(t))
  }, [kartlar, q])

  const byDers = useMemo(() => {
    const m = {}
    for (const k of filtered) { (m[k.ders] = m[k.ders] || []).push(k) }
    return m
  }, [filtered])

  return (
    <>
      {!embedded && <BackgroundScene />}
      {!embedded && (
        <Seo title="Formül ve Konu Özetleri — YKS Cheat Sheet | UniSense"
          description="TYT-AYT matematik, geometri, fizik ve kimya formülleri tek yerde. Aranabilir, çevrimdışı erişilebilir konu özetleri — ücretsiz."
          path="/ozetler" />
      )}
      <div className="max-w-3xl mx-auto space-y-5">
        {!embedded && (
          <div className="text-center">
            <h1 className="text-3xl md:text-4xl font-display font-bold text-white mb-1 flex items-center justify-center gap-2">
              <BookMarked className="text-amber-300" /> Formül Özetleri
            </h1>
            <p className="text-slate-400 text-sm">Sık kullanılan formülleri hızlıca gözden geçir.</p>
          </div>
        )}

        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input value={q} onChange={(e) => setQ(e.target.value)}
            placeholder="Formül veya konu ara — ör. pisagor, logaritma, mol..."
            className="input-glass w-full pl-9 text-sm" />
        </div>

        {loading ? (
          <div className="text-center py-10"><Loader2 className="animate-spin mx-auto text-amber-400" /></div>
        ) : error ? (
          <div className="card text-center text-rose-300">⚠️ {error}</div>
        ) : filtered.length === 0 ? (
          <div className="card text-center py-8 text-sm text-slate-400">"{q}" için sonuç yok.</div>
        ) : (
          Object.entries(byDers).map(([ders, ks]) => (
            <div key={ders} className="space-y-2">
              <div className="text-[11px] uppercase tracking-wider text-amber-300/80 font-semibold px-1">{ders}</div>
              {ks.map((k) => (
                <div key={k.slug} className="card">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="font-semibold text-white text-sm">{k.baslik}</div>
                      <div className="text-[11px] text-slate-500">{k.konu} · {k.seviye}</div>
                    </div>
                    <Link to={`/ozet/${k.slug}`} title="Kalıcı sayfa"
                      className="shrink-0 text-slate-500 hover:text-amber-300"><ArrowUpRight size={16} /></Link>
                  </div>
                  <ul className="mt-2.5 space-y-1">
                    {k.maddeler.map((m, i) => (
                      <li key={i} className="text-[13px] font-mono text-slate-200 bg-white/[0.03] border border-white/8 rounded-lg px-2.5 py-1.5">{m}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          ))
        )}

        {!loading && !error && (
          <div className="text-[11px] text-slate-600 text-center px-2">{notLine}</div>
        )}
      </div>
    </>
  )
}
