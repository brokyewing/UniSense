import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Loader2, Stethoscope, Info, ExternalLink, Building2, Search, ShieldCheck, Target, Rocket, Users } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { apiFetch } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import {
  watchUzmanlikTercih, addToUzmanlikTercih, removeFromUzmanlikTercih, MAX_TUS_TERCIH,
  getUserProfile,
} from '../firebase'

const SINAVLAR = [
  { key: 'TUS', label: 'TUS', desc: 'Tıpta Uzmanlık' },
  { key: 'DUS', label: 'DUS', desc: 'Diş Hekimliğinde Uzmanlık' },
]

const KOVALAR = [
  { key: 'guvenli', label: 'Güvenli', icon: ShieldCheck, renk: 'from-emerald-500 to-teal-600', desc: 'Tabanın belirgin üstünde' },
  { key: 'tutar',   label: 'Tutar',   icon: Target,      renk: 'from-amber-500 to-orange-600', desc: 'Taban civarı — sınırda' },
  { key: 'riskli',  label: 'Riskli',  icon: Rocket,      renk: 'from-rose-500 to-fuchsia-600', desc: 'Tabanın altında — taban düşerse şans' },
]

function ProgramKart({ p, inList, onToggle }) {
  return (
    <div className="rounded-xl bg-white/[0.03] border border-white/5 p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="font-medium text-sm text-white leading-tight">{p.dal}</div>
          <div className="flex items-center gap-1.5 mt-0.5 text-[11px] text-slate-400">
            <Building2 size={10} className="shrink-0" /> <span className="truncate">{p.kurum || '—'}</span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          {p.kontenjan_turu && p.kontenjan_turu !== 'Genel' && (
            <span className="text-[9px] px-1.5 py-0.5 rounded-full border bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-500/30">
              {p.kontenjan_turu}
            </span>
          )}
          <button
            onClick={() => onToggle(p)}
            title={inList ? 'Tercihten çıkar' : 'Tercih listeme ekle'}
            className={`rounded-lg px-2 py-0.5 text-[10px] border transition ${
              inList
                ? 'border-emerald-500/40 text-emerald-300 bg-emerald-500/10'
                : 'border-white/10 text-slate-300 hover:bg-white/10'
            }`}
          >
            {inList ? '✓ Listede' : '+ Tercih'}
          </button>
        </div>
      </div>
      <div className="flex items-end justify-between mt-2">
        <div>
          <div className="text-[10px] text-slate-500">En küçük puan</div>
          <div className="text-lg font-display font-bold text-accent-300 leading-none font-mono">
            {p.min_puan?.toFixed(2)}
          </div>
        </div>
        <div className="text-right text-[10px] text-slate-400 space-y-0.5">
          {p.max_puan != null && <div>En büyük: <span className="text-slate-200 font-mono">{p.max_puan.toFixed(2)}</span></div>}
          {p.kontenjan != null && (
            <div className="inline-flex items-center gap-1"><Users size={9} /> {p.yerlesen}/{p.kontenjan}</div>
          )}
        </div>
      </div>
    </div>
  )
}

