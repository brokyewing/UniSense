/**
 * Custom Hooks — yaygın pattern'leri soyutlar.
 * Search.jsx, Recommend.jsx, Calisma.jsx'deki tekrar eden mantığı merkezileştirir.
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { useAuth } from '../contexts/AuthContext'
import {
  watchTercihList, watchDgsTercih, watchKpssTercih, watchLgsTercih, watchUzmanlikTercih,
} from './firestore-prefs'
import {
  watchKonuIlerleme, watchDenemeler, watchSoruKayit, watchYanlislar, watchNotlar, watchKartlar,
} from './firestore-study'
import {
  watchPlanGorevler,
  getPlanConfig, setPlanConfig, updatePlanGorev, addPlanGorev, addPlanGorevler, removePlanGorev, getKonuChecked, getSoruList,
} from './firestore-plan'
import {
  watchSessions, watchSessionMessages,
  setEmailReminders,
} from './firestore-push'
import { getIstatistik, sureEkle as sureEklePlan, recordActivity as recordActivityPlan, guestStats, recordActivity } from './firestore-plan'
import { watchSubcollection } from './firestore-core'
import { FIRESTORE_COLLECTIONS, TERCIH_LIMITS } from './constants'

// === Tercih Listesi Hooks ===

/**
 * YKS Tercih Listesi — canlı izleme + ekleme/çıkarma helper'ları.
 * @returns { tercihIds: Set, add: fn, remove: fn, busyCode: string, setBusyCode: fn }
 */
export function useTercihList() {
  const { user } = useAuth()
  const [tercihIds, setTercihIds] = useState(new Set())
  const [busyCode, setBusyCode] = useState(null)

  useEffect(() => {
    if (!user) { setTercihIds(new Set()); return }
    return watchTercihList(user.uid, (items) =>
      setTercihIds(new Set(items.map(i => String(i.department_code || i.id))))
    )
  }, [user])

  return { tercihIds, busyCode, setBusyCode }
}

export function useDgsTercih() {
  const { user } = useAuth()
  const [tercihIds, setTercihIds] = useState(new Set())
  const [busyCode, setBusyCode] = useState(null)

  useEffect(() => {
    if (!user) { setTercihIds(new Set()); return }
    return watchDgsTercih(user.uid, (items) =>
      setTercihIds(new Set(items.map(i => String(i.department_code))))
    )
  }, [user])

  return { tercihIds, busyCode, setBusyCode }
}

export function useKpssTercih() {
  const { user } = useAuth()
  const [tercihIds, setTercihIds] = useState(new Set())
  const [busyCode, setBusyCode] = useState(null)

  useEffect(() => {
    if (!user) { setTercihIds(new Set()); return }
    return watchKpssTercih(user.uid, (items) =>
      setTercihIds(new Set(items.map(i => String(i.kadro_kodu))))
    )
  }, [user])

  return { tercihIds, busyCode, setBusyCode }
}

export function useLgsTercih() {
  const { user } = useAuth()
  const [tercihIds, setTercihIds] = useState(new Set())

  useEffect(() => {
    if (!user) { setTercihIds(new Set()); return }
    return watchLgsTercih(user.uid, (items) =>
      setTercihIds(new Set(items.map(i => String(i.okul || i.id))))
    )
  }, [user])

  return { tercihIds }
}

export function useUzmanlikTercih(sinav) {
  const { user } = useAuth()
  const [tercihIds, setTercihIds] = useState(new Set())

  useEffect(() => {
    if (!user) { setTercihIds(new Set()); return }
    return watchUzmanlikTercih(user.uid, sinav, (items) =>
      setTercihIds(new Set(items.map(i => String(i.kod || i.id))))
    )
  }, [user, sinav])

  return { tercihIds }
}

// === Çalışma Takibi Hooks ===

export function useKonuIlerleme(sinav) {
  const { user } = useAuth()
  const [checked, setChecked] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user || !sinav) { setChecked({}); setLoading(false); return }
    setLoading(true)
    return watchKonuIlerleme(user.uid, sinav, (data) => {
      setChecked(data || {})
      setLoading(false)
    })
  }, [user, sinav])

  return { checked, loading }
}

export function useDenemeler(sinav) {
  const { user } = useAuth()
  const [denemeler, setDenemeler] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user || !sinav) { setDenemeler([]); setLoading(false); return }
    setLoading(true)
    return watchDenemeler(user.uid, sinav, (data) => {
      setDenemeler(data || [])
      setLoading(false)
    })
  }, [user, sinav])

  return { denemeler, loading }
}

export function useSoruKayit(sinav) {
  const { user } = useAuth()
  const [kayitlar, setKayitlar] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user || !sinav) { setKayitlar([]); setLoading(false); return }
    setLoading(true)
    return watchSoruKayit(user.uid, sinav, (data) => {
      setKayitlar(data || [])
      setLoading(false)
    })
  }, [user, sinav])

  return { kayitlar, loading }
}

