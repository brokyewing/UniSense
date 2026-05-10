# 🗺️ UniSense — Yol Haritası

**Son güncelleme:** 2026-05-07
**Sürüm:** v2.0 (Pusula + Hesap + Önlisans + Qwen fine-tuning hazır)

> Türkiye 2025 YKS üniversite tercih asistanı.

---

## 🎯 Vizyon

YÖK Atlas/ÖSYM verilerini doğal dilde sorgulayabilen, **kullanıcının ilgilerine
göre bölüm öneren**, tercih listesini akıllıca yöneten **kişisel tercih
asistanı**.

> "Ne istediğini bilmesen bile sana doğru bölümü buluruz."

---

## ✅ Tamamlananlar (v2.0)

### Veri katmanı
- ✅ **227 üniversite** (DEVLET 128 + VAKIF 74 + KKTC 16 + diğer)
- ✅ **21.602 program** (12.265 lisans + 9.337 önlisans)
- ✅ **3.061 fakülte/MYO**
- ✅ **Trend verisi (3 yıl):** rankings.json `history` alanında 2024+2023 otomatik
- ✅ **Coğrafi metadata:** 28 sahil ili (deniz adları, kıyı km), 30 metropol, 31 ilin merkez ilçeleri
- ✅ **Akademik kadro:** prof, doçent, dr.üyesi, ar.gör., öğr.gör. sayıları
- ✅ **Akreditasyon:** MÜDEK, FEDEK, TEPDAD, vs.
- ✅ **ÖSYM koşul kodları:** kosulList parser
- ✅ **Burs/ücret bilgisi:** vakıf programları için
- ✅ **Eğitim dili:** TR/İngilizce/Almanca/Fransızca/Arapça
- ❌ DGS — yokatlas-py 0.6.0 desteklemiyor, ileride manuel scrape

### Backend (Clean Architecture)
- ✅ FastAPI 0.115 + Pydantic v2 + structlog + slowapi
- ✅ ChromaDB (14.539 chunk; önlisans için rebuild gerek)
- ✅ Hybrid retrieval (keyword + vector, Türkçe-safe upper/lower)
- ✅ AskService **multi-turn chat** (history son 8 mesaj)
- ✅ AskService **intent routing** — sıra/puan/coğrafi pattern detect → Recommend hybrid context
- ✅ Recommend service: safe/target/reach kovaları + filtreler (puan türü, üni türü, şehir, bölüm, geo)
- ✅ Compass service: 358 lisans bölüm grubu, 9 kategori, 150+ ilgi pill, 5-boyutlu kişilik vektörü
- ✅ Trend service: program-bazlı 3 yıllık tablo + momentum (📈/📉/📊)
- ✅ Geo enrich: deniz/merkez/metropol filtreleri Recommend'a entegre
- ✅ Multi-LLM router: Gemini (default) + UniSenseLocal (Ollama, opsiyonel)
- ✅ `/api/v1/models` endpoint — frontend hangisi available öğrenir

### LLM
- ✅ **Gemini API** — multi-key, model fallback chain (3.1 Flash Lite preview)
- ✅ Quota dolunca fast model'e fallback
- ✅ 404 / model not found handling
- ✅ Multi-turn `contents` formatı (chat history desteği)
- ⏳ **UniSenseLocal (Qwen3-4B fine-tuned)** — dataset 58k hazır, Kaggle eğitim bekleniyor

### Frontend (React + Vite)
- ✅ **Splash** — 3D arkaplan + Logo (sağ üst, ThemeToggle yanında)
- ✅ **Auth** — Login (Google + Email) + Logo, Profile sayfa (avatar + şifre + YKS)
- ✅ **Profile YKS tab:** puan/sıra/şehir/üni tipi/preferred interests
- ✅ **Pusula** — 3 mod: Kart Seç (ilgi pill'leri), Soru Sor (Search'e yönlendir), 5 Soru
- ✅ **Recommend** — Pusula gating, Devlet/Vakıf toggle, +Tercihe Ekle/-Çıkar
- ✅ **Hesap Makinesi** — TYT/AYT-SAY/EA/SÖZ/DİL/DGS, ders-bazlı katsayı, OBP 100'lük (DGS 4'lük), simulasyon paneli
- ✅ **Search** — RAG + multi-turn + LLM seçici (Gemini/UniSenseLocal) + kaynak collapsible + auto-scroll fix
- ✅ **TercihList** — drag-drop sıralama (@dnd-kit) + ↑↓ butonlar + ÖSYM kodu chip + sıra/taban/kontenjan + auto-fill backfill + Sıraya Göre Diz + Kodları Kopyala + Kod ile Ekle (manuel input)
- ✅ **Tema** dark/light (3D arkaplan korunur)
- ✅ **Logo** — yeni transparent PNG (RGB → RGBA dönüştürüldü), favicon güncel

