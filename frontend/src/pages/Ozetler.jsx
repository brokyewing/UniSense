import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { BookMarked, Search, Loader2, ArrowUpRight } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { apiFetch } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import { getUserProfile } from '../firebase'

const SINAVLAR = ['YKS', 'DGS', 'KPSS', 'LGS']

// Bir kartın hangi sınavlara uygun olduğu (ders + seviyeden türetilir).
function kartSinavlari(k) {
  if (k.seviye === 'AYT') return ['YKS'] // yalnız YKS-AYT (ör. logaritma)
  switch (k.ders) {
    case 'Matematik': return ['YKS', 'DGS', 'KPSS', 'LGS']
    case 'Geometri': return ['YKS', 'KPSS', 'DGS', 'LGS']
    case 'Fizik':
    case 'Kimya': return ['YKS', 'LGS']
    default: return ['YKS']
  }
}

// Formül / konu özeti kartları — sınav yoluna (examTrack) göre + aranabilir.
// Her kartın kalıcı SEO sayfası var (/ozet/:slug). Veri: /api/v1/ozet-kartlar.
export default function Ozetler({ embedded = false }) {
  const { user } = useAuth()
  const [kartlar, setKartlar] = useState([])
  const [notLine, setNotLine] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [q, setQ] = useState('')
  const [sinav, setSinav] = useState('YKS')

  useEffect(() => {
    apiFetch('/api/v1/ozet-kartlar')
      .then((d) => { setKartlar(d.kartlar || []); setNotLine(d.not || '') })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  // Varsayılan sınav = profildeki examTrack (kullanıcı seçiciden değiştirebilir)
  useEffect(() => {
    if (!user) return
    getUserProfile(user.uid).then((p) => {
      const t = p?.profile?.examTrack
      if (SINAVLAR.includes(t)) setSinav(t)
    }).catch(() => {})
  }, [user])

  const filtered = useMemo(() => {
    const t = q.trim().toLowerCase()
    return kartlar
      .filter((k) => kartSinavlari(k).includes(sinav))
      .filter((k) => !t || [k.baslik, k.ders, k.konu, ...(k.maddeler || [])].join(' ').toLowerCase().includes(t))
  }, [kartlar, q, sinav])

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

        {/* Sınav seçici — profildeki alana göre açılır */}
        <div className="flex justify-center">
          <div className="inline-flex gap-1 p-1 rounded-xl bg-white/5 border border-white/10">
            {SINAVLAR.map((s) => (
              <button key={s} onClick={() => setSinav(s)}
                className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition ${sinav === s ? 'bg-gradient-to-r from-amber-500 to-orange-600 text-white' : 'text-slate-300 hover:text-white'}`}>{s}</button>
            ))}
          </div>
        </div>

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
          <div className="card text-center py-8 text-sm text-slate-400">
            {q ? `"${q}" için sonuç yok.` : `${sinav} için formül özeti henüz eklenmedi — çok yakında.`}
          </div>
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
