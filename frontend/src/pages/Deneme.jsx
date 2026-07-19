import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Loader2, Plus, Trash2, TrendingUp, Target, X, LineChart, ArrowRight, Sparkles } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { apiFetch } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import {
  getUserProfile, watchDenemeler, addDeneme, removeDeneme, recordActivity, getKonuIlerleme,
  watchSoruKayit, addSoruKayit, removeSoruKayit,
} from '../firebase'
import { track } from '../lib/analytics'
import { konuLocal, eksikKonular, konuBloklari } from '../lib/konu'
import { tasimaGerekli, damgala } from '../lib/bulutTasima'
import {
  TYT_FIELDS, AYT_FIELDS, KPSS_FIELDS, LGS_FIELDS, DGS_FIELDS,
  denemeAlanlari, denemeHesaplaSinav, diploma100ToObp, gpa4ToAobp,
} from '../lib/yksHesap'

const DENEME_SINAVLAR = ['YKS', 'DGS', 'KPSS', 'LGS']
// Puan türü olan sınavlar (YKS 4 tür, DGS 3 tür); KPSS/LGS'de tür yok
const YKS_TURLER = ['SAY', 'EA', 'SÖZ', 'DİL']
const DGS_TURLER = ['SAY', 'EA', 'SÖZ']
const turlerFor = (s) => (s === 'YKS' ? YKS_TURLER : s === 'DGS' ? DGS_TURLER : null)
// Diploma/GPA girişi olan sınavlar (YKS: 100'lük diploma→OBP, DGS: 4'lük GPA→AÖBP)
const hasDiploma = (s) => s === 'YKS' || s === 'DGS'
// Tüm sınavların ders etiketleri — geçmiş/zayıf ders gösterimi için
const ALL_LABELS = Object.fromEntries(
  [...TYT_FIELDS, ...AYT_FIELDS.SAY, ...AYT_FIELDS.EA, ...AYT_FIELDS.SÖZ, ...AYT_FIELDS.DİL,
    ...KPSS_FIELDS, ...LGS_FIELDS, ...DGS_FIELDS].map((f) => [f.id, { label: f.label, max: f.max }]))
const lsKey = (s) => 'unisense_deneme_' + s
const loadLocal = (s) => { try { return JSON.parse(localStorage.getItem(lsKey(s)) || '[]') } catch { return [] } }
const saveLocal = (s, a) => { try { localStorage.setItem(lsKey(s), JSON.stringify(a)) } catch { /* noop */ } }
// Çözülen soru kaydı — sınav başına ayrı
const soruKey = (s) => 'unisense_soru_' + s
const loadSoru = (s) => { try { return JSON.parse(localStorage.getItem(soruKey(s)) || '[]') } catch { return [] } }
const saveSoru = (s, a) => { try { localStorage.setItem(soruKey(s), JSON.stringify(a)) } catch { /* noop */ } }
// yerel tarih (UTC değil — gece 00-03 TR'de önceki güne kaymasın)
const bugun = () => {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

function Spark({ points }) {
  const pts = points.filter((p) => p != null)
  if (pts.length < 2) return null
  const W = 200, H = 44, P = 4
  const min = Math.min(...pts), range = Math.max(Math.max(...pts) - min, 0.01)
  const co = pts.map((v, i) => ({
    x: P + (i / (pts.length - 1)) * (W - P * 2),
    y: H - P - ((v - min) / range) * (H - P * 2),
  }))
  const d = co.map((c, i) => `${i ? 'L' : 'M'} ${c.x.toFixed(1)} ${c.y.toFixed(1)}`).join(' ')
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} preserveAspectRatio="none">
      <path d={d} fill="none" stroke="url(#g)" strokeWidth="2" />
      <defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stopColor="#3b82f6" /><stop offset="1" stopColor="#8b5cf6" /></linearGradient></defs>
      <circle cx={co[co.length - 1].x} cy={co[co.length - 1].y} r="3" fill="#a78bfa" />
    </svg>
  )
}

