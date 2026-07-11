import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Mail, Lock, User, Loader2, ArrowRight } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import BackgroundScene from '../components/three/BackgroundScene'
import Logo from '../components/Logo'

export default function Login() {
  const nav = useNavigate()
  const { loginWithEmail, loginWithGoogle, register } = useAuth()
  const [mode, setMode] = useState('login') // login | register
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function onEmail(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (mode === 'login') {
        await loginWithEmail(email, password)
      } else {
        await register(email, password, name)
      }
      nav('/home')
    } catch (e) {
      setError(parseError(e))
    } finally {
      setLoading(false)
    }
  }

  async function onGoogle() {
    setLoading(true)
    setError('')
    try {
      await loginWithGoogle()
      nav('/home')
    } catch (e) {
      setError(parseError(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <BackgroundScene />

      <div className="max-w-md mx-auto py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card space-y-5"
        >
          <div className="text-center">
            <Logo size={64} rounded="rounded-2xl" className="mx-auto mb-3" />
            <h1 className="text-3xl font-display font-bold text-white mb-1">
              {mode === 'login' ? 'Hoş Geldin' : 'Hesap Oluştur'}
            </h1>
            <p className="text-sm text-slate-400">
              {mode === 'login'
                ? 'Tercih listeni kaydetmek için giriş yap'
                : 'UniSense\'e katıl, tercihlerini sakla'}
            </p>
          </div>

          {/* Google butonu */}
          <button
            onClick={onGoogle}
            disabled={loading}
            className="google-btn w-full py-3 px-4 rounded-xl font-medium transition flex items-center justify-center gap-3 disabled:opacity-50"
          >
            <svg width="18" height="18" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Google ile devam et
          </button>

          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-xs text-slate-500">veya</span>
            <div className="flex-1 h-px bg-white/10" />
          </div>

          {/* Email form */}
          <form onSubmit={onEmail} className="space-y-3">
            {mode === 'register' && (
              <div className="relative">
                <User size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Adın"
                  className="input-glass pl-11"
                  required
                />
              </div>
            )}
            <div className="relative">
              <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="E-posta"
                className="input-glass pl-11"
                required
              />
            </div>
            <div className="relative">
              <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Şifre (min 6)"
                minLength={6}
                className="input-glass pl-11"
                required
              />
            </div>

            {error && (
              <div className="text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-2">
                ⚠️ {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full inline-flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <>
                  {mode === 'login' ? 'Giriş Yap' : 'Hesap Oluştur'}
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          <div className="text-center text-sm text-slate-400">
            {mode === 'login' ? (
              <>Hesabın yok mu?{' '}
                <button
                  onClick={() => setMode('register')}
                  className="text-accent-400 hover:underline"
                >
                  Kayıt ol
                </button>
              </>
            ) : (
              <>Zaten hesabın var mı?{' '}
                <button
                  onClick={() => setMode('login')}
                  className="text-accent-400 hover:underline"
                >
                  Giriş yap
                </button>
              </>
            )}
          </div>

          <Link
            to="/home"
            className="block text-center text-xs text-slate-500 hover:text-slate-300 transition"
          >
            Üye olmadan keşfet →
          </Link>
        </motion.div>
      </div>
    </>
  )
}

function parseError(e) {
  const msg = e?.message || String(e)
  if (msg.includes('user-not-found')) return 'Kullanıcı bulunamadı'
  if (msg.includes('wrong-password')) return 'Şifre yanlış'
  if (msg.includes('email-already-in-use')) return 'Bu e-posta zaten kayıtlı'
  if (msg.includes('weak-password')) return 'Şifre çok zayıf (min 6)'
  if (msg.includes('Firebase yok')) return 'Firebase yapılandırılmamış (.env.local kontrol et)'
  if (msg.includes('popup-closed')) return 'Google girişi iptal edildi'
  return msg.slice(0, 200)
}
