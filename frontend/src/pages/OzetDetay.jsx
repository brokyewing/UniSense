import { useState, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Loader2, BookMarked } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { apiFetch } from '../lib/api'

// Tek formül/özet kartının kalıcı sayfası — paylaşılabilir + SEO landing.
// Prerender bu rotayı içerik gömülü statik HTML olarak da üretir (crawler için).
export default function OzetDetay() {
  const { slug } = useParams()
  const [kart, setKart] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    let live = true
    setLoading(true); setNotFound(false)
    apiFetch('/api/v1/ozet-kartlar')
      .then((d) => {
        if (!live) return
        const k = (d.kartlar || []).find((x) => x.slug === slug)
        if (k) setKart(k); else setNotFound(true)
      })
      .catch(() => { if (live) setNotFound(true) })
      .finally(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [slug])

  return (
    <>
      <BackgroundScene />
      {kart && (
        <Seo title={`${kart.baslik} — Formül Özeti | UniSense`}
          description={`${kart.ozet} ${kart.ders} ${kart.konu} formülleri.`}
          path={`/ozet/${slug}`} />
      )}
      <div className="max-w-2xl mx-auto space-y-4">
        <Link to="/ozetler" className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-amber-300">
          <ArrowLeft size={15} /> Tüm formül özetleri
        </Link>

        {loading ? (
          <div className="text-center py-10"><Loader2 className="animate-spin mx-auto text-amber-400" /></div>
        ) : notFound ? (
          <div className="card text-center py-8">
            <p className="text-sm text-slate-400">Bu özet bulunamadı.</p>
            <Link to="/ozetler" className="text-amber-300 text-sm">← Formül özetlerine dön</Link>
          </div>
        ) : (
          <div className="card">
            <div className="text-[11px] uppercase tracking-wider text-amber-300/80 font-semibold mb-1">
              {kart.ders} · {kart.seviye}
            </div>
            <h1 className="text-2xl font-display font-bold text-white flex items-center gap-2">
              <BookMarked size={20} className="text-amber-300" /> {kart.baslik}
            </h1>
            <p className="text-slate-400 text-sm mt-1">{kart.ozet}</p>
            <ul className="mt-4 space-y-1.5">
              {kart.maddeler.map((m, i) => (
                <li key={i} className="text-[14px] font-mono text-slate-100 bg-white/[0.03] border border-white/8 rounded-lg px-3 py-2">{m}</li>
              ))}
            </ul>
            <div className="text-[11px] text-slate-600 mt-4">
              Temel formül seçkisidir — her zaman kendi kaynağınla teyit et.
            </div>
          </div>
        )}
      </div>
    </>
  )
}
