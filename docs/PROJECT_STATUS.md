# 📊 UniSense — Proje Anlık Durumu

**Son güncelleme:** 2026-05-17
**Sürüm:** v3.0
**Bu doküman:** Projenin **şu an çalışan** sistemini gösterir.

---

## 🚦 Servisler — şu an

| Servis | URL / Yer | Durum | Sürüm |
|---|---|:-:|---|
| Backend (FastAPI) | http://localhost:8002 | ✅ Live | v0.1.0 |
| Frontend (Vite) | http://localhost:5174 | ✅ Live | React 18 + Vite 5 + Three.js |
| ChromaDB | `backend/data/embeddings/chromadb/` | ✅ **23.876 chunk** | persistent (lisans + önlisans + wiki) |
| Firebase Auth | Firebase project | ✅ Google + Email | — |
| Firestore | `users/{uid}/{sessions,tercih,profile,queries}` | ✅ Live | — |
| GitHub Actions | `.github/workflows/yearly-data-sync.yml` | ✅ Cron (15 Ağu) | scrape + chunks + embed otomatik |
| Render (backend prod) | hazır | ⏳ deploy bekliyor | `backend/render.yaml` |
| Vercel (frontend prod) | hazır | ⏳ deploy bekliyor | `frontend/vercel.json` |

### Health check

```bash
curl http://localhost:8002/api/v1/health
# {"status":"ok","version":"0.1.0","chunks_count":23876}

curl http://localhost:8002/api/v1/models
# {"models":[{"id":"gemini","name":"Gemini","available":true,"description":"..."}]}
```

---

## 🧪 Test edilebilir akış (uçtan uca)

```bash
# 1. Backend başlat (lifespan warmup ile cold start ~4sn)
cd backend
uvicorn unisense.main:app --port 8002 --reload

# 2. Frontend başlat
cd frontend
npm run dev   # http://localhost:5174

# 3. UI akışı
Splash → "Başla"
  → Login (Google ile)
    → Pusula (Kart Seç → Yapay Zeka, Bilim, Sağlık)
      → Recommend (puan + sıra → safe/target/reach + Yerleşme % rozet + Tercihe Ekle)
        → TercihList (drag-drop sırala → Notlar + Karşılaştır → Kodları Kopyala)
          → Compare (2-5 program yan yana, EN İYİ/EN ZAYIF vurgu, mini trend)

# Yan akışlar
- Hesap Makinesi: TYT/AYT-SAY/EA/SÖZ/DİL/DGS net gir → puan
- Search: "ITÜ web sitesi nedir?", "Boğaziçi ne zaman kuruldu?" (Wikipedia infobox)
- Privacy: /privacy → KVKK politikası (10 bölüm)
- Profile YKS tab: puan + sıralama + ilgiler + üni türü kaydet
```

---

## 📦 Veri durumu (mevcut)

### ChromaDB

```yaml
collection: unisense
total_chunks: 23876
embedding_model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
embedding_dim: 384
persist_dir: backend/data/embeddings/chromadb
size: ~50 MB
```

### Chunk dağılımı

| Tür | Sayı | Açıklama |
|---|---|---|
| **Lisans program** | 12.265 | İsim + üni + fakülte + il + puan + sıralama + koşul + kadro |
| **Önlisans program** | 9.337 | TYT puan, MYO programları |
| **Üni özeti** | 227 | Türü + şehir + bölge + bölüm sayısı + **website + logo + kuruluş yılı + rektör + adres** (Wikipedia infobox enrich) |
| **Wikipedia** | 2.047 | Üni tarihçesi/kampüs/fakülte (200+ üni) |
| **TOPLAM** | **23.876** | Hepsi RAG'da aktif |

### YÖK Atlas verisi

