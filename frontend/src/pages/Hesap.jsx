/**
 * YKS Hesap Makinesi 2025
 *
 * ÖSYM 2025 yaklaşık katsayıları (her ders için ayrı ağırlık):
 *
 * TYT (max ~500):
 *   100 + 3.3×Türkçe + 3.4×Sosyal + 3.3×Mat + 3.4×Fen
 *
 * AYT-SAY (max ~560):
 *   100 + 3.0×Mat + 2.85×Fizik + 3.07×Kimya + 3.07×Biyoloji
 *
 * AYT-EA (max ~560):
 *   100 + 3.0×Mat + 3.0×Edebiyat + 2.8×Tarih-1 + 3.33×Coğrafya-1
 *
 * AYT-SÖZ (max ~560):
 *   100 + 3.0×Edebiyat + 2.8×Tarih-1 + 3.33×Coğrafya-1
 *       + 2.91×Tarih-2 + 2.91×Coğrafya-2 + 2.67×Felsefe + 5.33×Din
 *
 * YDT-DİL (max ~500):
 *   100 + 5.0×Yabancı Dil
 *
 * YERLEŞTİRME (lisans):
 *   = TYT × 0.4 + AYT × 0.6 + OBP × 0.12
 *
 * OBP (Ortaöğretim Başarı Puanı):
 *   100'lük diploma notu × 5 = OBP (max 500)
 *   Örn: 85 → OBP 425, +51 puan eklenir
 *
 * DGS (önlisans → lisans):
 *   DGS_HAM = 100 + 3.0×Say + 3.0×Söz
 *   AOBP   = (GPA × 25) × 0.5  (4'lük GPA)
 *   DGS_PUAN = DGS_HAM + AOBP
 *
 * NOT: Yaklaşık formüller. Gerçek ÖSYM puanları norm tablosuyla
 * standardize ediliyor — sapma ±5-10 puan olabilir.
 */
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Calculator, Save, Loader2, Info, ListChecks, ArrowRight,
  GraduationCap, BookOpen, Sparkles, Building2, MapPin,
  Hash, TrendingUp,
} from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import { useAuth } from '../contexts/AuthContext'
import { getUserProfile, updateUserProfile } from '../firebase'
import { apiFetch } from '../lib/api'

// === ÖSYM 2025 katsayıları (yaklaşık, ders-bazlı)
const TYT_BIAS = 100
const AYT_BIAS = 100
const OBP_MULT = 0.12          // ÖSYM yerleştirme puanına eklenen OBP katsayısı
const TYT_W = 0.4              // YERLEŞTİRME = 0.4*TYT + 0.6*AYT
const AYT_W = 0.6

// TYT ders katsayıları (max 500'e ulaşacak şekilde)
const TYT_COEF = {
  tyt_tr:  3.3,   // 40 × 3.3 = 132
  tyt_sos: 3.4,   // 20 × 3.4 = 68
  tyt_mat: 3.3,   // 40 × 3.3 = 132
  tyt_fen: 3.4,   // 20 × 3.4 = 68
}
// SAY: 40m + 14f + 13k + 13b
const AYT_SAY_COEF = {
  ayt_mat: 3.0,   // 40 × 3.0 = 120
  ayt_fiz: 2.85,  // 14 × 2.85 ≈ 40
  ayt_kim: 3.07,  // 13 × 3.07 ≈ 40
  ayt_biy: 3.07,  // 13 × 3.07 ≈ 40
}
// EA: 40m + 24e + 10t + 6c
const AYT_EA_COEF = {
  ayt_mat:  3.0,
  ayt_edb:  3.0,
  ayt_tar1: 2.8,
  ayt_cog1: 3.33,
}
// SÖZ: 24e + 10t1 + 6c1 + 11t2 + 11c2 + 12f + 6d
const AYT_SOZ_COEF = {
  ayt_edb:  3.0,
  ayt_tar1: 2.8,
  ayt_cog1: 3.33,
  ayt_tar2: 2.91,
  ayt_cog2: 2.91,
  ayt_fel:  2.67,
  ayt_din:  5.33,
}
const AYT_DIL_COEF = { ayt_dil: 5.0 }  // 80 × 5.0 = 400 + 100 = 500
const DGS_COEF = { dgs_say: 3.0, dgs_soz: 3.0 }

