// Aralıklı tekrar (Leitner sistemi) — yanlışları unutmadan pekiştirmek için.
// Kutu 1..5; her doğru cevapta bir üst kutuya (daha uzun aralık), yanlışta 1'e döner.
export const TEKRAR_ARALIK = [1, 2, 4, 8, 16] // kutu → kaç gün sonra tekrar

export function bugunStr() {
  return new Date().toISOString().slice(0, 10)
}

/** Tekrar sonucu: biliyorsa üst kutu (uzun aralık), bilmiyorsa kutu 1 (yarın). */
export function sonrakiTekrar(box = 1, biliyor = true) {
  const b = biliyor ? Math.min((box || 1) + 1, 5) : 1
  const gun = TEKRAR_ARALIK[b - 1]
  const next = new Date(Date.now() + gun * 86400000).toISOString().slice(0, 10)
  return { box: b, nextReview: next }
}

/** Bugün (veya geçmişte) tekrar edilmesi gereken mi? */
export function tekrarZamani(y, today = bugunStr()) {
  return !y?.nextReview || y.nextReview <= today
}
