# Product Lens (Steve Jobs — Walter Isaacson)

**Score: 8/10 | Vote: FUND**

## What is Strong
- **Focus**: "Türkiye tercih asistanı" tek cümle pitch. Feature creep var (Kariyer, Konu Takibi, Planım, Kariyer, LGS/TUS) ama core "tercih" etrafında organize.
- **Experience-first**: Öğrenci "puanımı gir → liste al → tercih yap" akışı net. Pusula (ilgi) → Tercih Robotu (puan) → Karşılaştırma → PDF → Kaydet akışı tutarlı.
- **End-to-end ownership**: Auth (Firebase) → Veri (Firestore) → API (FastAPI) → UI (React) → Deploy (Vercel/Render) tek elden. Seam (geçiş) noktaları: RAG latency, Firebase sync, SEO prerender.
- **Taste in details**: Dark/light theme, Framer Motion geçişleri, three.js arka plan (opsiyonel), gradient text, hover states, loading skeletons. "Kullanıcı pil tüketir" diye BackgroundScene opt-in planı var (iyi instinct).
- **Simplicity**: "Puan gir, liste al" ana value prop. Pusula modu "puan yoksa" alternatifi.

## What Would Kill It (Top 3)
1. **RAG latency + hallucination**: İlk sorgu 10+ saniye (cold start), cevapta yanlış ÖSYM kodu verirse güven çöker. "Kaynak linki" butonu var ama kullanıcı tıklamazsa?
3. **Mobile deneyimi**: three.js 856KB chunk + Tailwind + Framer Motion → entry-level telefonlarda 3-4 saniye TTI. BackgroundScene her sayfada (Search, Kariyer, Pusula) → pil tüketimi.
4. **Onboarding friksiyon**: "Puan gir" ilk ekranında → giriş yapmadan deneme yok. Pusula modu gizli (2. sekme). Kullanıcı "ne yapmam gerekiyor?" anlayamazsa bounce.

## What to Cut
- **Kariyer sekmesi** (MVP'den çık, ayrı ürün olabilir)
- **Konu Takibi / Planım / Deneme** (core "tercih" değilmiş; ayrı "çalışma" uygulaması)
- **LGS/TUS/DUS robotları** (farklı segment, ayrı landing page)
- **three.js BackgroundScene** (sadece Home'da, opsiyonel toggle ile)

## Questions for Founder
- **One thing**: "Puanına göre güvenli/hedef/riskli liste al" mi, yoksa "İlgi alanlarına göre bölüm keşfet" mi? İkisi birden "tercih asistanı" ama UX akışları farklı.
- **First 5 minutes**: Giriş yapmadan "Örnek sorgu dene" butonu var mı? (Pusula demo → kaydol → Tercih Robotu)
- **Handoffs**: RAG cevabı → "Tümünü Tercihe Ekle" butonu → Firestore yazma → UI güncelleme. Bu geçiş ne kadar smooth? Hata olursa ne gösterir?

## If FUND: Conditions
1. **Core flow hardening**: RAG p95 < 3s (warmup + cache), hallucination rate < %2 (golden set test), "Kaynak yok" fallback mesajı.
2. **Mobile-first**: BackgroundScene kaldır (veya lazy load), chunk splitting (three.js ayrı), TTI < 2s (4G).
3. **Onboarding redesign**: "Puan girmek istemiyorum" → Pusula demo (3 tıkla bölüm önerisi) → "Şimdi puan girip liste al" CTA.
4. **Feature flag system**: Kariyer/Konuları/Planım/LGS/TUS flag'lı → MVP'de kapalı, ileride açılabilir.