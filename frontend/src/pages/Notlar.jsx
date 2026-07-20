import { useState, useEffect, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { NotebookPen, Plus, Trash2, Check, Loader2, CalendarPlus } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { useAuth } from '../contexts/AuthContext'
import { watchNotlar, addNot, updateNot, removeNot, recordActivity } from '../firebase'
import { tasimaGerekli, damgala } from '../lib/bulutTasima'

const LS = 'unisense_notlar'
const loadLocal = () => { try { return JSON.parse(localStorage.getItem(LS) || '[]') } catch { return [] } }
const saveLocal = (a) => { try { localStorage.setItem(LS, JSON.stringify(a)) } catch { /* noop */ } }

// Yapacaklar / serbest not — girişli bulut (notlar), girişsiz localStorage.
export default function Notlar({ embedded = false }) {
  const { user } = useAuth()
  const nav = useNavigate()
  const [notlar, setNotlar] = useState([])
  const [metin, setMetin] = useState('')
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState('')
  const [filtre, setFiltre] = useState('hepsi') // hepsi | yapilacak

  useEffect(() => {
    if (!user) { setNotlar(loadLocal()); return }
    return watchNotlar(user.uid, (items) => {
      if (items == null) { setNotlar(loadLocal()); return }
      const local = loadLocal()
      if (tasimaGerekli(LS, items.length === 0, local.length > 0)) {
        for (const n of local) {
          addNot(user.uid, { metin: String(n.metin || '').slice(0, 2000), tamamlandi: !!n.tamamlandi }).catch(() => {})
        }
        damgala(LS, user.uid); setNotlar(local); return
      }
      setNotlar(items); saveLocal(items); damgala(LS, user.uid)
    })
  }, [user])

  function flash(m) { setToast(m); setTimeout(() => setToast(''), 2000) }

  const gosterilen = useMemo(
    () => (filtre === 'yapilacak' ? notlar.filter((n) => !n.tamamlandi) : notlar),
    [notlar, filtre],
  )
  const kalan = useMemo(() => notlar.filter((n) => !n.tamamlandi).length, [notlar])

  async function ekle() {
    const t = metin.trim()
    if (!t) { flash('Bir not yaz'); return }
    setSaving(true)
    const n = { metin: t.slice(0, 2000), tamamlandi: false }
    try {
      if (user) await addNot(user.uid, n)
      else { const a = [{ ...n, id: 'l' + Date.now(), createdAt: Date.now() }, ...notlar]; saveLocal(a); setNotlar(a) }
      recordActivity(user?.uid).catch(() => {})
      setMetin('')
      flash('✓ Not eklendi')
    } catch (e) { flash(e.message) } finally { setSaving(false) }
  }

  async function toggle(n) {
    const yeni = !n.tamamlandi
    if (user && !String(n.id).startsWith('l')) { await updateNot(user.uid, n.id, { tamamlandi: yeni }).catch(() => {}) }
    else { const a = notlar.map((x) => (x.id === n.id ? { ...x, tamamlandi: yeni } : x)); saveLocal(a); setNotlar(a) }
  }

  async function sil(n) {
    if (user && !String(n.id).startsWith('l')) { await removeNot(user.uid, n.id).catch(() => {}) }
    else { const a = notlar.filter((x) => x.id !== n.id); saveLocal(a); setNotlar(a) }
  }

  return (
    <>
      {!embedded && <BackgroundScene />}
      {!embedded && (
        <Seo title="Notlarım — Yapacaklar & Çalışma Notları | UniSense"
          description="Yapacaklarını ve aklındakileri not et, tamamladıkça işaretle. Ücretsiz çalışma not defteri." path="/notlar" noindex />
      )}
      {toast && <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl glass text-sm">{toast}</div>}
      <div className="max-w-3xl mx-auto space-y-5">
        {!embedded && (
          <div className="text-center">
            <h1 className="text-3xl md:text-4xl font-display font-bold text-white mb-1 flex items-center justify-center gap-2">
              <NotebookPen className="text-rose-300" /> Notlarım
            </h1>
            <p className="text-slate-400 text-sm">Yapacaklarını ve aklındakileri not et — tamamladıkça işaretle.</p>
          </div>
        )}

        {/* Not ekleme */}
        <div className="card space-y-2">
          <textarea value={metin} onChange={(e) => setMetin(e.target.value)} rows={2} maxLength={2000}
            onKeyDown={(e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) ekle() }}
            placeholder="Bugün ne yapacaksın? (ör. AYT Matematik türev 40 soru çöz)"
            className="input-glass text-sm w-full resize-none" />
          <div className="flex justify-end">
            <button onClick={ekle} disabled={saving} className="btn-primary text-sm inline-flex items-center gap-1.5 disabled:opacity-50">
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />} Ekle
            </button>
          </div>
        </div>

        {/* Filtre */}
        {notlar.length > 0 && (
          <div className="inline-flex gap-1 p-1 rounded-xl bg-white/5 border border-white/10">
            <button onClick={() => setFiltre('hepsi')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${filtre === 'hepsi' ? 'bg-gradient-to-r from-brand-500 to-accent-500 text-white' : 'text-slate-300'}`}>Tümü ({notlar.length})</button>
            <button onClick={() => setFiltre('yapilacak')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${filtre === 'yapilacak' ? 'bg-gradient-to-r from-rose-500 to-pink-600 text-white' : 'text-slate-300'}`}>Yapılacak ({kalan})</button>
          </div>
        )}

        {/* Liste */}
        {gosterilen.length === 0 ? (
          <div className="card text-center py-8 text-sm text-slate-400">
            {filtre === 'yapilacak' ? 'Yapılacak not yok 🎉' : 'Henüz not yok. Yapacaklarını yaz — takip et. 📝'}
          </div>
        ) : (
          <div className="space-y-2">
            {gosterilen.map((n) => (
              <div key={n.id} className="card !py-2.5 flex items-start gap-3">
                <button onClick={() => toggle(n)} title={n.tamamlandi ? 'Geri al' : 'Tamamlandı'}
                  className={`shrink-0 mt-0.5 w-5 h-5 rounded-md border flex items-center justify-center transition ${n.tamamlandi ? 'bg-emerald-500/80 border-emerald-400 text-white' : 'border-white/25 text-transparent hover:border-emerald-400'}`}>
                  <Check size={13} />
                </button>
                <div className={`flex-1 min-w-0 text-sm whitespace-pre-wrap break-words ${n.tamamlandi ? 'text-slate-500 line-through' : 'text-slate-100'}`}>{n.metin}</div>
                {!n.tamamlandi && (
                  <button onClick={() => nav('/planim', { state: { gorev: n.metin } })} title="Plana görev olarak ekle"
                    className="shrink-0 text-slate-600 hover:text-teal-300"><CalendarPlus size={14} /></button>
                )}
                <button onClick={() => sil(n)} className="shrink-0 text-slate-600 hover:text-rose-400"><Trash2 size={14} /></button>
              </div>
            ))}
          </div>
        )}

        {!user && notlar.length > 0 && (
          <div className="text-[11px] text-slate-600 text-center px-2">
            <Link to="/giris" className="text-accent-300">Giriş yap</Link> → notların cihazlar arası senkronlanır.
          </div>
        )}
      </div>
    </>
  )
}
