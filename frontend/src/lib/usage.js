import { useEffect, useRef } from 'react'
import { kullanimEkle } from '../firebase'

// Uygulamada geçirilen AKTİF süreyi dakika olarak biriktirir → XP/seviyeye katkı
// ("ne kadar kalırsan seviye atlarsın"). Sadece sekme GÖRÜNÜR ve son 2 dk içinde
// ETKİLEŞİM varsa sayar → arka planda açık unutulan sekme idle-farm yapmaz.
// Ek korumalar:
//  - Çoklu sekme: localStorage kilidi — aynı anda yalnız BİR sekme sayar (2× XP olmaz).
//  - Pomodoro: odak bloğu çalışırken saymaz (aynı dakika sureDk olarak zaten yazılıyor).
//  - Flush: yazım başarısız olursa dakikalar geri eklenir (sessiz kayıp yok).
const LS = 'unisense_kullanim'
const LOCK = 'unisense_kullanim_lock'
const load = () => { try { return JSON.parse(localStorage.getItem(LS) || '{}') } catch { return {} } }
const save = (o) => { try { localStorage.setItem(LS, JSON.stringify(o)) } catch { /* noop */ } }

export function useAppTime(user) {
  const lastActive = useRef(Date.now())
  const pending = useRef(0)
  const tabId = useRef(Math.random().toString(36).slice(2))

  useEffect(() => {
    const bump = () => { lastActive.current = Date.now() }
    const evs = ['click', 'keydown', 'scroll', 'mousemove', 'touchstart']
    evs.forEach((e) => window.addEventListener(e, bump, { passive: true }))

    const flush = () => {
      const n = pending.current
      if (n <= 0 || !user?.uid) { pending.current = 0; return }
      pending.current = 0
      kullanimEkle(user.uid, n).catch(() => { pending.current += n }) // başarısızsa geri koy
    }

    const tick = setInterval(() => {
      const now = Date.now()
      if (document.visibilityState !== 'visible' || now - lastActive.current >= 120000) return
      try { if (sessionStorage.getItem('unisense_pomodoro_on')) return } catch { /* noop */ }
      // Sekme kilidi: kilit başka sekmede ve tazeyse (<90sn) bu sekme saymaz
      try {
        const lock = JSON.parse(localStorage.getItem(LOCK) || 'null')
        if (lock && lock.id !== tabId.current && now - lock.ts < 90000) return
        localStorage.setItem(LOCK, JSON.stringify({ id: tabId.current, ts: now }))
      } catch { /* noop */ }
      const o = load(); o.dk = (o.dk || 0) + 1; save(o)
      pending.current += 1
      if (pending.current >= 5) flush() // 5 dk'da bir buluta yaz (yazma tasarrufu)
    }, 60000)

    const onHide = () => { if (document.visibilityState === 'hidden') flush() }
    document.addEventListener('visibilitychange', onHide)
    window.addEventListener('beforeunload', flush)

    return () => {
      clearInterval(tick)
      evs.forEach((e) => window.removeEventListener(e, bump))
      document.removeEventListener('visibilitychange', onHide)
      window.removeEventListener('beforeunload', flush)
      flush()
    }
  }, [user])
}
