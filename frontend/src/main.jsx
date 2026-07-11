import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { inject } from '@vercel/analytics'
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
import { AuthProvider } from './contexts/AuthContext.jsx'
import { ThemeProvider } from './contexts/ThemeContext.jsx'
import './index.css'

inject()

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<App />}>
              <Route index element={<Splash />} />
              <Route path="/home" element={<Home />} />
              <Route path="/search" element={<Search />} />
              <Route path="/recommend" element={<Recommend />} />
              <Route path="/login" element={<Login />} />
              <Route path="/tercih" element={<TercihList />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/pusula" element={<Pusula />} />
              <Route path="/hesap" element={<Hesap />} />
              <Route path="/privacy" element={<Privacy />} />
              <Route path="/compare" element={<Compare />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  </React.StrictMode>,
)
