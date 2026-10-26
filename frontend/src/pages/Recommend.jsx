import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Loader2, ListChecks, Target, ShieldCheck, Mountain,
  TrendingUp, Building2, MapPin, UserCog, Sparkles,
  Compass, X, ArrowRight, Check, Plus,
  GraduationCap, Briefcase, AlertTriangle,
} from 'lucide-react'
import BackgroundScene from '../components/three/LazyBackgroundScene'
import { useAuth } from '../contexts/AuthContext'
import {
  useTercihList, useDgsTercih, useKpssTercih, useToast,
} from '@/services/hooks'
import { api } from '@/services/api'
import { dgsLevel, kpssLevel } from '../lib/riskLevels'
import { TR_ILLER } from '../lib/iller'
import MiniTrend from '../components/MiniTrend'
import { LgsRobot } from './LGS'
import { TusRobot } from './TusDus'
import { TERCIH_LIMITS, MAX_DGS_TERCIH, MAX_KPSS_TERCIH } from '@/services/constants'

// ===== Shared Components =====

const SCORE_TYPES = [
  { v: 'SAY', label: 'Sayısal', color: 'from-blue-500 to-cyan-400' },
  { v: 'EA', label: 'Eşit Ağırlık', color: 'from-emerald-500 to-teal-400' },
  { v: 'SÖZ', label: 'Sözel', color: 'from-rose-500 to-pink-400' },
  { v: 'DİL', label: 'Yabancı Dil', color: 'from-amber-500 to-orange-400' },
  { v: 'TYT', label: 'TYT', color: 'from-purple-500 to-violet-400' },
]

const CATEGORIES = [
  { key: 'safe', label: 'Güvenli', icon: ShieldCheck, color: 'from-emerald-500 to-emerald-700', desc: 'Garanti yerleşeceğin tercihler' },
  { key: 'target', label: 'Hedef', icon: Target, color: 'from-amber-500 to-orange-600', desc: 'Puanına en uygun tercihler' },
  { key: 'reach', label: 'Üst Seviye', icon: Mountain, color: 'from-rose-500 to-fuchsia-600', desc: 'Hedef üstü, denemeye değer' },
]

const ScoreTypePicker = ({ value, onChange }) => (
  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
    {SCORE_TYPES.map((s) => {
      const active = value === s.v
      return (
        <button key={s.v} type="button" onClick={() => onChange(s.v)}
          className={`relative px-3 py-3 rounded-xl text-sm font-medium transition-all ${
            active ? `bg-gradient-to-br ${s.color} text-white shadow-lg` : 'glass glass-hover text-slate-300'
          }`}>
          <div className="font-display font-bold text-lg">{s.v}</div>
          <div className={`text-[10px] ${active ? 'text-white/80' : 'text-slate-500'}`}>{s.label}</div>
        </button>
      )
    })}
  </div>
)

