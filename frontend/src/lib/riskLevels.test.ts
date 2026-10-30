import { describe, it, expect } from 'vitest'
import { yksLevel, dgsLevel, kpssLevel } from './riskLevels'

describe('riskLevels', () => {
  describe('yksLevel', () => {
    it('returns null when userRank or tabanRank missing', () => {
      expect(yksLevel(null, 5000)).toBeNull()
      expect(yksLevel(5000, null)).toBeNull()
      expect(yksLevel(0, 5000)).toBeNull()
    })
    it('returns safe when ratio >= 1.5', () => {
      expect(yksLevel(10000, 16000)).toBe('safe')
    })
    it('returns target when ratio >= 0.85', () => {
      expect(yksLevel(10000, 9000)).toBe('target')
    })
    it('returns reach when ratio < 0.85', () => {
      expect(yksLevel(10000, 5000)).toBe('reach')
    })
  })

  describe('dgsLevel', () => {
    it('returns bos when taban is null', () => {
      expect(dgsLevel(250, null)).toBe('bos')
    })
    it('returns null when puan is null', () => {
      expect(dgsLevel(null, 250)).toBeNull()
    })
    it('returns safe when diff >= 10', () => {
      expect(dgsLevel(260, 250)).toBe('safe')
    })
    it('returns target when diff >= 0', () => {
      expect(dgsLevel(250, 250)).toBe('target')
    })
    it('returns reach when diff < 0', () => {
      expect(dgsLevel(240, 250)).toBe('reach')
    })
  })

  describe('kpssLevel', () => {
    it('returns bilinmez when taban is null', () => {
      expect(kpssLevel(80, null)).toBe('bilinmez')
    })
    it('returns null when puan is null', () => {
      expect(kpssLevel(null, 75)).toBeNull()
    })
    it('returns safe when diff >= 3', () => {
      expect(kpssLevel(80, 75)).toBe('safe')
    })
    it('returns target when diff >= -1', () => {
      expect(kpssLevel(75, 75)).toBe('target')
    })
    it('returns reach when diff < -1', () => {
      expect(kpssLevel(70, 75)).toBe('reach')
    })
  })
})