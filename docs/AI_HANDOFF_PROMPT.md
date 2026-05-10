# 🤝 AI Asistan Handoff Promptu — UniSense

> **Kullanım:** Yeni Claude/Gemini/ChatGPT session açtığında bu metni kopyalayıp ilk mesaj olarak yapıştır.

---

## 📋 KOPYALA-YAPIŞTIR PROMPT

```
Selam! UniSense isimli mevcut Türkiye 2025 YKS Üniversite Tercih Asistanı projemde
devam etmen gerekiyor.

PROJE ÖZETİ:
- YÖK Atlas/ÖSYM verilerini doğal Türkçe sorgulayabilen tercih asistanı
- Kullanıcının ilgilerine göre bölüm öneren Pusula
- Puan/sıralamaya göre safe/target/reach öneri
- Drag-drop tercih listesi + ÖSYM kod kopyalama
- TYT/AYT/DGS hesap makinesi
- 9 sayfa frontend (React + Vite + Three.js + Firebase)

MİMARİ:
- Backend: Python FastAPI 0.115 + Pydantic v2 + ChromaDB + Gemini API
- Clean Architecture: domain/application/infrastructure/api/security/core/cli
- LLM: gemini-3.1-flash-lite-preview (multi-key + 429 fallback)
- Opsiyonel: UniSenseLocal (Ollama Qwen3-4B fine-tuned)
- Frontend: React 18 + Vite 5 + Tailwind 3 + Firebase Auth/Firestore + @dnd-kit
- 3D: Three.js + R3F + Drei (BackgroundScene + Splash 3D)

ÖNEMLİ KARARLAR (v2 - 2026-05):
- ✅ Pusula (3 mod: Kart Seç + Soru Sor + 5 Soru) — 358 bölüm grubu, 150+ ilgi pill
- ✅ Hesap Makinesi (TYT/AYT-SAY/EA/SÖZ/DİL/DGS, OBP 100'lük, DGS 4'lük)
- ✅ Önlisans verisi (9.337 program TYT, total 21.602 program)
- ✅ Trend (3 yıllık taban + sıra + momentum 📈/📉/📊)
- ✅ Coğrafi filtreler (28 sahil ili + 30 metropol + 31 merkez ilçe)
- ✅ Multi-turn chat (history son 8)
- ✅ Multi-LLM router (Gemini ↔ UniSenseLocal)
- ✅ Logo transparent PNG (RGB→RGBA dönüştürüldü)
- ✅ Qwen fine-tuning pipeline hazır (58.585 Q/A dataset + Kaggle notebook)
- ❌ DGS desteği yok (yokatlas-py 0.6.0 desteklemiyor — manuel ileride)

KOD KONUMLARI:
- Backend Clean Arch: backend/src/unisense/ (api/v1/routes.py, application/services/...)
- Frontend pages: frontend/src/pages/ (Splash, Home, Login, Profile, Pusula, Search, Recommend, TercihList, Hesap)
- Dataset üretici: backend/scripts/build_unisense_dataset.py
- Kaggle notebook: backend/data/training/unisense-egitimi-kaggle.ipynb
- Config: backend/.env (GEMINI_API_KEYS zorunlu)

ÇALIŞTIRMA:
- Backend: cd backend && uvicorn unisense.main:app --port 8002 --reload
- Frontend: cd frontend && npm run dev (http://localhost:5173)
- (Opsiyonel) Ollama: ollama serve (UniSenseLocal için)

NE YAPACAĞIZ:
[Buraya kendi sorunu/isteğini yaz. Örnek:
- "Bölüm karşılaştırma sayfası ekle (/compare?d=X,Y,Z)"
- "ChromaDB rebuild et — önlisans chunks'ları ekle"
- "DGS manuel scrape yaz"
- "Kaggle eğitiminden Qwen modelini Ollama'ya import et"
- "Yerleşme olasılığı simülasyonu (rank_q1/rank_q3)"
- "Production deploy: Vercel + Render"]

HİZMET TARZI:
- Doğrudan kod değişikliği yap (Edit/Write tool kullan)
- Önce dosyayı oku, sonra değiştir
- Türkçe açıklama yap, kısa ve sayısal cevaplar ver
- Önemli kararlar için onay iste
- docs/AI_CONTEXT.md, ROADMAP.md, PROJECT_STATUS.md'yi oku — tüm bağlam orada

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
3. ChromaDB'de chunk yok mu → curl /api/v1/health (chunks_count)
4. Önlisans cevap eksik → ChromaDB rebuild gerek
5. Multi-LLM router hata → hasattr(self._llm, '_providers') check
```

### D) Yeni veri kaynağı ekle
```
1. backend/src/unisense/infrastructure/scrapers/<kaynak>_scraper.py oluştur
2. Çıktı: backend/data/raw/<kaynak>/<isim>.json
3. transform_yokatlas.py'a benzer transform yaz (history + geo enrich)
4. cli/build_chunks.py'a yeni chunk türü ekle
5. ChromaDB'yi yeniden embedle (collection: unisense)
6. (Opsiyonel) build_unisense_dataset.py'a yeni Q/A kategorisi ekle
```

### E) Frontend yeni sayfa ekle
```
1. frontend/src/pages/<NewPage>.jsx oluştur
2. App.jsx'e route ekle
3. Tasarım: index.css'deki .glass, .card, .btn-primary kullan
4. 3D efekt: BackgroundScene veya yeni Scene komponenti
5. Framer Motion + lucide-react icons
6. Firebase entegrasyonu için: src/lib/firestore.js + src/lib/auth.js
```

