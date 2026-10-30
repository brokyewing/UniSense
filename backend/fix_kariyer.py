p = r'C:\Users\asker\Projelerim\UniSense\frontend\src\pages\Kariyer.tsx'
s = open(p, encoding='utf-8').read()
# simple params
s = s.replace('.map((b) =>', '.map((b: any) =>')
s = s.replace('.map((pdf) =>', '.map((pdf: any) =>')
s = s.replace('.map((k) =>', '.map((k: any) =>')
s = s.replace('.map((x) =>', '.map((x: any) =>')
s = s.replace('.filter((x) =>', '.filter((x: any) =>')
s = s.replace('.forEach((k) =>', '.forEach((k: any) =>')
s = s.replace('.forEach((k, i) =>', '.forEach((k: any, i: number) =>')
# function params
s = s.replace('function handleKaynak(kaynak)', 'function handleKaynak(kaynak: any)')
s = s.replace('function handleBolum(bolum)', 'function handleBolum(bolum: any)')
# guncelle, cokluDegistir
s = s.replace('const guncelle = (yama) =>', 'const guncelle = (yama: any) =>')
s = s.replace('const cokluDegistir = (alan, deger) =>', 'const cokluDegistir = (alan: any, deger: any) =>')
s = s.replace('const secimStil = (aktif) =>', 'const secimStil = (aktif: any) =>')
s = s.replace('const yaz = (yeni) =>', 'const yaz = (yeni: any) =>')
# id in useState setter
s = s.replace('for (const k of Object.keys', 'for (const k of Object.keys')
# facet indexing
s = s.replace('facet.il || []', '(facet as any).il || []')
s = s.replace('facet.bolge || []', '(facet as any).bolge || []')
open(p, 'w', encoding='utf-8').write(s)
print('done')