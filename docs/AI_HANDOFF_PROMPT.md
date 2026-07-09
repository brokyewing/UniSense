# 🤝 AI Asistan Handoff Promptu — UniSense

> **Kullanım:** Yeni Claude/Gemini/ChatGPT session açtığında bu metni kopyalayıp ilk mesaj olarak yapıştır.

---

## 📋 KOPYALA-YAPIŞTIR PROMPT

```
Selam! UniSense isimli mevcut Türkiye 2025 YKS Üniversite Tercih Asistanı projemde
devam etmen gerekiyor.

PROJE ÖZETİ (v3.0):
- YÖK Atlas/ÖSYM verilerini doğal Türkçe sorgulayabilen tercih asistanı
- Wikipedia infobox ile zenginleştirilmiş üni verisi (website/logo/kuruluş)
- Kullanıcının ilgilerine göre bölüm öneren Pusula (5-axis)
- Puan/sıralamaya göre safe/target/reach öneri + yerleşme olasılığı (sigmoid)
- 2-5 program yan yana karşılaştırma (Compare)
- Drag-drop tercih listesi + kişisel notlar + ÖSYM kod kopyalama
- TYT/AYT/DGS hesap makinesi
- 11 sayfa frontend (React + Vite + Three.js + Firebase)

MİMARİ:
- Backend: Python FastAPI 0.115 + Pydantic v2 + ChromaDB + Gemini API
- Clean Architecture: domain/application/infrastructure/api/security/core/cli
- LLM: sadece Gemini (gemini-2.5-flash-lite, multi-key + 429 fallback)
- Cache: TTLCache (512 entry, 1 saat)
- Warmup: FastAPI lifespan startup ile embedding modeli ısınır
- Frontend: React 18 + Vite 5 (manualChunks vendor split + lazy 3D)
- Tailwind 3 + Firebase Auth/Firestore/Storage + @dnd-kit
- 3D: Three.js + R3F + Drei (BackgroundScene + Splash 3D)

ÖNEMLİ KARARLAR (v3.0 — 2026-05):
- ✅ Compare (/compare?d=X,Y,Z) — 2-5 program yan yana, EN İYİ/EN ZAYIF vurgu
- ✅ Yerleşme olasılığı — sigmoid (user_rank vs base_rank, q1 ile yumuşatma) yüzde rozet
- ✅ Kişisel tercih notları — TercihList textarea, debounced 700ms save
- ✅ Production deploy hazır — Dockerfile, render.yaml, vercel.json, firestore.rules, storage.rules
- ✅ Wikipedia infobox enrich (221 üni) — website/logo/kuruluş yılı/rektör
- ✅ Önlisans RAG'a eklendi (toplam 23.876 chunk)
- ✅ KVKK / Gizlilik sayfası (/privacy)
- ✅ Embedding warm-up + Gemini cache + retrieval optimize
- ✅ GitHub Actions yıllık cron (15 Ağustos otomatik scrape)
- ❌ UniSenseLocal / Qwen3-4B / Ollama tamamen KALDIRILDI (v2.5)
- ❌ DGS desteği yok (yokatlas-py 0.6.0 desteklemiyor — manuel ileride)

KOD KONUMLARI:
- Backend Clean Arch: backend/src/unisense/ (api/v1/routes.py, application/services/...)
- Frontend pages: frontend/src/pages/ (Splash, Home, Login, Profile, Pusula, Search, Recommend, TercihList, Compare, Hesap, Privacy)
- Compare service: backend/src/unisense/application/services/compare_service.py
- Yerleşme olasılığı: backend/src/unisense/application/services/recommendation_service.py (placement_probability fn)
- Firebase helper: frontend/src/firebase.js (updateTercihNote)
- Wikipedia infobox: backend/src/unisense/infrastructure/scrapers/wikipedia_infobox_scraper.py
- Config: backend/.env (GEMINI_API_KEYS zorunlu)
- Production deploy: docs/DEPLOY.md (Render + Vercel + Firebase rules)
- Workflow: .github/workflows/yearly-data-sync.yml

ÇALIŞTIRMA:
- Backend: cd backend && uvicorn unisense.main:app --port 8002 --reload
- Frontend: cd frontend && npm run dev (http://localhost:5174)

NE YAPACAĞIZ:
[Buraya kendi sorunu/isteğini yaz. Örnek:
- "DGS manuel scrape yaz (HTML scrape veya ÖSYM PDF parser)"
- "Geçmiş yıl (2022, 2021) history scrape — 5 yıllık trend grafiği için"
- "LinkedIn alumni intelligence — bir üniden mezunlar nereye gitmiş"
- "Email bildirim sistemi — tercih son günü hatırlatması"
- "Maliyet hesabı (kira+yemek+ulaşım × 4 yıl)"
- "Production deploy gerçekleştir (docs/DEPLOY.md adımları)"
- "Compare sayfasına recharts ile gerçek grafik ekle"
- "Mobile app (Expo) MVP"]

HİZMET TARZI:
- Doğrudan kod değişikliği yap (Edit/Write tool kullan)
- Önce dosyayı oku, sonra değiştir
- Türkçe açıklama yap, kısa ve sayısal cevaplar ver
- Önemli kararlar için onay iste
- docs/AI_CONTEXT.md, ROADMAP.md, PROJECT_STATUS.md, DEPLOY.md'yi oku — tüm bağlam orada

Hadi başla.
```

