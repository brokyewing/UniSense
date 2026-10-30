p = r'C:\Users\asker\Projelerim\UniSense\frontend\src\pages\Search.tsx'
s = open(p, encoding='utf-8').read()
s = s.replace('.map((d, i) =>', '.map((d: any, i: number) =>')
s = s.replace('function showToast', 'function showToast')
s = s.replace('} catch (e) {', '} catch (e: any) {')
s = s.replace('.map((doc) =>', '.map((doc: any) =>')
s = s.replace('.map((p) =>', '.map((p: any) =>')
s = s.replace('.map((m) =>', '.map((m: any) =>')
s = s.replace('.filter((m) =>', '.filter((m: any) =>')
# text param
s = s.replace('function flash(text)', 'function flash(text: any)')
open(p, 'w', encoding='utf-8').write(s)
print('done')