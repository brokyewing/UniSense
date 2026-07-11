import { useState, useEffect, useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  BarChart3, Loader2, AlertCircle, ArrowLeft, TrendingUp,
  TrendingDown, Minus, Award, Calendar, Users, Building2,
  MapPin, GraduationCap, ExternalLink, X,
} from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import { apiFetch } from '../lib/api'


function numberOrDash(v, fmt = (x) => x) {
  if (v === null || v === undefined) return '—'
  try { return fmt(v) } catch { return '—' }
}

function fmtRank(v) {
  return v == null ? '—' : v.toLocaleString('tr-TR')
}

function fmtScore(v) {
  return v == null ? '—' : Number(v).toFixed(2)
}

function fmtFee(v) {
  if (!v) return 'Devlet (ücretsiz)'
  return v.toLocaleString('tr-TR') + ' ₺/yıl'
}


/** Mini SVG line chart for trend (year → rank). Y axis ters (küçük = yukarı). */
function MiniTrend({ trend }) {
  if (!trend || trend.length < 2) {
    return <div className="text-[10px] text-slate-500 italic">Trend verisi yetersiz</div>
  }
  const pts = trend.filter((t) => t.base_rank != null)
  if (pts.length < 2) {
    return <div className="text-[10px] text-slate-500 italic">Trend verisi yetersiz</div>
  }
  const W = 140, H = 50, P = 6
  const ranks = pts.map((p) => p.base_rank)
  const minR = Math.min(...ranks)
  const maxR = Math.max(...ranks)
  const range = Math.max(maxR - minR, 1)

  const points = pts.map((p, i) => {
    const x = P + (i / (pts.length - 1)) * (W - P * 2)
    // Küçük rank = iyi = yukarı (Y küçük)
    const y = P + ((p.base_rank - minR) / range) * (H - P * 2)
    return { x, y, p }
  })
  const path = points.map((pt, i) => `${i === 0 ? 'M' : 'L'} ${pt.x} ${pt.y}`).join(' ')

  // Momentum: ilk vs son
  const first = pts[0].base_rank
  const last = pts[pts.length - 1].base_rank
  const diff = first - last  // pozitif = iyileşmiş (rank düşmüş)
  const momentum = Math.abs(diff) < 100 ? 'stable' : diff > 0 ? 'up' : 'down'
  const momentumColor = momentum === 'up' ? 'text-emerald-400' : momentum === 'down' ? 'text-rose-400' : 'text-slate-400'
  const MomentumIcon = momentum === 'up' ? TrendingUp : momentum === 'down' ? TrendingDown : Minus

  return (
    <div>
      <svg width={W} height={H} className="block">
        <path d={path} stroke="currentColor" strokeWidth="1.5" fill="none" className="text-accent-400" />
        {points.map((pt, i) => (
          <circle key={i} cx={pt.x} cy={pt.y} r="2.5" className="fill-accent-300">
            <title>{pt.p.year}: sıra {pt.p.base_rank?.toLocaleString('tr-TR')}</title>
          </circle>
        ))}
      </svg>
      {/* Her yıl etiketi görünsün (2023 dahil) — uçlarda değil hepsi */}
      <div className="flex items-center justify-between text-[10px] text-slate-500 mt-1">
        {points.map((pt, i) => (
          <span key={i} title={`sıra ${pt.p.base_rank?.toLocaleString('tr-TR')}`}>
            {pt.p.year}
          </span>
        ))}
      </div>
      <div className={`flex items-center justify-center gap-0.5 text-[10px] mt-0.5 ${momentumColor}`}>
        <MomentumIcon size={10} />
        {Math.abs(diff).toLocaleString('tr-TR')} sıra
      </div>
    </div>
  )
}


function DiffMark({ field, code, diffs }) {
  const d = diffs?.[field]
  if (!d) return null
  if (d.best_code === code) {
    return <span className="ml-1 inline-block px-1 rounded text-[9px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">EN İYİ</span>
  }
  if (d.worst_code === code) {
    return <span className="ml-1 inline-block px-1 rounded text-[9px] bg-rose-500/20 text-rose-300 border border-rose-500/30">EN ZAYIF</span>
  }
  return null
}


function Row({ label, items, fmt, diffField, diffs, Icon }) {
  return (
    <div className="grid grid-cols-[120px_repeat(auto-fit,minmax(0,1fr))] gap-2 py-2 border-b border-white/5 last:border-b-0">
      <div className="text-xs text-slate-400 flex items-center gap-1.5">
        {Icon && <Icon size={11} className="text-slate-500" />}
        {label}
      </div>
      {items.map((it, i) => {
        const value = it.found ? fmt(it) : '—'
        return (
          <div key={i} className="text-sm text-slate-200 font-medium">
            {value}
            {diffField && it.found && <DiffMark field={diffField} code={it.code} diffs={diffs} />}
          </div>
        )
      })}
    </div>
  )
}


