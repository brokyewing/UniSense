# 🤖 AI ASSISTANT BRIEFING — UniSense Projesi

**Son güncelleme:** 2026-05-07
**Versiyon:** v2.0

> Bu doküman: AI asistanlara (Claude, Gemini, ChatGPT) UniSense'in **mevcut durumunu**,
> **kararlarımızı** ve **devam yöntemini** anlatmak için hazırlanmıştır.
> ROADMAP.md ile birlikte oku.

---

## 📋 META

```yaml
project: UniSense
description: Türkiye 2025 YKS Üniversite Tercih Asistanı (Pusula + Recommend + RAG + Hesap Makinesi)
version: 2.0.0
status: MVP+ tamamen çalışıyor (v2 Pusula + Hesap + Önlisans + Trend + Multi-LLM)
language: Türkçe (primary)
deployment:
  frontend_dev: http://localhost:5173 (Vite)
  backend_dev:  http://localhost:8002 (FastAPI)
  prod: planlanan (Vercel + Render/Cloudflare Tunnel)

repos:
  local: C:\Users\asker\Projelerim\UniSense

stack:
  backend:
    - Python 3.11
    - FastAPI 0.115 + Pydantic v2 + slowapi + structlog + tenacity
    - ChromaDB 0.4 (PersistentClient, collection: unisense)
    - sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2, 384 dim)
    - google-generativeai (Gemini 3.1 Flash Lite preview, multi-key + fallback chain)
    - yokatlas-py 0.6.0 + raw HTTP fallback (KKTC + önlisans)
    - Ollama HTTP client (UniSenseLocal — opsiyonel)
  frontend:
    - React 18 + Vite 5
    - Three.js + @react-three/fiber + @react-three/drei
    - Framer Motion + lucide-react + Tailwind 3.4
    - @dnd-kit (sortable drag-drop)
    - Firebase Auth (Google + Email) + Firestore
  data_sources:
    - YÖK Atlas (yokatlas-py): 21.602 program (12.265 lisans + 9.337 önlisans)
    - 227 üniversite, 3.061 fakülte/MYO
    - Wikipedia TR: 200+ üniversite metni
    - Manuel: 28 sahil ili, 30 metropol, 31 il merkez ilçeleri
  llm_providers:
    - Gemini API (default, online, multi-key)
    - UniSenseLocal (Ollama Qwen3-4B fine-tuned — dataset hazır, training pending)

architecture: Clean Architecture (Domain / Application / Infrastructure / API / Security / Core / CLI)
```

---

## 🎯 ANA HEDEF

> **Türkiye'deki 2025 YKS tercih dönemine yönelik, doğal Türkçe sorgularla
> üniversite/bölüm/sıralama bilgisi sunan ve kullanıcının ilgilerine göre tercih
> öneren AI destekli asistan.**

> "Ne istediğini bilmesen bile sana doğru bölümü buluruz."

Örnek sorgular ve akışlar:
- "300.000 sıralamayla devlet, denizi olan il, EA bölümler" → Recommend (geo + filter)
- "Bilgisayar mühendisliği son 3 yıl trend nasıl?" → Trend service
- "İTÜ Bilgisayar tercih şartları" → Search RAG (ÖSYM kosul kodları)
- "Kart Seç → Yapay Zeka, Sağlık, Sanat" → Pusula (5-axis kişilik vektörü)
- "Net girdim → puanım kaç?" → Hesap Makinesi (TYT/AYT-SAY/EA/SÖZ/DİL/DGS)
- "ÖSYM tercih kodlarını sırala + kopyala" → TercihList (drag-drop + Kodları Kopyala)

---

## 🏗 Mimari (Clean Architecture)