```yaml
yokatlas_total: 21602
  lisans: 12265 (SAY 5653 + EA 3987 + SÖZ 1948 + DİL 677)
  onlisans: 9337 (TYT)

universities:
  total: 227

universities_enriched_by_wikipedia_infobox:
  website: 219 / 227
  founded_year: 219 / 227
  logo_url: 218 / 227
  rector: 217 / 227
  address: 219 / 227
```

---

## 📁 Disk durumu

```
C:\Users\asker\Projelerim\UniSense\
├── backend/
│   ├── src/unisense/           (Clean Architecture)
│   ├── scripts/                (enrich_geo, probe_dgs)
│   ├── data/
│   │   ├── raw/yokatlas/       (lisans + önlisans + universities)
│   │   ├── raw/wikipedia/      (universities.json + infobox.json)
│   │   ├── processed/          (universities, departments, faculties, rankings, chunks)
│   │   └── embeddings/chromadb/ (23.876 chunk persistent)
│   ├── Dockerfile              (production — Render)
│   ├── render.yaml             (Render blueprint)
│   ├── .dockerignore
│   └── pyproject.toml
│
├── frontend/                   (React + Vite + Three.js + Firebase)
│   ├── src/pages/              (11 sayfa: + Privacy + Compare)
│   ├── src/components/three/
│   ├── public/                 (logo.png transparent + favicon)
│   ├── vercel.json             (production — Vercel)
│   └── vite.config.js          (manualChunks vendor split)
│
├── .github/workflows/
│   └── yearly-data-sync.yml    (yıllık otomatik scrape + chunks + embed)
│
├── docs/
│   ├── PROJECT_STATUS.md       (bu dosya)
│   ├── ROADMAP.md
│   ├── AI_CONTEXT.md
│   ├── AI_HANDOFF_PROMPT.md
│   └── DEPLOY.md               (production deploy rehberi)
│
├── firestore.rules             (Firebase Security Rules)
└── storage.rules
```

---

## 🤖 Aktif LLM

### Gemini API
- **Model:** `gemini-2.5-flash-lite` (default) + `gemini-flash-lite-latest` (quality)
- **Multi-key:** virgülle ayrılmış GEMINI_API_KEYS, round-robin + 429 fallback
- **Quota:** 15 RPM / 500 RPD (per-key, free tier)
- **Multi-turn:** chat history son 8 mesaj
- **Cache:** TTLCache (512 entry, 1 saat) — tekrar sorgu <300ms

> Önceki UniSenseLocal (Qwen3-4B fine-tuned, Ollama) v2.5'te kaldırıldı.

---

## 🔌 API Endpoints

```
GET  /api/v1/health                  # liveness + chunks_count
GET  /api/v1/models                  # aktif LLM'ler (sadece Gemini)
POST /api/v1/ask                     # multi-turn RAG + intent + cache
POST /api/v1/recommend               # safe/target/reach + filter + geo + yerleşme olasılığı
POST /api/v1/programs/lookup         # ÖSYM kodu → detay
POST /api/v1/programs/compare        # 2-5 program yan yana karşılaştır
GET  /api/v1/compass/taxonomy        # 358 lisans grup, 9 kategori
GET  /api/v1/compass/interests       # 150+ ilgi pill
POST /api/v1/compass/by-selection
POST /api/v1/compass/by-text
POST /api/v1/compass/by-axes
POST /api/v1/compass/by-interests
GET  /api/docs                       # Swagger UI (dev)
```

---

## 🎨 Frontend (11 sayfa)

