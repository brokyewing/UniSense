import { useState, useEffect, useMemo } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Loader2, ArrowLeft, Building2, MapPin, GraduationCap } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import Seo from '../components/Seo'
import { apiFetch } from '../lib/api'

/** Basit markdown → JSX: **kalın**, * madde, satır başlıkları. AI içeriği hafif biçimli. */
function renderContent(content) {
  const lines = (content || '').split('\n')
  const out = []
  let list = []
  const flush = (key) => {
    if (list.length) {
      out.push(<ul key={`ul${key}`} className="list-disc pl-5 space-y-0.5 my-1.5 text-slate-300">{list}</ul>)
      list = []
    }
  }
  lines.forEach((raw, i) => {
    const line = raw.trim()
    if (!line) { flush(i); return }
    if (line.startsWith('*') || line.startsWith('-')) {
      list.push(<li key={i}>{bold(line.replace(/^[*-]\s*/, ''))}</li>)
      return
    }
    flush(i)
    // Emoji + **Başlık:** satırı → alt başlık
    if (/^\S{0,3}\s*\*\*.+\*\*/.test(line)) {
      out.push(<h2 key={i} className="text-sm font-semibold text-white mt-4 mb-1">{bold(line)}</h2>)
    } else {
      out.push(<p key={i} className="text-sm text-slate-300 leading-relaxed my-1">{bold(line)}</p>)
    }
  })
  flush('end')
  return out
}
function bold(text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return parts.map((p, i) =>
    p.startsWith('**') && p.endsWith('**')
      ? <strong key={i} className="text-white">{p.slice(2, -2)}</strong>
      : p)
}

export default function BolumDetay() {
  const { slug } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [il, setIl] = useState('')
  const [tur, setTur] = useState('all')

  useEffect(() => {
    setLoading(true); setError('')
    apiFetch(`/api/v1/bolum/${slug}`)
      .then(setData)
      .catch((e) => setError(e.status === 404 ? 'Bu bölüm için henüz rehber yok.' : e.message))
      .finally(() => setLoading(false))
  }, [slug])

  const programs = useMemo(() => {
    if (!data) return []
    const ilf = il.trim().toLocaleLowerCase('tr')
    return data.programs.filter((p) => {
      if (ilf && !p.city.toLocaleLowerCase('tr').includes(ilf)) return false
      if (tur !== 'all' && !(p.university_type || '').toLowerCase().startsWith(tur.toLowerCase())) return false
      return true
    })
  }, [data, il, tur])

  if (loading) return <div className="text-center py-16"><Loader2 className="animate-spin mx-auto text-accent-400" /></div>
  if (error) return (
    <div className="max-w-2xl mx-auto card text-center py-10">
      <p className="text-slate-300 mb-4">{error}</p>
      <Link to="/bolum" className="btn-ghost inline-flex items-center gap-2"><ArrowLeft size={14} /> Bölüm Rehberine Dön</Link>
    </div>
  )

  const tabanlilar = programs.filter((p) => p.base_score != null)

  return (
    <>
      <BackgroundScene />
      <Seo
        title={`${data.name} — Ne İş Yapar, Taban Puanları | UniSense`}
        description={`${data.name} bölümü ne iş yapar, hangi dersleri okur, mezunları nerede çalışır? ${data.name} veren ${data.program_count} programın güncel taban puanı ve başarı sıralaması.`}
        path={`/bolum/${slug}`}
      />
      <div className="max-w-4xl mx-auto space-y-5">
        <Link to="/bolum" className="text-xs text-slate-400 hover:text-accent-300 inline-flex items-center gap-1">
          <ArrowLeft size={12} /> Bölüm Rehberi
        </Link>

        <div>
          <h1 className="text-3xl md:text-4xl font-display font-bold text-white mb-1">{data.name}</h1>
          <p className="text-sm text-slate-500">{data.program_count} üniversite programı</p>
        </div>

        {/* Tanıtım içeriği */}
        <div className="card">
          {renderContent(data.content)}
          <p className="text-[10px] text-slate-600 mt-4 pt-3 border-t border-white/5">
            Tanıtım yapay zekâ ile özetlenmiştir; resmi bilgi için ilgili üniversiteye danışın.
          </p>
        </div>

        {/* Taban puan tablosu */}
        <div className="card space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h2 className="font-semibold text-white flex items-center gap-2">
              <GraduationCap size={16} className="text-accent-300" />
              {data.name} Taban Puanları <span className="text-xs text-slate-500 font-normal">(2025 yerleştirme)</span>
            </h2>
            <div className="flex gap-2">
              <input value={il} onChange={(e) => setIl(e.target.value)} placeholder="Şehir"
                className="input-glass !py-1.5 !w-28 text-xs" />
              <select value={tur} onChange={(e) => setTur(e.target.value)} className="input-glass !py-1.5 !w-24 text-xs">
                <option value="all">Tümü</option>
                <option value="Devlet">Devlet</option>
                <option value="Vakıf">Vakıf</option>
              </select>
            </div>
          </div>

          <div className="text-xs text-slate-500">
            {tabanlilar.length} programın tabanı var{programs.length - tabanlilar.length > 0 ? ` · ${programs.length - tabanlilar.length} program geçen yıl boş/veri yok` : ''}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[520px]">
              <thead>
                <tr className="text-[10px] text-slate-500 uppercase text-left border-b border-white/5">
                  <th className="py-2 pr-2">Üniversite</th>
                  <th className="py-2 px-2">Şehir</th>
                  <th className="py-2 px-2 text-right">Taban</th>
                  <th className="py-2 px-2 text-right">Sıra</th>
                  <th className="py-2 pl-2 text-right">Kont.</th>
                </tr>
              </thead>
              <tbody>
                {programs.map((p) => (
                  <tr key={p.department_code} className="border-b border-white/5 last:border-0 hover:bg-white/5">
                    <td className="py-2 pr-2">
                      <div className="text-slate-200 flex items-center gap-1.5">
                        <Building2 size={11} className="text-slate-500 shrink-0" />
                        <span className="truncate">{p.university_name}</span>
                      </div>
                      <div className="flex gap-1.5 mt-0.5">
                        {p.scholarship && /burslu|ücretsiz/i.test(p.scholarship) && (
                          <span className="text-[9px] text-emerald-300">🎓 {p.scholarship}</span>
                        )}
                        {p.education_language && p.education_language !== 'Türkçe' && (
                          <span className="text-[9px] text-sky-300">{p.education_language}</span>
                        )}
                      </div>
                    </td>
                    <td className="py-2 px-2 text-slate-400 text-xs">{p.city}</td>
                    <td className="py-2 px-2 text-right font-mono text-accent-300">{p.base_score != null ? p.base_score.toFixed(2) : '—'}</td>
                    <td className="py-2 px-2 text-right font-mono text-cyber-cyan text-xs">{p.base_rank != null ? p.base_rank.toLocaleString('tr') : '—'}</td>
                    <td className="py-2 pl-2 text-right text-slate-500 text-xs">{p.quota ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {programs.length === 0 && <div className="text-center text-slate-500 text-sm py-4">Bu filtreyle program yok.</div>}
        </div>

        <div className="flex items-center gap-2">
          <Link to="/pusula" className="btn-ghost text-sm inline-flex items-center gap-1.5">
            <MapPin size={13} /> Sana uygun mu? İlgi Pusulası
          </Link>
        </div>
      </div>
    </>
  )
}