### UX akış (uçtan uca)
```
Splash → Login → Pusula (ilgi seç) → Recommend (puan + tercih) → TercihList (sırala + ÖSYM kod kopyala)
       Hesap (net gir → puan)  ↗
       Search (sohbet RAG)     ↗
```

### NLP / Dataset (Qwen fine-tuning için)
- ✅ **build_unisense_dataset.py** — 58.585 unique Q/A çifti (Alpaca format, 16.5 MB)
- ✅ Kategoriler: tüm program detayı, trend, akademik kadro, akreditasyon, burs, eğitim dili, coğrafi, ilgi, hesap mantığı
- ✅ **unisense-egitimi-kaggle.ipynb** — Qwen3-4B-Instruct-2507 LoRA pipeline
- ✅ Ollama provider (`infrastructure/llm/qwen.py`) + multi-router

---

## 🚧 Şu an pending

### Hemen yapılacaklar
- ⏳ **Kaggle Qwen eğitimi başlat** — dataset Kaggle'a yüklendi, notebook hazır, eğitim bekleniyor (~6-8 saat T4)
- ⏳ ChromaDB rebuild — önlisans chunk'ları RAG'a eklensin (Search'te önlisans cevapları için)

### Kısa vade (1-2 hafta)
- ⏳ DGS desteği — yokatlas-py'da yok, HTML scrape veya ÖSYM PDF parser
- ⏳ Bölüm karşılaştırma sayfası (`/compare?d=X,Y,Z`)
- ⏳ Yerleşme olasılığı simülasyonu (`rank_q1`/`rank_q3` kullanılarak)
- ⏳ Üretim deploy: Vercel (frontend) + Render/Cloudflare Tunnel (backend)
- ⏳ KVKK / Gizlilik politikası sayfası

### Orta vade
- ⏳ LinkedIn alumni intelligence (mezunlar nereye yerleşmiş)
- ⏳ Reddit/Ekşi öğrenci yorumlarından sentiment analizi
- ⏳ Maliyet hesabı (kira+yemek+ulaşım × 4 yıl)
- ⏳ Bölüm önerisinden sonra "kişisel notlar" alanı (her tercih için)
- ⏳ Email bildirimleri (tercih son günü)

### Uzun vade
- ⏳ Mobile app (Expo)
- ⏳ Multi-year trend grafikleri (5 yıl backfill)
- ⏳ ÖSYM tercih öncesi hareketli demo (yerleşme olasılığı simulator)

---

## ❌ Vazgeçilenler & sebebi

| Özellik | Sebep |
|---|---|
| **DGS desteği (kısa vade)** | yokatlas-py 0.6.0'da DGS endpoint yok; HTML scrape karmaşık |
| **Akademisyen detay scrape (Avesis)** | Her üni farklı subdomain + HTML; YÖK Akademik anti-bot. Çözüm: linkin gösterimi |
| **Cloudflare Tunnel + Ollama lokal** | Henüz değerlendirilecek; UniSenseLocal kullanmak için Ollama gerek |

---

## 📊 Mevcut metrikler

- **Backend**: 21.602 program, 3.061 fakülte, 227 üni, 14.539 RAG chunk
- **Dataset (Qwen fine-tuning)**: 58.585 Q/A (16.5 MB JSONL, ~5.7M token)
- **Frontend sayfa**: Splash, Home, Search, Pusula, Recommend, TercihList, Profile, Hesap, Login (9 sayfa)
- **Auth**: Firebase Auth (Google + Email) + Firestore (sessions, tercih, profile, queries)
- **API endpoints**: `/ask`, `/recommend`, `/health`, `/models`, `/programs/lookup`, `/compass/{taxonomy,interests,by-selection,by-text,by-axes,by-interests}`

---

## 🚀 Sürüm tarihçesi

- **v2.0** (2026-05-07) — Devasa güncelleme:
  - Pusula (İlgi Pusulası) + Hesap Makinesi + Önlisans + Trend + Coğrafi filtreler + Multi-turn chat + LLM seçici + Logo + Favicon transparent
  - Qwen fine-tuning pipeline (dataset + notebook + Ollama provider) hazır
- **v1.5** — Tercih akışı sertleştirildi:
  - Pusula gating, drag-drop sıralama, ÖSYM kodu, +Tercihe Ekle/Çıkar, Kod ile Ekle
- **v1.0** — Temel kurulum:
  - Clean Architecture, ChromaDB, Search, Recommend, Auth, Profile, Tema
