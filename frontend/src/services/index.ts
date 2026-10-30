/**
 * Services Barrel Export — tek import noktası.
 * import { api, useTercihList, watchTercihList, ... } from '@/services'
 */

// Constants
export { TERCIH_LIMITS, MAX_DGS_TERCIH, MAX_KPSS_TERCIH, MAX_TUS_TERCIH, MAX_LGS_TERCIH, EXAM_TYPES, SCORE_TYPES, FIRESTORE_COLLECTIONS, RISK_THRESHOLDS, API_TIMEOUT_MS, STORAGE_KEYS, FIRESTORE_MAX_ID_LENGTH, MAX_SESSIONS_PER_USER, DEFAULT_LIMITS, PRESET_AVATARS } from './constants'

// Core Firestore
export { db, watchSubcollection, getSubcollectionDoc, getSubcollectionAll, addSubcollectionDoc, setSubcollectionDoc, updateSubcollectionDoc, deleteSubcollectionDoc, batchWrite } from './firestore-core'

// Auth
export { auth, googleProvider, loginWithGoogle, loginWithEmail, registerWithEmail, logout, watchAuth, updateUserBasicInfo, changePassword, getAuthProvider } from './auth'

// Firestore Domain Services
export * from './firestore-user'
export * from './firestore-study'
export * from './firestore-prefs'
export * from './firestore-plan'
export * from './firestore-push'

// API
export { API_BASE, ApiError, apiFetch, api } from './api'

// Hooks
export * from './hooks'