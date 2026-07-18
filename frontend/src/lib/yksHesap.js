// YKS net + yerleştirme puanı hesabı — Deneme Günlüğü ve (ileride) Hesap ortak kullanır.
// KATSAYILAR Hesap.jsx ile BİREBİR aynı; şimdilik duplike, ileride Hesap da buradan
// import edecek (tek kaynak). Değişirse İKİSİ birden güncellensin.

export const OBP_MULT = 0.12
export const YKS_PEN = 0.25 // 4 yanlış 1 doğru götürür

// TYT ders katsayıları — yerleştirme (SAY/EA/SÖZ/DİL tek formülü)
export const TYT_PLACEMENT_COEF = {
  tyt_tr: 1.32, tyt_sos: 1.36, tyt_mat: 1.32, tyt_fen: 1.36, // TYT bloğu max ≈160
}
export const AYT_COEF = {
  SAY: { ayt_mat: 3.0, ayt_fiz: 2.85, ayt_kim: 3.07, ayt_biy: 3.07 },
  EA: { ayt_mat: 3.0, ayt_edb: 3.0, ayt_tar1: 2.8, ayt_cog1: 3.33 },
  SÖZ: { ayt_edb: 3.0, ayt_tar1: 2.8, ayt_cog1: 3.33, ayt_tar2: 2.91, ayt_cog2: 2.91, ayt_fel: 2.67, ayt_din: 4.0 },
  DİL: { ayt_dil: 3.0 }, // AYT bloğu max ≈240
}

// Ders alanları (id, etiket, soru sayısı) — form + net için
export const TYT_FIELDS = [
  { id: 'tyt_tr', label: 'TYT Türkçe', max: 40 },
  { id: 'tyt_sos', label: 'TYT Sosyal', max: 20 },
  { id: 'tyt_mat', label: 'TYT Matematik', max: 40 },
  { id: 'tyt_fen', label: 'TYT Fen', max: 20 },
]
export const AYT_FIELDS = {
  SAY: [
    { id: 'ayt_mat', label: 'AYT Matematik', max: 40 },
    { id: 'ayt_fiz', label: 'AYT Fizik', max: 14 },
    { id: 'ayt_kim', label: 'AYT Kimya', max: 13 },
    { id: 'ayt_biy', label: 'AYT Biyoloji', max: 13 },
  ],
  EA: [
    { id: 'ayt_mat', label: 'AYT Matematik', max: 40 },
    { id: 'ayt_edb', label: 'AYT Edebiyat', max: 24 },
    { id: 'ayt_tar1', label: 'AYT Tarih-1', max: 10 },
    { id: 'ayt_cog1', label: 'AYT Coğrafya-1', max: 6 },
  ],
  SÖZ: [
    { id: 'ayt_edb', label: 'AYT Edebiyat', max: 24 },
    { id: 'ayt_tar1', label: 'AYT Tarih-1', max: 10 },
    { id: 'ayt_cog1', label: 'AYT Coğrafya-1', max: 6 },
    { id: 'ayt_tar2', label: 'AYT Tarih-2', max: 11 },
    { id: 'ayt_cog2', label: 'AYT Coğrafya-2', max: 11 },
    { id: 'ayt_fel', label: 'AYT Felsefe', max: 12 },
    { id: 'ayt_din', label: 'AYT Din', max: 6 },
  ],
  DİL: [{ id: 'ayt_dil', label: 'YDT Yabancı Dil', max: 80 }],
}

/** Net = doğru − penalty×yanlış (ÖSYM kuralı; negatif kalabilir). */
export function netOf(dogru, yanlis, pen = YKS_PEN) {
  return (parseFloat(dogru) || 0) - pen * (parseFloat(yanlis) || 0)
}

/** diploma notu (50-100) → OBP (250-500). */
export function diploma100ToObp(diploma100) {
  const d = parseFloat(diploma100)
  if (!d || d < 50 || d > 100) return 0
  return d * 5
}

function weightedSum(nets, coefMap) {
  let total = 0
  let any = false
  for (const [key, coef] of Object.entries(coefMap)) {
    const n = parseFloat(nets[key]) || 0
    if (n !== 0) { any = true; total += n * coef }
  }
  return any ? total : 0
}

/** Yerleştirme puanı (SAY/EA/SÖZ/DİL). nets: {tyt_*, ayt_*}. obp: 0-500. */
export function placementScore(nets, type, obp = 0) {
  const ayt = weightedSum(nets, AYT_COEF[type] || {})
  if (ayt <= 0) return 0
  const tyt = weightedSum(nets, TYT_PLACEMENT_COEF)
  return 100 + tyt + ayt + obp * OBP_MULT
}

/** Bir deneme girdisinden (ders→{d,y}) net haritası + toplam net + puan üret. */
export function denemeHesapla(girdi, type, obp = 0) {
  const fields = [...TYT_FIELDS, ...(AYT_FIELDS[type] || [])]
  const nets = {}
  let toplamNet = 0
  const dersNet = {}
  for (const f of fields) {
    const g = girdi[f.id] || {}
    const net = netOf(g.d, g.y)
    nets[f.id] = net
    dersNet[f.id] = net
    toplamNet += net
  }
  const puan = placementScore(nets, type, obp)
  return { nets, dersNet, toplamNet: Math.round(toplamNet * 100) / 100, puan: Math.round(puan * 100) / 100 }
}
