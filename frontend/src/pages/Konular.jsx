import { useState, useEffect, useMemo } from 'react'
import { CheckCircle2, Circle, ListChecks, Loader2, RotateCcw } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { apiFetch } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import { getUserProfile, watchKonuIlerleme, setKonuIlerleme, recordActivity } from '../firebase'

const SINAVLAR = [
  { key: 'YKS', label: 'YKS' },
  { key: 'KPSS', label: 'KPSS' },
  { key: 'DGS', label: 'DGS' },
  { key: 'LGS', label: 'LGS' },
]

const LS_KEY = (sinav) => `unisense_konu_v1_${sinav}`

function loadChecked(sinav) {
  try { return JSON.parse(localStorage.getItem(LS_KEY(sinav)) || '{}') } catch { return {} }
}
function saveChecked(sinav, obj) {
  try { localStorage.setItem(LS_KEY(sinav), JSON.stringify(obj)) } catch { /* noop */ }
}

// Veri şeklini düzleştir: YKS gruplu (TYT/AYT), diğerleri düz ders listesi
function bloklar(data) {
  if (!data) return []
  if (data.gruplar) {
    const out = []
    for (const [grup, dersler] of Object.entries(data.gruplar)) {
      for (const [ders, konular] of Object.entries(dersler)) {
        out.push({ grup, ders, konular })
      }
    }
    return out
  }
  return Object.entries(data.dersler || {}).map(([ders, konular]) => ({ grup: null, ders, konular }))
}

function ProgressBar({ done, total }) {
  const pct = total ? Math.round((done / total) * 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-white/10 overflow-hidden">
        <div className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-teal-500 transition-all duration-500"
          style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[11px] text-slate-400 font-mono shrink-0">{done}/{total}</span>
    </div>
  )
}

