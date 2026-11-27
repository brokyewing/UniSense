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
    | 'remove_preference'
    | 'reorder_preferences'
    | 'delete_task'
    | 'reschedule_task'
    | 'complete_note'
    | 'delete_note'
    | 'unmark_topic_done'
    | 'open_compare'
  label: string
  auto_apply?: boolean
  payload?: Record<string, any>
}

export interface AppliedActionResult {
  type: CoachAction['type']
  label: string
  ok: boolean
  detail?: string
  navigateTo?: string
}

const VALID_SINAV = new Set(['YKS', 'KPSS', 'DGS', 'LGS'])
const VALID_PROF_SINAV = new Set(['YKS', 'KPSS', 'DGS', 'LGS', 'TUS', 'DUS', 'AGS'])
const VALID_PREF_SINAV = new Set(['YKS', 'KPSS', 'DGS', 'LGS', 'TUS', 'DUS'])
const TR_LOCALE = 'tr'

function normSinav(raw: unknown, fallback = 'YKS', allowed: Set<string> = VALID_SINAV): string {
  const s = String(raw || fallback).toUpperCase()
  if (allowed.has(s)) return s
  const fb = String(fallback || 'YKS').toUpperCase()
  return allowed.has(fb) ? fb : 'YKS'
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

async function applyAddPreference(payload: Record<string, any>, user: any, defaultTrack: string): Promise<string> {
  const sinav = normSinav(payload.sinav, defaultTrack, VALID_PREF_SINAV)
  const codes = Array.isArray(payload.codes) ? payload.codes.map(String).filter(Boolean).slice(0, 5) : []
  const query = typeof payload.query === 'string' ? payload.query.trim() : ''
  if (!codes.length && !query) return 'Eklenecek geçerli kod veya ad bulunamadı'

  if (sinav === 'YKS' && codes.length > 0 && !query) {
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
    return `${count} YKS programı tercih listene eklendi`
  }

  const res = await api.preferencesResolve({ sinav, codes, ...(query ? { query } : {}) })
  const items = Array.isArray(res?.items) ? res.items : []
  if (!items.length) return `${sinav} için eşleşen kayıt bulunamadı`

  if (!user?.uid) {
    if (sinav === 'YKS') {
      let c = 0
      for (const p of items) {
        if (addGuestTercih(p).ok) c++
      }
      return `${c} YKS programı tercih listene eklendi`
    }
    return `${sinav} tercih listesine kaydetmek için ücretsiz giriş yapmalısın`
  }

  const prefsMod = await import('@/services/firestore-prefs')
  let count = 0
  for (let i = 0; i < items.length; i++) {
    const it = items[i]
    try {
      if (sinav === 'KPSS') {
        await prefsMod.addToKpssTercih(user.uid, it, Date.now() + i)
      } else if (sinav === 'DGS') {
        await prefsMod.addToDgsTercih(user.uid, it, Date.now() + i)
      } else if (sinav === 'TUS' || sinav === 'DUS') {
        await prefsMod.addToUzmanlikTercih(user.uid, sinav, it, Date.now() + i)
      } else if (sinav === 'LGS') {
        await prefsMod.addToLgsTercih(user.uid, it, Date.now() + i)
      } else {
        await prefsMod.addToTercih(user.uid, it, 20 + i)
      }
      count++
    } catch { /* zaten ekli veya sınır */ }
  }
  return `${sinav} · ${count} tercih listene eklendi`
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
  const sinav = normSinav(payload.sinav, defaultTrack, VALID_PROF_SINAV)
  const parts = [sinav]

  let curProf: Record<string, any> = {}
  if (user?.uid) {
    const coreMod = await import('@/services/firestore-core')
    const curDoc = await coreMod.getUserProfile(user.uid).catch(() => null)
    curProf = curDoc?.profile || {}
  } else {
    curProf = loadJSON<Record<string, any>>('unisense_guest_profile', {})
  }

  const nextProf: Record<string, any> = { ...curProf, examTrack: sinav }
  const rankVal = payload.siralama ?? payload.hedef_siralama
  if (rankVal != null) {
    const r = Math.max(1, Math.min(3_000_000, Number(rankVal)))
    if (Number.isFinite(r)) {
      nextProf.targetRank = r
      if (sinav === 'YKS') nextProf.rank = r
      parts.push(`Sıra ${r}`)
    }
  }

  const puanVal = payload.puan ?? payload.hedef_puan
  if (puanVal != null) {
    const s = Math.max(10, Math.min(600, Number(puanVal)))
    if (Number.isFinite(s)) {
      nextProf.targetScore = s
      if (sinav === 'YKS') nextProf.score = s
      else if (sinav === 'KPSS') {
        nextProf.kpss = { ...(curProf.kpss || {}), score: s, duzey: payload.kpss_duzey || curProf.kpss?.duzey || 'lisans', updatedAt: Date.now() }
      } else if (sinav === 'DGS') {
        nextProf.dgs = { ...(curProf.dgs || {}), score: s, type: payload.puan_turu || curProf.dgs?.type || 'SAY', updatedAt: Date.now() }
      } else if (sinav === 'TUS') {
        nextProf.tus = { score: s, updatedAt: Date.now() }
      } else if (sinav === 'DUS') {
        nextProf.dus = { score: s, updatedAt: Date.now() }
      } else if (sinav === 'AGS') {
        nextProf.ags = { net: s, updatedAt: Date.now() }
      }
      parts.push(`Puan ${s}`)
    }
  }

  if (typeof payload.puan_turu === 'string' && payload.puan_turu.trim()) {
    if (sinav === 'YKS') nextProf.scoreType = payload.puan_turu.trim().toUpperCase()
    else if (sinav === 'DGS') {
      nextProf.dgs = { ...(nextProf.dgs || curProf.dgs || {}), type: payload.puan_turu.trim().toUpperCase(), updatedAt: Date.now() }
    }
  }
  if (payload.kpss_duzey && sinav === 'KPSS') {
    nextProf.kpss = { ...(nextProf.kpss || curProf.kpss || {}), duzey: String(payload.kpss_duzey), updatedAt: Date.now() }
  }
  if (payload.lgs_yuzdelik != null) {
    const yz = Math.max(0.01, Math.min(100, Number(payload.lgs_yuzdelik)))
    if (Number.isFinite(yz)) {
      nextProf.lgs = { yuzdelik: yz, updatedAt: Date.now() }
      parts.push(`%${yz} yüzdelik`)
    }
  }
  if (payload.obp != null) {
    const o = Math.max(0, Math.min(500, Number(payload.obp)))
    if (Number.isFinite(o)) {
      nextProf.obp = o
      parts.push(`OBP ${o}`)
    }
  }
  if (Array.isArray(payload.sehirler) && payload.sehirler.length > 0) {
    nextProf.preferredCities = payload.sehirler.map((c: unknown) => String(c).trim().toUpperCase()).filter(Boolean).slice(0, 10)
    parts.push(nextProf.preferredCities.slice(0, 3).join(', '))
  }
  if (payload.daily_question_goal != null) {
    const dq = Math.max(5, Math.min(1000, Number(payload.daily_question_goal)))
    if (Number.isFinite(dq)) {
      nextProf.dailyQuestionGoal = dq
      parts.push(`Günlük ${dq} soru`)
    }
  }

  if (user?.uid) {
    const [coreMod, planMod] = await Promise.all([
      import('@/services/firestore-core'),
      import('@/services/firestore-plan'),
    ])
    await coreMod.updateUserProfile(user.uid, nextProf)
    if (nextProf.dailyQuestionGoal && VALID_SINAV.has(sinav)) {
      const cfg = (await planMod.getPlanConfig(user.uid)) || { haftaIciBlok: 2, haftaSonuBlok: 4, hedefSaat: 15 }
      await planMod.setPlanConfig(user.uid, { ...cfg, track: sinav, kuruldu: true, gunlukSoruHedef: nextProf.dailyQuestionGoal })
    }
  } else {
    saveJSON('unisense_guest_profile', nextProf)
    if (nextProf.dailyQuestionGoal && VALID_SINAV.has(sinav)) {
      const curCfg = loadJSON<Record<string, any>>('unisense_plan_cfg', { haftaIciBlok: 2, haftaSonuBlok: 4, hedefSaat: 15 })
      saveJSON('unisense_plan_cfg', { ...curCfg, track: sinav, kuruldu: true, gunlukSoruHedef: nextProf.dailyQuestionGoal })
    }
  }
  return `${parts.join(' · ')} güncellendi`
}

async function applyUnmarkTopicDone(payload: Record<string, any>, user: any, defaultTrack: string): Promise<string> {
  const sinav = normSinav(payload.sinav, defaultTrack)
  const rawTopic = String(payload.konu || '').trim()
  if (!rawTopic) throw new Error('Konu adı belirtilmedi')
  const needle = rawTopic.toLocaleLowerCase(TR_LOCALE)

  let cur: Record<string, boolean> = {}
  if (user?.uid) {
    const studyMod = await import('@/services/firestore-study')
    cur = (await studyMod.getKonuIlerleme(user.uid, sinav)) || {}
  } else {
    cur = loadJSON<Record<string, boolean>>(`unisense_konu_v1_${sinav}`, {})
  }
  const next = { ...cur }
  let removedLabel = ''
  for (const k of Object.keys(next)) {
    const tail = (k.split('|').pop() || k).toLocaleLowerCase(TR_LOCALE)
    if (k.toLocaleLowerCase(TR_LOCALE).includes(needle) || needle.includes(tail)) {
      delete next[k]
      removedLabel = k.split('|').pop() || rawTopic
      break
    }
  }
  if (!removedLabel) return `${sinav} · '${rawTopic}' işaretli konular arasında bulunamadı`

  if (user?.uid) {
    const studyMod = await import('@/services/firestore-study')
    await studyMod.setKonuIlerleme(user.uid, sinav, next)
  } else {
    saveJSON(`unisense_konu_v1_${sinav}`, next)
  }
  return `${sinav} · '${removedLabel}' konu işareti kaldırıldı`
}

async function applyDeleteTask(payload: Record<string, any>, user: any, defaultTrack: string): Promise<string> {
  const sinav = normSinav(payload.sinav, defaultTrack)
  const titleNeedle = String(payload.title || '').trim()
  if (!titleNeedle) throw new Error('Silinecek görev adı belirtilmedi')
  const needleLow = titleNeedle.toLocaleLowerCase(TR_LOCALE)
  const hafta = isoHafta(new Date())

  if (user?.uid) {
    const planMod = await import('@/services/firestore-plan')
    const list = await new Promise<any[]>((resolve) => {
      let unsub: (() => void) | null = null
      const timer = setTimeout(() => { if (unsub) unsub(); resolve([]) }, 1500)
      unsub = planMod.watchPlanGorevler(user.uid, hafta, (rows: any[]) => {
        clearTimeout(timer); if (unsub) unsub(); resolve(rows || [])
      })
    })
    const match = list.find((t) => {
      const tStr = String(t?.title || t?.konu || '').toLocaleLowerCase(TR_LOCALE)
      return tStr.includes(needleLow) || needleLow.includes(tStr)
    })
    if (match?.id) {
      await planMod.removePlanGorev(user.uid, match.id)
      return `${sinav} · '${match.title || titleNeedle}' görevi silindi`
    }
    return `${sinav} · '${titleNeedle}' için görev bulunamadı`
  }

  const key = `unisense_plan_${hafta}`
  const cur = loadJSON<any[]>(key, [])
  let hitTitle = ''
  const next = cur.filter((t) => {
    if (!hitTitle && t) {
      const tStr = String(t.title || t.konu || '').toLocaleLowerCase(TR_LOCALE)
      if (tStr.includes(needleLow) || needleLow.includes(tStr)) {
        hitTitle = String(t.title || titleNeedle)
        return false
      }
    }
    return true
  })
  if (hitTitle) {
    saveJSON(key, next)
    return `${sinav} · '${hitTitle}' görevi silindi`
  }
  return `${sinav} · '${titleNeedle}' için görev bulunamadı`
}

async function applyRescheduleTask(payload: Record<string, any>, user: any, defaultTrack: string): Promise<string> {
  const sinav = normSinav(payload.sinav, defaultTrack)
  const titleNeedle = String(payload.title || '').trim()
  if (!titleNeedle) throw new Error('Taşınacak görev adı belirtilmedi')
  const needleLow = titleNeedle.toLocaleLowerCase(TR_LOCALE)
  const offset = Number(payload.gun_offset) === 1 ? 1 : 0
  const curHafta = isoHafta(new Date())
  const nextTarih = addDaysIso(isoGun(), offset)
  const nextHafta = isoHafta(new Date(`${nextTarih}T00:00:00`))

  if (user?.uid) {
    const planMod = await import('@/services/firestore-plan')
    const list = await new Promise<any[]>((resolve) => {
      let unsub: (() => void) | null = null
      const timer = setTimeout(() => { if (unsub) unsub(); resolve([]) }, 1500)
      unsub = planMod.watchPlanGorevler(user.uid, curHafta, (rows: any[]) => {
        clearTimeout(timer); if (unsub) unsub(); resolve(rows || [])
      })
    })
    const match = list.find((t) => {
      const tStr = String(t?.title || t?.konu || '').toLocaleLowerCase(TR_LOCALE)
      return tStr.includes(needleLow) || needleLow.includes(tStr)
    })
    if (match?.id) {
      await planMod.updatePlanGorev(user.uid, match.id, { tarih: nextTarih, hafta: nextHafta })
      return `${sinav} · '${match.title || titleNeedle}' ${offset ? 'yarına' : 'bugüne'} taşındı`
    }
    return `${sinav} · '${titleNeedle}' için görev bulunamadı`
  }

  const curKey = `unisense_plan_${curHafta}`
  const cur = loadJSON<any[]>(curKey, [])
  let movedTask: any = null
  const remCur = cur.filter((t) => {
    if (!movedTask && t) {
      const tStr = String(t.title || t.konu || '').toLocaleLowerCase(TR_LOCALE)
      if (tStr.includes(needleLow) || needleLow.includes(tStr)) {
        movedTask = { ...t, tarih: nextTarih, hafta: nextHafta }
        return false
      }
    }
    return true
  })
  if (!movedTask) return `${sinav} · '${titleNeedle}' için görev bulunamadı`
  if (nextHafta === curHafta) {
    saveJSON(curKey, [...remCur, movedTask])
  } else {
    saveJSON(curKey, remCur)
    const dstKey = `unisense_plan_${nextHafta}`
    const dst = loadJSON<any[]>(dstKey, [])
    saveJSON(dstKey, [...dst, movedTask])
  }
  return `${sinav} · '${movedTask.title || titleNeedle}' ${offset ? 'yarına' : 'bugüne'} taşındı`
}

async function applyNoteMutation(payload: Record<string, any>, user: any, mode: 'complete' | 'delete'): Promise<string> {
  const needle = String(payload.metin || '').trim()
  if (!needle) throw new Error('Not metni belirtilmedi')
  const needleLow = needle.toLocaleLowerCase(TR_LOCALE)

  if (user?.uid) {
    const studyMod = await import('@/services/firestore-study')
    const list = await new Promise<any[]>((resolve) => {
      let unsub: (() => void) | null = null
      const timer = setTimeout(() => { if (unsub) unsub(); resolve([]) }, 1500)
      unsub = studyMod.watchNotlar(user.uid, (rows: any[]) => {
        clearTimeout(timer); if (unsub) unsub(); resolve(rows || [])
      })
    })
    const match = list.find((n) => String(n?.metin || '').toLocaleLowerCase(TR_LOCALE).includes(needleLow))
    if (!match?.id) return `'${needle}' ile eşleşen not bulunamadı`
    if (mode === 'delete') {
      await studyMod.removeNot(user.uid, match.id)
      return `Not silindi: '${String(match.metin).slice(0, 50)}'`
    }
    await studyMod.updateNot(user.uid, match.id, { tamamlandi: true })
    return `Not tamamlandı: '${String(match.metin).slice(0, 50)}'`
  }

  const cur = loadJSON<any[]>('unisense_notlar', [])
  let matched = ''
  const next = mode === 'delete'
    ? cur.filter((n) => {
        if (!matched && String(n?.metin || '').toLocaleLowerCase(TR_LOCALE).includes(needleLow)) {
          matched = String(n.metin)
          return false
        }
        return true
      })
    : cur.map((n) => {
        if (!matched && String(n?.metin || '').toLocaleLowerCase(TR_LOCALE).includes(needleLow)) {
          matched = String(n.metin)
          return { ...n, tamamlandi: true }
        }
        return n
      })
  if (!matched) return `'${needle}' ile eşleşen not bulunamadı`
  saveJSON('unisense_notlar', next)
  return `${mode === 'delete' ? 'Not silindi' : 'Not tamamlandı'}: '${matched.slice(0, 50)}'`
}

async function applyRemovePreference(payload: Record<string, any>, user: any, defaultTrack: string): Promise<string> {
  const sinav = normSinav(payload.sinav, defaultTrack, VALID_PREF_SINAV)
  const code = String(payload.code || '').trim()
  const qLow = String(payload.query || '').trim().toLocaleLowerCase(TR_LOCALE)

  if (!user?.uid) {
    if (sinav !== 'YKS') return `${sinav} tercih listesi için giriş yapmalısın`
    const { getGuestTercih, removeGuestTercih } = await import('./guestTercih')
    const cur = getGuestTercih()
    const target = cur.find((it) => {
      const dc = String(it?.department_code || it?.id || '')
      if (code && dc === code) return true
      const blob = `${it?.department_name || ''} ${it?.university_name || ''}`.toLocaleLowerCase(TR_LOCALE)
      return Boolean(qLow && blob.includes(qLow))
    })
    if (!target) return `'${payload.query || code}' tercih listende bulunamadı`
    removeGuestTercih(String(target.department_code || target.id))
    return `${target.department_name || target.department_code} tercih listenden çıkarıldı`
  }

  const prefsMod = await import('@/services/firestore-prefs')
  const rows = await new Promise<any[]>((resolve) => {
    let unsub: (() => void) | null = null
    const timer = setTimeout(() => { if (unsub) unsub(); resolve([]) }, 1500)
    const cb = (r: any[]) => { clearTimeout(timer); if (unsub) unsub(); resolve(r || []) }
    if (sinav === 'KPSS') unsub = prefsMod.watchKpssTercih(user.uid, cb)
    else if (sinav === 'DGS') unsub = prefsMod.watchDgsTercih(user.uid, cb)
    else if (sinav === 'LGS') unsub = prefsMod.watchLgsTercih(user.uid, cb)
    else if (sinav === 'TUS' || sinav === 'DUS') unsub = prefsMod.watchUzmanlikTercih(user.uid, sinav, cb)
    else unsub = prefsMod.watchTercihList(user.uid, cb)
  })
  const hit = rows.find((it) => {
    const idVal = String(it.department_code || it.kadro_kodu || it.kod || it.id || '')
    if (code && idVal === code) return true
    const blob = `${it.department_name || ''} ${it.university_name || ''} ${it.unvan || ''} ${it.kurum || ''} ${it.program_adi || ''} ${it.okul || ''} ${it.dal || ''}`.toLocaleLowerCase(TR_LOCALE)
    return Boolean(qLow && blob.includes(qLow))
  })
  if (!hit) return `${sinav} listende '${payload.query || code}' bulunamadı`

  const docId = String(hit.id || hit.department_code || hit.kadro_kodu || hit.kod)
  if (sinav === 'KPSS') await prefsMod.removeFromKpssTercih(user.uid, docId)
  else if (sinav === 'DGS') await prefsMod.removeFromDgsTercih(user.uid, docId)
  else if (sinav === 'LGS') await prefsMod.removeFromLgsTercih(user.uid, docId)
  else if (sinav === 'TUS' || sinav === 'DUS') await prefsMod.removeFromUzmanlikTercih(user.uid, sinav, docId)
  else await prefsMod.removeFromTercih(user.uid, docId)
  return `${sinav} tercih listenden çıkarıldı`
}

async function applyReorderPreferences(payload: Record<string, any>, user: any, defaultTrack: string): Promise<string> {
  const sinav = normSinav(payload.sinav, defaultTrack, VALID_PREF_SINAV)

  const sortRows = (rows: any[]) => {
    const copy = [...rows]
    if (sinav === 'YKS') {
      copy.sort((a, b) => (a.last_year_base_rank ?? 9_999_999) - (b.last_year_base_rank ?? 9_999_999))
    } else if (sinav === 'LGS') {
      copy.sort((a, b) => (a.yuzdelik ?? 999) - (b.yuzdelik ?? 999))
    } else if (sinav === 'KPSS') {
      copy.sort((a, b) => (b.gecmis_taban ?? -1) - (a.gecmis_taban ?? -1))
    } else {
      copy.sort((a, b) => (b.min_puan ?? -1) - (a.min_puan ?? -1))
    }
    return copy
  }

  if (!user?.uid) {
    if (sinav !== 'YKS') return `${sinav} sıralama için giriş yapmalısın`
    const { getGuestTercih, setGuestTercih } = await import('./guestTercih')
    const cur = getGuestTercih()
    if (cur.length < 2) return 'Sıralamak için en az 2 tercih gerekli'
    const sorted = sortRows(cur).map((it, idx) => ({ ...it, order: idx + 1 }))
    setGuestTercih(sorted)
    return `YKS tercih listen (${sorted.length} öğe) taban sırasına göre dizildi`
  }

  const prefsMod = await import('@/services/firestore-prefs')
  const rows = await new Promise<any[]>((resolve) => {
    let unsub: (() => void) | null = null
    const timer = setTimeout(() => { if (unsub) unsub(); resolve([]) }, 1500)
    const cb = (r: any[]) => { clearTimeout(timer); if (unsub) unsub(); resolve(r || []) }
    if (sinav === 'KPSS') unsub = prefsMod.watchKpssTercih(user.uid, cb)
    else if (sinav === 'DGS') unsub = prefsMod.watchDgsTercih(user.uid, cb)
    else if (sinav === 'LGS') unsub = prefsMod.watchLgsTercih(user.uid, cb)
    else if (sinav === 'TUS' || sinav === 'DUS') unsub = prefsMod.watchUzmanlikTercih(user.uid, sinav, cb)
    else unsub = prefsMod.watchTercihList(user.uid, cb)
  })
  if (rows.length < 2) return `${sinav} listende sıralamak için en az 2 tercih olmalı`
  const sorted = sortRows(rows)
  if (sinav === 'KPSS') await prefsMod.reorderKpssTercih(user.uid, sorted)
  else if (sinav === 'DGS') await prefsMod.reorderDgsTercih(user.uid, sorted)
  else if (sinav === 'LGS') await prefsMod.reorderLgsTercih(user.uid, sorted)
  else if (sinav === 'TUS' || sinav === 'DUS') await prefsMod.reorderUzmanlikTercih(user.uid, sinav, sorted)
  else await prefsMod.reorderTercihList(user.uid, sorted)
  return `${sinav} tercih listen (${sorted.length} öğe) taban sıra/puana göre optimal dizildi`
}

/** Backend'den gelen sistem aksiyonlarını sırayla uygular ve sonuç listesi döner. */
export async function executeCoachActions(
  actions: CoachAction[] = [],
  opts: { user?: any; defaultTrack?: string } = {}
): Promise<AppliedActionResult[]> {
  if (!Array.isArray(actions) || actions.length === 0) return []
  const user = opts.user || null
  const defaultTrack = normSinav(opts.defaultTrack, 'YKS', VALID_PROF_SINAV)
  const results: AppliedActionResult[] = []

  for (const act of actions) {
    if (!act || act.auto_apply === false) continue
    const payload = act.payload || {}
    try {
      let detail = act.label
      let navigateTo: string | undefined
      if (act.type === 'set_daily_goal') detail = await applySetDailyGoal(payload, user, defaultTrack)
      else if (act.type === 'create_study_plan') detail = await applyCreateStudyPlan(payload, user, defaultTrack)
      else if (act.type === 'log_questions') detail = await applyLogQuestions(payload, user, defaultTrack)
      else if (act.type === 'add_task') detail = await applyAddTask(payload, user, defaultTrack)
      else if (act.type === 'mark_topic_done') detail = await applyMarkTopicDone(payload, user, defaultTrack)
      else if (act.type === 'unmark_topic_done') detail = await applyUnmarkTopicDone(payload, user, defaultTrack)
      else if (act.type === 'add_preference') detail = await applyAddPreference(payload, user, defaultTrack)
      else if (act.type === 'remove_preference') detail = await applyRemovePreference(payload, user, defaultTrack)
      else if (act.type === 'reorder_preferences') detail = await applyReorderPreferences(payload, user, defaultTrack)
      else if (act.type === 'add_deneme') detail = await applyAddDeneme(payload, user, defaultTrack)
      else if (act.type === 'complete_task') detail = await applyCompleteTask(payload, user, defaultTrack)
      else if (act.type === 'delete_task') detail = await applyDeleteTask(payload, user, defaultTrack)
      else if (act.type === 'reschedule_task') detail = await applyRescheduleTask(payload, user, defaultTrack)
      else if (act.type === 'add_note') detail = await applyAddNote(payload, user, defaultTrack)
      else if (act.type === 'complete_note') detail = await applyNoteMutation(payload, user, 'complete')
      else if (act.type === 'delete_note') detail = await applyNoteMutation(payload, user, 'delete')
      else if (act.type === 'log_study_time') detail = await applyLogStudyTime(payload, user, defaultTrack)
      else if (act.type === 'update_profile') detail = await applyUpdateProfile(payload, user, defaultTrack)
      else if (act.type === 'open_compare') {
        const codes = Array.isArray(payload.codes) ? payload.codes.map(String).filter(Boolean).slice(0, 5) : []
        if (codes.length < 2) throw new Error('Karşılaştırma için en az 2 program kodu gerekli')
        navigateTo = `/karsilastir?d=${codes.join(',')}`
        detail = `${codes.length} program karşılaştırmaya hazır`
      }
      results.push({ type: act.type, label: detail, ok: true, detail, ...(navigateTo ? { navigateTo } : {}) })
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
