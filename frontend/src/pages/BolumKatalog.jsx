import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Loader2, Search as SearchIcon, BookOpen, ArrowRight } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { apiFetch } from '../lib/api'

const CAT_LABEL = {
  muhendislik: 'Mühendislik', saglik: 'Sağlık', sosyal: 'Sosyal', egitim: 'Eğitim',
  fen: 'Fen', hukuk: 'Hukuk', iktisadi: 'İktisadi/İdari', sanat: 'Sanat',
  ziraat: 'Ziraat/Orman', turizm: 'Turizm', spor: 'Spor', dil: 'Dil',
}

export default function BolumKatalog() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [q, setQ] = useState('')

  useEffect(() => {
    apiFetch('/api/v1/bolumler')
      .then((d) => setItems(d.items || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    const f = q.trim().toLocaleLowerCase('tr')
    if (!f) return items
    return items.filter((it) => it.name.toLocaleLowerCase('tr').includes(f))
  }, [items, q])

  return (
    <>
      <BackgroundScene />
      <Seo
        title="Bölüm Rehberi — Üniversite Bölümleri Tanıtımı | UniSense"
        description="Üniversite bölümleri ne iş yapar, hangi dersleri okur, mezunları nerede çalışır? Bölüm tanıtımları + o bölümü veren üniversitelerin güncel taban puanları."
        path="/bolum"
      />
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="text-center">
          <h1 className="text-4xl md:text-5xl font-display font-bold text-white mb-2">
            Bölüm <span className="gradient-text">Rehberi</span>
          </h1>
          <p className="text-slate-400 max-w-xl mx-auto">
            Bir bölümün ne iş yaptığını, hangi dersleri okuduğunu, mezunların nerede
            çalıştığını öğren — ve o bölümü veren üniversitelerin güncel taban puanlarını gör.
          </p>
        </div>

        <div className="relative max-w-md mx-auto">
          <SearchIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Bölüm ara — örn: bilgisayar, hemşirelik…"
            className="input-glass !pl-9"
          />
        </div>

        {loading ? (
          <div className="text-center py-10"><Loader2 className="animate-spin mx-auto text-accent-400" /></div>
        ) : error ? (
          <div className="card text-center text-rose-300">⚠️ {error}</div>
        ) : (
          <>
            <div className="text-xs text-slate-500 text-center">{filtered.length} bölüm</div>
            <div className="grid sm:grid-cols-2 gap-3">
              {filtered.map((it, i) => (
                <motion.div key={it.slug} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: Math.min(i * 0.01, 0.3) }}>
                  <Link to={`/bolum/${it.slug}`}
                    className="card glass-hover p-4 flex items-start gap-3 group h-full">
                    <div className="w-9 h-9 rounded-xl bg-accent-500/15 text-accent-300 flex items-center justify-center shrink-0">
                      <BookOpen size={16} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <h3 className="font-semibold text-white truncate">{it.name}</h3>
                        <ArrowRight size={14} className="text-slate-500 group-hover:text-accent-300 transition shrink-0" />
                      </div>
                      <div className="flex items-center gap-2 mt-0.5 text-[10px] text-slate-500">
                        {CAT_LABEL[it.category] && <span>{CAT_LABEL[it.category]}</span>}
                        <span>· {it.program_count} program</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1.5 line-clamp-2">{it.summary}</p>
                    </div>
                  </Link>
                </motion.div>
              ))}
            </div>
          </>
        )}
      </div>
    </>
  )
}
