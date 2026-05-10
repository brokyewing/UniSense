import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  User, Lock, GraduationCap, Camera, Check, Loader2, Upload,
  Save, AlertCircle, Eye, EyeOff,
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import {
  PRESET_AVATARS,
  updateUserBasicInfo,
  updateUserProfile,
  uploadAvatar,
  changePassword,
  getUserProfile,
  getAuthProvider,
} from '../firebase'
import BackgroundScene from '../components/three/BackgroundScene'

const SCORE_TYPES = [
  { v: 'SAY', label: 'Sayısal', color: 'from-blue-500 to-cyan-400' },
  { v: 'EA',  label: 'Eşit Ağırlık', color: 'from-emerald-500 to-teal-400' },
  { v: 'SÖZ', label: 'Sözel', color: 'from-rose-500 to-pink-400' },
  { v: 'DİL', label: 'Yabancı Dil', color: 'from-amber-500 to-orange-400' },
  { v: 'TYT', label: 'TYT', color: 'from-purple-500 to-violet-400' },
]

export default function Profile() {
  const nav = useNavigate()
  const { user, isAuthed, loading } = useAuth()

  // Tab
  const [tab, setTab] = useState('account') // account | password | yks

  useEffect(() => {
    if (!loading && !isAuthed) nav('/login')
  }, [loading, isAuthed, nav])

  if (!isAuthed || !user) return null

  return (
    <>
      <BackgroundScene />

      <div className="max-w-3xl mx-auto space-y-5">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card flex items-center gap-4"
        >
          <ProfileAvatar user={user} size={64} />
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-display font-bold text-white truncate">
              {user.displayName || 'Kullanıcı'}
            </h1>
            <p className="text-sm text-slate-400 truncate">{user.email}</p>
          </div>
        </motion.div>

        {/* Tab nav */}
        <div className="card p-2 flex gap-1">
          <TabBtn active={tab === 'account'} onClick={() => setTab('account')} icon={User}>
            Hesap
          </TabBtn>
          <TabBtn active={tab === 'password'} onClick={() => setTab('password')} icon={Lock}>
            Şifre
          </TabBtn>
          <TabBtn active={tab === 'yks'} onClick={() => setTab('yks')} icon={GraduationCap}>
            YKS Profili
          </TabBtn>
        </div>

        <AnimatePresence mode="wait">
          {tab === 'account' && <AccountTab key="account" user={user} />}
          {tab === 'password' && <PasswordTab key="password" user={user} />}
          {tab === 'yks' && <YksTab key="yks" user={user} />}
        </AnimatePresence>
      </div>
    </>
  )
}


function TabBtn({ active, onClick, icon: Icon, children }) {
  return (
    <button
      onClick={onClick}
      className={`
        flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium
        transition-all relative
        ${active
          ? 'bg-gradient-to-r from-brand-500/20 to-accent-500/20 text-white border border-accent-500/30'
          : 'text-slate-400 hover:text-slate-200'
        }
      `}
    >
      <Icon size={14} />
      {children}
    </button>
  )
}


/* === Avatar Display === */
function ProfileAvatar({ user, size = 56 }) {
  if (user.photoURL) {
    return (
      <img
        src={user.photoURL}
        alt=""
        className="rounded-full object-cover ring-2 ring-accent-500/30"
        style={{ width: size, height: size }}
        referrerPolicy="no-referrer"
      />
    )
  }
  const initial = (user.displayName || user.email || 'U')[0].toUpperCase()
  return (
    <div
      className="rounded-full bg-gradient-to-br from-brand-500 to-accent-600 flex items-center justify-center text-white font-display font-bold ring-2 ring-accent-500/30"
      style={{ width: size, height: size, fontSize: size * 0.4 }}
    >
      {initial}
    </div>
  )
}


