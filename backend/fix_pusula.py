p = r'C:\Users\asker\Projelerim\UniSense\frontend\src\pages\Pusula.tsx'
s = open(p, encoding='utf-8').read()
s = s.replace('.map((iv) =>', '.map((iv: any) =>')
s = s.replace('.map((iv, i) =>', '.map((iv: any, i: number) =>')
s = s.replace('.map((tag) =>', '.map((tag: any) =>')
s = s.replace('.map((m) =>', '.map((m: any) =>')
s = s.replace('.map((m, i) =>', '.map((m: any, i: number) =>')
s = s.replace('.filter((iv) =>', '.filter((iv: any) =>')
# weights indexing
s = s.replace("scores[cat]", "scores[cat as any]")
s = s.replace("scores[w]", "scores[w as any]")
open(p, 'w', encoding='utf-8').write(s)
print('done')