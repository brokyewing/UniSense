import { describe, it, expect } from 'vitest'
import { TERCIH_LIMITS, MAX_DGS_TERCIH, MAX_KPSS_TERCIH, MAX_TUS_TERCIH, MAX_LGS_TERCIH, EXAM_TYPES, SCORE_TYPES, FIRESTORE_COLLECTIONS, RISK_THRESHOLDS, API_TIMEOUT_MS, STORAGE_KEYS, FIRESTORE_MAX_ID_LENGTH, MAX_SESSIONS_PER_USER, DEFAULT_LIMITS, PRESET_AVATARS } from './constants'

describe('constants', () => {
  it('should have correct tercih limits', () => {
    expect(TERCIH_LIMITS.YKS).toBe(24)
    expect(TERCIH_LIMITS.DGS).toBe(30)
    expect(TERCIH_LIMITS.KPSS).toBe(30)
    expect(TERCIH_LIMITS.TUS).toBe(30)
    expect(TERCIH_LIMITS.DUS).toBe(30)
    expect(TERCIH_LIMITS.LGS).toBe(25)
  })

  it('should have backward-compatible MAX_* exports', () => {
    expect(MAX_DGS_TERCIH).toBe(TERCIH_LIMITS.DGS)
    expect(MAX_KPSS_TERCIH).toBe(TERCIH_LIMITS.KPSS)
    expect(MAX_TUS_TERCIH).toBe(TERCIH_LIMITS.TUS)
    expect(MAX_LGS_TERCIH).toBe(TERCIH_LIMITS.LGS)
  })

  it('should have exam types', () => {
    expect(EXAM_TYPES).toContain('YKS')
    expect(EXAM_TYPES).toContain('DGS')
    expect(EXAM_TYPES).toContain('KPSS')
    expect(EXAM_TYPES).toContain('LGS')
  })

  it('should have score types for YKS and DGS', () => {
    expect(SCORE_TYPES.YKS).toContain('SAY')
    expect(SCORE_TYPES.YKS).toContain('EA')
    expect(SCORE_TYPES.DGS).toContain('SAY')
    expect(SCORE_TYPES.DGS).toContain('EA')
  })

  it('should have firestore collections', () => {
    expect(FIRESTORE_COLLECTIONS.TERCIH).toBe('tercih')
    expect(FIRESTORE_COLLECTIONS.NOTLAR).toBe('notlar')
    expect(FIRESTORE_COLLECTIONS.DENEMELER).toBe('denemeler')
  })

  it('should have risk thresholds', () => {
    expect(RISK_THRESHOLDS.SAFE).toBe(15)
    expect(RISK_THRESHOLDS.TARGET).toBe(0)
    expect(RISK_THRESHOLDS.REACH).toBe(-15)
  })

  it('should have API timeout', () => {
    expect(API_TIMEOUT_MS).toBe(30000)
  })

  it('should have storage keys', () => {
    expect(STORAGE_KEYS.KONU_PREFIX).toBe('unisense_konu_v1_')
    expect(STORAGE_KEYS.SORU_PREFIX).toBe('unisense_soru_')
  })

  it('should have firestore max ID length', () => {
    expect(FIRESTORE_MAX_ID_LENGTH).toBe(200)
  })

  it('should have max sessions per user', () => {
    expect(MAX_SESSIONS_PER_USER).toBe(5)
  })

  it('should have default limits', () => {
    expect(DEFAULT_LIMITS.PROGRAM_LOOKUP).toBe(100)
    expect(DEFAULT_LIMITS.RECOMMEND).toBe(50)
    expect(DEFAULT_LIMITS.SEARCH).toBe(12)
  })

  it('should have preset avatars', () => {
    expect(PRESET_AVATARS).toHaveLength(12)
    expect(PRESET_AVATARS[0]).toHaveProperty('id')
    expect(PRESET_AVATARS[0]).toHaveProperty('url')
  })
})