import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import {
  Search, ListChecks,
  LogIn, LogOut, User, ChevronDown, Compass, Calculator, BookOpen, CalendarDays,
  GraduationCap, Trophy, Briefcase,
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from './contexts/AuthContext'
import { apiFetch } from './lib/api'
import { initAnalytics, identify, capturePageview } from './lib/analytics'
import { useAppTime } from './lib/usage'
import ThemeToggle from './components/ThemeToggle'
import Logo from './components/Logo'
import Seo from './components/Seo'
import { TERCIH_YILI } from './lib/donem'

// Rota → SEO meta (50-60 krk title + 125-158 krk description + self-canonical).
// Kişisel sayfalar noindex (prerender.mjs ile birebir eşleşir).
const ROUTE_SEO = {
  '/': { title: `YKS, LGS, DGS, KPSS Tercih Robotu ${TERCIH_YILI} & Puanlar | UniSense`, description: 'Üniversite ve lise taban puanları, başarı sıralamaları, TYT-AYT net ve OBP hesaplama, KPSS, DGS, TUS tercih robotu — YÖK Atlas/ÖSYM verisiyle ücretsiz.' },
  '/anasayfa': { title: `Üniversite Taban Puanları ${TERCIH_YILI} & Tercih Robotu | UniSense`, description: `${TERCIH_YILI} YKS, LGS, DGS, KPSS ve TUS tercih robotu: 4 ve 2 yıllık üniversite taban puanları, başarı sıralamaları, net hesaplama ve AI tercih önerileri.` },
  '/arama': { title: 'YÖK Atlas Taban Puan & Sıralama Sorgula (AI) | UniSense', description: 'Üniversite taban puanları, başarı sıralamaları, kontenjanlar ve KPSS nitelik kodlarını doğal dilde sor; ÖSYM kodlu ve kaynaklı yanıtı anında al.' },
  '/oneriler': { title: `YKS, DGS ve KPSS Tercih Robotu ${TERCIH_YILI} — Sıralama | UniSense`, description: 'Sıralamana ve puanına göre güvenli, hedef ve riskli üniversite bölümlerini, DGS geçiş programlarını ve KPSS atama kadrolarını ücretsiz listele.' },
  '/hesap': { title: 'TYT AYT Puan, Net, OBP ve Sıralama Hesaplama | UniSense', description: 'TYT, AYT, YDT net ve OBP (diploma notu) hesaplama ile YKS başarı sıralamanı gör; DGS, KPSS, LGS, ALES ve AGS puanlarını tek ekranda ücretsiz hesapla.' },
  '/pusula': { title: 'Meslek Seçimi Testi & Hangi Bölümü Seçmeliyim | UniSense', description: 'Ne okuyacağına karar veremiyor musun? İlgi alanlarına göre yapay zekâ destekli üniversite bölümü ve meslek seçimi testiyle sana en uygun alanları bul.' },
  '/karsilastir': { title: 'Üniversite ve Bölüm Karşılaştırma — Taban Puan | UniSense', description: '2 ila 5 üniversite programını yan yana karşılaştır: taban puanı, 3 yıllık başarı sıralaması trendi, kontenjan, burs/ücret, akreditasyon ve istihdam.' },
  '/konular': { title: 'TYT AYT Konu Dağılımı & YKS Konu Takip Çizelgesi | UniSense', description: `${TERCIH_YILI} TYT, AYT, KPSS, DGS ve LGS güncel müfredat konu listesi. Ders ders konuları işaretle, eksiklerini gör ve online konu takip çizelgesiyle hazırlan.` },
  '/deneme': { title: 'YKS Deneme Takip, TYT AYT Net Analizi ve Grafik | UniSense', description: 'TYT, AYT, KPSS, DGS ve LGS deneme netlerini ve çözdüğün soruları kaydet; net gelişim grafiği ve AI Koç analiziyle eksik konularını ücretsiz takip et.' },
  '/ozetler': { title: 'TYT AYT Matematik, Fizik, Kimya Formül Özetleri | UniSense', description: 'YKS (TYT-AYT), LGS ve KPSS matematik, geometri, fizik ve kimya formülleri ile pratik konu özetleri tek yerde. Aranabilir ve ücretsiz ders notları.' },
  '/planim': { title: 'Planım — AI Çalışma Planlayıcısı | UniSense', description: 'Haftalık çalışma planını kur, günlük görevlerini takip et.', noindex: true },
  '/notlar': { title: 'Notlarım | UniSense', description: 'Kişisel çalışma notların ve yapılacaklar listen.', noindex: true },
  '/pano': { title: 'Çalışma Panom | UniSense', description: 'Pomodoro sayacı, çalışma istatistiklerin ve rozetlerin.', noindex: true },
  '/bolum': { title: 'Üniversite Bölümleri ve Taban Puanları Rehberi | UniSense', description: '600+ lisans ve önlisans üniversite bölümü ne iş yapar, hangi dersleri okur, mezunları nerede çalışır? Bölüm tanıtımları ve güncel taban puanları.' },
  '/takvim': { title: `${TERCIH_YILI} ÖSYM Sınav Takvimi & YKS Geri Sayım Sayacı | UniSense`, description: `${TERCIH_YILI} YKS, LGS, DGS, KPSS, ALES, TUS, DUS ve AGS başvuru, sınav, sonuç ve tercih tarihleri. Sınava kaç gün kaldığını canlı geri sayım sayacıyla takip et.` },
  '/lgs': { title: `LGS Tercih Robotu ${TERCIH_YILI} — Lise Taban Puanları & Yüzdelik`, description: 'LGS yüzdelik dilimini gir; 81 il ve ilçedeki Fen, Anadolu, Sosyal Bilimler ve İmam Hatip liselerinin taban puanlarını ve yüzdelik dilimlerini listele.' },
  '/tus': { title: `TUS ve DUS Tercih Robotu ${TERCIH_YILI} — Uzmanlık Taban Puanları`, description: 'TUS ve DUS puanına göre tıp ve diş hekimliği uzmanlık dallarının ÖSYM en küçük taban puanlarını, kontenjanlarını ve kurumlarını güvenli/hedef olarak gör.' },
  '/kariyer': { title: 'Kamu Personel Alımı, Kariyer Kapısı & İş İlanları | UniSense', description: 'Günlük güncellenen Resmî Gazete kamu personel alımı, Kariyer Kapısı, BİK, savunma sanayii, KPSS şartlı/şartsız memur ve özel sektör iş/staj ilanları.' },
  '/gizlilik': { title: 'Gizlilik Politikası ve KVKK Aydınlatma Metni | UniSense', description: 'UniSense kullanıcı verilerinin korunması, çerez/yerel depolama kullanımı, hesap silme hakları ve 6698 sayılı KVKK kapsamındaki aydınlatma metni.' },
  '/tercih': { title: 'Tercih Listem | UniSense', description: 'Kişisel tercih listen.', noindex: true },
  '/profil': { title: 'Sınav Profilim | UniSense', description: 'Kişisel sınav profili ve hedeflerin.', noindex: true },
  '/siralama': { title: 'Sıralama | UniSense', description: 'Çalışma sıralaması.', noindex: true },
  '/giris': { title: 'Giriş | UniSense', description: 'UniSense hesabına giriş yap.', noindex: true },
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
    initAnalytics() // VITE_POSTHOG_KEY yoksa no-op
  }, [])

  // Analitik: rota değişiminde pageview + girişte kullanıcıyı tanımla (dormant değilse)
  useEffect(() => { capturePageview(loc.pathname) }, [loc.pathname])
  useEffect(() => { if (user?.uid) identify(user.uid) }, [user])

  // Uygulamada geçirilen aktif süre → XP/seviye
  useAppTime(user)

  // /bolum* sayfaları kendi <Seo>'sunu basar (dinamik başlık) — App burada basmaz,
  // yoksa parent effect child'ı ezip yanlış başlık kalır.
  const ownsSeo = loc.pathname.startsWith('/bolum') || loc.pathname.startsWith('/ozet/')
  const seo = (ROUTE_SEO as any)[loc.pathname] || ROUTE_SEO['/anasayfa']
  const routePath = loc.pathname === '/' ? '/' : loc.pathname
  const routeJsonLd = seo.noindex || routePath === '/gizlilik'
    ? null
    : (routePath === '/' || routePath === '/anasayfa')
      ? {
          '@context': 'https://schema.org',
          '@graph': [
            {
              '@type': 'Organization',
              name: 'UniSense',
              url: 'https://www.unisense.com.tr',
              logo: 'https://www.unisense.com.tr/logo.png',
              sameAs: ['https://github.com/brokyewing/UniSense'],
              contactPoint: [{
                '@type': 'ContactPoint',
                contactType: 'customer support',
                url: 'https://www.unisense.com.tr/gizlilik',
                availableLanguage: ['Turkish'],
              }],
            },
            {
              '@type': 'WebSite',
              name: 'UniSense',
              url: 'https://www.unisense.com.tr',
              inLanguage: 'tr-TR',
              potentialAction: {
                '@type': 'SearchAction',
                target: 'https://www.unisense.com.tr/arama?q={search_term_string}',
                'query-input': 'required name=search_term_string',
              },
            },
          ],
        }
      : {
          '@context': 'https://schema.org',
          '@graph': [
            {
              '@type': 'WebApplication',
              name: seo.title,
              description: seo.description,
              url: `https://www.unisense.com.tr${routePath}`,
              inLanguage: 'tr-TR',
              applicationCategory: 'EducationalApplication',
              operatingSystem: 'Web',
              offers: { '@type': 'Offer', price: '0', priceCurrency: 'TRY' },
            },
            {
              '@type': 'BreadcrumbList',
              itemListElement: [
                { '@type': 'ListItem', position: 1, name: 'Ana Sayfa', item: 'https://www.unisense.com.tr/' },
                { '@type': 'ListItem', position: 2, name: seo.title.split('—')[0].split('|')[0].trim(), item: `https://www.unisense.com.tr${routePath}` },
              ],
            },
          ],
        }
  const seoEl = ownsSeo ? null : (
    <Seo
      title={seo.title}
      description={seo.description}
      path={routePath}
      noindex={seo.noindex}
      jsonLd={routeJsonLd}
    />
  )

  // Splash sayfası kendi tam ekran layout'u (SEO head yine de basılır)
  if (loc.pathname === '/') {
    return <>{seoEl}<Outlet /></>
  }

  const navItem = (to: string, label: string, Icon: any, activePaths?: string[]) => {
    const active = activePaths
      ? activePaths.some((p) => loc.pathname === p)
      : loc.pathname === to
    return (
      <Link
        to={to}
        title={label}
        className={`
          relative flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium
          transition-all duration-300 shrink-0
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
        {/* Etiketler lg+ ekranda: login avatarı geniş — orta ekranda ikon-only
            kalınca 6 sekme her durumda sığar, 'Hesap' kaydırmada gizli kalmaz */}
        <span className="relative z-10 hidden lg:inline">{label}</span>
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
        <div className="w-full px-4 md:px-6 xl:px-8 3xl:px-12 py-3 flex items-center justify-between gap-4">
          {/* Logo = Ana Sayfa (nav'da ayrı öğe yok) */}
          <Link to="/anasayfa" className="flex items-center gap-3 group shrink-0">
            <Logo size={40} rounded="rounded-none" />
            <div className="hidden sm:block">
              <span className="block font-display font-bold text-lg text-white leading-none">UniSense</span>
              <p className="text-[10px] text-slate-400 leading-none mt-1">Tercih Asistanı · {TERCIH_YILI}</p>
            </div>
          </Link>

          {/* Ana Sayfa nav'da yok — logo zaten anasayfaya götürür.
              Konular + Deneme tek "Çalışma" sekmesinde birleşti (nav ferahladı). */}
          <nav className="flex items-center gap-1 min-w-0 overflow-x-auto no-scrollbar">
            {navItem('/konular', 'Çalışma', GraduationCap, ['/konular', '/deneme', '/planim', '/ozetler', '/notlar', '/pano'])}
            {navItem('/arama', 'Sorgu', Search)}
            {navItem('/oneriler', 'Tercih', ListChecks)}
            {navItem('/hesap', 'Hesap', Calculator)}
            {navItem('/takvim', 'Takvim', CalendarDays)}
            {navItem('/bolum', 'Bölümler', BookOpen)}
            {navItem('/pusula', 'Pusula', Compass)}
            {navItem('/kariyer', 'Kariyer', Briefcase)}
          </nav>

          {/* Sağ taraf — theme toggle profil avatarına yakın */}
          <div className="flex items-center gap-2 ml-auto shrink-0">
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
                    <Link
                      to="/siralama"
                      onClick={() => setMenuOpen(false)}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-white/5 hover:text-white transition"
                    >
                      <Trophy size={14} /> Sıralama
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

      <main className="flex-1 w-full px-4 md:px-6 xl:px-8 3xl:px-12 py-8 relative z-10">
        <Outlet />
      </main>

      <footer className="border-t border-white/5 py-4 text-center text-xs text-slate-500 relative z-10">
        <div className="w-full px-4 md:px-6 xl:px-8 3xl:px-12 flex flex-wrap items-center justify-center gap-x-3 gap-y-1">
          <span>UniSense</span>
          <span className="text-slate-700">•</span>
          <Link to="/oneriler" className="text-slate-400 hover:text-accent-300 transition">YKS Tercih Robotu</Link>
          <span className="text-slate-700">•</span>
          <Link to="/hesap" className="text-slate-400 hover:text-accent-300 transition">TYT-AYT &amp; OBP Hesaplama</Link>
          <span className="text-slate-700">•</span>
          <Link to="/bolum" className="text-slate-400 hover:text-accent-300 transition">Bölüm Taban Puanları</Link>
          <span className="text-slate-700">•</span>
          <Link to="/lgs" className="text-slate-400 hover:text-accent-300 transition">LGS Robotu</Link>
          <span className="text-slate-700">•</span>
          <Link to="/tus" className="text-slate-400 hover:text-accent-300 transition">TUS/DUS Robotu</Link>
          <span className="text-slate-700">•</span>
          <Link to="/takvim" className="text-slate-400 hover:text-accent-300 transition">Sınav Takvimi</Link>
          <span className="text-slate-700">•</span>
          <Link to="/kariyer" className="text-slate-400 hover:text-accent-300 transition">Kamu İş İlanları</Link>
          <span className="text-slate-700">•</span>
          <span>
            Resmi kaynak:{' '}
            <a className="text-accent-400 hover:underline" href="https://yokatlas.yok.gov.tr" target="_blank" rel="noreferrer">
              YÖK Atlas
            </a>
            {' · '}
            <a className="text-accent-400 hover:underline" href="https://www.osym.gov.tr" target="_blank" rel="noreferrer">
              ÖSYM
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