// === TYT şablonu (40 Türkçe, 20 Sosyal, 40 Mat, 20 Fen — toplam 120)
const TYT_FIELDS = [
  { id: 'tyt_tr',  label: 'TYT Türkçe',     max: 40 },
  { id: 'tyt_sos', label: 'TYT Sosyal',     max: 20 },
  { id: 'tyt_mat', label: 'TYT Matematik',  max: 40 },
  { id: 'tyt_fen', label: 'TYT Fen',        max: 20 },
]

// === AYT şablonları
const AYT_SAY_FIELDS = [
  { id: 'ayt_mat', label: 'AYT Matematik', max: 40 },
  { id: 'ayt_fiz', label: 'AYT Fizik',     max: 14 },
  { id: 'ayt_kim', label: 'AYT Kimya',     max: 13 },
  { id: 'ayt_biy', label: 'AYT Biyoloji',  max: 13 },
]
const AYT_EA_FIELDS = [
  { id: 'ayt_mat', label: 'AYT Matematik',     max: 40 },
  { id: 'ayt_edb', label: 'AYT Edebiyat',      max: 24 },
  { id: 'ayt_tar1', label: 'AYT Tarih-1',       max: 10 },
  { id: 'ayt_cog1', label: 'AYT Coğrafya-1',   max: 6 },
]
const AYT_SOZ_FIELDS = [
  { id: 'ayt_edb', label: 'AYT Edebiyat',     max: 24 },
  { id: 'ayt_tar1', label: 'AYT Tarih-1',       max: 10 },
  { id: 'ayt_cog1', label: 'AYT Coğrafya-1',   max: 6 },
  { id: 'ayt_tar2', label: 'AYT Tarih-2',       max: 11 },
  { id: 'ayt_cog2', label: 'AYT Coğrafya-2',   max: 11 },
  { id: 'ayt_fel', label: 'AYT Felsefe',      max: 12 },
  { id: 'ayt_din', label: 'AYT Din',          max: 6 },
]
const AYT_DIL_FIELDS = [
  { id: 'ayt_dil', label: 'YDT Yabancı Dil', max: 80 },
]

// === DGS (önlisans mezunu için lisans geçişi)
const DGS_FIELDS = [
  { id: 'dgs_say', label: 'DGS Sayısal', max: 60 },
  { id: 'dgs_soz', label: 'DGS Sözel',   max: 60 },
]

const TABS = [
  { id: 'TYT', label: 'TYT', desc: 'Önlisans / temel', color: 'from-purple-500 to-violet-500' },
  { id: 'SAY', label: 'AYT-SAY', desc: 'Sayısal lisans', color: 'from-blue-500 to-cyan-400' },
  { id: 'EA',  label: 'AYT-EA',  desc: 'Eşit Ağırlık', color: 'from-emerald-500 to-teal-400' },
  { id: 'SÖZ', label: 'AYT-SÖZ', desc: 'Sözel lisans',  color: 'from-rose-500 to-pink-400' },
  { id: 'DİL', label: 'YDT-DİL', desc: 'Yabancı dil',   color: 'from-amber-500 to-orange-400' },
  { id: 'DGS', label: 'DGS',     desc: 'Önlisans→Lisans', color: 'from-fuchsia-500 to-purple-500' },
]

// === Net hesaplama: doğru - 0.25*yanlış
function netOf(dogru, yanlis) {
  const d = parseFloat(dogru) || 0
  const y = parseFloat(yanlis) || 0
  return Math.max(0, d - 0.25 * y)
}

