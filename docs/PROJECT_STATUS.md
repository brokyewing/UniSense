# 📊 UniSense — Proje Anlık Durumu

**Son güncelleme:** 2026-05-07
**Sürüm:** v2.0
**Bu doküman:** Projenin **şu an çalışan** sistemini gösterir.

---

## 🚦 Servisler — şu an

| Servis | URL / Yer | Durum | Sürüm |
|---|---|:-:|---|
| Backend (FastAPI) | http://localhost:8002 | ✅ Live | v2.0.0 |
| Frontend (Vite) | http://localhost:5173 | ✅ Live | React 18 + Vite 5 + Three.js |
| ChromaDB | `backend/data/embeddings/chromadb/` | ✅ 14.539 chunk | persistent (önlisans rebuild gerek) |
| Firebase Auth | Firebase project | ✅ Google + Email | — |
| Firestore | `users/{uid}/{sessions,tercih,profile,queries}` | ✅ Live | — |
| Ollama (UniSenseLocal) | localhost:11434 | ⏳ opsiyonel (training pending) | — |

### Health check

```bash
curl http://localhost:8002/api/v1/health
# {"status":"ok","version":"2.0.0","chunks_count":14539}

curl http://localhost:8002/api/v1/models
# {"models":[{"name":"Gemini","available":true},{"name":"UniSenseLocal","available":false}]}
```

---

## 🧪 Test edilebilir akış (uçtan uca)

```bash
# 1. Backend başlat
cd backend
uvicorn unisense.main:app --port 8002 --reload

# 2. Frontend başlat
cd frontend
npm run dev   # http://localhost:5173

# 3. UI akışı
Splash → "Başla"
  → Login (Google ile)
    → Pusula (Kart Seç → Yapay Zeka, Bilim, Sağlık)
      → Recommend (puan + sıra → safe/target/reach + Tercihe Ekle)
        → TercihList (drag-drop sırala → Kodları Kopyala)

# Yan akışlar
- Hesap Makinesi: TYT/AYT-SAY/EA/SÖZ/DİL/DGS net gir → puan
- Search: "denizi olan il + EA bölüm" → multi-turn RAG
- Profile YKS tab: puan + sıralama + ilgiler + üni türü kaydet
```

---

## 📦 Veri durumu (mevcut)

### ChromaDB

```yaml
collection: unisense
total_chunks: 14539
embedding_model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
embedding_dim: 384
persist_dir: backend/data/embeddings/chromadb
size: ~30 MB
not_yet_indexed: 9337 önlisans (rebuild bekliyor)
```

### Chunk dağılımı

| Tür | Sayı | Açıklama |
|---|---|---|
| **Lisans program** | 12.265 | İsim + üni + fakülte + il + puan + sıralama + kosul + kadro |
| **Üni özeti** | 227 | Türü + şehir + bölge + bölüm sayısı + akreditasyon |
| **Wikipedia** | 2.047 | Üni tarihçesi/kampüs/fakülte (200+ üni) |
| **Toplam (mevcut)** | **14.539** | |
| **Önlisans (pending rebuild)** | +9.337 | TYT puan, MYO programları |

### YÖK Atlas verisi

```yaml
yokatlas_total: 21602
  lisans: 12265 (SAY 5653 + EA 3987 + SÖZ 1948 + DİL 677)
  onlisans: 9337 (TYT)

universities:
  total: 227
  DEVLET: 128
  VAKIF: 74
  KKTC: 16
  YURTDIŞI_KAMU: 3
  YURTDIŞI_VAKIF: 2

faculties_and_myo: 3061

geo_regions:
  Marmara: 71 üni
  İç Anadolu: 44
  Karadeniz: 21
  Akdeniz: 19
  Ege: 18
  Doğu Anadolu: 17
  Güneydoğu Anadolu: 11
  Bilinmiyor / KKTC / Yurtdışı: 26

geo_metadata:
  sahil_illeri: 28
  metropoller: 30
  merkez_ilceler: 31

trend_history:
  years: [2025, 2024, 2023]   # rankings.json `history` alanı
```

