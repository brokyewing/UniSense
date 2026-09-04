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
2026-09-04 23:55 | Claude Code | KPSS veri kaybi geri alindi + bos-sonuc bekcisi, CI pin bypass i duzeltildi (CI artik yesil), tusdus sessiz basarisi giderildi; OSYM URL kesfi engelli.
2026-09-05 01:40 | Claude Code | OSYM yeni URL semasi cozuldu (chunked-hang toleransli fetch + Duyurular/Index kesfi); KPSS 2026/1, TUS ve DUS 2026 verileri geldi; CI yesil.
