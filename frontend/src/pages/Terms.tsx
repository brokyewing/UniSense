import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Scale, AlertTriangle, ShieldCheck, BookOpen, ExternalLink } from 'lucide-react'
import BackgroundScene from '../components/three/LazyBackgroundScene'

export default function Terms() {
  return (
    <>
      <BackgroundScene />

      <div className="space-y-6 max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center pt-4"
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium mb-4">
            <Scale size={12} />
            Bilgilendirme &amp; İlk Taslak Metni
          </div>
          <h1 className="text-3xl md:text-5xl font-display font-bold text-white mb-3">
            Kullanım Koşulları ve <span className="gradient-text">Yasal Uyarı</span>
          </h1>
          <p className="text-sm text-slate-400">
            Son güncelleme: 27 Kasım 2026
          </p>
        </motion.div>

        <div className="card border-amber-500/30 bg-amber-500/5 text-sm text-amber-100 leading-relaxed flex items-start gap-3">
          <AlertTriangle size={20} className="text-amber-300 shrink-0 mt-0.5" />
          <div>
            <strong>Önemli Bilgilendirme:</strong> UniSense; <strong>ÖSYM, YÖK, YÖK Atlas</strong> veya{' '}
            <strong>MEB</strong> ile resmî bağı bulunmayan bağımsız, ücretsiz bir yardımcı araçtır. Tüm puan
            hesaplamaları, sıralama tahminleri, yerleşme olasılıkları ve yapay zekâ yanıtları{' '}
            <strong>kesin garanti teşkil etmez</strong>; resmî tercih onayı öncesinde verileri{' '}
            <a href="https://yokatlas.yok.gov.tr" target="_blank" rel="noopener noreferrer" className="underline text-amber-300">
              yokatlas.yok.gov.tr
            </a>{' '}
            ve{' '}
            <a href="https://www.osym.gov.tr" target="_blank" rel="noopener noreferrer" className="underline text-amber-300">
              osym.gov.tr
            </a>{' '}
            üzerinden teyit etmen gerekir.
          </div>
        </div>

        <section className="card space-y-3 text-sm text-slate-300 leading-relaxed">
          <h2 className="font-display font-semibold text-xl text-white flex items-center gap-2">
            <BookOpen size={18} className="text-accent-300" /> 1. Hizmetin Kapsamı ve Niteliği
          </h2>
          <p>
            UniSense, geçmiş dönem kamuya açık ÖSYM, YÖK Atlas ve MEB istatistiklerine dayanarak adaylara
            ücretsiz tercih planlama, yaklaşık puan/net hesaplama, konu/deneme takibi ve kariyer ilanı sinyalleri sunar.
            Her yıl kontenjanlar, aday dağılımları ve sınav standart sapmaları değiştiği için önceki yıllara ait taban puan
            ve başarı sıralamaları gelecek yerleştirme sonuçlarını garanti etmez.
          </p>
        </section>

        <section className="card space-y-3 text-sm text-slate-300 leading-relaxed">
          <h2 className="font-display font-semibold text-xl text-white flex items-center gap-2">
            <AlertTriangle size={18} className="text-accent-300" /> 2. Sorumluluk Sınırı
          </h2>
          <ul className="space-y-2 list-disc list-inside">
            <li>YKS, LGS, ALES, AGS, DGS, KPSS ve TUS/DUS puan hesaplayıcıları bilgilendirme amaçlı yaklaşık hesaplama yapar.</li>
            <li>Yapay zekâ destekli sorgu çıktıları yalnızca referans verisiyle sınırlıdır; ÖSYM tercih kılavuzundaki özel koşul ve bakınız maddeleri mutlaka aday tarafından kontrol edilmelidir.</li>
            <li>Adayların ÖSYM AİS veya MEB e-Okul üzerinden yaptığı nihai tercih sıralaması ve tesliminden kullanıcının kendisi sorumludur.</li>
          </ul>
        </section>

        <section className="card space-y-3 text-sm text-slate-300 leading-relaxed">
          <h2 className="font-display font-semibold text-xl text-white flex items-center gap-2">
            <ShieldCheck size={18} className="text-accent-300" /> 3. Reşit Olmayan Kullanıcılar ve Kişisel Veriler
          </h2>
          <p>
            18 yaşından küçük (LGS / lise öğrencisi) ziyaretçiler tüm hesaplama ve tercih robotu araçlarını{' '}
            <strong>hesap açmadan ve kişisel veri paylaşmadan</strong> misafir olarak kullanabilir. Üyelik oluşturulması
            hâlinde 18 yaş altı adayların yasal temsilci/veli bilgisi ve onayı ile hareket etmesi beklenir. Kişisel veri
            işleme esasları için{' '}
            <Link to="/gizlilik" className="text-accent-300 hover:underline">
              KVKK / Gizlilik Politikası
            </Link>{' '}
            sayfasını inceleyebilirsin.
          </p>
        </section>

        <section className="card space-y-3 text-sm text-slate-300 leading-relaxed">
          <h2 className="font-display font-semibold text-xl text-white flex items-center gap-2">
            <ExternalLink size={18} className="text-accent-300" /> 4. Kabul Edilebilir Kullanım ve Uygulanacak Hukuk
          </h2>
          <p>
            Platforma otomatik bot/aşırı istek göndermek, güvenlik kontrollerini aşmaya çalışmak veya sahte veriyle liderlik
            tablosunu manipüle etmek yasaktır. Bu koşullar Türkiye Cumhuriyeti hukukuna tabidir.
          </p>
          <p className="text-xs text-slate-500 italic">
            Not: Bu sayfa ilk inceleme taslağı niteliğindedir; hukuki tavsiye değildir.
          </p>
        </section>

        <div className="text-center py-4 flex items-center justify-center gap-4 text-sm">
          <Link to="/" className="text-slate-400 hover:text-accent-300 transition">← Ana sayfaya dön</Link>
          <Link to="/gizlilik" className="text-accent-400 hover:underline">KVKK / Gizlilik Politikası</Link>
        </div>
      </div>
    </>
  )
}
