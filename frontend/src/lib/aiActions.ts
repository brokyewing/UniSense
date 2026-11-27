/**
 * Gemini / AI Koç sistem aksiyonları yürütücüsü.
 *
 * Backend `/api/v1/ask` yanıtındaki doğrulanmış `actions` dizisini öğrencinin
 * kendi hesabına (Firestore veya misafir localStorage) uygular.
 */
import { api } from '@/services/api'
import { addGuestTercih, markEngaged } from './guestTercih'
import { konuAnahtar, konuBloklari, konuLocal } from './konu'
import { gorevYap, isoGun, isoHafta, ufukPlanla } from './planlayici'

export interface CoachAction {
  type: 'set_daily_goal' | 'create_study_plan' | 'log_questions' | 'add_task' | 'mark_topic_done' | 'add_preference'
  label: string
  auto_apply?: boolean
  payload?: Record<string, any>
}

export interface AppliedActionResult {
  type: CoachAction['type']
  label: string
  ok: boolean
  detail?: string
}

const VALID_SINAV = new Set(['YKS', 'KPSS', 'DGS', 'LGS'])
const TR_LOCALE = 'tr'

function normSinav(raw: unknown, fallback = 'YKS'): string {
  const s = String(raw || fallback).toUpperCase()
  return VALID_SINAV.has(s) ? s : fallback
}

function addDaysIso(baseIso: string, offsetDays: number): string {
  const d = new Date(`${baseIso}T00:00:00`)
  d.setDate(d.getDate() + offsetDays)
  return isoGun(d)
}

function loadJSON<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

function saveJSON(key: string, val: unknown): void {
  try {
    localStorage.setItem(key, JSON.stringify(val))
  } catch { /* noop */ }
}

/** Bugün çözülen toplam soru sayısını verilen soru kayıtlarından hesaplar. */
export function getTodayQuestionCount(kayitlar: any[] = [], todayIso: string = isoGun()): number {
  let total = 0
  for (const r of kayitlar || []) {
    if (r && r.tarih === todayIso) {
      total += Number(r.cozulen) || 0
    }
  }
  return total
}

function gruplaSoru(list: any[]): any[] {
  const m = new Map<string, { ders: string; konu: string; cozulen: number; dogru: number }>()
  for (const r of list || []) {
    const key = r?.konu || r?.ders
    if (!key) continue
    const cur = m.get(key) || { ders: r.ders || '', konu: r.konu || r.ders || '', cozulen: 0, dogru: 0 }
    cur.cozulen += Number(r.cozulen) || 0
    cur.dogru += Number(r.dogru) || 0
    m.set(key, cur)
  }
  return [...m.values()]
}

async function applySetDailyGoal(payload: Record<string, any>, user: any, defaultTrack: string): Promise<string> {
  const track = normSinav(payload.sinav, defaultTrack)
  const gunlukSoruHedef = payload.gunluk_soru != null ? Math.max(5, Math.min(1000, Number(payload.gunluk_soru))) : null
  const hedefSaat = payload.hedef_saat != null ? Math.max(1, Math.min(100, Number(payload.hedef_saat))) : null
  const hedefBolum = typeof payload.hedef_bolum === 'string' && payload.hedef_bolum.trim()
    ? payload.hedef_bolum.trim().slice(0, 120)
    : null
  const patch: Record<string, any> = {
    track,
    kuruldu: true,
    ...(gunlukSoruHedef ? { gunlukSoruHedef } : {}),
    ...(hedefSaat ? { hedefSaat } : {}),
    ...(hedefBolum ? { hedefBolum } : {}),
  }
  if (user?.uid) {
    const planMod = await import('@/services/firestore-plan')
    const cur = (await planMod.getPlanConfig(user.uid)) || { haftaIciBlok: 2, haftaSonuBlok: 4, hedefSaat: 15 }
    await planMod.setPlanConfig(user.uid, { ...cur, ...patch })
  } else {
    const cur = loadJSON<Record<string, any>>('unisense_plan_cfg', { haftaIciBlok: 2, haftaSonuBlok: 4, hedefSaat: 15 })
    saveJSON('unisense_plan_cfg', { ...cur, ...patch })
  }
  const summaryParts = [track]
  if (gunlukSoruHedef) summaryParts.push(`Günlük ${gunlukSoruHedef} soru hedefi`)
  if (hedefSaat) summaryParts.push(`Haftalık ${hedefSaat} saat`)
  if (hedefBolum) summaryParts.push(`Hedef: ${hedefBolum}`)
  return `${summaryParts.join(' · ')} kaydedildi`
}

