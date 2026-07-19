/**
 * YKS Hesap Makinesi 2026
 *
 * Yaklaşık ÖSYM katsayıları (2026 dönemi, her ders için ayrı ağırlık):
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
 *       + 2.91×Tarih-2 + 2.91×Coğrafya-2 + 2.67×Felsefe + 4.0×Din
 *
 * YDT-DİL (max ~500):
 *   100 + 3.0×Yabancı Dil (tek formülde)
 *
 * YERLEŞTİRME (lisans):
 *   = 100 + TYT_netleri×(~1.32) + AYT_netleri×(~3.0) + OBP×0.12  (ÖSYM tek formülü)
 *   TYT'nin %40 ağırlığı küçük katsayılara gömülüdür; tam net + tam OBP = 560
 *
 * OBP (Ortaöğretim Başarı Puanı):
 *   100'lük diploma notu × 5 = OBP (max 500)
 *   Örn: 85 → OBP 425, +51 puan eklenir
 *
 * DGS (önlisans → lisans) — 50 say + 50 söz soru; üç puan türü:
 *   SAY = 100 + 4.0×Say + 2.6×Söz | EA = 3.3/3.3 | SÖZ = 2.6/4.0 (+AÖBP)
 *   AOBP = (GPA × 25) × 0.5  (4'lük GPA)
 *
 * ALES — 50 say + 50 söz, net = D−Y/4; puan STANDART-puan → sabit ham→puan YOK.
 *   Makine NET odaklı: ağırlıklı net SAY 0.75/0.25, SÖZ 0.25/0.75, EA 0.50/0.50.
 * LGS — 90 soru, net = D−Y/3 (3 yanlış!); MSP ≈ 100 + (ağırlıklı_net/270)×400,
 *   ders katsayısı Tr/Mat/Fen=4, İnkılap/Din/İng=1.
 * AGS — 6 alt test (15/15/6/6/30/8=80), net = D−Y/4; NET-ONLY (standart-puan +
 *   ilk uygulama → güvenilir puan tahmini yok).
 * (Ayrıntılı sabit/açıklama her sınavın kendi tanımının yanında — bkz. ALES_/LGS_/AGS_.)
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
  Hash, TrendingUp, School,
} from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import { useAuth } from '../contexts/AuthContext'
import { getUserProfile, updateUserProfile } from '../firebase'
import { apiFetch } from '../lib/api'
import { TERCIH_YILI } from '../lib/donem'

// === Yaklaşık ÖSYM katsayıları (ders-bazlı)
const TYT_BIAS = 100
const AYT_BIAS = 100
const OBP_MULT = 0.12          // ÖSYM yerleştirme puanına eklenen OBP katsayısı

// TYT ders katsayıları — SADECE TYT puanı için (max 100+400=500)
const TYT_COEF = {
  tyt_tr:  3.3,   // 40 × 3.3 = 132
  tyt_sos: 3.4,   // 20 × 3.4 = 68
  tyt_mat: 3.3,   // 40 × 3.3 = 132
  tyt_fen: 3.4,   // 20 × 3.4 = 68
}

// ÖSYM SAY/EA/SÖZ/DİL yerleştirme puanı TEK formüldür:
//   PUAN = 100 + Σ(TYT netleri × ~1.32) + Σ(AYT netleri × ~3.0) + OBP×0.12
// TYT'nin %40 ağırlığı bu küçük katsayılara GÖMÜLÜdür (max 160 + 240 = 400).
// ESKİ HATA: AYT katsayıları tek-formül değerleriyken üstüne bir de
// 0.4×TYT + 0.6×AYT uygulanıyordu → çifte indirim → tam nette 460 çıkıyordu.
const TYT_PLACEMENT_COEF = {
  tyt_tr:  1.32,  // 40 × 1.32 = 52.8
  tyt_sos: 1.36,  // 20 × 1.36 = 27.2
  tyt_mat: 1.32,  // 40 × 1.32 = 52.8
  tyt_fen: 1.36,  // 20 × 1.36 = 27.2   → TYT bloğu max ≈ 160
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
  ayt_din:  4.0,   // 6 × 4.0 = 24 → AYT bloğu toplam ≈ 240 (5.33 tavanı taşırıyordu)
}
const AYT_DIL_COEF = { ayt_dil: 3.0 }  // 80 × 3.0 = 240 (tek formülde TYT 160 + 240 = 400)

// DGS: puan türüne göre ağırlık farklıdır — sayısalcıya SAY testi,
// sözelciye SÖZ testi daha çok puan getirir (ÖSYM standart puan modeli
// yaklaşıklaması; kesin değer aday kitlesine göre değişir).
// 2021+ format: 50 sayısal + 50 sözel soru.
const DGS_COEF_BY_TYPE = {
  SAY: { dgs_say: 4.0, dgs_soz: 2.6 },  // 50×4.0 + 50×2.6 = 330 → max ≈ 430 + AÖBP
  EA:  { dgs_say: 3.3, dgs_soz: 3.3 },
  SÖZ: { dgs_say: 2.6, dgs_soz: 4.0 },
}

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

// === DGS (önlisans mezunu için lisans geçişi) — 2021+ format: 50+50 soru
const DGS_FIELDS = [
  { id: 'dgs_say', label: 'DGS Sayısal',          max: 50 },
  { id: 'dgs_soz', label: 'DGS Sözel (Türkçe)',   max: 50 },
]

// === KPSS GY-GK (lisans P3 / önlisans P93 / ortaöğretim P94 — aynı oturum yapısı)
const KPSS_FIELDS = [
  { id: 'kpss_gy', label: 'Genel Yetenek', max: 60 },
  { id: 'kpss_gk', label: 'Genel Kültür',  max: 60 },
]
// Yaklaşık model: 40 + 0.5×(GY+GK neti) → tam net = 100. Gerçek puan ÖSYM
// standart sapma normalizasyonuyla hesaplanır; sapma birkaç puan olabilir.
const KPSS_BASE = 40
const KPSS_COEF = 0.5

// === ALES (ÖSYM) — 50 Sayısal + 50 Sözel, net = D − Y/4. Puan STANDART-puandır
// (o dönemin aday ort/std'sine bağlı) → sabit ham→puan katsayısı YOK; bu yüzden
// makine NET odaklıdır (net kesin), sahte puan üretmez. Ağırlıklar resmi
// 2026-ALES/1 kılavuzu Bölüm 3.9: SAY 0.75/0.25, SÖZ 0.25/0.75, EA 0.50/0.50
// (internetteki 0.70/0.30 YANLIŞ — eski varsayılan).
const ALES_FIELDS = [
  { id: 'ales_say', label: 'Sayısal', max: 50 },
  { id: 'ales_soz', label: 'Sözel',   max: 50 },
]
const ALES_WEIGHTS = {
  SAY: { ales_say: 0.75, ales_soz: 0.25 },
  EA:  { ales_say: 0.50, ales_soz: 0.50 },
  SÖZ: { ales_say: 0.25, ales_soz: 0.75 },
}

// === LGS (MEB Merkezi Sınav) — 90 soru, net = D − Y/3 (3 yanlış 1 doğru götürür,
// YKS'deki 1/4 DEĞİL!). Tek puan türü: MSP 100-500. Resmi puan her dersin netini
// ülke ort/std'ye göre standartlaştırır → sınav öncesi yaklaşık. Ders katsayıları
// (standart-puan ağırlığı): Türkçe/Matematik/Fen = 4, İnkılap/Din/İngilizce = 1.
// Yaklaşık MSP = 100 + (ağırlıklı_net / 270) × 400  (tüm boş→100, tüm doğru→500).
const LGS_PEN = 1 / 3
const LGS_FIELDS = [
  { id: 'lgs_tr',  label: 'Türkçe',         max: 20, pen: LGS_PEN, k: 4 },
  { id: 'lgs_mat', label: 'Matematik',      max: 20, pen: LGS_PEN, k: 4 },
  { id: 'lgs_fen', label: 'Fen Bilimleri',  max: 20, pen: LGS_PEN, k: 4 },
  { id: 'lgs_ink', label: 'İnkılap Tarihi', max: 10, pen: LGS_PEN, k: 1 },
  { id: 'lgs_din', label: 'Din Kültürü',    max: 10, pen: LGS_PEN, k: 1 },
  { id: 'lgs_ing', label: 'İngilizce',      max: 10, pen: LGS_PEN, k: 1 },
]
const LGS_MAX_WN = 270  // 4×(20+20+20) + 1×(10+10+10)

// === AGS (MEB Akademi Giriş Sınavı, 2026, ÖSYM) — öğretmenlik seçme sınavı.
// 1. oturum: 6 alt test = 80 soru, net = D − Y/4. Puan STANDART-puan + sınav ilk
// uygulamalardan → güvenilir puan tahmini YOK (resmi doğrulama: can_build=false).
// Makine yalnız NET verir (kural kesin). ÖABT AYRI 2. oturumdur, buraya dahil değil.
const AGS_FIELDS = [
  { id: 'ags_soz', label: 'Sözel Yetenek',      max: 15 },
  { id: 'ags_say', label: 'Sayısal Yetenek',    max: 15 },
  { id: 'ags_tar', label: 'Tarih',              max: 6 },
  { id: 'ags_cog', label: 'Türkiye Coğrafyası', max: 6 },
  { id: 'ags_egt', label: 'Eğitim Bilimleri',   max: 30 },
  { id: 'ags_mev', label: 'Mevzuat',            max: 8 },
]

const TABS = [
  { id: 'TYT', label: 'TYT', desc: 'Önlisans / temel', color: 'from-purple-500 to-violet-500' },
  { id: 'SAY', label: 'AYT-SAY', desc: 'Sayısal lisans', color: 'from-blue-500 to-cyan-400' },
  { id: 'EA',  label: 'AYT-EA',  desc: 'Eşit Ağırlık', color: 'from-emerald-500 to-teal-400' },
  { id: 'SÖZ', label: 'AYT-SÖZ', desc: 'Sözel lisans',  color: 'from-rose-500 to-pink-400' },
  { id: 'DİL', label: 'YDT-DİL', desc: 'Yabancı dil',   color: 'from-amber-500 to-orange-400' },
  { id: 'DGS', label: 'DGS',     desc: 'Önlisans→Lisans', color: 'from-fuchsia-500 to-purple-500' },
  { id: 'KPSS', label: 'KPSS',   desc: 'Memurluk (GY-GK)', color: 'from-sky-500 to-indigo-500' },
  { id: 'ALES', label: 'ALES',   desc: 'Akademik / YL', color: 'from-indigo-500 to-blue-500' },
  { id: 'LGS',  label: 'LGS',    desc: 'Liseye geçiş',  color: 'from-green-500 to-emerald-500' },
  { id: 'AGS',  label: 'AGS',    desc: 'Öğretmenlik',   color: 'from-teal-500 to-cyan-500' },
]

// === Net hesaplama: doğru - penalty*yanlış
// penalty: ÖSYM/YKS/ALES/DGS/KPSS/AGS = 0.25 (4 yanlış 1 doğru),
//          LGS = 1/3 (3 yanlış 1 doğru). Field bazlı `pen` ile geçilir.
// Negatif net NEGATİF kalır (ÖSYM kuralı): 0'a kırpılırsa çok yanlışlı
// derslerde toplam puan olduğundan yüksek çıkar.
function netOf(dogru, yanlis, penalty = 0.25) {
  const d = parseFloat(dogru) || 0
  const y = parseFloat(yanlis) || 0
  return d - penalty * y
}

// === Diploma puanı → OBP
//   YKS (lise diploması): 100'lük sistem (50-100), × 5 = OBP (250-500)
//     Örn: 85 → 425, 100 → 500
//   DGS (önlisans GPA): 4'lük sistem (0-4), × 25 = 100'lük, × 0.5 sonra
//     AOBP = GPA × 25 × 0.5 (DGS yerleştirmeye eklenen)
function diploma100ToObp(diploma100) {
  const d = parseFloat(diploma100)
  // Diploma notu 50-100 aralığındadır (min OBP 250); 50 altı henüz geçerli
  // bir not değil → 0 (yazarken ara değerler puana karışmasın)
  if (!d || d < 50 || d > 100) return 0
  return d * 5  // 50→250, 100→500
}
function gpa4ToAobp(gpa4) {
  const d = parseFloat(gpa4)
  if (!d || d < 0 || d > 4) return 0
  return d * 25 * 0.5  // 4 → 50 puan eklenir
}

// === Ham puan hesabı (ders bazlı katsayılar). Negatif netler de toplama
// katılır (ÖSYM kuralı) — sadece n>0 alınsaydı çok yanlışlı ders yok sayılır,
// puan olduğundan yüksek çıkardı.
function weightedSum(nets, coefMap) {
  let total = 0
  let anyNet = false
  for (const [key, coef] of Object.entries(coefMap)) {
    const n = parseFloat(nets[key]) || 0
    if (n !== 0) {
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

function aytWeighted(nets, type) {
  const coefMap =
    type === 'SAY' ? AYT_SAY_COEF
    : type === 'EA' ? AYT_EA_COEF
    : type === 'SÖZ' ? AYT_SOZ_COEF
    : type === 'DİL' ? AYT_DIL_COEF
    : null
  if (!coefMap) return 0
  return weightedSum(nets, coefMap)  // max ≈ 240
}

// === KPSS puanı (yaklaşık P3/P93/P94 — GY+GK, düzeye göre etiket değişir)
function kpssScore(nets) {
  const gy = parseFloat(nets.kpss_gy) || 0
  const gk = parseFloat(nets.kpss_gk) || 0
  if (gy <= 0 && gk <= 0) return 0
  return KPSS_BASE + KPSS_COEF * (gy + gk)
}

// === DGS puanları — üç tür birden (SAY/EA/SÖZ farklı ağırlıklarla)
function dgsScores(nets, aobp) {
  const out = {}
  for (const [type, coef] of Object.entries(DGS_COEF_BY_TYPE)) {
    const w = weightedSum(nets, coef)
    out[type] = w > 0 ? 100 + w + aobp : 0
  }
  return out
}

// === SAY/EA/SÖZ/DİL yerleştirme puanı — ÖSYM tek formülü:
//   100 + TYT netleri×küçük katsayı (max 160) + AYT netleri (max 240) + OBP×0.12
//   Tam net + tam OBP = 100 + 400 + 60 = 560 ✓
function placementScore(nets, type, obp) {
  const aytW = aytWeighted(nets, type)
  if (aytW <= 0) return 0
  const tytW = weightedSum(nets, TYT_PLACEMENT_COEF)
  return 100 + tytW + aytW + obp * OBP_MULT
}

// === ALES ağırlıklı net (puan türü başına). ALES puanı standart-puandır → sabit
// ham→puan yok; ağırlıklı net göreli bir göstergedir (0-50 bandı, resmi 0.75/0.25
// ağırlıklarıyla). Kesin puan sınav sonrası ÖSYM'ce belirlenir.
function alesWeightedNets(nets) {
  const say = nets.ales_say || 0
  const soz = nets.ales_soz || 0
  const out = {}
  for (const [type, w] of Object.entries(ALES_WEIGHTS)) {
    out[type] = (say !== 0 || soz !== 0) ? w.ales_say * say + w.ales_soz * soz : 0
  }
  return out
}

// === LGS puanı (MSP, yaklaşık 100-500). Doğrusal: 100 + (ağırlıklı_net/270)×400.
// Resmi yöntem her dersin netini ayrı standartlaştırır; bu birinci-derece yaklaşım.
function lgsScore(nets) {
  let wn = 0
  let any = false
  for (const f of LGS_FIELDS) {
    const n = nets[f.id] || 0
    if (n !== 0) any = true
    wn += (f.k || 1) * n
  }
  // Taban 100'ün altına inmesin (negatif ağırlıklı nette bile MSP min 100)
  return any ? Math.max(100, 100 + (wn / LGS_MAX_WN) * 400) : 0
}

// === AGS toplam net (kesin). Puan yok — standart-puan + ilk uygulama.
function agsTotalNet(nets) {
  return AGS_FIELDS.reduce((s, f) => s + (nets[f.id] || 0), 0)
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
  const net = netOf(d, y, field.pen ?? 0.25)

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
      <div className={`w-16 text-right text-sm font-mono ${net < 0 ? 'text-rose-400' : 'text-accent-300'}`}>
        {total > 0 ? net.toFixed(2) : '-'}
      </div>
    </div>
  )
}


/** DGS: hesaplanan puanlarla geçilebilecek lisans programları */
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
  const [uniPref, setUniPref] = useState('all') // all | Devlet | Vakıf — profilden dolar
  const [siralama, setSiralama] = useState(null) // YKS puanından tahmini başarı sırası

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
        else if (p?.profile?.examTrack === 'DGS') setTab('DGS')
        else if (p?.profile?.examTrack === 'KPSS') setTab('KPSS')
        if (p?.profile?.preferredUniType) setUniPref(p.profile.preferredUniType)
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
      ...AYT_SOZ_FIELDS, ...AYT_DIL_FIELDS, ...DGS_FIELDS, ...KPSS_FIELDS,
      ...ALES_FIELDS, ...LGS_FIELDS, ...AGS_FIELDS,
    ]
    const seen = new Set()
    for (const f of allFields) {
      if (seen.has(f.id)) continue
      seen.add(f.id)
      out[f.id] = netOf(data[`${f.id}_d`], data[`${f.id}_y`], f.pen ?? 0.25)
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
    if (tab === 'KPSS') {
      const s = kpssScore(nets)
      return {
        scoreType: 'KPSS',
        ham: s,
        finalScore: s,
        label: 'KPSS GY-GK Puanı (yaklaşık)',
      }
    }
    if (tab === 'DGS') {
      const scores = dgsScores(nets, aobp)  // {SAY, EA, SÖZ} — AÖBP dahil
      const best = Math.max(scores.SAY, scores.EA, scores['SÖZ'])
      return {
        scoreType: 'DGS',
        ham: best > 0 ? best - aobp : 0,
        dgsScores: scores,
        finalScore: best,
        label: 'DGS Puanları (SAY / EA / SÖZ)',
      }
    }
    if (tab === 'ALES') {
      const wn = alesWeightedNets(nets)  // {SAY, EA, SÖZ} ağırlıklı net
      const best = Math.max(wn.SAY, wn.EA, wn['SÖZ'])
      return {
        scoreType: 'ALES',
        alesNets: wn,
        sayNet: nets.ales_say || 0,
        sozNet: nets.ales_soz || 0,
        finalScore: best,
        label: 'ALES Ağırlıklı Net (SAY / EA / SÖZ)',
      }
    }
    if (tab === 'LGS') {
      const s = lgsScore(nets)
      return { scoreType: 'LGS', finalScore: s, label: 'LGS Puanı (MSP · yaklaşık)' }
    }
    if (tab === 'AGS') {
      return { scoreType: 'AGS', finalScore: agsTotalNet(nets), label: 'AGS Toplam Net' }
    }
    // SAY/EA/SÖZ/DİL — ÖSYM tek formülü (TYT katkısı katsayılara gömülü)
    const finalScore = placementScore(nets, tab, obp)
    return {
      scoreType: tab,
      ham: finalScore > 0 ? finalScore - obp * OBP_MULT : 0,
      tytHam: tytH,
      finalScore,
      label: `${tab} Yerleştirme Puanı`,
    }
  }, [nets, obp, aobp, tab])

  // YKS yerleştirme puanı → tahmini başarı sırası (puanın yanında göster).
  // Sadece YKS türlerinde (SAY/EA/SÖZ/DİL/TYT) ve geçerli puanda çağrılır.
  useEffect(() => {
    const yks = ['TYT', 'SAY', 'EA', 'SÖZ', 'DİL'].includes(tab)
    if (!yks || result.finalScore <= 100) { setSiralama(null); return }
    let cancelled = false
    const puan = result.finalScore.toFixed(2)
    apiFetch(`/api/v1/hesap/siralama?puan=${puan}&tur=${encodeURIComponent(tab)}`)
      .then((d) => { if (!cancelled) setSiralama(d) })
      .catch(() => { if (!cancelled) setSiralama(null) })
    return () => { cancelled = true }
  }, [tab, result.finalScore])

  // Üni türü değişince mevcut simülasyon sonucunu otomatik yenile —
  // eskiden eski liste ekranda kalıyordu ("filtre çalışmıyor" izlenimi)
  useEffect(() => {
    if (simResults) runSimulation()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uniPref])

  // === Simulasyon: bu puanla hangi programlar yazılır? ===
  async function runSimulation() {
    // isYksPlacement render kapsamında (aşağıda) tanımlı; runSimulation tıklamada
    // çalıştığından çağrı anında ilklenmiş olur.
    if (result.finalScore <= 100 || !isYksPlacement) {
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
          // Profildeki üni türü tercihi (üstteki Tümü/Devlet/Vakıf seçiminden)
          preferred_uni_types: uniPref === 'all' ? [] : [uniPref],
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
      // Eğer tab AYT türü ve hesap geçerliyse, profile.scoreType ve score'u güncelle.
      // rank'ı da SIFIRLA: yeni puana eski sıra yapışık kalırsa backend rank'ı puana
      // ÖNCELEDİĞİ için yanlış öneri çıkıyordu; null → puandan tahmin edilir.
      if (['SAY', 'EA', 'SÖZ', 'DİL'].includes(tab) && result.finalScore > 100) {
        profilePatch.scoreType = tab
        profilePatch.score = parseFloat(result.finalScore.toFixed(2))
        profilePatch.rank = null
      } else if (tab === 'TYT' && result.finalScore > 100) {
        profilePatch.scoreType = 'TYT'
        profilePatch.score = parseFloat(result.finalScore.toFixed(2))
        profilePatch.rank = null
      } else if (tab === 'KPSS' && result.finalScore > KPSS_BASE) {
        // KPSS puanı profile ayrı alanda tutulur (YKS scoreType'ı bozmaz)
        profilePatch.kpss = {
          score: parseFloat(result.finalScore.toFixed(2)),
          updatedAt: Date.now(),
        }
      } else if (tab === 'DGS' && result.finalScore > 100 && result.dgsScores) {
        // En yüksek çıkan türü profile yaz
        const bestType = ['SAY', 'EA', 'SÖZ'].reduce((a, b) =>
          (result.dgsScores[a] >= result.dgsScores[b] ? a : b))
        profilePatch.dgs = {
          score: parseFloat(result.dgsScores[bestType].toFixed(2)),
          type: bestType,
          updatedAt: Date.now(),
        }
      } else if (tab === 'AGS' && result.finalScore > 0) {
        // Profil sayfasının AGS bloğu profile.ags.net bekler — aynı şema
        profilePatch.ags = {
          net: parseFloat(result.finalScore.toFixed(2)),
          updatedAt: Date.now(),
        }
      }
      await updateUserProfile(user.uid, profilePatch)
      // Tercih sayfası yalnız YKS/DGS/KPSS puanını kullanır (feedsTercih); ALES/
      // LGS/AGS netleri sadece hesap makinesine geri yüklenir — yanlış vaat verme.
      setSavedMsg({
        type: 'success',
        text: `✓ Hesap kaydedildi${profilePatch.score ? ` (${tab} puanı: ${profilePatch.score})` : ''}.${feedsTercih ? ' Tercih sayfasında otomatik dolar.' : ''}`,
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
    if (tab === 'KPSS') return KPSS_FIELDS
    if (tab === 'ALES') return ALES_FIELDS
    if (tab === 'LGS') return LGS_FIELDS
    if (tab === 'AGS') return AGS_FIELDS
    return []
  }, [tab])

  // Bu sekmeler YKS yerleştirme puanı üretir → "hangi programları yazarım"
  // simülasyonu yalnız bunlarda anlamlı (ALES/LGS/AGS öneri motoruna bağlanmaz).
  const isYksPlacement = ['TYT', 'SAY', 'EA', 'SÖZ', 'DİL'].includes(tab)
  // Puanı Tercih (/oneriler) sayfasına taşınan sekmeler — YKS + KPSS + DGS
  // (Recommend.jsx profile.kpss/dgs.score'u yükler). ALES/LGS/AGS taşınmaz.
  const feedsTercih = isYksPlacement || tab === 'KPSS' || tab === 'DGS'
  // Geçerli bir sonuç oluştu mu (kaydet/gösterim eşiği sekmeye göre değişir)
  const hasResult =
    tab === 'KPSS' ? result.finalScore > KPSS_BASE
    : tab === 'ALES' || tab === 'AGS' ? result.finalScore > 0
    : result.finalScore > 100  // YKS puanları ve LGS MSP (taban 100)

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
            {['DGS', 'KPSS', 'ALES', 'LGS', 'AGS'].includes(tab) ? tab : 'YKS'}{' '}
            <span className="gradient-text">Hesap Makinesi</span> {TERCIH_YILI}
          </motion.h1>
          <p className="text-sm text-slate-400 max-w-xl mx-auto">
            Netlerini yaz,{' '}
            <strong className="text-amber-300">
              {tab === 'KPSS' ? 'yaklaşık KPSS GY-GK puanını'
                : tab === 'DGS' ? 'yaklaşık DGS yerleştirme puanını'
                : tab === 'ALES' ? 'ALES netini ve ağırlıklı netini'
                : tab === 'LGS' ? 'yaklaşık LGS puanını (MSP)'
                : tab === 'AGS' ? 'AGS netini'
                : 'yaklaşık YKS yerleştirme puanını'}
            </strong> hesapla.{feedsTercih ? ' Kaydedersen Tercih sayfasında otomatik dolar.' : ''}
          </p>
        </div>

        {/* Sınav türü tabları */}
        <div className="card !p-2">
          <div className="grid grid-cols-3 sm:grid-cols-5 gap-1">
            {TABS.map((t) => {
              const active = tab === t.id
              return (
                <button
                  key={t.id}
                  onClick={() => {
                    setTab(t.id)
                    // Eski sekmenin simülasyon sonuçları yeni sekmenin puanıyla
                    // yan yana kalmasın (yanıltıcı eşleşme)
                    setSimResults(null)
                    setSimError('')
                  }}
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
                {isYksPlacement && tab !== 'TYT' ? `TYT + ${tab} Net Girişi`
                  : tab === 'KPSS' ? 'KPSS GY-GK Net Girişi'
                  : `${tab} Net Girişi`}
              </h3>
              <div className="text-[10px] text-slate-500 flex items-center gap-3">
                <span>D: doğru</span>
                <span>Y: yanlış</span>
                <span>{tab === 'LGS' ? 'Net = D − Y/3' : 'Net = D − 0.25Y'}</span>
              </div>
            </div>

            {/* TYT zorunlu — yalnız YKS AYT puan türlerinde (SAY/EA/SÖZ/DİL) */}
            {isYksPlacement && tab !== 'TYT' && (
              <div className="opacity-90">
                <div className="text-[10px] text-slate-500 uppercase mt-2 mb-1">TYT (zorunlu)</div>
                {TYT_FIELDS.map((f) => (
                  <NetInput key={f.id} field={f} value={data} onChange={setField} />
                ))}
              </div>
            )}

            <div>
              {isYksPlacement && tab !== 'TYT' && (
                <div className="text-[10px] text-slate-500 uppercase mt-2 mb-1">{tab}</div>
              )}
              {activeFields.map((f) => (
                <NetInput key={f.id} field={f} value={data} onChange={setField} />
              ))}
            </div>

            {/* Diploma notu — yalnız YKS (100'lük diploma) ve DGS (4'lük GPA); diğerlerinde yok */}
            {['TYT', 'SAY', 'EA', 'SÖZ', 'DİL', 'DGS'].includes(tab) && (
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
            )}
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
              {result.dgsScores ? (
                <div className="mt-3 grid grid-cols-3 gap-2 px-4">
                  {['SAY', 'EA', 'SÖZ'].map((t) => (
                    <div key={t} className="rounded-xl bg-black/20 py-3">
                      <div className="text-[10px] text-slate-400">{t}</div>
                      <div className="text-2xl font-display font-bold bg-gradient-to-br from-amber-300 to-rose-400 bg-clip-text text-transparent">
                        {result.dgsScores[t] > 100 ? result.dgsScores[t].toFixed(1) : '—'}
                      </div>
                    </div>
                  ))}
                </div>
              ) : result.alesNets ? (
                <div className="mt-3 grid grid-cols-3 gap-2 px-4">
                  {['SAY', 'EA', 'SÖZ'].map((t) => (
                    <div key={t} className="rounded-xl bg-black/20 py-3">
                      <div className="text-[10px] text-slate-400">{t}</div>
                      <div className="text-2xl font-display font-bold bg-gradient-to-br from-amber-300 to-rose-400 bg-clip-text text-transparent">
                        {result.alesNets[t] > 0 ? result.alesNets[t].toFixed(1) : '—'}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-5xl font-display font-bold mt-2 bg-gradient-to-br from-amber-300 to-rose-400 bg-clip-text text-transparent">
                  {/* KPSS 40-100; YKS 100 tabanlı; LGS MSP 100-500; AGS toplam net 0-80 */}
                  {hasResult ? result.finalScore.toFixed(2) : '—'}
                </div>
              )}
              {/* Tahmini başarı sırası — sadece YKS türlerinde (puan → sıra) */}
              {isYksPlacement && hasResult && siralama && (
                <div className="mt-2 text-sm text-slate-300">
                  ≈ <span className="font-display font-bold text-amber-300">
                    {siralama.tahmini_sira.toLocaleString('tr-TR')}.
                  </span> başarı sırası
                  <span className="block text-[10px] text-slate-500 mt-0.5">
                    tahmini{siralama.sinir ? ' · puan veri aralığının ucunda, sapma yüksek' : ''}
                  </span>
                </div>
              )}
              <div className="text-[10px] text-slate-500 mt-2 flex items-center justify-center gap-2 flex-wrap">
                {tab === 'ALES' && (result.sayNet > 0 || result.sozNet > 0) && (
                  <span>Sayısal net: {result.sayNet.toFixed(2)} · Sözel net: {result.sozNet.toFixed(2)}</span>
                )}
                {isYksPlacement && tab !== 'TYT' && result.tytHam > 0 && (
                  <span>TYT ham: {result.tytHam.toFixed(1)}</span>
                )}
                {result.ham > 0 && (
                  <span>{tab} ham: {result.ham.toFixed(1)}</span>
                )}
                {tab === 'DGS' && aobp > 0 && (
                  <span>AOBP: +{aobp.toFixed(1)}</span>
                )}
                {isYksPlacement && obp > 0 && (
                  <span>OBP: +{(obp * OBP_MULT).toFixed(1)}</span>
                )}
              </div>
            </motion.div>

            {/* KPSS: aktif dönem kadro arama */}
            {/* Kadro/program arama Tercih sayfasına taşındı — Hesap yalnız hesaplar */}
            {(tab === 'KPSS' || tab === 'DGS') && (
              <Link
                to="/oneriler"
                className="card !py-3 flex items-center gap-3 text-sm border-accent-500/30 bg-accent-500/5 hover:bg-accent-500/10 transition"
              >
                <Sparkles size={16} className="text-accent-300 shrink-0" />
                <span className="flex-1 text-slate-200">
                  {tab === 'KPSS'
                    ? 'Bu puanla başvurabileceğin kadroları Tercih sayfasında ara — bölüm, çoklu şehir ve geçmiş taban eşleşmesiyle.'
                    : 'Bu puanla geçebileceğin lisans programlarını Tercih sayfasında ara — geçiş yolları ve bölüm filtresiyle.'}
                </span>
                <ArrowRight size={14} className="text-accent-300 shrink-0" />
              </Link>
            )}


            {/* Yaklaşık/kesin olduğunu açıklayan info — sekmeye göre */}
            <div className="text-[10px] text-slate-500 px-3 py-2 rounded-lg bg-white/5 border border-white/10 flex items-start gap-2">
              <Info size={12} className="text-amber-400 mt-0.5 shrink-0" />
              <span>
                {tab === 'ALES'
                  ? 'Net kesindir. ALES puanı standart-puandır (o dönemki aday ortalama/std\'sine bağlı) → kesin puan ancak ÖSYM sonucuyla belli olur. Ağırlıklar resmi 2026-ALES/1 kılavuzu (SAY 0.75/0.25, SÖZ 0.25/0.75, EA 0.50/0.50).'
                  : tab === 'LGS'
                  ? 'Net kuralı D − Y/3 (3 yanlış 1 doğru) kesindir. MSP (100-500) yaklaşıktır — resmi puan her dersin netini ülke ortalama/std\'sine göre standartlaştırır; kesin puan ve yüzdelik dilim sınav sonrası belli olur.'
                  : tab === 'AGS'
                  ? 'Yalnız net gösterilir (kural kesin: D − Y/4). AGS puanı standart-puandır ve sınav ilk uygulamalardan biri → güvenilir puan tahmini yapılamaz; puanı üçüncü-parti sitelerden de doğrulama. ÖABT ayrı 2. oturumdur.'
                  : 'Yaklaşık ÖSYM katsayıları (2026 dönemi). Gerçek puan ±5-10 puan farkedebilir (norm/standardizasyon nedeniyle).'}
              </span>
            </div>

            {/* LGS: yüzdelikle hangi liselere girebilirim → LGS tercih robotu */}
            {tab === 'LGS' && (
              <Link
                to="/lgs"
                className="w-full inline-flex items-center justify-center gap-2 text-sm px-3 py-2.5 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-500/20 border border-emerald-500/40 text-emerald-200 hover:from-green-500/30 hover:to-emerald-500/30 transition"
              >
                <School size={14} /> Bu yüzdelikle hangi liselere girebilirim?
                <ArrowRight size={12} />
              </Link>
            )}

            {/* Aksiyonlar */}
            <button
              onClick={handleSave}
              disabled={saving || !hasResult}
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
            {isYksPlacement && result.finalScore > 100 && (
              <div className="flex items-center justify-center gap-1.5">
                <span className="text-[10px] text-slate-500">Üni türü:</span>
                {[['all', 'Tümü'], ['Devlet', 'Devlet'], ['Vakıf', 'Vakıf']].map(([v, l]) => (
                  <button
                    key={v}
                    onClick={() => setUniPref(v)}
                    className={`rounded-lg px-2.5 py-1 text-[10px] border transition ${
                      uniPref === v
                        ? 'border-accent-500/60 bg-accent-500/15 text-accent-200'
                        : 'border-white/10 text-slate-400 hover:bg-white/10'
                    }`}
                  >
                    {l}
                  </button>
                ))}
              </div>
            )}
            {isYksPlacement && result.finalScore > 100 && (
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

            {/* hasResult: KPSS eşiği KPSS_BASE(40)'tır — sabit >100 KPSS'de linki hiç göstermiyordu */}
            {feedsTercih && hasResult && isAuthed && (
              <Link
                to="/oneriler"
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
                  to="/oneriler"
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
