// Çalışma planlayıcısı — SAF planlama mantığı (test edilebilir, 0 sunucu).
// Tüm mekanik iş burada, DETERMİNİSTİK: öneri, haftalık dağıtım, carry-forward,
// gecikme (lag), aralıklı tekrar. LLM YALNIZ "takvimim nasıl?" yorumu için (Planim.jsx).
// Konu verisi + eksik konu hesabı lib/konu.js ile paylaşılır.
import { eksikKonular } from './konu'

// ---- Tarih yardımcıları (yerel gün — UTC kayması olmasın) ----
export function isoGun(d = new Date()) {
  const t = new Date(d)
  t.setHours(0, 0, 0, 0)
  const y = t.getFullYear()
  const m = String(t.getMonth() + 1).padStart(2, '0')
  const g = String(t.getDate()).padStart(2, '0')
  return `${y}-${m}-${g}`
}

/** ISO hafta anahtarı "yyyy-Www" (Pazartesi başlangıç, ISO-8601). */
export function isoHafta(d = new Date()) {
  const t = new Date(d)
  t.setHours(0, 0, 0, 0)
  const gun = (t.getDay() + 6) % 7 // Pzt=0 … Paz=6
  t.setDate(t.getDate() - gun + 3) // haftanın Perşembesi
  const yil = t.getFullYear()
  const ocak4 = new Date(yil, 0, 4)
  const o4gun = (ocak4.getDay() + 6) % 7
  const ilkPer = new Date(yil, 0, 4 - o4gun + 3)
  const hafta = 1 + Math.round((t - ilkPer) / (7 * 86400000))
  return `${yil}-W${String(hafta).padStart(2, '0')}`
}

/** Verilen tarihin haftasının 7 günü (Pzt→Paz), ISO gün string dizisi. */
export function haftaGunleri(d = new Date()) {
  const t = new Date(d)
  t.setHours(0, 0, 0, 0)
  t.setDate(t.getDate() - ((t.getDay() + 6) % 7)) // Pazartesi
  return Array.from({ length: 7 }, (_, i) => {
    const x = new Date(t)
    x.setDate(t.getDate() + i)
    return isoGun(x)
  })
}

/** İki ISO gün arasındaki fark (b - a), tam gün. */
export function gunFark(aIso, bIso) {
  const a = new Date(aIso + 'T00:00:00')
  const b = new Date(bIso + 'T00:00:00')
  return Math.round((b - a) / 86400000)
}

const HAFTA_SONU = new Set([0, 6]) // Paz, Cmt
const haftaSonuMu = (iso) => HAFTA_SONU.has(new Date(iso + 'T00:00:00').getDay())

// ---- Konu havuzu (ağırlıklı, dersler arası round-robin) ----
// tur: 'tekrar' (çözülmüş ama doğruluk düşük) > 'yeni' (hiç işaretlenmemiş)
function havuz(konuData, checked, soruOzet = []) {
  const aday = []
  // Çok soru çözülmüş ama doğruluğu <%60 → öncelikli tekrar
  for (const o of soruOzet) {
    if ((o.cozulen || 0) >= 5 && (o.dogru || 0) / o.cozulen < 0.6) {
      aday.push({ ders: o.ders || 'Genel', konu: o.konu || o.ders || 'Tekrar', tur: 'tekrar', agirlik: 3 })
    }
  }
  const gorulen = new Set(aday.map((a) => a.konu))
  // Hiç işaretlenmemiş konular → yeni çalışma
  const { eksik } = eksikKonular(konuData, checked)
  for (const e of eksik) {
    if (gorulen.has(e.konu)) continue
    aday.push({ ders: e.ders, konu: e.konu, tur: 'yeni', agirlik: 2 })
  }
  return roundRobinDers(aday)
}

/** Aynı ders arka arkaya gelmesin: derslere böl, sırayla birer tane al. */
function roundRobinDers(list) {
  const kova = new Map()
  for (const x of list) {
    if (!kova.has(x.ders)) kova.set(x.ders, [])
    kova.get(x.ders).push(x)
  }
  const gruplar = [...kova.values()]
  const out = []
  let kaldi = true
  while (kaldi) {
    kaldi = false
    for (const g of gruplar) {
      if (g.length) { out.push(g.shift()); kaldi = true }
    }
  }
  return out
}

const gorevBaslik = (c) => (c.tur === 'tekrar' ? `${c.konu} — tekrar & 15 soru` : `${c.konu} — 20 soru`)

/** "Bugün ne çalışayım?" — en öncelikli n öneri (deterministik). */
export function oneriler(konuData, checked, soruOzet = [], n = 3) {
  return havuz(konuData, checked, soruOzet).slice(0, n).map((c) => ({
    ders: c.ders, konu: c.konu, tur: c.tur, title: gorevBaslik(c),
  }))
}

/** Görev nesnesi kur (deterministik id: hafta-gün-slot ya da çağıranın verdiği). */
export function gorevYap({ id, ders, konu, title, tarih, durMin = 45, status = 'planned', source = 'auto', tur }) {
  return { id, ders, konu, title, tarih, durMin, status, source, ...(tur ? { tur } : {}) }
}

/**
 * Haftayı deterministik planla. Bugün ve sonrası günlere, hafta içi/sonu blok
 * sayısına göre ağırlıklı konuları dağıtır. Mevcut görevleri EZMEZ — sadece
 * boş slotları doldurur (aynı gün+ders çakışması atlanır).
 */