async function applyCreateStudyPlan(payload: Record<string, any>, user: any, defaultTrack: string): Promise<string> {
  const sinav = normSinav(payload.sinav, defaultTrack)
  const gunSayisi = Math.max(1, Math.min(365, Number(payload.gun_sayisi) || 30))
  const gunlukSoru = payload.gunluk_soru != null ? Math.max(5, Math.min(1000, Number(payload.gunluk_soru))) : null
  const bugun = isoGun()

  const konuData = await api.konular(sinav).catch(() => null)
  if (!konuData) {
    throw new Error(`${sinav} konu listesi alınamadı`)
  }

  let checked: Record<string, boolean> = {}
  let soruKayit: any[] = []
  if (user?.uid) {
    const planMod = await import('@/services/firestore-plan')
    checked = await planMod.getKonuChecked(user.uid, sinav)
    soruKayit = await planMod.getSoruList(user.uid, sinav)
    const curCfg = (await planMod.getPlanConfig(user.uid)) || { haftaIciBlok: 2, haftaSonuBlok: 4, hedefSaat: 15 }
    await planMod.setPlanConfig(user.uid, {
      ...curCfg,
      track: sinav,
      kuruldu: true,
      ...(gunlukSoru ? { gunlukSoruHedef: gunlukSoru } : {}),
    })
  } else {
    checked = konuLocal(sinav)
    soruKayit = loadJSON<any[]>('unisense_soru_' + sinav, [])
    const curCfg = loadJSON<Record<string, any>>('unisense_plan_cfg', { haftaIciBlok: 2, haftaSonuBlok: 4, hedefSaat: 15 })
    saveJSON('unisense_plan_cfg', {
      ...curCfg,
      track: sinav,
      kuruldu: true,
      ...(gunlukSoru ? { gunlukSoruHedef: gunlukSoru } : {}),
    })
  }

  const tasks = ufukPlanla({
    konuData,
    checked,
    soruOzet: gruplaSoru(soruKayit),
    gunSayisi,
    gunlukSoru,
    baslangic: bugun,
  })
  if (!tasks.length) {
    return `${sinav} · tüm konular zaten işaretli olduğu için yeni görev eklenmedi`
  }

  if (user?.uid) {
    const planMod = await import('@/services/firestore-plan')
    const hafta = isoHafta(new Date())
    await new Promise<void>((resolve) => {
      let unsub: (() => void) | null = null
      const timer = setTimeout(() => {
        if (unsub) unsub()
        resolve()
      }, 1500)
      unsub = planMod.watchPlanGorevler(user.uid, hafta, async (curTasks: any[]) => {
        clearTimeout(timer)
        if (unsub) unsub()
        const temiz = (curTasks || []).filter((t) => t.status !== 'done' && t.source !== 'manual')
        await Promise.all(temiz.map((t) => planMod.removePlanGorev(user.uid, t.id).catch(() => {})))
        resolve()
      })
    })
    await planMod.addPlanGorevler(user.uid, tasks)
  } else {
    const gruplar: Record<string, any[]> = {}
    for (const t of tasks) {
      ;(gruplar[t.hafta] = gruplar[t.hafta] || []).push(t)
    }
    for (const [wk, list] of Object.entries(gruplar)) {
      const cur = loadJSON<any[]>(`unisense_plan_${wk}`, []).filter((t) => t.status === 'done' || t.source === 'manual')
      const merged = [...cur, ...list.map((t, idx) => ({ ...t, id: `ai-${wk}-${Date.now()}-${idx}` }))]
      saveJSON(`unisense_plan_${wk}`, merged)
    }
  }
  return `${sinav} · ${gunSayisi} güne ${tasks.length} çalışma görevi dağıtıldı`
}