export default function Konular({ embedded = false }) {
  const { user } = useAuth()
  const [sinav, setSinav] = useState('YKS')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [checked, setChecked] = useState({})
  const [userPicked, setUserPicked] = useState(false)

  // Profildeki sınav yoluna göre varsayılan sınav (kullanıcı seçmediyse)
  useEffect(() => {
    if (!user || userPicked) return
    getUserProfile(user.uid).then((p) => {
      const track = p?.profile?.examTrack
      const map = { YKS: 'YKS', KPSS: 'KPSS', DGS: 'DGS', LGS: 'LGS' }
      if (map[track]) setSinav(map[track])
    }).catch(() => {})
  }, [user, userPicked])

  // Seçili sınavın konularını yükle
  useEffect(() => {
    setLoading(true)
    setError('')
    apiFetch(`/api/v1/konular?sinav=${sinav}`)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [sinav])

  // Tikleri yükle: localStorage anında + girişliyse Firestore bulut senkronu.
  // Bulut erişilemezse (kural/App Check/offline) localStorage'a düşer — asla kırılmaz.
  useEffect(() => {
    const local = loadChecked(sinav)
    setChecked(local)
    if (!user) return
    return watchKonuIlerleme(user.uid, sinav, (cloud) => {
      if (cloud == null) return // erişilemedi → localStorage kalsın
      if (Object.keys(cloud).length === 0 && Object.keys(local).length > 0) {
        // Bulut boş ama cihazda veri var → bir kez yukarı taşı (migration)
        setKonuIlerleme(user.uid, sinav, local).catch(() => {})
        setChecked(local)
      } else {
        setChecked(cloud)
        saveChecked(sinav, cloud) // cihaza da yansıt
      }
    })
  }, [user, sinav])

  const bl = useMemo(() => bloklar(data), [data])
  const toplam = useMemo(() => bl.reduce((s, b) => s + b.konular.length, 0), [bl])
  const yapilan = useMemo(
    () => bl.reduce((s, b) => s + b.konular.filter((k) => checked[`${b.grup || ''}|${b.ders}|${k}`]).length, 0),
    [bl, checked],
  )

  function toggle(b, konu) {
    const key = `${b.grup || ''}|${b.ders}|${konu}`
    setChecked((prev) => {
      const next = { ...prev }
      if (next[key]) delete next[key]
      else next[key] = true
      saveChecked(sinav, next)
      if (user) setKonuIlerleme(user.uid, sinav, next).catch(() => {}) // bulut senkronu
      recordActivity(user?.uid).catch(() => {}) // günlük seri (streak)
      return next
    })
  }

  function sifirla() {
    if (!confirm(`${sinav} işaretlerini sıfırlamak istediğine emin misin?`)) return
    setChecked({})
    saveChecked(sinav, {})
    if (user) setKonuIlerleme(user.uid, sinav, {}).catch(() => {})
  }

  return (
    <>
      {!embedded && <BackgroundScene />}
      {!embedded && (
        <Seo
          title={`Konu Takibi — YKS, KPSS, DGS, LGS Konuları | UniSense`}
          description="Sınavında çıkan tüm konuları ders ders takip et, çalıştıkça işaretle. YKS, KPSS, DGS ve LGS için ücretsiz konu kontrol listesi."
          path="/konular"
        />
      )}
      <div className="max-w-3xl mx-auto space-y-5">
        {!embedded && (
          <div className="text-center">
            <h1 className="text-3xl md:text-4xl font-display font-bold text-white mb-1 flex items-center justify-center gap-2">
              <ListChecks className="text-emerald-300" /> Konu Takibi
            </h1>
            <p className="text-slate-400 text-sm">Sınavının tüm konularını çalıştıkça işaretle — ilerlemeni gör.</p>
          </div>
        )}

        {/* Sınav seçici */}
        <div className="flex justify-center">
          <div className="inline-flex flex-wrap justify-center rounded-xl bg-white/5 border border-white/10 p-1 gap-1">
            {SINAVLAR.map((s) => (
              <button key={s.key}
                onClick={() => { setUserPicked(true); setSinav(s.key) }}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
                  sinav === s.key ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white' : 'text-slate-300 hover:bg-white/10'
                }`}>
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="text-center py-10"><Loader2 className="animate-spin mx-auto text-emerald-400" /></div>
        ) : error ? (
          <div className="card text-center text-rose-300">⚠️ {error}</div>
        ) : (
          <>
            {/* Genel ilerleme */}
            <div className="card !py-3">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-semibold text-white">{data?.ad || sinav}</div>
                <button onClick={sifirla} title="Bu sınavın işaretlerini sıfırla"
                  className="text-[11px] text-slate-400 hover:text-rose-300 inline-flex items-center gap-1">
                  <RotateCcw size={11} /> sıfırla
                </button>
              </div>
              <ProgressBar done={yapilan} total={toplam} />
            </div>

            {/* Ders kartları */}
            <div className="space-y-3">
              {bl.map((b, i) => {
                const dersDone = b.konular.filter((k) => checked[`${b.grup || ''}|${b.ders}|${k}`]).length
                return (
                  <div key={i} className="card">
                    <div className="flex items-center justify-between gap-3 mb-2.5">
                      <div className="font-semibold text-sm text-white flex items-center gap-2">
                        {b.grup && <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-slate-300">{b.grup}</span>}
                        {b.ders}
                      </div>
                      <div className="w-28"><ProgressBar done={dersDone} total={b.konular.length} /></div>
                    </div>
                    <div className="grid sm:grid-cols-2 gap-1.5">
                      {b.konular.map((konu) => {
                        const on = !!checked[`${b.grup || ''}|${b.ders}|${konu}`]
                        return (
                          <button key={konu} onClick={() => toggle(b, konu)}
                            className={`flex items-center gap-2 text-left text-[13px] px-2.5 py-2 rounded-lg border transition ${
                              on ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200'
                                 : 'bg-white/[0.02] border-white/8 text-slate-300 hover:bg-white/5'
                            }`}>
                            {on ? <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
                                : <Circle size={16} className="text-slate-500 shrink-0" />}
                            <span className={on ? 'line-through decoration-emerald-400/50' : ''}>{konu}</span>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>

            <div className="text-[11px] text-slate-600 text-center px-2">
              {data?.not || 'Konular MEB/ÖSYM müfredatına göredir.'} · İşaretlerin bu cihazda saklanır.
            </div>
          </>
        )}
      </div>
    </>
  )
}