const SafetyBadge = ({ level }) => {
  const config = {
    safe: { label: 'Güvenli', icon: ShieldCheck, bg: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
    target: { label: 'Hedef', icon: Target, bg: 'bg-amber-500/15 text-amber-300 border-amber-500/30' },
    reach: { label: 'Üst Seviye', icon: Mountain, bg: 'bg-rose-500/15 text-rose-300 border-rose-500/30' },
  }
  const c = config[level] || config.target
  return <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${c.bg} border`}><c.icon size={9} /> {c.label}</span>
}

const ItemCard = ({ item, isInTercih, onAdd, onRemove, busyCode }) => {
  const code = String(item.department_code)
  const busy = busyCode === code
  const safety = item.safety_level || (item.placement_probability != null
    ? item.placement_probability >= 0.75 ? 'safe' : item.placement_probability >= 0.4 ? 'target' : 'reach'
    : null)
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card glass-hover p-4 group">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-white text-base truncate">{item.department_name}</h4>
          <div className="flex items-center gap-2 mt-1 text-xs text-slate-400 flex-wrap">
            <span className="flex items-center gap-1"><Building2 size={11} /> {item.university_name}</span>
            {item.city && <span className="flex items-center gap-1"><MapPin size={11} /> {item.city}</span>}
          </div>
        </div>
        {item.fit_score != null && (
          <div className="text-right shrink-0">
            <div className="text-xs text-slate-500">Uygunluk</div>
            <div className="font-display font-bold text-lg text-accent-300">%{item.fit_score.toFixed(0)}</div>
          </div>
        )}
      </div>
      {(item.scholarship || (item.education_language && item.education_language !== 'Türkçe') || item.duration_years || item.osym_conditions?.length > 0) && (
        <div className="flex flex-wrap items-center gap-1.5 mt-2">
          {item.scholarship && /burslu|ücretsiz/i.test(item.scholarship) && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">🎓 {item.scholarship}</span>}
          {item.scholarship && /ücretli|paralı/i.test(item.scholarship) && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/5 text-slate-300 border border-white/10">{item.scholarship}</span>}
          {item.education_language && item.education_language !== 'Türkçe' && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-sky-500/15 text-sky-300 border border-sky-500/25">{item.education_language}</span>}
          {item.duration_years && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/5 text-slate-400 border border-white/10">{item.duration_years} yıl</span>}
          {item.osym_conditions?.slice(0, 2).map((c, i) => (
            <span key={i} title={c} className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/25 inline-flex items-center gap-0.5"><AlertTriangle size={9} /> {c.length > 28 ? c.slice(0, 28) + '…' : c}</span>
          ))}
        </div>
      )}
      {(item.last_year_base_rank || item.last_year_base_score || item.placement_probability != null) && (
        <div className="mt-3 pt-3 border-t border-white/5 flex items-center gap-4 text-xs flex-wrap">
          {item.last_year_base_rank && <div><div className="text-slate-500">Sıra</div><div className="font-mono text-cyber-cyan">{item.last_year_base_rank.toLocaleString('tr')}</div></div>}
          {item.last_year_base_score && <div><div className="text-slate-500">Taban</div><div className="font-mono text-accent-300">{item.last_year_base_score.toFixed(2)}</div></div>}
          {item.trend?.filter((t) => t.base_rank != null).length >= 2 && <div><div className="text-slate-500">Trend</div><MiniTrend trend={item.trend} compact /></div>}
          {item.placement_probability != null && (() => {
            const pct = Math.round(item.placement_probability * 100)
            const color = pct >= 75 ? 'text-emerald-300 bg-emerald-500/10 border-emerald-500/30' : pct >= 40 ? 'text-amber-300 bg-amber-500/10 border-amber-500/30' : 'text-rose-300 bg-rose-500/10 border-rose-500/30'
            return <div className="ml-auto"><div className="text-slate-500 text-[10px] text-right">Yerleşme olasılığı</div><div className={`inline-flex items-center px-2 py-0.5 rounded-lg border font-mono font-semibold ${color}`} title="Geçen yılki sıraya göre tahmini sigmoid olasılık">%{pct}</div></div>
          })()}
        </div>
      )}
      {item.reason && <p className="mt-2 text-xs text-slate-400 italic">{item.reason}</p>}
      {(onAdd || onRemove) && (
        <div className="mt-3 pt-3 border-t border-white/5">
          {isInTercih ? (
            <button onClick={() => onRemove?.(item)} disabled={busy} title="Tercih listesinden çıkar"
              className="group/btn text-xs px-2.5 py-1.5 rounded-lg bg-emerald-500/15 hover:bg-rose-500/20 text-emerald-300 hover:text-rose-200 border border-emerald-500/30 hover:border-rose-500/40 transition inline-flex items-center gap-1 disabled:opacity-40">
              {busy ? <><Loader2 size={11} className="animate-spin" /> çıkartılıyor…</> : <><Check size={12} className="group-hover/btn:hidden" /><X size={12} className="hidden group-hover/btn:inline" /><span className="group-hover/btn:hidden">Tercih Listemde</span><span className="hidden group-hover/btn:inline">Listeden Çıkar</span></>}
            </button>
          ) : (
            <button onClick={() => onAdd?.(item)} disabled={busy}
              className="text-xs px-2.5 py-1.5 rounded-lg bg-accent-500/20 hover:bg-accent-500/40 text-accent-200 hover:text-white border border-accent-500/30 transition inline-flex items-center gap-1 disabled:opacity-40">
              {busy ? <Loader2 size={11} className="animate-spin" /> : <Plus size={12} />} Tercih Listeme Ekle
            </button>
          )}
        </div>
      )}
    </motion.div>
  )
}

const CategoryGroup = ({ cat, items, renderItem }) => {
  if (!items || items.length === 0) return null
  return (
    <div className="card">
      <div className="flex items-center gap-3 mb-4">
        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${cat.color} flex items-center justify-center shadow-lg`}><cat.icon size={18} className="text-white" /></div>
        <div><h3 className="font-display font-semibold text-lg text-white">{cat.label} <span className="text-slate-500 text-sm">({items.length})</span></h3><p className="text-xs text-slate-400">{cat.desc}</p></div>
      </div>
      <AnimatePresence initial={false}>
        <div className="grid md:grid-cols-2 gap-3">{items.map((it, i) => renderItem(it, i))}</div>
      </AnimatePresence>
    </div>
  )
}

const TercihToggleButton = ({ inList, busy, onToggle }) => inList ? (
  <button onClick={onToggle} disabled={busy} title="Tercih listesinden çıkar" className="text-xs px-2.5 py-1.5 rounded-lg bg-emerald-500/15 hover:bg-rose-500/20 text-emerald-300 hover:text-rose-200 border border-emerald-500/30 hover:border-rose-500/40 transition inline-flex items-center gap-1 disabled:opacity-40"><Check size={12} /> Listemde</button>
) : (
  <button onClick={onToggle} disabled={busy} className="text-xs px-2.5 py-1.5 rounded-lg bg-accent-500/20 hover:bg-accent-500/40 text-accent-200 hover:text-white border border-accent-500/30 transition inline-flex items-center gap-1 disabled:opacity-40"><Plus size={12} /> Tercihe Ekle</button>
)

const renderDgsCard = (p, { tercihIds, busyCode, toggleTercih, MAX_DGS_TERCIH }) => {
  const code = String(p.department_code)
  return (
    <div key={code} className="card glass-hover p-4 animate-fade-in-up">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0"><h4 className="font-semibold text-white text-sm">{p.program_adi}</h4>
          <div className="flex items-center gap-2 mt-1 text-xs text-slate-400 flex-wrap"><span className="flex items-center gap-1"><Building2 size={11} /> {p.university_name}</span>{p.city && <span className="flex items-center gap-1"><MapPin size={11} /> {p.city}</span>}</div></div>
        <div className="mt-3 pt-3 border-t border-white/5 flex items-center gap-4 text-xs flex-wrap">
          <div><div className="text-slate-500">Taban{p.yil ? ` (${p.yil})` : ''}</div><div className="font-mono text-accent-300">{p.min_puan != null ? p.min_puan.toFixed(2) : 'boş kaldı'}</div></div>
          <div><div className="text-slate-500">Kontenjan</div><div className="font-mono text-cyber-cyan">{p.kontenjan ?? '?'}</div></div>
          <div className="ml-auto"><TercihToggleButton inList={tercihIds.has(code)} busy={busyCode === code} onToggle={() => toggleTercih(p)} /></div>
        </div>
      </div>
    </div>
  )
}

