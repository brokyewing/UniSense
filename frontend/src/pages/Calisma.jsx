import { Link } from 'react-router-dom'
import { ListTodo, LineChart, BookMarked, NotebookPen, LayoutDashboard } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import PushOptIn from '../components/PushOptIn'
import Konular from './Konular'
import Deneme from './Deneme'
import Ozetler from './Ozetler'
import Notlar from './Notlar'
import Pano from './Pano'

// Çalışma merkezi: Konular + Deneme + Özetler tek "Çalışma" sekmesi altında (nav ferah).
// Her biri kendi rotasını korur (/konular, /deneme, /ozetler) → SEO/prerender değişmez;
// sekmeler o rotalara Link. Yeni retention özellikleri de buraya segment olarak eklenir.
// h1/alt: prerender edilen sayfa başlığıyla UYUMLU olsun (SEO — anahtar kelime eşleşir).
const TABS = [
  { key: 'konular', label: 'Konular', to: '/konular', Icon: ListTodo, renk: 'text-emerald-300', h1: 'Konu Takibi', alt: 'Sınavının tüm konularını çalıştıkça işaretle — ilerlemeni gör.' },
  { key: 'deneme', label: 'Çalışmalarım', to: '/deneme', Icon: LineChart, renk: 'text-accent-300', h1: 'Çalışmalarım', alt: 'Denemelerini ve konu konu çözdüğün soruları kaydet — AI Koç ikisini de okur.' },
  { key: 'ozetler', label: 'Özetler', to: '/ozetler', Icon: BookMarked, renk: 'text-amber-300', h1: 'Formül Özetleri', alt: 'Sık kullanılan formülleri hızlıca gözden geçir.' },
  { key: 'notlar', label: 'Notlar', to: '/notlar', Icon: NotebookPen, renk: 'text-rose-300', h1: 'Notlarım', alt: 'Yapacaklarını ve aklındakileri not et — işaretleyerek takip et.' },
  { key: 'pano', label: 'Pano', to: '/pano', Icon: LayoutDashboard, renk: 'text-sky-300', h1: 'Çalışma Panom', alt: 'Pomodoro ile çalış, ilerlemeni ve rozetlerini gör.' },
]

export default function Calisma({ tab = 'konular' }) {
  const active = TABS.some((t) => t.key === tab) ? tab : 'konular'
  const meta = TABS.find((t) => t.key === active)
  return (
    <>
      <BackgroundScene />
      <div className="max-w-3xl mx-auto space-y-4 mb-5">
        <div className="text-center">
          <h1 className="text-3xl md:text-4xl font-display font-bold text-white mb-1 flex items-center justify-center gap-2">
            <meta.Icon className={meta.renk} /> {meta.h1}
          </h1>
          <p className="text-slate-400 text-sm">{meta.alt}</p>
        </div>
        <div className="flex justify-center">
          <div className="inline-flex gap-1 p-1 rounded-xl bg-white/5 border border-white/10 max-w-full overflow-x-auto no-scrollbar">
            {TABS.map((t) => {
              const on = active === t.key
              return (
                <Link key={t.key} to={t.to}
                  className={`shrink-0 px-3.5 py-2 rounded-lg text-sm font-semibold inline-flex items-center gap-1.5 transition ${
                    on ? 'bg-gradient-to-r from-brand-500 to-accent-500 text-white' : 'text-slate-300 hover:text-white'
                  }`}>
                  <t.Icon size={15} /> {t.label}
                </Link>
              )
            })}
          </div>
        </div>
        <PushOptIn />
      </div>
      {active === 'konular' && <Konular embedded />}
      {active === 'deneme' && <Deneme embedded />}
      {active === 'ozetler' && <Ozetler embedded />}
      {active === 'notlar' && <Notlar embedded />}
      {active === 'pano' && <Pano embedded />}
    </>
  )
}
