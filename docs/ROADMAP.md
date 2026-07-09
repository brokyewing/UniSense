# 🗺️ UniSense — Yol Haritası

**Son güncelleme:** 2026-05-17
**Sürüm:** v2.5 (Önlisans + Infobox + KVKK + Perf + Cron)

> Türkiye 2025 YKS üniversite tercih asistanı.

---

## 🎯 Vizyon

YÖK Atlas/ÖSYM verilerini doğal dilde sorgulayabilen, **kullanıcının ilgilerine
göre bölüm öneren**, tercih listesini akıllıca yöneten **kişisel tercih
asistanı**.

> "Ne istediğini bilmesen bile sana doğru bölümü buluruz."

---

## ✅ Tamamlananlar

### v2.5 (2026-05-17) — Zenginleştirme + Perf
- ✅ **Önlisans (TYT) chunk'ları** RAG'a eklendi (+9.337 chunk, toplam 23.876)
- ✅ **Wikipedia infobox enrich** — 219 üni için website + logo + kuruluş yılı + rektör + adres
- ✅ **KVKK / Gizlilik Politikası** sayfası (`/privacy` — 10 bölüm)
- ✅ **Embedding warm-up** (FastAPI lifespan startup → cold start ~10sn → ~4sn)
- ✅ **Gemini cevap cache** (TTLCache 1 saat → tekrar sorgu <300ms)
- ✅ **Retrieval optimize** (ChromaDB collection reuse, yeni client açma yok)
- ✅ **Frontend bundle split** (Vite manualChunks: react/three/firebase/ui)
- ✅ **Splash 3D lazy** (Three.js bundle ilk paint'i bloklamıyor)
- ✅ **GitHub Actions yıllık cron** (15 Ağustos → scrape + chunks + embed otomatik)
- ❌ **Qwen3-4B / UniSenseLocal kaldırıldı** (multi-LLM router, dataset, GGUF — disk ~2.4 GB temizlik)

### v2.0 (2026-05-07)
- ✅ Pusula (3 mod: Kart Seç, Soru Sor, 5 Soru) — 358 bölüm grubu, 9 kategori, 150+ ilgi pill
- ✅ Hesap Makinesi (TYT/AYT-SAY/EA/SÖZ/DİL/DGS + simulasyon)
- ✅ Önlisans verisi (9.337 program TYT — sadece data, RAG eklenmesi v2.5'te)
- ✅ Trend service (3 yıllık taban+sıra + momentum 📈/📉/📊)
- ✅ Coğrafi filtreler (28 sahil ili + 30 metropol + 31 merkez ilçe)
- ✅ Multi-turn chat (history son 8 mesaj)
- ✅ Akademik kadro + akreditasyon + burs + eğitim dili
- ✅ Firebase Auth + Firestore (Google/Email + sessions/tercih/profile/queries)
- ✅ TercihList drag-drop + ÖSYM kod chip + Kodları Kopyala + Kod ile Ekle
- ✅ Recommend Pusula gating + Devlet/Vakıf toggle + +Tercihe Ekle/Çıkar
- ✅ Profile YKS tab (puan/sıra/şehir/üni türü/preferred interests)
- ✅ Logo transparent PNG (RGB→RGBA) + favicon multi-size

### v1.x — Temel kurulum
- ✅ FastAPI 0.115 + Pydantic v2 + structlog + slowapi
- ✅ ChromaDB persistent (hibrit keyword + vector retrieval)
- ✅ Clean Architecture (domain → application → infrastructure)
- ✅ Gemini API multi-key + fallback chain
- ✅ Geo enrich + scrapers (YÖK Atlas, URAP, Wikipedia)

---

## 🚧 Şu an pending

### Faz 3 — Yeni özellikler (devam ediyor)
- ⏳ **Bölüm Karşılaştırma sayfası** (`/compare?d=X,Y,Z`)
  - Backend: `/api/v1/programs/compare` endpoint + `compare_service.py`
  - Frontend: `Compare.jsx` (yan yana tablo, recharts grafik)
  - TercihList'e "Karşılaştır" butonu
- ⏳ **Yerleşme olasılığı simülasyonu**
  - `rank_q1`/`rank_q3` quartile alanları → ECDF probability hesabı
  - `recommendation_service.py`'a `placement_probability` eklemesi
  - Recommend.jsx'te yüzde rozet (yeşil/sarı/kırmızı)
- ⏳ **Tercih başı kişisel notlar**
  - Firestore: `users/{uid}/tercih/{slot}` → `note` alanı
  - TercihList.jsx expandable textarea (max 500 char, debounced)

### Faz 4 — Production deploy
- ⏳ Backend → Render (Dockerfile + persistent disk for ChromaDB)
- ⏳ Frontend → Vercel
- ⏳ Firebase Security Rules (production) + API key restrictions
- ⏳ Uptime monitoring (UptimeRobot veya Better Stack)
- ⏳ README + dokümantasyon güncelleme (canlı URL'ler)

### Orta vade
- ⏳ DGS manuel scrape (yokatlas-py 0.6.0 desteklemiyor)
- ⏳ Geçmiş yıl history (2022, 2021) — 5 yıllık trend grafiği için
- ⏳ LinkedIn alumni intelligence (mezunlar nereye yerleşmiş)
- ⏳ Reddit/Ekşi öğrenci yorumları sentiment analizi
- ⏳ Maliyet hesabı (kira+yemek+ulaşım × 4 yıl)
- ⏳ Email bildirimleri (tercih son günü)

### Uzun vade
- ⏳ Mobile app (Expo)
- ⏳ Multi-year trend grafikleri (5 yıl backfill)
- ⏳ ÖSYM tercih öncesi hareketli demo (yerleşme olasılığı simulator)

---

## ❌ Vazgeçilenler & sebebi

| Özellik | Sebep |
|---|---|
| **UniSenseLocal (Qwen3-4B fine-tuned)** | v2.5'te kaldırıldı; tek LLM (Gemini) stratejisine geçildi |
| **DGS desteği (kısa vade)** | yokatlas-py 0.6.0'da DGS endpoint yok; HTML scrape karmaşık |
| **Akademisyen detay scrape (Avesis)** | Her üni farklı subdomain + HTML; YÖK Akademik anti-bot |

---

## 📊 Mevcut metrikler

- **Backend**: 21.602 program, 3.061 fakülte, 227 üni, **23.876 RAG chunk**
- **Wikipedia infobox enrich**: 219/227 üni (website + logo + kuruluş)
- **Frontend sayfa**: Splash, Home, Search, Pusula, Recommend, TercihList, Profile, Hesap, Login, **Privacy** (10 sayfa)
- **Auth**: Firebase Auth (Google + Email) + Firestore
- **LLM**: Gemini API (sadece)
- **Otomatik update**: GitHub Actions yıllık cron (15 Ağustos)

---

## 🚀 Sürüm tarihçesi

- **v2.5** (2026-05-17) — Zenginleştirme + Performans:
  - Önlisans RAG'a, Wikipedia infobox enrich, KVKK sayfası
  - Embedding warm-up, Gemini cache, retrieval optimize, bundle split
  - GitHub Actions yıllık cron
  - Qwen/UniSenseLocal kaldırıldı
- **v2.0** (2026-05-07) — Devasa güncelleme:
  - Pusula + Hesap Makinesi + Önlisans data + Trend + Coğrafi filtreler + Multi-turn chat
- **v1.5** — Tercih akışı sertleştirildi:
  - Pusula gating, drag-drop sıralama, ÖSYM kodu
- **v1.0** — Temel kurulum:
  - Clean Architecture, ChromaDB, Search, Recommend, Auth, Profile, Tema
