import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Loader2, School, Info, ExternalLink, MapPin, Users, Search, ShieldCheck, Target, Rocket } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { apiFetch } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import {
  watchLgsTercih, addToLgsTercih, removeFromLgsTercih, MAX_LGS_TERCIH, lgsTercihKey,
} from '../firebase'

const TUR_STIL = {
  fen:            { label: 'Fen',            cls: 'bg-blue-500/15 text-blue-300 border-blue-500/30' },
  anadolu:        { label: 'Anadolu',        cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
  sosyal:         { label: 'Sosyal Bil.',    cls: 'bg-violet-500/15 text-violet-300 border-violet-500/30' },
  imam_hatip:     { label: 'İmam Hatip',     cls: 'bg-amber-500/15 text-amber-300 border-amber-500/30' },
  meslek:         { label: 'Meslek',         cls: 'bg-slate-500/15 text-slate-300 border-slate-500/30' },
  guzel_sanatlar: { label: 'Güzel San.',     cls: 'bg-pink-500/15 text-pink-300 border-pink-500/30' },
  spor:           { label: 'Spor',           cls: 'bg-orange-500/15 text-orange-300 border-orange-500/30' },
  diger:          { label: 'Diğer',          cls: 'bg-slate-500/15 text-slate-400 border-slate-500/30' },
}

// Filtre için ana türler
const TUR_FILTRE = ['fen', 'anadolu', 'sosyal', 'imam_hatip', 'meslek']

const KOVALAR = [
  { key: 'guvenli', label: 'Güvenli', icon: ShieldCheck, renk: 'from-emerald-500 to-teal-600', desc: 'Rahatça yerleşebilirsin' },
  { key: 'tutar',   label: 'Tutar',   icon: Target,      renk: 'from-amber-500 to-orange-600', desc: 'Senin seviyende — sınırda' },
  { key: 'riskli',  label: 'Riskli',  icon: Rocket,      renk: 'from-rose-500 to-fuchsia-600', desc: 'Taban üstü — denemeye değer' },
]

// Çok-yıllı arşiv değerlendirmesi rozeti (backend trend_yonu üretir)
const TREND_YONU = {
  zorlasiyor:   { label: '↗ zorlaşıyor',  cls: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
                  title: 'Taban yüzdeliği yıllar içinde daraldı — rekabet artıyor' },
  kolaylasiyor: { label: '↘ kolaylaşıyor', cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
                  title: 'Taban yüzdeliği yıllar içinde genişledi — rekabet azalıyor' },
  istikrarli:   { label: '→ istikrarlı',  cls: 'bg-white/5 text-slate-400 border-white/10',
                  title: 'Taban yüzdeliği yıllar içinde stabil' },
}

// Küçük yüzdelik trend sparkline (düşük yüzdelik = iyi = grafikte yukarı)
function YuzdelikTrend({ trend }) {
  const pts = (trend || []).filter((t) => t.yuzdelik != null).slice().reverse() // eski→yeni
  if (pts.length < 2) return null
  const W = 74, H = 22, P = 3
  const ys = pts.map((p) => p.yuzdelik)
  const min = Math.min(...ys), range = Math.max(Math.max(...ys) - min, 0.01)
  const points = pts.map((p, i) => ({
    x: P + (i / (pts.length - 1)) * (W - P * 2),
    // düşük yüzdelik = iyi → yukarıda (küçük y)
    y: P + ((p.yuzdelik - min) / range) * (H - P * 2),
  }))
  const path = points.map((pt, i) => `${i === 0 ? 'M' : 'L'} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`).join(' ')
  return (
    <svg width={W} height={H} className="block" title={`${pts[0].yil}→${pts[pts.length - 1].yil} yüzdelik trendi`}>
      <path d={path} stroke="currentColor" strokeWidth="1.5" fill="none" className="text-accent-400" />
      {points.map((pt, i) => <circle key={i} cx={pt.x} cy={pt.y} r="1.6" className="fill-accent-300" />)}
    </svg>
  )
}

function LiseKart({ lise, inList, onToggle }) {
  const s = TUR_STIL[lise.tur] || TUR_STIL.diger
  return (
    <div className="rounded-xl bg-white/[0.03] border border-white/5 p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="font-medium text-sm text-white leading-tight">{lise.okul}</div>
          <div className="flex items-center gap-1.5 mt-0.5 text-[11px] text-slate-400">
            <MapPin size={10} /> {lise.ilce ? `${lise.ilce} / ` : ''}{lise.il}
          </div>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <span className={`text-[10px] px-1.5 py-0.5 rounded-full border ${s.cls}`}>{s.label}</span>
          <button
            onClick={() => onToggle(lise)}
            title={inList ? 'Tercihten çıkar' : 'Tercih listeme ekle'}
            className={`rounded-lg px-2 py-0.5 text-[10px] border transition ${
              inList
                ? 'border-emerald-500/40 text-emerald-300 bg-emerald-500/10'
                : 'border-white/10 text-slate-300 hover:bg-white/10'
            }`}
          >
            {inList ? '✓ Listede' : '+ Tercih'}
          </button>
        </div>
      </div>
      <div className="flex items-end justify-between mt-2">
        <div>
          <div className="text-[10px] text-slate-500">Taban yüzdelik (2025)</div>
          <div className="text-lg font-display font-bold text-accent-300 leading-none">
            %{lise.yuzdelik?.toLocaleString('tr-TR')}
          </div>
        </div>
        <div className="text-right text-[10px] text-slate-400 space-y-0.5">
          {lise.taban_puan != null && <div>Puan: <span className="text-slate-200 font-mono">{lise.taban_puan.toFixed(2)}</span></div>}
          {lise.kontenjan != null && <div className="inline-flex items-center gap-1"><Users size={9} /> {lise.kontenjan}</div>}
        </div>
      </div>
      <div className="flex items-center justify-between mt-1.5 gap-1.5">
        <span className="text-[10px] text-slate-500 truncate">{lise.dil}</span>
        <span className="flex items-center gap-1.5 shrink-0">
          {TREND_YONU[lise.trend_yonu] && (
            <span title={TREND_YONU[lise.trend_yonu].title}
              className={`text-[9px] px-1.5 py-0.5 rounded-full border ${TREND_YONU[lise.trend_yonu].cls}`}>
              {TREND_YONU[lise.trend_yonu].label}
            </span>
          )}
          <YuzdelikTrend trend={lise.trend} />
        </span>
      </div>
    </div>
  )
}

// Robot çekirdeği — hem /lgs sayfasında hem Öneriler sekmesinde kullanılır
export function LgsRobot() {
  const [yuzdelik, setYuzdelik] = useState('')
  const [il, setIl] = useState('')
  const [turler, setTurler] = useState([])
  const [iller, setIller] = useState([])
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { user } = useAuth()
  const [tercihIds, setTercihIds] = useState(new Set())
  const [toast, setToast] = useState('')

  useEffect(() => {
    apiFetch('/api/v1/lgs/iller').then((d) => setIller(d.iller || [])).catch(() => {})
  }, [])

  // Tercih listesini canlı izle → kartlardaki "Listede/+ Tercih" senkron
  useEffect(() => {
    if (!user) { setTercihIds(new Set()); return }
    return watchLgsTercih(user.uid, (items) => setTercihIds(new Set(items.map((i) => i.id))))
  }, [user])

  function flash(msg) { setToast(msg); setTimeout(() => setToast(''), 2500) }

  async function toggleTercih(lise) {
    if (!user) { flash('Tercihe eklemek için giriş yap'); return }
    const key = lgsTercihKey(lise)
    try {
      if (tercihIds.has(key)) {
        await removeFromLgsTercih(user.uid, key)
      } else {
        if (tercihIds.size >= MAX_LGS_TERCIH) { flash(`Liste dolu (en fazla ${MAX_LGS_TERCIH} lise)`); return }
        // order = Date.now(): size+1 silme sonrası çakışıyor; reorder 1..n normalleştirir
        await addToLgsTercih(user.uid, lise, Date.now())
        flash('✓ Tercih listene eklendi — Tercihlerim sayfasında')
      }
    } catch (e) { flash(e.message) }
  }

  function toggleTur(t) {
    setTurler((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]))
  }

  async function bul(e) {
    e?.preventDefault()
    const y = parseFloat(yuzdelik)
    if (isNaN(y) || y < 0 || y > 100) {
      setError('Geçerli bir yüzdelik dilim gir (0–100 arası).')
      setTimeout(() => setError(''), 2500)
      return
    }
    // İl seçimi zorunlu — LGS tercihi il bazlıdır; tüm Türkiye ancak bilinçli
    // seçimle (yatılı/pansiyonlu arayanlar) anlamlı.
    if (!il) {
      setError('Önce ilini seç (yatılı düşünüyorsan "Tüm Türkiye").')
      setTimeout(() => setError(''), 3000)
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await apiFetch('/api/v1/lgs/oneri', {
        method: 'POST',
        body: { yuzdelik: y, il: il === '__ALL__' ? null : il, turler: turler.length ? turler : null },
      })
      setData(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-5">
        {/* Uyarı + kapsam + MEB linki */}
        <div className="card bg-amber-500/5 border-amber-500/20 text-xs text-slate-300 space-y-1.5">
          <div className="flex items-start gap-2">
            <Info size={13} className="text-amber-400 mt-0.5 shrink-0" />
            <span>
              <strong className="text-amber-300">Tahminîdir.</strong> Sonuçlar geçen yıl (LGS 2025) Türkiye geneli
              taban yüzdeliklerine dayanır; bu yılki taban puanları değişebilir — garanti değildir.
            </span>
          </div>
          <div className="flex items-start gap-2">
            <Info size={13} className="text-slate-500 mt-0.5 shrink-0" />
            <span>
              Yalnızca <strong>merkezî sınavla (LGS)</strong> öğrenci alan liseleri kapsar; adrese dayalı yerleştirmeyle
              öğrenci alan okullar (öğrencilerin ~%85'i) kapsam dışıdır. Resmî tercih ve tam liste için{' '}
              <a href="https://rotamaarif.meb.gov.tr" target="_blank" rel="noopener noreferrer"
                className="text-accent-300 hover:underline inline-flex items-center gap-0.5">
                MEB Rota Maarif <ExternalLink size={10} />
              </a>.
            </span>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={bul} className="card space-y-3">
          <div className="grid sm:grid-cols-[1fr,1fr] gap-3">
            <div>
              <label className="text-xs text-slate-300 mb-1 block">
                Yüzdelik dilimin <span className="text-slate-500">(LGS sonuç belgende yazar, ör. 2.5)</span>
              </label>
              <div className="relative">
                <input
                  type="number" min="0" max="100" step="0.01" value={yuzdelik}
                  onChange={(e) => setYuzdelik(e.target.value)}
                  placeholder="ör. 2.50"
                  className="input-glass w-full pr-8"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 text-sm">%</span>
              </div>
            </div>
            <div>
              <label className="text-xs text-slate-300 mb-1 block">
                İlin <span className="text-slate-500">(tercih edeceğin il — yatılı düşünüyorsan "Tüm Türkiye")</span>
              </label>
              <select value={il} onChange={(e) => setIl(e.target.value)} className="input-glass w-full">
                <option value="" disabled>İl seçin…</option>
                <option value="__ALL__">🇹🇷 Tüm Türkiye (pansiyonlu okullar dahil)</option>
                {iller.map((i) => <option key={i} value={i}>{i}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs text-slate-300 mb-1 block">Lise türü <span className="text-slate-500">(boş = hepsi)</span></label>
            <div className="flex flex-wrap gap-1.5">
              {TUR_FILTRE.map((t) => {
                const aktif = turler.includes(t)
                return (
                  <button key={t} type="button" onClick={() => toggleTur(t)}
                    className={`text-xs px-2.5 py-1 rounded-lg border transition ${
                      aktif ? `${TUR_STIL[t].cls} font-medium` : 'border-white/10 text-slate-400 hover:bg-white/5'
                    }`}>
                    {TUR_STIL[t].label}
                  </button>
                )
              })}
            </div>
          </div>
          <button type="submit" disabled={loading}
            className="btn-primary w-full inline-flex items-center justify-center gap-2 disabled:opacity-50">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
            Liseleri Bul
          </button>
          {error && <div className="text-xs text-rose-300 text-center">⚠️ {error}</div>}
        </form>

        {toast && (
          <div className="text-xs text-center text-accent-200 bg-accent-500/10 border border-accent-500/30 rounded-lg py-2">
            {toast}
          </div>
        )}

        {/* Sonuçlar */}
        <AnimatePresence>
          {data && (
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
              <div className="text-center text-xs text-slate-400">
                <strong className="text-white">%{data.yuzdelik}</strong> yüzdelik dilimiyle
                {il && il !== '__ALL__' ? <> <strong className="text-white">{il}</strong>'da</> : ' Türkiye genelinde'}{' '}
                <span className="text-emerald-300">{data.sayilar.guvenli}</span> güvenli ·{' '}
                <span className="text-amber-300">{data.sayilar.tutar}</span> tutar ·{' '}
                <span className="text-rose-300">{data.sayilar.riskli}</span> riskli lise
              </div>

              {data.sayilar.guvenli + data.sayilar.tutar + data.sayilar.riskli === 0 && (
                <div className="card text-center text-sm text-slate-400">
                  Bu filtreyle lise bulunamadı. İl/tür filtresini genişletmeyi dene.
                </div>
              )}

              {KOVALAR.map((kova) => {
                const items = data[kova.key] || []
                if (items.length === 0) return null
                return (
                  <div key={kova.key} className="card">
                    <div className="flex items-center gap-2 mb-3">
                      <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${kova.renk} flex items-center justify-center`}>
                        <kova.icon size={16} className="text-white" />
                      </div>
                      <div>
                        <h2 className="font-display font-semibold text-white leading-none">
                          {kova.label} <span className="text-xs text-slate-400 font-normal">({data.sayilar[kova.key]})</span>
                        </h2>
                        <p className="text-[10px] text-slate-500">{kova.desc}</p>
                      </div>
                    </div>
                    <div className="grid sm:grid-cols-2 gap-2">
                      {items.map((l, i) => (
                        <LiseKart key={`${l.okul}-${i}`} lise={l}
                          inList={tercihIds.has(lgsTercihKey(l))} onToggle={toggleTercih} />
                      ))}
                    </div>
                    {data.sayilar[kova.key] > items.length && (
                      <div className="text-[10px] text-slate-500 text-center mt-2">
                        + {data.sayilar[kova.key] - items.length} lise daha (il/tür filtresiyle daralt)
                      </div>
                    )}
                  </div>
                )
              })}

              <div className="text-[10px] text-slate-600 text-center flex items-center justify-center gap-1.5">
                <Info size={11} /> {data.not}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
    </div>
  )
}

export default function LGS() {
  return (
    <>
      <BackgroundScene />
      <Seo
        title="LGS Tercih Robotu 2026 — Yüzdelik Dilimine Göre Lise Bul | UniSense"
        description="LGS yüzdelik dilimini gir, geçen yıl taban puanlarına göre girebileceğin Fen, Anadolu, Sosyal Bilimler ve İmam Hatip liselerini güvenli/tutar/riskli olarak gör. Ücretsiz, tahminî."
        path="/lgs"
      />
      <div className="max-w-4xl mx-auto space-y-5">
        <div className="text-center">
          <div className="w-14 h-14 mx-auto mb-2 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-lg">
            <School size={28} className="text-white" />
          </div>
          <h1 className="text-3xl md:text-4xl font-display font-bold text-white">
            LGS <span className="gradient-text">Tercih Robotu</span>
          </h1>
          <p className="text-sm text-slate-400 max-w-xl mx-auto mt-1">
            Yüzdelik dilimini gir → geçen yılın taban puanlarına göre <strong className="text-emerald-300">girebileceğin liseleri</strong> güvenli / tutar / riskli olarak gör.
          </p>
        </div>
        <LgsRobot />
      </div>
    </>
  )
}
