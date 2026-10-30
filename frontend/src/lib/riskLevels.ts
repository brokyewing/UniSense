/**
 * Risk kategorisi — TEK KAYNAK.
 *
 * Öneriler (Recommend) ve Tercih Listem (AnalizPanel) aynı programı AYNI
 * kategoride göstersin diye eşikler burada toplanır. Eşiği burada değiştir →
 * her iki ekran birlikte güncellenir. (Önceden 3 ayrı yerde farklı eşik vardı:
 * YKS 1.5↔1.2, DGS +10↔+5, KPSS +3↔+2 — aynı program iki yerde farklı görünüyordu.)
 *
 * Dönüş: 'safe' | 'target' | 'reach' | 'bos' | 'bilinmez' | null
 *   null → hesaplamak için gereken bilgi (puan/sıra/taban) eksik.
 */

// YKS — rank oranı: taban_sırası / kullanıcı_sırası (oran yüksekse daha güvenli)
export const YKS_SAFE_RATIO = 1.5
export function yksLevel(userRank, tabanRank) {
  if (!userRank || !tabanRank) return null
  const ratio = tabanRank / userRank
  if (ratio >= YKS_SAFE_RATIO) return 'safe'
  if (ratio >= 0.85) return 'target'
  return 'reach'
}

// DGS — fark: puan - taban
export function dgsLevel(puan, taban) {
  if (taban == null) return 'bos'
  if (puan == null) return null
  const diff = puan - taban
  if (diff >= 10) return 'safe'
  if (diff >= 0) return 'target'
  return 'reach'
}

// KPSS — fark: puan - geçmiş dönem taban
export function kpssLevel(puan, taban) {
  if (taban == null) return 'bilinmez'
  if (puan == null) return null
  const diff = puan - taban
  if (diff >= 3) return 'safe'
  if (diff >= -1) return 'target'
  return 'reach'
}
