import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  Shield, Database, Cloud, Lock, UserCheck, Mail, FileText,
  Cookie, ExternalLink, AlertCircle, Trash2, Download,
} from 'lucide-react'
import BackgroundScene from '../components/three/BackgroundScene'

const LAST_UPDATED = '17 Mayıs 2026'

const COLLECTED_DATA = [
  {
    icon: UserCheck,
    title: 'Hesap Bilgileri',
    source: 'Firebase Authentication',
    items: [
      'E-posta adresi',
      'Ad/soyad (Google ile girişte)',
      'Profil fotoğrafı (Google ile girişte, opsiyonel)',
      'Şifre (yalnızca Email/Password yöntemi — Firebase tarafından hash\'lenir)',
    ],
  },
  {
    icon: FileText,
    title: 'YKS Profili',
    source: 'Firestore — users/{uid}/profile',
    items: [
      'TYT/AYT puanı, başarı sıralaması',
      'Tercih ettiğin şehirler ve bölgeler',
      'İlgi alanları (Pusula sonuçları)',
      'Tercih ettiğin üniversite türü (Devlet/Vakıf/KKTC)',
    ],
  },
  {
    icon: Database,
    title: 'Tercih Listesi',
    source: 'Firestore — users/{uid}/tercih',
    items: [
      '24 sıralık ÖSYM tercih kodları',
      'Sıralama / öncelik bilgisi',
      'Eklenme zamanı',
    ],
  },
  {
    icon: Cloud,
    title: 'Sohbet Geçmişi',
    source: 'Firestore — users/{uid}/sessions (son 5 oturum, FIFO)',
    items: [
      'Sorduğun sorular ve Gemini\'nin cevapları',
      'Kullanılan kaynak chunk referansları',
      'Oturum başlangıç/bitiş zamanı',
    ],
  },
]

const THIRD_PARTIES = [
  {
    name: 'Google Firebase',
    purpose: 'Kimlik doğrulama (Authentication), veri saklama (Firestore), dosya saklama (Storage)',
    region: 'Google Cloud — EU/US sunucuları',
    link: 'https://firebase.google.com/support/privacy',
  },
  {
    name: 'Google Gemini API',
    purpose: 'Sohbet sorgusu metni LLM cevabı üretimi için Gemini\'ye gönderilir',
    region: 'Google AI — global',
    link: 'https://ai.google.dev/gemini-api/terms',
  },
  {
    name: 'Vercel (Frontend hosting)',
    purpose: 'Statik dosya teslimatı + CDN log\'ları (IP, user-agent)',
    region: 'Global edge network',
    link: 'https://vercel.com/legal/privacy-policy',
  },
]

const USER_RIGHTS = [
  { icon: Download, title: 'Veri Aktarma', desc: 'Firestore\'daki tüm verilerini JSON formatında talep edebilirsin.' },
  { icon: FileText, title: 'Düzeltme', desc: 'Yanlış veriyi Profil sayfasından düzeltebilirsin.' },
  { icon: Trash2, title: 'Silme Hakkı', desc: 'Hesabını ve tüm verilerini Profil → Hesap Sil ile kalıcı silebilirsin.' },
  { icon: AlertCircle, title: 'İşlemeye İtiraz', desc: 'Belirli bir veri işleme faaliyetine itiraz edebilirsin (iletişim altta).' },
]


function Section({ icon: Icon, title, children, delay = 0 }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="card"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500/30 to-accent-500/30 border border-accent-500/30 flex items-center justify-center">
          <Icon size={18} className="text-accent-300" />
        </div>
        <h2 className="font-display font-semibold text-xl text-white">{title}</h2>
      </div>
      <div className="text-slate-300 text-sm leading-relaxed space-y-3">{children}</div>
    </motion.section>
  )
}