async function applyLogQuestions(payload: Record<string, any>, user: any, defaultTrack: string): Promise<string> {
  const sinav = normSinav(payload.sinav, defaultTrack)
  const cozulen = Math.max(1, Math.min(500, Number(payload.cozulen) || 0))
  const dogru = Math.max(0, Math.min(cozulen, Number(payload.dogru ?? cozulen)))
  const ders = String(payload.ders || 'Genel').slice(0, 60)
  const konu = String(payload.konu || ders || 'Günlük Çalışma').slice(0, 120)
  const tarih = isoGun()
  const kayit = { sinav, ders, konu, cozulen, dogru, tarih }

  if (user?.uid) {
    const studyMod = await import('@/services/firestore-study')
    await studyMod.addSoruKayit(user.uid, kayit)
  } else {
    const key = `unisense_soru_${sinav}`
    const cur = loadJSON<any[]>(key, [])
    saveJSON(key, [{ ...kayit, id: `l${Date.now()}`, createdAt: Date.now() }, ...cur])
  }
  const planMod = await import('@/services/firestore-plan')
  await planMod.recordActivity(user?.uid ?? null).catch(() => {})
  return `${sinav} · ${konu}: ${cozulen} soru (${dogru} doğru) işlendi`
}

async function applyAddTask(payload: Record<string, any>, user: any, defaultTrack: string): Promise<string> {
  const title = String(payload.title || '').trim().slice(0, 120)
  if (!title) throw new Error('Görev başlığı boş')
  const bugun = isoGun()
  const offset = Number(payload.gun_offset) === 1 ? 1 : 0
  const tarih = addDaysIso(bugun, offset)
  const hafta = isoHafta(new Date(`${tarih}T00:00:00`))
  const task = {
    ...gorevYap({
      id: `ai-${Date.now()}`,
      ders: String(payload.ders || '').slice(0, 60),
      konu: String(payload.konu || title).slice(0, 120),
      title,
      tarih,
      source: 'ai',
      tur: 'yeni',
    }),
    hafta,
  }
  if (user?.uid) {
    const planMod = await import('@/services/firestore-plan')
    const sinav = normSinav(payload.sinav, defaultTrack)
    const cur = await planMod.getPlanConfig(user.uid)
    if (!cur?.kuruldu) {
      await planMod.setPlanConfig(user.uid, { track: sinav, hedefSaat: 15, haftaIciBlok: 2, haftaSonuBlok: 4, kuruldu: true })
    }
    await planMod.addPlanGorev(user.uid, task)
  } else {
    const cur = loadJSON<any[]>(`unisense_plan_${hafta}`, [])
    saveJSON(`unisense_plan_${hafta}`, [...cur, task])
  }
  return `${offset ? 'Yarın' : 'Bugün'} için '${title}' eklendi`
}