function ProgramHeader({ item, onRemove }) {
  if (!item.found) {
    return (
      <div className="card border-rose-500/30 bg-rose-500/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-rose-300">
            <AlertCircle size={16} />
            <span className="text-sm">Kod bulunamadı: <strong>{item.code}</strong></span>
          </div>
          <button onClick={onRemove} className="text-slate-400 hover:text-rose-300">
            <X size={14} />
          </button>
        </div>
      </div>
    )
  }
  return (
    <div className="card relative overflow-hidden">
      <button
        onClick={onRemove}
        className="absolute top-3 right-3 text-slate-500 hover:text-rose-400 transition"
        title="Listeden çıkar"
      >
        <X size={14} />
      </button>
      <div className="flex items-start gap-3">
        {item.logo_url ? (
          <img
            src={item.logo_url}
            alt=""
            className="w-12 h-12 rounded-lg object-cover shrink-0 bg-white/5 p-1"
            onError={(e) => { e.currentTarget.style.display = 'none' }}
          />
        ) : (
          <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-brand-500/30 to-accent-500/30 border border-white/10 flex items-center justify-center shrink-0">
            <GraduationCap size={20} className="text-accent-300" />
          </div>
        )}
        <div className="min-w-0 flex-1">
          <div className="text-[10px] text-slate-500 font-mono mb-0.5">{item.code}</div>
          <div className="font-display font-semibold text-white text-sm truncate" title={item.department_name}>
            {item.department_name}
          </div>
          <div className="text-xs text-slate-400 mt-1 truncate" title={item.university_name}>
            {item.university_name}
          </div>
          <div className="flex items-center gap-2 mt-1 text-[10px] text-slate-500">
            <MapPin size={10} />
            <span>{item.city}</span>
            {item.university_type && (
              <>
                <span className="text-slate-700">•</span>
                <span>{item.university_type}</span>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}


export default function Compare() {
  const [searchParams, setSearchParams] = useSearchParams()
  const codesFromUrl = useMemo(
    () => (searchParams.get('d') || '').split(',').map((c) => c.trim()).filter(Boolean),
    [searchParams],
  )

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (codesFromUrl.length < 2) {
      setData(null)
      setError(null)
      return
    }

    let cancelled = false
    setLoading(true)
    setError(null)

    apiFetch('/api/v1/programs/compare', {
      method: 'POST',
      body: { codes: codesFromUrl.slice(0, 5) },
    })
      .then((d) => {
        if (cancelled) return
        if (d.error) {
          setError(d.error)
          setData(null)
        } else {
          setData(d)
        }
      })
      .catch((e) => {
        if (cancelled) return
        setError(e.message || 'Bilinmeyen hata')
        setData(null)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [codesFromUrl])

  function removeCode(code) {
    const remaining = codesFromUrl.filter((c) => c !== code)
    setSearchParams({ d: remaining.join(',') })
  }

  const items = data?.items || []
  const diffs = data?.diffs || {}
  const found = items.filter((it) => it.found)

  return (
    <>
      <BackgroundScene />

      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex items-center justify-between flex-wrap gap-3"
        >
          <div>
            <h1 className="font-display font-bold text-2xl text-white flex items-center gap-2">
              <BarChart3 size={22} className="text-accent-400" />
              Bölüm Karşılaştırma
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              2 ila 5 program kodunu yan yana karşılaştır (taban, sıra, trend, akademik kadro)
            </p>
          </div>
          <Link to="/tercih" className="btn-ghost inline-flex items-center gap-2 text-sm">
            <ArrowLeft size={14} /> Tercih Listem
          </Link>
        </motion.div>

        {/* Boş durum */}
        {codesFromUrl.length < 2 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="card text-center py-12"
          >
            <BarChart3 size={48} className="mx-auto text-slate-600 mb-3" />
            <h2 className="font-display font-semibold text-lg text-white mb-2">
              Henüz karşılaştırma yapılmadı
            </h2>
            <p className="text-sm text-slate-400 mb-4">
              Tercih Listenden 2-5 program seç, "Karşılaştır" butonuna bas.
            </p>
            <Link to="/tercih" className="btn-primary inline-flex items-center gap-2 text-sm">
              Tercih Listene Git
            </Link>
          </motion.div>
        )}

        {loading && (
          <div className="card text-center py-12">
            <Loader2 size={32} className="mx-auto animate-spin text-accent-400 mb-3" />
            <p className="text-sm text-slate-400">Veriler getiriliyor…</p>
          </div>
        )}

        {error && !loading && (
          <div className="card border-rose-500/30 bg-rose-500/5 text-rose-200 text-sm flex items-start gap-2">
            <AlertCircle size={16} className="shrink-0 mt-0.5" />
            <div>{error}</div>
          </div>
        )}

        {data && !loading && (
          <>
            {/* Program başlıkları */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="grid gap-3"
              style={{ gridTemplateColumns: `repeat(${items.length}, minmax(0, 1fr))` }}
            >
              {items.map((it) => (
                <ProgramHeader key={it.code} item={it} onRemove={() => removeCode(it.code)} />
              ))}
            </motion.div>

            {/* Karşılaştırma tablosu */}
            {found.length >= 2 && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="card"
              >
                <h2 className="font-display font-semibold text-white text-lg mb-4 flex items-center gap-2">
                  <Award size={16} className="text-amber-400" />
                  Sayısal Karşılaştırma
                </h2>

                <Row label="Başarı sırası"   items={items} fmt={(it) => fmtRank(it.base_rank)}   diffField="base_rank"   diffs={diffs} Icon={TrendingUp} />
                <Row label="Taban puan"       items={items} fmt={(it) => fmtScore(it.base_score)} diffField="base_score"  diffs={diffs} Icon={Award} />
                <Row label="Puan türü"        items={items} fmt={(it) => it.score_type || '—'} />
                <Row label="Kontenjan"        items={items} fmt={(it) => numberOrDash(it.quota)} diffField="quota" diffs={diffs} />
                <Row label="Yerleşen"          items={items} fmt={(it) => numberOrDash(it.yerlesen)} diffField="yerlesen" diffs={diffs} />
                <Row label="Süre"              items={items} fmt={(it) => it.duration_years ? `${it.duration_years} yıl` : '—'} />
                <Row label="Eğitim dili"       items={items} fmt={(it) => it.education_language || '—'} />
                <Row label="Burs"               items={items} fmt={(it) => it.scholarship || '—'} />
                <Row label="Ücret"              items={items} fmt={(it) => fmtFee(it.fee_try)} diffField="fee_try" diffs={diffs} />
                <Row label="Akreditasyon"      items={items} fmt={(it) => it.accreditation || '—'} />
                <Row label="Min başarı sırası" items={items} fmt={(it) => it.min_basari_sirasi_kosul || '—'} />

                <div className="h-3" />

                <h3 className="font-display font-semibold text-white text-sm mb-3 flex items-center gap-2 mt-2 border-t border-white/5 pt-4">
                  <Building2 size={14} className="text-cyber-cyan" />
                  Üniversite Bilgileri
                </h3>
                <Row label="Türü"         items={items} fmt={(it) => it.university_type || '—'} />
                <Row label="Kuruluş yılı" items={items} fmt={(it) => numberOrDash(it.founded_year)} diffField="founded_year" diffs={diffs} Icon={Calendar} />
                <Row label="Bölge"         items={items} fmt={(it) => it.region || '—'} />
                <Row
                  label="Web sitesi"
                  items={items}
                  fmt={(it) => it.website ? (
                    <a href={it.website} target="_blank" rel="noopener noreferrer" className="text-accent-300 hover:text-accent-200 inline-flex items-center gap-1">
                      Aç <ExternalLink size={10} />
                    </a>
                  ) : '—'}
                />

                <div className="h-3" />

                <h3 className="font-display font-semibold text-white text-sm mb-3 flex items-center gap-2 mt-2 border-t border-white/5 pt-4">
                  <Users size={14} className="text-emerald-400" />
                  Akademik Kadro
                </h3>
                <Row label="Toplam"     items={items} fmt={(it) => numberOrDash(it.academic_total)} diffField="academic_total" diffs={diffs} />
                <Row label="Profesör"   items={items} fmt={(it) => numberOrDash(it.academic_professor)} />
                <Row label="Doçent"     items={items} fmt={(it) => numberOrDash(it.academic_associate)} />
                <Row label="Dr. Öğr."   items={items} fmt={(it) => numberOrDash(it.academic_assistant)} />

                <div className="h-3" />

                <h3 className="font-display font-semibold text-white text-sm mb-3 flex items-center gap-2 mt-2 border-t border-white/5 pt-4">
                  <TrendingUp size={14} className="text-accent-400" />
                  Sıralama Trendi
                </h3>
                <div
                  className="grid gap-2 pt-2"
                  style={{ gridTemplateColumns: `120px repeat(${items.length}, minmax(0, 1fr))` }}
                >
                  <div className="text-xs text-slate-400">3 yıllık trend</div>
                  {items.map((it) => (
                    <div key={it.code} className="text-accent-300">
                      <MiniTrend trend={it.trend} />
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Legend */}
            {found.length >= 2 && Object.keys(diffs).length > 0 && (
              <div className="text-xs text-slate-500 flex items-center gap-3 flex-wrap">
                <span className="inline-flex items-center gap-1">
                  <span className="inline-block px-1 rounded text-[9px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">EN İYİ</span>
                  Her kategoride en güçlü program
                </span>
                <span className="inline-flex items-center gap-1">
                  <span className="inline-block px-1 rounded text-[9px] bg-rose-500/20 text-rose-300 border border-rose-500/30">EN ZAYIF</span>
                  En geride olan
                </span>
              </div>
            )}
          </>
        )}
      </div>
    </>
  )
}
