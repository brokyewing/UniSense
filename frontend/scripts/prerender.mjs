/**
 * Post-build prerender/SSG — CSR SPA'yı arama motorlarına açar.
 * `vite build` sonrası çalışır: her rota için doğru <head> meta'sı + Schema.org
 * JSON-LD + taranabilir semantik HTML (<h1>, özet, iç linkler) ve 631 URL'lik
 * sitemap.xml üretir.
 *
 * Fail-safe: veri okunamazsa (Vercel kök dizin farklıysa) statik rota meta'sı +
 * temel sitemap yine yazılır; build ASLA kırılmaz.
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const DIST = resolve(__dirname, '../dist')
const SITE = 'https://www.unisense.com.tr'
const LOGO_URL = `${SITE}/logo.png`
// Tercih dönemi yılı — src/lib/donem.ts ile AYNI formül (build anında hesaplanır)
const TERCIH_YILI = (() => { const d = new Date(); return d.getMonth() >= 8 ? d.getFullYear() + 1 : d.getFullYear() })()
const TITLE_RE = /<title>[\s\S]*?<\/title>/
const KEYWORDS_RE = /<meta name="keywords"[^>]*>/i
const GOOGLE_VERIFICATION = process.env.VITE_GOOGLE_SITE_VERIFICATION || ''

if (!existsSync(resolve(DIST, 'index.html'))) {
  console.log('[prerender] dist/index.html yok — build çalışmamış, atlanıyor')
  process.exit(0)
}
const template = readFileSync(resolve(DIST, 'index.html'), 'utf-8')

const FOLD = { 'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u', 'â': 'a', 'î': 'i', 'û': 'u' }
const slugify = (name) =>
  name.replace(/İ/g, 'i').replace(/I/g, 'ı').toLowerCase()
    .replace(/[çğıöşüâîû]/g, (c) => FOLD[c] || c)
    .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')

const esc = (s = '') => String(s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
const boldHtml = (t) => esc(t).replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
const stripMd = (s = '') => String(s).replace(/\*\*([^*]+)\*\*/g, '$1').replace(/^[*-]\s*/gm, '').replace(/\s+/g, ' ').trim()
const clampDesc = (s, max = 158) => (s.length <= max ? s : s.slice(0, max - 3).replace(/\s+\S*$/, '') + '…')

function bolumSeoTitle(name, yil) {
  const c1 = `${name} Taban Puanları ve Sıralaması ${yil} | UniSense`
  if (c1.length <= 60) return c1
  const c2 = `${name} Taban Puanları ${yil} | UniSense`
  if (c2.length <= 60) return c2
  const c3 = `${name} Taban Puanları | UniSense`
  if (c3.length <= 60) return c3
  return `${name.slice(0, 42).trim()} Taban Puanları`
}

function contentToHtml(name, content) {
  let html = `<article><h1>${esc(name)}</h1>`
  let inList = false
  for (const raw of (content || '').split('\n')) {
    const line = raw.trim()
    if (!line) { if (inList) { html += '</ul>'; inList = false } continue }
    if (/^[*-]\s/.test(line)) {
      if (!inList) { html += '<ul>'; inList = true }
      html += `<li>${boldHtml(line.replace(/^[*-]\s*/, ''))}</li>`
    } else {
      if (inList) { html += '</ul>'; inList = false }
      html += /\*\*.+\*\*/.test(line) ? `<h2>${boldHtml(line)}</h2>` : `<p>${boldHtml(line)}</p>`
    }
  }
  if (inList) html += '</ul>'
  html += `<nav aria-label="İlgili araçlar"><a href="/bolum">Tüm Üniversite Bölümleri</a> · <a href="/oneriler">YKS Tercih Robotu</a> · <a href="/hesap">TYT-AYT Puan Hesaplama</a></nav></article>`
  return html
}

