// Guest→bulut migration'ını GÜVENLİ yapar. Sorun: localStorage hem misafir verisini
// hem de girişli kullanıcının bulut AYNASINI aynı anahtarda tutuyor → "bulut boş +
// yerel dolu" koşulu ikisini ayırt edemiyordu. Sonuç: (a) son kayıt silinince ayna
// dolu kaldığı için migration silineni geri yüklüyordu; (b) ORTAK cihazda önceki
// hesabın aynası yeni hesabın bulutuna yazılıyordu (gizlilik sızıntısı).
//
// Çözüm: aynaya OWNER (uid) damgası koy. Sadece SAHİPSİZ (owner yok = gerçek misafir)
// veri taşınır. Damgalı ayna (kendi/başka kullanıcı) asla taşınmaz.
const ownerKey = (k: any) => k + '_owner'

/** Taşıma gerekli mi? Yalnız bulut boş + yerel dolu + ayna SAHİPSİZ (guest) ise. */
export function tasimaGerekli(lsKey: any, cloudBos: any, localDolu: any) {
  if (!cloudBos || !localDolu) return false
  let owner = null
  try { owner = localStorage.getItem(ownerKey(lsKey)) } catch { /* noop */ }
  return owner == null // sadece hiç damgalanmamış (misafir) veri
}

/** Bu aynanın sahibini uid olarak işaretle (her snapshot'ta çağrılır). */
export function damgala(lsKey: any, uid: any) {
  try { if (uid) localStorage.setItem(ownerKey(lsKey), uid) } catch { /* noop */ }
}
