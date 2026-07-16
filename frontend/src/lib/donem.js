// Tercih dönemi (pazarlama) yılı — TEK merkezden.
// Eylül'den itibaren siteler bir SONRAKİ yılın dönemini pazarlar
// ("2027 Tercih Dönemi" Ekim 2026'da başlar). Build/çalışma anında hesaplanır;
// her deploy'da kendini günceller — yıllık elle string düzeltme gerekmez.
// NOT: VERİ yılları (taban puan "2025" gibi) buradan DEĞİL, API yanıtlarındaki
// yil/data_yili alanlarından gelir.
export const TERCIH_YILI = (() => {
  const d = new Date()
  return d.getMonth() >= 8 ? d.getFullYear() + 1 : d.getFullYear()
})()