// Robot çekirdeği — hem /tus sayfasında hem Öneriler sekmesinde kullanılır
export function TusRobot() {
  const [sinav, setSinav] = useState('TUS')
  const [puan, setPuan] = useState('')
  const [dal, setDal] = useState('')
  const [kurum, setKurum] = useState('')
  const [kontenjanTuru, setKontenjanTuru] = useState('Genel') // Genel | Yabancı Uyruklu
  const [meta, setMeta] = useState(null)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { user } = useAuth()
  const [tercihIds, setTercihIds] = useState(new Set())
  const [toast, setToast] = useState('')
  // Stale-response koruması: bul() beklerken sınav değişirse eski yanıt basılmasın
  const sinavRef = useRef(sinav)
  sinavRef.current = sinav

  // Profildeki TUS/DUS puanını otomatik doldur (diğer sınavlarla tutarlı) —
  // kullanıcı bir şey yazdıysa üzerine yazma. Sınav değişince o sınavın puanı denenir.
  const [profil, setProfil] = useState(null)
  const [autoNot, setAutoNot] = useState('')
  useEffect(() => {
    if (!user) { setProfil(null); return }
    let cancelled = false
    getUserProfile(user.uid).then((p) => { if (!cancelled) setProfil(p?.profile || null) }).catch(() => {})
    return () => { cancelled = true }
  }, [user])
  useEffect(() => {
    const score = sinav === 'DUS' ? profil?.dus?.score : profil?.tus?.score
    if (score == null) return
    setPuan((prev) => {
      if (prev) return prev
      setAutoNot(`${sinav} puanın profilinden geldi`)
      return String(score)
    })
  }, [profil, sinav])

  // Aktif sınavın (TUS/DUS) tercih listesini canlı izle → kart butonları senkron
  useEffect(() => {
    if (!user) { setTercihIds(new Set()); return }
    return watchUzmanlikTercih(user.uid, sinav, (items) => setTercihIds(new Set(items.map((i) => i.id))))
  }, [user, sinav])

  function flash(msg) { setToast(msg); setTimeout(() => setToast(''), 2500) }

  async function toggleTercih(p) {
    if (!user) { flash('Tercihe eklemek için giriş yap'); return }
    const code = String(p.kod)
    try {
      if (tercihIds.has(code)) {
        await removeFromUzmanlikTercih(user.uid, sinav, code)
      } else {
        if (tercihIds.size >= MAX_TUS_TERCIH) { flash(`Liste dolu (en fazla ${MAX_TUS_TERCIH})`); return }
        // order = Date.now(): size+1 silme sonrası çakışıyor (duplicate order →
        // yeni öğe listenin ortasına düşer); reorder zaten 1..n'e normalleştirir.
        await addToUzmanlikTercih(user.uid, sinav, p, Date.now())
        flash(`✓ ${sinav} tercihine eklendi — Tercihlerim sayfasında`)
      }
    } catch (e) { flash(e.message) }
  }

  // Sınav değişince dal listesini yükle + eski sonuç/filtreyi temizle.
  // ignore guard: hızlı TUS↔DUS toggle'da geç gelen eski yanıt yenisini ezmesin.
  useEffect(() => {
    let ignore = false
    setMeta(null); setDal(''); setData(null)
    apiFetch(`/api/v1/tus/meta?sinav=${sinav}`)
      .then((m) => { if (!ignore) setMeta(m) })
      .catch(() => {})
    return () => { ignore = true }
  }, [sinav])

  async function bul(e) {
    e?.preventDefault()
    const p = parseFloat(puan)
    if (isNaN(p) || p < 0 || p > 100) {
      setError('Geçerli bir puan gir (ör. 55.4).')
      setTimeout(() => setError(''), 2500)
      return
    }
    setLoading(true)
    setError('')
    const istekSinav = sinav
    try {
      const res = await apiFetch('/api/v1/tus/oneri', {
        method: 'POST',
        body: {
          puan: p, sinav, dal: dal || null, kurum: kurum || null,
          kontenjan_turu: kontenjanTuru,
        },
      })
      if (sinavRef.current !== istekSinav) return // sınav değişti — eski yanıtı basma
      setData(res)
    } catch (err) {
      if (sinavRef.current === istekSinav) setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-5">

        {/* TUS / DUS toggle */}
        <div className="flex justify-center">
          <div className="inline-flex rounded-xl bg-white/5 border border-white/10 p-1 gap-1">
            {SINAVLAR.map((sv) => (
              <button key={sv.key} onClick={() => setSinav(sv.key)}
                className={`px-4 py-1.5 rounded-lg text-sm transition ${
                  sinav === sv.key ? 'bg-gradient-to-br from-sky-500 to-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
                }`}>
                <span className="font-display font-bold">{sv.label}</span>
                <span className="hidden sm:inline text-[11px] opacity-80"> · {sv.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Uyarı */}
        <div className="card bg-amber-500/5 border-amber-500/20 text-xs text-slate-300 flex items-start gap-2">
          <Info size={13} className="text-amber-400 mt-0.5 shrink-0" />
          <span>
            <strong className="text-amber-300">Tahminîdir.</strong> Sonuçlar{meta?.donem ? ` ${meta.donem}` : ' geçen dönem'} ÖSYM
            en küçük yerleşme puanlarına dayanır; bu dönem taban puanları başvuru/kontenjana göre değişebilir — garanti değildir.
            Resmî tercih ve güncel kılavuz için{' '}
            <a href="https://www.osym.gov.tr" target="_blank" rel="noopener noreferrer"
              className="text-accent-300 hover:underline inline-flex items-center gap-0.5">
              osym.gov.tr <ExternalLink size={10} />
            </a>.
          </span>
        </div>

        {/* Form */}
        <form onSubmit={bul} className="card space-y-3">
          <div className="grid sm:grid-cols-[1fr,1.4fr] gap-3">
            <div>
              <label className="text-xs text-slate-300 mb-1 block">
                {sinav} puanın <span className="text-slate-500">(K/T, ör. 55.40)</span>
              </label>
              <input type="number" min="0" max="100" step="0.01" value={puan}
                onChange={(e) => { setPuan(e.target.value); setAutoNot('') }} placeholder="ör. 55.40"
                className="input-glass w-full" />
              {autoNot && <div className="text-[10px] text-accent-300 mt-1">✨ {autoNot}</div>}
            </div>
            <div>
              <label className="text-xs text-slate-300 mb-1 block">
                Uzmanlık dalı <span className="text-slate-500">(opsiyonel — {meta ? `${meta.dallar.length} dal` : '…'})</span>
              </label>
              <select value={dal} onChange={(e) => setDal(e.target.value)} className="input-glass w-full" disabled={!meta}>
                <option value="">Tüm dallar</option>
                {meta?.dallar.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
          </div>
          <div className="grid sm:grid-cols-[1.4fr,1fr] gap-3">
            <div>
              <label className="text-xs text-slate-300 mb-1 block">Kurum ara <span className="text-slate-500">(opsiyonel — ör. Hacettepe, İstanbul)</span></label>
              <input type="text" value={kurum} onChange={(e) => setKurum(e.target.value)} placeholder="Üniversite / hastane adı"
                className="input-glass w-full" />
            </div>
            <div>
              <label className="text-xs text-slate-300 mb-1 block">
                Kontenjan türü <span className="text-slate-500">(tabanları ayrıdır)</span>
              </label>
              <div className="grid grid-cols-2 gap-1.5">
                {['Genel', 'Yabancı Uyruklu'].map((t) => (
                  <button key={t} type="button" onClick={() => setKontenjanTuru(t)}
                    className={`px-2 py-2 rounded-lg text-xs border transition ${
                      kontenjanTuru === t
                        ? 'border-sky-500/60 bg-sky-500/15 text-sky-200 font-medium'
                        : 'border-white/10 text-slate-400 hover:bg-white/5'
                    }`}>
                    {t}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <button type="submit" disabled={loading}
            className="btn-primary w-full inline-flex items-center justify-center gap-2 disabled:opacity-50">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
            Programları Bul
          </button>
          {error && <div className="text-xs text-rose-300 text-center">⚠️ {error}</div>}
        </form>

        {toast && (
          <div className="text-xs text-center text-accent-200 bg-accent-500/10 border border-accent-500/30 rounded-lg py-2">
            {toast}
          </div>
        )}

        {/* Sonuçlar */}
        <AnimatePresence>
          {data && (
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
              <div className="text-center text-xs text-slate-400">
                <strong className="text-white">{data.puan}</strong> {data.sinav} puanıyla{' '}
                <span className="text-emerald-300">{data.sayilar.guvenli}</span> güvenli ·{' '}
                <span className="text-amber-300">{data.sayilar.tutar}</span> tutar ·{' '}
                <span className="text-rose-300">{data.sayilar.riskli}</span> riskli program
              </div>

              {data.sayilar.guvenli + data.sayilar.tutar + data.sayilar.riskli === 0 && (
                <div className="card text-center text-sm text-slate-400">
                  Bu filtreyle program bulunamadı. Dal/kurum filtresini genişletmeyi veya puanı kontrol etmeyi dene.
                </div>
              )}

              {KOVALAR.map((kova) => {
                const items = data[kova.key] || []
                if (items.length === 0) return null
                return (
                  <div key={kova.key} className="card">
                    <div className="flex items-center gap-2 mb-3">
                      <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${kova.renk} flex items-center justify-center`}>
                        <kova.icon size={16} className="text-white" />
                      </div>
                      <div>
                        <h2 className="font-display font-semibold text-white leading-none">
                          {kova.label} <span className="text-xs text-slate-400 font-normal">({data.sayilar[kova.key]})</span>
                        </h2>
                        <p className="text-[10px] text-slate-500">{kova.desc}</p>
                      </div>
                    </div>
                    <div className="grid sm:grid-cols-2 gap-2">
                      {items.map((p, i) => (
                        <ProgramKart key={`${p.kod}-${i}`} p={p}
                          inList={tercihIds.has(String(p.kod))} onToggle={toggleTercih} />
                      ))}
                    </div>
                    {data.sayilar[kova.key] > items.length && (
                      <div className="text-[10px] text-slate-500 text-center mt-2">
                        + {data.sayilar[kova.key] - items.length} program daha (dal/kurum filtresiyle daralt)
                      </div>
                    )}
                  </div>
                )
              })}

              <div className="text-[10px] text-slate-600 text-center flex items-center justify-center gap-1.5">
                <Info size={11} /> {data.not}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
    </div>
  )
}

export default function TusDus() {
  return (
    <>
      <BackgroundScene />
      <Seo
        title="TUS / DUS Tercih Robotu 2026 — Puanına Göre Uzmanlık Programı Bul | UniSense"
        description="TUS veya DUS puanını gir, geçen dönem ÖSYM en küçük yerleşme puanlarına göre yerleşebileceğin uzmanlık dallarını ve kurumları güvenli/tutar/riskli olarak gör — ücretsiz, tahminî."
        path="/tus"
      />
      <div className="max-w-4xl mx-auto space-y-5">
        <div className="text-center">
          <div className="w-14 h-14 mx-auto mb-2 rounded-2xl bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg">
            <Stethoscope size={28} className="text-white" />
          </div>
          <h1 className="text-3xl md:text-4xl font-display font-bold text-white">
            TUS / DUS <span className="gradient-text">Tercih Robotu</span>
          </h1>
          <p className="text-sm text-slate-400 max-w-xl mx-auto mt-1">
            Puanını gir → geçen dönem taban puanlarına göre <strong className="text-sky-300">yerleşebileceğin uzmanlık programlarını</strong> gör.
          </p>
        </div>
        <TusRobot />
      </div>
    </>
  )
}