const renderKpssCard = (k, { tercihIds, busyCode, toggleTercih, eslesmeBadge, MAX_KPSS_TERCIH }) => {
  const code = String(k.kadro_kodu)
  return (
    <div key={code} className="card glass-hover p-4 animate-fade-in-up">
      <div className="flex items-start justify-between gap-2"><div className="flex-1 min-w-0"><h4 className="font-semibold text-white text-sm">{k.unvan}</h4><div className="text-xs text-slate-400 mt-1">{k.kurum}</div><div className="flex items-center gap-2 mt-1.5 text-[11px] text-slate-500 flex-wrap">{k.il && <span className="flex items-center gap-1"><MapPin size={10} /> {k.il}</span>}<span>{k.duzey}</span><span className="font-mono">{k.puan_turu}</span>{eslesmeBadge(k.eslesme)}</div></div></div>
      {k.ozel_kosullar?.length > 0 && <div className="mt-2 space-y-1">{k.ozel_kosullar.map((o, i) => <div key={i} className="text-[10px] text-amber-300 flex items-start gap-1"><AlertTriangle size={10} className="shrink-0 mt-0.5" /> {o}</div>)}</div>}
      <div className="mt-3 pt-3 border-t border-white/5 flex items-center gap-4 text-xs flex-wrap"><div><div className="text-slate-500">Geçmiş taban</div><div className="font-mono text-accent-300">{k.gecmis_taban != null ? k.gecmis_taban.toFixed(2) : 'bilinmiyor'}</div></div><div><div className="text-slate-500">Kontenjan</div><div className="font-mono text-cyber-cyan">{k.kontenjan ?? '?'}</div></div><div className="ml-auto"><TercihToggleButton inList={tercihIds.has(code)} busy={busyCode === code} onToggle={() => toggleTercih(k)} /></div></div>
    </div>
  )
}

