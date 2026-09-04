# Günlük — UniSense

Append-only. Her oturum sonunda tek satır: `YYYY-MM-DD HH:MM | araç | ne yapıldı`

2026-08-27 16:00 | kurulum | Orkestra devir sistemi kuruldu
2026-09-04 21:12 | Claude Code | keep-alive workflow tek ping yerine 55 dk boyunca 5 dk arayla pingleyecek sekilde yeniden yazildi; GitHub cron gecikmesi olculdu (108-273 dk).
2026-09-04 22:05 | Claude Code | lgs-sync + yearly-data-sync workflowlarindaki 3 hata bulundu (eksik paket kurulumu, beyan edilmemis yokatlas-py, eksik --target) ve duzeltildi; temiz venvde dogrulandi.
2026-09-04 22:35 | Claude Code | tum workflow gecmisi tarandi; tusdus-sync de ayni eksik-paket hatasindan dusuyormus, duzeltildi; eski CI/Firebase hatalarinin coktan cozuldugu dogrulandi.
2026-09-04 22:55 | Claude Code | 3 sync workflow + ruff pin push edildi; KPSS placements verisinin 27 Temmuz bot commitiyle silindigi tespit edildi (karar bekliyor).
2026-09-04 22:41 | opencode | Responsive 1. adim plan taslagi yazildi (full-width karari, PLAN_RESPONSIVE_1ADIM.md); mevcut beyin yazilari korunup GOREVLER'e 6 madde eklendi; kodlama yapilmadi.
2026-09-04 22:50 | opencode | Kariyer sekmesi plan taslagi yazildi (gunluk otomatik ilan sync, PLAN_KARIYER.md); GOREVLER'e 6 madde eklendi; kaynak karari onay bekliyor; kodlama yapilmadi.
2026-09-04 22:58 | opencode | 21 sayfalik kamu rehberi + career-ops TR linkleri Kariyer planina islendi (Hat A A1-A18 + Hat B, iki hatli mimari); GOREVLER'e 4 madde eklendi; kodlama yapilmadi.
2026-09-04 23:07 | opencode | Responsive 1. adim uygulandi (sadece frontend: shell full-width, xs/3xl, 20 sayfa uncap, 3xl gridler); backend/data ve workflow'lara dokunulmadi; npm run build temiz.
2026-09-04 23:15 | opencode | Frontend push edildi (856513d + 2 merge: LGS a054d58, YKS 27e0b2d); Claude'un commitlenmemis dosyalari elenmedi.
2026-09-05 00:46 | opencode | Kariyer sehmesi uygulandi (scraper+API+workflow+sayfa); RG zincir sorunu cozuldu; pytest 92, ruff temiz, build 631 URL; ilk CI kosusu bekleniyor.
2026-09-05 01:02 | opencode | Kariyer beyaz ekran duzeltildi (rsplit->split, d52e8a6 pushlandi).
2026-09-05 01:15 | opencode | PDF kapsama denetimi: 12 eksik kaynak eklendi (37 toplam, URL'ler canli dogrulamali); test 11/11; e11a68e pushlandi.
2026-09-05 01:25 | opencode | 5 ek kaynak arastirildi (iskur acik is, elemanonline, cvyolla, stajim, jooble; 42 toplam); test 12/12; 0c02d8b pushlandi.
2026-09-05 01:38 | opencode | Hat B canli tarama yazildi (Jooble+Careerjet, career-ops desenli; anahtarsiz zarif atlama dogrulandi); test 16/16, ruff temiz; 0947055 pushlandi. API anahtarlari bekleniyor.
2026-09-05 01:52 | opencode | Anahtarlarla canli dogrulama: careerjet 117 + jooble 80 + RG 1 = 198 kayit; Jooble TLS zinciri (WE1+GTS R4) eklendi; 54c1a9b pushlandi.
2026-09-05 02:11 | opencode | Bolum secici: genis cekim + 12 bolum cift tarafli etiket + 30gun budama + secici UI; 563 cekim/488 kayit; test 21/21; 806961f pushlandi.
2026-09-04 23:55 | Claude Code | KPSS veri kaybi geri alindi + bos-sonuc bekcisi, CI pin bypass i duzeltildi (CI artik yesil), tusdus sessiz basarisi giderildi; OSYM URL kesfi engelli.
2026-09-05 01:40 | Claude Code | OSYM yeni URL semasi cozuldu (chunked-hang toleransli fetch + Duyurular/Index kesfi); KPSS 2026/1, TUS ve DUS 2026 verileri geldi; CI yesil.
2026-09-05 02:20 | Claude Code | CI kor noktasi kapatildi (haftalik schedule); LGS ve Yearly YKS dispatch ile yesil kosup 2026 verisini commitledi.
2026-09-05 03:10 | Claude Code | bos-sonuc bekcisi kalan 9 scrapera yayildi; transform_yokatlas sessiz return ve yokatlas ara-kayit ezmesi giderildi.
2026-09-05 04:30 | Claude Code | ruff <0.16 siniri kaldirildi (89 oto + 16 elle duzeltme, kalan 80 gerekceli ignore); TUS-DUS ve KPSS dispatch ile yesil; CI yesil.
2026-09-05 05:10 | Claude Code | Kariyer yol haritasi yazildi (PLAN_KARIYER_YOL_HARITASI.md); ilan.gov.tr JSON API kesfedildi, ISKUR WAF teyit edildi.
