import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import {
  watchAuth,
  loginWithGoogle as fbLoginGoogle,
  loginWithEmail as fbLoginEmail,
  registerWithEmail as fbRegister,
  logout as fbLogout,
} from '@/services/auth'
import type { User } from 'firebase/auth'

interface AuthContextValue {
  user: User | null
  loading: boolean
  isAuthed: boolean
  loginWithGoogle: (examTrack?: string) => Promise<User>
  loginWithEmail: (email: string, password: string) => Promise<User>
  register: (email: string, password: string, displayName?: string, examTrack?: string) => Promise<User>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsub = watchAuth((u) => {
      setUser(u)
      setLoading(false)
    })
    if (!unsub || typeof unsub !== 'function') {
      setLoading(false)
    }
    return unsub
  }, [])

  const value: AuthContextValue = {
    user,
    loading,
    isAuthed: !!user,
    loginWithGoogle: fbLoginGoogle,
    loginWithEmail: fbLoginEmail,
    register: fbRegister,
    logout: fbLogout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}