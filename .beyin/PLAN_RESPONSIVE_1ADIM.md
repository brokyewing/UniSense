# Plan Taslağı — Responsive 1. Adım (Full-Width)

**Yazan:** opencode (plan; kodlama yok)
**Tarih:** 2026-09-04 22:41
**Durum:** taslak — onay + ekstra görevler bekleniyor
**Karar:** full-width (cap'siz). 24"+ ekranda ortada dar sütun bırakılmayacak;
içerik sağ-sol eşit boşlukla kenarlara yayılacak.

> Bu dosya yeni taslaktır; `.beyin/` içindeki mevcut yazılar silinmedi.
> Uygulama kodlaması bugünün kapsamı DIŞI — sonra başlanacak.

## Hedefler

- 15.6" (1366×768, 1536×864): rahat, taşmasız, simetrik.
- 24" ve üstü (1920×1080, 2560×1440): full-width, sağ-sol eşit padding, ortada boş sütun yok.
- Android (360–412px): tek sütun, yatay scroll yok, 44px dokunma hedefi.
- Her durumda sağ-sol boşluk eşit, simetrik shell.

## Mevcut durum tespiti (kaynak)

- `frontend/src/App.jsx:228` — tüm sayfalar `max-w-6xl (1152px) mx-auto px-4` gövdede.
  1920px'de yanlarda ~384px boşluk kalıyor (şikâyetin kaynağı).
- `frontend/src/App.jsx:124,233` — header/footer da `max-w-6xl`, büyük ekranda dar.
- `frontend/tailwind.config.js` — özel breakpoint yok (yalnızca sm/md/lg/xl/2xl).
  15.6" ↔ 24"+ ayrımı yok, küçük Android için `xs` yok.
- Sayfalar iç içe `max-w-3xl/4xl/6xl mx-auto` kullanıyor
  (örn. `Hesap.jsx:696`, `Pusula.jsx:757`, `Compare.jsx:194`) → çift daralma.
- Sabit çok sütunlu grid'ler mobilde ezilir:
  `Pusula.jsx:497 grid-cols-5`, `Hesap.jsx:729 grid-cols-3`.
- `frontend/index.html:11` — viewport doğru; sorun viewport değil, container/grid.

## İş maddeleri (taslak)

1. **Shell full-width (App.jsx:124,228,233)**
   - `max-w-6xl mx-auto` kaldır → `w-full` + kademeli simetrik padding:
     `px-4 md:px-6 xl:px-8 3xl:px-12`.
   - Okunabilirlik için metin ağırlıklı dar sayfalarda (Login, Privacy) sayfa-içi
     `max-w` korunabilir — liste kodlamada netleşecek.
2. **Breakpoint ekle (tailwind.config.js)**
   - `xs: 360px` (küçük Android), `3xl: 1920px` (24"+). Mevcut kırılımlar ezilmez.
3. **Grid revizyonu (öncelik sırası taslağı)**
   - Önce: `Home.jsx:228`, `Compare.jsx`, `Hesap.jsx:756`, `Pusula.jsx:717`.
   - Sonra kalan ~25 sayfa: `sm:grid-cols-2 lg:grid-cols-3` → `+ 3xl:grid-cols-4`
     kademesi; full-width'ten faydalan.
   - Sabit `grid-cols-5/3` → mobil-first kademe (`grid-cols-2 xs:… sm:…`).
4. **İç içe max-w temizliği**
   - Genişliği shell yönetir; sayfa-içi `max-w-3xl mx-auto` daraltmaları kaldırılır
     ya da genişletilir (form/login gibi odaklar hariç).
5. **Header/nav (App.jsx:136)**
   - Android taşma yok (`no-scrollbar` korunur), dokunma hedefi 44px'e çıkar.
6. **Doğrulama**
   - Matriks: 360×740 · 1366×768 · 1536×864 · 1920×1080 · 2560×1440.
   - Kriter: yatay scroll yok + sağ-sol boşluk simetrik (ekran görüntüleri).
   - `npm run dev` + Chrome device toolbar; mümkünse gerçek Android PWA kontrolü.

## Kapsam dışı (bugün)

- Kod değişikliği yok (plan günü).
- KPSS veri kaybı / CI kırmızısı bu planın dışında; kararı hâlâ bekliyor (bkz. DEVIR).
- Ekstra görevler kullanıcı tarafından eklenecek.

## Sonraki adım

Kullanıcı ekstra görevleri ekleyecek → onay → kodlamaya başlanacak.
