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
})
