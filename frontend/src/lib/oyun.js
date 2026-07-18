// Oyunlaştırma — XP, seviye ve rozetler. Saf fonksiyonlar (test edilebilir).
// XP, kullanıcının YAPTIĞI işlerden TÜRETİLİR (event kaydı yok) → geçmişe dönük de çalışır.

// dakika: Pomodoro çalışma dakikası; kullanim: uygulamada geçirilen aktif dakika;
// soru: Günün Sorusu'nu doğru bilme
export const XP_PER = { konu: 5, deneme: 20, kart: 3, yanlis: 5, dakika: 1, kullanim: 1, soru: 10 }

/** İstatistiklerden toplam XP (yapılan işler + uygulamada geçen süre + doğru cevaplar). */
export function hesaplaXP(s = {}) {
  return (s.konuDone || 0) * XP_PER.konu
    + (s.denemeSayisi || 0) * XP_PER.deneme
    + (s.kartSayisi || 0) * XP_PER.kart
    + (s.yanlisSayisi || 0) * XP_PER.yanlis
    + Math.floor(s.sureDk || 0) * XP_PER.dakika
    + Math.floor(s.kullanimDk || 0) * XP_PER.kullanim
    + (s.dogruCevap || 0) * XP_PER.soru
}

/** Toplam XP → seviye + bu seviyedeki ilerleme. Her seviye biraz daha fazla XP ister. */
export function seviyeBilgi(xp) {
  let seviye = 1, acc = 0, need = 100
  while (xp >= acc + need) { acc += need; seviye += 1; need = 100 + (seviye - 1) * 60 }
  const mevcut = xp - acc
  return { seviye, mevcut, gereken: need, oran: Math.min(100, Math.round((mevcut / need) * 100)), toplam: xp }
}

export const ROZETLER = [
  { id: 'ilk-adim', ad: 'İlk Adım', ikon: '👣', aciklama: 'İlk çalışmanı yaptın', kosul: (s) => (s.konuDone + s.denemeSayisi + s.kartSayisi + s.yanlisSayisi) > 0 },
  { id: 'seri-7', ad: 'Azimli', ikon: '🔥', aciklama: '7 gün üst üste çalıştın', kosul: (s) => (s.streakLongest || 0) >= 7 },
  { id: 'seri-30', ad: 'Demir İrade', ikon: '💎', aciklama: '30 gün seri', kosul: (s) => (s.streakLongest || 0) >= 30 },
  { id: 'denemeci', ad: 'Denemeci', ikon: '📊', aciklama: '10 deneme girdin', kosul: (s) => (s.denemeSayisi || 0) >= 10 },
  { id: 'kart-100', ad: 'Kart Ustası', ikon: '🃏', aciklama: '100 bilgi kartı', kosul: (s) => (s.kartSayisi || 0) >= 100 },
  { id: 'calis-50', ad: 'Çalışkan', ikon: '📚', aciklama: '50 konu işaretledin', kosul: (s) => (s.konuDone || 0) >= 50 },
  { id: 'maraton', ad: 'Maratoncu', ikon: '⏱️', aciklama: '10 saat çalışma süresi', kosul: (s) => (s.sureDk || 0) >= 600 },
  { id: 'hata-avcisi', ad: 'Hata Avcısı', ikon: '🎯', aciklama: '20 yanlış kaydettin', kosul: (s) => (s.yanlisSayisi || 0) >= 20 },
]

export function kazanilanRozetler(s = {}) { return ROZETLER.filter((r) => r.kosul(s)) }

/** Girişsiz (guest) istatistikleri localStorage'dan topla. */
export function guestStats() {
  const j = (k, d) => { try { return JSON.parse(localStorage.getItem(k) || d) } catch { return JSON.parse(d) } }
  let konuDone = 0, denemeSayisi = 0
  for (const s of ['YKS', 'DGS', 'KPSS', 'LGS']) {
    konuDone += Object.keys(j('unisense_konu_v1_' + s, '{}')).length
    denemeSayisi += j('unisense_deneme_' + s, '[]').length
  }
  const streak = j('unisense_streak', 'null') || {}
  const sure = j('unisense_sure', '{}')
  const kullanim = j('unisense_kullanim', '{}')
  return {
    konuDone, denemeSayisi,
    kartSayisi: j('unisense_flashcards', '[]').length,
    yanlisSayisi: j('unisense_yanlis', '[]').length,
    streakLongest: streak.longest || 0,
    sureDk: sure.sureDk || 0, sureHafta: sure.sureHafta || {}, dersSure: sure.dersSure || {},
    kullanimDk: kullanim.dk || 0,
    dogruCevap: Number(localStorage.getItem('unisense_dogru') || 0),
  }
}