---

## 🎯 GÖREV-BAZLI HIZLI PROMPT'LAR

### A) Yeni özellik ekleme
> "AI_CONTEXT.md ve ROADMAP.md'yi oku. Sonra X özelliği eklemek istiyorum: [detay]. Önce plan, onayla, sonra kod."

### B) Bug fix
> "AI_CONTEXT.md'yi oku. Şu hata var: [traceback]. Sebebini bul + düzelt. Mevcut testleri bozma."

### C) Veri sorgu yanıtı yanlış geliyor
```
Hibrit retrieval'ı test et:
curl -X POST http://localhost:8002/api/v1/ask \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary @test.json

test.json: {"query":"<sorgu>","top_k":12,"history":[]}

Sorun çıkarsa:
1. Türkçe karakter varsa → _tr_lower / _tr_upper kullan
2. Üni adı tespit edilmiyorsa → _detect_university_keywords() SHORT_NAMES ekle
3. ChromaDB'de chunk yok mu → curl /api/v1/health (chunks_count = 23876 olmalı)
4. Cache hit dönüyor olabilir — query'ye \n boşluk ekle
```

### D) Yeni veri kaynağı ekle
```
1. backend/src/unisense/infrastructure/scrapers/<kaynak>_scraper.py oluştur
2. Çıktı: backend/data/raw/<kaynak>/<isim>.json
3. transform veya enrich script ile processed/universities.json'a katil
4. cli/build_chunks.py — yeni chunk türü veya alan ekle
5. python -m unisense.cli.build_chunks && python -m unisense.cli.embed
```

### E) Frontend yeni sayfa ekle
```
1. frontend/src/pages/<NewPage>.jsx oluştur (Privacy.jsx veya Compare.jsx tasarım dilini izle)
2. main.jsx'e route ekle: <Route path="/x" element={<NewPage />} />
3. Tasarım: index.css'deki .glass, .card, .btn-primary kullan
4. BackgroundScene + Framer Motion + lucide-react icons
5. Firebase entegrasyonu için: frontend/src/firebase.js helper'ları
```

### F) Production deploy
```
docs/DEPLOY.md adımlarını izle:
1. Backend Render (Dockerfile + render.yaml hazır)
2. Frontend Vercel (vercel.json hazır)
3. Firebase Security Rules publish (firestore.rules + storage.rules hazır)
4. Authorized domains + API key restrictions
5. UptimeRobot health monitor
```

### G) Yıllık veri sync (cron)
```
GitHub Actions otomatik 15 Ağustos'ta tetiklenir.
Manuel: GitHub repo → Actions → "Yearly YKS Data Sync" → Run workflow.
Akış: scrape (yokatlas + urap + wikipedia + infobox) → transform → enrich → build_chunks → commit
Render auto-deploy push sonrası tetiklenir, container start'ta embed çalışır.
```

---

## 🔍 ARAMA REHBERİ

