# 🤖 AI ASSISTANT BRIEFING — UniSense Projesi

**Son güncelleme:** 2026-05-17
**Versiyon:** v3.0

> Bu doküman: AI asistanlara (Claude, Gemini, ChatGPT) UniSense'in **mevcut durumunu**,
> **kararlarımızı** ve **devam yöntemini** anlatmak için hazırlanmıştır.
> ROADMAP.md ile birlikte oku.

---

## 📋 META

```yaml
project: UniSense
description: Türkiye 2025 YKS Üniversite Tercih Asistanı (Pusula + Recommend + RAG + Hesap + Compare)
version: 3.0.0
status: Production-ready (deploy config hazır; manuel deploy bekleniyor)
language: Türkçe (primary)
deployment:
  frontend_dev: http://localhost:5174 (Vite)
  backend_dev:  http://localhost:8002 (FastAPI)
  prod_target:  Vercel (frontend) + Render (backend)

repos:
  local: C:\Users\asker\Projelerim\UniSense

stack:
  backend:
    - Python 3.11
    - FastAPI 0.115 + Pydantic v2 + slowapi + structlog + tenacity + cachetools
    - ChromaDB 0.4 (PersistentClient, collection: unisense)
    - sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2, 384 dim)
    - google-generativeai (Gemini 2.5 Flash Lite, multi-key + fallback chain)
    - yokatlas-py 0.6.0 + raw HTTP fallback
  frontend:
    - React 18 + Vite 5 (manualChunks vendor split + lazy 3D)
    - Three.js + @react-three/fiber + @react-three/drei
    - Framer Motion + lucide-react + Tailwind 3.4
    - @dnd-kit (sortable drag-drop)
    - Firebase Auth (Google + Email) + Firestore + Storage
  data_sources:
    - YÖK Atlas (yokatlas-py): 21.602 program (12.265 lisans + 9.337 önlisans)
    - 227 üniversite, 3.061 fakülte/MYO
    - Wikipedia TR: 200+ üniversite metni + 221 üni infobox (website/logo/kuruluş)
  llm_providers:
    - Gemini API (sadece, online, multi-key)
    # UniSenseLocal/Qwen v2.5'te kaldırıldı

architecture: Clean Architecture (Domain / Application / Infrastructure / API / Security / Core / CLI)
```

---

## 🎯 ANA HEDEF

> **Türkiye'deki 2025 YKS tercih dönemine yönelik, doğal Türkçe sorgularla
> üniversite/bölüm/sıralama bilgisi sunan ve kullanıcının ilgilerine göre tercih
> öneren AI destekli asistan.**

> "Ne istediğini bilmesen bile sana doğru bölümü buluruz."

Örnek sorgular ve akışlar:
- "300.000 sıralamayla devlet, denizi olan il, EA bölümler" → Recommend (geo + filter + yerleşme %)
- "Bilgisayar mühendisliği son 3 yıl trend nasıl?" → Trend service
- "İTÜ ne zaman kuruldu?" → Search RAG (Wikipedia infobox enrich)
- "Kart Seç → Yapay Zeka, Sağlık, Sanat" → Pusula (5-axis kişilik vektörü)
- "Net girdim → puanım kaç?" → Hesap Makinesi
- "Tercihim Boğaziçi ve İTÜ — yan yana karşılaştır" → /compare?d=...,...
- "Bu tercih için not ekle" → TercihList'te kişisel not

---

## 🏗 Mimari (Clean Architecture)

