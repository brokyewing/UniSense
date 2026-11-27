import { describe, it, expect } from 'vitest'
import {
  netOf,
  diploma100ToObp,
  gpa4ToAobp,
  placementScore,
  denemeHesapla,
  denemeHesaplaSinav,
} from './yksHesap'

describe('yksHesap', () => {
  it('computes netOf with default 0.25 penalty and custom penalty', () => {
    expect(netOf(40, 0)).toBe(40)
    expect(netOf(36, 4)).toBe(35)
    expect(netOf(10, 3, 1 / 3)).toBeCloseTo(9, 5)
    expect(netOf('', '')).toBe(0)
  })

  it('validates diploma100ToObp and gpa4ToAobp bounds', () => {
    expect(diploma100ToObp(49.9)).toBe(0)
    expect(diploma100ToObp(50)).toBe(250)
    expect(diploma100ToObp(100)).toBe(500)
    expect(diploma100ToObp(101)).toBe(0)

    expect(gpa4ToAobp(-0.1)).toBe(0)
    expect(gpa4ToAobp(4)).toBe(50)
    expect(gpa4ToAobp(2)).toBe(25)
    expect(gpa4ToAobp(4.1)).toBe(0)
  })

  it('requires positive AYT score for placementScore and computes SAY placement', () => {
    expect(placementScore({ tyt_tr: 30, tyt_mat: 30 }, 'SAY', 400)).toBe(0)
    const say = placementScore(
      { tyt_tr: 30, tyt_sos: 10, tyt_mat: 30, tyt_fen: 15, ayt_mat: 30, ayt_fiz: 10, ayt_kim: 10, ayt_biy: 10 },
      'SAY',
      450
    )
    // 100 + (39.6 + 13.6 + 39.6 + 20.4) + (90 + 28.5 + 30.7 + 30.7) + 450*0.12 = 447.1
    expect(say).toBeCloseTo(447.1, 2)
  })

  it('computes denemeHesapla and falls back to TYT when AYT is zero', () => {
    const res = denemeHesapla({ tyt_tr: { d: 32, y: 8 }, ayt_dil: { d: 60, y: 0 } }, 'DİL', 400)
    expect(res.toplamNet).toBe(90)
    expect(res.puan).toBeGreaterThan(300)

    const tytOnly = denemeHesaplaSinav('YKS', 'SAY', { tyt_tr: { d: 36, y: 4 }, tyt_mat: { d: 28, y: 4 } }, 400)
    expect(tytOnly.puanTuru).toBe('TYT')
    expect(tytOnly.puan).toBeGreaterThan(200)
  })

  it('computes KPSS, LGS, and DGS scores via denemeHesaplaSinav', () => {
    const kpss = denemeHesaplaSinav('KPSS', 'SAY', { kpss_gy: { d: 44, y: 16 }, kpss_gk: { d: 40, y: 0 } })
    expect(kpss.toplamNet).toBe(80)
    expect(kpss.puan).toBe(80)

    const lgs = denemeHesaplaSinav('LGS', 'SAY', { lgs_tr: { d: 18, y: 0 }, lgs_mat: { d: 15, y: 3 } })
    expect(lgs.puanTuru).toBe('LGS · MSP')
    expect(lgs.puan).toBeGreaterThanOrEqual(100)

    const dgs = denemeHesaplaSinav('DGS', 'EA', { dgs_say: { d: 40, y: 0 }, dgs_soz: { d: 40, y: 0 } }, 40)
    expect(dgs.puanTuru).toBe('DGS EA')
    expect(dgs.puan).toBeCloseTo(100 + 40 * 3.3 + 40 * 3.3 + 40, 2)
  })
})
