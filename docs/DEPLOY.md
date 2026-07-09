# 🚀 UniSense — Production Deploy Rehberi

Bu doküman; backend (Render), frontend (Vercel), Firebase production ayarları
ve uptime monitoring için adımları içerir.

---

## 1A. Backend — Render Free + HF Dataset Index (ÖNERİLEN, $0/ay)

- Embedding lokal ONNX (`EMBEDDING_PROVIDER=local`) — API kotası/ücreti yok,
  RAM ~300-400MB → Render free'nin 512MB'ına sığar.
- Free tier'da kalıcı disk yok → hazır index HF **dataset** deposunda durur
  (dataset barındırma ücretsiz), container boot'ta indirir (~30-60 sn).
- NOT: HF Spaces'in Docker tipi artık PRO ($9/ay) istiyor — o yüzden Spaces
  değil Render free + HF dataset kombinasyonu kullanılıyor.

### Adımlar
1. Index'i lokalde üret (bir kez): `cd backend && python -m unisense.cli.embed`
2. Index'i HF'ye yükle (HF_TOKEN backend/.env içinde):
   `python scripts/upload_index_hf.py <kullanici>/unisense-index`
3. https://render.com → GitHub ile giriş (kart GEREKMEZ) → New + → **Blueprint**
   → UniSense repo → Apply. Kökteki `render.yaml` free plan ile hazır.
4. Sorulan env'leri gir: `GEMINI_API_KEYS`, `FIREBASE_PROJECT_ID`
5. Deploy logunda `Index indiriliyor` → `Uvicorn running` gör; sonra:
   `https://unisense-api.onrender.com/api/v1/health` → `{"status":"ok",...}`
6. **UptimeRobot şart:** free instance 15 dk boşta uyur; `/api/v1/health`'e
   5 dk'lık monitor ekle → hiç uyumaz (aylık 750 free saat 7/24'e yeter)

### Veri güncellenince
Lokalde re-embed → `upload_index_hf.py` tekrar → Render'da Manual Deploy.

## 1B. Backend — Render Starter (alternatif, $7/ay)

