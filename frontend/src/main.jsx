import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import App from './App.jsx'
import Splash from './pages/Splash.jsx'
import Home from './pages/Home.jsx'
import Search from './pages/Search.jsx'
import Recommend from './pages/Recommend.jsx'
import Login from './pages/Login.jsx'
import TercihList from './pages/TercihList.jsx'
import Profile from './pages/Profile.jsx'
import Pusula from './pages/Pusula.jsx'
import Hesap from './pages/Hesap.jsx'
import Privacy from './pages/Privacy.jsx'
import Compare from './pages/Compare.jsx'
import BolumKatalog from './pages/BolumKatalog.jsx'
import BolumDetay from './pages/BolumDetay.jsx'
import Takvim from './pages/Takvim.jsx'
import { AuthProvider } from './contexts/AuthContext.jsx'
import { ThemeProvider } from './contexts/ThemeContext.jsx'
import './index.css'

// Eski (İngilizce) adresler → yeni Türkçe adresler; query/hash korunur
const LEGACY_ROUTES = [
  ['/home', '/anasayfa'],
  ['/search', '/arama'],
  ['/recommend', '/oneriler'],
  ['/login', '/giris'],
  ['/profile', '/profil'],
  ['/privacy', '/gizlilik'],
  ['/compare', '/karsilastir'],
]

function LegacyRedirect({ to }) {
  const loc = useLocation()
  return <Navigate to={{ pathname: to, search: loc.search, hash: loc.hash }} replace />
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<App />}>
              <Route index element={<Splash />} />
              <Route path="/anasayfa" element={<Home />} />
              <Route path="/arama" element={<Search />} />
              <Route path="/oneriler" element={<Recommend />} />
              <Route path="/giris" element={<Login />} />
              <Route path="/tercih" element={<TercihList />} />
              <Route path="/profil" element={<Profile />} />
              <Route path="/pusula" element={<Pusula />} />
              <Route path="/hesap" element={<Hesap />} />
              <Route path="/gizlilik" element={<Privacy />} />
              <Route path="/karsilastir" element={<Compare />} />
              <Route path="/bolum" element={<BolumKatalog />} />
              <Route path="/bolum/:slug" element={<BolumDetay />} />
              <Route path="/takvim" element={<Takvim />} />
              {LEGACY_ROUTES.map(([from, to]) => (
                <Route key={from} path={from} element={<LegacyRedirect to={to} />} />
              ))}
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  </React.StrictMode>,
)
