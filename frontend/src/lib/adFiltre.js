// Takma ad moderasyonu — küfür + taklit (impersonation) filtresi.
// İstemci tarafı BİRİNCİL savunmadır; Firestore kuralları ayrıca ASCII taklit
// sözcüklerini engeller (defense-in-depth). Mükemmel değil — bariz kötüye
// kullanımı eler, gizli/yaratıcı varyasyonların tamamını değil.
//
// Yanlış-pozitiften kaçınmak için kısa/çakışan kökler (sik, got, am, piç, bok,
// yarak) YALNIZ tam eşleşmede engellenir; böylece "aşık", "ışık", "klasik",
// "psikoloji", "kapıcı", "koyarak", "robot", "model" gibi masum adlar geçer.

// Türkçe karakter + leetspeak katlama, harf-dışını at.
function normalize(s) {
  const map = {
    'ı': 'i', 'ş': 's', 'ğ': 'g', 'ü': 'u', 'ö': 'o', 'ç': 'c', 'â': 'a', 'î': 'i', 'û': 'u',
    '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '8': 'b', '9': 'g', '@': 'a', '$': 's', '!': 'i',
  }
  return String(s || '')
    .toLowerCase()
    .replace(/./g, (c) => (map[c] !== undefined ? map[c] : c))
    .replace(/[^a-z]/g, '')
}

// Tam eşleşmede engellenen kökler (kısa/çakışan → substring riskli)
const KUFUR_TAM = ['sik', 'got', 'am', 'amk', 'aq', 'mk', 'oc', 'pic', 'bok', 'yarak', 'amina', 'pust', 'sg']
// İçerdiğinde engellenen kökler (ayırt edici, düşük çakışma)
const KUFUR_PARCA = [
  'siktir', 'sikey', 'sikec', 'siker', 'sikim', 'sikik', 'sikis', 'sikip', 'siker', 'sikcem', 'sikecem',
  'sokarim', 'sokayim', 'amcik', 'aminako', 'aminasi', 'ananisik', 'anasinisik', 'sikini', 'siktigim',
  'orospu', 'orosp', 'oruspu', 'kahpe', 'kaltak', 'yarrak', 'yarrag', 'yarragi', 'yarram',
  'gotver', 'gotlek', 'gotune', 'gotoglan', 'pezeven', 'ibne', 'yavsak', 'gavat', 'fahise', 'surtuk',
  'dallama', 'oxospu', 'pussy', 'fuck', 'shit', 'bitch', 'nigga', 'nigger',
]
// Taklit (impersonation) — yetkili/marka. Tam eşleşme.
const TAKLIT_TAM = ['mod', 'bot', 'root', 'destek', 'support', 'sistem', 'system', 'resmi', 'sahibi']
// Taklit — içerdiğinde engelle.
const TAKLIT_PARCA = ['admin', 'unisense', 'yonetici', 'yonetim', 'moderator', 'moderato', 'official', 'kurucu', 'yetkili', 'resmihesap']

/**
 * Takma ad uygun mu? Uygunsa '' döner; değilse kullanıcıya gösterilecek TR mesaj.
 * (Uzunluk/temizlik kontrolü çağıran tarafta; bu yalnız içerik denetler.)
 */
export function adDenetle(ad) {
  const c = normalize(ad)
  if (!c) return ''
  const loose = c.replace(/(.)\1+/g, '$1') // tekrar eden harfleri sıkıştır (siktirrr → siktir)
  for (const w of KUFUR_TAM) if (c === w || loose === w) return 'Takma ad uygunsuz içerik barındırıyor.'
  for (const w of KUFUR_PARCA) if (c.includes(w) || loose.includes(w)) return 'Takma ad uygunsuz içerik barındırıyor.'
  for (const w of TAKLIT_TAM) if (c === w || loose === w) return 'Bu takma ad kullanılamaz (yetkili/marka taklidi).'
  for (const w of TAKLIT_PARCA) if (c.includes(w) || loose.includes(w)) return 'Bu takma ad kullanılamaz (yetkili/marka taklidi).'
  return ''
}
