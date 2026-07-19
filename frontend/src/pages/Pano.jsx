import { useState, useEffect, useMemo, useCallback } from 'react'
import { LayoutDashboard, Play, Pause, RotateCcw, Trophy, Flame, Clock, ListChecks, LineChart, Layers, Sparkles, Loader2, Mail, Check } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { useAuth } from '../contexts/AuthContext'
import { getIstatistik, sureEkle, recordActivity, getUserProfile, setEmailReminders, dogruCevapEkle } from '../firebase'
import { apiFetch } from '../lib/api'
import { track } from '../lib/analytics'
import { hesaplaXP, seviyeBilgi, ROZETLER, kazanilanRozetler, guestStats } from '../lib/oyun'

const ODAK = 25 * 60
const MOLA = 5 * 60
// Günün Sorusu — sınav yoluna göre ders seti (profildeki examTrack'e göre)
const SORU_DERSLERI = {
  YKS: 'Matematik, Türkçe, Fizik, Kimya, Biyoloji, Tarih, Coğrafya, Felsefe, Din Kültürü',
  DGS: 'Matematik (sayısal akıl yürütme) veya Türkçe (sözel akıl yürütme)',
  KPSS: 'Genel Yetenek (Matematik, Türkçe) veya Genel Kültür (Tarih, Coğrafya, Vatandaşlık)',
  LGS: 'Türkçe, Matematik, Fen Bilimleri, T.C. İnkılap Tarihi, Din Kültürü veya İngilizce',
}
const mmss = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`

function guestSureEkle(dk, ders) {
  let s
  try { s = JSON.parse(localStorage.getItem('unisense_sure') || '{}') } catch { s = {} }
  const today = new Date().toISOString().slice(0, 10)
  s.sureDk = (s.sureDk || 0) + dk
  s.sureHafta = s.sureHafta || {}; s.sureHafta[today] = (s.sureHafta[today] || 0) + dk
  if (ders) { s.dersSure = s.dersSure || {}; s.dersSure[ders] = (s.dersSure[ders] || 0) + dk }
  localStorage.setItem('unisense_sure', JSON.stringify(s))
}

// AI cevabından çoktan seçmeli soruyu ayrıştır (JSON). Bozuksa null → ham metin gösterilir.
function parseSoru(text) {
  try {
    const m = String(text).match(/\{[\s\S]*\}/)
    if (!m) return null
    const o = JSON.parse(m[0])
    const sec = o.secenekler || {}
    if (!o.soru || !sec.A || !sec.B || !sec.C || !sec.D || !o.dogru) return null
    const dogru = String(o.dogru).trim().toUpperCase().charAt(0)
    if (!'ABCD'.includes(dogru)) return null
    return { ders: o.ders || '', soru: String(o.soru), secenekler: { A: sec.A, B: sec.B, C: sec.C, D: sec.D }, dogru, aciklama: o.aciklama || '' }
  } catch { return null }
}

export default function Pano({ embedded = false }) {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [mod, setMod] = useState('odak') // odak | mola
  const [kalan, setKalan] = useState(ODAK)
  const [calisiyor, setCalisiyor] = useState(false)
  const [ders, setDers] = useState('')
  const [toast, setToast] = useState('')
  const [soru, setSoru] = useState(null)       // {ders, soru, secenekler, dogru, aciklama}
  const [soruHam, setSoruHam] = useState('')   // ayrıştırılamazsa ham metin (fallback)
  const [secildi, setSecildi] = useState(null) // seçilen şık (A/B/C/D)
  const [gsLoading, setGsLoading] = useState(false)
  const [emailOn, setEmailOn] = useState(false)

  const yukle = useCallback(async () => {
    setStats(user ? await getIstatistik(user.uid) : guestStats())
  }, [user])
  useEffect(() => { yukle() }, [yukle])

  // Günün sorusu — bugünkü soruyu + cevap durumunu cache'ten yükle
  useEffect(() => {
    try {
      const c = JSON.parse(localStorage.getItem('unisense_gunsoru') || 'null')
      if (c && c.date === new Date().toISOString().slice(0, 10)) {
        if (c.soru) { setSoru(c.soru); setSecildi(c.secildi || null) }
        else if (c.ham) setSoruHam(c.ham)
      }
    } catch { /* noop */ }
  }, [])

  // E-posta hatırlatma tercihini yükle (girişli)
  useEffect(() => {
    if (!user) return
    getUserProfile(user.uid).then((p) => setEmailOn(!!p?.emailReminders)).catch(() => {})
  }, [user])

  async function emailToggle() {
    const v = !emailOn
    setEmailOn(v)
    await setEmailReminders(user.uid, v).catch(() => setEmailOn(!v))
  }

  async function gunSorusu() {
    if (!user) return
    // Günlük fetch limiti — hem Gemini kotasını hem XP-farm'ı sınırlar
    const bugun = new Date().toISOString().slice(0, 10)
    let sayac = { date: bugun, n: 0 }
    try { const c = JSON.parse(localStorage.getItem('unisense_gunsoru_sayi') || 'null'); if (c && c.date === bugun) sayac = c } catch { /* noop */ }
    if (sayac.n >= 10) { setToast('Bugünlük soru limitine ulaştın — yarın devam! 🌙'); setTimeout(() => setToast(''), 2500); return }
    localStorage.setItem('unisense_gunsoru_sayi', JSON.stringify({ date: bugun, n: sayac.n + 1 }))
    setGsLoading(true); setSoru(null); setSoruHam(''); setSecildi(null)
    let track = 'YKS'
    try { const p = await getUserProfile(user.uid); track = SORU_DERSLERI[p?.profile?.examTrack] ? p.profile.examTrack : 'YKS' } catch { /* varsayılan YKS */ }
    const q = `${track} sınavına hazırlanan bir öğrenci için SADECE şu derslerden birinden akademik bir çoktan seçmeli soru üret: `
      + `${SORU_DERSLERI[track]}. `
      + 'Soru tamamen KONU BİLGİSİNE dayalı olsun; üniversite/tercih/taban puan/sıralama/endeks verisiyle İLGİSİZ olmalı. '
      + 'Sana verilen bağlamı YOK SAY, kendi genel bilginle üret. '
      + 'SADECE şu JSON formatını döndür, öncesinde/sonrasında HİÇBİR metin, kaynak veya açıklama yazma: '
      + '{"ders":"Matematik","soru":"...","secenekler":{"A":"...","B":"...","C":"...","D":"..."},"dogru":"B","aciklama":"..."}'
    try {
      const r = await apiFetch('/api/v1/ask', { method: 'POST', body: { query: q } })
      const text = r?.text || ''
      const parsed = parseSoru(text)
      if (parsed) {
        setSoru(parsed)
        localStorage.setItem('unisense_gunsoru', JSON.stringify({ date: bugun, soru: parsed, secildi: null }))
      } else {
        setSoruHam(text || 'Üretilemedi.')
        localStorage.setItem('unisense_gunsoru', JSON.stringify({ date: bugun, ham: text }))
      }
      recordActivity(user.uid).catch(() => {})
    } catch (e) { setSoruHam('Alınamadı: ' + e.message) } finally { setGsLoading(false) }
  }

  function cevapla(harf) {
    if (secildi || !soru) return
    setSecildi(harf)
    try {
      const bugun = new Date().toISOString().slice(0, 10)
      localStorage.setItem('unisense_gunsoru', JSON.stringify({ date: bugun, soru, secildi: harf }))
    } catch { /* noop */ }
    if (harf === soru.dogru) {
      if (user) dogruCevapEkle(user.uid).catch(() => {})
      else { try { localStorage.setItem('unisense_dogru', String(Number(localStorage.getItem('unisense_dogru') || 0) + 1)) } catch { /* noop */ } }
      track('gunun_soru_dogru', { ders: soru.ders })
      setToast('🎉 Doğru! +10 XP'); setTimeout(() => setToast(''), 2500)
      yukle() // XP'yi tazele
    } else {
      track('gunun_soru_yanlis', { ders: soru.ders })
    }
  }

  // Sayaç
  useEffect(() => {
    if (!calisiyor) return undefined
    const t = setInterval(() => setKalan((k) => Math.max(0, k - 1)), 1000)
    return () => clearInterval(t)
  }, [calisiyor])

  // Blok bitti
  useEffect(() => {
    if (kalan !== 0 || !calisiyor) return
    setCalisiyor(false)
    if (mod === 'odak') {
      const dk = ODAK / 60
      if (user) sureEkle(user.uid, dk, ders.trim()).catch(() => {})
      else guestSureEkle(dk, ders.trim())
      recordActivity(user?.uid).catch(() => {})
      track('pomodoro_tamamlandi', { ders: ders.trim() || null })
      setToast('🎉 25 dk odak tamam! Kısa mola.')
      setTimeout(() => setToast(''), 2500)
      setMod('mola'); setKalan(MOLA)
      yukle()
    } else {
      setMod('odak'); setKalan(ODAK)
    }
  }, [kalan, calisiyor, mod, ders, user, yukle])

  function sifirla() { setCalisiyor(false); setKalan(mod === 'odak' ? ODAK : MOLA) }
  function modDegis(m) { setCalisiyor(false); setMod(m); setKalan(m === 'odak' ? ODAK : MOLA) }

  const xp = useMemo(() => (stats ? hesaplaXP(stats) : 0), [stats])
  const sv = useMemo(() => seviyeBilgi(xp), [xp])
  const kazanilan = useMemo(() => new Set(kazanilanRozetler(stats || {}).map((r) => r.id)), [stats])
  const buHaftaDk = useMemo(() => {
    if (!stats?.sureHafta) return 0
    const now = Date.now(); let dk = 0
    for (const [d, m] of Object.entries(stats.sureHafta)) if (now - new Date(d).getTime() < 7 * 864e5) dk += m
    return dk
  }, [stats])
  const saat = (dk) => (dk >= 60 ? `${(dk / 60).toFixed(1)} sa` : `${dk} dk`)

  const ozet = [
    { Icon: ListChecks, renk: 'text-emerald-300', ad: 'Konu', deger: stats?.konuDone ?? 0 },
    { Icon: LineChart, renk: 'text-accent-300', ad: 'Deneme', deger: stats?.denemeSayisi ?? 0 },
    { Icon: Layers, renk: 'text-violet-300', ad: 'Kart', deger: stats?.kartSayisi ?? 0 },
    { Icon: Flame, renk: 'text-rose-300', ad: 'En uzun seri', deger: `${stats?.streakLongest ?? 0} gün` },
    { Icon: Clock, renk: 'text-amber-300', ad: 'Bu hafta', deger: saat(buHaftaDk) },
    { Icon: Clock, renk: 'text-sky-300', ad: 'Toplam süre', deger: saat(stats?.sureDk ?? 0) },
  ]

  return (
    <>
      {!embedded && <BackgroundScene />}
      {!embedded && (
        <Seo title="Çalışma Panom — İlerleme, Süre ve Rozetler | UniSense"
          description="Pomodoro ile çalış, XP kazan, rozet topla; konu, deneme ve çalışma saatini tek panoda gör." path="/pano" noindex />
      )}
      {toast && <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl glass text-sm">{toast}</div>}
      <div className="max-w-3xl mx-auto space-y-5">
        {!embedded && (
          <div className="text-center">
            <h1 className="text-3xl md:text-4xl font-display font-bold text-white mb-1 flex items-center justify-center gap-2">
              <LayoutDashboard className="text-sky-300" /> Çalışma Panom
            </h1>
            <p className="text-slate-400 text-sm">Pomodoro ile çalış, ilerlemeni ve rozetlerini gör.</p>
          </div>
        )}

        {/* Pomodoro */}
        <div className="card text-center">
          <div className="inline-flex gap-1 p-1 rounded-xl bg-white/5 border border-white/10 mb-3">
            <button onClick={() => modDegis('odak')} className={`px-3 py-1 rounded-lg text-xs font-semibold ${mod === 'odak' ? 'bg-gradient-to-r from-brand-500 to-accent-500 text-white' : 'text-slate-300'}`}>Odak 25'</button>
            <button onClick={() => modDegis('mola')} className={`px-3 py-1 rounded-lg text-xs font-semibold ${mod === 'mola' ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white' : 'text-slate-300'}`}>Mola 5'</button>
          </div>
          <div className="text-5xl md:text-6xl font-display font-bold gradient-text tabular-nums">{mmss(kalan)}</div>
          <input value={ders} onChange={(e) => setDers(e.target.value)} placeholder="Hangi ders? (ops.)"
            className="input-glass text-sm text-center mt-3 mx-auto block w-48" />
          <div className="flex items-center justify-center gap-2 mt-3">
            <button onClick={() => setCalisiyor((c) => !c)} className="btn-primary text-sm inline-flex items-center gap-1.5 px-5">
              {calisiyor ? <><Pause size={15} /> Duraklat</> : <><Play size={15} /> Başlat</>}
            </button>
            <button onClick={sifirla} className="text-sm inline-flex items-center gap-1.5 px-3 py-2 rounded-xl glass glass-hover text-slate-300"><RotateCcw size={15} /> Sıfırla</button>
          </div>
        </div>

        {/* XP / Seviye */}
        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center font-bold text-white">{sv.seviye}</div>
              <div>
                <div className="text-sm font-semibold text-white">Seviye {sv.seviye}</div>
                <div className="text-[11px] text-slate-500">{sv.toplam} XP toplam</div>
              </div>
            </div>
            <div className="text-[11px] text-slate-400">{sv.mevcut}/{sv.gereken} XP</div>
          </div>
          <div className="h-2 rounded-full bg-white/10 overflow-hidden">
            <div className="h-full rounded-full bg-gradient-to-r from-amber-400 to-orange-500 transition-all duration-500" style={{ width: `${sv.oran}%` }} />
          </div>
        </div>

        {/* Günün Sorusu — YKS derslerinden interaktif; doğru bilirsen +10 XP */}
        {user && (
          <div className="card">
            <div className="flex items-center justify-between gap-2 mb-2">
              <div className="text-sm font-semibold text-white flex items-center gap-2"><Sparkles size={16} className="text-accent-300" /> Günün Sorusu</div>
              <button onClick={gunSorusu} disabled={gsLoading} className="btn-primary text-xs inline-flex items-center gap-1.5 disabled:opacity-50">
                {gsLoading ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />} {(soru || soruHam) ? 'Yeni soru' : 'Getir'}
              </button>
            </div>
            {soru ? (
              <div>
                {soru.ders && <div className="text-[10px] uppercase tracking-wider text-accent-300/80 mb-1">{soru.ders}</div>}
                <div className="text-[14px] text-white whitespace-pre-wrap mb-3">{soru.soru}</div>
                <div className="space-y-1.5">
                  {['A', 'B', 'C', 'D'].map((harf) => {
                    const dogruSik = harf === soru.dogru
                    let cls = 'bg-white/[0.03] border-white/8 text-slate-200 hover:bg-white/5'
                    if (secildi) {
                      if (dogruSik) cls = 'bg-emerald-500/15 border-emerald-500/40 text-emerald-200'
                      else if (secildi === harf) cls = 'bg-rose-500/15 border-rose-500/40 text-rose-200'
                      else cls = 'bg-white/[0.02] border-white/8 text-slate-500'
                    }
                    return (
                      <button key={harf} onClick={() => cevapla(harf)} disabled={!!secildi}
                        className={`w-full text-left text-[13.5px] px-3 py-2 rounded-lg border flex items-center gap-2 transition ${cls}`}>
                        <span className="font-bold shrink-0">{harf})</span>
                        <span className="flex-1">{soru.secenekler[harf]}</span>
                        {secildi && dogruSik && <Check size={15} className="shrink-0 text-emerald-400" />}
                      </button>
                    )
                  })}
                </div>
                {secildi && (
                  <div className="mt-3 text-[13px] bg-white/[0.03] border border-white/8 rounded-lg px-3 py-2">
                    <span className={secildi === soru.dogru ? 'text-emerald-300 font-semibold' : 'text-rose-300 font-semibold'}>
                      {secildi === soru.dogru ? '✓ Doğru! +10 XP' : `✗ Yanlış — doğru cevap: ${soru.dogru}`}
                    </span>
                    {soru.aciklama && <div className="text-slate-400 mt-1">{soru.aciklama}</div>}
                    <div className="text-[11px] text-amber-300/80 mt-1.5">🤖 AI üretimi — kesinlik için teyit et.</div>
                  </div>
                )}
              </div>
            ) : soruHam ? (
              <div className="text-[13.5px] text-slate-200 whitespace-pre-wrap leading-relaxed">{soruHam}
                <div className="text-[11px] text-amber-300/80 mt-2">🤖 AI üretimi — teyit et.</div>
              </div>
            ) : (
              <p className="text-xs text-slate-500">Sınavının derslerinden bir soru için “Getir”e bas — cevabı işaretle, doğru bilirsen <b className="text-amber-300/90">+10 XP</b>.</p>
            )}
          </div>
        )}

        {/* İstatistik özeti */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {ozet.map((o) => (
            <div key={o.ad} className="card !py-3 text-center">
              <o.Icon size={16} className={`mx-auto ${o.renk}`} />
              <div className="text-lg font-bold text-white mt-1 tabular-nums">{o.deger}</div>
              <div className="text-[11px] text-slate-500">{o.ad}</div>
            </div>
          ))}
        </div>

        {/* Rozetler */}
        <div className="card">
          <div className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
            <Trophy size={16} className="text-amber-300" /> Rozetler <span className="text-[11px] text-slate-500">({kazanilan.size}/{ROZETLER.length})</span>
          </div>
          <div className="grid grid-cols-4 gap-2">
            {ROZETLER.map((r) => {
              const on = kazanilan.has(r.id)
              return (
                <div key={r.id} title={r.aciklama}
                  className={`rounded-xl border p-2 text-center ${on ? 'bg-amber-500/10 border-amber-500/30' : 'bg-white/[0.02] border-white/8 opacity-50'}`}>
                  <div className={`text-2xl ${on ? '' : 'grayscale'}`}>{r.ikon}</div>
                  <div className="text-[10px] text-slate-300 mt-0.5 leading-tight">{r.ad}</div>
                </div>
              )
            })}
          </div>
        </div>

        {/* E-posta hatırlatma opt-in (girişli; KVKK — varsayılan kapalı) */}
        {user && (
          <div className="card !py-3 flex items-center justify-between gap-3">
            <div className="min-w-0">
              <div className="text-sm text-white flex items-center gap-2"><Mail size={15} className="text-sky-300" /> Haftalık e-posta hatırlatma</div>
              <p className="text-[11px] text-slate-500 mt-0.5">Ara verdiğinde nazik bir hatırlatma e-postası gönderelim. İstediğin an kapatabilirsin.</p>
            </div>
            <button onClick={emailToggle} role="switch" aria-checked={emailOn}
              className={`shrink-0 w-11 h-6 rounded-full transition relative ${emailOn ? 'bg-gradient-to-r from-brand-500 to-accent-500' : 'bg-white/15'}`}>
              <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-all ${emailOn ? 'left-[22px]' : 'left-0.5'}`} />
            </button>
          </div>
        )}
      </div>
    </>
  )
}
