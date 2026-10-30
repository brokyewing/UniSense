import { describe, it, expect } from 'vitest'
import { konuAnahtar, konuBloklari, eksikKonular, rastgeleSec } from './konu'

describe('konu', () => {
  it('konuAnahtar builds key', () => {
    expect(konuAnahtar('TYT', 'Matematik', 'Limit')).toBe('TYT|Matematik|Limit')
    expect(konuAnahtar(null, 'Mat', 'Konu')).toBe('|Mat|Konu')
  })

  it('konuBloklari handles gruplu data', () => {
    const data = { gruplar: { TYT: { Matematik: ['Limit', 'Türev'] } } }
    const bl = konuBloklari(data)
    expect(bl).toHaveLength(1)
    expect(bl[0].grup).toBe('TYT')
    expect(bl[0].ders).toBe('Matematik')
    expect(bl[0].konular).toEqual(['Limit', 'Türev'])
  })

  it('konuBloklari handles düz data', () => {
    const data = { dersler: { Matematik: ['Limit'] } }
    const bl = konuBloklari(data)
    expect(bl).toHaveLength(1)
    expect(bl[0].grup).toBeNull()
  })

  it('konuBloklari returns [] for null', () => {
    expect(konuBloklari(null)).toEqual([])
  })

  it('eksikKonular counts correctly', () => {
    const data = { dersler: { Mat: ['A', 'B', 'C'] } }
    const checked = { '|Mat|A': true }
    const r = eksikKonular(data, checked)
    expect(r.toplam).toBe(3)
    expect(r.yapilan).toBe(1)
    expect(r.eksik).toHaveLength(2)
    expect(r.hepsiBitti).toBe(false)
  })

  it('eksikKonular hepsiBitti when all done', () => {
    const data = { dersler: { Mat: ['A'] } }
    const r = eksikKonular(data, { '|Mat|A': true })
    expect(r.hepsiBitti).toBe(true)
  })

  it('rastgeleSec returns n items', () => {
    const r = rastgeleSec([1, 2, 3, 4, 5], 3)
    expect(r).toHaveLength(3)
    expect(new Set(r).size).toBe(3)
  })
})