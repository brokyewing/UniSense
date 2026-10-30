import { describe, it, expect } from 'vitest'
import { sonrakiTekrar, tekrarZamani, sm2, TEKRAR_ARALIK } from './tekrar'

describe('tekrar', () => {
  it('TEKRAR_ARALIK has 5 boxes', () => {
    expect(TEKRAR_ARALIK).toHaveLength(5)
  })

  it('sonrakiTekrar: first correct → box 2', () => {
    const r = sonrakiTekrar(1, true)
    expect(r.box).toBe(2)
    expect(r.nextReview).toBeTruthy()
  })

  it('sonrakiTekrar: wrong → box 1', () => {
    const r = sonrakiTekrar(3, false)
    expect(r.box).toBe(1)
  })

  it('sonrakiTekrar: max box 5', () => {
    const r = sonrakiTekrar(5, true)
    expect(r.box).toBe(5)
  })

  it('tekrarZamani: no nextReview → true', () => {
    expect(tekrarZamani({})).toBe(true)
    expect(tekrarZamani(null)).toBe(true)
  })

  it('sm2: quality < 3 resets', () => {
    const r = sm2({ ef: 2.5, rep: 3, interval: 10 }, 2)
    expect(r.rep).toBe(0)
    expect(r.interval).toBe(1)
  })

  it('sm2: quality >= 3 increments rep', () => {
    const r = sm2({ ef: 2.5, rep: 1, interval: 1 }, 4)
    expect(r.rep).toBe(2)
    expect(r.interval).toBe(6)
  })
})