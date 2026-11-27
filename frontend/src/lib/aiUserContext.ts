/**
 * Birleşik AI Öğrenci Hafızası — /arama, Ana Ekran Koçu, Deneme, Planım,
 * Karşılaştır ve TercihList için kullanıcının tam bağlamını üretir.
 */
import { api } from '@/services/api'
import { getGuestTercih } from './guestTercih'
import { konuLocal, eksikKonular } from './konu'
import { isoGun, isoHafta } from './planlayici'
import { getTodayQuestionCount } from './aiActions'

const TRACKS = new Set(['YKS', 'KPSS', 'DGS', 'LGS', 'TUS', 'DUS', 'AGS'])
const STUDY_TRACKS = new Set(['YKS', 'KPSS', 'DGS', 'LGS'])

function loadJSON<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

function onceWatch<T>(
  subscribe: (cb: (rows: T) => void) => () => void,
  fallback: T,
  timeoutMs = 1200,
): Promise<T> {
  return new Promise((resolve) => {
    let settled = false
    let unsub: (() => void) | null = null
    const finish = (val: T) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      if (unsub) {
        try { unsub() } catch { /* noop */ }
      }
      resolve(val)
    }
    const timer = setTimeout(() => finish(fallback), timeoutMs)
    try {
      unsub = subscribe((rows) => finish(rows ?? fallback))
    } catch {
      finish(fallback)
    }
  })
}

function summarizeWeakTopics(sorular: any[]): string[] {
  const m = new Map<string, { konu: string; c: number; d: number }>()
  for (const r of sorular || []) {
    const k = r?.konu || r?.ders
    if (!k) continue
    const o = m.get(k) || { konu: String(k), c: 0, d: 0 }
    o.c += Number(r.cozulen) || 0
    o.d += Number(r.dogru) || 0
    m.set(k, o)
  }
  return [...m.values()]
    .filter((o) => o.c >= 5 && o.d / o.c < 0.6)
    .slice(0, 6)
    .map((o) => o.konu.slice(0, 120))
}

function summarizeDenemeler(rows: any[]): string[] {
  if (!Array.isArray(rows) || rows.length === 0) return []
  return rows.slice(-4).reverse().map((d) => {
    const ad = String(d.ad || d.sinav || 'Deneme').slice(0, 45)
    const net = d.toplamNet != null ? `${d.toplamNet} net` : ''
    const puan = Number(d.puan) > 0 ? ` (${d.puan} p)` : ''
    const tarih = d.tarih ? ` · ${d.tarih}` : ''
    return `${ad}: ${net}${puan}${tarih}`.trim().slice(0, 140)
  })
}

function summarizeTercihler(items: any[], track: string): string[] {
  if (!Array.isArray(items) || items.length === 0) return []
  return items.slice(0, 8).map((it) => {
    if (track === 'KPSS') {
      return `[${it.kadro_kodu || it.id}] ${it.unvan || ''} — ${it.kurum || ''} (${it.il || ''})`.slice(0, 140)
    }
    if (track === 'DGS') {
      return `[${it.department_code || it.id}] ${it.program_adi || ''} (${it.university_name || ''})`.slice(0, 140)
    }
    if (track === 'LGS') {
      return `${it.okul || ''} (${it.il || ''}/${it.ilce || ''}, %${it.yuzdelik ?? '?'})`.slice(0, 140)
    }
    if (track === 'TUS' || track === 'DUS') {
      return `[${it.kod || it.id}] ${it.dal || ''} — ${it.kurum || ''}`.slice(0, 140)
    }
    const rankStr = it.last_year_base_rank ? ` · sıra ${it.last_year_base_rank}` : ''
    return `[${it.department_code || it.id}] ${it.department_name || ''} — ${it.university_name || ''}${rankStr}`.slice(0, 140)
  })
}

/**
 * Girişli (Firestore) veya misafir (localStorage) öğrencinin tüm sınav/çalışma/tercih
 * bağlamını `/api/v1/ask` `user_context` şemasına uygun şekilde derler.
 */
