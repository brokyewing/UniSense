// PostHog analitik — retention/funnel/DAU-WAU ölçümü.
// VITE_POSTHOG_KEY yoksa TAMAMEN dormant: dinamik import sayesinde posthog-js
// chunk'ı hiç indirilmez, hiçbir ağ isteği yapılmaz, hiçbir çerez/veri yazılmaz.
// KVKK notu: key ekleyip analitiği açarsan gizlilik metnini analitik kullanımıyla güncelle.
const KEY = import.meta.env.VITE_POSTHOG_KEY
const HOST = import.meta.env.VITE_POSTHOG_HOST || 'https://eu.i.posthog.com'
let ph = null
let yukleniyor = null

export function analitikAcik() { return !!KEY }

export function initAnalytics() {
  if (!KEY || ph) return Promise.resolve(ph)
  if (yukleniyor) return yukleniyor
  yukleniyor = import('posthog-js').then(({ default: posthog }) => {
    posthog.init(KEY, {
      api_host: HOST,
      capture_pageview: false,   // SPA → pageview'i elle capturePageview ile yolluyoruz
      capture_pageleave: true,
      autocapture: true,
      persistence: 'localStorage',
    })
    ph = posthog
    return ph
  }).catch(() => null)
  return yukleniyor
}

const ready = () => (ph ? Promise.resolve(ph) : initAnalytics())

/** Girişli kullanıcıyı (opak Firebase UID ile) tanımla — retention cohort için. */
export function identify(uid) {
  if (!KEY || !uid) return
  ready().then((p) => p && p.identify(uid))
}

export function resetIdentity() {
  if (ph) ph.reset()
}

export function track(event, props) {
  if (!KEY) return
  ready().then((p) => p && p.capture(event, props))
}

export function capturePageview(path) {
  if (!KEY) return
  ready().then((p) => p && p.capture('$pageview', path ? { $pathname: path } : undefined))
}