const NAV_LINKS_HTML = `<nav aria-label="UniSense Araçları"><ul>`
  + `<li><a href="/oneriler">YKS, DGS ve KPSS Tercih Robotu ${TERCIH_YILI}</a></li>`
  + `<li><a href="/hesap">TYT, AYT, OBP, DGS, KPSS ve LGS Puan Hesaplama</a></li>`
  + `<li><a href="/bolum">Üniversite Bölümleri ve Taban Puanları Rehberi</a></li>`
  + `<li><a href="/arama">Yapay Zekâ Taban Puan ve Başarı Sıralaması Sorgulama</a></li>`
  + `<li><a href="/lgs">LGS Lise Tercih Robotu ve Yüzdelik Dilimleri</a></li>`
  + `<li><a href="/tus">TUS ve DUS Uzmanlık Taban Puanları Robotu</a></li>`
  + `<li><a href="/pusula">Meslek Seçimi ve Üniversite Bölümü Testi</a></li>`
  + `<li><a href="/karsilastir">Üniversite ve Bölüm Karşılaştırma</a></li>`
  + `<li><a href="/konular">TYT-AYT Konu Dağılımı ve Konu Takip Çizelgesi</a></li>`
  + `<li><a href="/deneme">YKS Deneme Takip ve Net Analizi</a></li>`
  + `<li><a href="/ozetler">TYT-AYT Matematik, Fizik, Kimya Formül Özetleri</a></li>`
  + `<li><a href="/takvim">${TERCIH_YILI} ÖSYM Sınav Takvimi ve YKS Geri Sayım</a></li>`
  + `<li><a href="/kariyer">Kamu Personel Alımı ve Kariyer Kapısı İş İlanları</a></li>`
  + `</ul></nav>`

function staticContentHtml({ h1, description, bullets = [] }) {
  const listHtml = bullets.length
    ? `<ul>${bullets.map((b) => `<li>${esc(b)}</li>`).join('')}</ul>`
    : ''
  return `<main><h1>${esc(h1)}</h1><p>${esc(description)}</p>${listHtml}${NAV_LINKS_HTML}</main>`
}

function homepageJsonLd() {
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Organization',
        name: 'UniSense',
        url: SITE,
        logo: LOGO_URL,
        sameAs: ['https://github.com/brokyewing/UniSense'],
        contactPoint: [{
          '@type': 'ContactPoint',
          contactType: 'customer support',
          url: `${SITE}/gizlilik`,
          availableLanguage: ['Turkish'],
        }],
      },
      {
        '@type': 'WebSite',
        name: 'UniSense',
        url: SITE,
        inLanguage: 'tr-TR',
        potentialAction: {
          '@type': 'SearchAction',
          target: `${SITE}/arama?q={search_term_string}`,
          'query-input': 'required name=search_term_string',
        },
      },
    ],
  }
}

function toolJsonLd({ name, description, path }) {
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'WebApplication',
        name,
        description,
        url: SITE + path,
        inLanguage: 'tr-TR',
        applicationCategory: 'EducationalApplication',
        operatingSystem: 'Web',
        offers: { '@type': 'Offer', price: '0', priceCurrency: 'TRY' },
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Ana Sayfa', item: SITE + '/' },
          { '@type': 'ListItem', position: 2, name, item: SITE + path },
        ],
      },
    ],
  }
}

function bolumJsonLd({ name, count, summary, path }) {
  const cleanSummary = stripMd(summary).slice(0, 320) || `${name} bölümü dersleri, çalışma alanları ve kariyer olanakları.`
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Ana Sayfa', item: SITE + '/' },
          { '@type': 'ListItem', position: 2, name: 'Bölüm Rehberi', item: SITE + '/bolum' },
          { '@type': 'ListItem', position: 3, name, item: SITE + path },
        ],
      },
      {
        '@type': 'FAQPage',
        mainEntity: [
          {
            '@type': 'Question',
            name: `${name} taban puanları ve başarı sıralaması ${TERCIH_YILI} nedir?`,
            acceptedAnswer: {
              '@type': 'Answer',
              text: `Türkiye genelinde ${name} eğitimi veren ${count} üniversite programının güncel YÖK Atlas ve ÖSYM taban puanlarını, başarı sıralamalarını ve kontenjanlarını UniSense üzerinde devlet/vakıf ve şehir filtresiyle karşılaştırabilirsiniz.`,
            },
          },
          {
            '@type': 'Question',
            name: `${name} mezunları ne iş yapar ve nerede çalışır?`,
            acceptedAnswer: {
              '@type': 'Answer',
              text: cleanSummary,
            },
          },
        ],
      },
    ],
  }
}