### Dataset (Qwen fine-tuning)

```yaml
file: backend/data/training/unisense_dataset.jsonl
size: 16.5 MB
examples: 58585
format: Alpaca (instruction + input + output)
tokens_estimate: ~5.7M

categories:
  - Tüm program detayı (her bölüm için Q/A)
  - 3-yıl trend analizi
  - Akademik kadro sayıları
  - Akreditasyon (MÜDEK, FEDEK, TEPDAD)
  - Burs/ücret bilgisi
  - Eğitim dili (TR/İng/Alm/Fr/Ar)
  - Coğrafi (sahil/metropol/merkez)
  - İlgi → bölüm
  - Hesap mantığı (TYT/AYT formül)
  - Önlisans (TYT)
  - Fakülte/MYO listesi
  - Üni özet karşılaştırma

kaggle:
  dataset_slug: ibrahimaskeroglu/unisense-dataset
  upload_path: training/unisense_dataset.jsonl
```

---

## 📁 Disk durumu

```
C:\Users\asker\Projelerim\UniSense\
├── backend/
│   ├── src/unisense/        (Clean Architecture)
│   ├── scripts/             (build_unisense_dataset, enrich_geo)
│   ├── data/
│   │   ├── raw/yokatlas/    (lisans + önlisans + universities)
│   │   ├── processed/       (universities, programs, faculties, rankings, chunks)
│   │   ├── embeddings/chromadb/   (14.539 chunk persistent)
│   │   └── training/        (unisense_dataset.jsonl + Kaggle notebook + metadata)
│   └── pyproject.toml
│
├── frontend/                (React + Vite + Three.js + Firebase)
│   ├── src/pages/           (9 sayfa)
│   ├── src/components/three/
│   └── public/              (logo.png transparent + favicon)
│
└── docs/                    (4 MD: ROADMAP, AI_CONTEXT, PROJECT_STATUS, HANDOFF)
```

---

## 🤖 Aktif LLM Modelleri

### 1. Gemini API (default, üretim)
- **Model:** `gemini-3.1-flash-lite-preview` (preview), fallback chain otomatik
- **Multi-key:** virgülle ayrılmış GEMINI_API_KEYS, round-robin + 429 fallback
- **Quota:** 15 RPM / 500 RPD (per-key, free tier)
- **Multi-turn:** chat history son 8 mesaj `contents` formatında

### 2. UniSenseLocal (Ollama Qwen3-4B fine-tuned) — opsiyonel
- **Status:** Dataset 58.5k hazır, Kaggle eğitim bekleniyor (~6-8 saat T4)
- **Provider:** `infrastructure/llm/qwen.py` (Ollama HTTP client)
- **Frontend:** Search'te LLM seçici (Gemini ↔ UniSenseLocal)

---

## 🔌 API Endpoints

```
GET  /api/v1/health                  # liveness + chunks_count
GET  /api/v1/models                  # hangi LLM'ler aktif
POST /api/v1/ask                     # multi-turn RAG + intent + LLM seçimi
POST /api/v1/recommend               # safe/target/reach + filter + geo
POST /api/v1/programs/lookup         # ÖSYM kodu / dept_group → detay
GET  /api/v1/compass/taxonomy        # 358 lisans grup, 9 kategori
GET  /api/v1/compass/interests       # 150+ ilgi pill
POST /api/v1/compass/by-selection    # seçili kategori → bölüm
POST /api/v1/compass/by-text         # metin → 5-axis → bölüm
POST /api/v1/compass/by-axes         # açık vektör → bölüm
POST /api/v1/compass/by-interests    # ilgi pill set → bölüm
GET  /api/docs                       # Swagger UI (dev)
```

---

## 🎨 Frontend (9 sayfa)

