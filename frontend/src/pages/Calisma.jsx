import { Link } from 'react-router-dom'
import { ListTodo, LineChart, GraduationCap, BookMarked } from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'
import PushOptIn from '../components/PushOptIn'
import Konular from './Konular'
import Deneme from './Deneme'
import Ozetler from './Ozetler'

// Çalışma merkezi: Konular + Deneme + Özetler tek "Çalışma" sekmesi altında (nav ferah).
// Her biri kendi rotasını korur (/konular, /deneme, /ozetler) → SEO/prerender değişmez;
// sekmeler o rotalara Link. Yeni retention özellikleri de buraya segment olarak eklenir.
const TABS = [
  { key: 'konular', label: 'Konular', to: '/konular', Icon: ListTodo },
  { key: 'deneme', label: 'Deneme', to: '/deneme', Icon: LineChart },
  { key: 'ozetler', label: 'Özetler', to: '/ozetler', Icon: BookMarked },
]

export default function Calisma({ tab = 'konular' }) {
  const active = TABS.some((t) => t.key === tab) ? tab : 'konular'
  return (
    <>
      <BackgroundScene />
      <div className="max-w-3xl mx-auto space-y-4 mb-5">
        <div className="text-center">
          <h1 className="text-3xl md:text-4xl font-display font-bold text-white mb-1 flex items-center justify-center gap-2">
            <GraduationCap className="text-accent-300" /> Çalışma
          </h1>
          <p className="text-slate-400 text-sm">Konularını işaretle, denemelerini kaydet — ilerlemeni tek yerde takip et.</p>
        </div>
        <div className="flex justify-center">
          <div className="inline-flex gap-1 p-1 rounded-xl bg-white/5 border border-white/10">
            {TABS.map((t) => {
              const on = active === t.key
              return (
                <Link key={t.key} to={t.to}
                  className={`px-5 py-2 rounded-lg text-sm font-semibold inline-flex items-center gap-2 transition ${
                    on ? 'bg-gradient-to-r from-brand-500 to-accent-500 text-white' : 'text-slate-300 hover:text-white'
                  }`}>
                  <t.Icon size={16} /> {t.label}
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
    </>
  )
}