function pageHtml({ title, description, path, contentHtml = '', noindex = false, jsonLd = null, keywords = '' }) {
  const url = SITE + path
  const headParts = [
    `<title>${esc(title)}</title>`,
    `<meta name="description" content="${esc(description)}" />`,
    `<link rel="canonical" href="${url}" />`,
    `<meta property="og:title" content="${esc(title)}" />`,
    `<meta property="og:description" content="${esc(description)}" />`,
    `<meta property="og:url" content="${url}" />`,
    `<meta name="twitter:title" content="${esc(title)}" />`,
    `<meta name="twitter:description" content="${esc(description)}" />`,
    `<meta name="twitter:image" content="${LOGO_URL}" />`,
    `<meta name="robots" content="${noindex ? 'noindex, nofollow' : 'index, follow'}" />`,
  ]
  if (GOOGLE_VERIFICATION) {
    headParts.push(`<meta name="google-site-verification" content="${esc(GOOGLE_VERIFICATION)}" />`)
  }
  if (jsonLd) {
    const safeJson = JSON.stringify(jsonLd).replace(/</g, '\\u003c')
    headParts.push(`<script type="application/ld+json">${safeJson}</script>`)
  }
  if (!TITLE_RE.test(template)) {
    console.error('[prerender] HATA: dist/index.html içinde <title> bulunamadı — meta enjekte edilemiyor')
    process.exit(1)
  }
  let html = template.replace(TITLE_RE, headParts.join('\n    '))
  if (keywords && KEYWORDS_RE.test(html)) {
    html = html.replace(KEYWORDS_RE, `<meta name="keywords" content="${esc(keywords)}" />`)
  }
  if (contentHtml) {
    html = html.replace('<div id="root"></div>', `<div id="root">${contentHtml}</div>`)
  }
  return html
}

function writePage(routePath, html) {
  const dir = routePath === '/' ? DIST : resolve(DIST, '.' + routePath)
  mkdirSync(dir, { recursive: true })
  writeFileSync(resolve(dir, 'index.html'), html, 'utf-8')
}

