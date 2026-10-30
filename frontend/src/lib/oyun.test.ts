import { describe, it, expect } from 'vitest'
import { hesaplaXP, seviyeBilgi, kazanilanRozetler, guestStats } from './oyun'

describe('oyun', () => {
  it('hesaplaXP returns 0 for empty', () => {
    expect(hesaplaXP({})).toBe(0)
  })

  it('hesaplaXP sums contributions', () => {
    const xp = hesaplaXP({ konuDone: 10, denemeSayisi: 2 })
    expect(xp).toBe(10 * 5 + 2 * 20)
  })

  it('seviyeBilgi level 1 for low xp', () => {
    const r = seviyeBilgi(50)
    expect(r.seviye).toBe(1)
    expect(r.mevcut).toBe(50)
  })

  it('kazanilanRozetler returns array', () => {
    const r = kazanilanRozetler({ konuDone: 1 })
    expect(Array.isArray(r)).toBe(true)
    expect(r.length).toBeGreaterThan(0)
  })
})