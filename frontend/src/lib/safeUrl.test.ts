import { describe, it, expect } from 'vitest'
import { safeHref } from './safeUrl'

describe('safeHref', () => {
  it('accepts valid http and https URLs with optional outer whitespace', () => {
    expect(safeHref('https://www.unisense.com.tr/yol')).toBe('https://www.unisense.com.tr/yol')
    expect(safeHref('  http://yokatlas.yok.gov.tr/lisans.php?y=123  ')).toBe('http://yokatlas.yok.gov.tr/lisans.php?y=123')
  })

  it('rejects javascript, data, vbscript, file, relative and non-string values', () => {
    expect(safeHref('javascript:alert(1)')).toBeUndefined()
    expect(safeHref('  JaVaScRiPt:alert(1)  ')).toBeUndefined()
    expect(safeHref('data:text/html,<script>alert(1)</script>')).toBeUndefined()
    expect(safeHref('vbscript:msgbox(1)')).toBeUndefined()
    expect(safeHref('ftp://example.com/file')).toBeUndefined()
    expect(safeHref('/tercih')).toBeUndefined()
    expect(safeHref('arucad.edu.tr')).toBeUndefined()
    expect(safeHref('')).toBeUndefined()
    expect(safeHref(null)).toBeUndefined()
    expect(safeHref(undefined)).toBeUndefined()
    expect(safeHref(123)).toBeUndefined()
  })
})