// --- Statik araç rotaları (App ROUTE_SEO ile birebir eşleşir; 50-60 krk title, 125-158 krk description) ---
const STATIC_ROUTES = {
  '/': {
    title: `YKS, LGS, DGS, KPSS Tercih Robotu ${TERCIH_YILI} & Puanlar | UniSense`,
    description: 'Üniversite ve lise taban puanları, başarı sıralamaları, TYT-AYT net ve OBP hesaplama, KPSS, DGS, TUS tercih robotu — YÖK Atlas/ÖSYM verisiyle ücretsiz.',
    h1: `${TERCIH_YILI} YKS, LGS, DGS, KPSS ve TUS Tercih Robotu`,
    bullets: [
      '4 yıllık lisans ve 2 yıllık önlisans üniversite taban puanları ve başarı sıralamaları',
      'TYT, AYT, YDT net ve OBP (okul başarı puanı) hesaplama + YKS sıralama tahmini',
      'LGS yüzdelik dilim lise robotu, DGS dikey geçiş bölümleri, KPSS atama kadroları ve TUS/DUS taban puanları',
    ],
    isHome: true,
  },
  '/arama': {
    title: 'YÖK Atlas Taban Puan & Sıralama Sorgula (AI) | UniSense',
    description: 'Üniversite taban puanları, başarı sıralamaları, kontenjanlar ve KPSS nitelik kodlarını doğal dilde sor; ÖSYM kodlu ve kaynaklı yanıtı anında al.',
    h1: 'Yapay Zekâ ile Taban Puan ve Başarı Sıralaması Sorgula',
    bullets: ['9 haneli ÖSYM program kodlarıyla doğrulanmış bölüm verileri', 'Devlet ve vakıf üniversitesi burslu/ücretli sıralama karşılaştırmaları'],
  },
  '/oneriler': {
    title: `YKS, DGS ve KPSS Tercih Robotu ${TERCIH_YILI} — Sıralama | UniSense`,
    description: 'Sıralamana ve puanına göre güvenli, hedef ve riskli üniversite bölümlerini, DGS geçiş programlarını ve KPSS atama kadrolarını ücretsiz listele.',
    h1: `${TERCIH_YILI} YKS, DGS ve KPSS Tercih Robotu`,
    bullets: ['Başarı sıralamasına göre güvenli, hedef ve riskli tercih analizi', '2 yıllıktan 4 yıllığa DGS geçiş bölümleri ve KPSS merkezi atama taban puanları'],
  },
  '/hesap': {
    title: 'TYT AYT Puan, Net, OBP ve Sıralama Hesaplama | UniSense',
    description: 'TYT, AYT, YDT net ve OBP (diploma notu) hesaplama ile YKS başarı sıralamanı gör; DGS, KPSS, LGS, ALES ve AGS puanlarını tek ekranda ücretsiz hesapla.',
    h1: 'YKS (TYT-AYT), OBP, DGS, KPSS, LGS ve ALES Puan Hesaplama',
    bullets: ['4 yanlış 1 doğruyu götürür kuralıyla anlık net ve yerleştirme puanı hesabı', 'Diploma notundan OBP hesaplama ve geçmiş yıl verileriyle tahmini başarı sıralaması'],
  },
  '/pusula': {
    title: 'Meslek Seçimi Testi & Hangi Bölümü Seçmeliyim | UniSense',
    description: 'Ne okuyacağına karar veremiyor musun? İlgi alanlarına göre yapay zekâ destekli üniversite bölümü ve meslek seçimi testiyle sana en uygun alanları bul.',
    h1: 'İlgi Pusulası — Üniversite Bölümü ve Meslek Seçimi Testi',
    bullets: ['İlgi alanların ve çalışma tarzına göre en uygun lisans bölümleri'],
  },
  '/karsilastir': {
    title: 'Üniversite ve Bölüm Karşılaştırma — Taban Puan | UniSense',
    description: '2 ila 5 üniversite programını yan yana karşılaştır: taban puanı, 3 yıllık başarı sıralaması trendi, kontenjan, burs/ücret, akreditasyon ve istihdam.',
    h1: 'Üniversite Programlarını Yan Yana Karşılaştır',
    bullets: ['Taban puan, başarı sırası trendi, kontenjan, burs ve mezun istihdam karşılaştırması'],
  },
  '/bolum': {
    title: 'Üniversite Bölümleri ve Taban Puanları Rehberi | UniSense',
    description: '600+ lisans ve önlisans üniversite bölümü ne iş yapar, hangi dersleri okur, mezunları nerede çalışır? Bölüm tanıtımları ve güncel taban puanları.',
    h1: 'Üniversite Bölümleri Tanıtım ve Taban Puanları Rehberi',
    bullets: ['4 yıllık fakülte ve 2 yıllık meslek yüksekokulu bölümlerinin dersleri ve iş olanakları'],
  },
  '/konular': {
    title: 'TYT AYT Konu Dağılımı & YKS Konu Takip Çizelgesi | UniSense',
    description: `${TERCIH_YILI} TYT, AYT, KPSS, DGS ve LGS güncel müfredat konu listesi. Ders ders konuları işaretle, eksiklerini gör ve online konu takip çizelgesiyle hazırlan.`,
    h1: `${TERCIH_YILI} YKS (TYT-AYT), KPSS, DGS ve LGS Konu Takip Çizelgesi`,
    bullets: ['Türkçe, Matematik, Geometri, Fizik, Kimya, Biyoloji, Tarih ve Coğrafya güncel konu listeleri'],
  },
  '/deneme': {
    title: 'YKS Deneme Takip, TYT AYT Net Analizi ve Grafik | UniSense',
    description: 'TYT, AYT, KPSS, DGS ve LGS deneme netlerini ve çözdüğün soruları kaydet; net gelişim grafiği ve AI Koç analiziyle eksik konularını ücretsiz takip et.',
    h1: 'Deneme Takip ve Çözülen Soru Net Analizi',
    bullets: ['Ders bazlı net grafiği, zayıf ders tespiti ve konu bazlı soru doğruluk takibi'],
  },
  '/ozetler': {
    title: 'TYT AYT Matematik, Fizik, Kimya Formül Özetleri | UniSense',
    description: 'YKS (TYT-AYT), LGS ve KPSS matematik, geometri, fizik ve kimya formülleri ile pratik konu özetleri tek yerde. Aranabilir ve ücretsiz ders notları.',
    h1: 'TYT-AYT Formül ve Konu Özetleri',
    bullets: ['Sınavda en çok çıkan matematik, geometri, fizik ve kimya formül kartları'],
  },
  '/takvim': {
    title: `${TERCIH_YILI} ÖSYM Sınav Takvimi & YKS Geri Sayım Sayacı | UniSense`,
    description: `${TERCIH_YILI} YKS, LGS, DGS, KPSS, ALES, TUS, DUS ve AGS başvuru, sınav, sonuç ve tercih tarihleri. Sınava kaç gün kaldığını canlı geri sayım sayacıyla takip et.`,
    h1: `${TERCIH_YILI} ÖSYM ve MEB Sınav Takvimi — Geri Sayım`,
    bullets: ['YKS, LGS, KPSS, DGS, ALES, TUS ve DUS sınav, başvuru ve sonuç açıklama günleri'],
  },
  '/lgs': {
    title: `LGS Tercih Robotu ${TERCIH_YILI} — Lise Taban Puanları & Yüzdelik`,
    description: 'LGS yüzdelik dilimini gir; 81 il ve ilçedeki Fen, Anadolu, Sosyal Bilimler ve İmam Hatip liselerinin taban puanlarını ve yüzdelik dilimlerini listele.',
    h1: `LGS Tercih Robotu ${TERCIH_YILI} — Lise Taban Puanları ve Yüzdelik Dilimleri`,
    bullets: ['81 il ve ilçe bazında Fen, Anadolu, Sosyal Bilimler, Mesleki ve İmam Hatip liseleri yüzdelik filtreleme'],
  },
  '/tus': {
    title: `TUS ve DUS Tercih Robotu ${TERCIH_YILI} — Uzmanlık Taban Puanları`,
    description: 'TUS ve DUS puanına göre tıp ve diş hekimliği uzmanlık dallarının ÖSYM en küçük taban puanlarını, kontenjanlarını ve kurumlarını güvenli/hedef olarak gör.',
    h1: `TUS ve DUS Tercih Robotu ${TERCIH_YILI} — Uzmanlık Taban Puanları`,
    bullets: ['Üniversite ve eğitim araştırma hastaneleri uzmanlık kontenjan ve taban puanları'],
  },
  '/kariyer': {
    title: 'Kamu Personel Alımı, Kariyer Kapısı & İş İlanları | UniSense',
    description: 'Günlük güncellenen Resmî Gazete kamu personel alımı, Kariyer Kapısı, BİK, savunma sanayii, KPSS şartlı/şartsız memur ve özel sektör iş/staj ilanları.',
    h1: 'Güncel Kamu Personel Alımı, Kariyer Kapısı ve Özel Sektör İş İlanları',
    bullets: ['Resmî Gazete, Kariyer Kapısı, BİK, Savunma Sanayii ve özel sektör yeni mezun/staj ilan sinyalleri'],
  },
  '/gizlilik': {
    title: 'Gizlilik Politikası ve KVKK Aydınlatma Metni | UniSense',
    description: 'UniSense kullanıcı verilerinin korunması, çerez/yerel depolama kullanımı, hesap silme hakları ve 6698 sayılı KVKK kapsamındaki aydınlatma metni.',
    h1: 'Gizlilik Politikası ve KVKK Aydınlatma Metni',
    bullets: [],
  },
  '/kullanim-kosullari': {
    title: 'Kullanım Koşulları ve Yasal Uyarı | UniSense',
    description: 'UniSense kullanım koşulları, ÖSYM, YÖK Atlas ve MEB resmi veri uyarısı, yapay zekâ ve puan hesaplama sorumluluk sınırı.',
    h1: 'Kullanım Koşulları ve Yasal Uyarı',
    bullets: [],
  },
}

