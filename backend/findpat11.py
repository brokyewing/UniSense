import re
p = r'C:\Users\asker\Projelerim\UniSense\frontend\src\pages\Search.tsx'
s = open(p, encoding='utf-8').read()
for m in re.finditer(r'const flash = \([^)]*\) =>', s):
    print(m.group(0))