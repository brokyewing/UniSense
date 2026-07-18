/* UniSense — FCM arka plan bildirim service worker'ı.
 * PWA sw.js'inden AYRI kayıt/scope → ikisi çakışmaz.
 * Firebase config app tarafından query param ile geçilir (apiKey/appId vb.
 * PUBLIC değerlerdir — her client'a zaten gönderilir, gizli değildir).
 * importScripts sürümü package.json'daki firebase (11.x) ile aynı olmalı.
 */
importScripts('https://www.gstatic.com/firebasejs/11.10.0/firebase-app-compat.js')
importScripts('https://www.gstatic.com/firebasejs/11.10.0/firebase-messaging-compat.js')

const cfg = Object.fromEntries(new URL(self.location).searchParams.entries())

if (cfg.apiKey && cfg.projectId) {
  firebase.initializeApp(cfg)
  const messaging = firebase.messaging()
  // data-only mesajlarda bildirimi kendimiz gösteririz (notification payload'da
  // tarayıcı otomatik gösterir ama tıklama/ikonu tutarlı olsun diye elle basıyoruz)
  messaging.onBackgroundMessage((payload) => {
    const n = payload.notification || {}
    self.registration.showNotification(n.title || 'UniSense', {
      body: n.body || 'Bugün çalışmayı unutma — serini koru! 🔥',
      icon: '/logo.png',
      badge: '/logo.png',
      tag: 'unisense-reminder',
      data: payload.data || {},
    })
  })
}

// Bildirime tıklayınca uygulamayı aç / öne getir
self.addEventListener('notificationclick', (e) => {
  e.notification.close()
  const target = (e.notification.data && e.notification.data.url) || '/konular'
  e.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
      for (const c of list) {
        if ('focus' in c) { if (c.navigate) c.navigate(target); return c.focus() }
      }
      return self.clients.openWindow(target)
    }),
  )
})
