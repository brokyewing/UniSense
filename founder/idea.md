# UniSense

- What it is: Türkiye üniversite tercih asistanı — RAG (Retrieval-Augmented Generation) ile YÖK Atlas/ÖSYM/URAP/Wikipedia verilerinden **gerçek sayılarla** bölüm önerileri üreten açık kaynak web uygulaması.

- Who it is for: YKS/DGS/KPSS/LGS/TUS/DUS sınavına girecek **öğrenciler** (yıllık ~2.5M aday) + velileri + okul müdürleri/rehber öğretmenleri. Segmentler: YKS (lisans), DGS (dikey geçiş), KPSS (memurluk), LGS (liseler), TUS/DUS (uzmanlık).

- What it sells, at what price: **Ücretsiz** (freemium). Core features: RAG tabanlı doğal dil sorgulama, Tercih Robotları (güvenli/hedef/riskli kovalar), Pusula (ilgi alanı → bölüm), Hesap Makinesi (net → puan), Bölüm Karşılaştırma, Kariyer Sinyalleri, Konu Takibi. Potansiyel premium: sınırsız sorgu, PDF rapor, e-posta hatırlatıcı, öncelikli destek.

- Where and how: Web (React + Vite + Tailwind, Vercel deploy) + API (FastAPI + ChromaDB, Render deploy). Kullanıcı: tarayıcıdan girer, Firebase Auth (Google/Email) ile giriş, veriler Firestore'da. SEO: programmatic sayfalar (bölüm/üniversite/taban puan), sitemap 631 URL.

- Budget and constraints:
  - Bütçe: $0 (açık kaynak, gönüllü geliştirici). Hosting: Render $7/ay (starter), Vercel Hobby (ücretsiz), Firebase Spark (ücretsiz).
  - Zaman: Tek geliştirici (part-time). Codebase: ~150 dosya, 85 Python + 54 JS/JSX.
  - Kısıtlar: Gemini free tier kota (1500 RPD Flash-Lite), ChromaDB 512MB RAM limiti (lokal embedding), YÖK Atlas/ÖSYM resmi veriler (scraping rate limit), mobil performans (three.js 856KB chunk).
  - Teknik borç: 4 pre-existing test failure (kariyer), SIM115/DTZ011 lint ignore, pre-commit hook yok, CI 18 commit kırmızı kaldı.