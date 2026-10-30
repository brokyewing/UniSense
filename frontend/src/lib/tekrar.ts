// Aralıklı tekrar (Leitner sistemi) — yanlışları unutmadan pekiştirmek için.
// Kutu 1..5; her doğru cevapta bir üst kutuya (daha uzun aralık), yanlışta 1'e döner.
export const TEKRAR_ARALIK = [1, 2, 4, 8, 16] // kutu → kaç gün sonra tekrar

// YEREL tarih (toISOString UTC döndürür — TR'de gece 00:00-03:00 işlemleri
// önceki güne yazılıp 1 günlük tekrar aralığını ~2.5 saate düşürüyordu)
const pad2 = (n) => String(n).padStart(2, '0')
const tarihStr = (d) => `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`

export function bugunStr() {
  return tarihStr(new Date())
}

/** Tekrar sonucu: biliyorsa üst kutu (uzun aralık), bilmiyorsa kutu 1 (yarın). */
export function sonrakiTekrar(box = 1, biliyor = true) {
  const b = biliyor ? Math.min((box || 1) + 1, 5) : 1
  const gun = TEKRAR_ARALIK[b - 1]
  const next = tarihStr(new Date(Date.now() + gun * 86400000))
  return { box: b, nextReview: next }
}

/** Bugün (veya geçmişte) tekrar edilmesi gereken mi? */
export function tekrarZamani(y, today = bugunStr()) {
  return !y?.nextReview || y.nextReview <= today
}

// === SM-2 (SuperMemo-2) — bilgi kartları için aralıklı tekrar ===
// kalite: 0-5 (Zor=2, Orta=3, Kolay=5). Döner: {ef, rep, interval, nextReview}.
export function sm2(kart, kalite) {
  let ef = kart?.ef ?? 2.5
  let rep = kart?.rep ?? 0
  let interval = kart?.interval ?? 0
  if (kalite < 3) {
    rep = 0
    interval = 1 // yarın tekrar
  } else {
    rep += 1
    if (rep === 1) interval = 1
    else if (rep === 2) interval = 6
    else interval = Math.round(interval * ef)
    ef = ef + (0.1 - (5 - kalite) * (0.08 + (5 - kalite) * 0.02))
    if (ef < 1.3) ef = 1.3
  }
  const next = tarihStr(new Date(Date.now() + interval * 86400000))
  return { ef: Math.round(ef * 100) / 100, rep, interval, nextReview: next }
}