const sitemapUrls = []
const now = new Date().toISOString().slice(0, 10)

for (const [path, meta] of Object.entries(STATIC_ROUTES)) {
  const jsonLd = meta.isHome
    ? homepageJsonLd()
    : (path === '/gizlilik' || path === '/kullanim-kosullari')
      ? null
      : toolJsonLd({ name: meta.h1, description: meta.description, path })
  writePage(path, pageHtml({
    title: meta.title,
    description: meta.description,
    path,
    contentHtml: staticContentHtml(meta),
    jsonLd,
  }))
  sitemapUrls.push({
    loc: SITE + path,
    priority: path === '/' ? '1.0' : (path === '/gizlilik' || path === '/kullanim-kosullari') ? '0.4' : '0.8',
    changefreq: 'weekly',
  })
}

// --- Kişisel noindex rotaları (sitemap'e eklenmez; doğrudan HTML'de noindex döner) ---
const NOINDEX_ROUTES = {
  '/planim': { title: 'Planım — AI Çalışma Planlayıcısı | UniSense', description: 'Haftalık çalışma planını kur, günlük görevlerini takip et.' },
  '/notlar': { title: 'Notlarım | UniSense', description: 'Kişisel çalışma notların ve yapılacaklar listen.' },
  '/pano': { title: 'Çalışma Panom | UniSense', description: 'Pomodoro sayacı, çalışma istatistiklerin ve rozetlerin.' },
  '/tercih': { title: 'Tercih Listem | UniSense', description: 'Kişisel tercih listen.' },
  '/profil': { title: 'Sınav Profilim | UniSense', description: 'Kişisel sınav profili ve hedeflerin.' },
  '/siralama': { title: 'Sıralama | UniSense', description: 'Çalışma sıralaması.' },
  '/giris': { title: 'Giriş | UniSense', description: 'UniSense hesabına giriş yap.' },
}