export function haftaPlanla({ konuData, checked, soruOzet = [], hafta, bugun = isoGun(), haftaIciBlok = 2, haftaSonuBlok = 4, oncelikKonu = [], mevcut = [] }) {
  const gunler = haftaGunleri(new Date(bugun + 'T00:00:00')) // hafta = bugünün haftası
  const havuzListe = havuz(konuData, checked, soruOzet)
  // AI önceliği: verilen konuları havuzun önüne al
  if (oncelikKonu.length) {
    const seto = new Set(oncelikKonu.map((s) => String(s).toLocaleLowerCase('tr')))
    havuzListe.sort((a, b) => {
      const ao = seto.has(a.konu.toLocaleLowerCase('tr')) ? 0 : 1
      const bo = seto.has(b.konu.toLocaleLowerCase('tr')) ? 0 : 1
      return ao - bo
    })
  }
  if (!havuzListe.length) return mevcut
  // Çakışma anahtarı gün+KONU (gün+ders değil): aynı gün aynı konuyu tekrar koyma ama
  // farklı konularla blok sayısı dolabilsin (az dersli sınavda hedef tutmayı engellemesin).
  const doluluk = new Set(mevcut.map((t) => `${t.tarih}|${t.konu}`))
  const yeni = [...mevcut]
  let hi = 0
  for (let gi = 0; gi < gunler.length; gi++) {
    const tarih = gunler[gi]
    if (gunFark(bugun, tarih) < 0) continue // geçmiş günü planlama
    const blok = haftaSonuMu(tarih) ? haftaSonuBlok : haftaIciBlok
    let konulan = 0
    let deneme = 0
    while (konulan < blok && deneme < havuzListe.length) {
      const c = havuzListe[hi % havuzListe.length]
      hi++; deneme++
      const anahtar = `${tarih}|${c.konu}`
      if (doluluk.has(anahtar)) continue
      doluluk.add(anahtar)
      yeni.push(gorevYap({
        id: `${hafta}-${gi}-${konulan}`, ders: c.ders, konu: c.konu,
        title: gorevBaslik(c), tarih, source: 'auto', tur: c.tur,
      }))
      konulan++
      deneme = 0
    }
  }
  return yeni
}

/** Geciken (planlanmış ama tarihi geçmiş) görevleri bugüne taşı. Yeni dizi döner. */
export function carryForward(tasks = [], bugun = isoGun()) {
  return tasks.map((t) =>
    t.status === 'planned' && gunFark(t.tarih, bugun) > 0
      ? { ...t, tarih: bugun, source: t.source === 'auto' ? 'moved' : t.source, moved: true }
      : t,
  )
}

/** Plana uyum: bugüne kadar planlanan görevlerin ne kadarı tamamlandı (0-100). */
export function uyumYuzde(tasks = [], bugun = isoGun()) {
  const gecmisVeBugun = tasks.filter((t) => gunFark(t.tarih, bugun) >= 0)
  if (!gecmisVeBugun.length) return null
  const bitti = gecmisVeBugun.filter((t) => t.status === 'done').length
  return Math.round((bitti / gecmisVeBugun.length) * 100)
}

/** Gecikme: bugünkü görevlerin kaçı GEÇMİŞTEN taşındı (moved) ve hâlâ yapılmadı (0-100).
 * carryForward geciken planlı görevlerin tarih'ini bugüne çeker ve moved=true işaretler;
 * bu yüzden gecikmeyi tarih farkından DEĞİL moved bayrağından okuruz (tarih hep bugün olur). */
export function gecikmeYuzde(tasks = [], bugun = isoGun()) {
  const bugunler = tasks.filter((t) => t.tarih === bugun)
  if (!bugunler.length) return 0
  const geciken = bugunler.filter((t) => t.moved && t.status === 'planned').length
  return Math.round((geciken / bugunler.length) * 100)
}

/** Aralıklı tekrar: tamamlanan konu için 1-3-7-14-30 gün sonrası tekrar tarihleri. */
export const TEKRAR_ARALIK = [1, 3, 7, 14, 30]
export function tekrarTarihleri(baseIso) {
  const b = new Date(baseIso + 'T00:00:00')
  return TEKRAR_ARALIK.map((d) => {
    const x = new Date(b)
    x.setDate(b.getDate() + d)
    return isoGun(x)
  })
}

/** "Takvimim nasıl?" için kompakt AI özeti (≤~150 karakter — /ask 500 sınırı korunur). */
export function kompaktOzet({ track = 'YKS', kalanGun, zayif = [], done = [], lag = 0, hedefSaat }) {
  const p = [`EXAM:${track}${kalanGun != null ? ` d-${kalanGun}` : ''}`]
  if (zayif.length) p.push(`ZAYIF:${zayif.slice(0, 3).join(',')}`)
  if (done.length) p.push(`BITEN:${done.slice(0, 3).join(',')}`)
  if (hedefSaat) p.push(`HEDEF:${hedefSaat}s/hafta`)
  p.push(`GECIKME:%${lag}`)
  return p.join('|').slice(0, 150)
}

/** LLM cevabından JSON direktif ayıkla: {oncelik:[...], tavsiye:"..."} | null. */
export function parseDirektif(text) {
  if (!text) return null
  try {
    const m = String(text).match(/\{[\s\S]*\}/)
    if (!m) return null
    const o = JSON.parse(m[0])
    return {
      oncelik: Array.isArray(o.oncelik) ? o.oncelik.map(String).slice(0, 8) : [],
      tavsiye: typeof o.tavsiye === 'string' ? o.tavsiye.slice(0, 400) : '',
    }
  } catch { return null }
}
