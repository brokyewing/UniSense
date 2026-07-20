import { useState, useEffect, useMemo, useCallback } from 'react'
import { useLocation, Link } from 'react-router-dom'
import { CalendarRange, Plus, Check, Loader2, Sparkles, Wand2, Trash2, Settings2, CheckCircle2, Target } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { apiFetch } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import {
  getPlanConfig, setPlanConfig, watchPlanGorevler, addPlanGorev, addPlanGorevler,
  updatePlanGorev, removePlanGorev, recordActivity, getUserProfile, getKonuChecked, getSoruList,
} from '../firebase'
import { tasimaGerekli, damgala } from '../lib/bulutTasima'
import { konuLocal } from '../lib/konu'
import {
  isoGun, isoHafta, gunFark, oneriler, haftaPlanla, carryForward,
  uyumYuzde, gecikmeYuzde, tekrarTarihleri, TEKRAR_ARALIK, kompaktOzet, parseDirektif, gorevYap,
  ufukPlanla, parseHedef,
} from '../lib/planlayici'

const SINAVLAR = ['YKS', 'DGS', 'KPSS', 'LGS']
const CFG_LS = 'unisense_plan_cfg'
const WK_LS = (h) => `unisense_plan_${h}`
const VARSAYILAN = { hedefSaat: 15, haftaIciBlok: 2, haftaSonuBlok: 4 }

const loadJSON = (k, d) => { try { return JSON.parse(localStorage.getItem(k) || d) } catch { return JSON.parse(d) } }
const saveJSON = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)) } catch { /* noop */ } }

// Çözülen soru kayıtlarını konu bazında özetle (hem localStorage hem bulut listesi için)
function grupla(list) {
  const m = new Map()
  for (const r of list || []) {
    const key = r.konu || r.ders
    if (!key) continue
    const o = m.get(key) || { ders: r.ders || '', konu: r.konu || r.ders || '', cozulen: 0, dogru: 0 }
    o.cozulen += r.cozulen || 0; o.dogru += r.dogru || 0
    m.set(key, o)
  }
  return [...m.values()]
}
const soruOzetLocal = (track) => grupla(loadJSON('unisense_soru_' + track, '[]'))

const fmtGun = (iso) => {
  try { return new Date(iso + 'T00:00:00').toLocaleDateString('tr-TR', { weekday: 'short', day: 'numeric', month: 'short' }) }
  catch { return iso }
}
const turEtiket = (t) => (t.source === 'manual' ? { ad: 'Elle', cls: 'bg-slate-500/20 text-slate-300' }
  : t.source === 'tekrar' || t.tur === 'tekrar' ? { ad: 'Tekrar', cls: 'bg-violet-500/20 text-violet-300' }
    : t.source === 'ai' ? { ad: 'AI', cls: 'bg-amber-500/20 text-amber-300' }
      : { ad: 'Yeni', cls: 'bg-emerald-500/20 text-emerald-300' })

