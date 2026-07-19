import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Trophy, Loader2, Sparkles, LogOut, Check, Pencil } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { useAuth } from '../contexts/AuthContext'
import {
  getIstatistik, siralamaBenim, siralamaKaydet, siralamaCik, siralamaListe, siralamaSira,
} from '../firebase'
import { hesaplaXP, seviyeBilgi } from '../lib/oyun'

const nf = (n) => (n || 0).toLocaleString('tr-TR')
const madalya = (sira) => (sira === 1 ? '🥇' : sira === 2 ? '🥈' : sira === 3 ? '🥉' : null)

export default function Siralama() {
  const nav = useNavigate()
  const { user, isAuthed, loading } = useAuth()

  const [yukleniyor, setYukleniyor] = useState(true)
  const [liste, setListe] = useState([])
  const [benimAd, setBenimAd] = useState(null) // katıldıysa takma ad, yoksa null
  const [siram, setSiram] = useState(null)
  const [xp, setXp] = useState(0)
  const [seviye, setSeviye] = useState(1)
  const [adInput, setAdInput] = useState('')
  const [hata, setHata] = useState('')
  const [islem, setIslem] = useState(false)
  const [duzenle, setDuzenle] = useState(false)

  useEffect(() => {
    if (!loading && !isAuthed) nav('/giris')
  }, [loading, isAuthed, nav])

  const yenile = useCallback(async (myXp) => {
    const [top, sira] = await Promise.all([siralamaListe(100), siralamaSira(myXp)])
    setListe(top)
    setSiram(sira)
  }, [])

  useEffect(() => {
    if (!user) return
    let iptal = false
    ;(async () => {
      setYukleniyor(true)
      const stats = await getIstatistik(user.uid)
      const myXp = hesaplaXP(stats)
      const sv = seviyeBilgi(myXp)
      const benim = await siralamaBenim(user.uid)
      if (iptal) return
      setXp(myXp)
      setSeviye(sv.seviye)
      if (benim?.ad) {
        setBenimAd(benim.ad)
        setAdInput(benim.ad)
        // Katıldıysa skorunu tazele (yalnız değiştiyse yaz — gereksiz yazımdan kaçın)
        if (benim.xp !== myXp || benim.seviye !== sv.seviye) {
          siralamaKaydet(user.uid, benim.ad, sv.seviye, myXp).catch(() => {})
        }
      } else {
        setAdInput((user.displayName || '').slice(0, 24))
      }
      await yenile(myXp)
      if (!iptal) setYukleniyor(false)
    })()
    return () => { iptal = true }
  }, [user, yenile])

  async function katil() {
    setHata('')
    setIslem(true)
    try {
      const ad = await siralamaKaydet(user.uid, adInput, seviye, xp)
      setBenimAd(ad)
      setDuzenle(false)
      await yenile(xp)
    } catch (e) {
      setHata(e.message || 'Kaydedilemedi')
    } finally {
      setIslem(false)
    }
  }

  async function ayril() {
    if (!confirm('Sıralamadan ayrılmak istediğine emin misin? Takma adın ve skorun listeden kaldırılır.')) return
    setIslem(true)
    try {
      await siralamaCik(user.uid)
      setBenimAd(null)
      setDuzenle(false)
      await yenile(xp)
    } catch (e) {
      setHata(e.message || 'İşlem başarısız')
    } finally {
      setIslem(false)
    }
  }

  if (!isAuthed || !user) return null

  return (
    <>
      <BackgroundScene />
      <Seo
        title="Sıralama | UniSense"
        description="UniSense çalışma sıralaması — en çok XP toplayan öğrenciler. Takma adınla katıl, sıranı gör."
        path="/siralama"
      />
      <div className="max-w-2xl mx-auto space-y-5">
        <div className="text-center">
          <h1 className="text-3xl md:text-4xl font-display font-bold text-white mb-1 flex items-center justify-center gap-2">
            <Trophy className="text-amber-300" /> Sıralama
          </h1>
          <p className="text-slate-400 text-sm">En çok XP toplayan 100 öğrenci. Takma adınla katıl, sıranı gör.</p>
        </div>

        {/* Katılım / kendi sıran */}
        <div className="card">
          {benimAd && !duzenle ? (
            <div className="flex items-center gap-3 flex-wrap">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center text-white font-display font-bold shrink-0">
                {siram ? `#${siram}` : '—'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-white truncate">{benimAd}</div>
                <div className="text-[12px] text-slate-400">
                  Seviye {seviye} · {nf(xp)} XP{siram ? ` · Senin sıran #${siram}` : ''}
                </div>
              </div>
              <button onClick={() => setDuzenle(true)}
                className="text-xs px-3 py-1.5 rounded-lg bg-white/5 text-slate-300 hover:bg-white/10 flex items-center gap-1">
                <Pencil size={12} /> Adı değiştir
              </button>
              <button onClick={ayril} disabled={islem}
                className="text-xs px-3 py-1.5 rounded-lg bg-rose-500/10 text-rose-300 hover:bg-rose-500/20 flex items-center gap-1 disabled:opacity-50">
                <LogOut size={12} /> Ayrıl
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="text-sm text-slate-200 flex items-center gap-2">
                <Sparkles size={15} className="text-amber-300" /> {benimAd ? 'Takma adını değiştir' : 'Sıralamaya katıl'}
              </div>
              <p className="text-[12px] text-slate-400">
                {siram
                  ? `Şu an ${nf(xp)} XP ile ${benimAd ? 'sıran' : 'katılırsan'} #${siram} ${benimAd ? 'olur' : 'olurdun'}.`
                  : 'Takma adın herkese görünür; gerçek adın ve e-postan gizli kalır.'}
              </p>
              <div className="flex gap-2 flex-wrap">
                <input
                  value={adInput}
                  onChange={(e) => setAdInput(e.target.value)}
                  maxLength={24}
                  placeholder="Takma ad (2–24 karakter)"
                  className="flex-1 min-w-[160px] px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-accent-500/40"
                />
                <button onClick={katil} disabled={islem || adInput.trim().length < 2}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 text-white text-sm font-medium disabled:opacity-50 flex items-center gap-1">
                  {islem ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} {benimAd ? 'Kaydet' : 'Katıl'}
                </button>
                {benimAd && (
                  <button onClick={() => { setDuzenle(false); setAdInput(benimAd) }}
                    className="px-3 py-2 rounded-xl bg-white/5 text-slate-300 text-sm">Vazgeç</button>
                )}
              </div>
              <p className="text-[11px] text-slate-500">Takma adın uygunsuz olmamalı; e-posta veya gerçek adını paylaşma.</p>
              {hata && <p className="text-[12px] text-rose-400">{hata}</p>}
            </div>
          )}
        </div>

        {/* Tablo */}
        {yukleniyor ? (
          <div className="card flex items-center justify-center py-10 text-slate-400">
            <Loader2 className="animate-spin mr-2" size={18} /> Yükleniyor…
          </div>
        ) : liste.length === 0 ? (
          <div className="card text-center py-10 text-slate-400 text-sm">Henüz kimse katılmadı — ilk sen ol! 🏆</div>
        ) : (
          <div className="card p-0 overflow-hidden divide-y divide-white/5">
            {liste.map((k, i) => {
              const sira = i + 1
              const benimMi = k.uid === user.uid
              const m = madalya(sira)
              return (
                <div key={k.uid} className={`flex items-center gap-3 px-4 py-2.5 ${benimMi ? 'bg-accent-500/10' : ''}`}>
                  <div className={`w-8 text-center font-mono ${sira <= 3 ? 'text-lg' : 'text-sm text-slate-400'}`}>{m || sira}</div>
                  <div className="flex-1 min-w-0 text-sm text-white truncate">
                    {k.ad}{benimMi && <span className="text-[11px] text-accent-300 ml-1">(sen)</span>}
                  </div>
                  <div className="text-[11px] px-2 py-0.5 rounded-full bg-white/5 text-slate-300 shrink-0">Sv {k.seviye}</div>
                  <div className="text-[12px] text-amber-300 font-mono shrink-0 w-16 text-right">{nf(k.xp)}</div>
                </div>
              )
            })}
          </div>
        )}

        {/* Kendi satırın ilk 100 dışındaysa altta göster */}
        {!yukleniyor && benimAd && siram && siram > liste.length && (
          <div className="card flex items-center gap-3 border-accent-500/30">
            <div className="w-8 text-center font-mono text-sm text-accent-300">#{siram}</div>
            <div className="flex-1 min-w-0 text-sm text-white truncate">
              {benimAd} <span className="text-[11px] text-accent-300 ml-1">(sen)</span>
            </div>
            <div className="text-[11px] px-2 py-0.5 rounded-full bg-white/5 text-slate-300 shrink-0">Sv {seviye}</div>
            <div className="text-[12px] text-amber-300 font-mono shrink-0 w-16 text-right">{nf(xp)}</div>
          </div>
        )}
      </div>
    </>
  )
}