// === Diploma puanı → OBP
//   YKS (lise diploması): 100'lük sistem (50-100), × 5 = OBP (250-500)
//     Örn: 85 → 425, 100 → 500
//   DGS (önlisans GPA): 4'lük sistem (0-4), × 25 = 100'lük, × 0.5 sonra
//     AOBP = GPA × 25 × 0.5 (DGS yerleştirmeye eklenen)
function diploma100ToObp(diploma100) {
  const d = parseFloat(diploma100)
  if (!d || d < 0 || d > 100) return 0
  return d * 5  // 50→250, 100→500
}
function gpa4ToAobp(gpa4) {
  const d = parseFloat(gpa4)
  if (!d || d < 0 || d > 4) return 0
  return d * 25 * 0.5  // 4 → 50 puan eklenir
}

// === Ham puan hesabı (ders bazlı katsayılar)
function weightedSum(nets, coefMap) {
  let total = 0
  let anyNet = false
  for (const [key, coef] of Object.entries(coefMap)) {
    const n = parseFloat(nets[key]) || 0
    if (n > 0) {
      anyNet = true
      total += n * coef
    }
  }
  return anyNet ? total : 0
}

function tytHam(nets) {
  const w = weightedSum(nets, TYT_COEF)
  return w > 0 ? w + TYT_BIAS : 0
}

function aytHam(nets, type) {
  const coefMap =
    type === 'SAY' ? AYT_SAY_COEF
    : type === 'EA' ? AYT_EA_COEF
    : type === 'SÖZ' ? AYT_SOZ_COEF
    : type === 'DİL' ? AYT_DIL_COEF
    : null
  if (!coefMap) return 0
  const w = weightedSum(nets, coefMap)
  return w > 0 ? w + AYT_BIAS : 0
}

function dgsHam(nets) {
  const w = weightedSum(nets, DGS_COEF)
  return w > 0 ? w + 100 : 0
}

// === Yerleştirme puanı (TYT %40 + AYT %60 + OBP × 0.12)
function placementScore(tytH, aytH, obp) {
  const obpAdd = obp * OBP_MULT
  if (aytH > 0 && tytH > 0) {
    return TYT_W * tytH + AYT_W * aytH + obpAdd
  }
  if (tytH > 0) return tytH + obpAdd
  return 0
}


function NetInput({ field, value, onChange }) {
  const dKey = `${field.id}_d`
  const yKey = `${field.id}_y`
  const d = value[dKey] ?? ''
  const y = value[yKey] ?? ''
  const dNum = parseFloat(d) || 0
  const yNum = parseFloat(y) || 0
  const total = dNum + yNum
  const exceeded = total > field.max
  const net = netOf(d, y)

  // D ve Y'nin max'ı, diğerine göre dinamik kalır
  const dMax = field.max - (yNum || 0)
  const yMax = field.max - (dNum || 0)

  function handleD(val) {
    const v = parseFloat(val)
    // Eğer D + mevcut Y > max ise D'yi sınırla
    if (val !== '' && !isNaN(v)) {
      const cappedD = Math.min(v, field.max - (yNum || 0))
      onChange(dKey, String(Math.max(0, cappedD)))
    } else {
      onChange(dKey, val)
    }
  }
  function handleY(val) {
    const v = parseFloat(val)
    if (val !== '' && !isNaN(v)) {
      const cappedY = Math.min(v, field.max - (dNum || 0))
      onChange(yKey, String(Math.max(0, cappedY)))
    } else {
      onChange(yKey, val)
    }
  }

  return (
    <div className={`flex items-center gap-2 py-1.5 ${exceeded ? 'bg-rose-500/5 rounded-lg px-2' : ''}`}>
      <div className="flex-1 text-xs text-slate-300">
        {field.label}
        <span className="text-slate-500 text-[10px] ml-1">
          / {field.max}
          {total > 0 && <> · {total}/{field.max}</>}
        </span>
      </div>
      <input
        type="number" min="0" max={dMax} step="1"
        value={d}
        onChange={(e) => handleD(e.target.value)}
        placeholder="D"
        title={`Maksimum ${field.max} soru — ${dMax} doğru girebilirsin`}
        className="w-14 input-glass !py-1 !px-2 text-center text-sm font-mono"
      />
      <input
        type="number" min="0" max={yMax} step="1"
        value={y}
        onChange={(e) => handleY(e.target.value)}
        placeholder="Y"
        title={`Maksimum ${yMax} yanlış girebilirsin`}
        className="w-14 input-glass !py-1 !px-2 text-center text-sm font-mono"
      />
      <div className="w-16 text-right text-sm font-mono text-accent-300">
        {net > 0 ? net.toFixed(2) : '-'}
      </div>
    </div>
  )
}