export default function Deneme({ embedded = false }) {
  const { user } = useAuth()
  const [sinav, setSinav] = useState('YKS')
  const [type, setType] = useState('SAY')
  const [diploma, setDiploma] = useState('85')
  const [tarih, setTarih] = useState(bugun())
  const [ad, setAd] = useState('')
  const [girdi, setGirdi] = useState({}) // {fieldId: {d, y}}
  const [denemeler, setDenemeler] = useState([])
  const [soruKayit, setSoruKayit] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [showSoru, setShowSoru] = useState(false)
  const [soruF, setSoruF] = useState({ blokIdx: '', konu: '', cozulen: '', dogru: '' })
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState('')
  const [profil, setProfil] = useState(null)
  const [koc, setKoc] = useState('')
  const [kocLoading, setKocLoading] = useState(false)
  const [konuData, setKonuData] = useState(null)

  // Profilden varsayılan sınav + tür + diploma + koç için profil
  useEffect(() => {
    if (!user) return
    getUserProfile(user.uid).then((p) => {
      const pr = p?.profile || {}
      setProfil(pr)
      // switchSinav ile AYNI uyarlama — aksi halde DGS profilinde 100'lük diploma
      // 4'lük GPA alanına sızıyor (AÖBP sessizce 0 oluyordu) ve DİL türü DGS'e taşıyordu
      const s = ['YKS', 'DGS', 'KPSS', 'LGS'].includes(pr.examTrack) ? pr.examTrack : 'YKS'
      setSinav(s)
      const t = turlerFor(s)
      if (t) setType(t.includes(pr.scoreType) ? pr.scoreType : t[0])
      if (s === 'YKS' && pr.diploma) setDiploma(String(pr.diploma))
      else if (s !== 'YKS') setDiploma('')
    }).catch(() => {})
  }, [user])

  // Sınav değiştir — tür ve diploma/GPA yeni sınava uyarlanır, form kapanır
  function switchSinav(s) {
    setSinav(s)
    setShowForm(false); setShowSoru(false)
    setKoc('') // önceki sınavın tavsiyesi yeni sekmede kalmasın
    const t = turlerFor(s)
    if (t && !t.includes(type)) setType(t[0]) // DGS'de DİL yok → SAY'a düş
    setDiploma(s === 'YKS' ? '85' : '') // YKS: 100'lük, DGS: 4'lük GPA (boş başla)
  }

  // Denemeleri yükle — sınav başına ayrı liste; girişli bulut, girişsiz localStorage
  useEffect(() => {
    setGirdi({})
    if (!user) { setDenemeler(loadLocal(sinav)); return }
    const key = lsKey(sinav)
    return watchDenemeler(user.uid, sinav, (items) => {
      if (items == null) { setDenemeler(loadLocal(sinav)); return }
      const local = loadLocal(sinav)
      if (tasimaGerekli(key, items.length === 0, local.length > 0)) {
        // Yalnız SAHİPSİZ (gerçek misafir) veri taşınır — ayna damgası bunu güvence altına alır.
        // Alanları kırp + null/yerel alanları at (rules type:null / uzun ad'ı reddeder).
        for (const d of local) {
          const temiz = {
            sinav: d.sinav || sinav, tarih: String(d.tarih || '').slice(0, 20),
            ad: String(d.ad || 'Deneme').slice(0, 120),
            dersNet: d.dersNet || {}, toplamNet: d.toplamNet || 0, puan: d.puan || 0,
          }
          if (typeof d.type === 'string') temiz.type = d.type.slice(0, 8)
          if (typeof d.sira === 'number') temiz.sira = d.sira
          addDeneme(user.uid, temiz).catch(() => {})
        }
        damgala(key, user.uid)
        setDenemeler(local)
        return
      }
      setDenemeler(items); saveLocal(sinav, items); damgala(key, user.uid)
    })
  }, [user, sinav])

  // Çözülen soru kaydını yükle — sınav başına ayrı; girişli bulut, girişsiz localStorage
  useEffect(() => {
    if (!user) { setSoruKayit(loadSoru(sinav)); return }
    const key = soruKey(sinav)
    return watchSoruKayit(user.uid, sinav, (items) => {
      if (items == null) { setSoruKayit(loadSoru(sinav)); return }
      const local = loadSoru(sinav)
      if (tasimaGerekli(key, items.length === 0, local.length > 0)) {
        for (const s of local) {
          addSoruKayit(user.uid, {
            sinav: s.sinav || sinav, ders: String(s.ders || '').slice(0, 60),
            konu: String(s.konu || '').slice(0, 120), cozulen: s.cozulen || 0,
            dogru: s.dogru || 0, tarih: String(s.tarih || '').slice(0, 20),
          }).catch(() => {})
        }
        damgala(key, user.uid); setSoruKayit(local); return
      }
      setSoruKayit(items); saveSoru(sinav, items); damgala(key, user.uid)
    })
  }, [user, sinav])

  // Seçili sınavın konu listesi (koç tavsiyesi + soru kaydı konu seçimi için)
  useEffect(() => {
    setKonuData(null)
    apiFetch(`/api/v1/konular?sinav=${sinav}`).then(setKonuData).catch(() => {})
  }, [sinav])
  // Konu işaretleri: girişli → bulut (bu cihazda Konular hiç açılmamış olabilir),
  // erişilemezse/girişsiz → localStorage
  const [konuChecked, setKonuChecked] = useState({})
  useEffect(() => {
    let live = true
    if (!user) { setKonuChecked(konuLocal(sinav)); return undefined }
    getKonuIlerleme(user.uid, sinav).then((c) => { if (live) setKonuChecked(c ?? konuLocal(sinav)) })
    return () => { live = false }
  }, [user, sinav])
  const konuDurum = useMemo(() => (konuData ? eksikKonular(konuData, konuChecked) : null), [konuData, konuChecked])
  // Konu bloklarını (grup·ders + konular) soru kaydı seçimi için hazırla
  const bloklar = useMemo(() => konuBloklari(konuData), [konuData])
  // Konu bazında soru çözüm özeti (birden çok kayıt toplanır) — gösterim + AI koç
  const soruOzet = useMemo(() => {
    const m = {}
    for (const s of soruKayit) {
      const k = `${s.ders || ''}|${s.konu || ''}`
      if (!m[k]) m[k] = { ders: s.ders, konu: s.konu, cozulen: 0, dogru: 0 }
      m[k].cozulen += s.cozulen || 0; m[k].dogru += s.dogru || 0
    }
    return Object.values(m).sort((a, b) => b.cozulen - a.cozulen)
  }, [soruKayit])

  const fields = useMemo(() => denemeAlanlari(sinav, type), [sinav, type])
  const canli = useMemo(
    () => denemeHesaplaSinav(sinav, type, girdi, sinav === 'DGS' ? gpa4ToAobp(diploma) : diploma100ToObp(diploma)),
    [sinav, type, girdi, diploma],
  )

  // D/Y girişi — Hesap gibi: D+Y o dersin soru sayısını (max) AŞAMAZ
  function setDY(field, k, v) {
    if (v === '') { setGirdi((p) => ({ ...p, [field.id]: { ...p[field.id], [k]: '' } })); return }
    const raw = Math.max(0, parseInt(v, 10) || 0)
    setGirdi((p) => {
      const cur = p[field.id] || {}
      const other = k === 'd' ? (parseInt(cur.y, 10) || 0) : (parseInt(cur.d, 10) || 0)
      const capped = Math.max(0, Math.min(raw, field.max - other)) // D+Y ≤ max
      return { ...p, [field.id]: { ...cur, [k]: capped } }
    })
  }

  function flash(m) { setToast(m); setTimeout(() => setToast(''), 2500) }

  async function kaydet() {
    const minPuan = sinav === 'KPSS' ? 40 : 100
    if (canli.puan <= minPuan) { flash('Ders netlerini gir'); return }
    setSaving(true)
    let sira = null
    // Tahmini sıra sadece YKS yerleştirme puanında (TYT-only/LGS/KPSS'de sıra verisi yok)
    if (sinav === 'YKS' && canli.puanTuru === type) {
      try {
        const r = await apiFetch(`/api/v1/hesap/siralama?puan=${canli.puan.toFixed(2)}&tur=${encodeURIComponent(type)}`)
        sira = r?.tahmini_sira ?? null
      } catch { /* sıra opsiyonel */ }
    }
    // DİKKAT: null alan YAZMA — firestore.rules strMax('type') alan mevcutsa string
    // şartı koşar; type:null yazmak KPSS/LGS create'ini reddettiriyordu.
    const deneme = {
      sinav, tarih, ad: ad || `${canli.puanTuru} Deneme`,
      ...(turlerFor(sinav) ? { type } : {}),
      dersNet: canli.dersNet, toplamNet: canli.toplamNet, puan: canli.puan,
      ...(sira != null ? { sira } : {}),
    }
    try {
      if (user) await addDeneme(user.uid, deneme)
      else { const a = [...denemeler, { ...deneme, id: 'l' + Date.now() }]; saveLocal(sinav, a); setDenemeler(a) }
      recordActivity(user?.uid).catch(() => {}) // günlük seri (streak)
      track('deneme_kaydedildi', { sinav })
      setGirdi({}); setAd(''); setShowForm(false)
      flash('✓ Deneme kaydedildi')
    } catch (e) { flash(e.message) } finally { setSaving(false) }
  }

  async function sil(d) {
    if (user && !String(d.id).startsWith('l')) { await removeDeneme(user.uid, d.id).catch(() => {}) }
    else { const a = denemeler.filter((x) => x.id !== d.id); saveLocal(sinav, a); setDenemeler(a) }
  }

  // Çözülen soru kaydı ekle — ders/konu Konular listesinden, çözülen + doğru
  async function soruEkle() {
    const blok = bloklar[parseInt(soruF.blokIdx, 10)]
    const cozulen = parseInt(soruF.cozulen, 10) || 0
    const dogru = Math.min(parseInt(soruF.dogru, 10) || 0, cozulen)
    if (!blok || !soruF.konu) { flash('Ders ve konu seç'); return }
    if (cozulen <= 0) { flash('Çözülen soru sayısını gir'); return }
    const ders = blok.grup ? `${blok.grup} ${blok.ders}` : blok.ders
    const kayit = { sinav, ders, konu: soruF.konu, cozulen, dogru, tarih }
    setSaving(true)
    try {
      if (user) await addSoruKayit(user.uid, kayit)
      else { const a = [{ ...kayit, id: 'l' + Date.now(), createdAt: Date.now() }, ...soruKayit]; saveSoru(sinav, a); setSoruKayit(a) }
      recordActivity(user?.uid).catch(() => {})
      track('soru_kaydedildi', { sinav })
      setSoruF({ blokIdx: soruF.blokIdx, konu: '', cozulen: '', dogru: '' }); setShowSoru(false)
      flash('✓ Soru kaydı eklendi')
    } catch (e) { flash(e.message) } finally { setSaving(false) }
  }

  async function soruSil(s) {
    if (user && !String(s.id).startsWith('l')) { await removeSoruKayit(user.uid, s.id).catch(() => {}) }
    else { const a = soruKayit.filter((x) => x.id !== s.id); saveSoru(sinav, a); setSoruKayit(a) }
  }

  // İstatistik: son deneme, trend, en zayıf 3 ders
  const sirali = useMemo(() => [...denemeler].sort((a, b) => (a.tarih || '').localeCompare(b.tarih || '')), [denemeler])
  const son = sirali[sirali.length - 1]
  const zayif = useMemo(() => {
    if (!son?.dersNet) return []
    return Object.entries(son.dersNet)
      .map(([id, net]) => ({ id, net, ...(ALL_LABELS[id] || { label: id, max: 1 }) }))
      .map((x) => ({ ...x, oran: x.net / x.max }))
      .sort((a, b) => a.oran - b.oran).slice(0, 3)
  }, [son])

  const kimDeyisi = () => (turlerFor(sinav) ? `${type} (${sinav})` : sinav)

  // user_context yalnız ilgili sınavın verisini gönderir (DGS'de YKS puanı GİTMESİN)
  function trackUc() {
    const uc = {}
    if (sinav === 'YKS') {
      if (profil?.score) { uc.yks_puan = profil.score; if (profil.scoreType) uc.yks_turu = profil.scoreType }
      if (profil?.rank) uc.yks_sira = profil.rank
    }
    return uc
  }

  // AI Koç — deneme geçmişi + zayıf ders + işaretlenmemiş konulara göre tavsiye.
  // NOT: /ask query max 500 karakter — prompt kısa + değişken veri sınırlı.
  async function kocIste() {
    if (!sirali.length && !soruKayit.length) return
    setKocLoading(true); setKoc('')
    const parcalar = [`${kimDeyisi()} öğrencisiyim (${sinav}).`]
    if (sirali.length) {
      const sonlar = sirali.slice(-3).map((d) => `${Math.round(d.toplamNet)} net`).join(', ')
      const zayifStr = zayif.map((z) => z.label).join(', ') || '—'
      parcalar.push(`Son deneme netlerim: ${sonlar}. Zayıf derslerim: ${zayifStr}.`)
    }
    // Çok soru çözüp doğruluğu düşük konular → AI "bu konudan daha çöz / tekrar et" desin
    const dusukSoru = soruOzet.filter((o) => o.cozulen >= 5 && o.dogru / o.cozulen < 0.6)
      .slice(0, 3).map((o) => `${o.konu} %${Math.round((o.dogru / o.cozulen) * 100)}`).join(', ')
    if (dusukSoru) parcalar.push(`Çözdüğüm ama doğruluğum düşük konular: ${dusukSoru}.`)
    const eksik = konuDurum?.eksik?.slice(0, 3).map((e) => e.konu).join(', ') || ''
    if (eksik) parcalar.push(`Hiç çalışmadığım konular: ${eksik}.`)
    let q = `${parcalar.join(' ')} Bu ${sinav} verilerine göre KISA maddeler halinde çalışma tavsiyesi ver: hangi konudan daha çok soru çözmeliyim, öncelik ve net artışı.`
    if (q.length > 490) q = q.slice(0, 490)
    const uc = trackUc()
    try {
      const r = await apiFetch('/api/v1/ask', {
        method: 'POST',
        body: { query: q, ...(Object.keys(uc).length ? { user_context: uc } : {}) },
      })
      setKoc(r?.text || 'Tavsiye üretilemedi.')
    } catch (e) { setKoc('Tavsiye alınamadı: ' + e.message) } finally { setKocLoading(false) }
  }

  return (
    <>
      {!embedded && <BackgroundScene />}
      {!embedded && (
        <Seo title="Çalışmalarım — Deneme & Çözülen Soru Takibi | UniSense"
          description="Denemelerini ve konu konu çözdüğün soruları tek yerde kaydet; AI Koç netlerine ve soru çözümüne göre hangi konuya odaklanman gerektiğini söyler — ücretsiz."
          path="/deneme" />
      )}
      {toast && <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl glass text-sm">{toast}</div>}
      <div className="max-w-3xl mx-auto space-y-5">
        {!embedded && (
          <div className="text-center">
            <h1 className="text-3xl md:text-4xl font-display font-bold text-white mb-1 flex items-center justify-center gap-2">
              <LineChart className="text-accent-300" /> Çalışmalarım
            </h1>
            <p className="text-slate-400 text-sm">Denemelerini ve konu konu çözdüğün soruları kaydet — AI Koç ikisini de okur.</p>
          </div>
        )}

        {/* Sınav seçici — her sınavın denemeleri ayrı tutulur */}
        <div className="flex justify-center">
          <div className="inline-flex gap-1 p-1 rounded-xl bg-white/5 border border-white/10">
            {DENEME_SINAVLAR.map((s) => (
              <button key={s} onClick={() => switchSinav(s)}
                className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition ${sinav === s ? 'bg-gradient-to-r from-brand-500 to-accent-500 text-white' : 'text-slate-300 hover:text-white'}`}>{s}</button>
            ))}
          </div>
        </div>

        {/* Özet + son deneme */}
        {son && (
          <div className="card">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div>
                <div className="text-[11px] text-slate-500 uppercase tracking-wider">Son deneme · {son.ad}</div>
                <div className="flex items-baseline gap-3 mt-1">
                  <span className="text-3xl font-display font-bold gradient-text">{son.puan?.toFixed(1)}</span>
                  <span className="text-sm text-slate-400 font-mono">{son.toplamNet?.toFixed(1)} net</span>
                  {son.sira && <span className="text-sm text-accent-300 font-mono">~{son.sira.toLocaleString('tr')}. sıra</span>}
                </div>
              </div>
              {son.sira && (
                <Link to="/oneriler" className="btn-primary text-sm inline-flex items-center gap-1.5">
                  Bu sırayla bölümler <ArrowRight size={15} />
                </Link>
              )}
            </div>
            {sirali.length >= 2 && (
              <div className="mt-3 pt-3 border-t border-white/5">
                <div className="text-[11px] text-slate-500 mb-1 flex items-center gap-1"><TrendingUp size={11} /> Net trendi ({sirali.length} deneme)</div>
                <Spark points={sirali.map((d) => d.toplamNet)} />
              </div>
            )}
            {zayif.length > 0 && (
              <div className="mt-3 pt-3 border-t border-white/5">
                <div className="text-[11px] text-slate-500 mb-1.5 flex items-center gap-1"><Target size={11} /> En zayıf 3 ders (son deneme)</div>
                <div className="flex flex-wrap gap-1.5">
                  {zayif.map((z) => (
                    <span key={z.id} className="text-[11px] px-2 py-1 rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/25">
                      {z.label}: {z.net.toFixed(1)}/{z.max}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* AI Koç — deneme + çözülen soru + konulara göre kişisel tavsiye */}
        {(sirali.length > 0 || soruKayit.length > 0) && (
          <div className="card">
            <div className="flex items-center justify-between gap-2 mb-2">
              <div className="text-sm font-semibold text-white flex items-center gap-2">
                <Sparkles size={16} className="text-accent-300" /> AI Koç
              </div>
              {user ? (
                <button onClick={kocIste} disabled={kocLoading}
                  className="btn-primary text-xs inline-flex items-center gap-1.5 disabled:opacity-50">
                  {kocLoading ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />} Tavsiye al
                </button>
              ) : (
                <Link to="/giris" className="text-xs text-accent-300">Giriş yap →</Link>
              )}
            </div>
            {!user ? (
              <p className="text-xs text-slate-400">Giriş yaparsan koç; denemelerine, çözdüğün sorulara ve zayıf konularına göre sana özel çalışma tavsiyesi verir.</p>
            ) : koc ? (
              <div className="text-[13.5px] text-slate-200 whitespace-pre-wrap leading-relaxed">{koc}</div>
            ) : (
              <p className="text-xs text-slate-500">Deneme + soru çözümü + işaretlemediğin konulara göre “hangi konudan daha çok çöz” tavsiyesi için “Tavsiye al”a bas.</p>
            )}
          </div>
        )}

        {/* Ekleme butonları — Deneme veya Çözdüğüm soru */}
        {!showForm && !showSoru && (
          <div className="grid grid-cols-2 gap-2">
            <button onClick={() => { setShowForm(true); setShowSoru(false) }} className="btn-primary inline-flex items-center justify-center gap-2">
              <Plus size={16} /> Deneme ekle
            </button>
            <button onClick={() => { setShowSoru(true); setShowForm(false) }} className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl glass glass-hover text-slate-100 text-sm font-semibold">
              <Plus size={16} /> Çözdüğüm soru
            </button>
          </div>
        )}

        {/* Deneme formu */}
        {showForm && (
          <div className="card space-y-3">
            <div className="flex items-center justify-between">
              <div className="font-semibold text-white text-sm">Yeni deneme</div>
              <button onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X size={16} /></button>
            </div>
            <div className="flex flex-wrap gap-2 items-end">
              {turlerFor(sinav) && (
                <div>
                  <label className="text-[11px] text-slate-400">Puan türü</label>
                  <div className="flex gap-1 mt-1">
                    {turlerFor(sinav).map((t) => (
                      <button key={t} onClick={() => setType(t)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${type === t ? 'bg-gradient-to-r from-brand-500 to-accent-500 text-white' : 'bg-white/5 text-slate-300'}`}>{t}</button>
                    ))}
                  </div>
                </div>
              )}
              <div><label className="text-[11px] text-slate-400">Tarih</label>
                <input type="date" value={tarih} onChange={(e) => setTarih(e.target.value)} className="input-glass block mt-1 text-sm" /></div>
              {hasDiploma(sinav) && (
                <div><label className="text-[11px] text-slate-400">{sinav === 'DGS' ? "Önlisans not ort. (4'lük)" : 'Diploma notu'}</label>
                  <input type="number" step={sinav === 'DGS' ? '0.01' : '1'} value={diploma} onChange={(e) => setDiploma(e.target.value)} placeholder={sinav === 'DGS' ? '3.20' : '85'} className="input-glass block mt-1 text-sm w-24" /></div>
              )}
              <div className="flex-1 min-w-[120px]"><label className="text-[11px] text-slate-400">Deneme adı (ops.)</label>
                <input value={ad} onChange={(e) => setAd(e.target.value)} placeholder="Deneme 5" maxLength={120} className="input-glass block mt-1 text-sm w-full" /></div>
            </div>

            {/* Ders D/Y girişleri */}
            <div className="grid sm:grid-cols-2 gap-2">
              {fields.map((f) => {
                const g = girdi[f.id] || {}
                const dNum = parseInt(g.d, 10) || 0
                const yNum = parseInt(g.y, 10) || 0
                const net = (dNum - (f.pen || 0.25) * yNum)
                return (
                  <div key={f.id} className="flex items-center gap-2 bg-white/[0.03] border border-white/8 rounded-lg px-2.5 py-1.5">
                    <span className="text-[12px] text-slate-300 flex-1 truncate">{f.label} <span className="text-slate-600">/{f.max}</span></span>
                    <input type="number" min="0" max={f.max - yNum} value={g.d ?? ''} onChange={(e) => setDY(f, 'd', e.target.value)} placeholder="D" title={`En fazla ${f.max - yNum} doğru`} className="input-glass w-12 text-center text-sm !py-1" />
                    <input type="number" min="0" max={f.max - dNum} value={g.y ?? ''} onChange={(e) => setDY(f, 'y', e.target.value)} placeholder="Y" title={`En fazla ${f.max - dNum} yanlış`} className="input-glass w-12 text-center text-sm !py-1" />
                    <span className="text-[11px] font-mono w-10 text-right text-accent-300">{(dNum || yNum) ? net.toFixed(1) : '–'}</span>
                  </div>
                )
              })}
            </div>

            <div className="flex items-center justify-between pt-1">
              <div className="text-sm">
                <span className="text-slate-400">Toplam: </span>
                <span className="font-mono text-white">{canli.toplamNet.toFixed(1)} net</span>
                <span className="text-slate-500"> · </span>
                <span className="font-mono gradient-text font-bold">{canli.puan > 0 ? canli.puan.toFixed(1) : '–'} {canli.puanTuru} puan</span>
              </div>
              <button onClick={kaydet} disabled={saving} className="btn-primary text-sm inline-flex items-center gap-1.5 disabled:opacity-50">
                {saving ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />} Kaydet
              </button>
            </div>
          </div>
        )}

        {/* Çözdüğüm soru formu — ders/konu Konular listesinden */}
        {showSoru && (
          <div className="card space-y-3">
            <div className="flex items-center justify-between">
              <div className="font-semibold text-white text-sm">Çözdüğüm soru</div>
              <button onClick={() => setShowSoru(false)} className="text-slate-500 hover:text-white"><X size={16} /></button>
            </div>
            {bloklar.length === 0 ? (
              <p className="text-xs text-slate-500">Konu listesi yükleniyor…</p>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[11px] text-slate-400">Ders</label>
                    <select value={soruF.blokIdx} onChange={(e) => setSoruF({ ...soruF, blokIdx: e.target.value, konu: '' })}
                      className="input-glass block mt-1 text-sm w-full">
                      <option value="">Seç…</option>
                      {bloklar.map((b, i) => <option key={i} value={i}>{b.grup ? `${b.grup} · ${b.ders}` : b.ders}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-400">Konu</label>
                    <select value={soruF.konu} onChange={(e) => setSoruF({ ...soruF, konu: e.target.value })}
                      disabled={soruF.blokIdx === ''} className="input-glass block mt-1 text-sm w-full disabled:opacity-50">
                      <option value="">Seç…</option>
                      {(bloklar[parseInt(soruF.blokIdx, 10)]?.konular || []).map((k) => <option key={k} value={k}>{k}</option>)}
                    </select>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 items-end">
                  <div><label className="text-[11px] text-slate-400">Çözülen</label>
                    <input type="number" min="0" value={soruF.cozulen} onChange={(e) => setSoruF({ ...soruF, cozulen: e.target.value })} placeholder="40" className="input-glass block mt-1 text-sm w-20" /></div>
                  <div><label className="text-[11px] text-slate-400">Doğru</label>
                    <input type="number" min="0" value={soruF.dogru} onChange={(e) => setSoruF({ ...soruF, dogru: e.target.value })} placeholder="30" className="input-glass block mt-1 text-sm w-20" /></div>
                  <div><label className="text-[11px] text-slate-400">Tarih</label>
                    <input type="date" value={tarih} onChange={(e) => setTarih(e.target.value)} className="input-glass block mt-1 text-sm" /></div>
                  <button onClick={soruEkle} disabled={saving} className="btn-primary text-sm inline-flex items-center gap-1.5 disabled:opacity-50 ml-auto">
                    {saving ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />} Kaydet
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* Çözdüğüm sorular — konu bazında toplam + doğruluk */}
        {soruOzet.length > 0 && (
          <div className="space-y-2">
            <div className="text-[11px] uppercase tracking-wider text-slate-500">Çözdüğüm sorular (konu bazında)</div>
            {soruOzet.map((o, i) => {
              const oran = o.cozulen ? Math.round((o.dogru / o.cozulen) * 100) : 0
              const renk = oran >= 70 ? 'text-emerald-300' : oran >= 50 ? 'text-amber-300' : 'text-rose-300'
              return (
                <div key={i} className="card !py-2.5 flex items-center gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="text-sm text-white truncate">{o.konu} <span className="text-[10px] text-slate-500">{o.ders}</span></div>
                  </div>
                  <div className="text-right shrink-0 font-mono text-sm">
                    <span className="text-white">{o.dogru}/{o.cozulen}</span>
                    <span className={`text-xs ${renk}`}> · %{oran}</span>
                  </div>
                </div>
              )
            })}
            <div className="text-[10px] text-slate-600 px-1">Silmek için: aynı konuya yeni kayıt eklersen toplanır. Tek tek silme geçmiş listesinden.</div>
          </div>
        )}

        {/* Soru kaydı geçmişi (tekil kayıtlar — silinebilir) */}
        {soruKayit.length > 0 && (
          <div className="space-y-2">
            <div className="text-[11px] uppercase tracking-wider text-slate-500">Soru kayıtları ({soruKayit.length})</div>
            {soruKayit.map((s) => (
              <div key={s.id} className="card !py-2 flex items-center gap-3">
                <div className="text-[11px] text-slate-500 font-mono w-20 shrink-0">{s.tarih}</div>
                <div className="min-w-0 flex-1"><div className="text-sm text-white truncate">{s.konu} <span className="text-[10px] text-slate-500">{s.ders}</span></div></div>
                <div className="text-right shrink-0 font-mono text-xs text-slate-300">{s.dogru}/{s.cozulen}</div>
                <button onClick={() => soruSil(s)} className="text-slate-600 hover:text-rose-400 shrink-0"><Trash2 size={14} /></button>
              </div>
            ))}
          </div>
        )}

        {/* Deneme geçmişi */}
        {sirali.length > 0 && (
          <div className="space-y-2">
            <div className="text-[11px] uppercase tracking-wider text-slate-500">Geçmiş ({sirali.length})</div>
            {[...sirali].reverse().map((d) => (
              <div key={d.id} className="card !py-2.5 flex items-center gap-3">
                <div className="text-[11px] text-slate-500 font-mono w-20 shrink-0">{d.tarih}</div>
                <div className="min-w-0 flex-1">
                  <div className="text-sm text-white truncate">{d.ad} <span className="text-[10px] text-slate-500">{d.type || d.sinav || sinav}</span></div>
                </div>
                <div className="text-right shrink-0 font-mono text-sm">
                  <span className="text-white">{d.puan?.toFixed(1)}</span>
                  <span className="text-slate-500 text-xs"> · {d.toplamNet?.toFixed(1)} net</span>
                  {d.sira && <div className="text-[11px] text-accent-300">~{d.sira.toLocaleString('tr')}. sıra</div>}
                </div>
                <button onClick={() => sil(d)} className="text-slate-600 hover:text-rose-400 shrink-0"><Trash2 size={14} /></button>
              </div>
            ))}
          </div>
        )}

        {sirali.length === 0 && soruKayit.length === 0 && !showForm && !showSoru && (
          <div className="card text-center py-8 text-sm text-slate-400">
            Henüz kaydın yok. <b className="text-white">Deneme ekle</b> ile net/puan takip et, ya da <b className="text-white">Çözdüğüm soru</b> ile konu konu çözümünü not et — AI Koç ikisini de okur. 📈
          </div>
        )}

        <div className="text-[11px] text-slate-600 text-center px-2">
          Puan/sıra TAHMİNÎDİR (yaklaşık ÖSYM katsayıları + program tabanları). {user ? 'Denemelerin hesabına kaydolur.' : 'Giriş yaparsan cihazlar arası senkronlanır.'}
        </div>
      </div>
    </>
  )
}
