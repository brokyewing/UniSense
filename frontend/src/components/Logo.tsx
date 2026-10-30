import { useState } from 'react'
import { GraduationCap } from 'lucide-react'

interface LogoProps {
  size?: number
  rounded?: string
  withGradient?: boolean
  className?: string
}

export default function Logo({
  size = 40,
  rounded = 'rounded-none',
  withGradient = true,
  className = '',
}: LogoProps) {
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