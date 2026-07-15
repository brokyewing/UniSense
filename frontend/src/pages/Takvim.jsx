import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Loader2, CalendarDays, Info } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { apiFetch } from '../lib/api'

const TUR_STIL = {
  sinav:       { label: 'Sınav',        cls: 'bg-blue-500/15 text-blue-300 border-blue-500/30' },
  sonuc:       { label: 'Sonuç',        cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
  tercih:      { label: 'Tercih',       cls: 'bg-amber-500/15 text-amber-300 border-amber-500/30' },
  yerlestirme: { label: 'Yerleştirme',  cls: 'bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-500/30' },
  basvuru:     { label: 'Başvuru',      cls: 'bg-slate-500/15 text-slate-300 border-slate-500/30' },
}

function fmtTarih(iso) {
  try {
    return new Date(iso + 'T00:00:00').toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' })
  } catch { return iso }
}

function KalanRozet({ gun, devam }) {
  if (devam) return <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">Sürüyor</span>
  if (gun === 0) return <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40">Bugün</span>
  const cls = gun <= 7 ? 'bg-rose-500/15 text-rose-300 border-rose-500/30'
    : gun <= 30 ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
    : 'bg-white/5 text-slate-400 border-white/10'
  return <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${cls}`}>{gun} gün</span>
}

export default function Takvim() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    apiFetch('/api/v1/takvim')
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <>
      <BackgroundScene />
      <Seo
        title="2026 Sınav Takvimi — YKS, LGS, DGS, KPSS, ALES, TUS Tarihleri | UniSense"
        description="2026 YKS, LGS, DGS, KPSS, ALES, TUS, DUS ve AGS sınav, sonuç ve tercih tarihleri — kaç gün kaldığıyla birlikte tek sayfada."
        path="/takvim"
      />
      <div className="max-w-3xl mx-auto space-y-5">
        <div className="text-center">
          <h1 className="text-3xl md:text-4xl font-display font-bold text-white mb-1 flex items-center justify-center gap-2">
            <CalendarDays className="text-accent-300" /> 2026 Sınav Takvimi
          </h1>
          <p className="text-slate-400 text-sm">Yaklaşan sınav, sonuç ve tercih tarihleri — kaç gün kaldığıyla.</p>
        </div>

        {loading ? (
          <div className="text-center py-10"><Loader2 className="animate-spin mx-auto text-accent-400" /></div>
        ) : error ? (
          <div className="card text-center text-rose-300">⚠️ {error}</div>
        ) : (
          <>
            {data.yaklasan.length === 0 && (
              <div className="card text-center py-8 text-sm text-slate-400">
                Bu yılın takvimi tamamlandı. 🎓<br />
                <span className="text-xs text-slate-500">
                  Yeni yılın sınav tarihleri ÖSYM/MEB duyurularıyla birlikte buraya eklenecek —
                  resmî takvim: <a href="https://www.osym.gov.tr" target="_blank" rel="noopener noreferrer" className="text-accent-300 hover:underline">osym.gov.tr</a>
                </span>
              </div>
            )}
            <div className="space-y-2">
              {data.yaklasan.map((e, i) => {
                const s = TUR_STIL[e.tur] || TUR_STIL.sinav
                return (
                  <motion.div key={e.id} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: Math.min(i * 0.02, 0.3) }}
                    className="card !py-3 flex items-center gap-3">
                    <div className="w-14 text-center shrink-0">
                      <div className="text-lg font-display font-bold text-white leading-none">{e.sinav}</div>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full border ${s.cls}`}>{s.label}</span>
                        <span className="text-sm text-slate-200">{fmtTarih(e.tarih)}</span>
                        {e.tahmini && <span className="text-[10px] text-slate-500" title="ÖSYM kılavuzuyla kesinleşecek">~tahmini</span>}
                      </div>
                      <div className="text-xs text-slate-500 truncate">{e.aciklama}</div>
                    </div>
                    <KalanRozet gun={e.kalan_gun} devam={e.devam} />
                  </motion.div>
                )
              })}
            </div>

            {data.gecmis?.length > 0 && (
              <div className="opacity-60">
                <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-2">Yakın geçmiş</div>
                <div className="space-y-1.5">
                  {data.gecmis.map((e) => (
                    <div key={e.id} className="text-xs text-slate-500 flex items-center gap-2 px-1">
                      <span className="font-semibold text-slate-400">{e.sinav}</span>
                      <span>{TUR_STIL[e.tur]?.label} · {fmtTarih(e.tarih)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data.not && (
              <div className="text-[10px] text-slate-600 flex items-start gap-1.5 px-1">
                <Info size={11} className="shrink-0 mt-0.5" /> {data.not}
              </div>
            )}
          </>
        )}
      </div>
    </>
  )
}
