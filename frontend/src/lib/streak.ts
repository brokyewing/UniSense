// Günlük çalışma serisi (streak) mantığı — saf, test edilebilir.
// "Çalışma günü" = kullanıcı o gün en az bir aktivite yaptı (konu işaretledi /
// deneme ekledi). Ardışık günler seriyi büyütür, bir gün atlanınca sıfırlanır.

const pad2 = (n: number) => String(n).padStart(2, '0')
export const bugunStr = () => {
  const d = new Date()
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`
}

function gunFarki(a: string, b: string) {
  const da = new Date(a + 'T00:00:00'), db = new Date(b + 'T00:00:00')
  return Math.round((db.getTime() - da.getTime()) / 86400000)
}

interface StreakPrev {
  current?: number
  longest?: number
  lastDate?: string
}

export function serisiIsle(prev: StreakPrev | null, today: string = bugunStr()) {
  if (!prev || !prev.lastDate) {
    return { current: 1, longest: 1, lastDate: today, changed: true }
  }
  if (prev.lastDate === today) return { ...prev, changed: false }
  const fark = gunFarki(prev.lastDate, today)
  const current = fark === 1 ? (prev.current || 0) + 1 : 1
  const longest = Math.max(prev.longest || 0, current)
  return { current, longest, lastDate: today, changed: true }
}

export function guncelSeri(prev: StreakPrev | null, today: string = bugunStr()) {
  if (!prev || !prev.lastDate) return 0
  const fark = gunFarki(prev.lastDate, today)
  return fark <= 1 ? (prev.current || 0) : 0
}