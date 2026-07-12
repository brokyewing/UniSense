import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

/**
 * Geçmiş yıl taban SIRASI trendi (sparkline). `trend` = [{year, base_rank}, ...].
 * Küçük rank = iyi = grafikte yukarı. compact=true kartlar için etiketsiz mini hali.
 * Compare (tam) ve Search/Recommend/Tercih kartları (compact) ortak kullanır.
 */
export default function MiniTrend({ trend, compact = false }) {
  const pts = (trend || []).filter((t) => t.base_rank != null)
  if (pts.length < 2) {
    return compact
      ? null
      : <div className="text-[10px] text-slate-500 italic">Trend verisi yetersiz</div>
  }

  const W = compact ? 96 : 140
  const H = compact ? 26 : 50
  const P = compact ? 3 : 6
  const ranks = pts.map((p) => p.base_rank)
  const minR = Math.min(...ranks)
  const range = Math.max(Math.max(...ranks) - minR, 1)

  const points = pts.map((p, i) => ({
    x: P + (i / (pts.length - 1)) * (W - P * 2),
    y: P + ((p.base_rank - minR) / range) * (H - P * 2),
    p,
  }))
  const path = points.map((pt, i) => `${i === 0 ? 'M' : 'L'} ${pt.x} ${pt.y}`).join(' ')

  // Momentum: ilk vs son (pozitif = sıra düştü = iyileşme)
  const diff = pts[0].base_rank - pts[pts.length - 1].base_rank
  const momentum = Math.abs(diff) < 100 ? 'stable' : diff > 0 ? 'up' : 'down'
  const color = momentum === 'up' ? 'text-emerald-400' : momentum === 'down' ? 'text-rose-400' : 'text-slate-400'
  const Icon = momentum === 'up' ? TrendingUp : momentum === 'down' ? TrendingDown : Minus

  if (compact) {
    return (
      <span className="inline-flex items-center gap-1" title={`${pts[0].p.year}→${pts[pts.length - 1].p.year} sıra trendi`}>
        <svg width={W} height={H} className="block">
          <path d={path} stroke="currentColor" strokeWidth="1.5" fill="none" className="text-accent-400" />
          {points.map((pt, i) => (
            <circle key={i} cx={pt.x} cy={pt.y} r="1.8" className="fill-accent-300" />
          ))}
        </svg>
        <span className={`inline-flex items-center gap-0.5 text-[10px] ${color}`}>
          <Icon size={10} />
        </span>
      </span>
    )
  }

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
      <div className="flex items-center justify-between text-[10px] text-slate-500 mt-1">
        {points.map((pt, i) => (
          <span key={i} title={`sıra ${pt.p.base_rank?.toLocaleString('tr-TR')}`}>{pt.p.year}</span>
        ))}
      </div>
      <div className={`flex items-center justify-center gap-0.5 text-[10px] mt-0.5 ${color}`}>
        <Icon size={10} />
        {Math.abs(diff).toLocaleString('tr-TR')} sıra
      </div>
    </div>
  )
}