| Route | Sayfa | Özellikler |
|---|---|---|
| `/` | **Splash** | 3D arkaplan + Logo (sağ üst, ThemeToggle yanında) |
| `/home` | **Home** | Hero + 4 stat (227 üni, 21.6k program, 3.1k fakülte, 7 bölge) |
| `/login` | **Login** | Firebase Auth (Google + Email) + Logo |
| `/profile` | **Profile** | 3 tab: Hesap, Şifre, **YKS** (puan/sıra/şehir/üni türü/preferred interests) |
| `/pusula` | **Pusula** | 3 mod: **Kart Seç** (ilgi pill) / **Soru Sor** (Search'e) / **5 Soru** |
| `/search` | **Search** | RAG + multi-turn (son 4) + LLM seçici + collapsible kaynak + auto-scroll fix |
| `/recommend` | **Recommend** | Pusula gating + Devlet/Vakıf toggle + +Tercihe Ekle/Çıkar + safe/target/reach |
| `/tercih` | **TercihList** | drag-drop (@dnd-kit) + ↑↓ + ÖSYM kod chip + Sıraya Göre Diz + Kodları Kopyala + Kod ile Ekle |
| `/hesap` | **Hesap Makinesi** | TYT/AYT-SAY/EA/SÖZ/DİL/DGS + ders katsayı + OBP 100'lük (DGS 4'lük) + simulasyon paneli |

### Tema
- Dark/Light toggle (3D arkaplan korunur)
- Cyber palet: brand mavi, accent mor, cyan/pink/violet
- Logo: transparent PNG (RGB→RGBA, 190.690 piksel alpha=0)
- Favicon: regenerated multi-size with alpha

---

## 🐛 Bilinen sorunlar / Kısıtlar

1. **DGS desteği yok** — yokatlas-py 0.6.0 desteklemiyor; HTML scrape karmaşık (manuel ileride)
2. **ChromaDB önlisans pending** — 9.337 önlisans chunk RAG'a henüz eklenmedi
3. **ChromaDB cold start** — ilk sorgu ~5sn (model + index yükler)
4. **Gemini quota** — 500 RPD/key, multi-key ile artırılır
5. **UniSenseLocal training pending** — dataset hazır, Kaggle T4 eğitim bekleniyor
6. **Avesis akademisyen detay** — her üni farklı subdomain, sadece link gösterimi
7. **YÖK Akademik anti-bot** — scrape edilemez, manuel link önerme

---

## 🔧 Güvenlik aktif özellikler

| Katman | Durum |
|---|---|
| Prompt injection defense (TR+EN) | ✅ Aktif |
| Unicode NFKC normalize | ✅ Aktif |
| Max query length 500 | ✅ Aktif |
| Rate limiting (slowapi 20/dk) | ✅ Aktif |
| CORS whitelist | ✅ Aktif |
| Audit log (PII hash) | ✅ Aktif |
| structlog JSON | ✅ Aktif |
| API Key auth | ⚠️ Kapalı (dev) |
| Firebase Auth | ✅ Google + Email |

---

## 📈 Performans metrikleri

```yaml
endpoint_latency_p50:
  /api/v1/health: 50ms
  /api/v1/ask: 4000ms (Gemini ortalama, multi-turn)
  /api/v1/recommend: 200ms (DB lookup)
  /api/v1/compass/*: 100ms

endpoint_latency_p95:
  /api/v1/ask: 9500ms (cold start dahil)

bottlenecks:
  - Gemini API: 3-5 sn (multi-turn için biraz daha)
  - Embedder ilk yükleme: ~10sn (CUDA init)
  - ChromaDB sorgu: <50ms

memory:
  - ChromaDB: ~30 MB
  - Embedding model: ~470 MB
  - Toplam process: ~2 GB
```

---

## 🔑 Env durumu

Backend `.env` zorunlu:
```env
GEMINI_API_KEYS=AIza...key1,AIza...key2
APP_PORT=8002
CHROMA_PERSIST_DIR=./data/embeddings/chromadb
```

