import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import {
  Search, ListChecks, Home as HomeIcon,
  LogIn, LogOut, User, ChevronDown, Compass, Calculator,
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from './contexts/AuthContext'
import ThemeToggle from './components/ThemeToggle'
import Logo from './components/Logo'

export default function App() {
  const loc = useLocation()
  const nav = useNavigate()
  const { user, isAuthed, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  // Splash sayfası kendi tam ekran layout'u
  if (loc.pathname === '/') {
    return <Outlet />
  }

  const navItem = (to, label, Icon) => {
    const active = loc.pathname === to
    return (
      <Link
        to={to}
        className={`
          relative flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium
          transition-all duration-300
          ${active ? 'text-white' : 'text-slate-400 hover:text-slate-200'}
        `}
      >
        {active && (
          <motion.div
            layoutId="navactive"
            className="absolute inset-0 rounded-xl bg-gradient-to-r from-brand-500/20 to-accent-500/20 border border-accent-500/30"
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          />
        )}
        <Icon size={16} className="relative z-10" />
        <span className="relative z-10 hidden sm:inline">{label}</span>
      </Link>
    )
  }

  async function handleLogout() {
    await logout()
    setMenuOpen(false)
    nav('/home')
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-30 backdrop-blur-2xl bg-slate-950/40 border-b border-white/5">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-3 group shrink-0">
            <Logo size={40} rounded="rounded-none" />
            <div className="hidden sm:block">
              <h1 className="font-display font-bold text-lg text-white leading-none">UniSense</h1>
              <p className="text-[10px] text-slate-400 leading-none mt-1">Tercih Asistanı · 2025</p>
            </div>
          </Link>

          <nav className="flex items-center gap-1">
            {navItem('/home', 'Ana Sayfa', HomeIcon)}
            {navItem('/search', 'Sorgu', Search)}
            {navItem('/pusula', 'Pusula', Compass)}
            {navItem('/recommend', 'Tercih', ListChecks)}
            {navItem('/hesap', 'Hesap', Calculator)}
          </nav>

          {/* Sağ taraf — theme toggle profil avatarına yakın */}
          <div className="flex items-center gap-2 ml-auto">
            <ThemeToggle />

            {/* Auth menu */}
            {isAuthed ? (
            <div className="relative">
              <button
                onClick={() => setMenuOpen((o) => !o)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl glass glass-hover text-sm"
              >
                {user?.photoURL ? (
                  <img src={user.photoURL} alt="" className="w-7 h-7 rounded-full" />
                ) : (
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-brand-500 to-accent-600 flex items-center justify-center">
                    <User size={14} className="text-white" />
                  </div>
                )}
                <span className="hidden md:inline truncate max-w-[120px] text-slate-200">
                  {user?.displayName || user?.email?.split('@')[0]}
                </span>
                <ChevronDown size={14} className="text-slate-400" />
              </button>
              <AnimatePresence>
                {menuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute right-0 mt-2 w-56 card p-2"
                  >
                    <div className="px-3 py-2 border-b border-white/5 mb-2">
                      <div className="text-sm font-medium text-white truncate">
                        {user?.displayName || 'Kullanıcı'}
                      </div>
                      <div className="text-xs text-slate-400 truncate">{user?.email}</div>
                    </div>
                    <Link
                      to="/tercih"
                      onClick={() => setMenuOpen(false)}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-white/5 hover:text-white transition"
                    >
                      <ListChecks size={14} /> Tercih Listem
                    </Link>
                    <Link
                      to="/profile"
                      onClick={() => setMenuOpen(false)}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-white/5 hover:text-white transition"
                    >
                      <User size={14} /> Profilim
                    </Link>
                    <div className="my-1 border-t border-white/5" />
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-rose-400 hover:bg-rose-500/10 transition"
                    >
                      <LogOut size={14} /> Çıkış Yap
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            <Link
              to="/login"
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl glass glass-hover text-sm text-slate-200"
            >
              <LogIn size={14} />
              <span className="hidden sm:inline">Giriş</span>
            </Link>
          )}
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8 relative z-10">
        <Outlet />
      </main>

      <footer className="border-t border-white/5 py-4 text-center text-xs text-slate-500 relative z-10">
        <div className="max-w-6xl mx-auto px-4 flex flex-wrap items-center justify-center gap-x-3 gap-y-1">
          <span>UniSense</span>
          <span className="text-slate-700">•</span>
          <span className="text-slate-400">YÖK Atlas + Wikipedia</span>
          <span className="text-slate-700">•</span>
          <span>
            Resmi tercih için{' '}
            <a className="text-accent-400 hover:underline" href="https://yokatlas.yok.gov.tr">
              yokatlas.yok.gov.tr
            </a>
          </span>
          <span className="text-slate-700">•</span>
          <Link to="/privacy" className="text-slate-400 hover:text-accent-300 transition">
            KVKK / Gizlilik
          </Link>
        </div>
      </footer>
    </div>
  )
}
