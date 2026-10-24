# Monopoly Lens (Peter Thiel - Zero to One)

**Score: 6/10 | Vote: FUND IF**

## What is Strong
- **Proprietary data pipeline**: YOK Atlas/OYSM/URAP/Wikipedia verilerini RAG icin hazirlayan (scraping -> cleaning -> embedding -> ChromaDB) tekrarlanabilir pipeline. Copycat'ler veri toplama + temizleme + embedding maliyetini (zaman + teknik bilgi) odemek zorunda.
- **Small market ownership**: "Turkiye YKS tercih asistani" dar bir niche. Genel "egitim uygulamasi" yerine, YKS/DGS/KPSS/LGS/TUS/DUS odakli. Bu pazarin %1'i bile buyuk (yillik ~25K premium kullanici potansiyeli).
- **Network effects (potansiyel)**: Kullanici tercih listeleri + notlar + konu takibi -> veri birikimi -> daha iyi oneriler -> daha fazla kullanici. Firestore verisi bu donguyu besler.

## What Would Kill It (Top 3)
1. **No 10x breakthrough**: RAG + resmi veri = incremental improvement. Mevcut "tercih robotu" siteleri (yokatlas, ozel siteler) zaten var. Teknik moat: veri kalitesi + RAG retrieval quality. Ama bu "10x better" degil "2x better" seviyesinde.
2. **Distribution risk**: SEO'ye bagimli. Google algoritmasi degisirse (HCU, core update) trafik %50+ dusebilir. Paid/referral/viral loop yok. Ilk 100 musteri nasil gelecek? (Content marketing? Influencer? Okul is birlikleri?)
3. **Durability**: YOK Atlas/OYSM verileri her yil degisiyor. Yillik scrap + embed pipeline bakimi surekli engineering ister. Tek gelistirici bu yuku tasir mi? "Secret" (bilgi asimetrisi) ne? Veri erisimi herkese acik -> moat zayif.

## Seven Questions
| Soru | Cevap | Risk |
|------|-------|------|
| Engineering: 10x mi? | RAG pipeline + veri kalitesi = ~2x. 10x yok. | Yuksek |
| Timing: Why now? | Gemini free tier + ChromaDB + Vercel/Render ucretsiz tier = maliyet ~0. | Dusuk |
| Monopoly: Small market own? | "Turkiye YKS RAG asistani" niche ownership mumkun. | Orta |
| People: Right team? | 1 dev. Bus factor = 1. | Cok Yuksek |
| Distribution: Reach buyers? | SEO organik. Paid/viral yok. | Yuksek |
| Durability: 10 yil? | Veri kaynagi resmi -> surecek. Pipeline bakim riski. | Orta |
| Secret: What do you know? | "RAG + resmi veri + OSYM kodu + sigmoid olasilik" kombinasyonu. | Orta |

## Questions for Founder
- Ilk 100 premium kullaniciyi nasil kazanacaksin? (CAC hedefi ne?)
- Tek gelistirici riskini nasil yonetecesin? (Docs, tests, bus factor artirma plani?)
- "Secret" ne? Sadece kod mu, veri pipeline mi, RAG tuning mu, marka mi?

## If FUND IF: Conditions
1. **Distribution plan**: Ilk 6 ayda 10K organic user hedefi + referral loop (arkadas davet -> 1 ekstra sorgu) + okul/rehber ogretmeni outreach programi.
2. **Bus factor mitigation**: Critical path dokumantasyonu (scraper -> embed -> RAG -> API), test coverage %80+, on-call runbook.
3. **Moat quantification**: Retrieval quality benchmark (golden set 200 soru) + human evaluation. Copycat'in bu benchmark'i gecmesi icin ne gerekir?
4. **Distribution diversification**: SEO + 1 paid channel (Google Ads YKS season) + 1 partnership (ozel dershane/rehberlik servisi).