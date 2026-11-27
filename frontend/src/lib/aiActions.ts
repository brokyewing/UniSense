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
import { denemeHesaplaSinav } from './yksHesap'

export interface CoachAction {
  type:
    | 'set_daily_goal'
    | 'create_study_plan'
    | 'log_questions'
    | 'add_task'
    | 'mark_topic_done'
    | 'add_preference'
    | 'add_deneme'
    | 'complete_task'
    | 'add_note'
    | 'log_study_time'
    | 'update_profile'
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

async function applyAddDeneme(payload: Record<string, any>, user: any, defaultTrack: string): Promise<string> {
  const sinav = normSinav(payload.sinav, defaultTrack)
  const rawGirdi = (payload.girdi && typeof payload.girdi === 'object') ? payload.girdi : {}
  const hasAyt = Object.keys(rawGirdi).some((k) => k.startsWith('ayt_'))
  let type: string | undefined
  if (sinav === 'YKS') {
    const reqType = String(payload.type || '').toUpperCase()
    const normT = reqType === 'SOZ' ? 'SÖZ' : reqType === 'DIL' ? 'DİL' : reqType
    type = ['TYT', 'SAY', 'EA', 'SÖZ', 'DİL'].includes(normT) ? normT : (hasAyt ? 'SAY' : 'TYT')
  } else if (sinav === 'DGS') {
    const reqType = String(payload.type || '').toUpperCase()
    const normT = reqType === 'SOZ' ? 'SÖZ' : reqType
    type = ['SAY', 'EA', 'SÖZ'].includes(normT) ? normT : 'SAY'
  }

  let obp = 0
  if (user?.uid && (sinav === 'YKS' || sinav === 'DGS')) {
    try {
      const coreMod = await import('@/services/firestore-core')
      const prof = await coreMod.getUserProfile(user.uid)
      const pVal = Number(prof?.profile?.obp)
      if (pVal > 0) obp = pVal
    } catch { /* opsiyonel */ }
  }

  const canli = denemeHesaplaSinav(sinav, type || 'TYT', rawGirdi, obp)
  const offset = Number(payload.gun_offset) === -1 ? -1 : 0
  const tarih = offset === 0 ? isoGun() : addDaysIso(isoGun(), offset)
  const ad = String(payload.ad || `${canli.puanTuru || sinav} Deneme`).trim().slice(0, 120)

  let sira: number | null = null
  if (sinav === 'YKS' && type && canli.puanTuru === type && type !== 'TYT' && canli.puan > 100) {
    try {
      const { apiFetch } = await import('./api')
      const r = await apiFetch(`/api/v1/hesap/siralama?puan=${canli.puan.toFixed(2)}&tur=${encodeURIComponent(type)}`)
      sira = r?.tahmini_sira ?? null
    } catch { /* sıra opsiyonel */ }
  }

  // firestore.rules strMax('type', 8) nedeniyle KPSS/LGS'de type alanını hiç ekleme
  const deneme: Record<string, any> = {
    sinav,
    tarih,
    ad,
    ...(sinav === 'YKS' || sinav === 'DGS' ? { type } : {}),
    dersNet: canli.dersNet,
    toplamNet: canli.toplamNet,
    puan: canli.puan,
    ...(sira != null ? { sira } : {}),
  }

  if (user?.uid) {
    const studyMod = await import('@/services/firestore-study')
    await studyMod.addDeneme(user.uid, deneme)
  } else {
    const lsKey = `unisense_deneme_${sinav}`
    const cur = loadJSON<any[]>(lsKey, [])
    saveJSON(lsKey, [...cur, { ...deneme, id: `l${Date.now()}` }])
  }
  const planMod = await import('@/services/firestore-plan')
  await planMod.recordActivity(user?.uid ?? null).catch(() => {})
  const puanSuffix = canli.puan > 0 ? ` · ~${canli.puan} puan` : ''
  return `${sinav} · ${ad}: ${canli.toplamNet} net${puanSuffix} kaydedildi`
}

async function applyCompleteTask(payload: Record<string, any>, user: any, defaultTrack: string): Promise<string> {
  const sinav = normSinav(payload.sinav, defaultTrack)
  const titleNeedle = String(payload.title || '').trim()
  if (!titleNeedle) throw new Error('Tamamlanacak görev adı belirtilmedi')
  const needleLow = titleNeedle.toLocaleLowerCase(TR_LOCALE)
  const hafta = isoHafta(new Date())

  if (user?.uid) {
    const planMod = await import('@/services/firestore-plan')
    const list = await new Promise<any[]>((resolve) => {
      let unsub: (() => void) | null = null
      const timer = setTimeout(() => { if (unsub) unsub(); resolve([]) }, 1500)
      unsub = planMod.watchPlanGorevler(user.uid, hafta, (rows: any[]) => {
        clearTimeout(timer)
        if (unsub) unsub()
        resolve(rows || [])
      })
    })
    const pending = list.filter((t) => t && t.status !== 'done')
    const match = pending.find((t) => {
      const tStr = String(t.title || t.konu || '').toLocaleLowerCase(TR_LOCALE)
      return tStr.includes(needleLow) || needleLow.includes(tStr)
    })
    if (match?.id) {
      await planMod.updatePlanGorev(user.uid, match.id, { status: 'done' })
      await planMod.recordActivity(user.uid).catch(() => {})
      return `${sinav} · '${match.title || titleNeedle}' görevi tamamlandı`
    }
    return `${sinav} · '${titleNeedle}' için bekleyen görev bulunamadı`
  }

  const key = `unisense_plan_${hafta}`
  const cur = loadJSON<any[]>(key, [])
  let hitTitle = ''
  const next = cur.map((t) => {
    if (hitTitle || !t || t.status === 'done') return t
    const tStr = String(t.title || t.konu || '').toLocaleLowerCase(TR_LOCALE)
    if (tStr.includes(needleLow) || needleLow.includes(tStr)) {
      hitTitle = String(t.title || titleNeedle)
      return { ...t, status: 'done' }
    }
    return t
  })
  if (hitTitle) {
    saveJSON(key, next)
    const planMod = await import('@/services/firestore-plan')
    await planMod.recordActivity(null).catch(() => {})
    return `${sinav} · '${hitTitle}' görevi tamamlandı`
  }
  return `${sinav} · '${titleNeedle}' için bekleyen görev bulunamadı`
}

async function applyAddNote(payload: Record<string, any>, user: any, defaultTrack: string): Promise<string> {
  const sinav = normSinav(payload.sinav, defaultTrack)
  const rawMetin = String(payload.metin || '').trim()
  if (!rawMetin) throw new Error('Not metni boş')
  const ders = String(payload.ders || '').trim()
  const metin = (ders && ders !== 'Genel' ? `[${ders}] ${rawMetin}` : rawMetin).slice(0, 2000)
  const noteDoc = { metin, tamamlandi: false }

  if (user?.uid) {
    const studyMod = await import('@/services/firestore-study')
    await studyMod.addNot(user.uid, noteDoc)
  } else {
    const cur = loadJSON<any[]>('unisense_notlar', [])
    saveJSON('unisense_notlar', [{ ...noteDoc, id: `l${Date.now()}`, createdAt: Date.now() }, ...cur])
  }
  const planMod = await import('@/services/firestore-plan')
  await planMod.recordActivity(user?.uid ?? null).catch(() => {})
  return `${sinav} · Not kaydedildi`
}

async function applyLogStudyTime(payload: Record<string, any>, user: any, defaultTrack: string): Promise<string> {
  const sinav = normSinav(payload.sinav, defaultTrack)
  const dk = Math.max(5, Math.min(720, Number(payload.dakika) || 0))
  if (!dk) throw new Error('Geçersiz çalışma süresi')
  const ders = String(payload.ders || 'Genel').trim().slice(0, 60) || 'Genel'
  const today = isoGun()

  if (user?.uid) {
    const planMod = await import('@/services/firestore-plan')
    await planMod.sureEkle(user.uid, dk, ders)
    await planMod.recordActivity(user.uid).catch(() => {})
  } else {
    const cur = loadJSON<Record<string, any>>('unisense_sure', { sureDk: 0, sureHafta: {}, dersSure: {} })
    const sureDk = (Number(cur.sureDk) || 0) + dk
    const sureHafta = { ...(cur.sureHafta || {}), [today]: (Number(cur.sureHafta?.[today]) || 0) + dk }
    const dersSure = { ...(cur.dersSure || {}), [ders]: (Number(cur.dersSure?.[ders]) || 0) + dk }
    saveJSON('unisense_sure', { sureDk, sureHafta, dersSure })
    const planMod = await import('@/services/firestore-plan')
    await planMod.recordActivity(null).catch(() => {})
  }
  return `${sinav} · ${ders}: ${dk} dk çalışma süresi eklendi`
}

async function applyUpdateProfile(payload: Record<string, any>, user: any, defaultTrack: string): Promise<string> {
  const sinav = normSinav(payload.sinav, defaultTrack)
  const profilePatch: Record<string, any> = { examTrack: sinav }
  const parts = [sinav]
  if (payload.hedef_siralama != null) {
    const r = Math.max(1, Math.min(3_000_000, Number(payload.hedef_siralama)))
    if (Number.isFinite(r)) {
      profilePatch.targetRank = r
      parts.push(`Hedef Sıra ${r}`)
    }
  }
  if (payload.hedef_puan != null) {
    const s = Math.max(10, Math.min(600, Number(payload.hedef_puan)))
    if (Number.isFinite(s)) {
      profilePatch.targetScore = s
      parts.push(`Hedef Puan ${s}`)
    }
  }
  if (payload.obp != null) {
    const o = Math.max(0, Math.min(500, Number(payload.obp)))
    if (Number.isFinite(o)) {
      profilePatch.obp = o
      parts.push(`OBP ${o}`)
    }
  }
  if (payload.daily_question_goal != null) {
    const dq = Math.max(5, Math.min(1000, Number(payload.daily_question_goal)))
    if (Number.isFinite(dq)) {
      profilePatch.dailyQuestionGoal = dq
      parts.push(`Günlük ${dq} soru`)
    }
  }

  if (user?.uid) {
    const [coreMod, planMod] = await Promise.all([
      import('@/services/firestore-core'),
      import('@/services/firestore-plan'),
    ])
    const curDoc = await coreMod.getUserProfile(user.uid).catch(() => null)
    const nextProf = { ...(curDoc?.profile || {}), ...profilePatch }
    await coreMod.updateUserProfile(user.uid, nextProf)
    if (profilePatch.dailyQuestionGoal) {
      const cfg = (await planMod.getPlanConfig(user.uid)) || { haftaIciBlok: 2, haftaSonuBlok: 4, hedefSaat: 15 }
      await planMod.setPlanConfig(user.uid, { ...cfg, track: sinav, kuruldu: true, gunlukSoruHedef: profilePatch.dailyQuestionGoal })
    }
  } else {
    const curProf = loadJSON<Record<string, any>>('unisense_guest_profile', {})
    saveJSON('unisense_guest_profile', { ...curProf, ...profilePatch })
    if (profilePatch.dailyQuestionGoal) {
      const curCfg = loadJSON<Record<string, any>>('unisense_plan_cfg', { haftaIciBlok: 2, haftaSonuBlok: 4, hedefSaat: 15 })
      saveJSON('unisense_plan_cfg', { ...curCfg, track: sinav, kuruldu: true, gunlukSoruHedef: profilePatch.dailyQuestionGoal })
    }
  }
  return `${parts.join(' · ')} güncellendi`
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
      else if (act.type === 'add_deneme') detail = await applyAddDeneme(payload, user, defaultTrack)
      else if (act.type === 'complete_task') detail = await applyCompleteTask(payload, user, defaultTrack)
      else if (act.type === 'add_note') detail = await applyAddNote(payload, user, defaultTrack)
      else if (act.type === 'log_study_time') detail = await applyLogStudyTime(payload, user, defaultTrack)
      else if (act.type === 'update_profile') detail = await applyUpdateProfile(payload, user, defaultTrack)
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
