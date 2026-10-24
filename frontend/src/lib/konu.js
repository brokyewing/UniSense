// Konu ilerlemesi yardımcıları — Konular sayfası + Deneme/mini-test paylaşır.
// checked haritası localStorage'da 'unisense_konu_v1_{sinav}' anahtarında,
// key = `${grup||''}|${ders}|${konu}` (Konular.jsx ile birebir).

export function konuBloklari(data) {
  if (!data) return []
  if (data.gruplar) {
    const out = []
    for (const [grup, dersler] of Object.entries(data.gruplar)) {
      for (const [ders, konular] of Object.entries(dersler)) out.push({ grup, ders, konular })
    }
    return out
  }
  return Object.entries(data.dersler || {}).map(([ders, konular]) => ({ grup: null, ders, konular }))
}

export const konuAnahtar = (grup, ders, konu) => `${grup || ''}|${ders}|${konu}`

export function konuLocal(sinav) {
  try { return JSON.parse(localStorage.getItem('unisense_konu_v1_' + sinav) || '{}') } catch { return {} }
}

/** Toplam/yapılan konu + işaretlenmemiş (eksik) konu listesi. */
export function eksikKonular(data, checked = {}) {
  const bl = konuBloklari(data)
  const eksik = []
  let toplam = 0, yapilan = 0
  for (const b of bl) {
    for (const k of b.konular) {
      toplam++
      if (checked[konuAnahtar(b.grup, b.ders, k)]) yapilan++
      else eksik.push({ ders: b.ders, konu: k })
    }
  }
  return { toplam, yapilan, eksik, hepsiBitti: toplam > 0 && eksik.length === 0 }
}

/** Rastgele n eksik konu seç (mini-test için). */
export function rastgeleSec(liste, n) {
  const a = [...liste]
  for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]] }
  return a.slice(0, n)
}