/* === ACCOUNT TAB === */
function AccountTab({ user }) {
  const [name, setName] = useState(user.displayName || '')
  const [photoURL, setPhotoURL] = useState(user.photoURL || '')
  const [showAvatars, setShowAvatars] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState(null)
  const fileInputRef = useRef(null)

  async function handleSelectPreset(url) {
    setPhotoURL(url)
    setShowAvatars(false)
  }

  async function handleFileUpload(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setMsg(null)
    try {
      const url = await uploadAvatar(user.uid, file)
      setPhotoURL(url)
    } catch (e) {
      setMsg({ type: 'error', text: e.message })
    } finally {
      setUploading(false)
    }
  }

  async function handleSave() {
    setSaving(true)
    setMsg(null)
    try {
      await updateUserBasicInfo(user, {
        displayName: name.trim(),
        photoURL,
      })
      setMsg({ type: 'success', text: 'Hesap bilgileri kaydedildi' })
    } catch (e) {
      setMsg({ type: 'error', text: e.message || 'Kayıt başarısız' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="space-y-4"
    >
      {/* Avatar */}
      <div className="card">
        <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
          <Camera size={16} /> Profil Resmi
        </h3>

        <div className="flex flex-col sm:flex-row items-center gap-4">
          <div className="relative">
            {photoURL ? (
              <img
                src={photoURL}
                alt=""
                className="w-24 h-24 rounded-full object-cover ring-2 ring-accent-500/40"
                referrerPolicy="no-referrer"
              />
            ) : (
              <div className="w-24 h-24 rounded-full bg-gradient-to-br from-brand-500 to-accent-600 flex items-center justify-center text-white text-3xl font-bold">
                {(name || user.email || 'U')[0].toUpperCase()}
              </div>
            )}
            {uploading && (
              <div className="absolute inset-0 rounded-full bg-black/50 flex items-center justify-center">
                <Loader2 size={24} className="animate-spin text-white" />
              </div>
            )}
          </div>

          <div className="flex flex-col gap-2 flex-1 w-full">
            <button
              onClick={() => setShowAvatars((s) => !s)}
              className="btn-ghost inline-flex items-center justify-center gap-2 text-sm"
            >
              <Camera size={14} />
              {showAvatars ? 'Hazır avatarları gizle' : 'Hazır avatar seç'}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="btn-ghost inline-flex items-center justify-center gap-2 text-sm disabled:opacity-50"
            >
              <Upload size={14} /> Bilgisayardan yükle
            </button>
            {photoURL && (
              <button
                onClick={() => setPhotoURL('')}
                className="text-xs text-slate-500 hover:text-rose-400"
              >
                Resmi kaldır
              </button>
            )}
          </div>
        </div>

        <AnimatePresence>
          {showAvatars && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="grid grid-cols-4 sm:grid-cols-6 gap-2 mt-4 pt-4 border-t border-white/5">
                {PRESET_AVATARS.map((av) => {
                  const selected = photoURL === av.url
                  return (
                    <button
                      key={av.id}
                      onClick={() => handleSelectPreset(av.url)}
                      className={`
                        relative aspect-square rounded-full overflow-hidden transition-all
                        ${selected
                          ? 'ring-2 ring-accent-500 scale-105'
                          : 'ring-1 ring-white/10 hover:ring-white/30 hover:scale-105'
                        }
                      `}
                    >
                      <img
                        src={av.url}
                        alt=""
                        className="w-full h-full object-cover"
                        loading="lazy"
                      />
                      {selected && (
                        <div className="absolute inset-0 bg-accent-500/30 flex items-center justify-center">
                          <Check size={20} className="text-white drop-shadow" />
                        </div>
                      )}
                    </button>
                  )
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* İsim */}
      <div className="card">
        <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
          <User size={16} /> Kişisel Bilgiler
        </h3>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Görünen ad</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Adın"
              className="input-glass"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">E-posta</label>
            <input
              type="email"
              value={user.email || ''}
              disabled
              className="input-glass opacity-60 cursor-not-allowed"
            />
          </div>
        </div>
      </div>

      {msg && <Banner msg={msg} />}

      <button
        onClick={handleSave}
        disabled={saving}
        className="btn-primary w-full inline-flex items-center justify-center gap-2 disabled:opacity-50"
      >
        {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
        Kaydet
      </button>
    </motion.div>
  )
}


/* === PASSWORD TAB === */
function PasswordTab({ user }) {
  const [curr, setCurr] = useState('')
  const [pw, setPw] = useState('')
  const [pwc, setPwc] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState(null)
  const provider = getAuthProvider(user)

  if (provider === 'google') {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="card text-center py-10"
      >
        <Lock size={32} className="mx-auto text-slate-500 mb-3" />
        <h3 className="font-semibold text-white mb-1">Google ile giriş yapıldı</h3>
        <p className="text-sm text-slate-400 max-w-md mx-auto">
          Google hesapları için şifre <strong>UniSense üzerinden değiştirilemez</strong>.
          Şifreni değiştirmek için{' '}
          <a
            href="https://myaccount.google.com/security"
            target="_blank"
            rel="noreferrer"
            className="text-accent-400 hover:underline"
          >
            Google Hesap Ayarları
          </a>'na git.
        </p>
      </motion.div>
    )
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setMsg(null)
    if (pw.length < 6) {
      setMsg({ type: 'error', text: 'Yeni şifre en az 6 karakter olmalı' })
      return
    }
    if (pw !== pwc) {
      setMsg({ type: 'error', text: 'Yeni şifreler eşleşmiyor' })
      return
    }
    setSaving(true)
    try {
      await changePassword(curr, pw)
      setMsg({ type: 'success', text: 'Şifren güncellendi' })
      setCurr('')
      setPw('')
      setPwc('')
    } catch (e) {
      setMsg({ type: 'error', text: parseAuthErr(e) })
    } finally {
      setSaving(false)
    }
  }

  return (
    <motion.form
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="card space-y-3"
    >
      <h3 className="font-semibold text-white flex items-center gap-2">
        <Lock size={16} /> Şifre Değiştir
      </h3>

      <PasswordInput
        label="Mevcut şifren"
        value={curr}
        onChange={setCurr}
        showPw={showPw}
        toggleShow={() => setShowPw((s) => !s)}
      />
      <PasswordInput
        label="Yeni şifre (min 6)"
        value={pw}
        onChange={setPw}
        showPw={showPw}
        toggleShow={() => setShowPw((s) => !s)}
      />
      <PasswordInput
        label="Yeni şifre (tekrar)"
        value={pwc}
        onChange={setPwc}
        showPw={showPw}
        toggleShow={() => setShowPw((s) => !s)}
      />

      {msg && <Banner msg={msg} />}

      <button
        type="submit"
        disabled={saving}
        className="btn-primary w-full inline-flex items-center justify-center gap-2 disabled:opacity-50"
      >
        {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
        Şifreyi Güncelle
      </button>
    </motion.form>
  )
}


function PasswordInput({ label, value, onChange, showPw, toggleShow }) {
  return (
    <div>
      <label className="text-xs text-slate-400 mb-1 block">{label}</label>
      <div className="relative">
        <input
          type={showPw ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="input-glass pr-10"
          required
          minLength={6}
        />
        <button
          type="button"
          onClick={toggleShow}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
        >
          {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
        </button>
      </div>
    </div>
  )
}


/* === YKS TAB === */
const UNI_TYPES = [
  { v: 'all',    label: 'Hepsi',           desc: 'Hem devlet hem vakıf', color: 'from-slate-500 to-slate-700' },
  { v: 'Devlet', label: 'Devlet',          desc: 'Sadece ücretsiz',      color: 'from-emerald-500 to-teal-600' },
  { v: 'Vakıf',  label: 'Vakıf (Özel)',    desc: 'Vakıf üniversiteleri', color: 'from-rose-500 to-pink-600' },
]

function YksTab({ user }) {
  const [scoreType, setScoreType] = useState('SAY')
  const [score, setScore] = useState('')
  const [rank, setRank] = useState('')
  const [cities, setCities] = useState('')
  const [uniType, setUniType] = useState('all')
  const [interests, setInterests] = useState([])
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await getUserProfile(user.uid)
        if (cancelled) return
        const p = data?.profile || {}
        if (p.scoreType) setScoreType(p.scoreType)
        if (p.score != null) setScore(String(p.score))
        if (p.rank != null) setRank(String(p.rank))
        if (Array.isArray(p.preferredCities)) setCities(p.preferredCities.join(', '))
        if (p.preferredUniType) setUniType(p.preferredUniType)
        if (Array.isArray(p.preferredInterests)) setInterests(p.preferredInterests)
      } catch (e) {
        console.warn(e)
      } finally {
        setLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, [user.uid])

  function removeInterest(name) {
    setInterests((prev) => prev.filter((x) => x !== name))
  }

  async function handleSave() {
    setSaving(true)
    setMsg(null)
    try {
      await updateUserProfile(user.uid, {
        scoreType,
        score: score ? parseFloat(score) : null,
        rank: rank ? parseInt(rank, 10) : null,
        preferredCities: cities
          .split(',')
          .map((c) => c.trim().toUpperCase())
          .filter(Boolean),
        preferredUniType: uniType,
        preferredInterests: interests,
      })
      setMsg({ type: 'success', text: 'YKS profilin kaydedildi. Tercih sayfasında otomatik kullanılacak.' })
    } catch (e) {
      setMsg({ type: 'error', text: e.message || 'Kayıt başarısız' })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="card text-center py-8">
        <Loader2 size={20} className="animate-spin mx-auto text-accent-400" />
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="card space-y-4"
    >
      <div>
        <h3 className="font-semibold text-white flex items-center gap-2 mb-1">
          <GraduationCap size={16} /> YKS Profili
        </h3>
        <p className="text-xs text-slate-400">
          Kaydedilen puan/sıralama "Tercih" sayfasında otomatik dolar.
        </p>
      </div>

      <div>
        <label className="text-xs text-slate-400 mb-2 block">Puan Türü</label>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {SCORE_TYPES.map((s) => {
            const active = scoreType === s.v
            return (
              <button
                key={s.v}
                type="button"
                onClick={() => setScoreType(s.v)}
                className={`
                  relative px-3 py-3 rounded-xl text-sm font-medium transition-all
                  ${active
                    ? `bg-gradient-to-br ${s.color} text-white shadow-lg`
                    : 'glass glass-hover text-slate-300'
                  }
                `}
              >
                <div className="font-display font-bold text-lg">{s.v}</div>
                <div className={`text-[10px] ${active ? 'text-white/80' : 'text-slate-500'}`}>
                  {s.label}
                </div>
              </button>
            )
          })}
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-slate-400 mb-1 block">YKS Puanın</label>
          <input
            type="number"
            step="0.01"
            value={score}
            onChange={(e) => setScore(e.target.value)}
            placeholder="örn: 480.50"
            className="input-glass"
          />
        </div>
        <div>
          <label className="text-xs text-slate-400 mb-1 block">Başarı Sırası</label>
          <input
            type="number"
            value={rank}
            onChange={(e) => setRank(e.target.value)}
            placeholder="örn: 5000"
            className="input-glass"
          />
        </div>
      </div>

      <div>
        <label className="text-xs text-slate-400 mb-1 block">
          Tercih ettiğin şehirler (virgülle ayır)
        </label>
        <input
          type="text"
          value={cities}
          onChange={(e) => setCities(e.target.value)}
          placeholder="İSTANBUL, ANKARA, İZMİR"
          className="input-glass"
        />
      </div>

      <div>
        <label className="text-xs text-slate-400 mb-2 block">
          Üniversite Tipi
        </label>
        <div className="grid grid-cols-3 gap-2">
          {UNI_TYPES.map((u) => {
            const active = uniType === u.v
            return (
              <button
                key={u.v}
                type="button"
                onClick={() => setUniType(u.v)}
                className={`
                  relative px-3 py-2.5 rounded-xl text-sm font-medium transition-all text-left
                  ${active
                    ? `bg-gradient-to-br ${u.color} text-white shadow-lg`
                    : 'glass glass-hover text-slate-300'
                  }
                `}
              >
                <div className="font-semibold">{u.label}</div>
                <div className={`text-[10px] mt-0.5 ${active ? 'text-white/80' : 'text-slate-500'}`}>
                  {u.desc}
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Pusula'dan kayıtlı ilgilerim */}
      <div>
        <label className="text-xs text-slate-400 mb-2 flex items-center justify-between">
          <span>Pusula'dan kayıtlı ilgilerim</span>
          {interests.length > 0 && (
            <span className="text-[10px] text-slate-500">{interests.length} ilgi</span>
          )}
        </label>
        {interests.length === 0 ? (
          <div className="text-xs text-slate-500 italic px-2">
            Henüz Pusula'dan ilgi seçmedin. <a href="/pusula" className="text-accent-300 hover:underline">Pusula'ya git →</a>
          </div>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {interests.map((iv) => (
              <span
                key={iv}
                className="text-xs px-2 py-1 rounded-full bg-emerald-500/15 text-emerald-200 border border-emerald-500/30 flex items-center gap-1"
              >
                ✓ {iv}
                <button
                  type="button"
                  onClick={() => removeInterest(iv)}
                  className="opacity-50 hover:opacity-100 hover:text-rose-300 transition"
                  title="Çıkar"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {msg && <Banner msg={msg} />}

      <button
        onClick={handleSave}
        disabled={saving}
        className="btn-primary w-full inline-flex items-center justify-center gap-2 disabled:opacity-50"
      >
        {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
        Profili Kaydet
      </button>
    </motion.div>
  )
}


function Banner({ msg }) {
  const isErr = msg.type === 'error'
  return (
    <motion.div
      initial={{ opacity: 0, y: -5 }}
      animate={{ opacity: 1, y: 0 }}
      className={`
        text-sm rounded-xl px-4 py-3 flex items-center gap-2
        ${isErr
          ? 'bg-rose-500/10 border border-rose-500/30 text-rose-300'
          : 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300'
        }
      `}
    >
      {isErr ? <AlertCircle size={14} /> : <Check size={14} />}
      {msg.text}
    </motion.div>
  )
}


function parseAuthErr(e) {
  const m = e?.message || String(e)
  if (m.includes('wrong-password')) return 'Mevcut şifren yanlış'
  if (m.includes('weak-password')) return 'Yeni şifre çok zayıf'
  if (m.includes('requires-recent-login')) return 'Yeniden giriş yapman gerek (güvenlik)'
  return m.slice(0, 200)
}
