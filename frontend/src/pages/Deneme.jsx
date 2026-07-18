import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Loader2, Plus, Trash2, TrendingUp, Target, X, LineChart, ArrowRight, Sparkles } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { apiFetch } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import { getUserProfile, watchDenemeler, addDeneme, removeDeneme, recordActivity } from '../firebase'
import {
  TYT_FIELDS, AYT_FIELDS, KPSS_FIELDS, LGS_FIELDS,
  denemeAlanlari, denemeHesaplaSinav, diploma100ToObp,
} from '../lib/yksHesap'

const DENEME_SINAVLAR = ['YKS', 'KPSS', 'LGS']
const TURLER = ['SAY', 'EA', 'SÖZ', 'DİL']
// Tüm sınavların ders etiketleri — geçmiş/zayıf ders gösterimi için
const ALL_LABELS = Object.fromEntries(
  [...TYT_FIELDS, ...AYT_FIELDS.SAY, ...AYT_FIELDS.EA, ...AYT_FIELDS.SÖZ, ...AYT_FIELDS.DİL,
    ...KPSS_FIELDS, ...LGS_FIELDS].map((f) => [f.id, { label: f.label, max: f.max }]))
const lsKey = (s) => 'unisense_deneme_' + s
const loadLocal = (s) => { try { return JSON.parse(localStorage.getItem(lsKey(s)) || '[]') } catch { return [] } }
const saveLocal = (s, a) => { try { localStorage.setItem(lsKey(s), JSON.stringify(a)) } catch { /* noop */ } }
const bugun = () => new Date().toISOString().slice(0, 10)

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
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState('')
  const [profil, setProfil] = useState(null)
  const [koc, setKoc] = useState('')
  const [kocLoading, setKocLoading] = useState(false)

  // Profilden varsayılan tür + diploma + koç için profil
  useEffect(() => {
    if (!user) return
    getUserProfile(user.uid).then((p) => {
      const pr = p?.profile || {}
      setProfil(pr)
      if (['YKS', 'KPSS', 'LGS'].includes(pr.examTrack)) setSinav(pr.examTrack)
      if (['SAY', 'EA', 'SÖZ', 'DİL'].includes(pr.scoreType)) setType(pr.scoreType)
      if (pr.diploma) setDiploma(String(pr.diploma))
    }).catch(() => {})
  }, [user])

  // Denemeleri yükle — sınav başına ayrı liste; girişli bulut, girişsiz localStorage
  useEffect(() => {
    setGirdi({})
    if (!user) { setDenemeler(loadLocal(sinav)); return }
    return watchDenemeler(user.uid, sinav, (items) => {
      if (items == null) { setDenemeler(loadLocal(sinav)); return }
      setDenemeler(items); saveLocal(sinav, items)
    })
  }, [user, sinav])

  const fields = useMemo(() => denemeAlanlari(sinav, type), [sinav, type])
  const canli = useMemo(
    () => denemeHesaplaSinav(sinav, type, girdi, diploma100ToObp(diploma)),
    [sinav, type, girdi, diploma],
  )

  function setDY(id, k, v) {
    const n = v === '' ? '' : Math.max(0, parseInt(v, 10) || 0)
    setGirdi((p) => ({ ...p, [id]: { ...p[id], [k]: n } }))
  }

  function flash(m) { setToast(m); setTimeout(() => setToast(''), 2500) }

  async function kaydet() {
    const minPuan = sinav === 'KPSS' ? 40 : 100
    if (canli.puan <= minPuan) { flash('Ders netlerini gir'); return }
    setSaving(true)
    let sira = null
    // Tahmini sıra sadece YKS'de (LGS yüzdelik, KPSS'de aday sırası verisi yok)
    if (sinav === 'YKS') {
      try {
        const r = await apiFetch(`/api/v1/hesap/siralama?puan=${canli.puan.toFixed(2)}&tur=${encodeURIComponent(type)}`)
        sira = r?.tahmini_sira ?? null
      } catch { /* sıra opsiyonel */ }
    }
    const deneme = {
      sinav, type: sinav === 'YKS' ? type : null, tarih, ad: ad || `${canli.puanTuru} Deneme`,
      dersNet: canli.dersNet, toplamNet: canli.toplamNet, puan: canli.puan, sira,
    }
    try {
      if (user) await addDeneme(user.uid, deneme)
      else { const a = [...denemeler, { ...deneme, id: 'l' + Date.now() }]; saveLocal(sinav, a); setDenemeler(a) }
      recordActivity(user?.uid).catch(() => {}) // günlük seri (streak)
      setGirdi({}); setAd(''); setShowForm(false)
      flash('✓ Deneme kaydedildi')
    } catch (e) { flash(e.message) } finally { setSaving(false) }
  }

  async function sil(d) {
    if (user && !String(d.id).startsWith('l')) { await removeDeneme(user.uid, d.id).catch(() => {}) }
    else { const a = denemeler.filter((x) => x.id !== d.id); saveLocal(sinav, a); setDenemeler(a) }
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

  async function kocIste() {
    if (!sirali.length) return
    setKocLoading(true); setKoc('')
    const sonlar = sirali.slice(-5).map((d) => `${d.tarih}: ${Math.round(d.toplamNet)} net`).join(', ')
    const zayifStr = zayif.map((z) => z.label).join(', ') || '—'
    const kim = sinav === 'YKS' ? `${type} (YKS)` : sinav
    const q = `${kim} öğrencisiyim, deneme netlerimi takip ediyorum. Son denemelerim: ${sonlar}. `
      + `En zayıf 3 dersim: ${zayifStr}.${son?.sira ? ` Tahmini başarı sıram ~${son.sira}.` : ''} `
      + `Bu verilere göre bana KISA, maddeler halinde uygulanabilir çalışma tavsiyesi ver: `
      + `hangi konulara öncelik vermeliyim ve netimi nasıl artırabilirim?`
    const uc = {}
    if (profil?.score) { uc.yks_puan = profil.score; if (profil.scoreType) uc.yks_turu = profil.scoreType }
    if (profil?.rank) uc.yks_sira = profil.rank
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
        <Seo title="Deneme Takibi — Net & Puan | YKS · KPSS · LGS | UniSense"
          description="YKS, KPSS ve LGS denemelerini kaydet: ders ders netini gir, tahmini puanını (ve YKS'de başarı sıranı + girebileceğin bölümleri) gör. Net trendini takip et — ücretsiz."
          path="/deneme" />
      )}
      {toast && <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl glass text-sm">{toast}</div>}
      <div className="max-w-3xl mx-auto space-y-5">
        {!embedded && (
          <div className="text-center">
            <h1 className="text-3xl md:text-4xl font-display font-bold text-white mb-1 flex items-center justify-center gap-2">
              <LineChart className="text-accent-300" /> Deneme Takibi
            </h1>
            <p className="text-slate-400 text-sm">Netini gir → tahmini puan{sinav === 'YKS' ? ', sıra ve girebileceğin bölümleri' : ''} gör. Trendini izle.</p>
          </div>
        )}

        {/* Sınav seçici — her sınavın denemeleri ayrı tutulur */}
        <div className="flex justify-center">
          <div className="inline-flex gap-1 p-1 rounded-xl bg-white/5 border border-white/10">
            {DENEME_SINAVLAR.map((s) => (
              <button key={s} onClick={() => { setSinav(s); setShowForm(false) }}
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

        {/* AI Koç — denemelerden kişisel tavsiye */}
        {sirali.length > 0 && (
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
              <p className="text-xs text-slate-400">Giriş yaparsan koç, denemelerine ve zayıf konularına göre sana özel çalışma tavsiyesi verir.</p>
            ) : koc ? (
              <div className="text-[13.5px] text-slate-200 whitespace-pre-wrap leading-relaxed">{koc}</div>
            ) : (
              <p className="text-xs text-slate-500">Denemelerine ve zayıf konularına göre kişisel tavsiye için “Tavsiye al”a bas.</p>
            )}
          </div>
        )}

        {/* Yeni deneme */}
        {!showForm ? (
          <button onClick={() => setShowForm(true)} className="btn-primary w-full inline-flex items-center justify-center gap-2">
            <Plus size={16} /> Yeni deneme ekle
          </button>
        ) : (
          <div className="card space-y-3">
            <div className="flex items-center justify-between">
              <div className="font-semibold text-white text-sm">Yeni deneme</div>
              <button onClick={() => setShowForm(false)} className="text-slate-500 hover:text-white"><X size={16} /></button>
            </div>
            <div className="flex flex-wrap gap-2 items-end">
              {sinav === 'YKS' && (
                <div>
                  <label className="text-[11px] text-slate-400">Puan türü</label>
                  <div className="flex gap-1 mt-1">
                    {TURLER.map((t) => (
                      <button key={t} onClick={() => setType(t)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${type === t ? 'bg-gradient-to-r from-brand-500 to-accent-500 text-white' : 'bg-white/5 text-slate-300'}`}>{t}</button>
                    ))}
                  </div>
                </div>
              )}
              <div><label className="text-[11px] text-slate-400">Tarih</label>
                <input type="date" value={tarih} onChange={(e) => setTarih(e.target.value)} className="input-glass block mt-1 text-sm" /></div>
              {sinav === 'YKS' && (
                <div><label className="text-[11px] text-slate-400">Diploma notu</label>
                  <input type="number" value={diploma} onChange={(e) => setDiploma(e.target.value)} placeholder="85" className="input-glass block mt-1 text-sm w-24" /></div>
              )}
              <div className="flex-1 min-w-[120px]"><label className="text-[11px] text-slate-400">Deneme adı (ops.)</label>
                <input value={ad} onChange={(e) => setAd(e.target.value)} placeholder="Deneme 5" className="input-glass block mt-1 text-sm w-full" /></div>
            </div>

            {/* Ders D/Y girişleri */}
            <div className="grid sm:grid-cols-2 gap-2">
              {fields.map((f) => {
                const g = girdi[f.id] || {}
                const net = ((parseFloat(g.d) || 0) - (f.pen || 0.25) * (parseFloat(g.y) || 0))
                return (
                  <div key={f.id} className="flex items-center gap-2 bg-white/[0.03] border border-white/8 rounded-lg px-2.5 py-1.5">
                    <span className="text-[12px] text-slate-300 flex-1 truncate">{f.label} <span className="text-slate-600">/{f.max}</span></span>
                    <input type="number" min="0" max={f.max} value={g.d ?? ''} onChange={(e) => setDY(f.id, 'd', e.target.value)} placeholder="D" className="input-glass w-12 text-center text-sm !py-1" />
                    <input type="number" min="0" max={f.max} value={g.y ?? ''} onChange={(e) => setDY(f.id, 'y', e.target.value)} placeholder="Y" className="input-glass w-12 text-center text-sm !py-1" />
                    <span className="text-[11px] font-mono w-10 text-right text-accent-300">{net ? net.toFixed(1) : '–'}</span>
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

        {/* Geçmiş */}
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

        {sirali.length === 0 && !showForm && (
          <div className="card text-center py-8 text-sm text-slate-400">
            Henüz deneme yok. İlk denemeni ekle — net trendini ve tahmini sıranı takip et. 📈
          </div>
        )}

        <div className="text-[11px] text-slate-600 text-center px-2">
          Puan/sıra TAHMİNÎDİR (yaklaşık ÖSYM katsayıları + program tabanları). {user ? 'Denemelerin hesabına kaydolur.' : 'Giriş yaparsan cihazlar arası senkronlanır.'}
        </div>
      </div>
    </>
  )
}
