/** Yalnızca http/https dış bağlantılara izin verir (javascript:/data:/vbscript: XSS koruması). */
export function safeHref(url: unknown): string | undefined {
  if (typeof url !== 'string') return undefined
  const trimmed = url.trim()
  if (!/^https?:\/\//i.test(trimmed)) return undefined
  try {
    const parsed = new URL(trimmed)
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return undefined
    return trimmed
  } catch {
    return undefined
  }
}