export function useYanlislar() {
  const { user } = useAuth()
  const [yanlislar, setYanlislar] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) { setYanlislar([]); setLoading(false); return }
    setLoading(true)
    return watchYanlislar(user.uid, (data) => {
      setYanlislar(data || [])
      setLoading(false)
    })
  }, [user])

  return { yanlislar, loading }
}

export function useNotlar() {
  const { user } = useAuth()
  const [notlar, setNotlar] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) { setNotlar([]); setLoading(false); return }
    setLoading(true)
    return watchNotlar(user.uid, (data) => {
      setNotlar(data || [])
      setLoading(false)
    })
  }, [user])

  return { notlar, loading }
}

export function useKartlar() {
  const { user } = useAuth()
  const [kartlar, setKartlar] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) { setKartlar([]); setLoading(false); return }
    setLoading(true)
    return watchKartlar(user.uid, (data) => {
      setKartlar(data || [])
      setLoading(false)
    })
  }, [user])

  return { kartlar, loading }
}

// === Planlayıcı Hooks ===

export function usePlanGorevler(hafta) {
  const { user } = useAuth()
  const [gorevler, setGorevler] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user || !hafta) { setGorevler([]); setLoading(false); return }
    setLoading(true)
    return watchPlanGorevler(user.uid, hafta, (data) => {
      setGorevler(data || [])
      setLoading(false)
    })
  }, [user, hafta])

  return { gorevler, loading }
}

// === Chat Session Hooks ===

export function useSessions() {
  const { user } = useAuth()
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) { setSessions([]); setLoading(false); return }
    setLoading(true)
    return watchSessions(user.uid, (data) => {
      setSessions(data || [])
      setLoading(false)
    })
  }, [user])

  return { sessions, loading }
}

export function useSessionMessages(sessionId) {
  const { user } = useAuth()
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user || !sessionId) { setMessages([]); setLoading(false); return }
    setLoading(true)
    return watchSessionMessages(user.uid, sessionId, (data) => {
      setMessages(data || [])
      setLoading(false)
    })
  }, [user, sessionId])

  return { messages, loading }
}

// === Generic Subcollection Hook ===

/**
 * Herhangi bir alt koleksiyonu izlemek için jenerik hook.
 * @param {string} subcollection - koleksiyon adı (constants'tan)
 * @param {Object} options - { where, orderBy, limit }
 * @returns { data, loading, error }
 */
export function useSubcollection(subcollection, options = {}) {
  const { user } = useAuth()
  const [data, setData] = useState(options.where ? [] : {})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!user) { setData(options.where ? [] : {}); setLoading(false); return }
    setLoading(true)
    setError(null)

    const unsub = watchSubcollection(user.uid, subcollection, (items) => {
      if (items === null) { setError(new Error('İzin hatası / offline')); setData(options.where ? [] : {}) }
      else { setData(items); setError(null) }
      setLoading(false)
    }, options)

    return () => { unsub(); setLoading(false) }
  }, [user, subcollection, JSON.stringify(options)])

  return { data, loading, error }
}

// === Debounced Search / Input Hook ===

export function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(id)
  }, [value, delay])
  return debounced
}

// === LocalStorage Sync Hook ===

export function useLocalStorage(key, initialValue) {
  const [value, setValue] = useState(() => {
    try { const item = localStorage.getItem(key); return item ? JSON.parse(item) : initialValue } catch { return initialValue }
  })

  const setStoredValue = useCallback((newValue) => {
    try { const val = newValue instanceof Function ? newValue(value) : newValue; setValue(val); localStorage.setItem(key, JSON.stringify(val)) } catch {}
  }, [key, value])

  return [value, setStoredValue]
}

// === SessionStorage Hook ===

export function useSessionStorage(key, initialValue) {
  const [value, setValue] = useState(() => {
    try { const item = sessionStorage.getItem(key); return item ? JSON.parse(item) : initialValue } catch { return initialValue }
  })

  const setStoredValue = useCallback((newValue) => {
    try { const val = newValue instanceof Function ? newValue(value) : newValue; setValue(val); sessionStorage.setItem(key, JSON.stringify(val)) } catch {}
  }, [key, value])

  return [value, setStoredValue]
}

// === Toast / Notification Hook ===

export function useToast() {
  const [toasts, setToasts] = useState([])

  const show = useCallback((message, { type = 'info', duration = 3000 } = {}) => {
    const id = Date.now() + Math.random()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration)
    return id
  }, [])

  const dismiss = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return { toasts, show, dismiss }
}

// === Async Operation Hook (loading/error state management) ===

export function useAsync(asyncFn) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)

  const execute = useCallback(async (...args) => {
    setLoading(true)
    setError(null)
    try { const result = await asyncFn(...args); setData(result); return result } catch (e) { setError(e); throw e } finally { setLoading(false) }
  }, [asyncFn])

  return { execute, loading, error, data, setData, setError }
}

// === Intersection Observer Hook (lazy load, infinite scroll) ===

export function useIntersectionObserver(ref, options = {}) {
  const [isIntersecting, setIsIntersecting] = useState(false)

  useEffect(() => {
    if (!ref.current) return
    const observer = new IntersectionObserver(([entry]) => setIsIntersecting(entry.isIntersecting), options)
    observer.observe(ref.current)
    return () => observer.disconnect()
  }, [ref, options])

  return isIntersecting
}

