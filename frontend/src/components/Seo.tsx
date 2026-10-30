import { useEffect } from 'react'

const SITE = 'https://www.unisense.com.tr'
const DEFAULT_IMAGE = `${SITE}/logo.png`

interface SeoProps {
  title?: string
  description?: string
  path?: string
  noindex?: boolean
  image?: string
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

export default function Seo({ title, description, path = '', noindex = false, image }: SeoProps) {
  useEffect(() => {
    const url = SITE + (path || '')
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
    upsertMeta('property', 'og:image', image || DEFAULT_IMAGE)
    upsertMeta('name', 'robots', noindex ? 'noindex, nofollow' : 'index, follow')
  }, [title, description, path, noindex, image])

  return null
}