/**
 * Post-build prerender/SSG — CSR SPA'yı arama motorlarına açar (Dalga 3).
 * `vite build` sonrası çalışır: her rota için doğru <head> meta'sı gömülü statik
 * HTML, her bölüm için tanıtım İÇERİĞİ gömülü sayfa, ve tüm URL'leri içeren sitemap.
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
// Tercih dönemi yılı — src/lib/donem.js ile AYNI formül (build anında hesaplanır)
const TERCIH_YILI = (() => { const d = new Date(); return d.getMonth() >= 8 ? d.getFullYear() + 1 : d.getFullYear() })()
const TITLE_ANCHOR = `<title>UniSense — ${TERCIH_YILI} Tercih Robotu | YKS, DGS, KPSS</title>`

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

function contentToHtml(name, content) {
  let html = `<h1>${esc(name)}</h1>`
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
  return html
}

function pageHtml({ title, description, path, contentHtml = '', noindex = false }) {
  const url = SITE + path
  const head = [
    `<title>${esc(title)}</title>`,
    `<meta name="description" content="${esc(description)}" />`,
    `<link rel="canonical" href="${url}" />`,
    `<meta property="og:title" content="${esc(title)}" />`,
    `<meta property="og:description" content="${esc(description)}" />`,
    `<meta property="og:url" content="${url}" />`,
    `<meta name="robots" content="${noindex ? 'noindex, nofollow' : 'index, follow'}" />`,
  ].join('\n    ')
  let html = template.replace(TITLE_ANCHOR, head)
  if (contentHtml) {
    // Crawler'lar için içerik #root'a gömülür; React mount'ta client-render ile değişir
    html = html.replace('<div id="root"></div>', `<div id="root">${contentHtml}</div>`)
  }
  return html
}

function writePage(routePath, html) {
  const dir = routePath === '/' ? DIST : resolve(DIST, '.' + routePath)
  mkdirSync(dir, { recursive: true })
  writeFileSync(resolve(dir, 'index.html'), html, 'utf-8')
}

// --- Statik araç rotaları (App ROUTE_SEO ile aynı) ---
const STATIC_ROUTES = {
  '/': { title: `UniSense — ${TERCIH_YILI} Tercih Robotu | YKS, DGS, KPSS Taban Puanlar`, description: 'YKS, DGS ve KPSS tercihine yapay zekâ destekli hazırlan: güncel taban puanlar, başarı sıralamaları, net hesaplama ve kişisel tercih önerileri — ücretsiz.' },
  '/anasayfa': { title: `UniSense — ${TERCIH_YILI} Tercih Robotu | YKS, DGS, KPSS`, description: 'Güncel taban puanlar, sıralamalar ve yapay zekâ destekli tercih önerileriyle YKS, DGS ve KPSS tercihine hazırlan.' },
  '/arama': { title: 'Tercih Sorgu — Taban Puan & Sıralama Sorgula | UniSense', description: 'Doğal dilde sor: bölüm taban puanları, başarı sıralamaları, kontenjanlar ve KPSS kadroları — kaynak gösterimli yapay zekâ sohbeti.' },
  '/oneriler': { title: 'Tercih Önerileri — YKS · DGS · KPSS | UniSense', description: 'Puanına uygun güvenli, hedef ve üst seviye tercihleri yapay zekâyla al. YKS, DGS ve KPSS için ayrı öneriler.' },
  '/hesap': { title: 'Puan Hesaplama — YKS · DGS · KPSS Net Hesap | UniSense', description: 'Netlerini gir, yaklaşık YKS, DGS veya KPSS yerleştirme puanını anında hesapla.' },
  '/pusula': { title: 'İlgi Pusulası — Sana Uygun Bölümü Bul | UniSense', description: 'İlgi alanlarından yapay zekâ ile sana uygun üniversite bölümlerini keşfet.' },
  '/karsilastir': { title: 'Program Karşılaştırma — Taban, Trend, Kadro | UniSense', description: 'Üniversite programlarını yan yana karşılaştır: taban puan, 3 yıllık sıralama trendi, akademik kadro, ücret ve akreditasyon.' },
  '/bolum': { title: 'Bölüm Rehberi — Üniversite Bölümleri Tanıtımı | UniSense', description: 'Üniversite bölümleri ne iş yapar, hangi dersleri okur, mezunları nerede çalışır? Tanıtımlar + güncel taban puanları.' },
  '/konular': { title: 'Konu Takibi — YKS, KPSS, DGS, LGS Konuları | UniSense', description: 'Sınavının tüm konularını ders ders takip et, çalıştıkça işaretle. YKS, KPSS, DGS ve LGS için ücretsiz konu kontrol listesi.' },
  '/takvim': { title: `${TERCIH_YILI} Sınav Takvimi — YKS, LGS, DGS, KPSS, ALES, TUS | UniSense`, description: `${TERCIH_YILI} YKS, LGS, DGS, KPSS, ALES, TUS, DUS ve AGS sınav, sonuç ve tercih tarihleri — kaç gün kaldığıyla tek sayfada.` },
  '/lgs': { title: `LGS Tercih Robotu ${TERCIH_YILI} — Yüzdelik Dilimine Göre Lise Bul | UniSense`, description: 'LGS yüzdelik dilimini gir, girebileceğin Fen, Anadolu, Sosyal Bilimler ve İmam Hatip liselerini güvenli/tutar/riskli olarak gör — ücretsiz, tahminî.' },
  '/tus': { title: `TUS / DUS Tercih Robotu ${TERCIH_YILI} — Puanına Göre Uzmanlık Bul | UniSense`, description: 'TUS veya DUS puanını gir, geçen dönem ÖSYM taban puanlarına göre yerleşebileceğin uzmanlık dallarını ve kurumları güvenli/tutar/riskli olarak gör — ücretsiz, tahminî.' },
  '/gizlilik': { title: 'Gizlilik ve KVKK | UniSense', description: 'UniSense gizlilik politikası ve KVKK aydınlatma metni.' },
}

const sitemapUrls = []
const now = new Date().toISOString().slice(0, 10)

for (const [path, meta] of Object.entries(STATIC_ROUTES)) {
  writePage(path, pageHtml({ ...meta, path }))
  sitemapUrls.push({ loc: SITE + path, priority: path === '/' ? '1.0' : '0.8', changefreq: 'weekly' })
}

// --- Bölüm içerik sayfaları (yalnız dept_guides.json — küçük, garanti erişilebilir) ---
let guideCount = 0
try {
  const guidesPath = resolve(__dirname, '../../backend/data/processed/dept_guides.json')
  const guides = JSON.parse(readFileSync(guidesPath, 'utf-8'))
  for (const g of guides) {
    const slug = slugify(g.name)
    const path = `/bolum/${slug}`
    const desc = `${g.name} bölümü ne iş yapar, hangi dersleri okur, mezunları nerede çalışır? ${g.name} veren ${g.program_count} programın güncel taban puanı ve başarı sıralaması.`
    writePage(path, pageHtml({
      title: `${g.name} — Ne İş Yapar, Taban Puanları | UniSense`,
      description: desc,
      path,
      contentHtml: contentToHtml(g.name, g.content),
    }))
    sitemapUrls.push({ loc: SITE + path, priority: '0.7', changefreq: 'monthly' })
    guideCount++
  }
} catch (e) {
  console.log(`[prerender] bölüm verisi okunamadı (${e.message}) — sadece statik rotalar prerender edildi`)
}

// --- Dinamik sitemap ---
const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${sitemapUrls.map((u) => `  <url><loc>${u.loc}</loc><lastmod>${now}</lastmod><changefreq>${u.changefreq}</changefreq><priority>${u.priority}</priority></url>`).join('\n')}
</urlset>
`
writeFileSync(resolve(DIST, 'sitemap.xml'), sitemap, 'utf-8')

console.log(`[prerender] ✓ ${Object.keys(STATIC_ROUTES).length} statik rota + ${guideCount} bölüm sayfası + sitemap (${sitemapUrls.length} URL)`)