export default function Planim({ embedded = false }) {
  const { user } = useAuth()
  const loc = useLocation()
  const bugun = useMemo(() => isoGun(), [])
  const hafta = useMemo(() => isoHafta(new Date()), [])

  const [config, setConfig] = useState(undefined) // undefined=yükleniyor, null=kurulmadı
  const [tasks, setTasks] = useState([])
  const [konuData, setKonuData] = useState(null)
  const [checked, setChecked] = useState({}) // konu ilerlemesi (bulut hidrasyonlu — Rev-4)
  const [soruOzet, setSoruOzet] = useState([]) // çözülen soru özeti (bulut hidrasyonlu)
  const [kalanGun, setKalanGun] = useState(null)
  const [defaultTrack, setDefaultTrack] = useState('YKS')

  const [manuel, setManuel] = useState(loc.state?.gorev || '')
  const [toast, setToast] = useState('')
  const [ai, setAi] = useState({ loading: false, text: '', oncelik: null })
  const [ayar, setAyar] = useState(false) // ayar panelini aç
  const [hedefMetin, setHedefMetin] = useState('')
  const [hedefAI, setHedefAI] = useState({ loading: false, text: '' })

  const flash = useCallback((m) => { setToast(m); setTimeout(() => setToast(''), 2200) }, [])

  // --- Ayar (config) yükle: girişsiz local, girişli bulut + migration ---
  useEffect(() => {
    let iptal = false
    ;(async () => {
      if (!user) { setConfig(loadJSON(CFG_LS, 'null')); return }
      getUserProfile(user.uid).then((p) => {
        const tr = p?.profile?.examTrack
        if (tr && SINAVLAR.includes(tr)) setDefaultTrack(tr)
      }).catch(() => {})
      const cloud = await getPlanConfig(user.uid)
      if (iptal) return
      const local = loadJSON(CFG_LS, 'null')
      if (tasimaGerekli(CFG_LS, cloud == null, local != null)) {
        setPlanConfig(user.uid, local).catch(() => {}); damgala(CFG_LS, user.uid); setConfig(local); return
      }
      damgala(CFG_LS, user.uid)
      // ORTAK cihaz sızıntısı (Finding 2): migration yoksa YALNIZ bulutu göster — başka
      // kullanıcının bayat local ayarına DÜŞME. Bulut yoksa kurulum akışı (null).
      setConfig(cloud || null)
      if (cloud) saveJSON(CFG_LS, cloud)
    })()
    return () => { iptal = true }
  }, [user])

  // --- Haftanın görevlerini yükle + carry-forward (girişsiz local / girişli bulut) ---
  useEffect(() => {
    if (!user) {
      const local = loadJSON(WK_LS(hafta), '[]')
      const cf = carryForward(local, bugun)
      setTasks(cf)
      if (JSON.stringify(cf) !== JSON.stringify(local)) saveJSON(WK_LS(hafta), cf)
      return
    }
    return watchPlanGorevler(user.uid, hafta, (items) => {
      if (items == null) { setTasks(carryForward(loadJSON(WK_LS(hafta), '[]'), bugun)); return }
      const local = loadJSON(WK_LS(hafta), '[]')
      // Guest→bulut migration (bir kez, sahipsiz veri): her görevi doküman olarak taşı
      if (tasimaGerekli(WK_LS(hafta), items.length === 0, local.length > 0)) {
        const cf = carryForward(local, bugun)
        addPlanGorevler(user.uid, cf.map((t) => ({ ...t, hafta }))).catch(() => {})
        damgala(WK_LS(hafta), user.uid); setTasks(cf); return
      }
      damgala(WK_LS(hafta), user.uid)
      const cf = carryForward(items, bugun)
      setTasks(cf); saveJSON(WK_LS(hafta), cf)
      // carry-forward tarih taşıdıysa o görevleri güncelle (idempotent → snapshot döngüsü yok).
      // moved bayrağı da yazılır (Rev-1: gecikme sinyali reload sonrası kalıcı olsun).
      for (const t of cf) {
        const orig = items.find((x) => x.id === t.id)
        if (orig && orig.tarih !== t.tarih) {
          updatePlanGorev(user.uid, t.id, { tarih: t.tarih, source: t.source, moved: true }).catch(() => {})
        }
      }
    })
  }, [user, hafta, bugun])

  // --- Konu listesi + geri sayım + konu/soru ilerlemesi (bulut hidrasyonu — Rev-4) ---
  const track = config?.track
  useEffect(() => {
    if (!track) return
    apiFetch(`/api/v1/konular?sinav=${track}`).then(setKonuData).catch(() => setKonuData(null))
    apiFetch('/api/v1/takvim').then((d) => {
      const ev = (d?.yaklasan || []).find((e) => e.sinav === track && e.tur === 'sinav')
      setKalanGun(ev ? ev.kalan_gun : null)
    }).catch(() => {})
    // İlerleme: önce local ayna; girişli + local BOŞSA buluttan doldur (doğrudan
    // /planim'e gelen, Konular/Çalışmalarım'ı bu tarayıcıda açmamış kullanıcı için).
    const yerelChecked = konuLocal(track)
    const yerelSoru = soruOzetLocal(track)
    setChecked(yerelChecked); setSoruOzet(yerelSoru)
    if (user) {
      if (!Object.keys(yerelChecked).length) {
        getKonuChecked(user.uid, track).then((c) => { if (c && Object.keys(c).length) setChecked(c) }).catch(() => {})
      }
      if (!yerelSoru.length) {
        getSoruList(user.uid, track).then((l) => { if (l?.length) setSoruOzet(grupla(l)) }).catch(() => {})
      }
    }
  }, [track, user])

  // --- Kalıcılık: girişli = doküman başına Firestore op; girişsiz = local hafta dizisi ---
  const guestSave = useCallback((next) => { setTasks(next); saveJSON(WK_LS(hafta), next) }, [hafta])

  function kur(cfg) {
    const eff = { ...VARSAYILAN, ...cfg, kuruldu: true }
    setConfig(eff); setAyar(false)
    if (user) setPlanConfig(user.uid, eff).catch(() => {})
    else saveJSON(CFG_LS, eff)
    damgala(CFG_LS, user?.uid)
  }

  // Aralıklı tekrar: bir görev İLK kez tamamlanınca sıradaki tekrarı ilgili haftaya ekle.
  // Yalnız ilk tamamlamada çağrılır (toggle'daki ilkTamam) → çift ekleme yok; tek doküman
  // eklemesi (addPlanGorev) → oku-değiştir-yaz yarışı yok (Rev-2).
  function tekrarPlanla(t) {
    const idx = (t.tekrarNo ?? -1) + 1
    if (!t.konu || idx >= TEKRAR_ARALIK.length) return
    const revDate = tekrarTarihleri(bugun)[idx]
    const wk = isoHafta(new Date(revDate + 'T00:00:00'))
    const rev = { ...gorevYap({ id: `rev-${t.konu}-${idx}`, ders: t.ders, konu: t.konu, title: `${t.konu} — tekrar`, tarih: revDate, source: 'tekrar', tur: 'tekrar' }), tekrarNo: idx, hafta: wk }
    if (user) { addPlanGorev(user.uid, rev).catch(() => {}); return }
    const cur = loadJSON(WK_LS(wk), '[]')
    const next = [...cur, rev]
    saveJSON(WK_LS(wk), next)
    if (wk === hafta) setTasks(next)
  }

  function toggle(t) {
    const done = t.status !== 'done'
    const ilkTamam = done && !t.sayildi
    const patch = { status: done ? 'done' : 'planned', ...(ilkTamam ? { sayildi: true } : {}) }
    if (user) updatePlanGorev(user.uid, t.id, patch).catch(() => {}) // snapshot state'i tazeler
    else guestSave(tasks.map((x) => (x.id === t.id ? { ...x, ...patch } : x)))
    if (done) {
      recordActivity(user?.uid).catch(() => {}) // streak (günde 1 yazar)
      // XP: planGorev getIstatistik/guestStats'ta done sayımından TÜRETİLİR (uncheck'te de tutarlı — Rev-3)
      if (ilkTamam) tekrarPlanla(t) // aralıklı tekrar yalnız ilk tamamlamada
    }
  }

  function ekleGorev(title, tarih = bugun, extra = {}) {
    const t = String(title || '').trim()
    if (!t) return
    const task = gorevYap({ id: `m-${Date.now()}`, title: t.slice(0, 120), tarih, source: 'manual', ...extra })
    if (user) addPlanGorev(user.uid, { ...task, hafta }).catch(() => {})
    else guestSave([...tasks, task])
  }

  function planla() {
    if (!konuData) { flash('Konu listesi yükleniyor…'); return }
    const next = haftaPlanla({
      konuData, checked, soruOzet, hafta, bugun,
      haftaIciBlok: config.haftaIciBlok, haftaSonuBlok: config.haftaSonuBlok, mevcut: tasks,
    })
    const yeniler = next.slice(tasks.length) // haftaPlanla mevcut'u başa koyar → yeni olanlar sonda
    if (!yeniler.length) { flash('Uygun boş slot yok'); return }
    if (user) addPlanGorevler(user.uid, yeniler.map((t) => ({ ...t, hafta }))).catch(() => {})
    // guest: deterministik id'ler re-plan'da çakışabilir → benzersiz id ver
    else guestSave([...tasks, ...yeniler.map((t, i) => ({ ...t, id: `p-${Date.now()}-${i}` }))])
    flash(`✓ ${yeniler.length} görev planlandı`)
  }

  async function takvimimNasil() {
    setAi({ loading: true, text: '', oncelik: null })
    const zayif = oneriler(konuData, checked, soruOzet, 3).map((o) => o.konu)
    const done = tasks.filter((t) => t.status === 'done').slice(-3).map((t) => t.konu || t.title).filter(Boolean)
    const lag = gecikmeYuzde(tasks, bugun)
    const ozet = kompaktOzet({ track, kalanGun, zayif, done, lag, hedefSaat: config.hedefSaat })
    const q = `${ozet}. Bu ${track} çalışma planı durumu. SADECE şu JSON: {"oncelik":["konu1","konu2"],"tavsiye":"1-2 cümle Türkçe koçluk"}`.slice(0, 490)
    const cagir = () => apiFetch('/api/v1/ask', { method: 'POST', body: { query: q } }).then((r) => r?.text || '')
    try {
      let text = await cagir()
      let d = parseDirektif(text)
      if (!d) { text = await cagir(); d = parseDirektif(text) } // retry=1
      if (d) setAi({ loading: false, text: d.tavsiye || 'Planın iyi görünüyor.', oncelik: d.oncelik })
      else setAi({ loading: false, text: text || 'Yorum üretilemedi.', oncelik: null }) // fallback: ham metin
    } catch (e) {
      setAi({ loading: false, text: 'AI yorumu alınamadı (' + e.message + '). Plan yine de çalışıyor — "Haftayı planla" ile devam et.', oncelik: null })
    }
  }

  function aiUygula() {
    const next = haftaPlanla({
      konuData, checked, soruOzet, hafta, bugun,
      haftaIciBlok: config.haftaIciBlok, haftaSonuBlok: config.haftaSonuBlok, oncelikKonu: ai.oncelik || [], mevcut: tasks,
    })
    const yeniler = next.slice(tasks.length)
    if (user) addPlanGorevler(user.uid, yeniler.map((t) => ({ ...t, hafta }))).catch(() => {})
    else guestSave([...tasks, ...yeniler.map((t, i) => ({ ...t, id: `p-${Date.now()}-${i}` }))])
    setAi({ loading: false, text: '', oncelik: null }); flash('✓ Plan güncellendi')
  }

  // Serbest hedef → AI yorumlar {gunSayisi, gunlukSoru} → ufuk planı tüm konuları N güne dağıtır
  async function hedefPlanla() {
    const g = hedefMetin.trim()
    if (!g) return
    if (!konuData) { flash('Konu listesi yükleniyor…'); return }
    setHedefAI({ loading: true, text: '' })
    const q = `Öğrenci çalışma hedefi: "${g.slice(0, 140)}". Sınav: ${track}. SADECE şu JSON: {"gunSayisi":<toplam kaç gün>,"gunlukSoru":<günde kaç soru, belirtilmediyse 0>,"tavsiye":"1 kısa cümle Türkçe"}`.slice(0, 490)
    const cagir = () => apiFetch('/api/v1/ask', { method: 'POST', body: { query: q } }).then((r) => r?.text || '')
    let hedef = null
    try {
      let text = await cagir()
      hedef = parseHedef(text)
      if (!hedef) { text = await cagir(); hedef = parseHedef(text) } // retry=1
    } catch { /* AI erişilemedi → aşağıda regex fallback */ }
    // Fallback: AI çözemezse cümledeki sayıları yakala (uygulama LLM'siz de çalışsın)
    if (!hedef) {
      const gm = g.match(/(\d{1,3})\s*g[üu]n/i)
      const sm = g.match(/(\d{1,4})\s*soru/i)
      if (gm) hedef = { gunSayisi: Math.min(365, +gm[1]), gunlukSoru: sm ? Math.min(1000, +sm[1]) : null, tavsiye: '' }
    }
    if (!hedef) { setHedefAI({ loading: false, text: 'Hedefi anlayamadım. Örn: "50 günde tüm konular, günde 100 soru".' }); return }
    const yeni = ufukPlanla({ konuData, checked, soruOzet, gunSayisi: hedef.gunSayisi, gunlukSoru: hedef.gunlukSoru, baslangic: bugun })
    if (!yeni.length) { setHedefAI({ loading: false, text: 'Planlanacak konu bulunamadı — önce Konu Takibi\'nden konularını işaretle.' }); return }
    if (user) {
      // Bu haftanın otomatik görevlerini temizle (görünür çift-plan olmasın) + hepsini batch yaz
      for (const t of tasks.filter((t) => t.status !== 'done' && t.source !== 'manual')) removePlanGorev(user.uid, t.id).catch(() => {})
      addPlanGorevler(user.uid, yeni).catch(() => {}) // her görev zaten hafta alanlı → çok-haftalık
    } else {
      // Haftaya göre grupla; her haftanın auto'sunu değiştir (manual/done korunur)
      const gruplar = {}
      for (const t of yeni) (gruplar[t.hafta] = gruplar[t.hafta] || []).push(t)
      for (const [wk, list] of Object.entries(gruplar)) {
        const cur = loadJSON(WK_LS(wk), '[]').filter((t) => t.status === 'done' || t.source === 'manual')
        const merged = [...cur, ...list.map((t, i) => ({ ...t, id: `u-${wk}-${i}` }))]
        saveJSON(WK_LS(wk), merged)
        if (wk === hafta) setTasks(merged)
      }
    }
    setHedefMetin('')
    setHedefAI({ loading: false, text: `✓ ${hedef.gunSayisi} güne ${yeni.length} görev dağıtıldı${hedef.gunlukSoru ? ` (günde ~${hedef.gunlukSoru} soru)` : ''}.${hedef.tavsiye ? ' ' + hedef.tavsiye : ''}` })
    flash('✓ Plan oluşturuldu')
  }

  function sil(t) {
    if (user) removePlanGorev(user.uid, t.id).catch(() => {})
    else guestSave(tasks.filter((x) => x.id !== t.id))
  }
  function otomatikTemizle() {
    if (!confirm('Bu haftanın otomatik (tamamlanmamış) görevlerini temizle?')) return
    if (user) { for (const t of tasks.filter((t) => t.status !== 'done' && t.source !== 'manual')) removePlanGorev(user.uid, t.id).catch(() => {}) }
    else guestSave(tasks.filter((t) => t.status === 'done' || t.source === 'manual'))
  }

  // --- Türetilen ---
  const bugunTasks = useMemo(() => tasks.filter((t) => t.tarih === bugun), [tasks, bugun])
  const ileri = useMemo(() => {
    const g = new Map()
    for (const t of tasks) if (gunFark(bugun, t.tarih) > 0) { if (!g.has(t.tarih)) g.set(t.tarih, []); g.get(t.tarih).push(t) }
    return [...g.entries()].sort((a, b) => (a[0] < b[0] ? -1 : 1))
  }, [tasks, bugun])
  const uyum = useMemo(() => uyumYuzde(tasks, bugun), [tasks, bugun])
  const oneriListe = useMemo(() => {
    if (!konuData) return []
    const mevcutKonu = new Set(tasks.map((t) => t.konu).filter(Boolean))
    return oneriler(konuData, checked, soruOzet, 5)
      .filter((o) => !mevcutKonu.has(o.konu)).slice(0, 3)
  }, [konuData, tasks, checked, soruOzet])

  // ================= RENDER =================
  const H1 = (
    <div className="text-center">
      <h1 className="text-3xl md:text-4xl font-display font-bold text-white mb-1 flex items-center justify-center gap-2">
        <CalendarRange className="text-teal-300" /> Planım
      </h1>
      <p className="text-slate-400 text-sm">Haftanı planla, günlük görevlerini bitir — AI geri kalınca yeniden düzenler.</p>
    </div>
  )

  // Onboarding / ayar formu
  const Onboarding = (
    <OnboardingForm
      defaultTrack={config?.track || defaultTrack}
      config={config}
      onKur={kur}
      onIptal={config?.kuruldu ? () => setAyar(false) : null}
    />
  )

  const body = (config === undefined) ? (
    <div className="card flex items-center justify-center py-10 text-slate-400"><Loader2 className="animate-spin mr-2" size={18} /> Yükleniyor…</div>
  ) : (!config?.kuruldu || ayar) ? Onboarding : (
    <>
      {/* Üst durum */}
      <div className="card flex flex-wrap items-center gap-3">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center text-white font-display font-bold shrink-0">
          {config.track}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-white">
            {kalanGun != null ? `Sınava ${kalanGun} gün` : 'Çalışma planın'} · hedef {config.hedefSaat} sa/hafta
          </div>
          {uyum != null && (
            <div className="mt-1.5 flex items-center gap-2">
              <div className="flex-1 h-1.5 rounded-full bg-white/10 overflow-hidden">
                <div className="h-full rounded-full bg-gradient-to-r from-teal-400 to-emerald-500" style={{ width: `${uyum}%` }} />
              </div>
              <span className="text-[11px] text-slate-400 font-mono shrink-0">%{uyum} uyum</span>
            </div>
          )}
        </div>
        <button onClick={() => setAyar(true)} title="Ayarlar" className="shrink-0 text-slate-500 hover:text-teal-300"><Settings2 size={16} /></button>
      </div>

      {/* Aksiyonlar */}
      <div className="flex gap-2">
        <button onClick={planla} className="btn-primary flex-1 text-sm inline-flex items-center justify-center gap-1.5">
          <Wand2 size={15} /> Haftayı planla
        </button>
        <button onClick={takvimimNasil} disabled={ai.loading}
          className="flex-1 text-sm inline-flex items-center justify-center gap-1.5 rounded-xl px-4 py-2 font-semibold text-white bg-gradient-to-r from-amber-500 to-orange-600 disabled:opacity-50">
          {ai.loading ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />} Takvimim nasıl?
        </button>
      </div>

      {/* AI cevabı */}
      {ai.text && (
        <div className="card border-amber-500/25 bg-amber-500/[0.04] space-y-2">
          <div className="text-[11px] font-mono uppercase tracking-wider text-amber-300 flex items-center gap-1.5"><Sparkles size={12} /> UniSense Koç</div>
          <p className="text-sm text-slate-200 whitespace-pre-wrap">{ai.text}</p>
          {ai.oncelik?.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {ai.oncelik.slice(0, 6).map((k, i) => <span key={i} className="text-[11px] px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-200">{k}</span>)}
            </div>
          )}
          <div className="flex gap-2 pt-1">
            {ai.oncelik?.length > 0 && <button onClick={aiUygula} className="btn-primary text-xs inline-flex items-center gap-1"><Check size={13} /> Uygula</button>}
            <button onClick={() => setAi({ loading: false, text: '', oncelik: null })} className="text-xs px-3 py-1.5 rounded-lg bg-white/5 text-slate-300">Kapat</button>
          </div>
        </div>
      )}

      {/* Hedefle planla — serbest hedef → AI → tüm konuları N güne dağıt */}
      <div className="card space-y-2">
        <div className="text-sm font-semibold text-white flex items-center gap-1.5"><Target size={15} className="text-teal-300" /> Hedefle planla</div>
        <p className="text-[12px] text-slate-400">Hedefini yaz; AI tüm konuları o tempoya göre günlere dağıtsın.</p>
        <div className="flex gap-2">
          <input value={hedefMetin} onChange={(e) => setHedefMetin(e.target.value)} maxLength={140}
            onKeyDown={(e) => { if (e.key === 'Enter') hedefPlanla() }}
            placeholder="ör. 50 günde tüm konular, günde 100 soru"
            className="input-glass text-sm flex-1" />
          <button onClick={hedefPlanla} disabled={hedefAI.loading || !hedefMetin.trim()}
            className="btn-primary text-sm inline-flex items-center gap-1 disabled:opacity-50">
            {hedefAI.loading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />} Planla
          </button>
        </div>
        {hedefAI.text && <p className="text-[12px] text-teal-200 whitespace-pre-wrap">{hedefAI.text}</p>}
      </div>

      {/* Bugün ne çalışayım? */}
      {oneriListe.length > 0 && (
        <div className="card space-y-2">
          <div className="text-sm font-semibold text-white flex items-center gap-1.5"><CheckCircle2 size={15} className="text-emerald-300" /> Bugün ne çalışayım?</div>
          <div className="space-y-1.5">
            {oneriListe.map((o, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="flex-1 min-w-0 truncate text-slate-200">{o.title} <span className="text-[11px] text-slate-500">· {o.ders}</span></span>
                <button onClick={() => ekleGorev(o.title, bugun, { ders: o.ders, konu: o.konu, source: 'auto', tur: o.tur })}
                  className="shrink-0 text-xs px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/25 inline-flex items-center gap-1"><Plus size={12} /> Ekle</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Elle görev ekle */}
      <div className="card flex gap-2">
        <input value={manuel} onChange={(e) => setManuel(e.target.value)} maxLength={120}
          onKeyDown={(e) => { if (e.key === 'Enter') { ekleGorev(manuel); setManuel('') } }}
          placeholder="Bugüne görev ekle (ör. AYT Fizik optik 30 soru)"
          className="input-glass text-sm flex-1" />
        <button onClick={() => { ekleGorev(manuel); setManuel('') }} disabled={!manuel.trim()}
          className="btn-primary text-sm inline-flex items-center gap-1 disabled:opacity-50"><Plus size={14} /> Ekle</button>
      </div>

      {/* Bugün */}
      <div className="space-y-2">
        <div className="text-xs uppercase tracking-wider text-slate-500 px-1 flex items-center justify-between">
          <span>Bugün · {fmtGun(bugun)}</span>
          {tasks.some((t) => t.source === 'auto' || t.source === 'ai') && (
            <button onClick={otomatikTemizle} className="text-[11px] text-slate-600 hover:text-rose-400">otomatiği temizle</button>
          )}
        </div>
        {bugunTasks.length === 0 ? (
          <div className="card text-center py-6 text-sm text-slate-400">
            Bugün için görev yok. <span className="text-teal-300">Haftayı planla</span> ya da yukarıdan öneri ekle.
          </div>
        ) : bugunTasks.map((t) => <GorevSatir key={t.id} t={t} onToggle={toggle} onSil={sil} />)}
      </div>

      {/* Bu hafta (ileri günler) */}
      {ileri.length > 0 && (
        <div className="space-y-3">
          <div className="text-xs uppercase tracking-wider text-slate-500 px-1">Bu hafta</div>
          {ileri.map(([tarih, gs]) => (
            <div key={tarih} className="space-y-1.5">
              <div className="text-[11px] text-slate-500 px-1">{fmtGun(tarih)}</div>
              {gs.map((t) => <GorevSatir key={t.id} t={t} onToggle={toggle} onSil={sil} />)}
            </div>
          ))}
        </div>
      )}

      {!user && (
        <div className="text-[11px] text-slate-600 text-center px-2">
          <Link to="/giris" className="text-accent-300">Giriş yap</Link> → planın cihazlar arası senkronlanır.
        </div>
      )}
    </>
  )

  return (
    <>
      {!embedded && <BackgroundScene />}
      {!embedded && (
        <Seo title="Planım — AI Çalışma Planlayıcısı | UniSense"
          description="Haftalık çalışma planını kur, günlük görevlerini bitir; AI geri kaldığında planı yeniden düzenler. Ücretsiz." path="/planim" noindex />
      )}
      {toast && <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl glass text-sm">{toast}</div>}
      <div className="max-w-3xl mx-auto space-y-4">
        {!embedded && H1}
        {body}
      </div>
    </>
  )
}

// ---- Görev satırı ----
function GorevSatir({ t, onToggle, onSil }) {
  const et = turEtiket(t)
  const done = t.status === 'done'
  return (
    <div className="card !py-2.5 flex items-center gap-3">
      <button onClick={() => onToggle(t)} title={done ? 'Geri al' : 'Tamamlandı'}
        className={`shrink-0 w-5 h-5 rounded-md border flex items-center justify-center transition ${done ? 'bg-emerald-500/80 border-emerald-400 text-white' : 'border-white/25 text-transparent hover:border-emerald-400'}`}>
        <Check size={13} />
      </button>
      <div className={`flex-1 min-w-0 text-sm break-words ${done ? 'text-slate-500 line-through' : 'text-slate-100'}`}>{t.title}</div>
      <span className={`shrink-0 text-[10px] px-1.5 py-0.5 rounded-full ${et.cls}`}>{et.ad}</span>
      <button onClick={() => onSil(t)} className="shrink-0 text-slate-600 hover:text-rose-400"><Trash2 size={13} /></button>
    </div>
  )
}

// ---- Onboarding / ayar formu ----
function OnboardingForm({ defaultTrack, config, onKur, onIptal }) {
  const [track, setTrack] = useState(config?.track || defaultTrack || 'YKS')
  const [hedefSaat, setHedefSaat] = useState(config?.hedefSaat ?? VARSAYILAN.hedefSaat)
  const [ici, setIci] = useState(config?.haftaIciBlok ?? VARSAYILAN.haftaIciBlok)
  const [sonu, setSonu] = useState(config?.haftaSonuBlok ?? VARSAYILAN.haftaSonuBlok)
  useEffect(() => { if (!config?.track && defaultTrack) setTrack(defaultTrack) }, [defaultTrack, config])
  return (
    <div className="card space-y-4">
      <div className="text-sm font-semibold text-white">{config?.kuruldu ? 'Plan ayarları' : 'Planını kuralım'}</div>
      <div>
        <div className="text-xs text-slate-400 mb-1.5">Hangi sınav?</div>
        <div className="inline-flex flex-wrap gap-1 p-1 rounded-xl bg-white/5 border border-white/10">
          {SINAVLAR.map((s) => (
            <button key={s} onClick={() => setTrack(s)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium ${track === s ? 'bg-gradient-to-r from-teal-500 to-emerald-600 text-white' : 'text-slate-300 hover:bg-white/10'}`}>{s}</button>
          ))}
        </div>
      </div>
      <label className="block">
        <div className="text-xs text-slate-400 mb-1">Haftalık hedef (saat)</div>
        <input type="number" min="1" max="80" value={hedefSaat} onChange={(e) => setHedefSaat(Math.max(1, Math.min(80, +e.target.value || 1)))}
          className="input-glass text-sm w-28" />
      </label>
      <div className="grid grid-cols-2 gap-3">
        <label className="block">
          <div className="text-xs text-slate-400 mb-1">Hafta içi görev/gün</div>
          <input type="number" min="0" max="8" value={ici} onChange={(e) => setIci(Math.max(0, Math.min(8, +e.target.value || 0)))} className="input-glass text-sm w-full" />
        </label>
        <label className="block">
          <div className="text-xs text-slate-400 mb-1">Hafta sonu görev/gün</div>
          <input type="number" min="0" max="10" value={sonu} onChange={(e) => setSonu(Math.max(0, Math.min(10, +e.target.value || 0)))} className="input-glass text-sm w-full" />
        </label>
      </div>
      <p className="text-[11px] text-slate-500">Saatleri sonra değiştirebilirsin. Plan, Konu Takibi'ndeki eksik konuların ve Çalışmalarım'daki zayıf derslerine göre kurulur.</p>
      <div className="flex gap-2">
        <button onClick={() => onKur({ track, hedefSaat, haftaIciBlok: ici, haftaSonuBlok: sonu })} className="btn-primary text-sm inline-flex items-center gap-1.5">
          <Check size={14} /> {config?.kuruldu ? 'Kaydet' : 'Planı kur'}
        </button>
        {onIptal && <button onClick={onIptal} className="text-sm px-3 py-2 rounded-xl bg-white/5 text-slate-300">Vazgeç</button>}
      </div>
    </div>
  )
}