export async function buildUnifiedUserContext(
  user: any,
  preferredTrack?: string,
): Promise<Record<string, any> | null> {
  const bugun = isoGun()
  const hafta = isoHafta(new Date())
  const prefTr = preferredTrack ? String(preferredTrack).toUpperCase() : ''

  if (!user?.uid) {
    try {
      const cfg = loadJSON<Record<string, any> | null>('unisense_plan_cfg', null)
      const gProf = loadJSON<Record<string, any>>('unisense_guest_profile', {})
      const rawTrack = prefTr || cfg?.track || gProf?.examTrack || 'YKS'
      const track = TRACKS.has(String(rawTrack).toUpperCase()) ? String(rawTrack).toUpperCase() : 'YKS'
      const studyTrack = STUDY_TRACKS.has(track) ? track : 'YKS'

      const ctx: Record<string, any> = { exam_track: track }
      if (gProf.score) ctx.yks_puan = Number(gProf.score)
      if (gProf.scoreType) ctx.yks_turu = gProf.scoreType
      if (gProf.rank) ctx.yks_sira = Number(gProf.rank)
      if (gProf.kpss?.score) {
        ctx.kpss_puan = Number(gProf.kpss.score)
        if (gProf.kpss.duzey) ctx.kpss_duzey = gProf.kpss.duzey
      }
      if (gProf.dgs?.score) {
        ctx.dgs_puan = Number(gProf.dgs.score)
        if (gProf.dgs.type) ctx.dgs_turu = gProf.dgs.type
      }
      if (gProf.lgs?.yuzdelik != null) ctx.lgs_yuzdelik = Number(gProf.lgs.yuzdelik)
      if (gProf.tus?.score) ctx.tus_puan = Number(gProf.tus.score)
      if (gProf.dus?.score) ctx.dus_puan = Number(gProf.dus.score)
      if (Array.isArray(gProf.preferredCities) && gProf.preferredCities.length) {
        ctx.tercih_sehirler = gProf.preferredCities.slice(0, 10)
      }
      if (Array.isArray(gProf.preferredInterests) && gProf.preferredInterests.length) {
        ctx.ilgi_alanlari = gProf.preferredInterests.slice(0, 15)
      }

      const sorular = loadJSON<any[]>(`unisense_soru_${studyTrack}`, [])
      ctx.bugun_cozulen_soru = getTodayQuestionCount(sorular, bugun)
      const hedef = Number(cfg?.gunlukSoruHedef || gProf?.dailyQuestionGoal || 0)
      if (hedef > 0) ctx.gunluk_soru_hedef = hedef
      const zayif = summarizeWeakTopics(sorular)
      if (zayif.length) ctx.calisma_zayif = zayif

      const denemeler = summarizeDenemeler(loadJSON<any[]>(`unisense_deneme_${studyTrack}`, []))
      if (denemeler.length) ctx.son_denemeler = denemeler

      const tasks = loadJSON<any[]>(`unisense_plan_${hafta}`, [])
      const pending = tasks.filter((t) => t && t.status !== 'done').slice(0, 6).map((t) => `${t.title || t.konu || 'Görev'} (${t.tarih || 'bugün'})`.slice(0, 120))
      if (pending.length) ctx.bekleyen_gorevler = pending

      const notlar = loadJSON<any[]>('unisense_notlar', [])
      const activeNotlar = notlar.filter((n) => n && !n.tamamlandi).slice(0, 5).map((n) => String(n.metin || '').slice(0, 140)).filter(Boolean)
      if (activeNotlar.length) ctx.son_notlar = activeNotlar

      const guestPrefs = getGuestTercih()
      const tercihOzeti = summarizeTercihler(guestPrefs, 'YKS')
      if (tercihOzeti.length) ctx.tercih_ozeti = tercihOzeti

      const sure = loadJSON<Record<string, any>>('unisense_sure', {})
      if (Number(sure?.sureDk) > 0) ctx.toplam_calisma_dk = Number(sure.sureDk)
      const streak = loadJSON<Record<string, any> | null>('unisense_streak', null)
      if (Number(streak?.current) > 0) ctx.seri_gun = Number(streak?.current)

      const checked = konuLocal(studyTrack)
      try {
        const konuData = await api.konular(studyTrack)
        const { toplam, eksik } = eksikKonular(konuData, checked)
        if (toplam) {
          ctx.calisma_toplam_konu = toplam
          ctx.calisma_kalan_konu = eksik.length
          if (eksik.length) {
            ctx.calisma_eksik_konular = eksik.slice(0, 6).map((e: any) => `${e.ders}: ${e.konu}`.slice(0, 100))
          }
        }
      } catch { /* konu listesi opsiyonel */ }

      return ctx
    } catch {
      return null
    }
  }

  try {
    const [coreMod, planMod, studyMod, prefsMod] = await Promise.all([
      import('@/services/firestore-core'),
      import('@/services/firestore-plan'),
      import('@/services/firestore-study'),
      import('@/services/firestore-prefs'),
    ])
    const [profDoc, planCfg, istat] = await Promise.all([
      coreMod.getUserProfile(user.uid).catch(() => null),
      planMod.getPlanConfig(user.uid).catch(() => null),
      planMod.getIstatistik(user.uid).catch(() => null),
    ])

    const prof: any = profDoc?.profile || {}
    const ctx: Record<string, any> = {}
    const rawTrack = prefTr || prof.examTrack || planCfg?.track || 'YKS'
    const track = TRACKS.has(String(rawTrack).toUpperCase()) ? String(rawTrack).toUpperCase() : 'YKS'
    const studyTrack = STUDY_TRACKS.has(track) ? track : 'YKS'
    ctx.exam_track = track

    if (prof.score) {
      ctx.yks_puan = prof.score
      if (prof.scoreType) ctx.yks_turu = prof.scoreType
    }
    if (prof.rank) ctx.yks_sira = prof.rank
    if (prof.kpss?.score) {
      ctx.kpss_puan = prof.kpss.score
      if (prof.kpss.duzey) ctx.kpss_duzey = prof.kpss.duzey
    }
    if (prof.dgs?.score) {
      ctx.dgs_puan = prof.dgs.score
      if (prof.dgs.type) ctx.dgs_turu = prof.dgs.type
    }
    if (prof.tus?.score) ctx.tus_puan = prof.tus.score
    if (prof.dus?.score) ctx.dus_puan = prof.dus.score
    if (prof.lgs?.yuzdelik != null) ctx.lgs_yuzdelik = prof.lgs.yuzdelik
    if (prof.ags?.net != null) ctx.ags_net = prof.ags.net
    if (Array.isArray(prof.preferredCities) && prof.preferredCities.length) {
      ctx.tercih_sehirler = prof.preferredCities.slice(0, 10)
    }
    if (prof.preferredUniType && prof.preferredUniType !== 'all') {
      ctx.tercih_uni_turu = prof.preferredUniType
    }
    if (Array.isArray(prof.preferredInterests) && prof.preferredInterests.length) {
      ctx.ilgi_alanlari = prof.preferredInterests.slice(0, 15)
    }

    const hedef = Number(planCfg?.gunlukSoruHedef || prof.dailyQuestionGoal || 0)
    if (hedef > 0) ctx.gunluk_soru_hedef = hedef
    if (Number(istat?.sureDk) > 0) ctx.toplam_calisma_dk = Number(istat.sureDk)
    const streak = loadJSON<Record<string, any> | null>('unisense_streak', null)
    if (Number(streak?.current) > 0) ctx.seri_gun = Number(streak?.current)

    const tercihSubscribe = (cb: (rows: any[]) => void) => {
      if (track === 'KPSS') return prefsMod.watchKpssTercih(user.uid, cb)
      if (track === 'DGS') return prefsMod.watchDgsTercih(user.uid, cb)
      if (track === 'LGS') return prefsMod.watchLgsTercih(user.uid, cb)
      if (track === 'TUS' || track === 'DUS') return prefsMod.watchUzmanlikTercih(user.uid, track, cb)
      return prefsMod.watchTercihList(user.uid, cb)
    }

    const [sorular, checked, denemelerRows, tasksRows, notlarRows, tercihRows] = await Promise.all([
      planMod.getSoruList(user.uid, studyTrack).catch(() => []),
      planMod.getKonuChecked(user.uid, studyTrack).catch(() => ({})),
      onceWatch<any[]>((cb) => studyMod.watchDenemeler(user.uid, studyTrack, cb), []),
      onceWatch<any[]>((cb) => planMod.watchPlanGorevler(user.uid, hafta, cb), []),
      onceWatch<any[]>((cb) => studyMod.watchNotlar(user.uid, cb), []),
      onceWatch<any[]>(tercihSubscribe, []),
    ])

    ctx.bugun_cozulen_soru = getTodayQuestionCount(sorular, bugun)
    const zayif = summarizeWeakTopics(sorular)
    if (zayif.length) ctx.calisma_zayif = zayif

    const denemeler = summarizeDenemeler(denemelerRows)
    if (denemeler.length) ctx.son_denemeler = denemeler

    const pending = (tasksRows || [])
      .filter((t) => t && t.status !== 'done')
      .slice(0, 6)
      .map((t) => `${t.title || t.konu || 'Görev'} (${t.tarih || 'bugün'})`.slice(0, 120))
    if (pending.length) ctx.bekleyen_gorevler = pending

    const activeNotlar = (notlarRows || [])
      .filter((n) => n && !n.tamamlandi)
      .slice(0, 5)
      .map((n) => String(n.metin || '').slice(0, 140))
      .filter(Boolean)
    if (activeNotlar.length) ctx.son_notlar = activeNotlar

    const tercihOzeti = summarizeTercihler(tercihRows, track)
    if (tercihOzeti.length) ctx.tercih_ozeti = tercihOzeti

    try {
      const konuData = await api.konular(studyTrack)
      const { toplam, eksik } = eksikKonular(konuData, checked)
      if (toplam) {
        ctx.calisma_toplam_konu = toplam
        ctx.calisma_kalan_konu = eksik.length
        if (eksik.length) {
          ctx.calisma_eksik_konular = eksik.slice(0, 6).map((e: any) => `${e.ders}: ${e.konu}`.slice(0, 100))
        }
      }
    } catch { /* konu listesi opsiyonel */ }

    return Object.keys(ctx).length ? ctx : null
  } catch {
    return null
  }
}
