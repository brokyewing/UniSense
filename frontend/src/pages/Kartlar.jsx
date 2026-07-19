import { useState, useEffect, useMemo, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Layers, Plus, Trash2, X, Loader2, Play, RotateCw, ChevronDown, ChevronUp, Check } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { useAuth } from '../contexts/AuthContext'
import { watchKartlar, addKart, updateKart, removeKart, recordActivity } from '../firebase'
import { sm2, tekrarZamani, bugunStr } from '../lib/tekrar'
import { tasimaGerekli, damgala } from '../lib/bulutTasima'

const LS = 'unisense_flashcards'
const loadLocal = () => { try { return JSON.parse(localStorage.getItem(LS) || '[]') } catch { return [] } }
const saveLocal = (a) => { try { localStorage.setItem(LS, JSON.stringify(a)) } catch { /* noop */ } }

export default function Kartlar({ embedded = false }) {
  const { user } = useAuth()
  const [kartlar, setKartlar] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [f, setF] = useState({ deste: '', on: '', arka: '' })
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState('')
  const [acik, setAcik] = useState(null)
  const [sesh, setSesh] = useState(null) // { deste, queue:[id], i, flipped, done }

  useEffect(() => {
    if (!user) { setKartlar(loadLocal()); return }
    return watchKartlar(user.uid, (items) => {
      if (items == null) { setKartlar(loadLocal()); return }
      const local = loadLocal()
      if (tasimaGerekli(LS, items.length === 0, local.length > 0)) {
        // Yalnız SAHİPSİZ (gerçek misafir) kartlar taşınır — ayna damgası ortak cihazda sızıntıyı önler
        for (const k of local) {
          addKart(user.uid, {
            deste: String(k.deste || 'Genel').slice(0, 80), on: String(k.on || '').slice(0, 500),
            arka: String(k.arka || '').slice(0, 1000), ef: k.ef ?? 2.5, rep: k.rep ?? 0,
            interval: k.interval ?? 0, nextReview: String(k.nextReview || '').slice(0, 20),
          }).catch(() => {})
        }
        damgala(LS, user.uid)
        setKartlar(local)
        return
      }
      setKartlar(items); saveLocal(items); damgala(LS, user.uid)
    })
  }, [user])

  function flash(m) { setToast(m); setTimeout(() => setToast(''), 2200) }
  const today = bugunStr()

  const desteler = useMemo(() => {
    const m = {}
    for (const k of kartlar) {
      const d = k.deste || 'Genel'
      if (!m[d]) m[d] = { deste: d, total: 0, due: 0, kartlar: [] }
      m[d].total++; m[d].kartlar.push(k)
      if (tekrarZamani(k, today)) m[d].due++
    }
    return Object.values(m)
  }, [kartlar, today])

  async function persistAdd(k) {
    if (user) await addKart(user.uid, k)
    else { const a = [{ ...k, id: 'l' + Date.now(), createdAt: Date.now() }, ...kartlar]; saveLocal(a); setKartlar(a) }
  }
  async function persistUpdate(id, patch) {
    if (user && !String(id).startsWith('l')) await updateKart(user.uid, id, patch).catch(() => {})
    else { const a = kartlar.map((x) => (x.id === id ? { ...x, ...patch } : x)); saveLocal(a); setKartlar(a) }
  }
  async function persistDelete(id) {
    if (user && !String(id).startsWith('l')) await removeKart(user.uid, id).catch(() => {})
    else { const a = kartlar.filter((x) => x.id !== id); saveLocal(a); setKartlar(a) }
  }

  async function ekle() {
    if (!f.on.trim() || !f.arka.trim()) { flash('Ön ve arka yüzü doldur'); return }
    setSaving(true)
    const k = { deste: f.deste.trim() || 'Genel', on: f.on.trim(), arka: f.arka.trim(), ef: 2.5, rep: 0, interval: 0, nextReview: today }
    try { await persistAdd(k); recordActivity(user?.uid).catch(() => {}); setF({ deste: f.deste, on: '', arka: '' }); flash('✓ Kart eklendi') }
    catch (e) { flash(e.message) } finally { setSaving(false) }
  }

  function calisBaslat(deste) {
    const due = kartlar.filter((k) => (k.deste || 'Genel') === deste && tekrarZamani(k, today))
    if (!due.length) { flash('Bu destede bugün tekrar edilecek kart yok'); return }
    setSesh({ deste, queue: due.map((k) => k.id), i: 0, flipped: false, done: 0 })
  }

  const puanlaniyor = useRef(false) // hızlı çift tık aynı karta 2× SM-2 uygulamasın
  async function puanla(kalite) {
    if (puanlaniyor.current) return
    puanlaniyor.current = true
    try {
      const id = sesh.queue[sesh.i]
      const kart = kartlar.find((k) => k.id === id)
      if (kart) await persistUpdate(id, sm2(kart, kalite))
      recordActivity(user?.uid).catch(() => {})
      setSesh((s) => ({ ...s, i: s.i + 1, flipped: false, done: s.done + 1 }))
    } finally { puanlaniyor.current = false }
  }

  // === Çalışma (tekrar) oturumu ===
  if (sesh) {
    const bitti = sesh.i >= sesh.queue.length
    const kart = bitti ? null : kartlar.find((k) => k.id === sesh.queue[sesh.i])
    return (
      <>
        {!embedded && <BackgroundScene />}
        <div className="max-w-xl mx-auto space-y-4">
          <div className="flex items-center justify-between">
            <div className="text-sm text-slate-300 font-semibold">{sesh.deste}</div>
            <button onClick={() => setSesh(null)} className="text-slate-500 hover:text-white inline-flex items-center gap-1 text-xs"><X size={15} /> Bitir</button>
          </div>
          {bitti || !kart ? (
            <div className="card text-center py-10 space-y-3">
              <div className="text-3xl">🎉</div>
              <div className="text-white font-semibold">{sesh.done} kart çalıştın!</div>
              <button onClick={() => setSesh(null)} className="btn-primary text-sm">Bitti</button>
            </div>
          ) : (
            <>
              <div className="text-center text-[11px] text-slate-500">{sesh.i + 1} / {sesh.queue.length}</div>
              <button onClick={() => setSesh((s) => ({ ...s, flipped: !s.flipped }))}
                className="card w-full min-h-[180px] flex items-center justify-center text-center p-6">
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-2">{sesh.flipped ? 'Arka' : 'Ön'}</div>
                  <div className="text-lg text-white whitespace-pre-wrap">{sesh.flipped ? kart.arka : kart.on}</div>
                  {!sesh.flipped && <div className="text-[11px] text-slate-500 mt-3 inline-flex items-center gap-1"><RotateCw size={12} /> Çevirmek için dokun</div>}
                </div>
              </button>
              {sesh.flipped ? (
                <div className="grid grid-cols-3 gap-2">
                  <button onClick={() => puanla(2)} className="py-2.5 rounded-xl bg-rose-500/15 text-rose-300 border border-rose-500/30 text-sm font-semibold hover:bg-rose-500/25">Zor</button>
                  <button onClick={() => puanla(3)} className="py-2.5 rounded-xl bg-amber-500/15 text-amber-300 border border-amber-500/30 text-sm font-semibold hover:bg-amber-500/25">Orta</button>
                  <button onClick={() => puanla(5)} className="py-2.5 rounded-xl bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 text-sm font-semibold hover:bg-emerald-500/25">Kolay</button>
                </div>
              ) : (
                <button onClick={() => setSesh((s) => ({ ...s, flipped: true }))} className="btn-primary w-full text-sm inline-flex items-center justify-center gap-1.5"><RotateCw size={15} /> Çevir</button>
              )}
            </>
          )}
        </div>
      </>
    )
  }

  // === Deste listesi ===
  return (
    <>
      {!embedded && <BackgroundScene />}
      {!embedded && (
        <Seo title="Bilgi Kartları — Aralıklı Tekrarla Ezberle | UniSense"
          description="Kendi soru-cevap kartlarını oluştur, SM-2 aralıklı tekrarla kalıcı öğren. Ücretsiz flashcard aracı." path="/kartlar" noindex />
      )}
      {toast && <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl glass text-sm">{toast}</div>}
      <div className="max-w-3xl mx-auto space-y-5">
        {!embedded && (
          <div className="text-center">
            <h1 className="text-3xl md:text-4xl font-display font-bold text-white mb-1 flex items-center justify-center gap-2">
              <Layers className="text-violet-300" /> Bilgi Kartları
            </h1>
            <p className="text-slate-400 text-sm">Soru-cevap kartları oluştur, aralıklı tekrarla ezberle.</p>
          </div>
        )}

        <div className="flex justify-end">
          {!showForm && (
            <button onClick={() => setShowForm(true)} className="btn-primary text-sm inline-flex items-center gap-1.5">
              <Plus size={15} /> Kart ekle
            </button>
          )}
        </div>

        {showForm && (
          <div className="card space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="font-semibold text-white text-sm">Yeni kart</div>
              <button onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X size={16} /></button>
            </div>
            <input value={f.deste} onChange={(e) => setF({ ...f, deste: e.target.value })} placeholder="Deste (ör. İngilizce Kelime)" maxLength={80} className="input-glass text-sm w-full" list="deste-list" />
            <datalist id="deste-list">{desteler.map((d) => <option key={d.deste} value={d.deste} />)}</datalist>
            <textarea value={f.on} onChange={(e) => setF({ ...f, on: e.target.value })} rows={2} maxLength={500} placeholder="Ön yüz (soru / kelime)" className="input-glass text-sm w-full resize-none" />
            <textarea value={f.arka} onChange={(e) => setF({ ...f, arka: e.target.value })} rows={2} maxLength={1000} placeholder="Arka yüz (cevap / anlam)" className="input-glass text-sm w-full resize-none" />
            <div className="flex justify-end">
              <button onClick={ekle} disabled={saving} className="btn-primary text-sm inline-flex items-center gap-1.5 disabled:opacity-50">
                {saving ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />} Kaydet
              </button>
            </div>
          </div>
        )}

        {desteler.length === 0 ? (
          <div className="card text-center py-8 text-sm text-slate-400">Henüz kart yok. İlk kartını ekle — soru-cevaplarını aralıklı tekrarla ezberle. 🧠</div>
        ) : (
          <div className="space-y-2">
            {desteler.map((d) => {
              const open = acik === d.deste
              return (
                <div key={d.deste} className="card !py-3">
                  <div className="flex items-center justify-between gap-3">
                    <button onClick={() => setAcik(open ? null : d.deste)} className="min-w-0 text-left flex-1 flex items-center gap-2">
                      {open ? <ChevronUp size={16} className="text-slate-500 shrink-0" /> : <ChevronDown size={16} className="text-slate-500 shrink-0" />}
                      <span className="font-semibold text-white text-sm truncate">{d.deste}</span>
                      <span className="text-[11px] text-slate-500 shrink-0">{d.total} kart</span>
                      {d.due > 0 && <span className="text-[10px] px-1.5 py-0.5 rounded bg-violet-500/15 text-violet-300 shrink-0">{d.due} tekrar</span>}
                    </button>
                    <button onClick={() => calisBaslat(d.deste)} disabled={d.due === 0}
                      className="btn-primary text-xs inline-flex items-center gap-1.5 disabled:opacity-40 shrink-0">
                      <Play size={13} /> Çalış
                    </button>
                  </div>
                  {open && (
                    <div className="mt-2.5 pt-2.5 border-t border-white/5 space-y-1.5">
                      {d.kartlar.map((k) => (
                        <div key={k.id} className="flex items-center gap-2 text-[13px]">
                          <span className="text-slate-200 flex-1 truncate">{k.on}</span>
                          <span className="text-slate-500">→</span>
                          <span className="text-slate-400 flex-1 truncate">{k.arka}</span>
                          <button onClick={() => persistDelete(k.id)} className="text-slate-600 hover:text-rose-400 shrink-0"><Trash2 size={13} /></button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {!user && kartlar.length > 0 && (
          <div className="text-[11px] text-slate-600 text-center px-2">
            <Link to="/giris" className="text-accent-300">Giriş yap</Link> → kartların cihazlar arası senkronlanır.
          </div>
        )}
      </div>
    </>
  )
}