```
backend/src/unisense/
├── domain/                  # Saf iş kuralları
│   ├── enums.py             # ScoreType, FacultyKind, QueryIntent
│   ├── geo.py               # il→bölge, sahil/metropol/merkez
│   └── models/              # University, Program, Ranking, Recommendation, Compass…
│
├── application/             # Use cases
│   ├── interfaces/
│   │   ├── llm_provider.py       # generate(query, context, **kwargs)
│   │   └── vector_store.py
│   └── services/
│       ├── ask_service.py        # multi-turn + intent routing + Recommend hybrid
│       ├── recommendation_service.py  # safe/target/reach + filter + geo
│       ├── retrieval_service.py  # hibrit (keyword + vector) Türkçe-safe
│       ├── trend_service.py      # 3 yıllık taban+sıra tablosu
│       ├── compass_service.py    # 5-axis kişilik → bölüm matching
│       ├── compass_taxonomy.py   # 358 lisans grup, 9 kategori
│       └── compass_interests.py  # 150+ ilgi pill
│
├── infrastructure/          # Dış sistemler
│   ├── llm/
│   │   ├── gemini.py             # Multi-key + 3.1 Flash Lite + fallback chain
│   │   ├── qwen.py               # Ollama HTTP client (UniSenseLocal)
│   │   └── multi_router.py       # Gemini ↔ Local routing
│   ├── vector_store/chroma_store.py
│   └── scrapers/
│       ├── yokatlas_scraper.py        # Lisans (puanTuru=SAY/EA/SÖZ/DİL)
│       ├── yokatlas_extra_scraper.py  # Önlisans (puanTuru=TYT)
│       ├── transform_yokatlas.py      # raw → models + history + geo enrich
│       └── wikipedia_uni_scraper.py
│
├── api/v1/
│   ├── routes.py            # /ask /recommend /health /models /programs/lookup /compass/*
│   ├── schemas.py
│   └── dependencies.py
│
├── security/                # auth, sanitizer, audit_log
├── core/                    # config (Pydantic Settings), logging (structlog), di
└── cli/build_chunks.py
```

---

## 🤖 LLM Stratejisi (v2)

### Default: Gemini API
- **Model:** `gemini-3.1-flash-lite-preview` (default), fallback chain otomatik
- **Multi-key:** virgülle ayrılmış `GEMINI_API_KEYS`, round-robin + 429 fallback
- **Quota:** 15 RPM / 500 RPD (per-key, free tier)
- **Multi-turn:** chat history son 8 mesaj `contents` formatında gider

### Opsiyonel: UniSenseLocal (Ollama Qwen3-4B fine-tuned)
- **Dataset:** 58.585 Q/A çift, 12 kategori (Alpaca format, 16.5 MB JSONL)
- **Notebook:** `backend/data/training/unisense-egitimi-kaggle.ipynb` (T4 LoRA)
- **Provider:** `infrastructure/llm/qwen.py` (localhost:11434)
- **Router:** `multi_router.py` — frontend'den `model_preference` ile seçilir
- **Status:** Training Kaggle'a yüklendi, eğitim bekleniyor

### Cevap akışı (`/api/v1/ask`)
```
User query + history (son 4)
    ↓
Sanitize (input_sanitizer)
    ↓
Audit log
    ↓
Intent router: sıra/puan/coğrafi pattern detect?
    ├── EVET → Recommend hybrid context (üst 5 öneri RAG'a inject edilir)
    └── HAYIR → Saf RAG context (ChromaDB top-K=12 hibrit)
    ↓
LLM router (Gemini default | UniSenseLocal opsiyonel)
    ↓
Response: {answer, sources, model_used, latency_ms}
```

---

## 📊 Veri

### Kaynaklar
- **YÖK Atlas (yokatlas-py 0.6.0)**:
  - Lisans: 12.265 (puanTuru=SAY/EA/SÖZ/DİL/TYT)
  - Önlisans: 9.337 (puanTuru=TYT)
  - 227 üniversite (DEVLET 128 + VAKIF 74 + KKTC 16 + diğer)
  - 3.061 fakülte/MYO
