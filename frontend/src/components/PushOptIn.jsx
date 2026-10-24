import { useState, useEffect } from 'react'
import { Bell, BellRing, Loader2, X } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { pushAvailable, enablePush, disablePush } from '../firebase'
import { track } from '../lib/analytics'

// Günlük çalışma hatırlatması opt-in kartı. Yalnızca: girişli + tarayıcı destekli
// + VAPID key yapılandırılmışsa görünür. Kapatılınca (dismiss) bir daha basmaz.
const LS_ON = 'unisense_push_on'
const LS_DISMISS = 'unisense_push_dismiss'

export default function PushOptIn() {
  const { user } = useAuth()
  const [avail, setAvail] = useState(false)
  const [state, setState] = useState('idle') // idle | on | denied | loading
  const [dismissed, setDismissed] = useState(() => !!localStorage.getItem(LS_DISMISS))

  useEffect(() => {
    let live = true
    pushAvailable().then((a) => { if (live) setAvail(a) })
    if (typeof Notification !== 'undefined') {
      if (Notification.permission === 'granted' && localStorage.getItem(LS_ON)) setState('on')
      else if (Notification.permission === 'denied') setState('denied')
    }
    return () => { live = false }
  }, [])

  if (!user || !avail) return null
  if (state !== 'on' && dismissed) return null

  async function ac() {
    setState('loading')
    try {
      // enablePush fırlatabilir (SW register hatası, FCM 'push service error', rules
      // reddi) — yakalanmazsa buton sonsuza dek spinner'da kalıyordu
      const r = await enablePush(user.uid)
      if (r.ok) { localStorage.setItem(LS_ON, '1'); setState('on'); track('push_acildi') }
      else if (r.reason === 'denied') setState('denied')
      else setState('idle')
    } catch { setState('idle') }
  }
  async function kapat() {
    await disablePush(user.uid).catch(() => {})
    localStorage.removeItem(LS_ON)
    setState('idle')
  }
  function dismiss() { localStorage.setItem(LS_DISMISS, '1'); setDismissed(true) }

  if (state === 'on') {
    return (
      <div className="card !py-2.5 flex items-center justify-between gap-3">
        <div className="text-sm text-emerald-300 flex items-center gap-2">
          <BellRing size={16} /> Günlük hatırlatma açık — serini korumak için dürteceğiz 🔥
        </div>
        <button onClick={kapat} className="text-[11px] text-slate-500 hover:text-rose-300">kapat</button>
      </div>
    )
  }

  return (
    <div className="card !py-3 flex items-center justify-between gap-3">
      <div className="min-w-0">
        <div className="text-sm font-semibold text-white flex items-center gap-2">
          <Bell size={16} className="text-accent-300" /> Günlük hatırlatma
        </div>
        <p className="text-[12px] text-slate-400 mt-0.5">
          {state === 'denied'
            ? 'Bildirim izni tarayıcıda kapalı — açmak için site ayarlarından izin ver.'
            : 'Çalışmayı unutma diye her gün nazik bir hatırlatma gönderelim. Serini korur.'}
        </p>
      </div>
      {state !== 'denied' && (
        <div className="flex items-center gap-1 shrink-0">
          <button onClick={ac} disabled={state === 'loading'}
            className="btn-primary text-xs inline-flex items-center gap-1.5 disabled:opacity-50">
            {state === 'loading' ? <Loader2 size={13} className="animate-spin" /> : <Bell size={13} />} Aç
          </button>
          <button onClick={dismiss} title="Şimdilik değil" className="text-slate-600 hover:text-white p-1"><X size={14} /></button>
        </div>
      )}
    </div>
  )
}