Backend `.env` opsiyonel:
```env
OLLAMA_URL=http://localhost:11434      # UniSenseLocal için
SECURITY_REQUIRE_API_KEY=false          # prod için true
RATE_LIMIT_ASK=20
CORS_ALLOWED_ORIGINS=https://unisense.app,http://localhost:5173
```

Frontend `.env`:
```env
VITE_API_URL=http://localhost:8002
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
```

---

## 📋 Hemen sırada (kısa vade)

- [ ] Kaggle Qwen eğitimi başlat (dataset Kaggle'a yüklendi, notebook hazır)
- [ ] ChromaDB rebuild — önlisans chunk'ları RAG'a ekle (Search önlisans cevapları için)
- [ ] DGS desteği — manuel HTML scrape veya ÖSYM PDF parser
- [ ] Bölüm karşılaştırma sayfası (`/compare?d=X,Y,Z`)
- [ ] Yerleşme olasılığı simülasyonu (`rank_q1`/`rank_q3` kullanılarak)
- [ ] Üretim deploy: Vercel (frontend) + Render/Cloudflare Tunnel (backend)
- [ ] KVKK / Gizlilik politikası sayfası

---

## 🔄 v2.0 değişiklikleri (özet)

**Eklendi:**
- **Pusula** (3 mod: Kart Seç, Soru Sor, 5 Soru) — 358 bölüm grubu, 9 kategori, 150+ ilgi pill
- **Hesap Makinesi** (TYT/AYT-SAY/EA/SÖZ/DİL/DGS + simulasyon)
- **Trend service** (3 yıllık taban+sıra tablosu + momentum)
- **Coğrafi filtreler** (sahil/metropol/merkez ilçe)
- **Multi-turn chat** (history son 8 mesaj)
- **LLM seçici** (Gemini ↔ UniSenseLocal)
- **Önlisans verisi** (9.337 program TYT)
- **Akademik kadro + akreditasyon + burs + eğitim dili** zenginleştirmeleri
- **Firebase Auth + Firestore** (Google/Email + sessions/tercih/profile/queries)
- **TercihList** drag-drop + ÖSYM kod chip + Kodları Kopyala + Kod ile Ekle
- **Recommend** Pusula gating + Devlet/Vakıf toggle + +Tercihe Ekle/Çıkar
- **Profile YKS tab** (puan/sıra/şehir/üni türü/preferred interests)
- **Logo transparent** (RGB→RGBA) + favicon multi-size

**Pipeline:**
- `build_unisense_dataset.py` (58.585 Q/A 12 kategori)
- `unisense-egitimi-kaggle.ipynb` (Qwen3-4B LoRA T4)
- `infrastructure/llm/qwen.py` (Ollama provider)
- `infrastructure/llm/multi_router.py` (LLM router)

---

## 📞 Sorun yaşarsan

```yaml
backend_500:
  - check: "tail backend/logs/*.log"
  - common: "Gemini key invalid → .env güncelle"
  - common: "Önlisans chunk yok → ChromaDB rebuild"

ask_yavas:
  - cause: "ChromaDB cold start + Gemini latency"
  - normal: "ilk istek 10s sonra <5s"

multi_llm_router_hata:
  - cause: "AskService LLM hasattr check eksik"
  - fix: "if hasattr(self._llm, '_providers'): kwargs['model_preference'] = ..."

turkish_karakter_bozuk:
  - cause: "Python default lower/upper"
  - fix: "_tr_lower / _tr_upper kullan (retrieval_service.py)"

frontend_blank:
  - check: "browser console + dev server log"
  - common: "Three.js shader error → npm install yenile"

logo_arka_plan_var:
  - cause: "PNG RGB modunda, alpha yok"
  - fix: "PIL ile RGBA dönüştür, white→alpha=0"

favicon_gelmiyor:
  - cause: "favicon.ico cache + index.html link sırası"
  - fix: "PNG link'leri .ico'dan önce, hard refresh"
```