// ===== DGS Panel =====
const DgsOneriPanel = ({ user, profile }) => {
  const [puan, setPuan] = useState('')
  const [pt, setPt] = useState('SAY')
  const [bolum, setBolum] = useState('')
  const [il, setIl] = useState('')
  const [uniType, setUniType] = useState('all')
  const [res, setRes] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [onlisans, setOnlisans] = useState('')
  const [onlisansListe, setOnlisansListe] = useState([])
  const [gecis, setGecis] = useState(null)
  const [gecisLoading, setGecisLoading] = useState(false)
  const { tercihIds, busyCode, setBusyCode } = useDgsTercih()
  const { show: showToast } = useToast()

  useEffect(() => {
    api.dgsGecis('').then(d => setOnlisansListe([...new Set(d.programlar || [])])).catch(() => {})
  }, [])

  async function gecisAra() {
    if (!onlisans.trim()) return
    setGecisLoading(true)
    try { const d = await api.dgsGecis(onlisans); setGecis(d.gruplar || []) } catch (e) { setError(e.message) } finally { setGecisLoading(false) }
  }

  function lisansSec(ad) { setBolum(ad); setGecis(null); const p = parseFloat(puan); if (p >= 100 && p <= 600) setTimeout(() => ara(ad), 0) }

  useEffect(() => { if (!profile) return; if (profile.dgs?.score != null) setPuan(String(profile.dgs.score)); if (profile.dgs?.type) setPt(profile.dgs.type); if (profile.preferredUniType) setUniType(profile.preferredUniType) }, [profile])

  async function ara(bolumOverride) {
    const p = parseFloat(puan)
    if (!p || p < 100 || p > 600) { setError('Geçerli bir DGS puanı gir (100–600)'); return }
    setLoading(true); setError('')
    try {
      const d = await api.dgsProgramlar({ puan_turu: pt, puan: p, bolum: bolumOverride ?? bolum, il: il.trim() || null, uni_turu: uniType === 'all' ? null : uniType, oneri: true, limit: 100 })
      setRes({ ...d, puan: p })
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }

  function onSubmit(e) { e.preventDefault(); ara() }

  useEffect(() => { if (res) ara() }, [uniType])

  async function toggleTercih(item) {
    if (!user) { showToast('Giriş yapman gerek', { type: 'error' }); return }
    const code = String(item.department_code)
    setBusyCode(code); setError('')
    try {
      if (tercihIds.has(code)) { await import('@/services/firestore-prefs').then(m => m.removeFromDgsTercih(user.uid, code)) }
      else {
        if (tercihIds.size >= MAX_DGS_TERCIH) { setError(`DGS tercih listesi dolu (max ${MAX_DGS_TERCIH})`); return }
        await import('@/services/firestore-prefs').then(m => m.addToDgsTercih(user.uid, { ...item, puan_turu: pt }, tercihIds.size + 1))
      }
    } catch (e) { setError(e.message) } finally { setBusyCode(null) }
  }

  const groups = { safe: [], target: [], reach: [], bos: [] }
  if (res) { for (const it of res.items) { groups[dgsLevel(res.puan, it.min_puan)].push(it) } }
  const hicYok = res && res.items.length === 0
  const BOS_CAT = { key: 'bos', label: 'Geçen Yıl Boş Kalanlar', icon: GraduationCap, color: 'from-slate-500 to-slate-700', desc: 'Taban oluşmadı — yerleşme şansı yüksek ama kontenjan ve koşulları kontrol et' }

  const renderCard = (p) => renderDgsCard(p, { tercihIds, busyCode, toggleTercih, MAX_DGS_TERCIH })

  return (
    <div className="space-y-6">
      {user && profile?.dgs?.score != null && (
        <div className="card border-accent-500/30 bg-accent-500/10 flex items-center gap-3 text-sm"><Sparkles size={14} className="text-accent-300 shrink-0" /><div className="flex-1 text-accent-100">DGS puanın <strong>profilden geldi</strong>.</div><Link to="/profil" className="text-xs px-2.5 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-accent-200 transition shrink-0"><UserCog size={12} className="inline mr-1" />Düzenle</Link></div>
      )}
      <form onSubmit={onSubmit} className="card space-y-4">
        <div className="grid sm:grid-cols-2 gap-4">
          <div><label className="text-sm text-slate-300 mb-2 block">DGS Puanın</label><input type="number" step="0.01" value={puan} onChange={e => setPuan(e.target.value)} placeholder="örn: 285.40" className="input-glass" /></div>
          <div><label className="text-sm text-slate-300 mb-2 block">Puan Türü</label><div className="grid grid-cols-3 gap-2">{['SAY', 'EA', 'SÖZ'].map(t => <button key={t} type="button" onClick={() => setPt(t)} className={`px-3 py-2.5 rounded-xl text-sm font-semibold transition ${pt === t ? 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-lg' : 'glass glass-hover text-slate-300'}`}>{t}</button>)}</div></div>
        </div>
        <div className="rounded-xl bg-white/5 border border-white/5 p-3 space-y-2">
          <div className="text-xs text-slate-300 font-medium">Önlisans bölümünü yaz → geçebileceğin lisans bölümlerini gör</div>
          <div className="flex gap-2"><input value={onlisans} onChange={e => setOnlisans(e.target.value)} list="dgs-onlisans-programlar" placeholder="örn: Bilgisayar Programcılığı" className="input-glass text-sm flex-1 !py-2" /><datalist id="dgs-onlisans-programlar">{onlisansListe.map(a => <option key={a} value={a} />)}</datalist><button type="button" onClick={gecisAra} disabled={gecisLoading || !onlisans.trim()} className="btn-ghost text-xs disabled:opacity-50">{gecisLoading ? <Loader2 size={12} className="animate-spin" /> : 'Geçiş yolları'}</button></div>
          {gecis && gecis.length === 0 && <div className="text-[11px] text-slate-500">Eşleşen alan bulunamadı — farklı yazımla dene</div>}
          {gecis && gecis.map((g, gi) => (
            <div key={`${g.alan}-${gi}`} className="space-y-1.5">
              <div className="text-[10px] text-slate-500">{g.alan}</div>
              <div className="flex flex-wrap gap-1.5">
                {g.lisans.map(l => <button key={l.kod} type="button" onClick={() => lisansSec(l.ad)} title={`${l.ad} programlarını tabanlarıyla listele`} className="rounded-lg px-2 py-1 text-[11px] border border-accent-500/30 text-accent-300 hover:bg-accent-500/10">{l.ad} <span className="text-slate-500">· {l.puan_turu}</span></button>)}
              </div>
            </div>
          ))}
        </div>
        <div className="grid sm:grid-cols-2 gap-4"><div><label className="text-sm text-slate-300 mb-2 block">Bölüm filtresi <span className="text-slate-500">(opsiyonel)</span></label><input value={bolum} onChange={e => setBolum(e.target.value)} placeholder="örn: bilgisayar — boş = hepsi" className="input-glass" /></div><div><label className="text-sm text-slate-300 mb-2 block">Şehir <span className="text-slate-500">(opsiyonel)</span></label><input value={il} onChange={e => setIl(e.target.value)} placeholder="örn: İstanbul" className="input-glass" /></div></div>
        <div><label className="text-sm text-slate-300 mb-2 block">Üniversite Tipi</label><div className="flex gap-2">{[['all', 'Hepsi'], ['Devlet', 'Devlet'], ['Vakıf', 'Vakıf (Özel)']].map(([v, l]) => <button key={v} type="button" onClick={() => setUniType(v)} className={`px-3 py-2 rounded-xl text-sm transition ${uniType === v ? 'bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-lg' : 'glass glass-hover text-slate-300'}`}>{l}</button>)}</div></div>
        {error && <div className="text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-3">⚠️ {error}</div>}
        <button type="submit" disabled={loading} className="btn-primary w-full inline-flex items-center justify-center gap-2 disabled:opacity-50">{loading ? <><Loader2 size={18} className="animate-spin" /> Programlar bulunuyor…</> : <><GraduationCap size={18} /> DGS Puanımla Tercih Öner</>}</button>
      </form>
      {res && (
        <div className="space-y-4">
          {user && <div className="flex items-center justify-between gap-3 px-1 text-xs"><span className="text-slate-400">DGS Tercih Listende:{' '}<strong className={tercihIds.size >= MAX_DGS_TERCIH ? 'text-rose-400' : 'text-emerald-400'}>{tercihIds.size}/{MAX_DGS_TERCIH}</strong></span><Link to="/tercih" className="text-accent-300 hover:text-accent-200 transition flex items-center gap-1">Tercih Listemi Gör <ArrowRight size={11} /></Link></div>}
          {error && <div className="text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-3">⚠️ {error}</div>}
          {hicYok && <div className="card border-rose-500/30 bg-rose-500/10 text-center py-8"><div className="text-rose-200 font-medium mb-2">Bu filtrelerle uygun program bulunamadı</div><div className="text-sm text-rose-200/70">Bölüm/şehir filtresini kaldırmayı veya üniversite tipini genişletmeyi dene.</div></div>}
          {CATEGORIES.map(cat => <CategoryGroup key={cat.key} cat={cat} items={groups[cat.key]} renderItem={renderCard} />)}
          <CategoryGroup cat={BOS_CAT} items={groups.bos} renderItem={renderCard} />
          {res.uyari && <div className="text-[11px] text-slate-500 px-1">{res.uyari}</div>}
        </div>
      )}
    </div>
  )
}

// ===== KPSS Panel =====
const KpssOneriPanel = ({ user, profile }) => {
  const [puan, setPuan] = useState('')
  const [duzey, setDuzey] = useState('lisans')
  const [bolum, setBolum] = useState('')
  const [secliIller, setSecliIller] = useState([])
  const [res, setRes] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { tercihIds, busyCode, setBusyCode } = useKpssTercih()
  const { show: showToast } = useToast()

  useEffect(() => { if (!profile) return; if (profile.kpss?.score != null) setPuan(String(profile.kpss.score)); if (profile.kpss?.duzey) setDuzey(profile.kpss.duzey); if (Array.isArray(profile.preferredCities) && profile.preferredCities.length) setSecliIller(prev => prev.length ? prev : profile.preferredCities) }, [profile])

  function ilEkle(v) { if (!v) return; setSecliIller(prev => prev.includes(v) ? prev : [...prev, v]) }

  async function onSubmit(e) {
    e.preventDefault()
    const p = parseFloat(puan)
    if (!p || p < 40 || p > 120) { setError('Geçerli bir KPSS GY-GK puanı gir (40–120)'); return }
    setLoading(true); setError('')
    try {
      const d = await api.kpssKadrolar({ bolum, duzey, iller: secliIller.length ? secliIller : null, puan: p, limit: 100 })
      setRes({ ...d, puan: p })
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }

  async function toggleTercih(k) {
    if (!user) { showToast('Giriş yapman gerek', { type: 'error' }); return }
    const code = String(k.kadro_kodu)
    setBusyCode(code); setError('')
    try {
      if (tercihIds.has(code)) { await import('@/services/firestore-prefs').then(m => m.removeFromKpssTercih(user.uid, code)) }
      else {
        if (tercihIds.size >= MAX_KPSS_TERCIH) { setError(`KPSS tercih listesi dolu (max ${MAX_KPSS_TERCIH})`); return }
        await import('@/services/firestore-prefs').then(m => m.addToKpssTercih(user.uid, k, tercihIds.size + 1))
      }
    } catch (e) { setError(e.message) } finally { setBusyCode(null) }
  }

  const groups = { safe: [], target: [], reach: [], bilinmez: [] }
  if (res) { for (const k of res.items) { groups[kpssLevel(res.puan, k.gecmis_taban)].push(k) } }
  const hicYok = res && res.items.length === 0

  const eslesmeBadge = (e) => { if (!e) return null; const cls = e.includes('✓') ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' : e === 'bölüme özel' ? 'bg-sky-500/15 text-sky-300 border-sky-500/30' : 'bg-white/5 text-slate-400 border-white/10'; return <span className={`text-[10px] px-2 py-0.5 rounded-full border ${cls}`}>{e}</span> }

  const renderCard = (k) => renderKpssCard(k, { tercihIds, busyCode, toggleTercih, eslesmeBadge, MAX_KPSS_TERCIH })

  const BILINMEZ_CAT = { key: 'bilinmez', label: 'Taban Bilinmiyor', icon: Briefcase, color: 'from-slate-500 to-slate-700', desc: 'Geçmiş dönem yerleştirme verisi eşleşmedi — nitelikleri kontrol ederek değerlendir' }

  return (
    <div className="space-y-6">
      {user && profile?.kpss?.score != null && <div className="card border-accent-500/30 bg-accent-500/10 flex items-center gap-3 text-sm"><Sparkles size={14} className="text-accent-300 shrink-0" /><div className="flex-1 text-accent-100">KPSS puanın ve düzeyin <strong>profilden geldi</strong>.</div><Link to="/profil" className="text-xs px-2.5 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-accent-200 transition shrink-0"><UserCog size={12} className="inline mr-1" />Düzenle</Link></div>}
      <form onSubmit={onSubmit} className="card space-y-4">
        <div className="grid sm:grid-cols-2 gap-4"><div><label className="text-sm text-slate-300 mb-2 block">KPSS Puanın (GY-GK)</label><input type="number" step="0.01" value={puan} onChange={e => setPuan(e.target.value)} placeholder="örn: 82.35" className="input-glass" /></div><div><label className="text-sm text-slate-300 mb-2 block">Düzey</label><div className="grid grid-cols-3 gap-2">{['lisans', 'önlisans', 'ortaöğretim'].map(d => <button key={d} type="button" onClick={() => setDuzey(d)} className={`px-2 py-2.5 rounded-xl text-xs font-semibold transition ${duzey === d ? 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-lg' : 'glass glass-hover text-slate-300'}`}>{d}</button>)}</div></div></div>
        <div className="grid sm:grid-cols-2 gap-4"><div><label className="text-sm text-slate-300 mb-2 block">Mezun olduğun bölüm <span className="text-slate-500">(nitelik eşleşmesi için)</span></label><input value={bolum} onChange={e => setBolum(e.target.value)} placeholder="örn: Bilgisayar Mühendisliği" className="input-glass" /></div><div><label className="text-sm text-slate-300 mb-2 block">Şehir ekle <span className="text-slate-500">(birden çok seçebilirsin — boş = tümü)</span></label><select value="" onChange={e => ilEkle(e.target.value)} className="input-glass w-full"><option value="" disabled>Şehir seçin…</option>{TR_ILLER.filter(i => !secliIller.includes(i)).map(i => <option key={i} value={i}>{i}</option>)}</select></div></div>
        {secliIller.length > 0 && <div className="flex flex-wrap gap-1.5">{secliIller.map(i => <span key={i} className="text-xs px-2.5 py-1 rounded-full bg-sky-500/15 text-sky-200 border border-sky-500/25 inline-flex items-center gap-1.5">{i}<button type="button" onClick={() => setSecliIller(prev => prev.filter(x => x !== i))} className="opacity-60 hover:opacity-100 hover:text-rose-300 transition">✕</button></span>)}</div>}
        {error && <div className="text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-3">⚠️ {error}</div>}
        <button type="submit" disabled={loading} className="btn-primary w-full inline-flex items-center justify-center gap-2 disabled:opacity-50">{loading ? <><Loader2 size={18} className="animate-spin" /> Kadrolar bulunuyor…</> : <><Briefcase size={18} /> KPSS Puanımla Kadro Öner</>}</button>
      </form>
      {res && (
        <div className="space-y-4">
          {user && <div className="flex items-center justify-between gap-3 px-1 text-xs"><span className="text-slate-400">KPSS Tercih Listende:{' '}<strong className={tercihIds.size >= MAX_KPSS_TERCIH ? 'text-rose-400' : 'text-emerald-400'}>{tercihIds.size}/{MAX_KPSS_TERCIH}</strong></span><Link to="/tercih" className="text-accent-300 hover:text-accent-200 transition flex items-center gap-1">Tercih Listemi Gör <ArrowRight size={11} /></Link></div>}
          {error && <div className="text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-3">⚠️ {error}</div>}
          {hicYok && <div className="card border-rose-500/30 bg-rose-500/10 text-center py-8"><div className="text-rose-200 font-medium mb-2">Bu filtrelerle uygun kadro bulunamadı</div><div className="text-sm text-rose-200/70">Bölüm adını farklı yazmayı veya şehir filtresini kaldırmayı dene.</div></div>}
          {CATEGORIES.map(cat => <CategoryGroup key={cat.key} cat={cat} items={groups[cat.key]} renderItem={renderCard} />)}
          <CategoryGroup cat={BILINMEZ_CAT} items={groups.bilinmez} renderItem={renderCard} />
          {res.uyari && <div className="text-[11px] text-slate-500 px-1">{res.uyari}</div>}
        </div>
      )}
    </div>
  )
}

// ===== Main Recommend Component =====
export default function Recommend() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [scoreType, setScoreType] = useState('SAY')
  const [score, setScore] = useState('')
  const [rank, setRank] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [profileLoaded, setProfileLoaded] = useState(false)
  const [autofilled, setAutofilled] = useState(false)
  const [pusulaState, setPusulaState] = useState(null)
  const [tercihIds, setTercihIds] = useState(new Set())
  const [busyCode, setBusyCode] = useState(null)
  const [tercihError, setTercihError] = useState('')
  const [uniType, setUniType] = useState('all')
  const [mode, setMode] = useState('YKS')
  const [profile, setProfile] = useState(null)
  const [bolumInput, setBolumInput] = useState('')
  const userPickedMode = useRef(false)
  const { show: showToast } = useToast()

  const { tercihIds: yksTercihIds, busyCode: yksBusyCode, setBusyCode: setYksBusyCode } = useTercihList()

  useEffect(() => { try { const raw = sessionStorage.getItem('pusula_depts'); if (raw) { const parsed = JSON.parse(raw); if (parsed?.names?.length) setPusulaState(parsed) } } catch (e) { console.warn('Pusula state okunamadı:', e) } }, [])

  useEffect(() => { if (!user) { setTercihIds(new Set()); return } const unsub = import('@/services/firestore-prefs').then(m => m.watchTercihList(user.uid, items => setTercihIds(new Set(items.map(i => String(i.department_code || i.id)))))); return () => unsub.then(unsub => unsub?.()) }, [user])

  async function handleAddToTercih(item) {
    if (!user) { setTercihError('Giriş yapman gerek'); return }
    if (yksTercihIds.size >= TERCIH_LIMITS.YKS) { setTercihError('Tercih listesi 24 dolu'); return }
    const code = String(item.department_code)
    setYksBusyCode(code); setTercihError('')
    try { await import('@/services/firestore-prefs').then(m => m.addToTercih(user.uid, item, yksTercihIds.size + 1)) } catch (e) { setTercihError(e.message || 'Eklenemedi') } finally { setYksBusyCode(null) }
  }

  async function handleRemoveFromTercih(item) {
    if (!user) return
    const code = String(item.department_code)
    setYksBusyCode(code); setTercihError('')
    try { await import('@/services/firestore-prefs').then(m => m.removeFromTercih(user.uid, code)) } catch (e) { setTercihError(e.message || 'Çıkarılamadı') } finally { setYksBusyCode(null) }
  }

  useEffect(() => {
    let cancelled = false
    if (!user) { setProfileLoaded(true); return }
    ;(async () => {
      try {
        const data = await import('@/services/firestore-core').then(m => m.getUserProfile(user.uid))
        if (cancelled) return
        const p = data?.profile
        if (p) {
          setProfile(p)
          if (!userPickedMode.current) { const t = p.examTrack === 'DUS' ? 'TUS' : p.examTrack; if (['DGS', 'KPSS', 'TUS', 'LGS'].includes(t)) setMode(t) }
          let filled = false
          if (p.scoreType) { setScoreType(p.scoreType); filled = true }
          if (p.score != null && p.score !== '') { setScore(String(p.score)); filled = true }
          if (p.rank != null && p.rank !== '') { setRank(String(p.rank)); filled = true }
          if (p.preferredUniType) { setUniType(p.preferredUniType); filled = true }
          setAutofilled(filled)
        }
      } catch (err) { console.warn('Profil yüklenemedi:', err) } finally { if (!cancelled) setProfileLoaded(true) }
    })()
    return () => { cancelled = true }
  }, [user])

  function clearPusula() { sessionStorage.removeItem('pusula_depts'); setPusulaState(null); setResult(null) }

  function removeDept(name) { if (!pusulaState) return; const next = { ...pusulaState, names: pusulaState.names.filter(n => n !== name) }; if (next.names.length === 0) { clearPusula(); return } setPusulaState(next); sessionStorage.setItem('pusula_depts', JSON.stringify(next)) }

  async function runRecommend() {
    if (!score && !rank) { setError('Lütfen puan veya sıralama gir'); return }
    setLoading(true); setError('')
    try {
      const manuel = bolumInput.split(',').map(s => s.trim()).filter(Boolean)
      const data = await api.recommend({ score_type: scoreType, score: score ? parseFloat(score) : null, rank: rank ? parseInt(rank, 10) : null, preferred_departments: [...(pusulaState?.names || []), ...manuel], preferred_uni_types: uniType === 'all' ? [] : [uniType] })
      setResult(data)
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }

  function onSubmit(e) { e.preventDefault(); runRecommend() }

  useEffect(() => { if (result && mode === 'YKS') runRecommend() }, [uniType])

  const modeLabel = pusulaState?.mode === 'interests' ? 'İlgilerine göre' : pusulaState?.mode === 'text' ? 'Yazdığın metne göre' : pusulaState?.mode === 'axes' ? '5 sorulu testin sonucuna göre' : 'Pusula sonucu'

  const SUBTITLES = { YKS: <>Puanına uygun <strong className="text-emerald-400">güvenli</strong>,{' '}<strong className="text-amber-400">hedef</strong> ve{' '}<strong className="text-rose-400">üst seviye</strong> üniversite tercihleri.</>, DGS: <>DGS puanınla geçebileceğin lisans programları —{' '}<strong className="text-emerald-400">güvenli</strong>,{' '}<strong className="text-amber-400">hedef</strong> ve{' '}<strong className="text-rose-400">üst seviye</strong>.</>, KPSS: <>KPSS puanına ve mezuniyetine göre başvurabileceğin{' '}<strong className="text-accent-300">aktif dönem kadroları</strong>.</>, TUS: <>TUS/DUS puanınla yerleşebileceğin{' '}<strong className="text-sky-300">uzmanlık programları</strong>.</>, LGS: <>LGS yüzdelik dilimine göre girebileceğin{' '}<strong className="text-emerald-300">liseler</strong>.</> }

  return (
    <>
      <BackgroundScene />
      <div className="space-y-6">
        <div className="text-center mb-2">
          <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-4xl md:text-5xl font-display font-bold text-white mb-2">Tercih <span className="gradient-text">Asistanın</span></motion.h1>
          <p className="text-slate-400 max-w-xl mx-auto">{SUBTITLES[mode]}</p>
        </div>
        <div className="flex justify-center gap-2 flex-wrap">{['YKS', 'DGS', 'KPSS', 'TUS', 'LGS'].map(m => <button key={m} onClick={() => { userPickedMode.current = true; setMode(m) }} className={`px-5 py-2 rounded-xl text-sm font-semibold transition ${mode === m ? 'bg-gradient-to-br from-brand-500 to-accent-500 text-white shadow-lg' : 'glass glass-hover text-slate-300'}`}>{m}</button>)}</div>
        {mode === 'DGS' && <DgsOneriPanel user={user} profile={profile} />}
        {mode === 'KPSS' && <KpssOneriPanel user={user} profile={profile} />}
        {mode === 'TUS' && <TusRobot />}
        {mode === 'LGS' && <LgsRobot />}
        {mode === 'YKS' && (
          <>
            {pusulaState?.names?.length > 0 ? (
              <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="card border-emerald-500/30 bg-emerald-500/5">
                <div className="flex items-center justify-between mb-3 flex-wrap gap-2"><div className="flex items-center gap-3"><div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center shrink-0"><Compass size={16} className="text-white" /></div><div><div className="text-sm font-semibold text-white">Pusula Bölümlerin</div><div className="text-xs text-slate-400">{modeLabel} · {pusulaState.names.length} bölüm</div></div></div><div className="flex gap-2"><button onClick={() => navigate('/pusula')} className="text-xs px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-accent-500/20 text-slate-300 hover:text-accent-200 transition flex items-center gap-1"><Compass size={12} /> Pusulaya Dön</button><button onClick={clearPusula} className="text-xs px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-rose-500/20 text-slate-400 hover:text-rose-200 transition flex items-center gap-1"><X size={12} /> Temizle</button></div></div><div className="flex flex-wrap gap-1.5">{pusulaState.names.map(n => <span key={n} className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-200 border border-emerald-500/25 flex items-center gap-1 group"><Check size={11} className="opacity-70" />{n}<button onClick={() => removeDept(n)} title="Listeden çıkar" className="opacity-50 hover:opacity-100 hover:text-rose-300 transition"><X size={11} /></button></span>)}</div></motion.div>
            ) : (
              <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="card border-accent-500/30 bg-accent-500/5 flex items-center gap-3"><div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-accent-500 flex items-center justify-center shrink-0"><ListChecks size={16} className="text-white" /></div><div className="flex-1 text-sm text-slate-200">Aşağıya bölüm yazabilir veya boş bırakıp <strong className="text-accent-200">puana göre tüm bölümlerden</strong> öneri alabilirsin.<span className="text-slate-400"> Ne okuyacağını bilmiyor musun?</span><button onClick={() => navigate('/pusula')} className="ml-1 text-accent-300 hover:underline inline-flex items-center gap-1"><Compass size={12} /> İlgi Pusulası'yla keşfet →</button></div></motion.div>
            )}
            {user && profileLoaded && (autofilled ? (
              <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="card border-accent-500/30 bg-accent-500/10 flex items-center gap-3 text-sm"><div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-accent-500 flex items-center justify-center shrink-0"><Sparkles size={14} className="text-white" /></div><div className="flex-1 text-accent-100">Puan/sıra bilgilerin <strong>profilden geldi</strong>.</div><Link to="/profil" className="text-xs px-2.5 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-accent-200 transition flex items-center gap-1 shrink-0"><UserCog size={12} /> Düzenle</Link></motion.div>
            ) : (
              <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="card border-slate-500/30 bg-white/5 flex items-center gap-3 text-sm"><UserCog size={16} className="text-slate-400 shrink-0" /><div className="flex-1 text-slate-300">Puan/sıra bilgini profiline kaydedersen bir dahaki sefere otomatik dolar.</div><Link to="/profil" className="text-xs px-2.5 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-slate-200 transition shrink-0">Profile Git →</Link></motion.div>
            ))}
            <form onSubmit={onSubmit} className="card space-y-5">
              <div><label className="text-sm text-slate-300 mb-2 block">Puan Türü</label><ScoreTypePicker value={scoreType} onChange={setScoreType} /></div>
              <div className="grid sm:grid-cols-2 gap-4"><div><label className="text-sm text-slate-300 mb-2 block">YKS Puanı</label><input type="number" step="0.01" value={score} onChange={e => setScore(e.target.value)} placeholder="örn: 480.50" className="input-glass" /></div><div><label className="text-sm text-slate-300 mb-2 block">Başarı Sırası</label><input type="number" value={rank} onChange={e => setRank(e.target.value)} placeholder="örn: 5000" className="input-glass" /></div></div>
              <div><label className="text-sm text-slate-300 mb-2 block">Bölüm filtresi <span className="text-slate-500">(opsiyonel — virgülle çoklu)</span></label><input value={bolumInput} onChange={e => setBolumInput(e.target.value)} placeholder="örn: bilgisayar, tıp, mühendislik" className="input-glass" /></div>
              <div><label className="text-sm text-slate-300 mb-2 block">Üniversite Tipi</label><div className="flex gap-2">{[['all', 'Hepsi'], ['Devlet', 'Devlet'], ['Vakıf', 'Vakıf (Özel)']].map(([v, l]) => <button key={v} type="button" onClick={() => setUniType(v)} className={`px-3 py-2 rounded-xl text-sm transition ${uniType === v ? 'bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-lg' : 'glass glass-hover text-slate-300'}`}>{l}</button>)}</div></div>
              {error && <div className="text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-3">⚠️ {error}</div>}
              <button type="submit" disabled={loading} className="btn-primary w-full inline-flex items-center justify-center gap-2 disabled:opacity-50">{loading ? <><Loader2 size={18} className="animate-spin" /> Öneriler getiriliyor…</> : <><ListChecks size={18} /> Tercih Öner</>}</button>
            </form>
            {result && (
              <div className="space-y-4">
                {user && <div className="flex items-center justify-between gap-3 px-1 text-xs"><span className="text-slate-400">YKS Tercih Listende:{' '}<strong className={yksTercihIds.size >= TERCIH_LIMITS.YKS ? 'text-rose-400' : 'text-emerald-400'}>{yksTercihIds.size}/{TERCIH_LIMITS.YKS}</strong></span><Link to="/tercih" className="text-accent-300 hover:text-accent-200 transition flex items-center gap-1">Tercih Listemi Gör <ArrowRight size={11} /></Link></div>}
                {tercihError && <div className="text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-3">⚠️ {tercihError}</div>}
                {result.safe.length === 0 && result.target.length === 0 && result.reach.length === 0 && <div className="card border-rose-500/30 bg-rose-500/10 text-center py-8"><div className="text-rose-200 font-medium mb-2">Bu puan ve filtrelerle uygun bölüm bulunamadı</div><div className="text-sm text-rose-200/70">Puan türünü, üniversite tipini veya bölüm filtresini değiştirmeyi dene.</div></div>}
                {CATEGORIES.map(cat => {
                  const items = cat.key === 'safe' ? result.safe : cat.key === 'target' ? result.target : result.reach
                  return <CategoryGroup key={cat.key} cat={cat} items={items} renderItem={item => (
                    <div key={String(item.department_code)} className="card glass-hover p-4 group animate-fade-in-up">
                      <div className="flex items-start justify-between gap-3"><div className="flex-1 min-w-0"><h4 className="font-semibold text-white text-base truncate">{item.department_name}</h4><div className="flex items-center gap-2 mt-1 text-xs text-slate-400 flex-wrap"><span className="flex items-center gap-1"><Building2 size={11} /> {item.university_name}</span>{item.city && <span className="flex items-center gap-1"><MapPin size={11} /> {item.city}</span>}</div></div><div className="text-right shrink-0"><div className="text-xs text-slate-500">Uygunluk</div><div className="font-display font-bold text-lg text-accent-300">%{item.fit_score?.toFixed(0) ?? 0}</div></div></div>
                      {(item.scholarship || (item.education_language && item.education_language !== 'Türkçe') || item.duration_years || item.osym_conditions?.length > 0) && <div className="flex flex-wrap items-center gap-1.5 mt-2">{item.scholarship && /burslu|ücretsiz/i.test(item.scholarship) && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">🎓 {item.scholarship}</span>}{item.scholarship && /ücretli|paralı/i.test(item.scholarship) && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/5 text-slate-300 border border-white/10">{item.scholarship}</span>}{item.education_language && item.education_language !== 'Türkçe' && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-sky-500/15 text-sky-300 border border-sky-500/25">{item.education_language}</span>}{item.duration_years && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/5 text-slate-400 border border-white/10">{item.duration_years} yıl</span>}{item.osym_conditions?.slice(0, 2).map((c, i) => <span key={i} title={c} className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/25 inline-flex items-center gap-0.5"><AlertTriangle size={9} /> {c.length > 28 ? c.slice(0, 28) + '…' : c}</span>)}</div>}
                      {(item.last_year_base_rank || item.last_year_base_score || item.placement_probability != null) && <div className="mt-3 pt-3 border-t border-white/5 flex items-center gap-4 text-xs flex-wrap">{item.last_year_base_rank && <div><div className="text-slate-500">Sıra</div><div className="font-mono text-cyber-cyan">{item.last_year_base_rank.toLocaleString('tr')}</div></div>}{item.last_year_base_score && <div><div className="text-slate-500">Taban</div><div className="font-mono text-accent-300">{item.last_year_base_score.toFixed(2)}</div></div>}{item.trend?.filter(t => t.base_rank != null).length >= 2 && <div><div className="text-slate-500">Trend</div><MiniTrend trend={item.trend} compact /></div>}{item.placement_probability != null && (() => { const pct = Math.round(item.placement_probability * 100); const color = pct >= 75 ? 'text-emerald-300 bg-emerald-500/10 border-emerald-500/30' : pct >= 40 ? 'text-amber-300 bg-amber-500/10 border-amber-500/30' : 'text-rose-300 bg-rose-500/10 border-rose-500/30'; return <div className="ml-auto"><div className="text-slate-500 text-[10px] text-right">Yerleşme olasılığı</div><div className={`inline-flex items-center px-2 py-0.5 rounded-lg border font-mono font-semibold ${color}`} title="Geçen yılki sıraya göre tahmini sigmoid olasılık">%{pct}</div></div> })()}</div>}
                      {item.reason && <p className="mt-2 text-xs text-slate-400 italic">{item.reason}</p>}
                      <div className="mt-3 pt-3 border-t border-white/5">
                        <TercihToggleButton inList={yksTercihIds.has(String(item.department_code))} busy={yksBusyCode === String(item.department_code)} onToggle={() => yksTercihIds.has(String(item.department_code)) ? handleRemoveFromTercih(item) : handleAddToTercih(item)} />
                      </div>
                    </div>
                  )} />
                })}
                {result.notes && <div className="text-[11px] text-slate-500">{result.notes}</div>}
              </div>
            )}
          </>
        )}
      </div>
    </>
  )
}