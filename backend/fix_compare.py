p = r'C:\Users\asker\Projelerim\UniSense\frontend\src\pages\Compare.tsx'
s = open(p, encoding='utf-8').read()
# implicit any params
s = s.replace('.filter((it) =>', '.filter((it: any) =>')
s = s.replace('.map((it) =>', '.map((it: any) =>')
s = s.replace('.map((r, i) =>', '.map((r: any, i: number) =>')
s = s.replace('.filter((r, i) =>', '.filter((r: any, i: number) =>')
s = s.replace('function toggle(code)', 'function toggle(code: any)')
s = s.replace('function remove(code)', 'function remove(code: any)')
# lines 15,20,24,28 - small helpers
# Let's view top
open(p, 'w', encoding='utf-8').write(s)
print('done')