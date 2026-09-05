import { useState, useEffect, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Briefcase, Loader2, Search, ExternalLink, Sparkles, BookOpen,
  Landmark, Building2, Globe, SlidersHorizontal, ChevronDown, CalendarClock,
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

const CALISMA_AD = { online: 'Uzaktan', hibrit: 'Hibrit', yuzyuze: 'Yüz yüze', bilinmiyor: 'Belirtilmemiş' }
const KPSS_SEC = [
  { id: '', label: 'KPSS: Tümü' },
  { id: 'var', label: 'KPSS şartlı' },
  { id: 'yok', label: 'KPSS’siz' },
]
const SIRA_SEC = [
  { id: 'tarih_desc', label: 'En yeniden' },
  { id: 'son_basvuru_asc', label: 'Son başvuru yakınlığı' },
]
const BOYUT = 30

function kalanGun(sonBasvuru) {
  if (!sonBasvuru) return null
  const gun = Math.ceil((new Date(sonBasvuru) - new Date()) / 86400000)
  return gun
}

function SinyalKart({ ilan, bolumAd }) {
  const eslesme = Object.entries(ilan.detay?.eslesme || {}).filter(([, c]) => c > 0)
  const kalan = kalanGun(ilan.son_basvuru)
  const yer = [ilan.il || ilan.sehir, ilan.ilce].filter(Boolean).join(' / ')
  return (
    <div className="rounded-xl bg-white/[0.03] border border-white/5 p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="text-[11px] text-slate-500 mb-0.5">{ilan.kurum || ilan.kaynak}</div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-sm text-white leading-tight">{ilan.baslik}</span>
            {ilan.yeni && (
              <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full border bg-emerald-500/15 text-emerald-300 border-emerald-500/30">
                <Sparkles size={10} /> yeni
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 flex-wrap text-[11px] text-slate-400 mt-1.5">
            {yer && <span>{yer}</span>}
            {ilan.calisma_sekli && ilan.calisma_sekli !== 'bilinmiyor' && (
              <span className="px-1.5 py-0.5 rounded-full border bg-sky-500/15 text-sky-300 border-sky-500/30">
                {CALISMA_AD[ilan.calisma_sekli] || ilan.calisma_sekli}
              </span>
            )}
            <span>{ilan.tarih}</span>
            {kalan !== null && (
              <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full border ${
                kalan < 0 ? 'bg-white/5 text-slate-500 border-white/10'
                : kalan <= 7 ? 'bg-rose-500/15 text-rose-300 border-rose-500/30'
                : 'bg-white/5 text-slate-300 border-white/10'
              }`}>
                <CalendarClock size={10} />
                {kalan < 0 ? 'süresi dolmuş' : kalan === 0 ? 'son gün!' : `son ${kalan} gün`}
              </span>
            )}
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
      {(ilan.bolumler?.length > 0) && (
        <div className="flex flex-wrap gap-1.5 mt-1.5">
          {ilan.bolumler.map((b) => (
            <span key={b} className="text-[10px] px-2 py-0.5 rounded-full border bg-teal-500/10 text-teal-200 border-teal-500/30">
              🎓 {bolumAd?.(b) || b}
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

function useFiltreDurumu() {
  // Filtre durumu URL'de yaşar — paylaşılabilir link (F1.5)
  const [params, setParams] = useSearchParams()
  const al = (k, varsayilan = '') => params.get(k) ?? varsayilan
  const diziAl = (k) => params.getAll(k)
  const yaz = (yeni) => {
    const p = new URLSearchParams()
    for (const [k, v] of Object.entries(yeni)) {
      if (Array.isArray(v)) v.forEach((x) => x && p.append(k, x))
      else if (v) p.set(k, v)
    }
    setParams(p, { replace: true })
  }
  return { al, diziAl, yaz }
}

export default function Kariyer() {
  const [sekme, setSekme] = useState('sinyaller')
  const [panelAcik, setPanelAcik] = useState(false) // mobil çekmece
  const { al, diziAl, yaz } = useFiltreDurumu()
  const hat = al('hat'), bolum = al('bolum'), q = al('q')
  const bolge = al('bolge'), il = al('il'), ilce = al('ilce')
  const calisma = diziAl('calisma'), istihdam = al('istihdam'), deneyim = al('deneyim')
  const kpss = al('kpss'), sira = al('sira', 'tarih_desc')
  const sadeceYeni = al('yeni') === '1'

  const [ilanlar, setIlanlar] = useState([])
  const [toplam, setToplam] = useState(0)
  const [kaynaklar, setKaynaklar] = useState([])
  const [bolumler, setBolumler] = useState([])
  const [facet, setFacet] = useState({})
  const [meta, setMeta] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(true)
  const [hata, setHata] = useState('')

  const bolumAd = (id) => (bolumler.find((b) => b.id === id)?.label || id)
  const filtreAnahtari = JSON.stringify({ hat, bolum, q, bolge, il, ilce, calisma, istihdam, deneyim, kpss, sira, sadeceYeni })

  useEffect(() => {
    let iptal = false
    async function yukle() {
      setYukleniyor(true)
      setHata('')
      try {
        const params = new URLSearchParams()
        if (hat) params.set('hat', hat)
        if (bolum) params.set('bolum', bolum)
        if (q.trim()) params.set('q', q.trim())
        if (bolge) params.set('bolge', bolge)
        if (il) params.set('il', il)
        if (ilce) params.set('ilce', ilce.trim())
        calisma.forEach((c) => params.append('calisma_sekli', c))
        if (istihdam) params.set('istihdam_turu', istihdam)
        if (deneyim) params.set('deneyim', deneyim)
        if (kpss === 'var') params.set('kpss', 'true')
        if (kpss === 'yok') params.set('kpss', 'false')
        if (sadeceYeni) params.set('sadece_yeni', 'true')
        params.set('sira', sira)
        params.set('boyut', String(BOYUT))
        params.set('sayfa', '1')
        const [i, f, k, m, b] = await Promise.all([
          apiFetch(`/api/v1/kariyer/ilanlar?${params}`),
          apiFetch('/api/v1/kariyer/filtreler'),
          apiFetch(`/api/v1/kariyer/kaynaklar${hat ? `?hat=${hat}` : ''}`),
          apiFetch('/api/v1/kariyer/meta'),
          apiFetch('/api/v1/kariyer/bolumler'),
        ])
        if (!iptal) {
          setIlanlar(i.ilanlar || [])
          setToplam(i.toplam || 0)
          setFacet(f || {})
          setKaynaklar(k.kaynaklar || [])
          setMeta(m)
          setBolumler(b.bolumler || [])
        }
      } catch (e) {
        if (!iptal) setHata(e.message || 'Veri alınamadı')
      } finally {
        if (!iptal) setYukleniyor(false)
      }
    }
    const t = setTimeout(() => yukle(false), q ? 400 : 0)
    return () => { iptal = true; clearTimeout(t) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtreAnahtari])

  const guncelle = (yama) => {
    const mevcut = { hat, bolum, q, bolge, il, ilce, calisma, istihdam, deneyim, kpss, sira }
    if (sadeceYeni) mevcut.yeni = '1'
    yaz({ ...mevcut, ...yama })
  }
  const cokluDegistir = (alan, deger) => {
    const liste = alan === 'calisma' ? calisma : []
    const yeni = liste.includes(deger) ? liste.filter((x) => x !== deger) : [...liste, deger]
    guncelle({ [alan]: yeni })
  }

  const ilSecenekleri = useMemo(() => {
    const iller = facet.il || []
    return bolge ? iller.filter((x) => x.bolge === bolge) : iller
  }, [facet, bolge])
  const dahaVar = ilanlar.length < toplam

  const secimStil = (aktif) => `px-3 py-1.5 rounded-lg text-xs font-medium transition border whitespace-nowrap ${
    aktif
      ? 'bg-gradient-to-r from-teal-500 to-emerald-600 text-white border-transparent'
      : 'text-slate-300 border-white/10 hover:bg-white/5'
  }`

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
            Kamu + özel sektör ilanları tek akışta. Her sabah otomatik güncellenir.
            {meta && meta.toplam > 0 && ` Son tarama: ${meta.son_tarih} (${meta.toplam} kayıt).`}
          </p>
        </div>

        {/* Sekmeler */}
        <div className="inline-flex gap-1 p-1 rounded-xl bg-white/5 border border-white/10 max-w-full overflow-x-auto no-scrollbar">
          {[
            { id: 'sinyaller', label: 'İlanlar' },
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

        {/* Bölüm seçici rehber */}
        {bolumler.length > 0 && (
          <div className="card !p-3">
            <div className="text-xs font-medium text-slate-400 mb-2 px-1">
              🎓 Bölümüne göre ilan akışı — bir ilan birden çok bölüme girebilir
            </div>
            <div className="flex gap-1.5 flex-wrap max-h-28 overflow-y-auto pr-1">
              <button onClick={() => guncelle({ bolum: '' })} className={secimStil(!bolum)}>
                Tümü
              </button>
              {bolumler.map((b) => (
                <button key={b.id} onClick={() => guncelle({ bolum: bolum === b.id ? '' : b.id })} className={secimStil(bolum === b.id)}>
                  {b.label}{b.sayi > 0 ? ` · ${b.sayi}` : ''}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Filtre paneli aç/kapa (mobil çekmece) */}
        <div className="card !p-3 space-y-3">
          <button
            onClick={() => setPanelAcik((v) => !v)}
            className="flex lg:hidden items-center gap-2 text-sm font-medium text-slate-200 w-full"
          >
            <SlidersHorizontal size={15} />
            Filtreler
            {(bolge || il || calisma.length > 0 || kpss) && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-teal-500/20 text-teal-200">aktif</span>
            )}
            <ChevronDown size={14} className={`ml-auto transition ${panelAcik ? 'rotate-180' : ''}`} />
          </button>

          <div className={`${panelAcik ? 'block' : 'hidden'} lg:block space-y-3`}>
            {/* Hat + arama + yeni + sıralama */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="inline-flex gap-1 p-1 rounded-xl bg-white/5 border border-white/10">
                {HATLAR.map((h) => (
                  <button
                    key={h.id}
                    onClick={() => guncelle({ hat: h.id })}
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
                  onChange={(e) => guncelle({ q: e.target.value })}
                  placeholder="Ara: başlık, kurum…"
                  className="input-glass !py-2 !pl-9 text-sm"
                />
              </div>
              <select
                value={sira}
                onChange={(e) => guncelle({ sira: e.target.value })}
                className="input-glass !py-2 !w-auto text-xs"
                title="Sıralama"
              >
                {SIRA_SEC.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
              </select>
              <button
                onClick={() => guncelle({ yeni: sadeceYeni ? '' : '1' })}
                className={`px-3 py-2 rounded-xl text-xs font-medium transition border ${
                  sadeceYeni
                    ? 'bg-emerald-500/20 text-emerald-200 border-emerald-500/40'
                    : 'text-slate-300 border-white/10 hover:bg-white/5'
                }`}
              >
                ✨ Sadece yeni
              </button>
            </div>

            {/* Bölge → il → ilçe */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              <select
                value={bolge}
                onChange={(e) => guncelle({ bolge: e.target.value, il: '' })}
                className="input-glass !py-2 text-xs"
              >
                <option value="">Bölge: Tümü</option>
                {(facet.bolge || []).map((x) => (
                  <option key={x.id} value={x.id}>{x.id} ({x.sayi})</option>
                ))}
              </select>
              <select
                value={il}
                onChange={(e) => guncelle({ il: e.target.value })}
                className="input-glass !py-2 text-xs"
              >
                <option value="">İl: Tümü{bolge ? ` (${bolge})` : ''}</option>
                {ilSecenekleri.map((x) => (
                  <option key={x.id} value={x.id}>{x.id} ({x.sayi})</option>
                ))}
              </select>
              <input
                value={ilce}
                onChange={(e) => guncelle({ ilce: e.target.value })}
                placeholder="İlçe yaz…"
                className="input-glass !py-2 text-xs col-span-2 sm:col-span-1"
              />
            </div>

            {/* Çalışma şekli (çoklu) + KPSS */}
            <div className="flex flex-wrap items-center gap-1.5">
              {['online', 'hibrit', 'yuzyuze'].map((c) => (
                <button
                  key={c}
                  onClick={() => cokluDegistir('calisma', c)}
                  className={secimStil(calisma.includes(c))}
                >
                  {c === 'online' ? 'Uzaktan' : c === 'hibrit' ? 'Hibrit' : 'Yüz yüze'}
                </button>
              ))}
              <span className="text-slate-600 mx-1">|</span>
              {KPSS_SEC.map((k) => (
                <button
                  key={k.id}
                  onClick={() => guncelle({ kpss: k.id })}
                  className={secimStil(kpss === k.id)}
                >
                  {k.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {hata && (
          <div className="text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-3">
            {hata}
          </div>
        )}

        {yukleniyor && ilanlar.length === 0 ? (
          <div className="card text-center py-12">
            <Loader2 size={32} className="mx-auto animate-spin text-accent-400 mb-3" />
            <p className="text-sm text-slate-400">Yükleniyor…</p>
          </div>
        ) : sekme === 'sinyaller' ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
            {ilanlar.length === 0 ? (
              <div className="card text-center py-12">
                <Briefcase size={48} className="mx-auto text-slate-600 mb-3" />
                <h2 className="font-display font-semibold text-lg text-white mb-2">Sonuç yok</h2>
                <p className="text-sm text-slate-400 mb-4 max-w-md mx-auto">
                  Filtrelere uyan ilan bulunamadı. Filtreleri gevşetmeyi dene ya da
                  Kaynak Rehberi sekmesinden resmî kanallara doğrudan git.
                </p>
                <button onClick={() => yaz({})} className="btn-ghost text-sm">
                  Filtreleri temizle
                </button>
              </div>
            ) : (
              <>
                <p className="text-xs text-slate-500">{toplam} ilan bulundu</p>
                <div className="grid md:grid-cols-2 gap-3">
                  {ilanlar.map((ilan) => <SinyalKart key={ilan.id} ilan={ilan} bolumAd={bolumAd} />)}
                </div>
                {dahaVar && (
                  <div className="text-center pt-2">
                    <button onClick={() => yukleDahaFazla()} className="btn-ghost text-sm">
                      Daha fazla göster ({toplam - ilanlar.length} kaldı)
                    </button>
                  </div>
                )}
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

  // Sayfalama: mevcut filtrelerle bir sonraki sayfayı ekler
  async function yukleDahaFazla() {
    const params = new URLSearchParams()
    if (hat) params.set('hat', hat)
    if (bolum) params.set('bolum', bolum)
    if (q.trim()) params.set('q', q.trim())
    if (bolge) params.set('bolge', bolge)
    if (il) params.set('il', il)
    if (ilce) params.set('ilce', ilce.trim())
    calisma.forEach((c) => params.append('calisma_sekli', c))
    if (istihdam) params.set('istihdam_turu', istihdam)
    if (deneyim) params.set('deneyim', deneyim)
    if (kpss === 'var') params.set('kpss', 'true')
    if (kpss === 'yok') params.set('kpss', 'false')
    if (sadeceYeni) params.set('sadece_yeni', 'true')
    params.set('sira', sira)
    params.set('boyut', String(BOYUT))
    // mevcut sayfa sayısı = yüklenen / BOYUT
    params.set('sayfa', String(Math.floor(ilanlar.length / BOYUT) + 1))
    try {
      const i = await apiFetch(`/api/v1/kariyer/ilanlar?${params}`)
      setIlanlar((onceki) => [...onceki, ...(i.ilanlar || [])])
    } catch (e) {
      setHata(e.message || 'Veri alınamadı')
    }
  }
}
