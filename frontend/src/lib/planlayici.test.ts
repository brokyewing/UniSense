import { describe, it, expect } from 'vitest'
import { haftaPlanla, ufukPlanla, parseDirektif, parseHedef } from './planlayici'

const sampleKonuData = {
  dersler: {
    Matematik: ['Temel Kavramlar', 'Fonksiyonlar'],
    Türkçe: ['Paragraf', 'Sözcükte Anlam'],
  },
}

describe('planlayici', () => {
  it('haftaPlanla skips past days, spreads topics round-robin, and preserves existing tasks', () => {
    const existing = [
      { id: 'manual-1', ders: 'Fizik', konu: 'Hareket', tarih: '2026-11-27', status: 'planned', source: 'manual' },
    ]
    const plan = haftaPlanla({
      konuData: sampleKonuData,
      checked: { '|Matematik|Temel Kavramlar': true },
      soruOzet: [{ ders: 'Matematik', konu: 'Üslü Sayılar', cozulen: 10, dogru: 3 }],
      hafta: '2026-W48',
      bugun: '2026-11-27',
      haftaIciBlok: 1,
      haftaSonuBlok: 2,
      mevcut: existing,
    })
    expect(plan[0]).toEqual(existing[0])
    expect(plan.length).toBeGreaterThan(existing.length)
    // bugun (2026-11-27) ve sonrası için plan yapar; geçmiş günlere koymaz
    expect(plan.slice(1).every((t: any) => t.tarih >= '2026-11-27')).toBe(true)
    expect(plan.some((t: any) => t.konu === 'Üslü Sayılar' && t.tur === 'tekrar')).toBe(true)
  })

  it('ufukPlanla distributes topics across gunSayisi with gunlukSoru tempo', () => {
    const tasks = ufukPlanla({
      konuData: sampleKonuData,
      checked: {},
      gunSayisi: 3,
      gunlukSoru: 60,
      baslangic: '2026-11-27',
    })
    // gunlukSoru=60 => 3 blok/gün, toplam 3 gün * 3 = 9 görev
    expect(tasks.length).toBe(9)
    expect(new Set(tasks.map((t: any) => t.tarih))).toEqual(new Set(['2026-11-27', '2026-11-28', '2026-11-29']))
    expect(tasks.every((t: any) => typeof t.hafta === 'string' && t.hafta.includes('-W'))).toBe(true)
  })

  it('parseDirektif extracts JSON directives safely or returns null', () => {
    const parsed = parseDirektif('Öneri:\n{"oncelik":["Paragraf","Fonksiyonlar"],"tavsiye":"Düzenli çöz"}')
    expect(parsed).toEqual({ oncelik: ['Paragraf', 'Fonksiyonlar'], tavsiye: 'Düzenli çöz' })
    expect(parseDirektif('geçersiz metin')).toBeNull()
    expect(parseDirektif('')).toBeNull()
  })

  it('parseHedef validates gunSayisi and clamps optional gunlukSoru', () => {
    const parsed = parseHedef('{"gunSayisi": 45, "gunlukSoru": 120, "tavsiye": "Harika"}')
    expect(parsed).toEqual({ gunSayisi: 45, gunlukSoru: 120, tavsiye: 'Harika' })
    expect(parseHedef('{"gunSayisi": 0}')).toBeNull()
    expect(parseHedef('not json')).toBeNull()
  })
})
