import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Briefcase, Loader2, Search, ExternalLink, Sparkles, BookOpen,
  Landmark, Building2, Globe,
} from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import { apiFetch } from '../lib/api'

const HATLAR = [
  { id: '', label: 'Tümü' },
  { id: 'kamu', label: 'Kamu' },
  { id: 'ozel', label: 'Özel' },
]

const TIP_STIL = {
  portal:      { label: 'Portal',   cls: 'bg-blue-500/15 text-blue-300 border-blue-500/30' },
  kurum:       { label: 'Kurum',    cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
  toplayici:   { label: 'Derleme',  cls: 'bg-amber-500/15 text-amber-300 border-amber-500/30' },
  site_sorgu:  { label: 'Site',     cls: 'bg-violet-500/15 text-violet-300 border-violet-500/30' },
}

const HAT_IKON = { kamu: Landmark, ozel: Building2 }

function SinyalKart({ ilan }) {
  const eslesme = Object.entries(ilan.detay?.eslesme || {}).filter(([, c]) => c > 0)
  return (
    <div className="rounded-xl bg-white/[0.03] border border-white/5 p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-sm text-white leading-tight">{ilan.baslik}</span>
            {ilan.yeni && (
              <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full border bg-emerald-500/15 text-emerald-300 border-emerald-500/30">
                <Sparkles size={10} /> yeni
              </span>
            )}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            {ilan.kaynak} · {ilan.tarih}
            {ilan.detay?.sayfa ? ` · ${ilan.detay.sayfa} sayfa tarandı` : ''}
          </div>
        </div>
        <a
          href={ilan.url} target="_blank" rel="noreferrer"
          className="btn-ghost inline-flex items-center gap-1.5 text-xs shrink-0"
        >
          <ExternalLink size={13} /> Kaynağa git
        </a>
      </div>
      {eslesme.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2.5">
          {eslesme.map(([grup, sayi]) => (
            <span key={grup} className="text-[10px] px-2 py-0.5 rounded-full border bg-accent-500/10 text-accent-200 border-accent-500/30">
              {grup.replaceAll('_', ' ')}: {sayi}
            </span>
          ))}
        </div>
      )}
      {ilan.detay?.pdfler?.length > 0 && (
        <details className="mt-2.5 text-xs text-slate-400">
          <summary className="cursor-pointer hover:text-slate-200">
            {ilan.detay.pdfler.length} PDF listesi
          </summary>
          <ul className="mt-1.5 space-y-1 max-h-40 overflow-y-auto pr-2">
            {ilan.detay.pdfler.map((pdf) => (
              <li key={pdf}>
                <a href={pdf} target="_blank" rel="noreferrer" className="hover:text-accent-300 break-all">
                  {pdf.split('/').pop()}
                </a>
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}

function KaynakKart({ kaynak }) {
  const s = TIP_STIL[kaynak.tip] || TIP_STIL.portal
  const Ikon = HAT_IKON[kaynak.hat] || Globe
  return (
    <a
      href={kaynak.url} target="_blank" rel="noreferrer"
      className="rounded-xl bg-white/[0.03] border border-white/5 p-4 hover:bg-accent-500/10 hover:border-accent-500/30 transition-all group block"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Ikon size={16} className="text-accent-300 shrink-0" />
          <span className="font-medium text-sm text-white leading-tight">{kaynak.ad}</span>
        </div>
        <ExternalLink size={13} className="text-slate-500 group-hover:text-accent-300 shrink-0" />
      </div>
      <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">{kaynak.not}</p>
      <div className="flex gap-1.5 mt-2">
        <span className={`text-[10px] px-1.5 py-0.5 rounded-full border ${s.cls}`}>{s.label}</span>
        <span className="text-[10px] px-1.5 py-0.5 rounded-full border bg-white/5 text-slate-400 border-white/10">
          {kaynak.hat === 'kamu' ? 'Kamu' : 'Özel'}
        </span>
      </div>
    </a>
  )
}

export default function Kariyer() {
  const [sekme, setSekme] = useState('sinyaller')
  const [hat, setHat] = useState('')
  const [q, setQ] = useState('')
  const [sadeceYeni, setSadeceYeni] = useState(false)
  const [ilanlar, setIlanlar] = useState([])
  const [kaynaklar, setKaynaklar] = useState([])
  const [meta, setMeta] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(true)
  const [hata, setHata] = useState('')

  useEffect(() => {
    let iptal = false
    async function yukle() {
      setYukleniyor(true)
      setHata('')
      try {
        const params = new URLSearchParams()
        if (hat) params.set('hat', hat)
        if (q.trim()) params.set('q', q.trim())
        if (sadeceYeni) params.set('sadece_yeni', 'true')
        params.set('limit', '50')
        const [i, k, m] = await Promise.all([
          apiFetch(`/api/v1/kariyer/ilanlar?${params}`),
          apiFetch(`/api/v1/kariyer/kaynaklar${hat ? `?hat=${hat}` : ''}`),
          apiFetch('/api/v1/kariyer/meta'),
        ])
        if (!iptal) {
          setIlanlar(i.ilanlar || [])
          setKaynaklar(k.kaynaklar || [])
          setMeta(m)
        }
      } catch (e) {
        if (!iptal) setHata(e.message || 'Veri alınamadı')
      } finally {
        if (!iptal) setYukleniyor(false)
      }
    }
    const t = setTimeout(yukle, q ? 400 : 0) // aramada debounce
    return () => { iptal = true; clearTimeout(t) }
  }, [hat, q, sadeceYeni])

  return (
    <>
      <BackgroundScene />

      <div className="space-y-5">
        {/* Hero */}
        <div className="text-center mb-2">
          <div className="w-16 h-16 mx-auto mb-3 rounded-2xl bg-gradient-to-br from-teal-500 via-emerald-500 to-cyan-500 flex items-center justify-center shadow-2xl shadow-emerald-500/30">
            <Briefcase size={32} className="text-white" />
          </div>
          <h1 className="text-3xl md:text-4xl font-display font-bold text-white mb-2">
            <span className="gradient-text">Kariyer</span> Sinyalleri
          </h1>
          <p className="text-sm text-slate-400 max-w-xl mx-auto">
            Resmî Gazete günlük taraması + kamu/özel kaynak rehberi. Her sabah otomatik güncellenir.
            {meta && meta.toplam > 0 && ` Son tarama: ${meta.son_tarih} (${meta.toplam} kayıt).`}
          </p>
        </div>

        {/* Sekmeler */}
        <div className="inline-flex gap-1 p-1 rounded-xl bg-white/5 border border-white/10 max-w-full overflow-x-auto no-scrollbar">
          {[
            { id: 'sinyaller', label: 'Sinyaller' },
            { id: 'rehber', label: 'Kaynak Rehberi' },
          ].map((s) => (
            <button
              key={s.id}
              onClick={() => setSekme(s.id)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition whitespace-nowrap ${
                sekme === s.id
                  ? 'bg-gradient-to-r from-teal-500 to-emerald-600 text-white'
                  : 'text-slate-300 hover:bg-white/10'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>

        {/* Filtreler */}
        <div className="card !p-3 flex flex-wrap items-center gap-2">
          <div className="inline-flex gap-1 p-1 rounded-xl bg-white/5 border border-white/10">
            {HATLAR.map((h) => (
              <button
                key={h.id}
                onClick={() => setHat(h.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  hat === h.id ? 'bg-gradient-to-r from-brand-500 to-accent-500 text-white' : 'text-slate-300 hover:text-white'
                }`}
              >
                {h.label}
              </button>
            ))}
          </div>
          <div className="relative flex-1 min-w-[180px]">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Ara: bilişim, mühendis, KPSS…"
              className="input-glass !py-2 !pl-9 text-sm"
            />
          </div>
          {sekme === 'sinyaller' && (
            <button
              onClick={() => setSadeceYeni((v) => !v)}
              className={`px-3 py-2 rounded-xl text-xs font-medium transition border ${
                sadeceYeni
                  ? 'bg-emerald-500/20 text-emerald-200 border-emerald-500/40'
                  : 'text-slate-300 border-white/10 hover:bg-white/5'
              }`}
            >
              ✨ Sadece yeni
            </button>
          )}
        </div>

        {hata && (
          <div className="text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-3">
            {hata}
          </div>
        )}

        {yukleniyor ? (
          <div className="card text-center py-12">
            <Loader2 size={32} className="mx-auto animate-spin text-accent-400 mb-3" />
            <p className="text-sm text-slate-400">Yükleniyor…</p>
          </div>
        ) : sekme === 'sinyaller' ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
            {ilanlar.length === 0 ? (
              <div className="card text-center py-12">
                <Briefcase size={48} className="mx-auto text-slate-600 mb-3" />
                <h2 className="font-display font-semibold text-lg text-white mb-2">Henüz sinyal yok</h2>
                <p className="text-sm text-slate-400 mb-4 max-w-md mx-auto">
                  Günlük tarama henüz veri üretmedi ya da filtreye uyan kayıt yok.
                  Bu arada Kaynak Rehberi sekmesinden resmî kanallara doğrudan gidebilirsin.
                </p>
              </div>
            ) : (
              <>
                <p className="text-xs text-slate-500">{ilanlar.length} kayıt (yeniden eskiye)</p>
                <div className="grid md:grid-cols-2 gap-3">
                  {ilanlar.map((ilan) => <SinyalKart key={ilan.id} ilan={ilan} />)}
                </div>
              </>
            )}
          </motion.div>
        ) : (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
            <p className="text-xs text-slate-500 flex items-center gap-1.5">
              <BookOpen size={12} /> {kaynaklar.length} kaynak — karta tıkla, resmî sitede ilana git
            </p>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 3xl:grid-cols-4 gap-3">
              {kaynaklar.map((k) => <KaynakKart key={k.id} kaynak={k} />)}
            </div>
          </motion.div>
        )}
      </div>
    </>
  )
}
