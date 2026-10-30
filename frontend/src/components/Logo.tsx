import { useState } from 'react'
import { GraduationCap } from 'lucide-react'

/**
 * UniSense Logo
 *
 * Logoyu değiştirmek için: `frontend/public/logo.png` (veya logo.svg) ekle.
 * Dosya yoksa otomatik fallback: GraduationCap ikonu (gradient kare).
 *
 * Props:
 *   - size: ikon boyutu (px). Container kareyi belirler.
 *   - rounded: köşe yuvarlaklığı (varsayılan 'rounded-2xl').
 *   - withGradient: fallback gradient arka plan (img varsa şeffaf).
 */
export default function Logo({
  size = 40,
  rounded = 'rounded-none',  // Transparent PNG için varsayılan: yuvarlatma yok
  withGradient = true,        // Sadece fallback (img yoksa) için
  className = '',
}) {
  const [imgFailed, setImgFailed] = useState(false)
  const iconSize = Math.round(size * 0.5)

  if (imgFailed) {
    return (
      <div
        className={`
          ${rounded === 'rounded-none' ? 'rounded-2xl' : rounded}
          ${withGradient ? 'bg-gradient-to-br from-brand-500 to-accent-600 shadow-lg shadow-accent-500/30' : ''}
          flex items-center justify-center shrink-0
          ${className}
        `}
        style={{ width: size, height: size }}
      >
        <GraduationCap size={iconSize} className="text-white" />
      </div>
    )
  }

  // Transparent PNG için: bg yok, shadow yok, sadece object-contain
  return (
    <img
      src="/logo.png"
      alt="UniSense"
      onError={() => setImgFailed(true)}
      className={`${rounded} object-contain shrink-0 ${className}`}
      style={{ width: size, height: size, background: 'transparent' }}
    />
  )
}