| Route | Sayfa | Özellikler |
|---|---|---|
| `/` | **Splash** | 3D arkaplan (lazy) + Logo (sağ üst) |
| `/home` | **Home** | Hero + 4 stat |
| `/login` | **Login** | Firebase Auth (Google + Email) |
| `/profile` | **Profile** | 3 tab: Hesap, Şifre, YKS |
| `/pusula` | **Pusula** | 3 mod (Kart Seç, Soru Sor, 5 Soru) |
| `/search` | **Search** | RAG + multi-turn + collapsible kaynak |
| `/recommend` | **Recommend** | Pusula gating + Devlet/Vakıf + **Yerleşme % rozeti** + Tercihe Ekle |
| `/tercih` | **TercihList** | drag-drop + **Kişisel notlar** + **Karşılaştır** + Kodları Kopyala |
| `/compare` | **Compare** | 2-5 program yan yana, fark vurgu, mini SVG trend |
| `/hesap` | **Hesap Makinesi** | TYT/AYT/DGS + simulasyon |
| `/privacy` | **Privacy (KVKK)** | 10 bölüm gizlilik politikası |

---

## 🚀 v3.0 Yenilikleri (2026-05-17)

**Yeni özellikler:**
- ✅ **Bölüm Karşılaştırma** sayfası (`/compare?d=X,Y,Z`) — 2-5 program yan yana
- ✅ **Yerleşme olasılığı** (sigmoid hesabı, q1 ile yumuşatma) — Recommend kartlarında renkli yüzde rozet
- ✅ **Kişisel tercih notları** — TercihList'te her satıra expandable textarea (500 char, debounced save)
- ✅ **Production deploy hazır**: `backend/Dockerfile`, `backend/render.yaml`, `frontend/vercel.json`, `firestore.rules`, `storage.rules`, `docs/DEPLOY.md`

**v2.5'ten devam eden:**
- 23.876 chunk RAG (önlisans dahil)
- Wikipedia infobox enrich (website, logo, kuruluş yılı, rektör)
- KVKK / Privacy sayfası
- Embedding warm-up + Gemini cache + retrieval optimize + bundle split
- GitHub Actions yıllık cron (15 Ağustos)

---

## 🐛 Bilinen sorunlar / Kısıtlar

1. **DGS desteği yok** — yokatlas-py 0.6.0 desteklemiyor (ileride manuel scrape)
2. **Gemini quota** — günde 500/key (free tier), multi-key ile artırılır
3. **Geçmiş yıl history** — sadece 2024+2023 (rankings.json `history` alanında). 2022 ve öncesi yok.

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
| Firebase Auth | ✅ Google + Email |
| Firestore Security Rules | ✅ `firestore.rules` (sadece sahibi) |
| Firebase Storage Rules | ✅ `storage.rules` (avatar 2MB max) |
| API Key auth | ✅ Production'da `SECURITY_REQUIRE_API_KEY=true` |

---

## 📈 Performans metrikleri (v3.0)

```yaml
endpoint_latency_p50:
  /api/v1/health: 50ms
  /api/v1/ask (cold): ~4000ms     # lifespan warmup ile
  /api/v1/ask (cache hit): <300ms
  /api/v1/recommend: 200ms
  /api/v1/programs/compare: 100-300ms
  /api/v1/compass/*: 100ms

memory:
  - ChromaDB: ~50 MB
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

Production (Render):
```env
APP_ENV=production
SECURITY_REQUIRE_API_KEY=true
SECURITY_API_KEYS=<frontend-secret>
CORS_ALLOWED_ORIGINS=https://unisense.vercel.app
CHROMA_PERSIST_DIR=/data/chromadb
```

Frontend `.env.local`:
```env
VITE_API_URL=http://localhost:8002         # prod: https://unisense-api.onrender.com
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_STORAGE_BUCKET=...
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...
```

---

## 📋 Sırada

### Kısa vade
- Production deploy gerçekleştirme (rehber: [DEPLOY.md](DEPLOY.md))
- DGS manuel scrape (yokatlas-py 0.6.0 desteklemiyor)
- Geçmiş yıl history (2022, 2021) → 5 yıllık trend grafiği

### Orta vade
- LinkedIn alumni intelligence
- Email bildirimleri (tercih son günü)
- Maliyet hesabı (kira+yemek+ulaşım × 4 yıl)

### Uzun vade
- Mobile app (Expo)
- ÖSYM tercih öncesi hareketli demo
