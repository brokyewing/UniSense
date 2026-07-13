import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import {
  Search, ListChecks, Home as HomeIcon,
  LogIn, LogOut, User, ChevronDown, Compass, Calculator, BookOpen, CalendarDays,
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from './contexts/AuthContext'
import { apiFetch } from './lib/api'
import ThemeToggle from './components/ThemeToggle'
import Logo from './components/Logo'
import Seo from './components/Seo'

// Rota → SEO meta (rota-bazlı benzersiz title + self-canonical). Kişisel/geçici
// sayfalar noindex (robots.txt de bunları engelliyor — çift güvence).
const ROUTE_SEO = {
  '/': { title: 'UniSense — 2026 Tercih Robotu | YKS, DGS, KPSS Taban Puanlar', description: 'YKS, DGS ve KPSS tercihine yapay zekâ destekli hazırlan: güncel taban puanlar, başarı sıralamaları, net hesaplama ve kişisel tercih önerileri — ücretsiz.' },
  '/anasayfa': { title: 'UniSense — 2026 Tercih Robotu | YKS, DGS, KPSS', description: 'Güncel taban puanlar, sıralamalar ve yapay zekâ destekli tercih önerileriyle YKS, DGS ve KPSS tercihine hazırlan.' },
  '/arama': { title: 'Tercih Sorgu — Taban Puan & Sıralama Sorgula | UniSense', description: 'Doğal dilde sor: bölüm taban puanları, başarı sıralamaları, kontenjanlar ve KPSS kadroları — kaynak gösterimli yapay zekâ sohbeti.' },
  '/oneriler': { title: 'Tercih Önerileri — YKS · DGS · KPSS | UniSense', description: 'Puanına uygun güvenli, hedef ve üst seviye tercihleri yapay zekâyla al. YKS, DGS ve KPSS için ayrı öneriler.' },
  '/hesap': { title: 'Puan Hesaplama — YKS · DGS · KPSS Net Hesap | UniSense', description: 'Netlerini gir, yaklaşık YKS, DGS veya KPSS yerleştirme puanını anında hesapla; bu puanla hangi programları yazabileceğini gör.' },
  '/pusula': { title: 'İlgi Pusulası — Sana Uygun Bölümü Bul | UniSense', description: 'Ne okuyacağına karar veremiyor musun? İlgi alanlarından yapay zekâ ile sana uygun üniversite bölümlerini keşfet.' },
  '/karsilastir': { title: 'Program Karşılaştırma — Taban, Trend, Kadro | UniSense', description: 'Üniversite programlarını yan yana karşılaştır: taban puan, 3 yıllık sıralama trendi, akademik kadro, ücret ve akreditasyon.' },
  '/bolum': { title: 'Bölüm Rehberi — Üniversite Bölümleri Tanıtımı | UniSense', description: 'Üniversite bölümleri ne iş yapar, hangi dersleri okur, mezunları nerede çalışır? Tanıtımlar + güncel taban puanları.' },
  '/takvim': { title: '2026 Sınav Takvimi — YKS, LGS, DGS, KPSS, ALES, TUS | UniSense', description: '2026 YKS, LGS, DGS, KPSS, ALES, TUS, DUS ve AGS sınav, sonuç ve tercih tarihleri — kaç gün kaldığıyla tek sayfada.' },
  '/gizlilik': { title: 'Gizlilik ve KVKK | UniSense', description: 'UniSense gizlilik politikası ve KVKK aydınlatma metni.' },
  '/tercih': { title: 'Tercih Listem | UniSense', noindex: true },
  '/profil': { title: 'Sınav Profilim | UniSense', noindex: true },
  '/giris': { title: 'Giriş | UniSense', noindex: true },
}

export default function App() {
  const loc = useLocation()
  const nav = useNavigate()
  const { user, isAuthed, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  // Backend'i erken uyandır: kullanıcı siteye girer girmez /health'i pingle.
  // Render free tier boşta uyur; Bölümler/Takvim gibi ilk API çağrısı geldiğinde
  // soğuk başlangıç beklememesi için sunucu kullanıcı gezerken ısınır.
  // Fire-and-forget — hatayı yut, UI'yi hiç etkilemesin.
  useEffect(() => {
    apiFetch('/api/v1/health').catch(() => {})
  }, [])

  // /bolum* sayfaları kendi <Seo>'sunu basar (dinamik başlık) — App burada basmaz,
  // yoksa parent effect child'ı ezip yanlış başlık kalır.
  const ownsSeo = loc.pathname.startsWith('/bolum')
  const seo = ROUTE_SEO[loc.pathname] || ROUTE_SEO['/anasayfa']
  const seoEl = ownsSeo ? null : (
    <Seo
      title={seo.title}
      description={seo.description}
      path={loc.pathname === '/' ? '/' : loc.pathname}
      noindex={seo.noindex}
    />
  )

  // Splash sayfası kendi tam ekran layout'u (SEO head yine de basılır)
  if (loc.pathname === '/') {
    return <>{seoEl}<Outlet /></>
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
    nav('/anasayfa')
  }

  return (
    <div className="min-h-screen flex flex-col">
      {seoEl}
      <header className="sticky top-0 z-30 backdrop-blur-2xl bg-slate-950/40 border-b border-white/5">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-3 group shrink-0">
            <Logo size={40} rounded="rounded-none" />
            <div className="hidden sm:block">
              <h1 className="font-display font-bold text-lg text-white leading-none">UniSense</h1>
              <p className="text-[10px] text-slate-400 leading-none mt-1">Tercih Asistanı · 2026</p>
            </div>
          </Link>

          <nav className="flex items-center gap-1">
            {navItem('/anasayfa', 'Ana Sayfa', HomeIcon)}
            {navItem('/arama', 'Sorgu', Search)}
            {navItem('/bolum', 'Bölümler', BookOpen)}
            {navItem('/takvim', 'Takvim', CalendarDays)}
            {navItem('/pusula', 'Pusula', Compass)}
            {navItem('/oneriler', 'Tercih', ListChecks)}
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
                      to="/profil"
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
              to="/giris"
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
          <Link to="/gizlilik" className="text-slate-400 hover:text-accent-300 transition">
            KVKK / Gizlilik
          </Link>
        </div>
      </footer>
    </div>
  )
}
