# Board Brief — UniSense

## Idea Summary
UniSense: Türkiye üniversite tercih asistanı. RAG + YÖK Atlas/ÖSYM/URAP/Wikipedia verileriyle öğrencinin puan/ilgi alanına göre **gerçek sayılarla** bölüm önerisi üreten açık kaynak web uygulaması.

## Target Customer
- **Primary**: YKS/DGS/KPSS/LGS/TUS/DUS adayları (yıllık ~2.5M)
- **Secondary**: Veliler, okul müdürleri, rehber öğretmenler
- **Segments**: YKS (lisans), DGS (dikey geçiş), KPSS (memurluk), LGS (liseler), TUS/DUS (uzmanlık)

## Product
| Feature | Description |
|---------|-------------|
| RAG Sorgulama | "İstanbul'da 80 bin sıralamayla bilgisayar mühendisliği" → kaynaklı cevap + ÖSYM kodları |
| Tercih Robotları | Puan/sıralama → güvenli/hedef/riskli kovalar + yerleşme olasılığı (sigmoid) |
| Pusula | İlgi alanı + güçlü dersler + şehir → bölüm önerisi (4 mod) |
| Hesap Makinesi | Net → YKS/DGS/KPSS/TUS puan + simülasyon |
| Bölüm Karşılaştırma | 2-5 program yan yana (taban, trend, kadro, ücret, akreditasyon) |
| Kariyer Sinyalleri | Günlük kamu/özel ilanlar (RG, Kariyer Kapısı, Jooble, Careerjet, ATS) |
| Konu Takibi / Planım | YKS/KPSS/DGS/LGS konuları + AI çalışma planı |

**Freemium model**: Core ücretsiz. Potansiyel premium: sınırsız sorgu, PDF rapor, e-posta hatırlatıcı.

## Distribution
- Web (React/Vite/Tailwind → Vercel) + API (FastAPI/ChromaDB → Render)
- SEO: Programmatic sayfalar (bölüm/üniversite/taban puan), sitemap 631 URL
- Auth: Firebase (Google + Email), veriler Firestore
- Mobil: PWA manifest, three.js arka plan (opsiyonel)

## Traction / Data
- YÖK Atlas: 221 üniversite, 600+ bölüm, yıllık taban puan/sıralama/kontenjan
- ÖSYM: Tercih kodları, puan türleri, yerleştirme verileri
- URAP: Akademik sıralama
- Wikipedia: 221 üniversite infobox (logo, kuruluş, rektör, adres)
- Kariyer: 10+ kaynak (RG, Jooble, Careerjet, ATS, Kariyer Kapısı, Savunma Kariyer, vb.)
- Veri güncelleme: Yıllık GitHub Actions cron (Ağustos)

## Tech Stack
- Backend: Python 3.11, FastAPI, Pydantic v2, ChromaDB (vector), sentence-transformers (lokal Model2Vec), Gemini 2.5 Flash-Lite
- Frontend: React 18, Vite 5, Tailwind 3, Framer Motion, React Three Fiber, Firebase SDK 11
- Infrastructure: Render (Docker), Vercel, Firebase, GitHub Actions (CI/CD + yearly data sync)

## Budget & Constraints
- **Budget**: $0 (açık kaynak, gönüllü). Hosting ~$7/ay (Render starter)
- **Team**: 1 geliştirici (part-time)
- **Technical debt**: 
  - 4 kariyer test failure (pre-existing)
  - SIM115 (35 `json.load(open)`), DTZ011 (date.today) lint ignore
  - Pre-commit hook yok → CI 18 commit kırmızı kaldı
  - BackgroundScene (three.js) her sayfada → mobil pil tüketimi
  - Kariyer scraper 1559 satır tek dosya (modülerleştirme yapıldı ama test edilmeli)
- **Rate limits**: Gemini 1500 RPD (Flash-Lite), scraping rate limitler

## Key Questions for Board
1. **Market**: YKS tercih danışmanlığı pazarı ne kadar? (resmi/özel danışman ücretleri 500-5000 TL)
2. **Monetization**: Freemium → premium geçiş oranı ne olabilir? (benzer SaaS: %2-5)
3. **Moat**: Veri + RAG pipeline mi, yoksa marka/SEO mu? Copycat riski?
4. **Distribution**: SEO organic trafik yeterli mi? Paid/referral gerekir mi?
5. **Team**: Tek geliştirici ölçeklenebilir mi? Neleri outsource/delegate edilebilir?