- **Trend verisi (3 yıl):** rankings.json `history` alanında 2024+2023 (yokatlas API'sinde gömülü `minPuan1/2`, `basariSirasi1/2`)
- **Coğrafi metadata:** 28 sahil ili (deniz adları + kıyı km), 30 metropol, 31 ilin merkez ilçeleri
- **Akademik kadro:** prof, doçent, dr.üyesi, ar.gör., öğr.gör. sayıları
- **Akreditasyon, koşul kodları, burs/ücret, eğitim dili** alanları

### ChromaDB
- Embedding: `paraphrase-multilingual-MiniLM-L12-v2` (384 dim)
- Distance: cosine
- Collection: `unisense`
- Persist: `backend/data/embeddings/chromadb/`
- Chunk: 14.539 (önlisans rebuild gerek)

### Hibrit Retrieval
1. Embedding similarity (semantic)
2. Keyword detection (Türkçe-safe `_tr_lower`/`_tr_upper`)
3. University name detection (SHORT_NAMES tablo)
4. top_k=12 default

---

## 🔌 API Endpoints (`/api/v1`)

| Method | Path | İş |
|---|---|---|
| GET | `/health` | liveness + chunks_count |
| GET | `/models` | hangi LLM'ler aktif (Gemini, UniSenseLocal) |
| POST | `/ask` | RAG + multi-turn + intent routing + LLM seçimi |
| POST | `/recommend` | safe/target/reach kovaları + filtre + geo |
| POST | `/programs/lookup` | ÖSYM kodu / department_group_name → program detay |
| GET | `/compass/taxonomy` | 358 lisans grup + 9 kategori |
| GET | `/compass/interests` | 150+ ilgi pill |
| POST | `/compass/by-selection` | seçili kategori → bölüm grubu |
| POST | `/compass/by-text` | metin → 5 boyutlu vektör → bölüm grubu |
| POST | `/compass/by-axes` | açık vektör → bölüm grubu |
| POST | `/compass/by-interests` | ilgi pill set → bölüm grubu |

---

## 🌐 Frontend (React + Vite — `frontend/`)

### Sayfalar (9 sayfa)

| Route | Sayfa | Özellikler |
|---|---|---|
| `/` | **Splash** | 3D arkaplan + Logo (sağ üst) + Theme toggle + "Başla" |
| `/home` | **Home** | Hero + 4 stat (227 üni, 21.6k program, 3.1k fakülte, 7 bölge) + örnek sorgular |
| `/login` | **Login** | Firebase Auth (Google + Email) + Logo |
| `/profile` | **Profile** | 3 tab: Hesap (avatar) + Şifre + YKS (puan/sıra/şehir/üni türü/preferred interests) |
| `/pusula` | **Pusula** | 3 mod: **Kart Seç** (ilgi pill) / **Soru Sor** (Search yönlendir) / **5 Soru** |
| `/search` | **Search** | RAG chat + multi-turn (son 4) + LLM seçici (Gemini/UniSenseLocal) + collapsible kaynaklar |
| `/recommend` | **Recommend** | Pusula gating + Devlet/Vakıf toggle + +Tercihe Ekle/Çıkar + safe/target/reach |
| `/tercih` | **TercihList** | Drag-drop (@dnd-kit) + ↑↓ + ÖSYM kod + Sıraya Göre Diz + Kodları Kopyala + Kod ile Ekle |
| `/hesap` | **Hesap Makinesi** | TYT/AYT-SAY/EA/SÖZ/DİL/DGS + ders bazlı katsayı + OBP 100'lük (DGS 4'lük) + simulasyon |

### UX akışı (uçtan uca)
```
Splash → Login → Pusula (ilgi seç) → Recommend (puan + tercih) → TercihList (sırala + ÖSYM kod kopyala)
                Hesap (net gir → puan)  ↗
                Search (sohbet RAG)     ↗
```

### Tasarım sistemi
- 3D arkaplan (Three.js + R3F + Drei): KnowledgeSphere, OrbitingNode, ParticleField
- Tailwind cyber palet: brand mavi, accent mor, cyan/pink/violet
- Glassmorphism: `.glass`, `.card`, `.btn-primary`, `.input-glass`
- Tema: dark/light (3D arkaplan korunur)
- Logo: yeni transparent PNG (RGB→RGBA dönüştürüldü), favicon güncel

---

## 📁 Önemli dosyalar

| Yol | Ne |
|---|---|
| `backend/src/unisense/main.py` | FastAPI app factory |
| `backend/src/unisense/api/v1/routes.py` | Tüm endpointler |
| `backend/src/unisense/application/services/ask_service.py` | Multi-turn + intent + Recommend hybrid |
| `backend/src/unisense/application/services/recommendation_service.py` | Safe/target/reach + filter + geo |
| `backend/src/unisense/application/services/trend_service.py` | 3 yıllık trend |
| `backend/src/unisense/application/services/compass_service.py` | 5-axis bölüm matching |
| `backend/src/unisense/infrastructure/llm/gemini.py` | Multi-key + fallback chain |
| `backend/src/unisense/infrastructure/llm/qwen.py` | Ollama UniSenseLocal |
| `backend/src/unisense/infrastructure/llm/multi_router.py` | LLM router |
| `backend/src/unisense/infrastructure/scrapers/yokatlas_extra_scraper.py` | Önlisans (TYT) scraper |
| `backend/src/unisense/infrastructure/scrapers/transform_yokatlas.py` | Lisans+önlisans+history+geo birleştir |
| `backend/scripts/build_unisense_dataset.py` | 58.585 Q/A dataset üretici |
| `backend/data/training/unisense_dataset.jsonl` | Qwen training dataset (16.5 MB) |
| `backend/data/training/unisense-egitimi-kaggle.ipynb` | Kaggle Qwen3-4B LoRA notebook |
| `frontend/src/pages/{Splash,Login,Profile,Pusula,Search,Recommend,TercihList,Hesap}.jsx` | Sayfalar |
| `frontend/src/components/Logo.jsx` | Transparent logo + GraduationCap fallback |
| `frontend/src/lib/firestore.js` | Firestore (sessions, tercih, profile, queries) |

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
npm run dev   # http://localhost:5173

