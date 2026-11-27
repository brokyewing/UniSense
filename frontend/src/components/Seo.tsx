import { useEffect } from 'react'

const SITE = 'https://www.unisense.com.tr'
const DEFAULT_IMAGE = `${SITE}/logo.png`
const GOOGLE_VERIFICATION = import.meta.env.VITE_GOOGLE_SITE_VERIFICATION

interface SeoProps {
  title?: string
  description?: string
  path?: string
  noindex?: boolean
  image?: string
  jsonLd?: Record<string, unknown> | Array<Record<string, unknown>> | null
}

function upsertMeta(attr: string, key: string, value: string): void {
  let el = document.head.querySelector(`meta[${attr}="${key}"]`)
  if (!el) {
    el = document.createElement('meta')
    el.setAttribute(attr, key)
    document.head.appendChild(el)
  }
  el.setAttribute('content', value)
}

function upsertLink(rel: string, href: string): void {
  let el = document.head.querySelector(`link[rel="${rel}"]`)
  if (!el) {
    el = document.createElement('link')
    el.setAttribute('rel', rel)
    document.head.appendChild(el)
  }
  el.setAttribute('href', href)
}

function upsertJsonLd(payload?: Record<string, unknown> | Array<Record<string, unknown>> | null): void {
  const existing = document.head.querySelector('script[data-unisense-ld="1"]')
  if (!payload) {
    if (existing) existing.remove()
    return
  }
  let el = existing as HTMLScriptElement | null
  if (!el) {
    el = document.createElement('script')
    el.type = 'application/ld+json'
    el.setAttribute('data-unisense-ld', '1')
    document.head.appendChild(el)
  }
  el.textContent = JSON.stringify(payload)
}

export default function Seo({ title, description, path = '', noindex = false, image, jsonLd }: SeoProps) {
  useEffect(() => {
    const url = SITE + (path || '')
    const img = image || DEFAULT_IMAGE
    if (title) document.title = title
    if (description) {
      upsertMeta('name', 'description', description)
      upsertMeta('property', 'og:description', description)
      upsertMeta('name', 'twitter:description', description)
    }
    if (title) {
      upsertMeta('property', 'og:title', title)
      upsertMeta('name', 'twitter:title', title)
    }
    upsertLink('canonical', url)
    upsertMeta('property', 'og:url', url)
    upsertMeta('property', 'og:image', img)
    upsertMeta('name', 'twitter:image', img)
    upsertMeta('name', 'robots', noindex ? 'noindex, nofollow' : 'index, follow')
    if (GOOGLE_VERIFICATION) upsertMeta('name', 'google-site-verification', GOOGLE_VERIFICATION)
    if (jsonLd !== undefined) upsertJsonLd(jsonLd)
  }, [title, description, path, noindex, image, jsonLd])

  return null
}