export default function Privacy() {
  return (
    <>
      <BackgroundScene />

      <div className="space-y-8 max-w-4xl mx-auto">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center pt-4"
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-medium mb-4 backdrop-blur-xl">
            <Shield size={12} />
            KVKK · 6698 sayılı kanun uyumlu
          </div>
          <h1 className="text-4xl md:text-5xl font-display font-bold mb-3 text-white">
            Gizlilik <span className="gradient-text">Politikası</span>
          </h1>
          <p className="text-slate-400 text-sm">
            Son güncelleme: <span className="text-slate-200">{LAST_UPDATED}</span>
          </p>
        </motion.div>

        {/* Özet */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="card border-accent-500/30 bg-gradient-to-br from-accent-500/5 to-brand-500/5"
        >
          <div className="flex items-start gap-3">
            <Lock size={20} className="text-accent-300 shrink-0 mt-0.5" />
            <div className="text-slate-200 text-sm leading-relaxed">
              <strong className="text-white">Kısaca:</strong> UniSense, sana tercih önerisi sunabilmek için
              yalnızca <strong>seçtiğin verileri</strong> Firebase'de saklar. Soruların yanıt üretmek için
              Google Gemini'ye gönderilir. Verilerini istediğin zaman görüntüleyebilir, düzeltebilir veya
              silebilirsin. Reklam, profil pazarlama veya 3. taraf satışı <strong>yapılmaz</strong>.
            </div>
          </div>
        </motion.div>

        {/* 1. Veri Sorumlusu */}
        <Section icon={Shield} title="1. Veri Sorumlusu" delay={0.15}>
          <p>
            UniSense, açık kaynak (MIT lisanslı) bir kişisel proje olarak <strong>BrokyEwing</strong>
            tarafından geliştirilmekte ve yürütülmektedir. KVKK kapsamında veri sorumlusu sıfatıyla
            aşağıdaki politikalar uygulanır.
          </p>
        </Section>

        {/* 2. Toplanan Veriler */}
        <Section icon={Database} title="2. Topladığımız Veriler" delay={0.2}>
          <p>Yalnızca senin doğrudan sağladığın veya hizmeti kullandığında zorunlu olarak işlenen veriler toplanır:</p>
          <div className="grid md:grid-cols-2 gap-3 mt-4">
            {COLLECTED_DATA.map((d, i) => (
              <div key={i} className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
                <div className="flex items-center gap-2 mb-2">
                  <d.icon size={16} className="text-cyber-cyan" />
                  <div className="font-display font-semibold text-white text-sm">{d.title}</div>
                </div>
                <div className="text-[11px] text-slate-500 mb-2 font-mono">{d.source}</div>
                <ul className="space-y-1 text-xs text-slate-300">
                  {d.items.map((item, j) => (
                    <li key={j} className="flex gap-2">
                      <span className="text-accent-400">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Section>

        {/* 3. İşleme Amaçları */}
        <Section icon={FileText} title="3. İşleme Amaçları" delay={0.25}>
          <ul className="space-y-2 ml-2">
            <li className="flex gap-2"><span className="text-accent-400">→</span> Hesap oluşturma ve kimlik doğrulama</li>
            <li className="flex gap-2"><span className="text-accent-400">→</span> Puanına ve sıralamana göre kişiselleştirilmiş bölüm önerisi üretme</li>
            <li className="flex gap-2"><span className="text-accent-400">→</span> Tercih listesini kaydetme ve cihazlar arası senkronlama</li>
            <li className="flex gap-2"><span className="text-accent-400">→</span> Multi-turn sohbet için son 5 oturumu hatırlama</li>
            <li className="flex gap-2"><span className="text-accent-400">→</span> Sistemin teknik güvenliğini sağlama (rate limit, audit log)</li>
          </ul>
          <p className="mt-4 text-xs text-slate-400 italic">
            Verilerin asla reklam, pazarlama veya 3. taraf satışı için kullanılmaz.
          </p>
        </Section>

        {/* 4. Üçüncü Taraf Hizmetler */}
        <Section icon={Cloud} title="4. Üçüncü Taraf Hizmetler" delay={0.3}>
          <p>UniSense aşağıdaki hizmet sağlayıcılarla veri paylaşır:</p>
          <div className="space-y-2 mt-3">
            {THIRD_PARTIES.map((t, i) => (
              <div key={i} className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <div className="font-display font-semibold text-white text-sm">{t.name}</div>
                  <a
                    href={t.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] text-accent-400 hover:text-accent-300 inline-flex items-center gap-1"
                  >
                    Politikaları <ExternalLink size={10} />
                  </a>
                </div>
                <div className="text-xs text-slate-400">{t.purpose}</div>
                <div className="text-[11px] text-slate-500 mt-1">📍 {t.region}</div>
              </div>
            ))}
          </div>
          <div className="mt-4 p-3 rounded-lg bg-amber-500/5 border border-amber-500/20 text-xs text-amber-200">
            <strong>Önemli:</strong> Gemini'ye gönderilen sorgu metnindeki kişisel bilgileri (ör. ad-soyad)
            içermemeye dikkat et. Audit log'larda hassas alanlar SHA-256 ile hash'lenir.
          </div>
        </Section>

        {/* 5. Saklama Süresi */}
        <Section icon={Lock} title="5. Saklama Süresi" delay={0.35}>
          <ul className="space-y-2 ml-2">
            <li className="flex gap-2">
              <span className="text-accent-400">•</span>
              <span><strong className="text-white">Hesap verileri:</strong> Hesabını silene kadar.</span>
            </li>
            <li className="flex gap-2">
              <span className="text-accent-400">•</span>
              <span><strong className="text-white">Sohbet geçmişi:</strong> Son 5 oturum (yeni oturum açıldıkça eskileri FIFO ile düşer).</span>
            </li>
            <li className="flex gap-2">
              <span className="text-accent-400">•</span>
              <span><strong className="text-white">Backend audit log:</strong> 30 gün sonra otomatik silinir.</span>
            </li>
            <li className="flex gap-2">
              <span className="text-accent-400">•</span>
              <span><strong className="text-white">Gemini API logları:</strong> Google'ın politikalarına tabidir (genelde 30 gün).</span>
            </li>
          </ul>
        </Section>

        {/* 6. Çerezler */}
        <Section icon={Cookie} title="6. Çerezler ve Yerel Depolama" delay={0.4}>
          <p>Yalnızca aşağıdaki teknik çerezler/depolama kullanılır:</p>
          <ul className="space-y-2 ml-2 mt-3">
            <li className="flex gap-2">
              <span className="text-accent-400">•</span>
              <span><strong className="text-white">Firebase Auth token</strong> — oturum kapatılmadıkça aktif</span>
            </li>
            <li className="flex gap-2">
              <span className="text-accent-400">•</span>
              <span><strong className="text-white">Tema tercihi</strong> (dark/light) — localStorage</span>
            </li>
            <li className="flex gap-2">
              <span className="text-accent-400">•</span>
              <span><strong className="text-white">LLM tercihi</strong> (Gemini) — localStorage</span>
            </li>
          </ul>
          <p className="text-xs text-slate-400 italic mt-3">
            Reklam çerezleri, analytics tracking, üçüncü taraf takipçi kullanılmaz.
          </p>
        </Section>

        {/* 7. Haklarınız */}
        <Section icon={UserCheck} title="7. KVKK Madde 11 — Haklarınız" delay={0.45}>
          <p>Veri sahibi olarak aşağıdaki haklara sahipsin:</p>
          <div className="grid md:grid-cols-2 gap-3 mt-4">
            {USER_RIGHTS.map((r, i) => (
              <div key={i} className="rounded-xl border border-white/5 bg-white/[0.02] p-4 flex gap-3">
                <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shrink-0">
                  <r.icon size={16} className="text-emerald-300" />
                </div>
                <div>
                  <div className="font-display font-semibold text-white text-sm">{r.title}</div>
                  <div className="text-xs text-slate-400 mt-1">{r.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* 8. Güvenlik */}
        <Section icon={Shield} title="8. Güvenlik Önlemleri" delay={0.5}>
          <ul className="space-y-2 ml-2">
            <li className="flex gap-2"><span className="text-accent-400">✓</span> TLS 1.3 ile şifreli iletişim (HTTPS)</li>
            <li className="flex gap-2"><span className="text-accent-400">✓</span> Firestore Security Rules — kullanıcı yalnızca kendi verisine erişir</li>
            <li className="flex gap-2"><span className="text-accent-400">✓</span> Prompt injection savunması (input sanitizer)</li>
            <li className="flex gap-2"><span className="text-accent-400">✓</span> Rate limiting (20 sorgu/dk/IP)</li>
            <li className="flex gap-2"><span className="text-accent-400">✓</span> Audit log'larda PII SHA-256 hash'lenir</li>
            <li className="flex gap-2"><span className="text-accent-400">✓</span> Gemini API anahtarları yalnızca backend'de tutulur</li>
          </ul>
        </Section>

        {/* 9. İletişim */}
        <Section icon={Mail} title="9. İletişim" delay={0.55}>
          <p>
            Verilerinle ilgili herhangi bir talep veya soru için GitHub üzerinden iletişime geçebilirsin:
          </p>
          <a
            href="https://github.com/BrokyEwing/UniSense/issues"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 mt-3 px-4 py-2 rounded-xl bg-accent-500/10 border border-accent-500/30 text-accent-200 hover:bg-accent-500/20 text-sm transition"
          >
            <Mail size={14} />
            GitHub Issues
            <ExternalLink size={12} />
          </a>
        </Section>

        {/* 10. Değişiklikler */}
        <Section icon={AlertCircle} title="10. Bu Politikadaki Değişiklikler" delay={0.6}>
          <p>
            Politika değiştiğinde bu sayfanın üst kısmındaki "Son güncelleme" tarihi yenilenir. Önemli
            değişikliklerde uygulamaya giriş yaptığında bildirim gösterilir.
          </p>
        </Section>

        {/* Footer nav */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.7 }}
          className="text-center py-6"
        >
          <Link
            to="/anasayfa"
            className="text-sm text-slate-400 hover:text-accent-300 transition inline-flex items-center gap-2"
          >
            ← Ana sayfaya dön
          </Link>
        </motion.div>
      </div>
    </>
  )
}