async function applyMarkTopicDone(payload: Record<string, any>, user: any, defaultTrack: string): Promise<string> {
  const sinav = normSinav(payload.sinav, defaultTrack)
  const rawTopic = String(payload.konu || '').trim()
  if (!rawTopic) throw new Error('Konu adı belirtilmedi')
  const needle = rawTopic.toLocaleLowerCase(TR_LOCALE)

  const konuData = await api.konular(sinav).catch(() => null)
  let matchedKey: string | null = null
  let matchedLabel = rawTopic
  if (konuData) {
    const bloklar = konuBloklari(konuData)
    for (const b of bloklar as any[]) {
      for (const k of b.konular || []) {
        const kLow = String(k).toLocaleLowerCase(TR_LOCALE)
        if (kLow === needle || kLow.includes(needle) || needle.includes(kLow)) {
          matchedKey = konuAnahtar(b.grup, b.ders, k)
          matchedLabel = String(k)
          break
        }
      }
      if (matchedKey) break
    }
  }
  const keyToWrite = matchedKey || konuAnahtar(null, 'Genel', matchedLabel)

  if (user?.uid) {
    const studyMod = await import('@/services/firestore-study')
    const cur = await studyMod.getKonuIlerleme(user.uid, sinav)
    await studyMod.setKonuIlerleme(user.uid, sinav, { ...(cur || {}), [keyToWrite]: true })
  } else {
    const lsKey = `unisense_konu_v1_${sinav}`
    const cur = loadJSON<Record<string, boolean>>(lsKey, {})
    saveJSON(lsKey, { ...cur, [keyToWrite]: true })
  }
  const planMod = await import('@/services/firestore-plan')
  await planMod.recordActivity(user?.uid ?? null).catch(() => {})
  return `${sinav} · '${matchedLabel}' konusu tamamlandı`
}

async function applyAddPreference(payload: Record<string, any>, user: any): Promise<string> {
  const codes = Array.isArray(payload.codes) ? payload.codes.map(String).filter(Boolean).slice(0, 5) : []
  if (!codes.length) return 'Eklenecek geçerli ÖSYM kodu bulunamadı'
  const res = await api.programsLookup(codes)
  const found = (res?.programs || []).filter((p: any) => p?.found)
  if (!found.length) return 'Program bilgisi bulunamadı'

  let count = 0
  if (user?.uid) {
    const prefsMod = await import('@/services/firestore-prefs')
    for (let i = 0; i < found.length; i++) {
      const p = found[i]
      try {
        await prefsMod.addToTercih(user.uid, {
          department_code: p.department_code,
          department_name: p.department_name,
          university_code: p.university_code,
          university_name: p.university_name,
          city: p.city,
          score_type: p.score_type || null,
          last_year_base_rank: p.last_year_base_rank ?? null,
          last_year_base_score: p.last_year_base_score ?? null,
          quota: p.quota ?? null,
        }, 20 + i)
        count++
      } catch { /* zaten ekli veya dolu */ }
    }
  } else {
    for (const p of found) {
      const out = addGuestTercih(p)
      if (out.ok) count++
    }
  }
  return `${count} program tercih listene eklendi`
}

/** Backend'den gelen sistem aksiyonlarını sırayla uygular ve sonuç listesi döner. */
export async function executeCoachActions(
  actions: CoachAction[] = [],
  opts: { user?: any; defaultTrack?: string } = {}
): Promise<AppliedActionResult[]> {
  if (!Array.isArray(actions) || actions.length === 0) return []
  const user = opts.user || null
  const defaultTrack = normSinav(opts.defaultTrack, 'YKS')
  const results: AppliedActionResult[] = []

  for (const act of actions) {
    if (!act || act.auto_apply === false) continue
    const payload = act.payload || {}
    try {
      let detail = act.label
      if (act.type === 'set_daily_goal') detail = await applySetDailyGoal(payload, user, defaultTrack)
      else if (act.type === 'create_study_plan') detail = await applyCreateStudyPlan(payload, user, defaultTrack)
      else if (act.type === 'log_questions') detail = await applyLogQuestions(payload, user, defaultTrack)
      else if (act.type === 'add_task') detail = await applyAddTask(payload, user, defaultTrack)
      else if (act.type === 'mark_topic_done') detail = await applyMarkTopicDone(payload, user, defaultTrack)
      else if (act.type === 'add_preference') detail = await applyAddPreference(payload, user)
      results.push({ type: act.type, label: detail, ok: true, detail })
    } catch (e: any) {
      results.push({ type: act.type, label: act.label, ok: false, detail: e?.message || 'Uygulanamadı' })
    }
  }

  if (results.some((r) => r.ok)) {
    markEngaged()
    try {
      window.dispatchEvent(new CustomEvent('unisense:ai-state-updated', { detail: results }))
    } catch { /* SSR/node test ortamı */ }
  }
  return results
}
