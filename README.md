# UniSense

> Türkiye üniversite tercih sürecini akıllı bir asistana dönüştüren açık kaynak proje.
> RAG (Retrieval-Augmented Generation) tabanlı, YÖK Atlas / ÖSYM / URAP verileriyle beslenen,
> öğrencinin puanına ve ilgi alanına göre **gerçek sayılarla** öneri üretir.

---

## İçindekiler

- [Neler yapar?](#neler-yapar)
- [Mimari](#mimari)
- [Teknoloji Yığını](#teknoloji-yığını)
- [Kurulum](#kurulum)
  - [1. Repo'yu klonla](#1-repoyu-klonla)
  - [2. Backend (FastAPI + ChromaDB)](#2-backend-fastapi--chromadb)
  - [3. Frontend (React + Vite + Firebase)](#3-frontend-react--vite--firebase)
- [Veri Hazırlama](#veri-hazırlama)
- [API Uç Noktaları](#api-uç-noktaları)
- [Deploy](#deploy)
- [Güvenlik Notları](#güvenlik-notları)
- [Klasör Yapısı](#klasör-yapısı)
- [Lisans](#lisans)

---

## Neler yapar?

- **Sohbet (Ask)** — "İstanbul'da 80 bin sıralamayla hangi bilgisayar mühendisliği bölümlerine girebilirim?" gibi doğal dil sorgularına RAG ile cevap verir; her programın **ÖSYM tercih kodunu** (örn. `[203910363]`) cevabın içine ekler, frontend tek tıkla tercihe atar.
- **Pusula (Compass)** — İlgi alanı + güçlü dersler + şehir tercihi gibi eksenler üzerinden öğrenciye uygun **bölüm önerisi** üretir.
- **Tercih Listesi** — 24 sıralık tercihe ekleme, sürükle-bırak ile yeniden sıralama, otomatik backfill (eksik puan/sıra/kontenjan alanları arka planda doldurulur).
- **Sohbet Geçmişi** — Kişi başı 5 oturumu Firestore'da saklar, FIFO ile en eskiyi düşürür.
- **Akademisyen Linkleri** — "Hoca/akademisyen" sorularında YÖK Akademik Arama linkini otomatik üretir.

---

## Mimari

```
                 ┌─────────────────────────────────────────────┐
                 │                  Frontend                    │
                 │  React 18 + Vite + Tailwind + Three.js       │
                 │  Firebase Auth (Google + Email)              │
                 │  Firestore (kullanıcı / tercih / sohbet)     │
                 └────────────────────┬────────────────────────┘
                                      │  REST (JSON)
                                      ▼
                 ┌─────────────────────────────────────────────┐
                 │              Backend  (FastAPI)              │
                 │                                              │
                 │   ┌───────────┐    ┌────────────────────┐    │
                 │   │ Ask       │───▶│ RetrievalService   │    │
                 │   │ Compass   │    │ (Top-K + filtre)   │    │
                 │   │ Recommend │    └─────────┬──────────┘    │
                 │   └─────┬─────┘              │               │
                 │         │                    ▼               │
                 │         │           ┌─────────────────┐     │
                 │         │           │ ChromaDB        │     │
                 │         │           │ (vektör store)  │     │
                 │         │           └─────────────────┘     │
                 │         ▼                                    │
                 │   ┌──────────────────────────┐               │
                 │   │ Gemini Provider          │               │
                 │   │ (multi-key + auto-rotate)│               │
                 │   └──────────────────────────┘               │
                 └─────────────────────────────────────────────┘
                                      ▲
                                      │
                 ┌─────────────────────────────────────────────┐
                 │            Veri Boru Hattı (offline)         │
                 │   Scrapers → JSON → chunks.json → embed →    │
                 │   ChromaDB persistent store                  │
                 │                                              │
                 │   Kaynaklar: YÖK Atlas, ÖSYM, URAP,          │
                 │   AVESİS, Wikipedia                          │
                 └─────────────────────────────────────────────┘
```

---

## Teknoloji Yığını

**Backend**
- Python 3.11+
- FastAPI · Pydantic v2 · Uvicorn
- ChromaDB (persistent vector store)
- sentence-transformers (`paraphrase-multilingual-MiniLM-L12-v2`, 384 dim)
- Google Generative AI (Gemini 2.5 Flash / Flash-Lite)
- structlog · slowapi · tenacity

**Frontend**
- React 18 + Vite 5
- Tailwind CSS 3 + Framer Motion
- React Three Fiber (3B arka plan sahneleri)
- Firebase Web SDK 11 (Auth + Firestore + Storage)
- @dnd-kit (sürükle-bırak tercih sıralama)

**Veri**
- YÖK Atlas (lisans + önlisans programları, sıralamalar, kontenjanlar)
- ÖSYM (puan türleri, tercih kodları)
- URAP (akademik sıralama)
- AVESİS (akademisyen verileri)
- Wikipedia (üniversite genel bilgileri)

---

## Kurulum

### 1. Repo'yu klonla

```bash
git clone https://github.com/<KULLANICI>/UniSense.git
cd UniSense
```

### 2. Backend (FastAPI + ChromaDB)

> Önkoşul: Python 3.11 veya üstü.

```bash
cd backend

# Sanal ortam
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# Bağımlılıklar (editable install)
pip install -e .
# veya minimal:
pip install -r requirements.txt

# .env dosyasını oluştur
copy .env.example .env       # Windows
# cp .env.example .env       # macOS / Linux
```

`.env` dosyasını aç ve **kendi Gemini API key'in** ile doldur (https://aistudio.google.com/apikey üzerinden ücretsiz alabilirsin):

```env
GEMINI_API_KEYS=ger_cek_key_1,ger_cek_key_2     # birden fazla key → quota dolunca otomatik geçiş
GEMINI_API_KEY=ger_cek_key                       # tek key kullanacaksan
```

ChromaDB'yi doldurmak için (veri zaten repoda hazır):

```bash
# chunks.json'dan vektör store'u kur
python -m unisense.cli.embed
```

Backend'i çalıştır:

```bash
uvicorn unisense.main:app --host 0.0.0.0 --port 8002 --reload
# veya:
unisense-api
```

API döküman: http://localhost:8002/api/docs

### 3. Frontend (React + Vite + Firebase)

> Önkoşul: Node.js 18+

```bash
cd ../frontend
npm install

# .env dosyasını oluştur
copy .env.example .env.local      # Windows
# cp .env.example .env.local      # macOS / Linux
```

`.env.local` dosyasını **kendi Firebase projenden** doldur:

1. https://console.firebase.google.com → Yeni proje oluştur
2. **Authentication** → Sign-in method → Google + Email/Password aktif et
3. **Firestore Database** → Production mode'da oluştur
4. **Storage** → Bucket oluştur
5. Project Settings → General → Your apps → Web app → Config'i kopyala

```env
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=projem.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=projem
VITE_FIREBASE_STORAGE_BUCKET=projem.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...
VITE_FIREBASE_MEASUREMENT_ID=G-...

VITE_API_URL=http://localhost:8002
```

Çalıştır:

```bash
npm run dev
```

http://localhost:5173 adresinde uygulama açılır.

---

## Veri Hazırlama

Tüm hazır veriler `backend/data/` altında commit'lidir. Sıfırdan çekmek istersen:

```bash
cd backend

# Scrapers (sırayla):
python -m unisense.infrastructure.scrapers.yokatlas_scraper
python -m unisense.infrastructure.scrapers.urap_scraper
python -m unisense.infrastructure.scrapers.wikipedia_uni_scraper
python -m unisense.infrastructure.scrapers.avesis_scraper

# Yokatlas raw → processed dönüşümü
python -m unisense.infrastructure.scrapers.transform_yokatlas

# Coğrafi zenginleştirme (şehir/bölge bilgisi)
python scripts/enrich_geo.py

# Chunks oluştur (RAG için)
python -m unisense.cli.build_chunks

# Embedding + ChromaDB
python -m unisense.cli.embed
```

> ⚠️ Scraper'lar dış sitelere istek atar; lütfen rate limit'lere saygı göster.

---

## API Uç Noktaları

Tümü `/api/v1` prefix'i altındadır.

| Metot | Path | Açıklama |
|---|---|---|
| `GET` | `/health` | Sağlık kontrolü + chunk sayısı |
| `GET` | `/models` | Mevcut LLM modellerini listele |
| `POST` | `/ask` | RAG sorgusu (cevap + kaynak chunk'lar) |
| `POST` | `/recommend` | Öğrenci profiline göre bölüm önerisi |
| `POST` | `/lookup` | Tercih kodlarına göre detay (sıra/taban/kontenjan) |
| `POST` | `/compass/text` | Pusula — serbest metin → eksen analizi |
| `POST` | `/compass/axes` | Pusula — eksen tabanlı öneri |
| `POST` | `/compass/interests` | Pusula — ilgi taksonomisi |
| `GET` | `/compass/taxonomy` | Pusula — eksen taksonomisi |
| `GET` | `/compass/interests-taxonomy` | Pusula — ilgi taksonomisi |

**Rate limit:** `/ask` için varsayılan **20 req/dk/IP** (`.env` içindeki `RATE_LIMIT_ASK`).

**Auth:** `.env` içinde `SECURITY_REQUIRE_API_KEY=true` yapılırsa `X-API-Key` header zorunlu olur (`SECURITY_API_KEYS=key1,key2,...`).

---

## Deploy

**Backend** — Hugging Face Spaces (Docker), Railway, Render, Fly.io ya da kendi VPS'in.
- ChromaDB persistent path için kalıcı disk gerekir.
- `APP_ENV=production` yap → API docs URL'leri kapanır.
- `CORS_ALLOWED_ORIGINS` ayarına frontend domain'ini ekle.

**Frontend** — Vercel ya da Netlify.
- Build komutu: `npm run build`
- Output: `dist/`
- Environment variables sayfasından tüm `VITE_FIREBASE_*` ve `VITE_API_URL` değerlerini gir.

---

## Güvenlik Notları

- `backend/.env` ve `frontend/.env.local` **git'e gitmez** (`.gitignore`'da). Sadece `.env.example` dosyaları commit'lidir.
- **Firebase Web API key public'tir** — Firebase güvenliği API key'in gizliliğine değil, **Firestore/Storage Security Rules**'a dayanır. Bu rules'ları mutlaka kullanıcı-bazlı yapılandır:

  ```
  match /users/{uid}/{document=**} {
    allow read, write: if request.auth != null && request.auth.uid == uid;
  }
  ```

- Üretimde **Firebase Console → Project Settings → API key restrictions** ile web key'i HTTP referrer kısıtlamasına al (`localhost`, prod domain'in).
- **Gemini API key'leri** sadece backend'de durur, frontend'e asla gönderilmez.

---

## Klasör Yapısı

```
UniSense/
├── backend/
│   ├── src/unisense/
│   │   ├── api/            # FastAPI router + middleware
│   │   ├── application/    # Use case servisleri (Ask, Compass, Recommend...)
│   │   ├── core/           # Config, DI, logging
│   │   ├── domain/         # Domain modelleri + enums + exceptions
│   │   ├── infrastructure/ # LLM provider, vector store, scrapers
│   │   ├── security/       # Auth, rate limit, sanitizer, audit log
│   │   └── cli/            # build_chunks, embed
│   ├── data/
│   │   ├── raw/            # Scrape edilmiş ham JSON'lar
│   │   ├── processed/      # universities / departments / chunks
│   │   ├── embeddings/     # ChromaDB persistent dir (gitignore'da)
│   │   └── training/       # Fine-tuning dataset (Kaggle)
│   ├── scripts/            # Yardımcı script'ler + test_queries
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/          # Splash, Login, Home, Search, Pusula, Tercih...
│   │   ├── components/     # ChatSidebar, ThemeToggle, Three sahneler...
│   │   ├── contexts/       # Auth, Theme
│   │   └── firebase.js     # Firebase init + helper'lar
│   ├── package.json
│   └── vite.config.js
├── docs/                   # AI handoff & roadmap notları
├── .gitignore
├── LICENSE
└── README.md
```

---

## Lisans

[MIT](./LICENSE) — özgürce kullan, fork'la, dağıt.

---

## Teşekkürler

- **YÖK Atlas / ÖSYM** — açık veri kaynakları
- **URAP** — akademik sıralama metodolojisi
- **Google Gemini** — ücretsiz tier (1500 RPD / Flash-Lite)
- **Firebase** — auth + Firestore + Storage (Spark plan yeterli)