### Hazırlık
Repo'da `backend/Dockerfile` ve kökte `render.yaml` zaten mevcut
(Blueprint, render.yaml'ı SADECE repo kökünde arar).

### Adımlar
1. https://render.com → Sign up (GitHub ile)
2. Dashboard → **New +** → **Blueprint**
3. UniSense repo'sunu bağla → branch: `main`
4. Render kökteki `render.yaml`'ı otomatik okuyacak, "Apply" bas
5. **Environment variables** (Render UI'de elle gir, `sync: false` olanlar):
   - `GEMINI_API_KEYS` → `AIza...key1,AIza...key2` (virgülle ayır, multi-key fallback için 2-3 key öner)
   - `FIREBASE_PROJECT_ID` → `unisense-13634` (ID token doğrulaması için;
     service account GEREKMEZ, sadece proje ID'si yeter)
   - NOT: Eski `SECURITY_API_KEYS` yaklaşımı kaldırıldı — SPA'ya gizli key
     gömülemez. Kimlik doğrulama artık Firebase ID token ile
     (`SECURITY_REQUIRE_AUTH=true` render.yaml'da hazır).
6. Persistent disk otomatik mount edilir (`/data/chromadb`, 1 GB)
7. İlk build ~10 dakika sürer (sentence-transformers indir + chromadb init + ilk embed)
   - İlk deploy logunda embed'in `/data/chromadb`'ye yazabildiğini doğrula;
     "Permission denied" görürsen Dockerfile'daki `USER app` satırını kaldır
     (non-root user + Render disk kombinasyonu).
8. Health check: `https://unisense-api.onrender.com/api/v1/health`
   - Index boşsa health bilinçli olarak **503 döner** — "degraded" görürsen
     embed bitmemiş/başarısız demektir, logları kontrol et.

### Verify
```bash
curl https://unisense-api.onrender.com/api/v1/health
# {"status":"ok","version":"0.1.0","chunks_count":23876}

curl https://unisense-api.onrender.com/api/v1/models
# {"models":[{"id":"gemini","name":"Gemini","available":true,...}]}
```

### Sorun giderme
- **Build timeout**: `plan: starter` yavaş build edebilir; `pro` plan'a yükselt veya pre-built data ile devam et.
- **Memory error**: Embedding modeli ~470 MB. `plan: starter` 512 MB — sınırda. `standard` plan ($7/ay) güvenli.
- **Disk dolu**: ChromaDB ~50 MB; disk 1 GB yeterli.

---

## 2. Frontend — Vercel

### Hazırlık
Repo'da `frontend/vercel.json` zaten mevcut.

### Adımlar
1. https://vercel.com → Sign up (GitHub ile)
2. Dashboard → **Add New...** → **Project**
3. UniSense repo'sunu import et
4. **Root Directory**: `frontend`
5. **Framework Preset**: Vite (otomatik tespit edilmeli)
6. **Environment variables** (Vercel UI):
   ```
   VITE_API_URL=https://unisense-api.onrender.com
   VITE_FIREBASE_API_KEY=AIza...
   VITE_FIREBASE_AUTH_DOMAIN=projem.firebaseapp.com
   VITE_FIREBASE_PROJECT_ID=projem
   VITE_FIREBASE_STORAGE_BUCKET=projem.firebasestorage.app
   VITE_FIREBASE_MESSAGING_SENDER_ID=...
   VITE_FIREBASE_APP_ID=...
   VITE_FIREBASE_MEASUREMENT_ID=G-...
   ```
7. Deploy
8. Custom domain (opsiyonel): Project Settings → Domains → `unisense.app` ekle

### Verify
- https://unisense.vercel.app → Splash görmeli
- Login → Google ile giriş çalışmalı
- Search → "İTÜ bilgisayar taban puanı" sorgusu cevap dönmeli
- Compare → `/compare?d=203910363,102210295` 2 program göstermeli

---

## 3. Firebase — Production ayarları

### 3.1 Security Rules (Firestore + Storage)
Tercihen CI ile: GitHub repo Settings → Secrets → Actions'a şunları ekle,
sonrasında `firestore.rules`/`storage.rules` her değiştiğinde
`.github/workflows/firebase-rules.yml` otomatik deploy eder:
- `FIREBASE_SERVICE_ACCOUNT` → Firebase Console → Project Settings →
  Service accounts → **Generate new private key** → inen JSON'un tamamı
- `FIREBASE_PROJECT_ID` → `unisense-13634`

Manuel alternatif (tek seferlik):
```bash
npx firebase-tools login
npx firebase-tools deploy --only firestore:rules,storage --project unisense-13634
```

> Console'a elle yapıştırma YAPMA — repo'daki kural ile console'daki kural
> ayrışıyor, bug'ları görünmez kılıyor.

### 3.3 Authorized domains
Firebase Console → **Authentication** → Settings → **Authorized domains**:
- Ekle: `unisense.vercel.app` (ve varsa custom domain)

### 3.4 API key restrictions
Google Cloud Console → APIs & Services → **Credentials** → Browser API key:
- **Application restrictions**: HTTP referrers
- **Website restrictions**:
  - `https://unisense.vercel.app/*`
  - `https://localhost:5174/*` (dev)
  - Varsa custom domain

### 3.5 (Opsiyonel) Firestore backup
Firebase Console → Firestore → Backups → **Schedule** → Daily, retention 7 gün

---

## 4. Uptime Monitoring

### UptimeRobot (ücretsiz)
1. https://uptimerobot.com → Sign up
2. **+ Add New Monitor** → HTTP(s)
3. URL: `https://unisense-api.onrender.com/api/v1/health`
4. Interval: 5 dakika
5. Alert contacts: e-posta ekle
6. Beklenen response: `"status":"ok"`

### (Opsiyonel) Better Stack — Status sayfası
- https://betterstack.com (eski Better Uptime)
- HTTPS healthcheck + alarm + status sayfası tek panelden

### (Opsiyonel) Sentry — Error tracking
1. https://sentry.io → Sign up
2. **Backend (Python)**:
   ```bash
   pip install "sentry-sdk[fastapi]"
   ```
   `main.py` lifespan başına:
   ```python
   import sentry_sdk
   sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), traces_sample_rate=0.1)
   ```
   `SENTRY_DSN` env var Render'a ekle.
3. **Frontend (React)**:
   ```bash
   npm install @sentry/react
   ```
   `main.jsx` başına:
   ```js
   import * as Sentry from '@sentry/react'
   Sentry.init({ dsn: import.meta.env.VITE_SENTRY_DSN, tracesSampleRate: 0.1 })
   ```
   `VITE_SENTRY_DSN` env var Vercel'e ekle.

---

## 5. CORS — Cross-domain ayarı

Backend `.env` / Render env:
```
CORS_ALLOWED_ORIGINS=https://unisense.vercel.app,https://unisense.app
```

Yeni domain eklenince hem Render env güncelle hem Firebase Authorized domains'e ekle.

---

## 6. Yıllık otomatik veri sync (GitHub Actions)

`.github/workflows/yearly-data-sync.yml` zaten hazır. Her 15 Ağustos UTC 03:00'te:
1. YÖK Atlas / URAP / Wikipedia scrape
2. Transform + enrich
3. chunks.json yeniden üret
4. Git commit + push

**Render auto-deploy** açıksa push sonrası otomatik redeploy olur ve container start'ında `embed` çalışır (Dockerfile CMD bunu yapar).

Manuel tetikleme: GitHub Actions sekmesi → **Yearly YKS Data Sync** → **Run workflow**.

---

## 7. Maliyet özeti (aylık)

| Servis | Plan | $/ay |
|---|---|---|
| Hugging Face Spaces (backend) | Free (2 vCPU / 16GB) | $0 |
| Vercel (frontend) | Hobby | $0 |
| Firebase Auth + Firestore + Storage | Spark (free) | $0 |
| Gemini API (sadece cevap üretimi; embedding lokal ONNX) | Free tier (500 RPD/key) | $0 |
| UptimeRobot | Free (50 monitor) | $0 |
| **TOPLAM** | | **$0** |

> Trafik artarsa ilk ücretli kalem Gemini generation olur (~$0.0006/sorgu);
> alternatif hosting: Render Starter $7 (ONNX sayesinde 512MB'a sığar).

---

## 8. Production checklist

- [ ] Backend Render'da deploy, health 200 (`FIREBASE_PROJECT_ID` + `GEMINI_API_KEYS` girildi)
- [ ] Frontend Vercel'de deploy, açılıyor (`VITE_API_URL` Render URL'ini gösteriyor)
- [ ] GitHub secrets eklendi (`FIREBASE_SERVICE_ACCOUNT`, `FIREBASE_PROJECT_ID`)
- [ ] Firebase Security Rules deploy edildi (workflow yeşil / CLI çıktısı OK)
- [ ] Firebase Authorized domains güncellendi (unisense.vercel.app)
- [ ] Google API key HTTP referrer restriction aktif
- [ ] Gemini API keys multi-key olarak Render env'de
- [ ] CORS Render env'de production domain ile
- [ ] UptimeRobot health monitor aktif
- [ ] Frontend → Backend bağlantısı çalışıyor (Search sorgusu, GİRİŞLİ kullanıcıyla)
- [ ] Girişsiz kullanıcıda /ask 401 + "giriş yapmalısın" mesajı görünüyor
- [ ] Login → Google + Email çalışıyor
- [ ] Tercih ekle → Firestore yazılıyor (rule kontrolü)
- [ ] /compare sayfası 2 program ile çalışıyor
- [ ] Recommend yerleşme olasılığı rozeti görünüyor
