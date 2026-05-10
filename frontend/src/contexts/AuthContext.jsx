import { createContext, useContext, useEffect, useState } from 'react'
import {
  watchAuth,
  loginWithGoogle as fbLoginGoogle,
  loginWithEmail as fbLoginEmail,
  registerWithEmail as fbRegister,
  logout as fbLogout,
} from '../firebase'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsub = watchAuth((u) => {
      setUser(u)
      setLoading(false)
    })
    // Firebase yoksa watchAuth no-op döner, sadece loading'i kapat
    if (!unsub || typeof unsub !== 'function') {
      setLoading(false)
    }
    return unsub
  }, [])

  const value = {
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

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