### F) Production deploy et
```
1. Backend → Render (auto-deploy from GitHub main)
   - render.yaml + Dockerfile
   - Environment: GEMINI_API_KEYS, CHROMA_PERSIST_DIR
2. Frontend → Vercel (auto-deploy)
   - VITE_API_URL + Firebase env'leri
3. CORS güncelle (production domain)
4. SECURITY_REQUIRE_API_KEY=true
```

### G) Qwen fine-tuning training
```
1. Kaggle hesabına gir
2. Notebook: backend/data/training/unisense-egitimi-kaggle.ipynb yükle
3. Dataset: ibrahimaskeroglu/unisense-dataset (58.585 Q/A) attach et
4. T4 GPU seç, ~6-8 saat eğitim
5. Output: model GGUF veya HF format
6. Ollama import: Modelfile + ollama create unisense-local
7. UniSense'e ekle: OLLAMA_URL ayarı + frontend Search'te seçici
```

---

## 🔍 ARAMA REHBERİ

| "Şunu nerede bulurum?" | Dosya |
|---|---|
| Tüm endpoint'ler | `backend/src/unisense/api/v1/routes.py` |
| Multi-turn chat + intent | `backend/src/unisense/application/services/ask_service.py` |
| LLM router (Gemini ↔ UniSenseLocal) | `backend/src/unisense/infrastructure/llm/multi_router.py` |
| Gemini provider | `backend/src/unisense/infrastructure/llm/gemini.py` |
| Ollama provider | `backend/src/unisense/infrastructure/llm/qwen.py` |
| ChromaDB sorguları | `backend/src/unisense/infrastructure/vector_store/chroma_store.py` |
| Hibrit retrieval (TR-safe) | `backend/src/unisense/application/services/retrieval_service.py` |
| Tercih önerme + filter + geo | `backend/src/unisense/application/services/recommendation_service.py` |
| Trend (3 yıl) | `backend/src/unisense/application/services/trend_service.py` |
| Pusula (5-axis) | `backend/src/unisense/application/services/compass_service.py` |
| Pusula taxonomy + interests | `backend/src/unisense/application/services/compass_{taxonomy,interests}.py` |
| Önlisans scraper | `backend/src/unisense/infrastructure/scrapers/yokatlas_extra_scraper.py` |
| Veri pipeline | `backend/src/unisense/infrastructure/scrapers/transform_yokatlas.py` |
| Dataset üretici | `backend/scripts/build_unisense_dataset.py` |
| Kaggle notebook | `backend/data/training/unisense-egitimi-kaggle.ipynb` |
| Geo enrich | `backend/scripts/enrich_geo.py` |
| Türkçe karakter helper | `_tr_lower`, `_tr_upper` (retrieval_service.py) |
| Frontend ana komponen | `frontend/src/App.jsx` |
| Sayfalar (9) | `frontend/src/pages/` |
| Logo + Theme | `frontend/src/components/Logo.jsx` + `ThemeToggle.jsx` |
| Firestore | `frontend/src/lib/firestore.js` |
| 3D arkaplan | `frontend/src/components/three/BackgroundScene.jsx` |
| Veri (chunks) | `backend/data/processed/chunks.json` (14.539 chunk) |

---

## ⚠️ Kritik Kurallar

1. **API endpoint'leri BOZMA** — frontend kullanıyor (`/api/v1/ask`, `/api/v1/recommend`, `/api/v1/health`, `/api/v1/models`)
2. **ChromaDB collection adı `unisense`** — değiştirme, data uçar
3. **Embedding modeli sabit** — `paraphrase-multilingual-MiniLM-L12-v2` (chunks bu boyutla embed edildi)
4. **`.env` asla commit etme** — `.env.example` üzerinden çalış
5. **Türkçe karakter** — Python default `lower()`/`upper()` BOZUK, `_tr_lower`/`_tr_upper` kullan
6. **yokatlas-py 0.6.0 KKTC bug** — raw HTTP (`yokatlas_py.http_client`) ile bypass
7. **logo.png** — `frontend/public/logo.png` transparent RGBA, RGB'ye çevirme
8. **Multi-LLM AskService** — `hasattr(self._llm, '_providers')` check, kwargs'a `model_preference` ekle
9. **DGS** — yokatlas-py 0.6.0'da yok, manuel scrape gerek (henüz yapılmadı)

---

## 📝 v2 Migration Notes

❌ Eski referansları kullanma:
- Tek-LLM AskService (artık MultiLLMRouter)
- Eski `/api/v1/ask` body (artık `history[]` opsiyonel)
- Pusula bölüm pill'leri (artık ilgi pill, 5-axis vektör)
- 4-üzerinden OBP her tabda (artık DGS dışı 100'lük)

✅ Yeni kullan:
- `MultiLLMRouter` + `model_preference: "Gemini" | "UniSenseLocal"`
- Multi-turn `history: [{role: "user"|"assistant", content: "..."}]`
- Compass services: `taxonomy`, `interests`, `compass_service`
- TYT katsayıları: TR/Mat 3.3, Sosyal/Fen 3.4 (max 500)
- AYT-SAY: 3.0/2.85/3.07/3.07
- OBP: 100'lük × 0.12 (TYT/AYT için), DGS: 4'lük AOBP (× 25 × 0.5)
