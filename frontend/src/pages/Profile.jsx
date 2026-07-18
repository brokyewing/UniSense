import { useEffect, useRef, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  User, Lock, GraduationCap, Camera, Check, Loader2,
  Save, AlertCircle, Eye, EyeOff,
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import {
  PRESET_AVATARS,
  updateUserBasicInfo,
  updateUserProfile,
  changePassword,
  getUserProfile,
  getAuthProvider,
  getIstatistik,
} from '../firebase'
import { hesaplaXP, seviyeBilgi, kazanilanRozetler } from '../lib/oyun'
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
    if (!loading && !isAuthed) nav('/giris')
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

        {/* Seviye kartı — tüm çalışma + uygulama süresine göre */}
        <SeviyeKarti user={user} />

        {/* Tab nav */}
        <div className="card p-2 flex gap-1">
          <TabBtn active={tab === 'account'} onClick={() => setTab('account')} icon={User}>
            Hesap
          </TabBtn>
          <TabBtn active={tab === 'password'} onClick={() => setTab('password')} icon={Lock}>
            Şifre
          </TabBtn>
          <TabBtn active={tab === 'yks'} onClick={() => setTab('yks')} icon={GraduationCap}>
            Sınav Profilim
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


function SeviyeKarti({ user }) {
  const [stats, setStats] = useState(null)
  useEffect(() => { getIstatistik(user.uid).then(setStats).catch(() => {}) }, [user])
  const xp = stats ? hesaplaXP(stats) : 0
  const sv = seviyeBilgi(xp)
  const rozet = stats ? kazanilanRozetler(stats).length : 0
  const saat = Math.floor((stats?.kullanimDk || 0) / 60)
  return (
    <div className="card">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center text-white font-display font-bold text-xl shrink-0">
          {sv.seviye}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-white">Seviye {sv.seviye}</div>
            <div className="text-[11px] text-slate-400">{sv.mevcut}/{sv.gereken} XP</div>
          </div>
          <div className="h-2 rounded-full bg-white/10 overflow-hidden mt-1.5">
            <div className="h-full rounded-full bg-gradient-to-r from-amber-400 to-orange-500 transition-all duration-500" style={{ width: `${sv.oran}%` }} />
          </div>
          <div className="text-[11px] text-slate-500 mt-1.5">
            {sv.toplam} XP · {rozet} rozet{saat > 0 ? ` · ${saat} sa uygulamada` : ''} · <Link to="/pano" className="text-accent-300 hover:underline">Panom →</Link>
          </div>
        </div>
      </div>
    </div>
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
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState(null)

  async function handleSelectPreset(url) {
    setPhotoURL(url)
    setShowAvatars(false)
  }

  // NOT: Bilgisayardan avatar yükleme kaldırıldı — Firebase Storage yeni
  // projelerde Blaze (ücretli) plan istiyor. Hazır avatarlar (DiceBear URL)
  // Storage gerektirmez. Blaze'e geçilirse: storage.rules deploy et +
  // firebase.js'teki uploadAvatar ile bu butonu geri getir.

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
          </div>

          <div className="flex flex-col gap-2 flex-1 w-full">
            <button
              onClick={() => setShowAvatars((s) => !s)}
              className="btn-ghost inline-flex items-center justify-center gap-2 text-sm"
            >
              <Camera size={14} />
              {showAvatars ? 'Hazır avatarları gizle' : 'Hazır avatar seç'}
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
  const [examTrack, setExamTrack] = useState('YKS')  // ana sınav yolu
  const [kpssScore, setKpssScore] = useState('')  // KPSS GY-GK (Hesap'tan da dolar)
  const [kpssDuzey, setKpssDuzey] = useState('lisans')
  const [dgsScore, setDgsScore] = useState('')    // DGS (Hesap'tan da dolar)
  const [dgsType, setDgsType] = useState('SAY')
  const [tusScore, setTusScore] = useState('')    // TUS (uzmanlık K/T puanı)
  const [dusScore, setDusScore] = useState('')    // DUS
  const [lgsYuzdelik, setLgsYuzdelik] = useState('')  // LGS yüzdelik dilim
  const [agsNet, setAgsNet] = useState('')        // AGS toplam net (öğretmenlik)
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
        if (p.examTrack) setExamTrack(p.examTrack)
        if (p.scoreType) setScoreType(p.scoreType)
        if (p.score != null) setScore(String(p.score))
        if (p.rank != null) setRank(String(p.rank))
        if (Array.isArray(p.preferredCities)) setCities(p.preferredCities.join(', '))
        if (p.preferredUniType) setUniType(p.preferredUniType)
        if (Array.isArray(p.preferredInterests)) setInterests(p.preferredInterests)
        if (p.kpss?.score != null) setKpssScore(String(p.kpss.score))
        if (p.kpss?.duzey) setKpssDuzey(p.kpss.duzey)
        if (p.dgs?.score != null) setDgsScore(String(p.dgs.score))
        if (p.dgs?.type) setDgsType(p.dgs.type)
        if (p.tus?.score != null) setTusScore(String(p.tus.score))
        if (p.dus?.score != null) setDusScore(String(p.dus.score))
        if (p.lgs?.yuzdelik != null) setLgsYuzdelik(String(p.lgs.yuzdelik))
        if (p.ags?.net != null) setAgsNet(String(p.ags.net))
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
        examTrack,
        scoreType,
        score: score ? parseFloat(score) : null,
        rank: rank ? parseInt(rank, 10) : null,
        preferredCities: cities
          .split(',')
          .map((c) => c.trim().toUpperCase())
          .filter(Boolean),
        preferredUniType: uniType,
        preferredInterests: interests,
        kpss: kpssScore
          ? { score: parseFloat(kpssScore), duzey: kpssDuzey, updatedAt: Date.now() }
          : null,
        dgs: dgsScore ? { score: parseFloat(dgsScore), type: dgsType, updatedAt: Date.now() } : null,
        tus: tusScore ? { score: parseFloat(tusScore), updatedAt: Date.now() } : null,
        dus: dusScore ? { score: parseFloat(dusScore), updatedAt: Date.now() } : null,
        lgs: lgsYuzdelik ? { yuzdelik: parseFloat(lgsYuzdelik), updatedAt: Date.now() } : null,
        ags: agsNet ? { net: parseFloat(agsNet), updatedAt: Date.now() } : null,
      })
      setMsg({ type: 'success', text: 'Sınav profilin kaydedildi. Tercih ve öneri sayfalarında otomatik kullanılacak.' })
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
          <GraduationCap size={16} /> Sınav Profilim
        </h3>
        <p className="text-xs text-slate-400">
          Hazırlandığın sınavı seç — alanlar ona göre açılır. Kaydedilen puanlar
          Tercih, Öneri ve sorgu sayfalarında otomatik kullanılır.
        </p>
      </div>

      {/* Sınav yolu blokları — seçili olan aktif kalır, diğer puanlar silinmez */}
      <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-7 gap-2">
        {[
          { id: 'YKS', desc: 'Lise → Üniversite', dolu: score },
          { id: 'DGS', desc: 'Önlisans → Lisans', dolu: dgsScore },
          { id: 'KPSS', desc: 'Memurluk', dolu: kpssScore },
          { id: 'TUS', desc: 'Tıpta uzmanlık', dolu: tusScore },
          { id: 'DUS', desc: 'Dişte uzmanlık', dolu: dusScore },
          { id: 'LGS', desc: 'Liseye geçiş', dolu: lgsYuzdelik },
          { id: 'AGS', desc: 'Öğretmenlik', dolu: agsNet },
        ].map((t) => {
          const active = examTrack === t.id
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setExamTrack(t.id)}
              className={`rounded-xl px-3 py-3 border text-center transition ${
                active
                  ? 'border-accent-500/60 bg-accent-500/15 text-accent-200 shadow-lg'
                  : 'border-white/10 text-slate-300 hover:bg-white/10'
              }`}
            >
              <div className="text-base font-display font-bold">{t.id}</div>
              <div className="text-[10px] text-slate-500">{t.desc}</div>
              <div className={`text-[10px] mt-1 font-mono ${
                t.dolu ? (active ? 'text-emerald-300' : 'text-slate-400') : 'text-slate-600'
              }`}>
                {t.dolu ? `puan: ${t.dolu}` : 'puan yok'}
              </div>
            </button>
          )
        })}
      </div>
      <p className="text-[10px] text-slate-500 !mt-2">
        Yol değiştirmek diğer puanlarını silmez — hepsi profilinde saklı kalır.
      </p>

      {/* === YKS alanları === */}
      {examTrack === 'YKS' && (<>
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
      </>)}

      {/* === DGS alanları === */}
      {examTrack === 'DGS' && (
        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">
              DGS Puanın <span className="text-slate-600">(Hesap sayfasından da dolar)</span>
            </label>
            <input
              type="number"
              step="0.01"
              min="0" max="600"
              value={dgsScore}
              onChange={(e) => setDgsScore(e.target.value)}
              placeholder="örn: 312.40"
              className="input-glass"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">DGS Puan Türü</label>
            <div className="grid grid-cols-3 gap-2">
              {['SAY', 'EA', 'SÖZ'].map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setDgsType(t)}
                  className={`px-2 py-2.5 rounded-xl text-sm font-semibold transition ${
                    dgsType === t
                      ? 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-lg'
                      : 'glass glass-hover text-slate-300'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* === KPSS alanları === */}
      {examTrack === 'KPSS' && (
        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">
              KPSS Puanın <span className="text-slate-600">(GY-GK — Hesap sayfasından da dolar)</span>
            </label>
            <input
              type="number"
              step="0.01"
              min="0" max="120"
              value={kpssScore}
              onChange={(e) => setKpssScore(e.target.value)}
              placeholder="örn: 85.40"
              className="input-glass"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Düzey</label>
            <div className="grid grid-cols-3 gap-2">
              {['lisans', 'önlisans', 'ortaöğretim'].map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setKpssDuzey(d)}
                  className={`px-2 py-2.5 rounded-xl text-xs font-semibold transition ${
                    kpssDuzey === d
                      ? 'bg-gradient-to-br from-sky-500 to-indigo-500 text-white shadow-lg'
                      : 'glass glass-hover text-slate-300'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* === TUS alanı === */}
      {examTrack === 'TUS' && (
        <div>
          <label className="text-xs text-slate-400 mb-1 block">
            TUS Puanın <span className="text-slate-600">(K/T — TUS robotunda tercih için kullanılır)</span>
          </label>
          <input
            type="number" step="0.01" min="0" max="100"
            value={tusScore}
            onChange={(e) => setTusScore(e.target.value)}
            placeholder="örn: 62.40"
            className="input-glass"
          />
        </div>
      )}

      {/* === DUS alanı === */}
      {examTrack === 'DUS' && (
        <div>
          <label className="text-xs text-slate-400 mb-1 block">
            DUS Puanın <span className="text-slate-600">(K/T — DUS robotunda tercih için kullanılır)</span>
          </label>
          <input
            type="number" step="0.01" min="0" max="100"
            value={dusScore}
            onChange={(e) => setDusScore(e.target.value)}
            placeholder="örn: 60.00"
            className="input-glass"
          />
        </div>
      )}

      {/* === LGS alanı === */}
      {examTrack === 'LGS' && (
        <div>
          <label className="text-xs text-slate-400 mb-1 block">
            LGS Yüzdelik Dilimin <span className="text-slate-600">(Türkiye geneli — LGS robotunda kullanılır)</span>
          </label>
          <input
            type="number" step="0.01" min="0" max="100"
            value={lgsYuzdelik}
            onChange={(e) => setLgsYuzdelik(e.target.value)}
            placeholder="örn: 2.50"
            className="input-glass"
          />
        </div>
      )}

      {/* === AGS alanı === (öğretmenlik — net-odaklı, standart puan resmî değil) */}
      {examTrack === 'AGS' && (
        <div>
          <label className="text-xs text-slate-400 mb-1 block">
            AGS Toplam Netin <span className="text-slate-600">(Hesap → AGS sekmesinden hesaplanır; 80 soru üzerinden)</span>
          </label>
          <input
            type="number" step="0.01" min="0" max="80"
            value={agsNet}
            onChange={(e) => setAgsNet(e.target.value)}
            placeholder="örn: 52.00"
            className="input-glass"
          />
          <p className="text-[10px] text-slate-500 mt-1">
            AGS puanı standart-puandır ve sınav ilk uygulama → güvenilir puan/tercih tahmini yok; net bilgi amaçlı saklanır.
          </p>
        </div>
      )}

      {/* Şehirler — tüm sınav yollarında (KPSS'de kadro ili olarak kullanılır) */}
      <div>
        <label className="text-xs text-slate-400 mb-1 block">
          {examTrack === 'KPSS'
            ? 'Tercih ettiğin şehirler — kadro aramada kullanılır (virgülle ayır)'
            : 'Tercih ettiğin şehirler (virgülle ayır)'}
        </label>
        <input
          type="text"
          value={cities}
          onChange={(e) => setCities(e.target.value)}
          placeholder="İSTANBUL, ANKARA, İZMİR"
          className="input-glass"
        />
      </div>

      {/* Üniversite tipi — KPSS'de gereksiz (kadrolar kurumlara ait) */}
      {examTrack !== 'KPSS' && (
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
      )}

      {/* Pusula ilgileri — YKS'ye özgü (bölüm önerilerini besler) */}
      {examTrack === 'YKS' && (
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
      )}

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
