// Shared type definitions for UniSense frontend

export interface Program {
  department_code: string
  department_name: string
  university_code?: string
  university_name: string
  city: string
  score_type?: string
  last_year_base_rank?: number | null
  last_year_base_score?: number | null
  quota?: number | null
  safety_level?: 'safe' | 'target' | 'reach' | null
  note?: string
  id?: string
}

export interface UserProfile {
  examTrack?: string
  scoreType?: string
  score?: number | null
  rank?: number | null
  preferredCities?: string[]
  preferredUniType?: string
  preferredInterests?: string[]
  diploma?: number | null
  diploma100?: number | null
  gpa4?: number | null
  obp?: number | null
  aobp?: number | null
  lastTab?: string
  calculator?: Record<string, unknown>
  kpss?: { score: number; duzey?: string; updatedAt?: number }
  dgs?: { score: number; type?: string; updatedAt?: number }
  tus?: { score: number; updatedAt?: number }
  dus?: { score: number; updatedAt?: number }
  lgs?: { yuzdelik: number; updatedAt?: number }
  ags?: { net: number; updatedAt?: number }
  emailReminders?: boolean
  lgs?: { yuzdelik: number; updatedAt?: number }
}

export interface AuthUser {
  uid: string
  email: string | null
  displayName: string | null
  photoURL: string | null
}

export interface KonuData {
  gruplar?: Record<string, Record<string, string[]>>
  dersler?: Record<string, string[]>
  ad?: string
  not?: string
}

export interface Deneme {
  id: string
  sinav: string
  tarih: string
  ad?: string
  type?: string
  dersNet?: Record<string, number>
  toplamNet?: number
  puan?: number
  sira?: number
}

export interface SoruKayit {
  id: string
  sinav: string
  ders: string
  konu: string
  cozulen: number
  dogru: number
  tarih: string
}

export interface PlanGorev {
  id: string
  title: string
  tarih: string
  status: 'done' | 'planned'
  source: 'manual' | 'auto' | 'ai' | 'tekrar'
  tur?: string
  konu?: string
  ders?: string
  hafta?: string
  sayildi?: boolean
  tekrarNo?: number
}

export interface PlanConfig {
  track?: string
  hedefSaat?: number
  haftaIciBlok?: number
  haftaSonuBlok?: number
  kuruldu?: boolean
}

export interface Istatistik {
  konuDone: number
  denemeSayisi: number
  soruCozulen: number
  yanlisSayisi: number
  streakLongest: number
  sureDk: number
  sureHafta: Record<string, number>
  dersSure: Record<string, number>
  kullanimDk: number
  dogruCevap: number
  planGorev: number
}

export interface Session {
  id: string
  title: string
  messageCount: number
  createdAt: any
  updatedAt: any
}

export interface SessionMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: any
}

export interface Toast {
  id: number
  message: string
  type: string
}

export type ExamType = 'YKS' | 'DGS' | 'KPSS' | 'TUS' | 'DUS' | 'LGS'
export type ScoreType = 'SAY' | 'EA' | 'SÖZ' | 'DİL' | 'TYT'
export type SafetyLevel = 'safe' | 'target' | 'reach'