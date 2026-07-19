import { useState, useEffect, useMemo, useRef } from 'react'
import { Link } from 'react-router-dom'
import { NotebookPen, Plus, Trash2, X, Check, RotateCcw, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { useAuth } from '../contexts/AuthContext'
import { watchYanlislar, addYanlis, updateYanlis, removeYanlis, recordActivity } from '../firebase'
import { sonrakiTekrar, tekrarZamani, bugunStr } from '../lib/tekrar'

const LS = 'unisense_yanlis'
const loadLocal = () => { try { return JSON.parse(localStorage.getItem(LS) || '[]') } catch { return [] } }
const saveLocal = (a) => { try { localStorage.setItem(LS, JSON.stringify(a)) } catch { /* noop */ } }
const KUTU_ETIKET = ['', 'Yeni', 'Tekrar 2', 'Tekrar 3', 'Pekişiyor', 'Öğrenildi']

export default function YanlisDefteri({ embedded = false }) {
  const { user } = useAuth()
  const [liste, setListe] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState('')
  const [filtre, setFiltre] = useState('hepsi') // hepsi | tekrar
  const [acik, setAcik] = useState(null)
  const [f, setF] = useState({ ders: '', konu: '', soru: '', neden: '' })

  const tasindi = useRef(false) // guest→bulut migration bir kez (duplike önlemi)
  useEffect(() => {
    if (!user) { setListe(loadLocal()); return }
    return watchYanlislar(user.uid, (items) => {
      if (items == null) { setListe(loadLocal()); return }
      const local = loadLocal()
      if (items.length === 0 && local.length > 0 && !tasindi.current) {
        // Bulut boş ama cihazda misafir yanlışları var → yukarı taşı (silme YOK)
        tasindi.current = true
        for (const y of local) {
          addYanlis(user.uid, {
            ders: String(y.ders || '').slice(0, 40), konu: String(y.konu || '').slice(0, 120),
            soru: String(y.soru || '').slice(0, 1000), neden: String(y.neden || '').slice(0, 1000),
            box: y.box || 1, nextReview: String(y.nextReview || '').slice(0, 20),
          }).catch(() => {})
        }
        setListe(local)
        return
      }
      setListe(items); saveLocal(items)
    })
  }, [user])

  function flash(m) { setToast(m); setTimeout(() => setToast(''), 2200) }

  const today = bugunStr()
  const tekrarSayisi = useMemo(() => liste.filter((y) => tekrarZamani(y, today)).length, [liste, today])
  const gosterilen = useMemo(
    () => (filtre === 'tekrar' ? liste.filter((y) => tekrarZamani(y, today)) : liste),
    [liste, filtre, today],
  )

  async function ekle() {
    if (!f.soru.trim()) { flash('Soruyu / neyi yanlış yaptığını yaz'); return }
    setSaving(true)
    const y = {
      ders: f.ders.trim(), konu: f.konu.trim(), soru: f.soru.trim(), neden: f.neden.trim(),
      box: 1, nextReview: today,
    }
    try {
      if (user) await addYanlis(user.uid, y)
      else { const a = [{ ...y, id: 'l' + Date.now(), createdAt: Date.now() }, ...liste]; saveLocal(a); setListe(a) }
      recordActivity(user?.uid).catch(() => {})
      setF({ ders: '', konu: '', soru: '', neden: '' }); setShowForm(false)
      flash('✓ Yanlış eklendi')
    } catch (e) { flash(e.message) } finally { setSaving(false) }
  }

  async function tekrarla(y, biliyor) {
    const patch = sonrakiTekrar(y.box || 1, biliyor)
    if (user && !String(y.id).startsWith('l')) { await updateYanlis(user.uid, y.id, patch).catch(() => {}) }
    else { const a = liste.map((x) => (x.id === y.id ? { ...x, ...patch } : x)); saveLocal(a); setListe(a) }
    recordActivity(user?.uid).catch(() => {})
  }

  async function sil(y) {
    if (user && !String(y.id).startsWith('l')) { await removeYanlis(user.uid, y.id).catch(() => {}) }
    else { const a = liste.filter((x) => x.id !== y.id); saveLocal(a); setListe(a) }
  }

  return (
    <>
      {!embedded && <BackgroundScene />}
      {!embedded && (
        <Seo title="Yanlış Defteri — Hatalarından Öğren | UniSense"
          description="Yanlış yaptığın soruları kaydet, sebebini yaz; aralıklı tekrarla kalıcı öğren. Ücretsiz dijital hata defteri." path="/yanlislarim" noindex />
      )}
      {toast && <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl glass text-sm">{toast}</div>}
      <div className="max-w-3xl mx-auto space-y-5">
        {!embedded && (
          <div className="text-center">
            <h1 className="text-3xl md:text-4xl font-display font-bold text-white mb-1 flex items-center justify-center gap-2">
              <NotebookPen className="text-rose-300" /> Yanlış Defteri
            </h1>
            <p className="text-slate-400 text-sm">Yanlışını kaydet, sebebini yaz — aralıklı tekrarla kalıcı öğren.</p>
          </div>
        )}

        {/* Filtre + tekrar rozeti */}
        <div className="flex items-center justify-between gap-2">
          <div className="inline-flex gap-1 p-1 rounded-xl bg-white/5 border border-white/10">
            <button onClick={() => setFiltre('hepsi')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${filtre === 'hepsi' ? 'bg-gradient-to-r from-brand-500 to-accent-500 text-white' : 'text-slate-300'}`}>Tümü ({liste.length})</button>
            <button onClick={() => setFiltre('tekrar')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${filtre === 'tekrar' ? 'bg-gradient-to-r from-rose-500 to-pink-600 text-white' : 'text-slate-300'}`}>Bugün tekrar ({tekrarSayisi})</button>
          </div>
          {!showForm && (
            <button onClick={() => setShowForm(true)} className="btn-primary text-sm inline-flex items-center gap-1.5">
              <Plus size={15} /> Ekle
            </button>
          )}
        </div>

        {/* Ekleme formu */}
        {showForm && (
          <div className="card space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="font-semibold text-white text-sm">Yeni yanlış</div>
              <button onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X size={16} /></button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <input value={f.ders} onChange={(e) => setF({ ...f, ders: e.target.value })} placeholder="Ders (ör. Matematik)" maxLength={40} className="input-glass text-sm" />
              <input value={f.konu} onChange={(e) => setF({ ...f, konu: e.target.value })} placeholder="Konu (ör. Türev)" maxLength={120} className="input-glass text-sm" />
            </div>
            <textarea value={f.soru} onChange={(e) => setF({ ...f, soru: e.target.value })} rows={2} maxLength={1000}
              placeholder="Soru / neyi yanlış yaptın? (kısa açıklama)" className="input-glass text-sm w-full resize-none" />
            <textarea value={f.neden} onChange={(e) => setF({ ...f, neden: e.target.value })} rows={2} maxLength={1000}
              placeholder="Neden yanlış yaptın / doğru yaklaşım nedir? (kendi notun)" className="input-glass text-sm w-full resize-none" />
            <div className="flex justify-end">
              <button onClick={ekle} disabled={saving} className="btn-primary text-sm inline-flex items-center gap-1.5 disabled:opacity-50">
                {saving ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />} Kaydet
              </button>
            </div>
          </div>
        )}

        {/* Liste */}
        {gosterilen.length === 0 ? (
          <div className="card text-center py-8 text-sm text-slate-400">
            {filtre === 'tekrar' ? 'Bugün tekrar edilecek yanlış yok 🎉' : 'Henüz yanlış eklenmedi. İlk yanlışını ekle — hatalarından öğren.'}
          </div>
        ) : (
          <div className="space-y-2">
            {gosterilen.map((y) => {
              const due = tekrarZamani(y, today)
              const open = acik === y.id
              return (
                <div key={y.id} className="card !py-3">
                  <div className="flex items-start justify-between gap-3">
                    <button onClick={() => setAcik(open ? null : y.id)} className="min-w-0 text-left flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        {y.ders && <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-slate-300">{y.ders}</span>}
                        {y.konu && <span className="text-[11px] text-accent-300">{y.konu}</span>}
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${due ? 'bg-rose-500/15 text-rose-300' : 'bg-emerald-500/10 text-emerald-300'}`}>{KUTU_ETIKET[y.box || 1]}</span>
                      </div>
                      <div className="text-sm text-white mt-1 truncate">{y.soru}</div>
                    </button>
                    <button onClick={() => setAcik(open ? null : y.id)} className="text-slate-500 shrink-0">{open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}</button>
                  </div>
                  {open && (
                    <div className="mt-2.5 pt-2.5 border-t border-white/5 space-y-2">
                      <div className="text-[13px] text-slate-200 whitespace-pre-wrap">{y.soru}</div>
                      {y.neden && (
                        <div className="text-[13px] text-slate-300 bg-white/[0.03] border border-white/8 rounded-lg px-3 py-2 whitespace-pre-wrap">
                          <span className="text-[10px] uppercase tracking-wider text-slate-500 block mb-0.5">Notum</span>{y.neden}
                        </div>
                      )}
                      <div className="flex items-center justify-between gap-2 pt-1">
                        <div className="flex gap-1.5">
                          <button onClick={() => tekrarla(y, true)} className="text-xs inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/25 hover:bg-emerald-500/20">
                            <Check size={13} /> Biliyorum
                          </button>
                          <button onClick={() => tekrarla(y, false)} className="text-xs inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/25 hover:bg-rose-500/20">
                            <RotateCcw size={13} /> Tekrar
                          </button>
                        </div>
                        <button onClick={() => sil(y)} className="text-slate-600 hover:text-rose-400"><Trash2 size={14} /></button>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {!user && liste.length > 0 && (
          <div className="text-[11px] text-slate-600 text-center px-2">
            <Link to="/giris" className="text-accent-300">Giriş yap</Link> → yanlışların cihazlar arası senkronlanır.
          </div>
        )}
      </div>
    </>
  )
}
