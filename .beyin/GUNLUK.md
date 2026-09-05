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
2026-09-05 09:43 | opencode | Yol haritasi F0.1: sema v2 + _migrate (487 kayipsiz, id surekliligi korunuyor); 8ebe2f8 pushlandi. Siradaki: F0.3.
2026-09-05 10:08 | opencode | Yol haritasi F0.3: calisma_sekli cikarimi (testli kalip tablosu, dagilim loglandi 480/2/4); 9fab443 pushlandi. Siradaki: F0.4.
2026-09-05 10:19 | opencode | Yol haritasi F0.4: kaynak kayit defteri + yukleyici (davranis paritesi testli+canli); 7d6dec3 pushlandi. Siradaki: F1.1.
2026-09-05 12:12 | opencode | F3.2 kamuilan adaptoru (postback+timeline, canli 76/68 ilan, 46368bb). F1.1/F1.3 arastirmasi: ilangovtr POST bot-skorlamali (GET GetAdsByPublishTime personelsiz), Vizyoner savunmakariyer.com'a tasinmis (keycloak, API yok). Siradaki: F1.1 filtreler.
2026-09-05 12:23 | opencode | F1.1-F1.3: API filtreleri + facet + siralama (test 41, canli dogrulandi); 2c99e58 pushlandi. Siradaki: F1.4 filtre paneli.
2026-09-05 12:39 | opencode | F1.4-F1.7: filtre paneli + URL senkron + kart + mobil (build temiz); aaf76f9 pushlandi. Siradaki: F2.1 kosu raporu.
2026-09-05 12:49 | opencode | F2.1: kaynak bazli kosu raporu + adaptor hata toleransi (canli 4 satir); a912594 pushlandi. Siradaki: F2.2 olu-kaynak alarmi.
2026-09-05 13:09 | opencode | F2.2: olu-kaynak alarmi (10 kosu gecmis, Step Summary; kirmiziya dusurmez karari); 7660aea pushlandi. Siradaki: F2.3 tekillestirme.
2026-09-05 14:16 | opencode | F2.3: capraz kaynak tekillestirme (kamu kazanir, canli 17 birlesme); da93be9 pushlandi. F2 tamam. Siradaki: F3.1 KK RSS.
2026-09-05 14:34 | opencode | F3.1: Kariyer Kapisi RSS adaptoru (girissiz, canli 33/30 ilan); 74bd5ea pushlandi. Siradaki: F3.3 ilan.yok.
2026-09-05 15:27 | opencode | F3.3: ilan.yok olu, akademiktr adaptoru (canli 32); F3.4: BIK API cozumuyle 126 personel ilani + union merge duzeltmesi; b18ebbe pushlandi. Siradaki: F3.5 Vizyoner.
2026-09-05 17:44 | opencode | F3.5: savunmakariyer API adaptoru (JS paketinden, 23 ilan canli, Sectigo zinciri); 059dc20 pushlandi. 8 kaynak/777 kayit. Siradaki: F3.6 olcum.
2026-09-05 18:04 | opencode | F3.6: olcum + turksat adaptoru (0 acik); Ziraat/TUBITAK [!]; 792 kayit, test 61; a9abc2e pushlandi. F3 tamam. Siradaki: F3.7 ISKUR.
2026-09-05 18:43 | opencode | F3.7 ISKUR [!] (WAF her seyi reddediyor) + F3.8 KPSS cikarimi (PDF detay, canli 13 kayit); 95b976d pushlandi. F3 tamam. Siradaki: F4.1 sorgu genisletme.
2026-09-05 21:00 | opencode | F4.1: sorgu genisletme (Jooble 10 + CJ 7; canli 1843 kayit/1.9MB); 9347f2e pushlandi. Siradaki: F4.2 ATS tespiti.
2026-09-05 21:37 | opencode | F4.2: 53 sirket ATS taramasi (Lever 4 + Ashby 2 dogrulandi; deftere is_kaynaklari.yml); YAML yerlesim hatasi parite testiyle yakalanip duzeltildi; test 65; 22fcdc7 pushlandi. Siradaki: F4.3 ATS adaptorleri.
2026-09-05 22:03 | opencode | F4.3: Lever+Ashby adaptorleri (6 sirket/62 ilan, Amazon+Starfield zinciri); 1965 kayit, test 68; d29270d pushlandi. Siradaki: F4.4 tek tek sirketler.
2026-09-05 22:27 | opencode | F4.4-F4.6: tek tek sirket arastirmasi (uygulanabilir adaptor cikmadi) + robots kararlari + indeed yasak; SAHIPLIK.md protokolune gecildi; c94eebd pushlandi. F4 tamam. Siradaki: F5 olcekleme.
2026-09-05 22:37 | opencode | F5.1 hazirlik: --hat filtresi + gecmis birlesmesi (test 71); workflow bolunmesi Claude'a birakildi (sahiplik); 9f16165 pushlandi. Siradaki: F5.2 hiz sinirlari.
2026-09-05 23:10 | opencode | F5.2: merkezi istek politikasi (retry+backoff+4xx kurali, 10 cagri noktasi); pre-commit 263 test yesil; 497bdd4 pushlandi. Yol haritasi bitti (F5.3 kullanici karari bekliyor).
2026-09-05 23:30 | opencode | Claude'un v2 degisikliklerine test uyarlandi (kamu varsayimi; CJ tarih duzeltmesi onda hazirdi); pre-commit 264 yesil; a3a186f pushlandi. SAHIPLIK protokolu dogrulandi.
2026-09-04 23:55 | Claude Code | KPSS veri kaybi geri alindi + bos-sonuc bekcisi, CI pin bypass i duzeltildi (CI artik yesil), tusdus sessiz basarisi giderildi; OSYM URL kesfi engelli.
2026-09-05 01:40 | Claude Code | OSYM yeni URL semasi cozuldu (chunked-hang toleransli fetch + Duyurular/Index kesfi); KPSS 2026/1, TUS ve DUS 2026 verileri geldi; CI yesil.
2026-09-05 02:20 | Claude Code | CI kor noktasi kapatildi (haftalik schedule); LGS ve Yearly YKS dispatch ile yesil kosup 2026 verisini commitledi.
2026-09-05 03:10 | Claude Code | bos-sonuc bekcisi kalan 9 scrapera yayildi; transform_yokatlas sessiz return ve yokatlas ara-kayit ezmesi giderildi.
2026-09-05 04:30 | Claude Code | ruff <0.16 siniri kaldirildi (89 oto + 16 elle duzeltme, kalan 80 gerekceli ignore); TUS-DUS ve KPSS dispatch ile yesil; CI yesil.
2026-09-05 05:10 | Claude Code | Kariyer yol haritasi yazildi (PLAN_KARIYER_YOL_HARITASI.md); ilan.gov.tr JSON API kesfedildi, ISKUR WAF teyit edildi.
2026-09-05 05:35 | Claude Code | F0.2 bitti: il_to_bolge yazim farklarina dayanikli hale getirildi (Istanbul/istanbul bolge bulamiyordu), 18 test eklendi.
2026-09-05 06:20 | Claude Code | il_ilce_ayikla eklendi: birlesik/ters sirali konum alani cozuluyor, bolge kapsami 147->460; Careerjet tarih hatasi (178 kayit) tespit edilip gorev yazildi.
2026-09-05 07:15 | Claude Code | Faz sirasi bagimlilik mantigina gore duzeltildi: deger (API+frontend) one alindi, emniyet (rapor+tekillestirme) kaynaklardan once, kamu hattinda kesin kaynaklar basa.
2026-09-05 07:45 | Claude Code | Kariyer Kapisi RSS bulundu (33 ilan, giris gerekmiyor); e-Devlet kurali plana yazildi: giris BASVURU icin, liste acik; giris asla otomatiklestirilmez.
2026-09-05 08:20 | Claude Code | Kapali kapilar bolumu eklendi: LinkedIn robots ile tamamen yasak (anthropic-ai dahil), Indeed kisitli, kariyer.net ilan yollari serbest; repo 230 MB sismesi F5.3 olarak yazildi.
2026-09-05 09:05 | Claude Code | KAYNAK_HARITASI.md yazildi: kurum-kurum yaklasimi olculerek elendi (ortak desen yok, soft-404), toplayici-once stratejisi BIK mevzuatiyla dogrulandi; OSB izi acildi.
2026-09-05 09:40 | Claude Code | Ikinci kesif turu: akademik+saglik alimlari BIKte cikti (ayri adaptor gereksiz), OSBUK 302 faal OSB 78/81 ilde haritalandi, odalar kaynak degil diye kapatildi.
2026-09-05 10:05 | Claude Code | 3. kesif turu: KPSS siz alim yapan 5 kurumda RSS aranmis, hepsi yanlis pozitif cikti (TUBITAK/VizyonerGenc soft-404, ASELSAN rss.xml aslinda HTML); kisa yol yok, API aranacak.
2026-09-05 10:55 | Claude Code | 4. tur: TOBB firma veri tabani ilan kaynagi degil (uyelik + sadece firma kaydi, eski PHP uclari olu); ATS yolu dogrulandi (Lever/Greenhouse acik JSON API) ama slug cakismasi tuzagi tespit edildi.
2026-09-05 11:20 | Claude Code | ATS kesfi olculdu: okunan slug 3/3 basarili (trendyol 27, dreamgames 19, iyzico 12 = 58 ilan), tahmin edilen 0/6. Kariyer sayfasi taramasi verimi 2/10 (cogu JS).
2026-09-05 11:50 | Claude Code | Vizyoner Genc cozuldu: site savunmakariyer.com olmus, tam acik REST API bulundu (24 ilan + 81 il + 343 onayli firma, auth yok). ASELSAN/HAVELSAN/ROKETSAN/STM/BAYKAR bu tek kaynakta -> F3.6 kapsami daraldi.
2026-09-05 12:15 | Claude Code | ATS haritasi genisledi: peakgames 20 ilan (slug aramayla bulundu, "peak" tutmuyordu) -> toplam 78 ilan. Peak Lever alanlari bozuk (location=Full-time) -> ATS alanlarina korlemesine guvenme kurali yazildi.
2026-09-05 12:45 | Claude Code | ilan.gov.tr COZULDU: sorun oturum degil gecersiz sorting degeriymis (API sessizce 0 donuyor). sorting=id desc, sayfa tavani 20, 25.061 ilan, cityCounts 81 il; personel alimi orani %10,5 (~2.600 ilan).
2026-09-05 13:15 | Claude Code | 7. tur: kodilan.com artik is sitesi degil (alan adi el degistirmis, kumar sitesi) -> listeden cikarildi; TUBITAK kariyer statik tanitim sayfasi, ilan yok; techcareer/youthall/yenibiris/eleman.net beslemesi yok.
2026-09-05 13:40 | Claude Code | SAHIPLIK.md yazildi (dosya sahipligi + cakisma onleme protokolu); PLAN_KARIYER.mddeki iki yanlis iddia duzeltildi (ATS APIsi yok / tek TR ATS Getir).
2026-09-05 14:05 | Claude Code | ATS haritasi: getmidas 13, insiderone 117 (kuresel, Istanbul 10), codeway 0 eklendi -> TR ilgili ~101 ilan. papara/useinsider/colendi arama sonucunda vardi ama 404 (bayat indeks) -> "aramadan geleni API de dogrula" kurali yazildi.
2026-09-05 14:40 | Claude Code | Kaynak rehberi icin 9 yeni girdi + 6 duzeltme hazirlandi (KAYNAK_REHBERI_ONERILERI.md); kodilan girdisi kumar sitesine donustugu icin silinmeli olarak isaretlendi.
2026-09-05 15:10 | Claude Code | Kapsama olculdu: 7 kaynak toplaniyor / rehberde 42 / ~35i yalniz link. KAPSAMA_MATRISI.md yazildi; hazir bekleyen iki adaptor (savunmakariyer, Lever ATS) gorev olarak isaretlendi.
2026-09-05 15:45 | Claude Code | Buyuk paneller olculdu: kariyer.net WAF 403 (elendi), eleman.net schema.org JobPosting JSON-LD ile en zengin kaynak cikti (il+ilce+son basvuru+istihdam turu hazir), yenibiris/isbul erisilebilir ama HTML parse gerekiyor.
2026-09-05 16:20 | Claude Code | DUZELTME: ilan.gov.tr id desc kronolojik degil (skip 0=2022, skip 100=2026) -> artimli tarama plani gecersiz; personel ilani orani %10,5 degil ~%1,4, "2.600 ilan" tahmini sisikti. Kamu kurumlarinin cogu BIKte YOK (15 kurumun 13u universite).
2026-09-05 16:55 | Claude Code | Kurum kapsamasi olculdu: BIK ve Kariyer Kapisi TAMAMLAYICI (BIK universite/belediye, KK bakanlik/kurum); duzenleyici+guvenlik kurumlari ikisinde de YOK ama hazir beslemeleri de yok -> onceligi dusuruldu.
2026-09-05 17:25 | Claude Code | KESIF FAZI KAPANDI: indeed robotsla kapali (jobs/viewjob/q-/jobs-TR hepsi yasak), secretcv render sonrasi bile tekil ilan URLsi vermiyor, akademikag JS. Ozet: 7 toplaniyor, 2 hazir, 3 yazilabilir, 5 kapali.
2026-09-05 18:05 | Claude Code | Budama hatasi bulundu: _merge yas kurali (tarih>30 gun) basvurusu ACIK ilanlari siliyor — Savunma Kariyer 24->12, Kariyer Kapisi 33->30, toplam 14 acik ilan kaybi. Satir numarasiyla GOREVLERe yazildi.
2026-09-05 18:30 | Claude Code | Denetim: 792 kaydin 128inde il yok (hepsi kamu kaynagi). geo.metinden_il_bul yazildi + istisna tablosu; 82/128 (%64) kurtariliyor. Careerjet tarih hatasi hala acik (228 kayit).
2026-09-05 18:55 | Claude Code | Careerjet tarih + acik ilan budama hatalari duzeltildi (88a6d5b); CI 4 saattir kirmiziydi, birikmis lint borcu temizlendi (ba1c12f). Commit oncesi ruff zorunlulugu GOREVLERe yazildi.
2026-09-05 19:15 | Claude Code | Jooble kapsamı COZULDU: kurum alani kaynak panoyu tutuyor (yenibiris 117, elemanonline 62, bakiciburada 56, secretcv 31, isbul 16) -> bu siteler icin ayri adaptor gereksiz. Kalite: calisma_sekli %99 bos, istihdam_turu %94 bos.
2026-09-05 19:40 | Claude Code | calisma_sekli tavani olculdu: Lever %100 (91 kayit), diger kaynaklarda alan YOK; 1843 kayittan 17si dolu. En iyi ihtimalle ~%21 -> urun karari gerekiyor. Budama duzeltmesi dogrulandi: Savunma Kariyer 12->23.
2026-09-05 20:05 | Claude Code | Bedava kazanc bulundu: Jooble detay.tur %88 dolu (658/744) ama istihdam_turuya eslenmemis. calisma_sekli metin cikarimi tavani %8 olculdu. Careerjet maas ve site alanlari 0/929 (olu).
2026-09-05 21:00 | Claude Code | Sehir kanoniklestirme (355->65 il) ve Jooble istihdam_turu (%2->%36) baglandi; lint duzeltmeleri 2. kez geri gittigi icin pre-commit kancasi eklendi. robots_kontrol eksik, CI opencode tarafinda kirik.
2026-09-06 | Claude Code | unisense.site render.yaml+vercel.json'dan silindi; ilce->il indeksi (98 tekil ilce) ve calisma_sekli cikarimi (27->568, %1,4->%29,4) baglandi, kaynak damgasi eklendi; 284 test yesil (83f0e4a).
