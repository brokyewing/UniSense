// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi } from 'vitest'

const store = new Map<string, string>()
const memoryStorage = {
  getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
  setItem: (k: string, v: string) => { store.set(k, String(v)) },
  removeItem: (k: string) => { store.delete(k) },
  clear: () => { store.clear() },
}
vi.stubGlobal('localStorage', memoryStorage)

vi.mock('@/services/api', () => ({
  api: {
    konular: vi.fn(async () => ({
      dersler: {
        Matematik: ['Temel Kavramlar', 'Türev'],
      },
    })),
    programsLookup: vi.fn(async () => ({ programs: [] })),
  },
}))

vi.mock('@/services/firestore-plan', () => ({
  recordActivity: vi.fn(async () => 1),
  getPlanConfig: vi.fn(async () => null),
  setPlanConfig: vi.fn(async () => {}),
  addPlanGorev: vi.fn(async () => 'id1'),
  addPlanGorevler: vi.fn(async () => {}),
  removePlanGorev: vi.fn(async () => {}),
  watchPlanGorevler: vi.fn(() => () => {}),
  getKonuChecked: vi.fn(async () => ({})),
  getSoruList: vi.fn(async () => []),
}))

import { executeCoachActions, getTodayQuestionCount } from './aiActions'
import { isoGun, isoHafta } from './planlayici'

describe('aiActions (misafir modu)', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('set_daily_goal writes gunlukSoruHedef into guest config', async () => {
    const res = await executeCoachActions(
      [
        {
          type: 'set_daily_goal',
          label: 'YKS günlük 40 soru',
          auto_apply: true,
          payload: { sinav: 'YKS', gunluk_soru: 40, hedef_saat: 20 },
        },
      ],
      { user: null, defaultTrack: 'YKS' }
    )
    expect(res[0].ok).toBe(true)
    const cfg = JSON.parse(localStorage.getItem('unisense_plan_cfg') || '{}')
    expect(cfg.gunlukSoruHedef).toBe(40)
    expect(cfg.hedefSaat).toBe(20)
    expect(cfg.track).toBe('YKS')
  })

  it('log_questions records daily questions and updates getTodayQuestionCount', async () => {
    const res = await executeCoachActions(
      [
        {
          type: 'log_questions',
          label: '40 soru kaydedildi',
          auto_apply: true,
          payload: { sinav: 'YKS', ders: 'Türkçe', konu: 'Paragraf', cozulen: 40, dogru: 35 },
        },
      ],
      { user: null, defaultTrack: 'YKS' }
    )
    expect(res[0].ok).toBe(true)
    const list = JSON.parse(localStorage.getItem('unisense_soru_YKS') || '[]')
    expect(list).toHaveLength(1)
    expect(getTodayQuestionCount(list, isoGun())).toBe(40)
  })

  it('add_task and mark_topic_done persist guest tasks and checked topic map', async () => {
    const res = await executeCoachActions(
      [
        {
          type: 'add_task',
          label: 'Görev eklendi',
          auto_apply: true,
          payload: { sinav: 'YKS', title: 'Türev tekrarı', ders: 'Matematik', konu: 'Türev', gun_offset: 0 },
        },
        {
          type: 'mark_topic_done',
          label: 'Konu işaretlendi',
          auto_apply: true,
          payload: { sinav: 'YKS', konu: 'Türev' },
        },
      ],
      { user: null, defaultTrack: 'YKS' }
    )
    expect(res.every((r) => r.ok)).toBe(true)

    const hafta = isoHafta(new Date())
    const tasks = JSON.parse(localStorage.getItem(`unisense_plan_${hafta}`) || '[]')
    expect(tasks.some((t: any) => t.title === 'Türev tekrarı' && t.source === 'ai')).toBe(true)

    const checked = JSON.parse(localStorage.getItem('unisense_konu_v1_YKS') || '{}')
    expect(checked['|Matematik|Türev']).toBe(true)
  })

  it('add_deneme persists KPSS trial without type field and exact net/puan', async () => {
    const res = await executeCoachActions(
      [
        {
          type: 'add_deneme',
          label: 'KPSS · Pozitif Bilgi Sınavı',
          auto_apply: true,
          payload: {
            sinav: 'KPSS',
            ad: 'Pozitif Bilgi Sınavı',
            gun_offset: 0,
            girdi: {
              kpss_gy: { d: 50, y: 5 },
              kpss_gk: { d: 40, y: 10 },
            },
          },
        },
      ],
      { user: null, defaultTrack: 'YKS' }
    )
    expect(res[0].ok).toBe(true)
    const list = JSON.parse(localStorage.getItem('unisense_deneme_KPSS') || '[]')
    expect(list).toHaveLength(1)
    expect(list[0].ad).toBe('Pozitif Bilgi Sınavı')
    expect(list[0].toplamNet).toBe(86.25)
    expect(list[0].puan).toBe(83.13)
    expect('type' in list[0]).toBe(false)
  })

  it('add_note, log_study_time and complete_task update guest stores', async () => {
    const hafta = isoHafta(new Date())
    const res = await executeCoachActions(
      [
        {
          type: 'add_task',
          label: 'Görev',
          auto_apply: true,
          payload: { sinav: 'YKS', title: 'Paragraf tekrarı', gun_offset: 0 },
        },
        {
          type: 'complete_task',
          label: 'Tamamlandı',
          auto_apply: true,
          payload: { sinav: 'YKS', title: 'Paragraf tekrarı' },
        },
        {
          type: 'add_note',
          label: 'Not',
          auto_apply: true,
          payload: { sinav: 'KPSS', ders: 'Türkçe', metin: 'Önce soru kökünü oku' },
        },
        {
          type: 'log_study_time',
          label: 'Süre',
          auto_apply: true,
          payload: { sinav: 'YKS', ders: 'Matematik', dakika: 90 },
        },
      ],
      { user: null, defaultTrack: 'YKS' }
    )
    expect(res.every((r) => r.ok)).toBe(true)

    const tasks = JSON.parse(localStorage.getItem(`unisense_plan_${hafta}`) || '[]')
    expect(tasks.some((t: any) => t.title === 'Paragraf tekrarı' && t.status === 'done')).toBe(true)

    const notlar = JSON.parse(localStorage.getItem('unisense_notlar') || '[]')
    expect(notlar[0].metin).toBe('[Türkçe] Önce soru kökünü oku')

    const sure = JSON.parse(localStorage.getItem('unisense_sure') || '{}')
    expect(sure.sureDk).toBe(90)
    expect(sure.dersSure.Matematik).toBe(90)
  })
})