# (Opsiyonel) UniSenseLocal Ollama
ollama serve
ollama pull qwen3:4b   # veya fine-tuned model
```

`.env` zorunlu:
- `GEMINI_API_KEYS=AIza...key1,AIza...key2`
- `CHROMA_PERSIST_DIR=./data/embeddings/chromadb`

`.env` opsiyonel:
- `OLLAMA_URL=http://localhost:11434` (UniSenseLocal için)

---

## ⚠️ DOKUNULMAMASI GEREKENLER

```yaml
do_not_change:
  - api_v1_paths: "/api/v1/ask, /api/v1/recommend, /api/v1/health — frontend kullanıyor"
  - chroma_collection_name: "unisense — değişirse data uçar"
  - embedding_model: "paraphrase-multilingual-MiniLM-L12-v2 — chunks bu boyutla embed edildi"
  - .env: ".env asla commit edilmez, .env.example'a sızdırma"
  - logo.png: "frontend/public/logo.png — transparent RGBA, RGB'ye çevirme"

watch_out:
  - "Türkçe karakter: Python default lower/upper bozuk, _tr_lower / _tr_upper kullan"
  - "yokatlas-py KKTC bug: raw HTTP (yokatlas_py.http_client) ile bypass"
  - "retrieval keyword detection: 'İSKENDERUN' → '.lower()' yerine '_tr_lower()' zorunlu"
  - "AskService LLM hasattr check: hasattr(self._llm, '_providers') gerekli (multi-router)"
  - "DGS endpoint: yokatlas-py 0.6.0'da yok — manuel scrape ileride"
```

---

## 🐛 Bilinen kısıtlar

1. **DGS desteği yok** — yokatlas-py 0.6.0 desteklemiyor, HTML scrape karmaşık
2. **ChromaDB önlisans rebuild gerek** — 9.337 önlisans henüz RAG'a eklenmedi
3. **Gemini quota** — günde 500/key (free tier), birden fazla key ile çoğalt
4. **UniSenseLocal eğitimi pending** — dataset hazır, Kaggle T4 ile ~6-8 saat
5. **Avesis akademisyen detay** — her üni farklı subdomain, çözüm: link gösterimi

---

## 📊 Mevcut metrikler

- **Backend**: 21.602 program, 3.061 fakülte, 227 üni, 14.539 RAG chunk
- **Dataset (Qwen)**: 58.585 Q/A (16.5 MB JSONL, ~5.7M token)
- **Frontend sayfa**: 9 (Splash, Home, Login, Profile, Pusula, Search, Recommend, TercihList, Hesap)
- **Auth**: Firebase Auth (Google + Email) + Firestore
- **API endpoints**: 12 (`/ask`, `/recommend`, `/health`, `/models`, `/programs/lookup`, 7×`/compass/*`)

---

## 🔄 v2 Migration Notes

Yeni AI yardım yazıyorsa **eski referansları silmemeli**:

❌ Kullanma:
- `model_choice="qwen"` (artık `model_preference="UniSenseLocal"`)
- Tek-LLM AskService (multi-router var)
- Eski `/api/v1/ask` body (artık `history[]` opsiyonel)
- Eski Pusula bölüm pill'leri (artık ilgi pill, 5-axis vektör)

✅ Kullan:
- `MultiLLMRouter` (`infrastructure/llm/multi_router.py`)
- `model_preference: "Gemini" | "UniSenseLocal"`
- `history: [{role: "user"|"assistant", content: "..."}]` (son 4)
- Compass services: `taxonomy`, `interests`, `compass_service`
- `Hesap` formülleri: TYT 3.3/3.4, AYT-SAY 3.0/2.85/3.07, OBP×0.12, DGS AOBP

---

## 🔄 SONRAKI SESSION İÇİN

Yeni AI asistana proje anlatmak için:
1. `docs/AI_CONTEXT.md` (bu dosya) okutarak başla
2. `docs/ROADMAP.md` ile yol haritasını gör
3. `docs/PROJECT_STATUS.md` ile anlık durum
4. `docs/AI_HANDOFF_PROMPT.md` ile hazır prompt al
5. `git log --oneline -20` (varsa)
