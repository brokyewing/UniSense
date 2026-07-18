import { useEffect, useRef } from 'react'
import { kullanimEkle } from '../firebase'

// Uygulamada geçirilen AKTİF süreyi dakika olarak biriktirir → XP/seviyeye katkı
// ("ne kadar kalırsan seviye atlarsın"). Sadece sekme GÖRÜNÜR ve son 2 dk içinde
// ETKİLEŞİM varsa sayar → arka planda açık unutulan sekme idle-farm yapmaz.
const LS = 'unisense_kullanim'
const load = () => { try { return JSON.parse(localStorage.getItem(LS) || '{}') } catch { return {} } }
const save = (o) => { try { localStorage.setItem(LS, JSON.stringify(o)) } catch { /* noop */ } }

export function useAppTime(user) {
  const lastActive = useRef(Date.now())
  const pending = useRef(0)

  useEffect(() => {
    const bump = () => { lastActive.current = Date.now() }
    const evs = ['click', 'keydown', 'scroll', 'mousemove', 'touchstart']
    evs.forEach((e) => window.addEventListener(e, bump, { passive: true }))

    const flush = () => {
      if (pending.current > 0 && user?.uid) kullanimEkle(user.uid, pending.current).catch(() => {})
      pending.current = 0
    }

    const tick = setInterval(() => {
      const aktif = document.visibilityState === 'visible' && (Date.now() - lastActive.current < 120000)
      if (!aktif) return
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
