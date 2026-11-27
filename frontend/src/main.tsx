import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { inject } from '@vercel/analytics'
import Seo from './components/Seo.tsx'
import App from './App.jsx'
import Home from './pages/Home.jsx'
import Search from './pages/Search.jsx'
import Recommend from './pages/Recommend.jsx'
import Login from './pages/Login.jsx'
import TercihList from './pages/TercihList.jsx'
import Profile from './pages/Profile.jsx'
import Pusula from './pages/Pusula.jsx'
import Hesap from './pages/Hesap.jsx'
import Privacy from './pages/Privacy.jsx'
import Terms from './pages/Terms.jsx'
import Compare from './pages/Compare.jsx'
import BolumKatalog from './pages/BolumKatalog.jsx'
import BolumDetay from './pages/BolumDetay.jsx'
import Takvim from './pages/Takvim.jsx'
import LGS from './pages/LGS.jsx'
import TusDus from './pages/TusDus.jsx'
import Kariyer from './pages/Kariyer.jsx'
import Calisma from './pages/Calisma.jsx'
import OzetDetay from './pages/OzetDetay.jsx'
import Siralama from './pages/Siralama.jsx'
import { AuthProvider } from './contexts/AuthContext.jsx'
import { ThemeProvider } from './contexts/ThemeContext.jsx'
import PWAInstallPrompt from './components/PWAInstallPrompt.jsx'
import ErrorBoundary from './components/ErrorBoundary.jsx'
import './index.css'

inject()
// Eski adresler → kanonik Türkçe adresler; query/hash korunur
const LEGACY_ROUTES = [
  ['/anasayfa', '/'],
  ['/home', '/'],
  ['/search', '/arama'],
  ['/recommend', '/oneriler'],
  ['/login', '/giris'],
  ['/profile', '/profil'],
  ['/privacy', '/gizlilik'],
  ['/compare', '/karsilastir'],
  ['/yanlislarim', '/notlar'], // Yanlış Defteri → Notlar (yeniden adlandırıldı)
  ['/kartlar', '/deneme'],     // Bilgi Kartları kaldırıldı → Çalışmalarım
]

function LegacyRedirect({ to }: { to: string }) {
  const loc = useLocation()
  return <Navigate to={{ pathname: to, search: loc.search, hash: loc.hash }} replace />
}

function NotFound() {
  const loc = useLocation()
  return (
    <>
      <Seo title="Sayfa Bulunamadı | UniSense" description="Aradığın sayfa bulunamadı." path={loc.pathname} noindex />
      <div className="card max-w-md mx-auto my-12 text-center space-y-4">
        <div className="text-4xl font-display font-bold gradient-text">404</div>
        <h1 className="text-xl font-display font-semibold text-white">Sayfa bulunamadı</h1>
        <p className="text-sm text-slate-400">
          Aradığın adres taşınmış veya mevcut değil.
        </p>
        <Link to="/" className="btn-primary inline-flex items-center justify-center text-sm">
          Ana sayfaya dön
        </Link>
      </div>
    </>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
            <Route element={<App />}>
              <Route index element={<Home />} />
              <Route path="/arama" element={<Search />} />
              <Route path="/oneriler" element={<Recommend />} />
              <Route path="/giris" element={<Login />} />
              <Route path="/tercih" element={<TercihList />} />
              <Route path="/profil" element={<Profile />} />
              <Route path="/siralama" element={<Siralama />} />
              <Route path="/pusula" element={<Pusula />} />
              <Route path="/hesap" element={<Hesap />} />
              <Route path="/gizlilik" element={<Privacy />} />
              <Route path="/kullanim-kosullari" element={<Terms />} />
              <Route path="/karsilastir" element={<Compare />} />
              <Route path="/bolum" element={<BolumKatalog />} />
              <Route path="/bolum/:slug" element={<BolumDetay />} />
              <Route path="/takvim" element={<Takvim />} />
              <Route path="/konular" element={<Calisma tab="konular" />} />
              <Route path="/deneme" element={<Calisma tab="deneme" />} />
              <Route path="/planim" element={<Calisma tab="planim" />} />
              <Route path="/ozetler" element={<Calisma tab="ozetler" />} />
              <Route path="/ozet/:slug" element={<OzetDetay />} />
              <Route path="/notlar" element={<Calisma tab="notlar" />} />
              <Route path="/pano" element={<Calisma tab="pano" />} />
              <Route path="/lgs" element={<LGS />} />
              <Route path="/tus" element={<TusDus />} />
              <Route path="/kariyer" element={<Kariyer />} />
              {LEGACY_ROUTES.map(([from, to]) => (
                <Route key={from} path={from} element={<LegacyRedirect to={to} />} />
              ))}
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
          <PWAInstallPrompt />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)

// PWA service worker — sadece production (dev'de HMR'ı bozmasın)
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {})
  })
}