| "Şunu nerede bulurum?" | Dosya |
|---|---|
| Tüm endpoint'ler | `backend/src/unisense/api/v1/routes.py` |
| Multi-turn chat + intent + cache | `backend/src/unisense/application/services/ask_service.py` |
| Gemini provider | `backend/src/unisense/infrastructure/llm/gemini.py` |
| ChromaDB sorguları + warmup | `backend/src/unisense/infrastructure/vector_store/chroma_store.py` |
| Hibrit retrieval (TR-safe) | `backend/src/unisense/application/services/retrieval_service.py` |
| Tercih önerme + filter + geo + olasılık | `backend/src/unisense/application/services/recommendation_service.py` |
| Trend (3 yıl) | `backend/src/unisense/application/services/trend_service.py` |
| **Compare service (v3)** | `backend/src/unisense/application/services/compare_service.py` |
| Pusula (5-axis) | `backend/src/unisense/application/services/compass_service.py` |
| Önlisans scraper | `backend/src/unisense/infrastructure/scrapers/yokatlas_extra_scraper.py` |
| **Wikipedia infobox (v2.5)** | `backend/src/unisense/infrastructure/scrapers/wikipedia_infobox_scraper.py` |
| **Enrich universities (v2.5)** | `backend/src/unisense/infrastructure/scrapers/enrich_universities.py` |
| Yokatlas transform | `backend/src/unisense/infrastructure/scrapers/transform_yokatlas.py` |
| Geo enrich | `backend/scripts/enrich_geo.py` |
| Türkçe karakter helper | `_tr_lower`, `_tr_upper` (retrieval_service.py) |
| Frontend ana | `frontend/src/App.jsx` + `main.jsx` |
| Sayfalar (11) | `frontend/src/pages/` |
| **Compare.jsx (v3)** | `frontend/src/pages/Compare.jsx` |
| **Privacy.jsx (v2.5)** | `frontend/src/pages/Privacy.jsx` |
| Logo + Theme | `frontend/src/components/Logo.jsx` + `ThemeToggle.jsx` |
| Firestore + **updateTercihNote** | `frontend/src/firebase.js` |
| 3D arkaplan | `frontend/src/components/three/BackgroundScene.jsx` |
| Veri (chunks) | `backend/data/processed/chunks.json` (23.876 chunk) |
| **Production Dockerfile** | `backend/Dockerfile` |
| **Render blueprint** | `backend/render.yaml` |
| **Vercel config** | `frontend/vercel.json` |
| **Firebase rules** | `firestore.rules` + `storage.rules` |
| **Deploy rehberi** | `docs/DEPLOY.md` |

---

## ⚠️ Kritik Kurallar

1. **API endpoint'leri BOZMA** — frontend kullanıyor (`/api/v1/ask`, `/recommend`, `/health`, `/models`, `/programs/{lookup,compare}`)
2. **ChromaDB collection adı `unisense`** — değiştirme, data uçar
3. **Embedding modeli sabit** — `paraphrase-multilingual-MiniLM-L12-v2` (chunks bu boyutla embed edildi)
4. **`.env` asla commit etme** — `.env.example` üzerinden çalış
5. **Türkçe karakter** — Python default `lower()`/`upper()` BOZUK, `_tr_lower`/`_tr_upper` kullan
6. **yokatlas-py 0.6.0 KKTC bug** — raw HTTP (`yokatlas_py.http_client`) ile bypass
7. **logo.png** — `frontend/public/logo.png` transparent RGBA, RGB'ye çevirme
8. **ChromaVectorStore.collection property** — yeni `chromadb.PersistentClient` açma, mevcut store'u kullan
9. **TTLCache key** — query + history + model_pref hash; cache hit'te LLM'ye gitme
10. **DGS** — yokatlas-py 0.6.0'da yok, manuel scrape gerek (henüz yapılmadı)

---

## 📝 v3.0 Migration Notes

❌ Eski referansları kullanma:
- `MultiLLMRouter`, `QwenProvider`, `UniSenseLocal`, `unisense-local` model_preference
- `backend/data/training/` (Qwen dataset)
- `unisense-tr-gguf/` (GGUF model)
- `backend/scripts/build_unisense_dataset.py`
- Eski Pusula bölüm pill'leri (artık ilgi pill, 5-axis vektör)

✅ Yeni kullan:
- Sadece Gemini API (multi-key fallback)
- TTLCache cevap önbelleği (1 saat)
- Lifespan startup warmup (cold start ~4sn)
- `placement_probability` Recommendation alanı (sigmoid)
- `/api/v1/programs/compare` endpoint (2-5 ÖSYM)
- `updateTercihNote(uid, code, note)` Firestore helper
- TYT katsayıları: TR/Mat 3.3, Sosyal/Fen 3.4
- AYT-SAY: 3.0/2.85/3.07/3.07
- OBP: 100'lük × 0.12 (TYT/AYT), DGS: 4'lük AOBP (× 25 × 0.5)