```
backend/src/unisense/
├── domain/                  # Saf iş kuralları
│   ├── enums.py             # ScoreType, FacultyKind, QueryIntent
│   ├── geo.py               # il→bölge, sahil/metropol/merkez
│   └── models/              # University, Program, Ranking, Recommendation, …
│
├── application/             # Use cases
│   ├── interfaces/
│   │   ├── llm_provider.py
│   │   └── vector_store.py
│   └── services/
│       ├── ask_service.py        # multi-turn + intent + Recommend hybrid + TTLCache
│       ├── recommendation_service.py  # safe/target/reach + filter + geo + YERLEŞME OLASILIĞI
│       ├── retrieval_service.py  # hibrit (keyword + vector) Türkçe-safe + collection reuse
│       ├── trend_service.py      # 3 yıllık taban+sıra tablosu
│       ├── compass_service.py    # 5-axis kişilik → bölüm matching
│       ├── compare_service.py    # YENİ v3 — 2-5 program karşılaştırma
│       ├── compass_taxonomy.py
│       └── compass_interests.py
│
├── infrastructure/          # Dış sistemler
│   ├── llm/
│   │   └── gemini.py             # Multi-key + 2.5 Flash Lite + fallback chain
│   ├── vector_store/chroma_store.py  # PersistentClient + warmup()
│   └── scrapers/
│       ├── yokatlas_scraper.py
│       ├── yokatlas_extra_scraper.py
│       ├── transform_yokatlas.py
│       ├── wikipedia_uni_scraper.py
│       ├── wikipedia_infobox_scraper.py    # YENİ v2.5 — infobox parse
│       └── enrich_universities.py          # YENİ v2.5 — universities.json merge
│
├── api/v1/
│   ├── routes.py            # /ask /recommend /health /models /programs/{lookup,compare} /compass/*
│   ├── schemas.py
│   └── dependencies.py
│
├── security/                # auth, sanitizer, audit_log
├── core/                    # config (Pydantic Settings), logging (structlog), di
│                            # main.py: lifespan ile embedding WARMUP
└── cli/build_chunks.py
```

---

## 🤖 LLM Stratejisi (v3)

### Sadece Gemini API
- **Model:** `gemini-2.5-flash-lite` (default) + `gemini-flash-lite-latest` (quality)
- **Multi-key:** virgülle ayrılmış `GEMINI_API_KEYS`, round-robin + 429 fallback
- **Quota:** 15 RPM / 500 RPD (per-key, free tier)
- **Multi-turn:** chat history son 8 mesaj
- **Cache:** TTLCache (512 entry, 1 saat) — tekrar sorgularda <300ms

### Cevap akışı (`/api/v1/ask`)
```
User query + history (son 4)
    ↓
Cache key (sha256) — hit ise döndür
    ↓
Sanitize (input_sanitizer)
    ↓
Audit log
    ↓
Intent router: sıra/puan/coğrafi pattern detect?
    ├── EVET → Recommend hybrid context (üst 5 öneri RAG'a inject)
    └── HAYIR → Saf RAG context (ChromaDB top-K=12 hibrit)
    ↓
LLM: Gemini multi-key (key rotation, fallback chain)
    ↓
Response cache'e yaz + döndür: {answer, sources, latency_ms}
```

---

## 📊 Veri

### Kaynaklar
- **YÖK Atlas (yokatlas-py 0.6.0)**: 21.602 program
- **Wikipedia TR + Infobox**: 222 üni metin + 221 üni infobox (website/logo/kuruluş/rektör/adres)
- **Trend (3 yıl):** rankings.json `history` alanı (2024, 2023 dahil)
- **Coğrafi:** 28 sahil ili, 30 metropol, 31 merkez ilçe

### ChromaDB
- **23.876 chunk** (12.265 lisans + 9.337 önlisans + 227 üni özet + 2.047 wiki)
- Embedding: `paraphrase-multilingual-MiniLM-L12-v2` (384 dim)
- Distance: L2 (hnsw)
- Collection: `unisense`

### Hibrit Retrieval
1. Keyword (Türkçe-safe `_tr_lower`/`_tr_upper`) — exact match
2. Vector (semantic) — top_k=12
3. Mevcut collection reuse (v2.5 optimization)

---

## 🔌 API Endpoints (`/api/v1`)

