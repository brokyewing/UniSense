import { useState, useEffect } from 'react'
import { Download, X } from 'lucide-react'

export default function PWAInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState(null)
  const [showPrompt, setShowPrompt] = useState(false)

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault()
      setDeferredPrompt(e)
      // Daha önce reddedilmişse gösterme
      const dismissed = localStorage.getItem('pwa-install-dismissed')
      if (!dismissed) setShowPrompt(true)
    }
    window.addEventListener('beforeinstallprompt', handler)
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  const handleInstall = async () => {
    if (!deferredPrompt) return
    deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    if (outcome === 'accepted') {
      setShowPrompt(false)
    }
    setDeferredPrompt(null)
  }

  const handleDismiss = () => {
    setShowPrompt(false)
    localStorage.setItem('pwa-install-dismissed', '1')
  }

  if (!showPrompt) return null

  return (
    <div className="fixed bottom-4 left-4 right-4 sm:left-auto sm:right-4 sm:w-80 z-50 card border-accent-500/30 bg-accent-500/10 backdrop-blur-xl animate-slide-up">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-accent-600 flex items-center justify-center shrink-0">
          <Download size={18} className="text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-white">UniSense'i Yükle</h3>
          <p className="text-xs text-slate-400 mt-0.5">Ana ekranına ekle, çevrimdışı erişim sağla</p>
          <div className="flex gap-2 mt-2">
            <button onClick={handleInstall} className="btn-primary text-xs px-3 py-1.5">Yükle</button>
            <button onClick={handleDismiss} className="text-xs text-slate-400 hover:text-white px-2 py-1.5">Şimdi değil</button>
          </div>
        </div>
        <button onClick={handleDismiss} className="text-slate-500 hover:text-white shrink-0">
          <X size={14} />
        </button>
      </div>
    </div>
  )
}