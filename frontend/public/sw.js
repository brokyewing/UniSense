// UniSense service worker — GÜVENLİ (network-first). Amaç: kurulabilirlik (PWA)
// + offline fallback. Bayat uygulama servis etme riskini önlemek için her zaman
// önce ağdan dener; ağ yoksa cache'ten döner. API asla cache'lenmez.
const CACHE = 'unisense-v1'
const SHELL = ['/', '/anasayfa']

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL)).catch(() => {}).then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (e) => {
  const { request } = e
  if (request.method !== 'GET') return
  const url = new URL(request.url)
  if (url.origin !== location.origin) return          // 3. parti (Gemini/FCM/CDN) dokunma
  if (url.pathname.startsWith('/api/')) return          // dinamik veri → cache'leme

  // Network-first: her zaman taze; başarılıysa cache'e yaz; ağ yoksa cache/shell
  e.respondWith(
    fetch(request)
      .then((res) => {
        if (res.ok) {
          const clone = res.clone()
          caches.open(CACHE).then((c) => c.put(request, clone)).catch(() => {})
        }
        return res
      })
      .catch(() => caches.match(request).then((r) => r || caches.match('/anasayfa'))),
  )
})