| Method | Path | İş |
|---|---|---|
| GET | `/health` | liveness + chunks_count |
| GET | `/models` | sadece Gemini |
| POST | `/ask` | RAG + multi-turn + cache |
| POST | `/recommend` | safe/target/reach + filter + geo + **yerleşme olasılığı** |
| POST | `/programs/lookup` | ÖSYM kodu → detay |
| POST | `/programs/compare` | **YENİ v3** — 2-5 program yan yana |
| GET | `/compass/taxonomy` | 358 grup, 9 kategori |
| GET | `/compass/interests` | 150+ ilgi pill |
| POST | `/compass/by-selection` | seçim → bölüm |
| POST | `/compass/by-text` | metin → bölüm |
| POST | `/compass/by-axes` | 5-soru vektör → bölüm |
| POST | `/compass/by-interests` | pill set → bölüm |

---

## 🌐 Frontend (React + Vite)

### Sayfalar (11)
| Route | Sayfa | Özellikler |
|---|---|---|
| `/` | Splash | 3D arkaplan (lazy) + Logo + Tema |
| `/home` | Home | Hero + 4 stat |
| `/login` | Login | Firebase Auth |
| `/profile` | Profile | 3 tab: Hesap, Şifre, YKS |
| `/pusula` | Pusula | Kart Seç / Soru Sor / 5 Soru |
| `/search` | Search | RAG + multi-turn + collapsible kaynak |
| `/recommend` | Recommend | Pusula gating + Devlet/Vakıf + **Yerleşme % rozeti** + Tercihe Ekle |
| `/tercih` | TercihList | drag-drop + **Kişisel notlar** + **Karşılaştır** + Kopyala |
| `/compare` | **Compare (YENİ v3)** | 2-5 program yan yana, EN İYİ/EN ZAYIF vurgu, mini SVG trend |
| `/hesap` | Hesap Makinesi | TYT/AYT/DGS + simulasyon |
| `/privacy` | **Privacy (YENİ v2.5)** | 10 bölüm KVKK |

### Tasarım sistemi
- 3D arkaplan (Three.js + R3F + Drei): KnowledgeSphere, OrbitingNode, ParticleField
- Tailwind cyber palet: brand mavi, accent mor, cyan/pink/violet
- Glassmorphism: `.glass`, `.card`, `.btn-primary`, `.input-glass`
- Tema: dark/light (3D arkaplan korunur)
- Logo: transparent PNG (RGB→RGBA)
- **v2.5 bundle:** Vite manualChunks (react/three/firebase/ui vendor split) + Splash 3D lazy

---

## 📁 Önemli dosyalar

| Yol | Ne |
|---|---|
| `backend/src/unisense/main.py` | FastAPI app factory + **lifespan warmup** |
| `backend/src/unisense/api/v1/routes.py` | Tüm endpointler |
| `backend/src/unisense/application/services/ask_service.py` | Multi-turn + intent + **TTLCache** |
| `backend/src/unisense/application/services/recommendation_service.py` | Safe/target/reach + **placement_probability** |
| `backend/src/unisense/application/services/compare_service.py` | **YENİ v3** — 2-5 program karşılaştırma |
| `backend/src/unisense/application/services/trend_service.py` | 3 yıllık trend |
| `backend/src/unisense/application/services/compass_service.py` | 5-axis bölüm matching |
| `backend/src/unisense/infrastructure/llm/gemini.py` | Multi-key + fallback chain |
| `backend/src/unisense/infrastructure/vector_store/chroma_store.py` | ChromaDB + **warmup()** |
| `backend/src/unisense/infrastructure/scrapers/wikipedia_infobox_scraper.py` | **YENİ v2.5** infobox parse |
| `backend/src/unisense/infrastructure/scrapers/enrich_universities.py` | **YENİ v2.5** infobox merge |
| `backend/Dockerfile` | **YENİ v3** production container |
| `backend/render.yaml` | **YENİ v3** Render blueprint |
| `frontend/src/pages/{Splash,Login,Profile,Pusula,Search,Recommend,TercihList,Hesap,Privacy,Compare}.jsx` | Sayfalar |
| `frontend/src/components/Logo.jsx` | Transparent logo |
| `frontend/src/firebase.js` | Firebase helper + **updateTercihNote** |
| `frontend/vercel.json` | **YENİ v3** Vercel SPA config |
| `firestore.rules` | **YENİ v3** Security Rules |
| `storage.rules` | **YENİ v3** Storage Rules |
| `docs/DEPLOY.md` | **YENİ v3** deploy rehberi |
| `.github/workflows/yearly-data-sync.yml` | Yıllık otomatik scrape (15 Ağustos) |