export default function Hesap() {
  const navigate = useNavigate()
  const { user, isAuthed } = useAuth()
  const [tab, setTab] = useState('SAY')
  const [diploma100, setDiploma100] = useState('') // YKS: 100'lük, örn: 85
  const [gpa4, setGpa4] = useState('')             // DGS: 4'lük, örn: 3.2
  const [data, setData] = useState({}) // {tyt_tr_d: 35, tyt_tr_y: 5, ...}
  const [saving, setSaving] = useState(false)
  const [savedMsg, setSavedMsg] = useState(null)
  const [simResults, setSimResults] = useState(null)
  const [simLoading, setSimLoading] = useState(false)
  const [simError, setSimError] = useState('')

  // YKS için OBP (250-500), DGS için AOBP (0-50 puan)
  const obp = diploma100ToObp(diploma100)   // YKS yerleştirmesinde × 0.12 ile eklenir
  const aobp = gpa4ToAobp(gpa4)             // DGS yerleştirmesinde direkt eklenir

  // Profile'tan eski değerleri yükle (varsa)
  useEffect(() => {
    if (!user) return
    let cancelled = false
    ;(async () => {
      try {
        const p = await getUserProfile(user.uid)
        if (cancelled) return
        const calc = p?.profile?.calculator
        if (calc?.netler) setData(calc.netler)
        if (calc?.diploma100 != null) setDiploma100(String(calc.diploma100))
        if (calc?.gpa4 != null) setGpa4(String(calc.gpa4))
        // eski format'lardan çevir (geriye uyumluluk)
        if (calc?.diploma100 == null && calc?.diploma != null) {
          // eski 4'lük YKS değerini 100'lüğe çevir
          const conv = parseFloat(calc.diploma) * 25
          if (conv > 0 && conv <= 100) setDiploma100(conv.toFixed(0))
        }
        if (calc?.lastTab) setTab(calc.lastTab)
      } catch {}
    })()
    return () => { cancelled = true }
  }, [user])

  function setField(key, val) {
    setData((prev) => ({ ...prev, [key]: val }))
  }

  // Tüm net'leri hesapla
  const nets = useMemo(() => {
    const out = {}
    const allFields = [
      ...TYT_FIELDS, ...AYT_SAY_FIELDS, ...AYT_EA_FIELDS,
      ...AYT_SOZ_FIELDS, ...AYT_DIL_FIELDS, ...DGS_FIELDS,
    ]
    const seen = new Set()
    for (const f of allFields) {
      if (seen.has(f.id)) continue
      seen.add(f.id)
      out[f.id] = netOf(data[`${f.id}_d`], data[`${f.id}_y`])
    }
    return out
  }, [data])

  // Aktif tab için sonuç
  const result = useMemo(() => {
    const tytH = tytHam(nets)
    if (tab === 'TYT') {
      return {
        scoreType: 'TYT',
        ham: tytH,
        finalScore: tytH + obp * OBP_MULT,
        label: 'TYT Yerleştirme Puanı',
      }
    }
    if (tab === 'DGS') {
      const dgsH = dgsHam(nets)
      return {
        scoreType: 'DGS',
        ham: dgsH,
        finalScore: dgsH + aobp,  // AOBP doğrudan eklenir (× 0.5 zaten içeride)
        label: 'DGS Yerleştirme Puanı',
      }
    }
    // AYT türleri
    const aytH = aytHam(nets, tab)
    return {
      scoreType: tab,
      ham: aytH,
      tytHam: tytH,
      finalScore: placementScore(tytH, aytH, obp),
      label: `${tab} Yerleştirme Puanı`,
    }
  }, [nets, obp, aobp, tab])

  // === Simulasyon: bu puanla hangi programlar yazılır? ===
  async function runSimulation() {
    if (result.finalScore <= 100 || !['SAY','EA','SÖZ','DİL','TYT'].includes(tab)) {
      setSimError('Önce netlerini gir, geçerli bir puan oluşunca dene')
      setTimeout(() => setSimError(''), 2500)
      return
    }
    setSimLoading(true)
    setSimError('')
    try {
      const data = await apiFetch('/api/v1/recommend', {
        method: 'POST',
        body: {
          score_type: tab === 'TYT' ? 'TYT' : tab,
          score: parseFloat(result.finalScore.toFixed(2)),
          rank: null,
          preferred_departments: [],
          preferred_uni_types: [],
        },
      })
      setSimResults(data)
    } catch (e) {
      setSimError(e.message)
    } finally {
      setSimLoading(false)
    }
  }

  // Profile'a kaydet
  async function handleSave() {
    if (!user) {
      setSavedMsg({ type: 'error', text: 'Kaydetmek için giriş yap' })
      setTimeout(() => setSavedMsg(null), 3000)
      return
    }
    setSaving(true)
    try {
      // Aktif tab puan/sıra olarak Profile'da setlemek istiyorsa: scoreType + score
      const profilePatch = {
        calculator: {
          netler: data,
          diploma100: diploma100 ? parseFloat(diploma100) : null,
          gpa4: gpa4 ? parseFloat(gpa4) : null,
          obp: obp || null,    // YKS için (250-500)
          aobp: aobp || null,  // DGS için (0-50)
          lastTab: tab,
          updatedAt: Date.now(),
        },
      }
      // Eğer tab AYT türü ve hesap geçerliyse, profile.scoreType ve score'u güncelle
      if (['SAY', 'EA', 'SÖZ', 'DİL'].includes(tab) && result.finalScore > 100) {
        profilePatch.scoreType = tab
        profilePatch.score = parseFloat(result.finalScore.toFixed(2))
      } else if (tab === 'TYT' && result.finalScore > 100) {
        profilePatch.scoreType = 'TYT'
        profilePatch.score = parseFloat(result.finalScore.toFixed(2))
      }
      await updateUserProfile(user.uid, profilePatch)
      setSavedMsg({
        type: 'success',
        text: `✓ Hesap kaydedildi${profilePatch.score ? ` (${tab} puanı: ${profilePatch.score})` : ''}. Tercih sayfasında otomatik dolar.`,
      })
      setTimeout(() => setSavedMsg(null), 4500)
    } catch (e) {
      setSavedMsg({ type: 'error', text: e.message || 'Kayıt hata' })
    } finally {
      setSaving(false)
    }
  }

  // Aktif tab field listesi
  const activeFields = useMemo(() => {
    if (tab === 'TYT') return TYT_FIELDS
    if (tab === 'SAY') return AYT_SAY_FIELDS
    if (tab === 'EA')  return AYT_EA_FIELDS
    if (tab === 'SÖZ') return AYT_SOZ_FIELDS
    if (tab === 'DİL') return AYT_DIL_FIELDS
    if (tab === 'DGS') return DGS_FIELDS
    return []
  }, [tab])

  return (
    <>
      <BackgroundScene />

      <div className="space-y-5 max-w-4xl mx-auto">
        {/* Hero */}
        <div className="text-center mb-2">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-16 h-16 mx-auto mb-3 rounded-2xl bg-gradient-to-br from-amber-500 via-orange-500 to-rose-500 flex items-center justify-center shadow-2xl shadow-amber-500/30"
          >
            <Calculator size={32} className="text-white" />
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl md:text-4xl font-display font-bold text-white mb-2"
          >
            YKS <span className="gradient-text">Hesap Makinesi</span> 2025
          </motion.h1>
          <p className="text-sm text-slate-400 max-w-xl mx-auto">
            Netlerini yaz, yaklaşık <strong className="text-amber-300">YKS yerleştirme puanını</strong> öğren.
            Kaydedersen Tercih sayfasında otomatik dolar.
          </p>
        </div>

        {/* Sınav türü tabları */}
        <div className="card !p-2">
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-1">
            {TABS.map((t) => {
              const active = tab === t.id
              return (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`px-2 py-2.5 rounded-lg text-xs font-medium transition ${
                    active
                      ? `bg-gradient-to-br ${t.color} text-white shadow-lg`
                      : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                  }`}
                >
                  <div className="font-display font-bold">{t.label}</div>
                  <div className={`text-[9px] ${active ? 'text-white/80' : 'text-slate-500'}`}>{t.desc}</div>
                </button>
              )
            })}
          </div>
        </div>

        <div className="grid lg:grid-cols-[1fr,380px] gap-4">
          {/* Sol: Net girişi */}
          <div className="card space-y-3">
            <div className="flex items-center justify-between border-b border-white/5 pb-2">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <BookOpen size={14} className="text-accent-300" />
                {tab === 'DGS' ? 'DGS Net Girişi' : tab === 'TYT' ? 'TYT Net Girişi' : `TYT + ${tab} Net Girişi`}
              </h3>
              <div className="text-[10px] text-slate-500 flex items-center gap-3">
                <span>D: doğru</span>
                <span>Y: yanlış</span>
                <span>Net = D − 0.25Y</span>
              </div>
            </div>

            {/* TYT zorunlu (DGS hariç) */}
            {tab !== 'DGS' && tab !== 'TYT' && (
              <div className="opacity-90">
                <div className="text-[10px] text-slate-500 uppercase mt-2 mb-1">TYT (zorunlu)</div>
                {TYT_FIELDS.map((f) => (
                  <NetInput key={f.id} field={f} value={data} onChange={setField} />
                ))}
              </div>
            )}

            <div>
              {tab !== 'DGS' && tab !== 'TYT' && (
                <div className="text-[10px] text-slate-500 uppercase mt-2 mb-1">{tab}</div>
              )}
              {activeFields.map((f) => (
                <NetInput key={f.id} field={f} value={data} onChange={setField} />
              ))}
            </div>

            {/* Diploma notu — Tab'a göre 100'lük (YKS) veya 4'lük (DGS) */}
            <div className="pt-2 mt-2 border-t border-white/5">
              {tab === 'DGS' ? (
                <>
                  <label className="text-xs text-slate-300 flex items-center gap-2 mb-1">
                    <GraduationCap size={12} className="text-accent-300" />
                    Önlisans GPA (4'lük sistem)
                    <span className="text-[10px] text-slate-500">örn: 3.20 — boş bırakabilirsin</span>
                  </label>
                  <div className="flex items-center gap-3">
                    <input
                      type="number" min="0" max="4" step="0.01"
                      value={gpa4}
                      onChange={(e) => {
                        const v = e.target.value
                        if (v === '') return setGpa4('')
                        const n = parseFloat(v)
                        if (isNaN(n)) return setGpa4('')
                        setGpa4(String(Math.max(0, Math.min(4, n))))
                      }}
                      placeholder="örn: 3.20"
                      className="input-glass text-sm flex-1"
                    />
                    <div className="text-xs text-slate-400 font-mono w-36 text-right">
                      {aobp > 0 ? (
                        <>
                          <div>AOBP: <span className="text-accent-300">+{aobp.toFixed(1)}</span></div>
                          <div className="text-[10px] text-slate-500">
                            puana eklenir
                          </div>
                        </>
                      ) : (
                        <span className="text-slate-600 text-[10px]">GPA girilmedi</span>
                      )}
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <label className="text-xs text-slate-300 flex items-center gap-2 mb-1">
                    <GraduationCap size={12} className="text-accent-300" />
                    Diploma Notu (100'lük sistem)
                    <span className="text-[10px] text-slate-500">örn: 85 — boş bırakabilirsin</span>
                  </label>
                  <div className="flex items-center gap-3">
                    <input
                      type="number" min="50" max="100" step="0.01"
                      value={diploma100}
                      onChange={(e) => {
                        const v = e.target.value
                        if (v === '') return setDiploma100('')
                        const n = parseFloat(v)
                        if (isNaN(n)) return setDiploma100('')
                        setDiploma100(String(Math.max(0, Math.min(100, n))))
                      }}
                      placeholder="örn: 85"
                      className="input-glass text-sm flex-1"
                    />
                    <div className="text-xs text-slate-400 font-mono w-36 text-right">
                      {obp > 0 ? (
                        <>
                          <div>OBP: <span className="text-accent-300">{obp.toFixed(0)}</span></div>
                          <div className="text-[10px] text-slate-500">
                            +{(obp * OBP_MULT).toFixed(1)} puan
                          </div>
                        </>
                      ) : (
                        <span className="text-slate-600 text-[10px]">diploma girilmedi</span>
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Sağ: Sonuç paneli */}
          <div className="space-y-3">
            <motion.div
              key={result.finalScore.toFixed(2)}
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="card border-amber-500/40 bg-gradient-to-br from-amber-500/10 to-rose-500/10 text-center py-6"
            >
              <div className="text-xs text-slate-400 uppercase tracking-wider">{result.label}</div>
              <div className="text-5xl font-display font-bold mt-2 bg-gradient-to-br from-amber-300 to-rose-400 bg-clip-text text-transparent">
                {result.finalScore > 100 ? result.finalScore.toFixed(2) : '—'}
              </div>
              <div className="text-[10px] text-slate-500 mt-2 flex items-center justify-center gap-2">
                {tab !== 'TYT' && tab !== 'DGS' && result.tytHam > 0 && (
                  <span>TYT ham: {result.tytHam.toFixed(1)}</span>
                )}
                {result.ham > 0 && (
                  <span>{tab} ham: {result.ham.toFixed(1)}</span>
                )}
                {tab === 'DGS' && aobp > 0 && (
                  <span>AOBP: +{aobp.toFixed(1)}</span>
                )}
                {tab !== 'DGS' && obp > 0 && (
                  <span>OBP: +{(obp * OBP_MULT).toFixed(1)}</span>
                )}
              </div>
            </motion.div>

            {/* Yaklaşık olduğunu açıklayan info */}
            <div className="text-[10px] text-slate-500 px-3 py-2 rounded-lg bg-white/5 border border-white/10 flex items-start gap-2">
              <Info size={12} className="text-amber-400 mt-0.5 shrink-0" />
              <span>
                Yaklaşık ÖSYM 2025 katsayıları. Gerçek puan ±5-10 puan farkedebilir
                (norm/standardizasyon nedeniyle).
              </span>
            </div>

            {/* Aksiyonlar */}
            <button
              onClick={handleSave}
              disabled={saving || result.finalScore <= 100}
              className="btn-primary w-full inline-flex items-center justify-center gap-2 disabled:opacity-40"
            >
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
              {isAuthed ? 'Profilime Kaydet' : 'Önce Giriş Yap'}
            </button>

            {savedMsg && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                className={`text-xs px-3 py-2 rounded-lg border ${
                  savedMsg.type === 'success'
                    ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                    : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                }`}
              >
                {savedMsg.text}
              </motion.div>
            )}

            {/* Simulasyon butonu — bu puanla yazılabilecek programları çek */}
            {result.finalScore > 100 && (
              <button
                onClick={runSimulation}
                disabled={simLoading}
                className="w-full inline-flex items-center justify-center gap-2 text-sm px-3 py-2.5 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/40 text-emerald-200 hover:from-emerald-500/30 hover:to-teal-500/30 transition disabled:opacity-40"
              >
                {simLoading ? (
                  <><Loader2 size={14} className="animate-spin" /> Programlar bulunuyor…</>
                ) : (
                  <><Sparkles size={14} /> Bu Puanla Hangi Programları Yazabilirim?</>
                )}
              </button>
            )}

            {simError && (
              <div className="text-xs px-3 py-2 rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/30">
                ⚠️ {simError}
              </div>
            )}

            {result.finalScore > 100 && isAuthed && (
              <Link
                to="/recommend"
                className="btn-ghost w-full inline-flex items-center justify-center gap-2 text-sm"
              >
                <ListChecks size={14} /> Tercih Sayfasına Geç
                <ArrowRight size={12} />
              </Link>
            )}
          </div>
        </div>

        {/* === SİMULASYON SONUÇLARI === */}
        <AnimatePresence>
          {simResults && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-3"
            >
              <div className="card border-emerald-500/30 bg-emerald-500/5">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
                      <Sparkles size={18} className="text-white" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-white">
                        {result.finalScore.toFixed(2)} puanla yazabileceğin programlar
                      </div>
                      <div className="text-xs text-slate-400">
                        Güvenli: {simResults.safe?.length || 0} · Hedef: {simResults.target?.length || 0} · Üst seviye: {simResults.reach?.length || 0}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => setSimResults(null)}
                    className="text-xs text-slate-400 hover:text-white"
                  >
                    Kapat
                  </button>
                </div>
                {simResults.notes && (
                  <div className="text-xs text-slate-500 mt-2 pt-2 border-t border-white/5">
                    💡 {simResults.notes}
                  </div>
                )}
              </div>

              {[
                { key: 'safe', label: 'Güvenli', color: 'from-emerald-500 to-emerald-700', desc: 'Garanti yerleşeceğin' },
                { key: 'target', label: 'Hedef', color: 'from-amber-500 to-orange-600', desc: 'Sana en uygun' },
                { key: 'reach', label: 'Üst Seviye', color: 'from-rose-500 to-fuchsia-600', desc: 'Denemeye değer' },
              ].map((cat) => {
                const items = (simResults[cat.key] || []).slice(0, 8)
                if (items.length === 0) return null
                return (
                  <div key={cat.key} className="card">
                    <div className="flex items-center gap-2 mb-3">
                      <div className={`w-7 h-7 rounded-lg bg-gradient-to-br ${cat.color} flex items-center justify-center text-xs font-bold text-white`}>
                        {items.length}
                      </div>
                      <div>
                        <h3 className="font-semibold text-sm text-white">{cat.label}</h3>
                        <p className="text-[10px] text-slate-400">{cat.desc}</p>
                      </div>
                    </div>
                    <div className="grid sm:grid-cols-2 gap-2">
                      {items.map((it, i) => (
                        <div key={i} className="text-xs p-2.5 rounded-lg bg-white/[0.03] border border-white/5">
                          <div className="font-medium text-white truncate">{it.department_name}</div>
                          <div className="flex items-center gap-2 mt-0.5 text-[10px] text-slate-400">
                            <Building2 size={9} /> {it.university_name}
                            {it.city && <><MapPin size={9} className="ml-1" /> {it.city}</>}
                          </div>
                          <div className="flex items-center gap-3 mt-1 text-[10px]">
                            {it.last_year_base_rank != null && (
                              <span className="font-mono text-cyber-cyan flex items-center gap-0.5">
                                <Hash size={8} /> {Number(it.last_year_base_rank).toLocaleString('tr')}
                              </span>
                            )}
                            {it.last_year_base_score != null && (
                              <span className="font-mono text-accent-300 flex items-center gap-0.5">
                                <TrendingUp size={8} /> {Number(it.last_year_base_score).toFixed(2)}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}

              <div className="text-center">
                <Link
                  to="/recommend"
                  className="btn-ghost inline-flex items-center gap-2 text-sm"
                >
                  Tüm sonuçları Tercih sayfasında gör <ArrowRight size={12} />
                </Link>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  )
}
