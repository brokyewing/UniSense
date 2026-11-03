# Devir — UniSense
**Son araç:** Claude Code
**Tarih:** 2026-11-03 16:20
**Durum:** bekliyor

## Nerede kaldık
- Kullanıcının "son birkaç gündür hata alıyorum" şikâyetinin kaynağı: **Kariyer Data Sync** workflow'u 2026-10-25'ten beri her gün `failure`. Kök neden `ecd4569`'daki scraper yeniden yazımı (kaynak başına `try/except` kaldırıldı, koşu raporu ve guard çağrısı bozuldu, `test_kariyer.py` 838 satır silinip devre dışı bırakıldı).
- Kullanıcı onayıyla (dosya opencode'un alanı) düzeltildi: `backend/src/unisense/infrastructure/scrapers/kariyer_scraper.py`, `backend/tests/test_kariyer.py`, `backend/tests/test_kariyer_tarih_budama.py` → `ecd4569^` sürümüne geri alındı + test tarih-bombası fixture'ı + ruff 0.17 temizliği.
- Doğrulandı: `ruff check src tests` temiz, `pytest` 284 passed; kamuilan'a 403 enjekte edilmiş gerçek `main()` koşusu (scratch dizine yazdırılarak) exit 0, rapor şekli workflow'un beklediğiyle aynı.
- Diğer her şey sağlam: frontend tsc 0 hata, vitest 50/50, build 631 URL; canlı `/api/v1/health` 200, site 200, App Check token takası 200.
- Kariyer düzeltmesi `eab06fc` ile push'landı; elle tetiklenen koşu yeşil (41642372679), veri commit'i `24b23f1`.
- **Google girişi kırık (2026-10-28 `ab974bb`'den beri):** `authDomain` = `unisense.com.tr`; site Vercel'de olduğu için `/__/auth/handler` SPA döndürüyor (boş sayfa) ve Google `redirect_uri_mismatch` veriyor. `frontend/src/services/firebase-init.ts`'de `authDomain` = `${projectId}.firebaseapp.com` yapıldı (env'e bağlı değil). tsc 0, vitest 50/50, build OK; yerelde popup firebaseapp.com'a açılıyor. **Commit edilmedi.**
- Eski hesaplarda e-posta girişi `invalid-credential`: büyük olasılıkla bu hesaplar Google ile açıldı (şifreleri yok); Google girişi düzelince açılmalı. Firebase kullanıcı listesi doğrulanamadı (admin SDK okuması izin sınıflandırıcısınca engellendi).

## Sıradaki adım
`firebase-init.ts` değişikliğini commit + push et, Vercel deploy'undan sonra canlıda Google girişini kullanıcıyla test et.

## Engeller
- `kamuilan.sbb.gov.tr` GitHub runner IP'lerini engelliyor (lokalden 200); CI'da bu kaynak boş kalacak.
- Vercel MCP `broky-ewing` takımına erişim yetkisi yok.

## Dokunma
yok