// === Media Query Hook ===

export function useMediaQuery(query) {
  const [matches, setMatches] = useState(false)

  useEffect(() => {
    const media = window.matchMedia(query)
    if (media.matches !== matches) setMatches(media.matches)
    const listener = (e) => setMatches(e.matches)
    media.addEventListener('change', listener)
    return () => media.removeEventListener('change', listener)
  }, [matches, query])

  return matches
}

// === Plan Config Hook ===

export function usePlanConfig() {
  const { user } = useAuth()
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) { setConfig(null); setLoading(false); return }
    setLoading(true)
    getPlanConfig(user.uid).then((c) => { setConfig(c); setLoading(false) }).catch(() => { setConfig(null); setLoading(false) })
  }, [user])

  const updateConfig = useCallback(async (cfg) => {
    if (!user) return
    await setPlanConfig(user.uid, cfg)
    setConfig((prev) => ({ ...prev, ...cfg }))
  }, [user])

  return { config, loading, updateConfig }
}

// === Istatistik Hook (Pano) ===

export function useIstatistik() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  const yukle = useCallback(async () => {
    if (!user) { setStats(await import('@/services/firestore-plan').then(m => m.guestStats())); return }
    setStats(await getIstatistik(user.uid))
  }, [user])

  useEffect(() => { yukle() }, [yukle])

  return { stats, loading, yukle }
}

// === Pomodoro Hook (Pano) ===

export function usePomodoro() {
  const { user } = useAuth()
  const [mod, setMod] = useState('odak')
  const [kalan, setKalan] = useState(25 * 60)
  const [calisiyor, setCalisiyor] = useState(false)
  const [ders, setDers] = useState('')
  const [toast, setToast] = useState('')

  const ODAK = 25 * 60
  const MOLA = 5 * 60

  const bitisRef = useRef(null)

  const yukle = useCallback(async () => {
    if (user) {
      const { getIstatistik } = await import('@/services/firestore-plan')
      const s = await getIstatistik(user.uid)
    }
  }, [user])

  useEffect(() => {
    if (!calisiyor) { bitisRef.current = null; return }
    bitisRef.current = Date.now() + kalan * 1000
    const t = setInterval(() => setKalan(Math.max(0, Math.round((bitisRef.current - Date.now()) / 1000))), 1000)
    return () => clearInterval(t)
  }, [calisiyor])

  useEffect(() => {
    if (kalan !== 0 || !calisiyor) return
    setCalisiyor(false)
    if (mod === 'odak') {
      const dk = 25
      if (user) sureEkle(user.uid, dk, ders.trim()).catch(() => {})
      else {
        import('@/services/firestore-plan').then(m => m.guestSureEkle(dk, ders.trim()))
      }
      recordActivity(user?.uid).catch(() => {})
      setToast('🎉 25 dk odak tamam! Kısa mola.')
      setTimeout(() => setToast(''), 2500)
      setMod('mola'); setKalan(5 * 60)
    } else {
      setMod('odak'); setKalan(25 * 60)
    }
  }, [kalan, calisiyor, mod, ders, user])

  const sifirla = () => { setCalisiyor(false); setKalan(mod === 'odak' ? 25 * 60 : 5 * 60) }
  const modDegis = (m) => { setCalisiyor(false); setMod(m); setKalan(m === 'odak' ? 25 * 60 : 5 * 60) }

  return { mod, kalan, calisiyor, ders, setDers, calisiyor, setCalisiyor, modDegis, sifirla, toast, setToast }
}

// === Email Reminders Hook ===

export function useEmailReminders() {
  const { user } = useAuth()
  const [emailOn, setEmailOn] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) { setEmailOn(false); setLoading(false); return }
    import('@/services/firestore-push').then(m => m.getUserProfile(user.uid)).then((p) => { setEmailOn(!!p?.emailReminders); setLoading(false) }).catch(() => { setEmailOn(false); setLoading(false) })
  }, [user])

  const toggle = useCallback(async () => {
    if (!user) return
    const v = !emailOn
    setEmailOn(v)
    await setEmailReminders(user.uid, v).catch(() => setEmailOn(!v))
  }, [user, emailOn])

  return { emailOn, loading, toggle }
}

// === Analytics Hook ===

export function useAnalytics() {
  const { user } = useAuth()
  const logEvent = useCallback((eventType, page, metadata = {}) => {
    import('@/services/api').then(m => m.api.analyticsLog(eventType, page, user?.uid || null).catch(() => {}))
  }, [user])
  return { logEvent }
}

// === User Profile Hook ===

export function useUserProfile() {
  const { user } = useAuth()
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) { setProfile(null); setLoading(false); return }
    setLoading(true)
    import('@/services/firestore-core').then(m => m.getUserProfile(user.uid)).then((p) => { setProfile(p); setLoading(false) }).catch(() => { setProfile(null); setLoading(false) })
  }, [user])

  return { profile, loading }
}