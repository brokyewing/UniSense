/**
 * Frontend constants — tek yerde, tek kaynak.
 * Backend'deki constants.py / riskLevels.py karşılığı.
 */

// Tercih listesi limitleri (backend rules ile uyumlu olmalı)
export const TERCIH_LIMITS = {
  YKS: 24,
  DGS: 30,
  KPSS: 30,
  TUS: 30,
  DUS: 30,
  LGS: 25,
} as const

// Geriye uyumluluk için ayrı export'lar
export const MAX_DGS_TERCIH = TERCIH_LIMITS.DGS
export const MAX_KPSS_TERCIH = TERCIH_LIMITS.KPSS
export const MAX_TUS_TERCIH = TERCIH_LIMITS.TUS
export const MAX_LGS_TERCIH = TERCIH_LIMITS.LGS

// Sınav tipleri
export const EXAM_TYPES = ['YKS', 'DGS', 'KPSS', 'TUS', 'DUS', 'LGS'] as const

// Puan türleri
export const SCORE_TYPES: Record<string, string[]> = {
  YKS: ['SAY', 'EA', 'SÖZ', 'DİL', 'TYT'],
  DGS: ['SAY', 'EA', 'SÖZ'],
  KPSS: [], // puan türü yok, sadece GY-GK puanı
}

// Firebase subcollection isimleri
export const FIRESTORE_COLLECTIONS = {
  TERCIH: 'tercih',
  DGS_TERCIH: 'dgs_tercih',
  KPSS_TERCIH: 'kpss_tercih',
  TUS_TERCIH: 'tus_tercih',
  DUS_TERCIH: 'dus_tercih',
  LGS_TERCIH: 'lgs_tercih',
  KONU_ILERLEME: 'konu_ilerleme',
  DENEMELER: 'denemeler',
  SORU_KAYIT: 'soru_kayit',
  YANLISLAR: 'yanlislar',
  NOTLAR: 'notlar',
  KARTLAR: 'kartlar',
  PLAN_CONFIG: 'plan_config',
  PLAN_GOREV: 'plan_gorev',
  ISTATISTIK: 'istatistik',
  AKTIVITE: 'aktivite',
  SESSIONS: 'sessions',
  QUERIES: 'queries',
  PUSH_TOKENS: 'pushTokens',
  SIRALAMA: 'siralama',
} as const

// Risk seviyesi eşikleri
export const RISK_THRESHOLDS = {
  SAFE: 15,
  TARGET: 0,
  REACH: -15,
} as const

// API timeout
export const API_TIMEOUT_MS = 30000

// LocalStorage key'leri
export const STORAGE_KEYS = {
  KONU_PREFIX: 'unisense_konu_v1_',
  SORU_PREFIX: 'unisense_soru_',
  STREAK: 'unisense_streak',
  PUSULA_DEPTS: 'pusula_depts',
} as const

// Firestore belge ID maksimum uzunluğu
export const FIRESTORE_MAX_ID_LENGTH = 200

// Session limiti
export const MAX_SESSIONS_PER_USER = 5

// Varsayılan sayfalama limitleri
export const DEFAULT_LIMITS = {
  PROGRAM_LOOKUP: 100,
  RECOMMEND: 50,
  SEARCH: 12,
} as const

// Preset avatars (DiceBear API, ücretsiz)
export const PRESET_AVATARS = [
  { id: 'av1', url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=UniSense01&backgroundColor=b6e3f4' },
  { id: 'av2', url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=UniSense02&backgroundColor=ffd5dc' },
  { id: 'av3', url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=UniSense03&backgroundColor=c0aede' },
  { id: 'av4', url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=UniSense04&backgroundColor=d1d4f9' },
  { id: 'av5', url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=UniSense05&backgroundColor=b6e3f4' },
  { id: 'av6', url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=UniSense06&backgroundColor=ffdfbf' },
  { id: 'av7', url: 'https://api.dicebear.com/7.x/lorelei/svg?seed=UniSense07&backgroundColor=ffd5dc' },
  { id: 'av8', url: 'https://api.dicebear.com/7.x/lorelei/svg?seed=UniSense08&backgroundColor=b6e3f4' },
  { id: 'av9', url: 'https://api.dicebear.com/7.x/notionists/svg?seed=UniSense09&backgroundColor=c0aede' },
  { id: 'av10', url: 'https://api.dicebear.com/7.x/notionists/svg?seed=UniSense10&backgroundColor=d1d4f9' },
  { id: 'av11', url: 'https://api.dicebear.com/7.x/bottts/svg?seed=UniSense11&backgroundColor=b6e3f4' },
  { id: 'av12', url: 'https://api.dicebear.com/7.x/bottts/svg?seed=UniSense12&backgroundColor=ffd5dc' },
] as const