---

## 🚀 Local Çalıştırma

```bash
# Backend
cd backend
pip install -e ".[dev]"
cp .env.example .env  # GEMINI_API_KEYS ekle
uvicorn unisense.main:app --host 0.0.0.0 --port 8002 --reload

# Frontend
cd frontend
npm install
npm run dev   # http://localhost:5174
```

`.env` zorunlu:
- `GEMINI_API_KEYS=AIza...key1,AIza...key2`

---

## ⚠️ DOKUNULMAMASI GEREKENLER

```yaml
do_not_change:
  - api_v1_paths: "/api/v1/ask, /recommend, /health, /models, /compass/*, /programs/lookup, /programs/compare — frontend kullanıyor"
  - chroma_collection_name: "unisense — değişirse data uçar"
  - embedding_model: "paraphrase-multilingual-MiniLM-L12-v2 — chunks bu boyutla embed edildi"
  - .env: ".env asla commit edilmez, .env.example'a sızdırma"
  - logo.png: "frontend/public/logo.png — transparent RGBA"

watch_out:
  - "Türkçe karakter: Python default lower/upper bozuk, _tr_lower / _tr_upper kullan"
  - "yokatlas-py KKTC bug: raw HTTP (yokatlas_py.http_client) ile bypass"
  - "retrieval keyword: 'İSKENDERUN' için _tr_lower zorunlu"
  - "ChromaVectorStore.collection property mevcut — yeni client açma"
  - "main.py lifespan startup'ta warmup çalışır — production'da ilk istek hızlı"
  - "ask_service TTLCache key: query+history+model_pref hash; cache hit'te LLM'ye gitme"
  - "DGS endpoint: yokatlas-py 0.6.0'da yok — manuel scrape ileride"
```

---

## 🐛 Bilinen kısıtlar

1. **DGS desteği yok** — yokatlas-py 0.6.0 desteklemiyor
2. **Gemini quota** — günde 500/key (free tier), birden fazla key ile çoğalt
3. **Geçmiş yıl history** — 2024+2023 var, 2022 ve öncesi yok

---

## 📊 Mevcut metrikler

- **Backend**: 21.602 program, 3.061 fakülte, 227 üni, **23.876 RAG chunk**
- **Wikipedia infobox enrich**: 219/227 üni (website + logo + kuruluş)
- **Frontend**: 11 sayfa
- **Auth**: Firebase Auth (Google + Email) + Firestore + Storage
- **API endpoints**: 12

---

## 🔄 v3.0 Migration Notes

✅ Kullan:
- Tek-LLM (sadece Gemini) — `MultiLLMRouter` artık YOK
- `placement_probability` her Recommendation'da (sigmoid + q1 yumuşatma)
- `/api/v1/programs/compare` 2-5 ÖSYM kodu
- `updateTercihNote(uid, code, note)` Firestore note alanı
- `lifespan` warmup main.py'da
- `TTLCache` ask_service'te

❌ Kullanma:
- `MultiLLMRouter` / `QwenProvider` (silindi)
- `model_preference="unisense-local"` (artık sadece "gemini")
- `backend/data/training/` (Qwen dataset silindi)
- `unisense-tr-gguf/` (GGUF silindi)

---

## 🔄 SONRAKI SESSION İÇİN

Yeni AI asistana proje anlatmak için:
1. `docs/AI_CONTEXT.md` (bu dosya) okutarak başla
2. `docs/ROADMAP.md` ile yol haritasını gör
3. `docs/PROJECT_STATUS.md` ile anlık durum
4. `docs/AI_HANDOFF_PROMPT.md` ile hazır prompt al
5. `docs/DEPLOY.md` production deploy için
6. `git log --oneline -20`