for (const [path, meta] of Object.entries(NOINDEX_ROUTES)) {
  writePage(path, pageHtml({ ...meta, path, noindex: true }))
}

// --- Bölüm içerik sayfaları (dept_guides.json) ---
let guideCount = 0
try {
  const guidesPath = resolve(__dirname, '../../backend/data/processed/dept_guides.json')
  const guides = JSON.parse(readFileSync(guidesPath, 'utf-8'))
  for (const g of guides) {
    const slug = slugify(g.name)
    const path = `/bolum/${slug}`
    const title = bolumSeoTitle(g.name, TERCIH_YILI)
    const desc = clampDesc(`${g.name} ${TERCIH_YILI} taban puanları, başarı sıralamaları ve kontenjanları (${g.program_count} program). Bölüm dersleri, ne iş yapar ve mezun çalışma alanları.`)
    writePage(path, pageHtml({
      title,
      description: desc,
      path,
      contentHtml: contentToHtml(g.name, g.content),
      jsonLd: bolumJsonLd({ name: g.name, count: g.program_count, summary: g.content, path }),
    }))
    sitemapUrls.push({ loc: SITE + path, priority: '0.7', changefreq: 'monthly' })
    guideCount++
  }
} catch (e) {
  console.log(`[prerender] bölüm verisi okunamadı (${e.message}) — sadece statik rotalar prerender edildi`)
}

// --- Formül/özet kartları (/ozet/:slug) ---
let ozetCount = 0
try {
  const ozetPath = resolve(__dirname, '../../backend/data/processed/ozet_kartlar.json')
  const ozet = JSON.parse(readFileSync(ozetPath, 'utf-8'))
  for (const k of (ozet.kartlar || [])) {
    const path = `/ozet/${k.slug}`
    const maddeler = (k.maddeler || []).map((m) => `<li>${esc(m)}</li>`).join('')
    const contentHtml =
      `<article><h1>${esc(k.baslik)}</h1><p>${esc(k.ders)} · ${esc(k.seviye)}</p>`
      + `<p>${esc(k.ozet)}</p><ul>${maddeler}</ul>`
      + `<nav aria-label="İlgili sayfalar"><a href="/ozetler">Tüm Formül Özetleri</a> · <a href="/konular">YKS Konu Takibi</a></nav></article>`
    const rawT = `${k.baslik} — ${k.ders} Formül Özeti | UniSense`
    const title = rawT.length <= 60 ? rawT : `${k.baslik} — Formül Özeti | UniSense`.slice(0, 60)
    const desc = clampDesc(`${k.ozet} ${k.ders} (${k.konu}) temel formülleri, kuralları ve sınav ipuçları — YKS, LGS ve KPSS için ücretsiz konu özeti.`)
    const jsonLd = {
      '@context': 'https://schema.org',
      '@graph': [
        {
          '@type': 'BreadcrumbList',
          itemListElement: [
            { '@type': 'ListItem', position: 1, name: 'Ana Sayfa', item: SITE + '/' },
            { '@type': 'ListItem', position: 2, name: 'Formül Özetleri', item: SITE + '/ozetler' },
            { '@type': 'ListItem', position: 3, name: k.baslik, item: SITE + path },
          ],
        },
        {
          '@type': 'LearningResource',
          name: k.baslik,
          description: desc,
          url: SITE + path,
          inLanguage: 'tr-TR',
          educationalLevel: k.seviye || 'YKS',
          about: k.ders,
        },
      ],
    }
    writePage(path, pageHtml({ title, description: desc, path, contentHtml, jsonLd }))
    sitemapUrls.push({ loc: SITE + path, priority: '0.6', changefreq: 'monthly' })
    ozetCount++
  }
} catch (e) {
  console.log(`[prerender] özet verisi okunamadı (${e.message}) — atlanıyor`)
}

// --- Sitemap ---
const sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
  sitemapUrls.map((u) => `  <url><loc>${u.loc}</loc><lastmod>${now}</lastmod><changefreq>${u.changefreq}</changefreq><priority>${u.priority}</priority></url>`).join('\n') +
  `\n</urlset>\n`

writeFileSync(resolve(DIST, 'sitemap.xml'), sitemap, 'utf-8')
console.log(`[prerender] ✓ ${Object.keys(STATIC_ROUTES).length} statik rota + ${guideCount} bölüm + ${ozetCount} özet sayfası + sitemap (${sitemapUrls.length} URL)`)
