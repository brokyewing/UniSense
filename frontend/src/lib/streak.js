// Günlük çalışma serisi (streak) mantığı — saf, test edilebilir.
// "Çalışma günü" = kullanıcı o gün en az bir aktivite yaptı (konu işaretledi /
// deneme ekledi). Ardışık günler seriyi büyütür, bir gün atlanınca sıfırlanır.

// YEREL tarih (toISOString UTC döndürür — TR'de 00:00-03:00 arası çalışma
// önceki güne yazılır, gece çalışan öğrencinin serisi yanlış kırılırdı)
const pad2 = (n) => String(n).padStart(2, '0')
export const bugunStr = () => {
  const d = new Date()
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`
}

function gunFarki(a, b) {
  const da = new Date(a + 'T00:00:00'), db = new Date(b + 'T00:00:00')
  return Math.round((db - da) / 86400000)
}

/**
 * prev: { current, longest, lastDate } | null — bugün aktivite işle.
 * Döner: { current, longest, lastDate, changed } (changed=false → bugün zaten sayıldı).
 */
export function serisiIsle(prev, today = bugunStr()) {
  if (!prev || !prev.lastDate) {
    return { current: 1, longest: 1, lastDate: today, changed: true }
  }
  if (prev.lastDate === today) return { ...prev, changed: false } // bugün zaten sayıldı
  const fark = gunFarki(prev.lastDate, today)
  const current = fark === 1 ? (prev.current || 0) + 1 : 1 // dün→devam, değilse yeniden 1
  const longest = Math.max(prev.longest || 0, current)
  return { current, longest, lastDate: today, changed: true }
}

/** Seri bugün/dün değilse görsel olarak "kopmuş" sayılır (0 göster). */
export function guncelSeri(prev, today = bugunStr()) {
  if (!prev || !prev.lastDate) return 0
  const fark = gunFarki(prev.lastDate, today)
  return fark <= 1 ? (prev.current || 0) : 0
}
