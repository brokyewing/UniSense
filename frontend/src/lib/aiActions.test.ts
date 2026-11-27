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
    preferencesResolve: vi.fn(async () => ({ sinav: 'YKS', items: [] })),
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

  it('update_profile syncs Profile.tsx schema fields and executes all Paket C mutations', async () => {
    const hafta = isoHafta(new Date())
    localStorage.setItem('unisense_guest_tercih_yks', JSON.stringify([
      { department_code: '203910363', department_name: 'Bilgisayar Müh', university_name: 'Boğaziçi', last_year_base_rank: 5000, order: 1 },
      { department_code: '105510079', department_name: 'Yazılım Müh', university_name: 'İTÜ', last_year_base_rank: 1500, order: 2 },
    ]))

    const res = await executeCoachActions(
      [
        {
          type: 'update_profile',
          label: 'Profil güncellendi',
          auto_apply: true,
          payload: { sinav: 'YKS', siralama: 25000, puan: 445, puan_turu: 'SAY', obp: 460, sehirler: ['İSTANBUL', 'ANKARA'] },
        },
        {
          type: 'mark_topic_done',
          label: 'İşaretlendi',
          auto_apply: true,
          payload: { sinav: 'YKS', konu: 'Türev' },
        },
        {
          type: 'unmark_topic_done',
          label: 'İşaret kaldırıldı',
          auto_apply: true,
          payload: { sinav: 'YKS', konu: 'Türev' },
        },
        {
          type: 'add_task',
          label: 'Görev eklendi',
          auto_apply: true,
          payload: { sinav: 'YKS', title: 'Optik tekrarı', gun_offset: 0 },
        },
        {
          type: 'reschedule_task',
          label: 'Taşındı',
          auto_apply: true,
          payload: { sinav: 'YKS', title: 'Optik tekrarı', gun_offset: 1 },
        },
        {
          type: 'delete_task',
          label: 'Silindi',
          auto_apply: true,
          payload: { sinav: 'YKS', title: 'Optik tekrarı' },
        },
        {
          type: 'add_note',
          label: 'Not eklendi',
          auto_apply: true,
          payload: { sinav: 'YKS', ders: 'Türkçe', metin: 'Paragraf taktiği' },
        },
        {
          type: 'complete_note',
          label: 'Not tamamlandı',
          auto_apply: true,
          payload: { metin: 'Paragraf taktiği' },
        },
        {
          type: 'delete_note',
          label: 'Not silindi',
          auto_apply: true,
          payload: { metin: 'Paragraf taktiği' },
        },
        {
          type: 'reorder_preferences',
          label: 'Sıralandı',
          auto_apply: true,
          payload: { sinav: 'YKS', strategy: 'optimal' },
        },
        {
          type: 'remove_preference',
          label: 'Çıkarıldı',
          auto_apply: true,
          payload: { sinav: 'YKS', code: '203910363', query: 'Boğaziçi' },
        },
        {
          type: 'open_compare',
          label: 'Karşılaştır',
          auto_apply: true,
          payload: { codes: ['203910363', '105510079'] },
        },
      ],
      { user: null, defaultTrack: 'YKS' }
    )

    expect(res.every((r) => r.ok)).toBe(true)
    const gp = JSON.parse(localStorage.getItem('unisense_guest_profile') || '{}')
    expect(gp.rank).toBe(25000)
    expect(gp.score).toBe(445)
    expect(gp.scoreType).toBe('SAY')
    expect(gp.obp).toBe(460)
    expect(gp.preferredCities).toEqual(['İSTANBUL', 'ANKARA'])

    const checked = JSON.parse(localStorage.getItem('unisense_konu_v1_YKS') || '{}')
    expect(Object.keys(checked)).toHaveLength(0)

    const notlar = JSON.parse(localStorage.getItem('unisense_notlar') || '[]')
    expect(notlar).toHaveLength(0)

    const tasks = JSON.parse(localStorage.getItem(`unisense_plan_${hafta}`) || '[]')
    expect(tasks.some((t: any) => t.title === 'Optik tekrarı')).toBe(false)

    const tercih = JSON.parse(localStorage.getItem('unisense_guest_tercih_yks') || '[]')
    expect(tercih).toHaveLength(1)
    expect(tercih[0].department_code).toBe('105510079')

    const cmp = res.find((r) => r.type === 'open_compare')
    expect(cmp?.navigateTo).toBe('/karsilastir?d=203910363,105510079')
  })
})
